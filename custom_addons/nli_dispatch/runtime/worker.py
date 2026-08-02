"""One turn, on its own cursor, with the identity of whoever asked for it.

Three properties of `05` §3.4 are realised here, and each one is a decision:

**Its own cursor and its own transaction.** The failure of one turn must not roll back
the others in the batch, which is why the cron's cursor cannot be reused.

**The identity of the requesting user.** V2 holds on the cron process too, and this is
exactly where the temptation to elevate becomes concrete: the code is no longer inside
an authenticated request, so the user has to be rebuilt. The environment is therefore
constructed with the uid **read from the queue row** and the company context
**rebuilt from the turn** (D40) — never with a constant, never with `sudo`. An
execution that restored the user but not their active companies would return the same
orders plus those of a company they had deselected: no error, no warning, a different
number.

**Nothing here decides.** The thread opens a cursor, builds an environment, calls the
pipeline, writes the outcome and notifies. Every judgement — what the limits are, what
the catalogue is, what the model said — belongs to code that can be tested without a
thread.

The pool is threads and not processes because the work is almost entirely network
wait: eight threads waiting on eight HTTP responses cost about what one costs, and
they do not contend for the interpreter lock. That is the case threads are the right
tool for, and `pool.py` is where the size stops being a matter of taste.
"""

from __future__ import annotations

import logging

import odoo
from odoo import api, fields

from . import pipeline

_logger = logging.getLogger(__name__)


def execute(dbname, item_id: int, uid: int, context: dict, *, adapter_factory,
            scope, context_window: int):
    """Run one queue row to completion. Never raises: it records and notifies.

    A thread that dies with an exception leaves a row in `running` and a user in
    front of a spinner. Every failure is therefore turned into a final state and a
    message, and the recovery cron of §5.3 is left to handle only what this function
    could not reach — a process that was killed.
    """
    registry = odoo.registry(dbname)
    with registry.cursor() as cr:
        env = api.Environment(cr, uid, context)
        item = env["nli.queue.item"].browse(item_id)
        try:
            outcome = pipeline.run(
                env, item, adapter=adapter_factory(env), scope=scope,
                context_window=context_window)
        except Exception as error:  # noqa: BLE001 — see the docstring
            cr.rollback()
            return _fail(env, item_id, error)

        _persist(env, item, outcome)
        cr.commit()
        item.notify({"outcome": outcome.outcome,
                     "interpretation": outcome.interpretation})
        return outcome


def _persist(env, item, outcome):
    """Write what the turn produced, then close the queue row.

    The order matters: the turn's state is what the user will see, and the queue row
    reaching a final state is what erases the utterance (D96). Erasing first would
    leave a window in which a crash loses the sentence and the answer both.
    """
    turn = item.turn_id
    values = {"executed_at": fields.Datetime.now(), "outcome": outcome.outcome}
    if outcome.executed:
        values["state_json"] = _dumped(outcome.state)
        values["record_count"] = outcome.record_count
        turn.interrogation_id.write_state(outcome.state)
    # La risposta impaginata si conserva qui, non si riderivera'. Vale per ogni esito,
    # non solo per quelli eseguiti: un chiarimento e un fuori-portata sono risposte che
    # la cronologia deve poter rimostrare (§12.7 li registra come turni completati).
    if outcome.interpretation is not None:
        values["interpretation_json"] = _dumped(outcome.interpretation)
    turn.write(values)

    if outcome.outcome == "operations":
        item.complete()
    elif outcome.provider_failed:
        item.fail("provider_unavailable")
    else:
        # A clarification or an out-of-scope answer is a completed turn, not a
        # failure: the system understood and answered. Recording them as failures
        # would make the failure rate measure the contract working (§12.7).
        item.complete()


def _fail(env, item_id: int, error: Exception):
    """Record an unexpected failure without ever writing what caused it verbatim.

    D60 forbids utterances and catalogues in diagnostic logs, and an exception
    message can carry either — a validation error quotes the value it refused. The
    class name is recorded; the detail stays in the exception, which is logged by the
    platform with the rest of the traceback and not by us.
    """
    item = env["nli.queue.item"].browse(item_id)
    _logger.warning("AIDA turn %s failed: %s", item_id, type(error).__name__)
    item.fail(type(error).__name__)
    item.notify({"outcome": "failed"})
    env.cr.commit()
    return None


def _dumped(state) -> str:
    import json

    return json.dumps(state, ensure_ascii=False)
