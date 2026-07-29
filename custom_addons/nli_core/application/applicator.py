"""The Applicator: operations plus a state produce a new state (§4.5, D9).

**Pure zone.** Same operations, same starting state, same result — always, and in
particular in six months. This is the invariant the fourth boundary check of
`04` §6.4 exists to protect, and the one the 1 200 cases of the foundational
corpus depend on: a corpus whose expected states shift with the clock is a
snapshot, not a key (D82).

The four rules of §4.5:

1. **Sequentiality** — operations apply in the order given; the order matters and
   is not normalised here.
2. **Atomicity** — all of them or none. A partially modified state is never
   observable, so the work happens on a copy that is returned only if the whole
   sequence succeeded.
3. **Total prior validation** — validation precedes application entirely
   (§12.1). This module therefore does not re-validate: it raises
   `ApplicationError` when an assumption validation should have guaranteed is
   broken, rather than repairing quietly. A repair here would mean an invalid
   envelope produced a result, which §12.1 forbids without exception.
4. **Final normalisation** — once, at the end of the sequence.

**A note on rule 4, because the specification is ambiguous and the reading
matters.** §4.5 says the resulting state is "brought into canonical form" once at
the end. Taken literally against §14.3 rule 1, that would strip `origin`,
`provenance` and the condition identifiers — and with them D64, the whole of §10
and the user's ability to recognise a misunderstanding. §14.2 resolves it: there
are two forms, and the one that persists is the **exercise form**, which keeps
insertion order and metadata. What happens at the end of application is therefore
the normalisation *common to both* — connective reduction, removal of empty
sections, materialisation of the effective limit and view (§14.3 rules 4, 5, 7).
The canonical form proper is computed on demand, for comparison, by
`contract.canonical`.

Two operations do not produce a state, and saying so in the return type is what
keeps them from being special-cased by every caller:

* `revert_last` restores the previous state from the history **the system owns**
  (§6.6). A pure function has no history, so it reports the request;
* `open_record` navigates and leaves the interrogation intact (§6.6).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Sequence

from ..contract import state as state_module
from ..contract.vocabulary import (
    DEFAULT_LIMITS,
    RULE_LATEST_DESC,
    RULE_TEXT_ASC,
    VIEW_DERIVATION_RULES,
    Limits,
)


class ApplicationError(Exception):
    """An operation could not be applied to this state.

    Every instance is a validation escape: the envelope reached application in a
    shape validation should have refused. Raising rather than coping is
    deliberate — the alternative is a state that nobody asked for.
    """


@dataclass(frozen=True)
class Navigation:
    """The outcome of `open_record`: a record to open, no change to the state."""

    selector: dict


@dataclass
class Result:
    """What applying one envelope's operations produced."""

    state: dict
    #: Requests to restore the previous state (`revert_last`). Resolved by the
    #: orchestrator against the persisted history, which is where the history is.
    revert_requested: bool = False
    #: Navigations produced by `open_record`, in order.
    navigations: list[Navigation] = field(default_factory=list)


def apply(
    state: dict,
    operations: Sequence[dict],
    *,
    limits: Limits = DEFAULT_LIMITS,
    default_fields: Sequence[str] = (),
) -> Result:
    """Apply `operations` to `state` and return the new state.

    `state` is never mutated. `default_fields` are the entity's default displayed
    attributes, which live in the Semantic Dictionary (§5.5): they are passed in
    rather than looked up, because looking them up is what would make this
    function impure. They are required only by `add_field` and `remove_field` on
    a state whose `fields` section is absent — the one case where the operation's
    meaning depends on what the default is.
    """
    working = copy.deepcopy(state)
    result = Result(state=working)

    for index, operation in enumerate(operations):
        verb = operation.get("op")
        handler = _HANDLERS.get(verb)
        if handler is None:
            raise ApplicationError(
                f"operations[{index}]: unknown operation {verb!r} reached "
                "application; level 2 should have refused it"
            )
        handler(result, operation, limits, tuple(default_fields), index)

    result.state = normalise(result.state, limits=limits)
    return result


