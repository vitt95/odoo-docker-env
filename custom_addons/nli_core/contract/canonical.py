"""The canonical form (§14.3) — the reason accuracy can be measured at all.

**Pure zone**, and of everything in the pure zone this is the module whose
determinism matters most: it is the measuring instrument of `07`. An instrument
whose reading depends on when it was taken cannot detect a regression, and a
regression it cannot detect is one that ships.

Two forms of the same state (§14.2):

* the **exercise form** — presentation, editing, persistence — keeps insertion
  order, identifiers, origin, provenance and confidence, because that is the order
  the interpretation is shown in and reordering it would disorient the user;
* the **canonical form** — comparison, deduplication, memoisation — keeps only
  what the interrogation asks.

**On rule 1, which is the delicate one.** Removing `origin` makes two states that
differ only in *who decided* the ordering — the user or an inference — equivalent.
That is correct for measuring interpretive accuracy: the interrogation is the same
and returns the same records. It is also incomplete, and §14.3 says so: a system
that inferred everything correctly and never declared an origin would violate P3
while scoring perfectly on this metric. Provenance correctness is a **separate
indicator** (D53), never folded into accuracy.
"""

from __future__ import annotations

import copy
import json
import unicodedata
from typing import Any

from . import state as state_module
from .vocabulary import DEFAULT_LIMITS, PREDICATES_WITHOUT_VALUE, Limits

#: Keys removed by rule 1: they describe *how* the interrogation was arrived at,
#: not *what* it asks.
METADATA_KEYS = frozenset({"origin", "provenance", "confidence", "rule", "id"})

#: Sections whose order is semantic and must survive canonicalisation.
#: `fields` is the presentation order (§5.5); `group_by` levels are nested in
#: order (§5.6); `order_by` is a sequence of tie-breakers (§5.7). Reordering any
#: of them would change the result, so rule 2 applies to conditions only.
ORDERED_SECTIONS = frozenset({"fields", "group_by", "order_by", "measures"})


