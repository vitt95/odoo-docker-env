"""The chain, assembled: catalogue -> interpreter -> validator -> applicator ->
resolver -> executor -> presenter (`05` §3.3).

This is the composition root, and it is the reason D94 exists: the chain needs the
module that builds the catalogue and the module that talks to the model, and §6.3
forbids either of them from depending on the other. Everything here is orchestration
— not one line of it decides anything the earlier parts had not already decided.

**It takes an environment and a queue row, and returns an outcome.** No threads, no
cursors, no cron: those are `worker.py`'s business. That split is what makes the
chain testable in an ordinary Odoo test, executed inline, with the same code path the
dispatcher runs. A pipeline reachable only through a thread pool is a pipeline nobody
tests at the boundaries.

**The identity is the caller's.** `env` arrives with the requesting user's uid and
the company context rebuilt from the turn (D40). Nothing here elevates, nothing here
reads a configuration the user could not read: §3.4 says *"the dispatcher never runs
with its own privileges"*, and the way to keep that true is for this file to have no
way of knowing it is on a cron process at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from odoo import fields as odoo_fields
from odoo.addons.nli_core.application import applicator
from odoo.addons.nli_core.execution import executor
from odoo.addons.nli_core.presentation import presenter
from odoo.addons.nli_core.resolution import calendar as calendar_module
from odoo.addons.nli_core.resolution import resolver as resolver_module
from odoo.addons.nli_core.validation import contextual
from odoo.addons.nli_engine import interpreter as interpreter_module

#: Outcomes that end the turn without an execution. None of them is a failure of the
#: system: a clarification is the contract working (§4.4), and `out_of_scope` is the
#: product declining honestly rather than answering something adjacent.
TERMINAL_OUTCOMES = ("clarification", "out_of_scope", "not_understood")


@dataclass
class Outcome:
    """What a turn produced, in the shape the notification and the turn both need."""

    outcome: str = "not_understood"
    state: dict | None = None
    interpretation: dict | None = None
    record_count: int = 0
    repairs: int = 0
    failures: list = field(default_factory=list)
    #: True when the provider itself was unreachable — the circuit breaker's input.
    provider_failed: bool = False

    @property
    def executed(self) -> bool:
        return self.outcome == "operations" and self.state is not None


def run(env, item, *, adapter, scope, context_window: int) -> Outcome:
    """One turn, from a sentence to a presented result."""
    turn = item.turn_id
    interrogation = turn.interrogation_id
    state = interrogation.state
    utterance = item.utterance()

    semantics = env["nli.semantics"].semantics(scope)

    entity_ref, outcome = _determine_entity(
        env, semantics, state, utterance, adapter=adapter,
        context_window=context_window)
    if entity_ref is None:
        return outcome

    catalogue = _phase_c(env, semantics, entity_ref, context_window)
    interpretation = interpreter_module.interpret(
        adapter, utterance=utterance, catalogue=catalogue,
        state=state if state.get("target") else None,
    )
    outcome = Outcome(outcome=interpretation.outcome, repairs=interpretation.repairs)
    if not interpretation.understood:
        # `04` §11: the provider being unavailable is a declared failure mode, not an
        # exception to leak. It is also the only failure that must reach the breaker.
        outcome.provider_failed = True
        outcome.failures = list(interpretation.failures)
        return outcome

    envelope = interpretation.envelope
    outcome.outcome = envelope.get("outcome", "not_understood")
    if outcome.outcome in TERMINAL_OUTCOMES:
        outcome.interpretation = {"outcome": outcome.outcome,
                                  **_terminal_payload(envelope)}
        return outcome

    # --- application: pure, and the same code the corpus runs ----------------
    applied = applicator.apply(state, envelope.get("operations") or [])
    new_state = applied.state

    # --- levels 3-5, with the dictionary this user actually has --------------
    types = {ref: binding.type for ref, binding in semantics.bindings.items()}
    failures = contextual.validate(
        new_state, known_refs=frozenset(semantics.bindings), types=types)
    if failures:
        # A validated envelope that produces an invalid state is a defect of ours,
        # not of the request: the user is told we did not understand (§12.7), and the
        # detail goes to the register — never to the user, and never with the words.
        outcome.outcome = "not_understood"
        outcome.failures = [str(failure) for failure in failures]
        return outcome

    entity_ref = (new_state.get("target") or {}).get("ref") or entity_ref
    model_name = semantics.model_of(entity_ref)
    if model_name is None:
        outcome.outcome = "not_understood"
        outcome.failures = [f"the state names an entity that is not in scope: {entity_ref}"]
        return outcome

    # --- resolution: the one component aware of time (04 §4.6) --------------
    resolution = resolver_module.resolve(
        new_state,
        bindings=semantics.bindings,
        instant=_instant(env),
        model=model_name,
    )
    if not resolution.resolved:
        outcome.outcome = "not_understood"
        outcome.failures = [str(failure) for failure in resolution.failures]
        return outcome

    result = executor.execute(env, resolution.plan)
    shown = presenter.present(state=new_state, plan=resolution.plan, result=result)

    outcome.outcome = "operations"
    outcome.state = new_state
    outcome.interpretation = shown.interpretation
    outcome.record_count = result.total
    return outcome


def _determine_entity(env, semantics, state, utterance, *, adapter, context_window):
    """Phases A, B and C — the strategy of D32 on a live dictionary.

    Returns `(entity_ref, None)` when an entity was determined, or `(None, outcome)`
    when the turn ends without one.

    Phase A applies **only when the entity is not known** (§5.5, and registry §16.3,
    which records what applying it to refinements cost: 116 wrong determinations out
    of 1 200). A refinement already carries its target, so it goes straight to C.
    """
    known = (state.get("target") or {}).get("ref")
    if known:
        return known, None

    from odoo.addons.nli_semantics.introspection import runtime

    decision = runtime.determine_entity(semantics, utterance)
    if decision.resolved:
        return decision.entity, None

    # Phase B: the entity names alone, and one question — *which entity is this
    # about?* Small, circumscribed, and the class of task models are most reliable
    # at. The expensive path is also the narrow one, which is what closes RC3.
    catalogue = env["nli.semantics"].entity_catalogue(
        semantics, context_window=context_window)
    interpretation = interpreter_module.interpret(
        adapter, utterance=utterance, catalogue=catalogue, state=None)
    outcome = Outcome(outcome=interpretation.outcome, repairs=interpretation.repairs)
    if not interpretation.understood:
        outcome.provider_failed = True
        outcome.failures = list(interpretation.failures)
        return None, outcome

    envelope = interpretation.envelope
    entity = _target_of(envelope)
    if entity and entity in semantics.entity_refs:
        return entity, outcome

    outcome.outcome = envelope.get("outcome", "not_understood")
    if outcome.outcome in TERMINAL_OUTCOMES:
        outcome.interpretation = {"outcome": outcome.outcome,
                                  **_terminal_payload(envelope)}
    else:
        # Operations without a target, or with one outside the catalogue it was just
        # given. D14: an unknown symbol is refused, never ignored — ignoring it here
        # would run the query against whichever entity happened to be around.
        outcome.outcome = "not_understood"
        outcome.failures = ["phase B produced no entity from the entity catalogue"]
    return None, outcome


def _target_of(envelope: dict) -> str | None:
    for operation in envelope.get("operations") or []:
        if operation.get("op") == "set_target":
            return operation.get("ref")
    return None


def _phase_c(env, semantics, entity_ref: str, context_window: int):
    return env["nli.semantics"].catalogue_for(
        semantics, entity_ref, context_window=context_window)


def _terminal_payload(envelope: dict) -> dict:
    """What travels to the user for a non-executing outcome.

    The clarification's own question and options, or the scope note. Never the
    envelope wholesale: it carries provenance fragments, which are the user's words,
    and D54 says those do not get written anywhere they would be retained.
    """
    if envelope.get("outcome") == "clarification":
        return {"clarification": envelope.get("clarification") or {}}
    if envelope.get("outcome") == "out_of_scope":
        return {"scope_note": envelope.get("scope_note")}
    return {}


def _instant(env) -> calendar_module.Instant:
    """The reference instant, read **here** and nowhere deeper.

    The Resolver is aware of time and never reads it (§4.6): this is the line where
    the clock enters the chain, in the user's own timezone, so that *"this month"*
    means their month. The fiscal year parameters ride along because `year_to_date`
    resolves against the fiscal year and not against January (V-D91-1) — in a company
    with a non-calendar year, January would give a wrong number that looks right.
    """
    now = odoo_fields.Datetime.context_timestamp(
        env["res.users"].browse(env.uid), odoo_fields.Datetime.now())
    last_month = int(getattr(env.company, "fiscalyear_last_month", 12) or 12)
    return calendar_module.Instant(
        now=now.replace(tzinfo=None),
        # The year starts the month after the one it ends in, on the first day. That
        # covers every fiscal year that ends at a month boundary, which is all of
        # them in practice; an installation ending mid-month would need the day too,
        # and would deserve a test before being claimed to work.
        fiscal_year_start_month=last_month % 12 + 1,
        fiscal_year_start_day=1,
    )