# ---------------------------------------------------------------------------
# Origin derivation (§6.1, §10.2)
# ---------------------------------------------------------------------------

def _origin(operation: dict) -> str:
    """Where a state element produced by this operation came from.

    §6.1: an operation carries its own provenance and confidence, and transfers
    them to the elements it produces. So an operation quoting a fragment of the
    user's sentence produces `user` elements, and one that quotes nothing
    produces `inferred` ones — the system added something nobody asked for, and
    §10.2 requires it to say so.

    An explicit `origin` on the operation wins over the derivation, because the
    derivation cannot reach every case §10.2 requires — see the note on
    `envelope.COMMON_OPERATION_KEYS`.

    The granularity stops at the operation either way. In `set_order` with a
    direction the model inferred, the reference is the user's and the direction is
    not, but the envelope of §6 has one provenance per operation, not one per
    parameter. It does not affect the accuracy measurement — §14.3 rule 1 removes
    `origin` from the canonical form — but it does mean the interpretation cannot
    distinguish those two cases, and that is worth knowing before §10.2 is relied
    upon as the defence against R1.
    """
    declared = operation.get("origin")
    if declared:
        return declared
    return "user" if operation.get("provenance") else "inferred"


def _metadata(operation: dict, *, origin: str | None = None) -> dict:
    """The provenance metadata an operation transfers to what it produces."""
    carried: dict = {"origin": origin or _origin(operation)}
    if "provenance" in operation:
        carried["provenance"] = copy.deepcopy(operation["provenance"])
    if "confidence" in operation:
        carried["confidence"] = operation["confidence"]
    return carried


# ---------------------------------------------------------------------------
# Family 1 — entity
# ---------------------------------------------------------------------------

