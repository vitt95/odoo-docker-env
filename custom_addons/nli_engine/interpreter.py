"""The Interpreter — the one non-deterministic point, and the fence around it.

Everything upstream restricts what the model can say; everything downstream refuses
what it should not have said. This module is where the two meet, and its whole job is
to make sure **nothing leaves it that is not a validated envelope** (V8).

## The single repair attempt (D15)

A failure at levels 1, 2 or 4 may be put back to the model **once**, with the error in
structured form. The limit is normative and worth its argument, because the pressure
to raise it will come:

> A second and a third attempt increase latency and cost on a request that is already
> going badly; above all they **mask a systematic defect**. If the model regularly
> produces invalid output, that datum must appear in the metrics and drive a
> correction, not be silently absorbed by a repetition loop.

So the repair count is returned with the outcome, because §12.7 says the repair rate
is itself an indicator to watch.

## Levels 1 and 2 failing at all is a finding

§12.3: with constrained generation those failures should be rare, and a
non-negligible rate is not a validation problem — it is the signal that constrained
generation is not being applied. `Interpretation` therefore reports which level
failed, not merely that something did.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from odoo.addons.nli_core.contract import schema as schema_module
from odoo.addons.nli_core.validation import coherence, structural

from .adapters.base import AdapterError, Request
from .prompt import catalogue_payload, catalogue_references


@dataclass
class Interpretation:
    """The outcome of one turn of interpretation."""

    envelope: dict | None = None
    failures: list = field(default_factory=list)
    repairs: int = 0
    #: Diagnostics: tokens and duration. Never the utterance, never the catalogue —
    #: D60 makes that a verified prohibition, not a habit.
    replies: list = field(default_factory=list)

    @property
    def understood(self) -> bool:
        return self.envelope is not None

    @property
    def outcome(self) -> str:
        return (self.envelope or {}).get("outcome", "not_understood")


def not_understood() -> dict:
    """The envelope produced when interpretation fails after its one repair.

    A defect of the system, not of the request (§12.7): the user is told *"I did not
    understand, can you rephrase?"* and the event is registered as ours.
    """
    return {"dsl_version": "1.0", "outcome": "not_understood"}


def interpret(adapter, *, utterance: str, catalogue, state: dict | None = None,
              mentions=None, scope_justifies=None, pending=None,
              max_repairs: int = 1) -> Interpretation:
    """Ask the model, validate, allow one repair, and never return anything else.

    `max_repairs` is an argument only so a test can assert that zero and two behave as
    D15 says they must; production uses the default. It is not configuration.

    `mentions(ref, text)` narrows the admitted categories to the ones the sentence
    names (**D112**). It is a callable rather than a dictionary because `nli_engine`
    does not depend on `nli_semantics` (§6.3); omitted, nothing is narrowed.
    """
    payload = catalogue_payload(catalogue)
    # D101: the references of this catalogue close the `ref` of every operation. The
    # prompt says the model chooses and never invents; here that stops depending on
    # the model having read the sentence.
    envelope_schema = schema_module.build_envelope_schema(
        refs=catalogue_references(payload, utterance=utterance, mentions=mentions))
    outcome = Interpretation()
    repair = None

    for attempt in range(max_repairs + 1):
        request = Request(utterance=utterance, catalogue=payload, state=state,
                          pending=pending, repair=repair)
        try:
            reply = adapter.complete(request, schema=envelope_schema)
        except AdapterError as error:
            # §11 of `04`: the model being unavailable is a declared failure mode, not
            # an exception to leak. Saved queries and editing the interpretation stay
            # available, which is why the system is "partially usable" there.
            outcome.failures = [f"provider unavailable: {error}"]
            outcome.envelope = None
            return outcome

        outcome.replies.append(reply)
        candidate, parse_error = _parse(reply.text)
        if candidate is None:
            failures = [parse_error]
        else:
            failures = structural.validate_envelope(candidate)
            if not failures and scope_justifies is not None:
                # D119: il rifiuto per portata deve citare parole che chiedono davvero
                # quella cosa. Qui e non al livello 3, perche' qui la riparazione di
                # D15 scatta e il modello risponde invece di uscire.
                failures = structural.validate_scope_grounding(
                    candidate, justifies=scope_justifies)
            if not failures:
                failures = coherence.validate_envelope_coherence(
                    candidate.get("operations") or [], state=state)

        if not failures:
            outcome.envelope = candidate
            outcome.failures = []
            return outcome

        outcome.failures = failures
        if attempt >= max_repairs:
            break
        outcome.repairs += 1
        repair = _structured_error(failures)

    # One repair spent and still invalid: the outcome towards the user is
    # `not_understood`, and the event is a system defect in the register (§12.7).
    outcome.envelope = not_understood()
    return outcome


def _parse(text: str) -> tuple[dict | None, str]:
    """Read the envelope out of the reply.

    Tolerant of a markdown fence and of nothing else. A model that wraps JSON in
    ```json is common and harmless; one that adds prose has ignored the instruction,
    and accepting that would be the start of a parser nobody can specify.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as error:
        return None, f"the reply is not JSON: {error}"
    if not isinstance(parsed, dict):
        return None, "the reply is JSON but not an object"
    return parsed, ""


def _structured_error(failures) -> dict:
    """The error handed back for the single repair attempt (D15).

    Structured, not prose: the model is being asked to correct a specific thing, and a
    sentence describing it invites a rewrite of the whole answer.
    """
    return {
        "level": min(getattr(failure, "level", 1) for failure in failures),
        "failures": [
            {"code": getattr(failure, "code", "invalid"),
             "path": getattr(failure, "path", ""),
             "detail": getattr(failure, "detail", str(failure))}
            for failure in failures[:5]
        ],
    }
