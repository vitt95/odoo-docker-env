"""Level 2 of `05` §3: the dispatcher, its cycle, and the two crons beside it.

The shape is forced by two verified platform constraints, not chosen:

* **V-A** — one `ir.cron` record admits a single concurrent execution across the whole
  cluster (`ir_cron.py:140`, row-level lock). Concurrency therefore has to be obtained
  *inside* the job, with a thread pool, and not by multiplying jobs;
* **V-B** — cron processes are few and shared with the customer's own scheduled work.
  Occupying one continuously would halve the installation's scheduling capacity, so
  the cycle is bounded at `CYCLE_MAX` and re-triggers itself.

`CYCLE_MAX` is fifteen seconds against a limit of a hundred and twenty (**V-C**). The
margin is not caution: a cycle killed by `--limit-time-real-cron` leaves rows in
`running` with nobody running them, and manufacturing work for the recovery mechanism
is a poor way to use it.

**The cron identity never touches business data.** The dispatcher runs as the root
cron user, because claiming rows and reading configuration is system bookkeeping; the
turn itself runs in `worker.py`, on another cursor, with the uid read from the queue
row. That separation is the whole of §3.4's *"the dispatcher never runs with its own
privileges"*, and a test asserts it by checking the uid the pipeline is handed.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor

from odoo import api, fields, models
from odoo.addons.nli_engine.adapters import synthetic
from odoo.tools import config

from ..queue import breaker as breaker_module
from ..queue import limits as limits_module
from ..queue import pool as pool_module
from ..runtime import claim as claim_module
from ..runtime import worker as worker_module
from .nli_queue_item import LANE_DEFERRED, LANE_INTERACTIVE, PENDING, RUNNING

_logger = logging.getLogger(__name__)

#: `05` §6. Seconds of one cycle before the dispatcher yields the cron process.
CYCLE_MAX = 15.0

#: The deferred lane runs the heaviest load the system generates — the corpus
#: recalculation — and has no latency requirement (§4.3, D20d). A narrow pool is the
#: point: it must not be able to consume the connection budget the interactive lane
#: needs, even when it is the only thing running.
DEFERRED_POOL_CEILING = 2

#: §5.3. Two claims and then `failed`. Without the counter, a turn that reliably
#: kills the process is retried forever, reproducing the failure every cycle.
MAX_ATTEMPTS = 2

#: How long a row may sit in `running` before it is presumed orphaned. Generous
#: against the slowest plausible provider: reviving a turn that is merely slow would
#: execute it twice.
ORPHAN_SECONDS = 300


class NliDispatcher(models.AbstractModel):
    _name = "nli.dispatcher"
    _description = "AIDA interpretation dispatcher"

    # -- cron entry points ----------------------------------------------------

    @api.model
    def _cron_dispatch(self):
        """The interactive lane."""
        return self._run_lane(LANE_INTERACTIVE, "nli_dispatch.cron_dispatcher")

    @api.model
    def _cron_dispatch_deferred(self):
        """The deferred lane, on its own cron record and its own pool (D20d)."""
        return self._run_lane(
            LANE_DEFERRED, "nli_dispatch.cron_dispatcher_deferred",
            pool_ceiling=DEFERRED_POOL_CEILING)

    @api.model
    def _cron_recover(self):
        """Rows left in `running` by a process that stopped (§5.3).

        Two outcomes, and the counter decides which: back to `pending` for another
        attempt, or `failed` with a message. The user is told either way — a turn
        that silently disappears is worse than one that failed, because the user
        waits for it.
        """
        threshold = fields.Datetime.subtract(
            fields.Datetime.now(), seconds=ORPHAN_SECONDS)
        orphans = self.env["nli.queue.item"].search([
            ("state", "=", RUNNING), ("started_at", "<", threshold),
        ])
        requeued = 0
        for item in orphans:
            if item.attempts >= MAX_ATTEMPTS:
                item.fail("orphaned")
                item.notify({"outcome": "failed"})
            else:
                item.write({"state": PENDING, "started_at": False})
                requeued += 1
        if requeued:
            self.env.ref("nli_dispatch.cron_dispatcher")._trigger()
        return len(orphans)

    # -- the cycle ------------------------------------------------------------

    def _run_lane(self, lane: str, cron_xmlid: str, *, pool_ceiling: int | None = None):
        limits = self._limits(pool_ceiling=pool_ceiling)
        scope = self.env["nli.semantics"].entity_scope()
        context_window = self._context_window()
        started = time.monotonic()
        executed = 0

        while time.monotonic() - started < CYCLE_MAX:
            self._expire(lane, limits)
            pending = claim_module.pending_count(self.env, lane=lane)
            items = claim_module.claim(
                self.env, lane=lane,
                size=limits_module.batch_size(pending=pending, limits=limits))
            if not items:
                break
            # §3.4: the reservation is confirmed **before** the work starts.
            self._checkpoint()
            executed += self._run_batch(items, scope=scope,
                                        context_window=context_window)

        if claim_module.pending_count(self.env, lane=lane):
            # Yield the cron process and come straight back: V-B is satisfied by
            # giving the slot up, not by working less.
            self.env.ref(cron_xmlid)._trigger()
        return executed

    def _run_batch(self, items, *, scope, context_window: int) -> int:
        """Run a claimed batch in parallel, one cursor and one identity per row."""
        dbname = self.env.cr.dbname
        jobs = [
            (item.id, item.user_id.id, item.turn_id.context_for_execution())
            for item in items
        ]
        outcomes = []
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            futures = [
                executor.submit(
                    worker_module.execute, dbname, item_id, uid, context,
                    adapter_factory=self._adapter_factory(), scope=scope,
                    context_window=context_window)
                for item_id, uid, context in jobs
            ]
            for future in futures:
                try:
                    outcomes.append(future.result())
                except Exception:  # noqa: BLE001
                    _logger.exception("AIDA dispatcher: a worker did not return")
                    outcomes.append(None)

        self._record_provider_health(outcomes)
        return len(jobs)

    def _expire(self, lane: str, limits: limits_module.Limits):
        """L4 — the limit that lets the queue recover instead of accumulating.

        A turn queued for more than thirty seconds has lost its recipient. Executing
        it costs money and holds the pool against live requests, so it is discarded
        **and the user is told**, with the message of D69.
        """
        threshold = fields.Datetime.subtract(
            fields.Datetime.now(), seconds=limits.max_age_seconds)
        stale = self.env["nli.queue.item"].search([
            ("lane", "=", lane), ("state", "=", PENDING),
            ("accepted_at", "<", threshold),
        ])
        for item in stale:
            item.expire()
            item.notify({"outcome": "expired"})
        if stale:
            self._checkpoint()

    def _checkpoint(self):
        """Make the reservation durable before any work depends on it.

        A method rather than a bare `commit()` for one reason, and it is worth being
        explicit about it: Odoo's test cursor refuses to commit, so a dispatcher that
        committed inline could not be exercised by any test at all. The seam is
        narrow — it commits and does nothing else — and the tests that neutralise it
        assert what the commit is *for*: that the rows are already `running` when the
        batch starts.
        """
        self.env.cr.commit()

    # -- configuration derived, never chosen ----------------------------------

    @api.model
    def _limits(self, *, pool_ceiling: int | None = None) -> limits_module.Limits:
        """The five limits, with the pool **derived** from `db_maxconn` (D20b, §6.4).

        RE4 is the risk this closes: a pool sized as though the work were computation.
        The ceiling is the number of PostgreSQL connections, every thread holds one,
        and exhausting them shows up on the ERP rather than on the product.
        """
        deployment = pool_module.Deployment(
            db_maxconn=int(config.get("db_maxconn") or 64),
            http_workers=int(config.get("workers") or 0) or 1,
            max_cron_threads=int(config.get("max_cron_threads") or 2),
            dispatchers=1,
        )
        size = pool_module.pool_size(
            deployment,
            ceiling=pool_ceiling or pool_module.DEFAULT_POOL_CEILING,
        )
        return limits_module.Limits(pool=size)

    @api.model
    def _context_window(self) -> int:
        """The active profile's declared window (D78), which sets the budget (D79)."""
        profile = self.env["nli.profile"].active_profile()
        return profile.capabilities().context_window if profile else 8192

    def _adapter_factory(self):
        """A callable the worker uses to get an adapter **inside its own env**.

        Passed as a factory rather than as an adapter because the profile is read
        with the user's rights on the worker's cursor: a shared object built here
        would carry the cron's environment into a thread that must not have it.

        **The one branch, and why it is here** (D97). The isolation proof of D27
        needs turns that occupy a pool thread and a database connection for the time
        a provider takes — without that, the queue drains instantly and the
        measurement is of nothing. The local model would give a real latency, but
        D80 refuses to activate a profile that has not been qualified, and that rule
        is right. So the bench does not go through a profile at all: it is an
        environment variable, absent by default, that never widens anything and
        announces itself in the log every cycle.
        """
        if synthetic.enabled():
            _logger.warning(
                "AIDA: %s is set — turns are answered by the load bench, not by a "
                "model (D97). Unset it to return to the active profile.",
                synthetic.VARIABLE)

            def bench(env):
                return synthetic.SyntheticAdapter.from_environment()

            return bench

        def factory(env):
            return env["nli.profile"].active_profile().adapter()

        return factory

    # -- the circuit breaker of §4.4 ------------------------------------------

    def _record_provider_health(self, outcomes):
        state = self.env["nli.breaker"]._get()
        for outcome in outcomes:
            if outcome is None:
                continue
            if outcome.provider_failed:
                state = state.after_failure(time.time())
            else:
                state = state.after_success()
        self.env["nli.breaker"]._put(state)

    @api.model
    def _breaker_admits(self) -> bool:
        return self.env["nli.breaker"]._get().admits(time.time())