def _set_target(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    ref = operation["ref"]
    current = (state.get("target") or {}).get("ref")

    if current is not None and current != ref:
        # §6.2 restart rule. A change of entity makes every reference built on the
        # previous one meaningless; carrying them over would be a silent inference
        # about meaning, which is the behaviour R1 exists to prevent.
        for section in state_module.SECTIONS_CLEARED_ON_TARGET_CHANGE:
            state.pop(section, None)
        state.pop("limit", None)
        state.pop("presentation", None)

    state["target"] = {"ref": ref, **_metadata(operation)}


# ---------------------------------------------------------------------------
# Family 2 — conditions
# ---------------------------------------------------------------------------

def _add_condition(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    condition = copy.deepcopy(operation["condition"])
    condition.setdefault("id", state_module.next_condition_id(state))
    for key, value in _metadata(operation).items():
        condition.setdefault(key, value)
    condition.pop("combine", None)

    combine = operation.get("combine", "all")
    existing = state.get("filter")

    if existing is None:
        state["filter"] = condition
        return
    if state_module.is_connective(existing) and existing["connective"] == combine:
        existing["conditions"].append(condition)
        return
    # Different connective, or a single condition as root: nest one level. The
    # depth limit of §5.4 is checked by level 4, not enforced by silent flattening
    # — flattening would change the meaning of the filter.
    state["filter"] = {"connective": combine, "conditions": [existing, condition]}


def _replace_condition(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    target_id = operation["id"]
    existing = state_module.find_condition(state, target_id)
    if existing is None:
        raise ApplicationError(
            f"operations[{index}]: replace_condition on unknown identifier "
            f"{target_id!r}; level 4 should have refused it"
        )
    replacement = copy.deepcopy(operation["condition"])
    replacement["id"] = target_id
    for key, value in _metadata(operation).items():
        replacement.setdefault(key, value)
    replacement.pop("combine", None)
    # Replace in place: the identifier and the position are what keep the element
    # anchored in the interpretation shown to the user — it changes value, it does
    # not disappear and reappear (§6.3).
    existing.clear()
    existing.update(replacement)


def _remove_condition(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    if "id" in operation:
        matches = lambda condition: condition.get("id") == operation["id"]
    else:
        matches = lambda condition: condition.get("ref") == operation["ref"]

    filtered = _prune(state.get("filter"), matches)
    if filtered is None:
        state.pop("filter", None)
    else:
        state["filter"] = filtered


def _prune(node: dict | None, matches) -> dict | None:
    if node is None:
        return None
    if not state_module.is_connective(node):
        return None if matches(node) else node
    kept = [child for child in (_prune(c, matches) for c in node["conditions"]) if child]
    if not kept:
        return None
    return {**node, "conditions": kept}


def _clear_filter(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.state.pop("filter", None)


# ---------------------------------------------------------------------------
# Family 3 — presentation
# ---------------------------------------------------------------------------

def _materialised_fields(state: dict, defaults: tuple[str, ...], operation: str, index: int) -> list[dict]:
    """The `fields` list to work on, expanding the entity defaults if needed.

    An absent `fields` section does not mean "no attributes": it means the user
    has not expressed a preference and the entity's default attributes apply
    (§5.5). So "show me the phone number too" on such a state means *defaults plus
    phone*, and producing `[phone]` instead would silently drop every column the
    user was looking at.
    """
    if "fields" in state:
        return state["fields"]
    if not defaults:
        raise ApplicationError(
            f"operations[{index}]: {operation} on a state without a 'fields' "
            "section requires the entity's default attributes, which come from "
            "the Semantic Dictionary (§5.5). Pass them as default_fields"
        )
    return [{"ref": ref, "origin": "default"} for ref in defaults]


def _add_field(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    fields = _materialised_fields(state, defaults, "add_field", index)
    ref = operation["ref"]
    if any(entry.get("ref") == ref for entry in fields):
        # "Show me the phone too" when the phone is already shown is a no-op from
        # the user's point of view. Refusing it would be hostile; duplicating the
        # column would be wrong.
        state["fields"] = fields
        return
    entry = {"ref": ref, **_metadata(operation)}
    position = operation.get("position")
    if position is None:
        fields = [*fields, entry]
    else:
        fields = [*fields[:position], entry, *fields[position:]]
    state["fields"] = fields


def _remove_field(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    fields = _materialised_fields(state, defaults, "remove_field", index)
    # An empty result is left as an empty list rather than turned into an absent
    # section: absent means "the entity defaults", so removing the last column
    # would silently restore every column. Validation refuses the empty list
    # (§5.5) and atomicity discards the whole envelope — which is the correct
    # answer to "remove the only column I am looking at".
    state["fields"] = [entry for entry in fields if entry.get("ref") != operation["ref"]]


def _set_fields(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    metadata = _metadata(operation)
    result.state["fields"] = [
        {"ref": ref, **metadata} for ref in operation["refs"]
    ]


def _clear_fields(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    # Restores the entity defaults by making the section absent (§6.4, §5.5).
    result.state.pop("fields", None)


def _set_view(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.state["presentation"] = {"view": operation["view"], **_metadata(operation)}


# ---------------------------------------------------------------------------
# Family 4 — organisation
# ---------------------------------------------------------------------------

def _add_group(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    groups = list(state.get("group_by", []))
    ref = operation["ref"]
    granularity = operation.get("granularity")
    for entry in groups:
        if entry.get("ref") == ref:
            if granularity is not None:
                entry["granularity"] = granularity
            state["group_by"] = groups
            return
    entry = {"ref": ref, **_metadata(operation)}
    if granularity is not None:
        entry["granularity"] = granularity
    state["group_by"] = [*groups, entry]


def _remove_group(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    state["group_by"] = [
        entry for entry in state.get("group_by", []) if entry.get("ref") != operation["ref"]
    ]


def _clear_groups(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.state.pop("group_by", None)


def _order_entry(operation: dict, index: int) -> dict:
    """One `order_by` entry.

    An absent direction is **refused**, not defaulted (D88). Ascending is the
    natural reading for a text attribute and descending by date for "the latest"
    (§17.1, §5.7) — both are deterministic in the attribute's *type*, which this
    module does not know and must not guess. Defaulting to `asc` would put a
    plausible wrong ordering on every date, and "the latest five orders" sorted
    ascending returns the five oldest: an answer that looks right and is exactly
    backwards.

    Whoever knows the type — the Resolver, which holds the dictionary — derives
    the direction and declares its rule. That is P4 applied here: information
    derivable deterministically is not asked of the model, and information this
    component cannot derive is not invented by it either.
    """
    direction = operation.get("direction")
    if direction is None:
        raise ApplicationError(
            f"operations[{index}]: {operation['op']} without a direction. It is "
            "derivable from the attribute's type — ascending for text, descending "
            "by date — and the type lives in the Semantic Dictionary, not here "
            "(D88). Resolve it before applying"
        )
    entry = {"ref": operation["ref"], "direction": direction, **_metadata(operation)}
    if entry["origin"] == "inferred":
        # §10.2: an inference declares the rule that produced it, or the user cannot
        # contradict it. The rule is **not** carried by the operation — §15.3 rejects
        # unknown keys there, and an operation is a request, not an explanation — so
        # it is derived from what the direction already says: descending was inferred
        # because the attribute is a date, ascending because it is not (D88, D99).
        entry["rule"] = RULE_LATEST_DESC if direction == "desc" else RULE_TEXT_ASC
    return entry


def _set_order(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    # §6.5: replacing is the default behaviour. "Sort by city" is what a person
    # means; multiple ordering exists but has to be asked for.
    result.state["order_by"] = [_order_entry(operation, index)]


def _add_order(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    entry = _order_entry(operation, index)
    existing = [e for e in state.get("order_by", []) if e.get("ref") != entry["ref"]]
    state["order_by"] = [*existing, entry]


def _clear_order(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.state.pop("order_by", None)


def _measure_key(entry: dict) -> tuple[str, str | None]:
    return entry.get("function", ""), entry.get("ref")


def _add_measure(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    entry = {"function": operation["function"], **_metadata(operation)}
    if "ref" in operation:
        entry["ref"] = operation["ref"]
    measures = list(state.get("measures", []))
    if any(_measure_key(existing) == _measure_key(entry) for existing in measures):
        state["measures"] = measures
        return
    state["measures"] = [*measures, entry]


def _remove_measure(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    state = result.state
    if "ref" in operation:
        keep = lambda entry: entry.get("ref") != operation["ref"]
    else:
        keep = lambda entry: entry.get("function") != operation["function"]
    state["measures"] = [entry for entry in state.get("measures", []) if keep(entry)]


def _set_limit(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    # The ceiling is a level 5 concern (§12.6): exceeding it produces an outcome
    # for the user with a proposal to narrow, not a value quietly clamped to the
    # maximum. Clamping here would answer a different question than the one asked.
    result.state["limit"] = {"value": operation["value"], **_metadata(operation)}


# ---------------------------------------------------------------------------
# Family 5 — session and navigation
# ---------------------------------------------------------------------------

def _reset(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.state.clear()
    result.state.update(state_module.empty_state())


def _revert_last(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.revert_requested = True


def _open_record(result: Result, operation: dict, limits: Limits, defaults, index: int) -> None:
    result.navigations.append(Navigation(selector=copy.deepcopy(operation["selector"])))


_HANDLERS = {
    "set_target": _set_target,
    "add_condition": _add_condition,
    "replace_condition": _replace_condition,
    "remove_condition": _remove_condition,
    "clear_filter": _clear_filter,
    "add_field": _add_field,
    "remove_field": _remove_field,
    "set_fields": _set_fields,
    "clear_fields": _clear_fields,
    "set_view": _set_view,
    "add_group": _add_group,
    "remove_group": _remove_group,
    "clear_groups": _clear_groups,
    "set_order": _set_order,
    "add_order": _add_order,
    "clear_order": _clear_order,
    "add_measure": _add_measure,
    "remove_measure": _remove_measure,
    "set_limit": _set_limit,
    "reset": _reset,
    "revert_last": _revert_last,
    "open_record": _open_record,
}


# ---------------------------------------------------------------------------
# Normalisation of the exercise form (§4.5 rule 4)
# ---------------------------------------------------------------------------

def derive_view(state: dict) -> tuple[str, str]:
    """The view and the identifier of the rule that produced it (§6.7).

    Deterministic and versioned: these are not an engine heuristic, they are part
    of the contract, and changing one changes the view of states already saved.

    The calendar view is never inferred. A temporal attribute does not imply the
    user wants a calendar; it implies the data has a date. Switching to a calendar
    changes how the result reads, and doing that unasked produces the
    disorientation that erodes trust.
    """
    measures = state.get("measures") or []
    groups = state.get("group_by") or []
    if measures and len(groups) >= 2:
        return "pivot", "measures_multi_group_implies_pivot"
    if measures and len(groups) == 1:
        return "graph", "measures_single_group_implies_graph"
    if measures:
        return "list", "measures_without_group_implies_list"
    if groups:
        return "list", "grouping_without_measure_implies_list"
    return "list", "default_list"


def reduce_filter(node: dict | None) -> dict | None:
    """§14.3 rule 4: a connective with one child becomes the child; nested
    connectives of the same type are flattened.

    Applied to the exercise form too, not only to the canonical one: the
    interpretation shown to the user must not contain `all(all(x))`, which says
    nothing and reads as complexity the user did not create.
    """
    if node is None:
        return None
    if not state_module.is_connective(node):
        return node

    children: list[dict] = []
    for child in node.get("conditions", []):
        reduced = reduce_filter(child)
        if reduced is None:
            continue
        if (
            state_module.is_connective(reduced)
            and reduced["connective"] == node["connective"]
            and node["connective"] != "not"
        ):
            children.extend(reduced["conditions"])
        else:
            children.append(reduced)

    if not children:
        return None
    if len(children) == 1 and node["connective"] != "not":
        return children[0]
    return {**node, "conditions": children}


def normalise(state: dict, *, limits: Limits = DEFAULT_LIMITS) -> dict:
    """Bring a state into the normalised **exercise** form.

    The three rules of §14.3 that apply to the persisted form: connective
    reduction (4), materialisation of the effective limit and view (5), removal of
    empty sections (7). Metadata and insertion order are kept — that is what
    distinguishes this from `contract.canonical`, and §14.2 is why.
    """
    normalised = copy.deepcopy(state)

    reduced = reduce_filter(normalised.get("filter"))
    if reduced is None:
        normalised.pop("filter", None)
    else:
        normalised["filter"] = reduced

    for section in state_module.LIST_SECTIONS:
        if section in normalised and not normalised[section]:
            # Rule 7: a section with no elements is absent, never present and
            # empty. The one exception is `fields`, where the distinction carries
            # meaning (§5.5) and an empty list must survive to be refused by
            # validation.
            if section != "fields":
                normalised.pop(section)

    # Rule 5: the effective limit and view are always present, even when derived.
    # §15.7: this is what makes a change to the derivation rules apply to future
    # interpretations and not to the past.
    if "limit" not in normalised:
        normalised["limit"] = {"value": limits.default_records, "origin": "default"}

    presentation = normalised.get("presentation")
    if not presentation or presentation.get("origin") != "user":
        view, rule = derive_view(normalised)
        normalised["presentation"] = {"view": view, "origin": "inferred", "rule": rule}

    return normalised


#: The five derivation rules, exposed for the tests that check this module against
#: the table of §6.7 rather than against itself.
DERIVATION_RULES = VIEW_DERIVATION_RULES
