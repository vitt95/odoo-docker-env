"""The registry of semantic equivalences (D43, §14.4).

Two canonical forms can differ while asking provably the same question. §8.1
minimises those cases by removing redundant forms from the vocabulary — there is
no `not_equals`, precisely so that one condition has one shape — but it cannot
remove them all, and where they remain the measurement must recognise them or it
penalises correct interpretations and reports a threshold lower than the truth
(RC5).

**Why this is a closed, versioned registry and not a similarity function.** D43
makes adding an entry a modification of the contract. The alternative — an open
notion of "close enough" — is the place where the accuracy threshold moves
without anyone declaring it: every disputed case becomes a candidate rule, the
rules accumulate, and the measurement drifts upwards while the product stands
still. A registry with a version and a diff cannot do that quietly.

**Pure zone.**

The two entries of version 1.0 both exist because the contract itself creates
them; neither is a concession to a model's phrasing:

* **E1** — `between` against the conjunction of two bounds. §14.4 names this case
  explicitly;
* **E2** — `is_not_one_of` against `not(is_one_of)`. §8.1 keeps `is_not_one_of`
  as the single exception to expressing negation with the `not` connective,
  because *"all except draft and cancelled"* is frequent and reads badly as a
  tree. Keeping both forms is a deliberate trade, and this entry is its cost.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable

from . import canonical as canonical_module
from . import state as state_module
from .vocabulary import DEFAULT_LIMITS, Limits

#: Version of the registry. Independent of `dsl_version`: a new equivalence does
#: not change what can be expressed, it changes what counts as equal — which is a
#: change to the measurement, and has to be citable in a report of `07`.
REGISTRY_VERSION = "1.0"

LOWER_BOUNDS = {"greater_or_equal": "from"}
UPPER_BOUNDS = {"less_or_equal": "to"}


@dataclass(frozen=True)
class Equivalence:
    """One declared equivalence, with the direction it normalises towards."""

    identifier: str
    description: str
    #: Why the two forms both exist. An equivalence without this line is a
    #: tolerance nobody argued for.
    rationale: str
    rewrite: Callable[[dict], dict]


def _rewrite_bounds(node: dict) -> dict:
    """E1: `all(X >= a, X <= b)` becomes `X between [a, b]`.

    `between` is chosen as the normal form because it is the form §14.4 writes
    first and the form the interpretation shows the user — *"amount between 1.000
    and 5.000"* rather than two lines that have to be read together.
    """
    if not state_module.is_connective(node) or node.get("connective") != "all":
        return node

    children = list(node.get("conditions", []))
    lowers: dict[str, tuple[int, dict]] = {}
    uppers: dict[str, tuple[int, dict]] = {}
    for index, child in enumerate(children):
        if state_module.is_connective(child):
            continue
        predicate = child.get("predicate")
        ref = child.get("ref")
        if predicate in LOWER_BOUNDS and ref is not None:
            lowers[ref] = (index, child)
        elif predicate in UPPER_BOUNDS and ref is not None:
            uppers[ref] = (index, child)

    merged: dict[int, dict] = {}
    dropped: set[int] = set()
    for ref, (low_index, low) in lowers.items():
        if ref not in uppers:
            continue
        high_index, high = uppers[ref]
        low_value = (low.get("value") or {}).get("value")
        high_value = (high.get("value") or {}).get("value")
        if low_value is None or high_value is None:
            continue
        merged[min(low_index, high_index)] = {
            "ref": ref,
            "predicate": "between",
            "value": {"kind": "range", "from": low_value, "to": high_value},
        }
        dropped.update({low_index, high_index})

    if not merged:
        return node

    rebuilt: list[dict] = []
    for index, child in enumerate(children):
        if index in merged:
            rebuilt.append(merged[index])
        elif index not in dropped:
            rebuilt.append(child)
    return {**node, "conditions": rebuilt}


def _rewrite_negated_enum(node: dict) -> dict:
    """E2: `not(X is_one_of S)` becomes `X is_not_one_of S`."""
    if not state_module.is_connective(node) or node.get("connective") != "not":
        return node
    children = node.get("conditions", [])
    if len(children) != 1:
        return node
    child = children[0]
    if state_module.is_connective(child) or child.get("predicate") != "is_one_of":
        return node
    value = child.get("value") or {}
    if value.get("kind") != "enum":
        return node
    return {**child, "predicate": "is_not_one_of"}


#: The registry. Closed: extending it is a modification of the contract (D43).
REGISTRY: tuple[Equivalence, ...] = (
    Equivalence(
        identifier="E1",
        description="between(a, b) == greater_or_equal(a) AND less_or_equal(b)",
        rationale=(
            "Named in §14.4. Both forms survive because a range and a pair of "
            "bounds are the same question, and a model may phrase either."
        ),
        rewrite=_rewrite_bounds,
    ),
    Equivalence(
        identifier="E2",
        description="is_not_one_of(S) == not(is_one_of(S))",
        rationale=(
            "§8.1 keeps is_not_one_of as the single exception to expressing "
            "negation with the 'not' connective, so the contract itself admits "
            "two shapes for one condition."
        ),
        rewrite=_rewrite_negated_enum,
    ),
)


def _apply_registry(node: dict | None, registry: tuple[Equivalence, ...]) -> dict | None:
    if node is None:
        return None
    if not state_module.is_connective(node):
        return node

    rewritten = {
        **node,
        "conditions": [
            child
            for child in (_apply_registry(c, registry) for c in node.get("conditions", []))
            if child is not None
        ],
    }
    for entry in registry:
        rewritten = entry.rewrite(rewritten)
        if not state_module.is_connective(rewritten):
            return rewritten
    return rewritten


def normal_form(
    state: dict,
    *,
    registry: tuple[Equivalence, ...] = REGISTRY,
    limits: Limits = DEFAULT_LIMITS,
) -> dict:
    """The canonical form with the registry's rewrites applied to a fixed point.

    Canonicalisation runs again afterwards because a rewrite changes the sort key
    of what it produced: `between` is not where the two bounds were.
    """
    current = canonical_module.canonicalise(state, limits=limits)
    for _ in range(len(registry) + 1):
        rewritten = copy.deepcopy(current)
        reduced = _apply_registry(rewritten.get("filter"), registry)
        if reduced is None:
            rewritten.pop("filter", None)
        else:
            rewritten["filter"] = reduced
        rewritten = canonical_module.canonicalise(rewritten, limits=limits)
        if rewritten == current:
            return current
        current = rewritten
    return current


def equivalent(
    left: dict,
    right: dict,
    *,
    registry: tuple[Equivalence, ...] = REGISTRY,
    limits: Limits = DEFAULT_LIMITS,
) -> bool:
    """§14.4 semantic equivalence: equal normal forms.

    Note what is **not** here: equivalence of outcome — the same set of records
    returned. §14.4 excludes it explicitly, and the reason is worth repeating
    because it looks like the most practical criterion available. Two different
    interrogations return the same records whenever the data is not discriminating
    — which is exactly the situation in a test environment, where the data is
    sparse. Using it would build a metric that improves while the product gets
    worse.
    """
    return normal_form(left, registry=registry, limits=limits) == normal_form(
        right, registry=registry, limits=limits
    )
