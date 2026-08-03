"""The queue row, and level 1 of `05` §3: acceptance.

## Why the queue is a model of its own, and not a few fields on `nli.turn`

L3 — queue depth — has to be evaluated **at acceptance**, on the HTTP worker, with
the identity of the user making the request. That means counting the turns of *other*
users, and `nli.turn` carries a record rule that says a user sees their own and
nobody else's. The rule is right: a turn holds `state_json`, which is the question
somebody asked, and making questions readable by colleagues by omission is the
opposite of what §5.10 intends.

The way out is not to widen the rule but to notice that **the queue holds no content
to protect**: a lane, a state, two timestamps, an attempt counter, and the utterance
as ciphertext (D96). There is no field here that could carry a question, which is
criterion **C3** — structural impossibility rather than a prohibition somebody has to
remember. So the rows are readable by internal users, and writable only by their
owner, and the depth of the queue becomes a number anybody can count honestly.

What a colleague can therefore see is *that* somebody asked something and when. That
is metadata, and it is the price of a load limit that works; the question itself, its
interpretation and its result live on `nli.turn`, behind the rule that was already
there.

## The three operations of acceptance, and nothing else

`05` §3.2: check the limits, create the row, trigger the cron. The worker is released
in about ten milliseconds, and the correctness of the release rests on a verified
platform property — `_trigger()` registers its notification **post-commit**
(`ir_cron.py:701`), so the cron worker is woken *after* the pending row is visible.
Without that guarantee there would be a race in which the dispatcher wakes, finds
nothing, and the turn waits for the next tick.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.sql import create_index

from .. import secrecy
from ..queue import limits as limits_module
from ..queue import messages as messages_module

#: `05` §4.3, D20d. Two lanes, never one: the corpus recalculation is the heaviest
#: load the system generates, and sharing the interactive pool with it would make it
#: visible to every user. The lane is on the row because that is what makes the
#: separation structural — each dispatcher claims its own lane and cannot claim the
#: other's, and a test shows it.
LANE_INTERACTIVE = "interactive"
LANE_DEFERRED = "deferred"

PENDING = "pending"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
EXPIRED = "expired"
SUPERSEDED = "superseded"

#: States from which nothing else will happen. Reaching one erases the utterance.
FINAL_STATES = (DONE, FAILED, EXPIRED, SUPERSEDED)

#: How a turn nobody executed is told. The queue's state and the turn's outcome are
#: two different vocabularies on purpose — the first describes the row, the second
#: describes what the user got — but for a turn that never ran they say the same thing,
#: and the turn has to say *something* or it stays a spinner for ever.
TURN_OUTCOME_FOR_STATE = {
    EXPIRED: "expired",
    SUPERSEDED: "superseded",
    FAILED: "failed",
}


class NliQueueItem(models.Model):
    _name = "nli.queue.item"
    _description = "AIDA interpretation queue item"
    _order = "id"

    turn_id = fields.Many2one(
        "nli.turn", required=True, ondelete="cascade", index=True,
        help="The turn this queue row will execute. It carries the company context "
             "of D40, captured at acceptance and restored by the dispatcher.")
    user_id = fields.Many2one(
        "res.users", required=True, ondelete="cascade", index=True,
        default=lambda self: self.env.user)
    lane = fields.Selection(
        [(LANE_INTERACTIVE, "Interactive"), (LANE_DEFERRED, "Deferred")],
        required=True, default=LANE_INTERACTIVE, index=True)
    state = fields.Selection(
        [(PENDING, "Pending"), (RUNNING, "Running"), (DONE, "Done"),
         (FAILED, "Failed"), (EXPIRED, "Expired"), (SUPERSEDED, "Superseded")],
        required=True, default=PENDING, index=True)

    utterance_sealed = fields.Text(
        help="The user's sentence, encrypted with the key named by "
             "NLI_UTTERANCE_KEY and erased on reaching a final state (D96). Never "
             "in clear, at any point, in any column.")

    accepted_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    started_at = fields.Datetime()
    finished_at = fields.Datetime()
    attempts = fields.Integer(
        default=0,
        help="Claims of this row. The recovery of §5.3 gives up at the second: a "
             "turn that reliably kills the process would otherwise be retried "
             "forever, reproducing the failure at every cycle.")
    failure_reason = fields.Char(
        help="A refusal reason of queue.limits, or a technical cause. Never the "
             "utterance and never the catalogue (D60).")

    _sql_constraints = [
        ("attempts_non_negative", "CHECK (attempts >= 0)",
         "An attempt counter that can go backwards cannot bound retries."),
    ]

    def init(self):
        """The index the claim reads.

        The claim is the one statement that runs on every dispatcher cycle under
        load, and it filters on exactly these two columns. Odoo's per-column indexes
        would each match a third of the table; this one matches the rows to lock.

        Built through the platform's own DDL helper rather than a hand-written
        statement: V3 is about our code not reaching past the ORM, and `create_index`
        is the ORM's own way of doing this.
        """
        create_index(
            self.env.cr, "nli_queue_item_claim_idx", self._table, ["lane", "state", "id"]
        )

    # -- level 1 of §3: acceptance -------------------------------------------

    @api.model
    def accept(self, interrogation, utterance: str, *, lane: str = LANE_INTERACTIVE):
        """Accept a request, or refuse it explicitly. Never accept and disappoint.

        Returns the queue row on acceptance. On refusal raises `QueueRefusal`, which
        carries the message of D69 — no fault tone, no attribution to the user, and
        an action — because a refusal presented as an error becomes a support ticket,
        and support tickets are how load limits get raised (RE2).
        """
        if not secrecy.available():
            # Fail closed. Accepting here would mean writing the sentence in clear to
            # get it across to the cron process, and D54 says that is not repairable
            # afterwards.
            raise UserError(
                "AIDA non e' configurata per accettare richieste: manca la chiave "
                f"{secrecy.KEY_VARIABLE} nell'ambiente."
            )

        limits = self._limits()
        decision = limits_module.admit(
            in_flight_for_session=self._in_flight_for(interrogation),
            queued=self._queued(lane),
            requests_last_minute=self._requests_last_minute(),
            provider_available=self._provider_available(),
            limits=limits,
        )
        if not decision.accepted:
            raise QueueRefusal(decision.reason)

        if decision.supersedes:
            # L1: the user changed their mind. The earlier turn is cancelled, not
            # queued behind this one — two interpretations of which the first is
            # already of no interest is wasted cost and a result that flashes.
            self._in_flight_records(interrogation).supersede()

        turn = self.env["nli.turn"].create({
            "interrogation_id": interrogation.id,
            "user_id": self.env.user.id,
            "company_ids": [(6, 0, self.env.companies.ids)],
            "lang": self.env.lang or "en_US",
            "tz": self.env.user.tz or "UTC",
            # D115: la frase resta sul turno, in chiaro, perche' la cronologia deve
            # poterla rimostrare. La copia sigillata qui sotto e' un'altra cosa: serve
            # ad attraversare il processo cron e viene cancellata (D96).
            "utterance": utterance,
        })
        item = self.create({
            "turn_id": turn.id,
            "lane": lane,
            "utterance_sealed": secrecy.seal(utterance),
        })
        self._wake_dispatcher(lane)
        return item

    @api.model
    def accept_request(self, interrogation_id: int, utterance: str,
                       lane: str = LANE_INTERACTIVE) -> dict:
        """`accept`, in the shape a remote call can use.

        The channel of part 7 and the load harness both need to accept a request
        over RPC, where a recordset cannot travel. Returning the refusal as data
        rather than as an exception is deliberate: a refusal for load is a normal
        outcome of a working system (D69), and a caller should not have to inspect a
        fault to find out that the answer is *"try again in a moment"*.
        """
        interrogation = self.env["nli.interrogation"].browse(interrogation_id)
        try:
            item = self.accept(interrogation, utterance, lane=lane)
        except QueueRefusal as refusal:
            return {"accepted": False, "reason": refusal.reason,
                    "message": str(refusal)}
        return {"accepted": True, "item_id": item.id, "turn_id": item.turn_id.id}

    def _wake_dispatcher(self, lane: str):
        """`ir.cron._trigger()` — F1: a wake-up in milliseconds, not in a minute.

        The widespread belief that Odoo's cron has one-minute granularity is about
        the `interval` field; a trigger sends `pg_notify` and the cron worker is
        waiting in `select()` on that connection.

        No `sudo` and none is needed: `_trigger` elevates internally for the trigger
        row it creates, and reading the cron record is not required to call it. The
        elevation that exists is the platform's own, on its own bookkeeping.
        """
        external_id = (
            "nli_dispatch.cron_dispatcher_deferred" if lane == LANE_DEFERRED
            else "nli_dispatch.cron_dispatcher"
        )
        self.env.ref(external_id)._trigger()

    # -- the counts the limits are computed on -------------------------------

    def _limits(self) -> limits_module.Limits:
        """The limits in force, with the pool derived rather than chosen (D20b)."""
        return self.env["nli.dispatcher"]._limits()

    def _in_flight_records(self, interrogation):
        return self.search([
            ("turn_id.interrogation_id", "=", interrogation.id),
            ("state", "in", (PENDING, RUNNING)),
        ])

    def _in_flight_for(self, interrogation) -> int:
        return len(self._in_flight_records(interrogation))

    def _queued(self, lane: str) -> int:
        """L3, counted over **everybody's** rows — see the module docstring."""
        return self.search_count([("state", "=", PENDING), ("lane", "=", lane)])

    def _requests_last_minute(self) -> int:
        since = fields.Datetime.subtract(fields.Datetime.now(), seconds=60)
        return self.search_count([
            ("user_id", "=", self.env.user.id),
            ("accepted_at", ">=", since),
        ])

    def _provider_available(self) -> bool:
        return self.env["nli.dispatcher"]._breaker_admits()

    # -- transitions ---------------------------------------------------------

    def supersede(self):
        return self._finish(SUPERSEDED)

    def expire(self):
        return self._finish(EXPIRED, failure_reason=limits_module.EXPIRED)

    def fail(self, reason: str):
        return self._finish(FAILED, failure_reason=reason)

    def complete(self):
        return self._finish(DONE)

    def _finish(self, state: str, failure_reason: str | None = None):
        """Reach a final state and **erase the utterance in the same write**.

        Not in a later pass, and not by a retention job: the sentence is transient by
        design (D96), and a transient thing that outlives its use by one cleanup cycle
        is a retained thing with extra steps.

        **The turn is closed too, when nobody else closed it.** A queue row that reaches
        a final state without the pipeline having run leaves a turn with no outcome, and
        a turn with no outcome is a turn *in corso* for ever: the history shows it
        waiting for an answer nobody will give. `worker._fail` already closed this for
        the failure it handles; every other way of ending — expiry, supersession, a
        failure recorded from the cron — went through here and closed nothing.

        It only writes when the turn is still blank. A completed turn already carries
        the outcome the pipeline produced, and overwriting it would replace the answer
        with the name of the queue state that followed it.
        """
        values = {
            "state": state,
            "finished_at": fields.Datetime.now(),
            "utterance_sealed": False,
        }
        if failure_reason:
            values["failure_reason"] = failure_reason
        self.write(values)
        for record in self:
            turn = record.turn_id
            if turn and not turn.outcome:
                turn.outcome = TURN_OUTCOME_FOR_STATE.get(state, "failed")
        return self

    def utterance(self) -> str:
        """The sentence, for the one component entitled to it: the Interpreter."""
        self.ensure_one()
        return secrecy.unseal(self.utterance_sealed or "")

    def age_seconds(self, now=None) -> float:
        self.ensure_one()
        now = now or fields.Datetime.now()
        return (now - self.accepted_at).total_seconds()

    # -- level 3 of §3: notification -----------------------------------------

    def notify(self, payload: dict):
        """Tell the client, on the bus served by the gevent process (F3).

        This is what distinguishes the design from polling: a client waiting here
        occupies **no HTTP worker**, whereas ten clients polling once a second
        reintroduce, on a smaller scale, the problem being solved.
        """
        self.ensure_one()
        turn = self.turn_id
        self.user_id.partner_id._bus_send("nli.turn", {
            "item_id": self.id,
            "turn_id": turn.id,
            "state": self.state,
            # Cio' che il canale disegna, cosi' non deve chiedere altro prima di
            # poter mostrare qualcosa: una seconda andata e ritorno fra l'avviso e il
            # disegno si vedrebbe, ed e' l'attrito che l'interfaccia non deve avere.
            # Niente di piu': non lo stato completo, non i record.
            "interrogation_id": turn.interrogation_id.id,
            "record_count": turn.record_count,
            "executed_at": fields.Datetime.to_string(turn.executed_at),
            **payload,
        })


class QueueRefusal(UserError):
    """An explicit refusal for load, with the message D69 requires.

    A `UserError` rather than a bespoke exception because it has to reach the user
    through whatever channel is in front of it, and the platform already knows how to
    do that. What is bespoke is the message: it is looked up, never written at the
    raise site, so that the three properties of D69 hold for every refusal instead of
    for the ones somebody remembered.
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(messages_module.rendered(reason))
