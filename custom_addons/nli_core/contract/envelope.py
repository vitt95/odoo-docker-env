"""The Interpretation Envelope: shape and operation signatures (§4.4, §6).

The envelope is what the model produces for one turn. It declares first of all
*what kind of answer* it is giving: not understanding is a legitimate outcome of
the contract, not a format error.

**Pure zone.**

    {
      "dsl_version": "1.0",
      "outcome": "operations" | "clarification" | "out_of_scope" | "not_understood",
      "confidence"?: float,
      "operations"?:    [<operation>],          # outcome == operations
      "clarification"?: {...},                  # outcome == clarification
      "scope_note"?:    str                     # outcome == out_of_scope
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .vocabulary import DSL_VERSION

#: Keys every envelope carries.
REQUIRED_ENVELOPE_KEYS = frozenset({"dsl_version", "outcome"})

#: Keys an envelope may carry beyond its outcome payload.
OPTIONAL_ENVELOPE_KEYS = frozenset({"confidence"})

#: Keys every operation may carry, whatever its verb: the provenance and the
#: confidence that get transferred to the state elements it produces (§6.1), plus
#: `origin`.
#:
#: **`origin` is not in §6.** It is here because §10.2 makes `origin` mandatory on
#: every element of the state, and the specification never says how it gets there.
#: Deriving it from the provenance covers most cases — an operation quoting the
#: user's words produces a `user` element — but not the one §17.1 turn 3 describes
#: itself: `set_order` on a text attribute, where the reference is the user's and
#: the ascending direction is the model's inference, and the state is expected to
#: record `origin: "inferred"`. Without a way to say so, that expectation is not
#: reachable from any envelope. Recorded for ratification alongside D87.
COMMON_OPERATION_KEYS = frozenset({"op", "provenance", "confidence", "origin"})

#: Keys of a clarification (§11.2).
REQUIRED_CLARIFICATION_KEYS = frozenset({"question", "options"})
OPTIONAL_CLARIFICATION_KEYS = frozenset({"provenance"})

#: Keys of a clarification option. Every option carries the operations it would
#: produce, so the user's choice is applied without a second interpretation.
REQUIRED_OPTION_KEYS = frozenset({"label", "operations"})


@dataclass(frozen=True)
class Signature:
    """The parameters of one operation (§6.2-6.6).

    `one_of` expresses the two operations that admit alternative addressing:
    `remove_condition` accepts an identifier *or* a reference, because the user
    says "drop the date filter", not "remove condition c2" — asking the model to
    remember identifiers is asking for exact recall, the task class models fail
    most (§6.3).
    """

    required: frozenset[str] = field(default_factory=frozenset)
    optional: frozenset[str] = field(default_factory=frozenset)
    one_of: tuple[frozenset[str], ...] = ()

    @property
    def allowed(self) -> frozenset[str]:
        alternatives: frozenset[str] = frozenset()
        for group in self.one_of:
            alternatives |= group
        return self.required | self.optional | alternatives | COMMON_OPERATION_KEYS


def _signature(
    required: tuple[str, ...] = (),
    optional: tuple[str, ...] = (),
    one_of: tuple[tuple[str, ...], ...] = (),
) -> Signature:
    return Signature(
        required=frozenset(required),
        optional=frozenset(optional),
        one_of=tuple(frozenset(group) for group in one_of),
    )


#: One entry per operation of `vocabulary.OPERATIONS`. The completeness of this
#: table against that set is checked by the contract's own tests: an operation
#: without a signature would pass level 2 and fail at application, which is the
#: latest and least diagnosable moment.
OPERATION_SIGNATURES: dict[str, Signature] = {
    # Family 1 — entity
    "set_target": _signature(required=("ref",)),
    # Family 2 — conditions
    "add_condition": _signature(required=("condition",), optional=("combine",)),
    "replace_condition": _signature(required=("id", "condition")),
    "remove_condition": _signature(one_of=(("id", "ref"),)),
    "clear_filter": _signature(),
    # Family 3 — presentation
    "add_field": _signature(required=("ref",), optional=("position",)),
    "remove_field": _signature(required=("ref",)),
    "set_fields": _signature(required=("refs",)),
    "clear_fields": _signature(),
    "set_view": _signature(required=("view",)),
    # Family 4 — organisation
    "add_group": _signature(required=("ref",), optional=("granularity",)),
    "remove_group": _signature(required=("ref",)),
    "clear_groups": _signature(),
    "set_order": _signature(required=("ref",), optional=("direction",)),
    "add_order": _signature(required=("ref",), optional=("direction",)),
    "clear_order": _signature(),
    # `count` needs no attribute (§8.5), so a measure may be addressed by
    # function alone.
    "add_measure": _signature(required=("function",), optional=("ref",)),
    "remove_measure": _signature(one_of=(("ref", "function"),)),
    "set_limit": _signature(required=("value",)),
    # Family 5 — session and navigation
    "reset": _signature(),
    "revert_last": _signature(),
    "open_record": _signature(required=("selector",)),
}

#: Keys of a condition as it appears inside an operation. The identifier is
#: absent: the system assigns it (`state.next_condition_id`), because an
#: identifier the model chooses is an identifier the model can collide.
REQUIRED_CONDITION_KEYS = frozenset({"ref", "predicate"})
OPTIONAL_CONDITION_KEYS = frozenset({
    "value", "origin", "provenance", "confidence", "combine",
})


def envelope(outcome: str, **payload) -> dict:
    """Build an envelope of the current version. Convenience for tests and callers."""
    return {"dsl_version": DSL_VERSION, "outcome": outcome, **payload}


def operations_of(candidate: dict) -> list[dict]:
    """The operations of an envelope, or an empty list.

    An empty list is never valid for `outcome: "operations"` (§4.4 completeness
    rule): an unchanged state presented as a success is indistinguishable, for
    the user, from an ignored request. The check belongs to validation; this
    accessor stays total so callers do not each invent their own default.
    """
    operations = candidate.get("operations")
    return list(operations) if isinstance(operations, list) else []