def normalise_text(text: str) -> str:
    """Rule 6: unicode and whitespace normalisation, case-insensitive comparison.

    NFC rather than NFD so that a precomposed and a decomposed accent compare
    equal; `casefold` rather than `lower` because it is the operation defined for
    caseless matching across scripts, and the corpus deliberately contains
    accent-stripped and lowercased perturbations (D83).
    """
    collapsed = " ".join(unicodedata.normalize("NFC", text).split())
    return collapsed.casefold()


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict = {}
        for key, item in value.items():
            if key in METADATA_KEYS:
                continue
            result[key] = _canonical_value(item)
        # Rule 3: the elements of a set are ordered. `is_one_of` and `enum` name
        # an unordered set, and two identical sets written in different orders are
        # the same condition — without this rule the corpus would penalise a
        # correct interpretation for its word order.
        items = result.get("items")
        if isinstance(items, list):
            result["items"] = sorted(items, key=_sort_key)
        return result
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, str):
        return normalise_text(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        # 1000 and 1000.0 are the same threshold. Keeping both forms would make an
        # equal interrogation compare unequal for a reason that has nothing to do
        # with interpretation.
        return int(value)
    return value


def _sort_key(value: Any) -> tuple:
    """A total order over JSON values, so sorting never depends on insertion order.

    Typed prefix first: comparing a number with a string raises in Python 3, and a
    canonicalisation that raises on a valid state is worse than one that orders
    oddly.
    """
    if isinstance(value, bool):
        return (0, str(value))
    if isinstance(value, (int, float)):
        return (1, float(value))
    if isinstance(value, str):
        return (2, value)
    if isinstance(value, list):
        return (3, tuple(_sort_key(item) for item in value))
    if isinstance(value, dict):
        return (4, tuple((key, _sort_key(value[key])) for key in sorted(value)))
    return (5, "")


def _condition_sort_key(node: dict) -> tuple:
    """Rule 2: the total order on conditions, defined on reference, predicate, value.

    Connectives sort after conditions and among themselves by their rendered
    content, so a tree with nested connectives has one canonical shape rather than
    one per traversal order.
    """
    if state_module.is_connective(node):
        return (
            1,
            node.get("connective", ""),
            "",
            _sort_key([_condition_sort_key(c) for c in node.get("conditions", [])]),
        )
    return (
        0,
        node.get("ref", ""),
        node.get("predicate", ""),
        _sort_key(node.get("value")),
    )


def _canonical_filter(node: dict | None) -> dict | None:
    if node is None:
        return None
    if not state_module.is_connective(node):
        canonical = _canonical_value(node)
        assert isinstance(canonical, dict)
        if canonical.get("predicate") in PREDICATES_WITHOUT_VALUE:
            # A predicate that is the whole condition carries no information in a
            # value. §17.1 writes `is_true` with one anyway, so both shapes exist
            # and C8 requires them to canonicalise to the same thing.
            canonical.pop("value", None)
        return canonical

    children: list[dict] = []
    for child in node.get("conditions", []):
        reduced = _canonical_filter(child)
        if reduced is None:
            continue
        # Rule 4: flatten nested connectives of the same type.
        if (
            state_module.is_connective(reduced)
            and reduced.get("connective") == node.get("connective")
            and node.get("connective") != "not"
        ):
            children.extend(reduced["conditions"])
        else:
            children.append(reduced)

    if not children:
        return None
    # Rule 4: a connective with a single child is replaced by the child. `not` is
    # unary, so it is never reduced away.
    if len(children) == 1 and node.get("connective") != "not":
        return children[0]
    return {
        "connective": node.get("connective"),
        "conditions": sorted(children, key=_condition_sort_key),
    }


def canonicalise(state: dict, *, limits: Limits = DEFAULT_LIMITS) -> dict:
    """The canonical form of a state — the object accuracy is measured on.

    Idempotent by construction: `canonicalise(canonicalise(s)) == canonicalise(s)`.
    The property is asserted by the tests, because a canonicalisation that is not
    idempotent turns comparison into a function of how many times it ran.
    """
    canonical: dict = {"dsl_version": state.get("dsl_version")}

    # Every section below accepts both the exercise form and the canonical form as
    # input. That is what makes the function a fixed point: `canonicalise` applied
    # to its own output must return it unchanged, or comparison becomes a function
    # of how many times it ran.
    target = state.get("target")
    if isinstance(target, dict) and "ref" in target:
        canonical["target"] = normalise_text(target["ref"])
    elif isinstance(target, str):
        canonical["target"] = normalise_text(target)

    filtered = _canonical_filter(state.get("filter"))
    if filtered is not None:
        canonical["filter"] = filtered

    for section in state_module.LIST_SECTIONS:
        entries = state.get(section)
        if not entries:
            # Rule 7: a section with no elements is absent, never present and empty.
            continue
        canonical[section] = [_canonical_value(entry) for entry in entries]

    # Rule 5: the effective limit and view are always present, even when derived.
    limit = state.get("limit")
    if isinstance(limit, dict):
        canonical["limit"] = limit.get("value", limits.default_records)
    elif isinstance(limit, int) and not isinstance(limit, bool):
        canonical["limit"] = limit
    else:
        canonical["limit"] = limits.default_records

    presentation = state.get("presentation")
    if isinstance(presentation, dict):
        canonical["presentation"] = presentation.get("view", "list")
    elif isinstance(presentation, str):
        canonical["presentation"] = presentation
    else:
        canonical["presentation"] = "list"

    return canonical


def canonical_json(state: dict, *, limits: Limits = DEFAULT_LIMITS) -> str:
    """A byte-stable rendering of the canonical form.

    What identity (§14.4) is computed on: two states are identical when this
    string is. Callers that need a short key hash this — hashing lives outside the
    pure zone so that the zone's only job stays "same input, same output".
    """
    return json.dumps(
        canonicalise(state, limits=limits),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def identical(left: dict, right: dict, *, limits: Limits = DEFAULT_LIMITS) -> bool:
    """§14.4 identity: equal canonical forms."""
    return canonicalise(left, limits=limits) == canonicalise(right, limits=limits)


def section_comparison(
    expected: dict,
    produced: dict,
    *,
    limits: Limits = DEFAULT_LIMITS,
) -> dict[str, bool]:
    """Section-by-section agreement (§14.5).

    Knowing overall accuracy is 87% says nothing about where to work. Knowing the
    entity is right 99% of the time, filters 91% and groupings 76% says exactly
    where. D44 turns the same decomposition into a gate: a per-section threshold,
    because a whole-corpus threshold lets groupings at 62% through.
    """
    left = canonicalise(expected, limits=limits)
    right = canonicalise(produced, limits=limits)
    keys = ("target", "filter", "fields", "group_by", "measures", "order_by",
            "limit", "presentation")
    return {key: left.get(key) == right.get(key) for key in keys}


def permutations_of_conditions(state: dict) -> list[dict]:
    """Variants of a state with the conditions of each connective reordered.

    Not a helper for production code: it exists so the stability property of the
    canonical form can be *tested* rather than asserted. The corpus harness uses
    it on all 948 `operations` cases.
    """
    variants: list[dict] = []
    for node in state_module.walk(state.get("filter")):
        if not state_module.is_connective(node) or len(node.get("conditions", [])) < 2:
            continue
        variant = copy.deepcopy(state)
        for candidate in state_module.walk(variant.get("filter")):
            if (
                state_module.is_connective(candidate)
                and candidate.get("connective") == node.get("connective")
                and len(candidate.get("conditions", [])) == len(node["conditions"])
            ):
                candidate["conditions"] = list(reversed(candidate["conditions"]))
                break
        variants.append(variant)
    return variants
