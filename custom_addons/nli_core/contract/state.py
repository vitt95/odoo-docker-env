"""The Interrogation State: shape, constructors and read-only helpers.

The state is represented as plain JSON-shaped dictionaries rather than a parallel
class hierarchy, for a reason that is part of the design and not a shortcut: the
normative form of the contract **is** JSON (D11, §18.1). A class hierarchy would
be a second representation to keep in step with the first, and validity would
become a property of construction — while §12 requires it to be an explicit
phase with five levels and typed failures. A state that cannot be built cannot
be reported as invalid to the user.

**Pure zone.** Every function here is a function of its arguments.

Section shapes (§5.2), all keys normative:

    {
      "dsl_version": "1.0",
      "target":     {"ref": str, "origin": origin, "provenance"?: {...}},
      "filter"?:    <node>,
      "fields"?:    [{"ref": str, "origin": origin, ...}],
      "group_by"?:  [{"ref": str, "granularity"?: str, "origin": origin, ...}],
      "measures"?:  [{"function": str, "ref"?: str, "origin": origin, ...}],
      "order_by"?:  [{"ref": str, "direction": str, "origin": origin, "rule"?: str}],
      "limit":      {"value": int, "origin": origin, "rule"?: str},
      "presentation": {"view": str, "origin": origin, "rule"?: str}
    }

    <node> ::= {"connective": "all"|"any"|"not", "conditions": [<node>]}
             | {"id": str, "ref": str, "predicate": str, "value"?: {...},
                "origin": origin, "provenance"?: {...}, "confidence"?: float}
"""

from __future__ import annotations

from typing import Iterator

from .vocabulary import DSL_VERSION

#: Section order, used by the canonical form and by section-by-section comparison
#: (§14.5). It is the reading order of §5.2, which is also the order the
#: interpretation is shown in.
SECTIONS: tuple[str, ...] = (
    "target",
    "filter",
    "fields",
    "group_by",
    "measures",
    "order_by",
    "limit",
    "presentation",
)

#: Sections that are lists of references.
LIST_SECTIONS: tuple[str, ...] = ("fields", "group_by", "measures", "order_by")

#: Sections `set_target` with a different entity resets (§6.2, restart rule).
SECTIONS_CLEARED_ON_TARGET_CHANGE: tuple[str, ...] = (
    "filter",
    "fields",
    "group_by",
    "measures",
    "order_by",
)


def empty_state() -> dict:
    """The state a conversation starts from.

    Deliberately without `target`: the first request is a sequence of operations
    applied to the empty state, so there is no special case for the opening turn
    (§4.3). The empty state is the identity element of application, not a valid
    state — `target` is mandatory (§5.2) and its absence is reported by
    validation, not prevented by construction.
    """
    return {"dsl_version": DSL_VERSION}


def is_connective(node: dict) -> bool:
    """True for an internal node of the filter tree, false for a condition."""
    return "connective" in node


def walk(node: dict | None) -> Iterator[dict]:
    """Every node of a filter tree, connectives included, parents before children."""
    if not node:
        return
    yield node
    if is_connective(node):
        for child in node.get("conditions", []):
            yield from walk(child)


def conditions(node: dict | None) -> Iterator[dict]:
    """Every leaf condition of a filter tree, in reading order."""
    for candidate in walk(node):
        if not is_connective(candidate):
            yield candidate


def depth(node: dict | None) -> int:
    """Depth of a filter tree: a lone condition has depth 1, an empty filter 0.

    Counted over connectives *and* leaves because the limit of §5.4 is what a
    person can verify at a glance, and a leaf is a level of that reading.
    """
    if not node:
        return 0
    if not is_connective(node):
        return 1
    children = node.get("conditions", [])
    if not children:
        return 1
    return 1 + max(depth(child) for child in children)


def condition_ids(state: dict) -> list[str]:
    """Identifiers of every condition in the state, in reading order."""
    return [
        condition["id"]
        for condition in conditions(state.get("filter"))
        if "id" in condition
    ]


def find_condition(state: dict, condition_id: str) -> dict | None:
    for condition in conditions(state.get("filter")):
        if condition.get("id") == condition_id:
            return condition
    return None


def next_condition_id(state: dict) -> str:
    """The next stable condition identifier, derived from the state alone.

    Derived rather than generated: a random or time-based identifier would make
    the Applicator non-deterministic, and the stable identifier is what lets the
    user remove one condition from the interpretation without rephrasing the
    whole sentence (§5.4).
    """
    used = 0
    for identifier in condition_ids(state):
        if identifier.startswith("c") and identifier[1:].isdigit():
            used = max(used, int(identifier[1:]))
    return f"c{used + 1}"


def references(state: dict) -> list[str]:
    """Every semantic reference the state names, in section order.

    Used by resolution (level 3, part 4) and by catalogue coverage (D34). It is
    here rather than there because it is a property of the state's shape, and the
    shape is defined here.
    """
    found: list[str] = []
    target = state.get("target")
    if isinstance(target, dict) and "ref" in target:
        found.append(target["ref"])
    for condition in conditions(state.get("filter")):
        if "ref" in condition:
            found.append(condition["ref"])
    for section in LIST_SECTIONS:
        for entry in state.get(section, []):
            if isinstance(entry, dict) and "ref" in entry:
                found.append(entry["ref"])
    return found


def relation_hops(ref: str) -> int:
    """Relation hops in a semantic reference (§7.3).

    `orders` is 0, `orders.state` is 0 — an attribute is not a hop —
    `orders.customer.city` is 1, `orders.customer.country.code` is 2.
    """
    segments = ref.split(".")
    return max(0, len(segments) - 2)