class NliBreaker(models.Model):
    """The circuit breaker's state, in a row instead of in a process.

    It has to be a row: acceptance runs on an HTTP worker and the dispatcher runs on
    a cron process, and a breaker that only one of them can see would refuse nothing
    at the point where refusing matters — §4.4 is about not *accepting* turns that
    are going to fail.

    Readable by every internal user, writable only by the dispatcher. It holds two
    integers and no user data, which is what makes the read harmless.
    """

    _name = "nli.breaker"
    _description = "AIDA provider circuit breaker"

    consecutive_failures = fields.Integer(default=0)
    opened_at = fields.Float(
        help="Monotonic-free wall clock, seconds since the epoch. Compared only "
             "with itself, to decide whether the cooling period has elapsed.")

    @api.model
    def _get(self) -> breaker_module.Breaker:
        row = self.search([], limit=1)
        if not row:
            return breaker_module.Breaker()
        return breaker_module.Breaker(
            consecutive_failures=row.consecutive_failures,
            opened_at=row.opened_at or None,
        )

    @api.model
    def _put(self, state: breaker_module.Breaker):
        values = {
            "consecutive_failures": state.consecutive_failures,
            "opened_at": state.opened_at or 0.0,
        }
        row = self.search([], limit=1)
        if row:
            row.write(values)
        else:
            self.create(values)
        return state
