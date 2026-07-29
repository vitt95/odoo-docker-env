"""Levels 3 to 5, the half that needs the dictionary (§12.4-12.6).

**Pure zone.** The dictionary arrives as two lookup tables — the type of each
reference, and the cost class of each category — so resolution here is a lookup, not
a database call. That is what keeps the levels testable without an ORM, and it is the
same split as everywhere else: the platform produces the tables, this decides.

## Level 3 is the valuable one

> Every failure at this level is **precious material**: it indicates a gap in the
> Semantic Dictionary, or a name users use and the dictionary does not know. It is
> registered as a candidate for enrichment, not only as an error. (§12.4)

And its second property is a security one. §7.4: a reference the user is not
authorised to see is **treated as unresolved**. Not "refused with an explanation" —
treated as though it did not exist, so that no refusal reveals the existence of an
attribute the user may not know about. The two cases are indistinguishable in the
outcome and distinguished only in the diagnostic log.
"""

from __future__ import annotations

from ..contract import state as state_module
from ..contract.failure import Failure
from ..contract.vocabulary import (
    AGGREGATION_TYPES,
    DEFAULT_LIMITS,
    PREDICATES_BY_TYPE,
    PREDICATES_WITHOUT_VALUE,
    Limits,
)

#: Attribute types a `granularity` may be applied to (§12.5).
TEMPORAL_TYPES = frozenset({"date", "datetime"})

#: Cost class of a category that aggregates over another entity (V-D87-2).
COST_AGGREGATE = "aggregate"

#: How many aggregating categories an interrogation may carry before level 5 refuses
#: it. **Declared parameter, not a constant**: one roll-up over a related entity is
#: an ordinary question — *"clienti importanti"* — and three in one filter is a
#: report. The value is recalibrated on the load test of `07` §7.2, and the indicator
#: to watch is how often it fires.
MAX_AGGREGATE_CATEGORIES = 1


def _failure(level: int, code: str, path: str, detail: str) -> Failure:
    return Failure(level=level, code=code, path=path, detail=detail)


def validate_resolution(state: dict, *, known_refs: frozenset[str]) -> list[Failure]:
    """Level 3 — every reference exists in the dictionary and is authorised.

    `known_refs` is the user's catalogue: built on their permissions, so a reference
    they may not read is simply not in it. The failure is the same in both cases, by
    design (§7.4).
    """
    failures: list[Failure] = []
    for reference in state_module.references(state):
        if reference in known_refs:
            continue
        failures.append(_failure(
            3, "unresolved_reference", reference,
            f"{reference!r} is not in this user's catalogue. Either the dictionary "
            "does not know the term — in which case this is a candidate enrichment "
            "(§12.4) — or the user may not read it, and the two are deliberately "
            "indistinguishable here (§7.4)",
        ))
    return failures


def validate_grounding(state: dict, *, mentions) -> list[Failure]:
    """Level 3 — a named condition must be grounded in what the user said (**D105**).

    **The failure this exists for.** Measured on 80 openings with `qwen3.5:9b`: twelve
    failures out of twenty-one were the same one — a fragment naming no condition at
    all turned into a named condition, because a named condition is the cheapest thing
    to write. No value, no `kind`, no expression.

        'voglio vedere ordini lo scorso mese'
          -> is_category(ordini_vendita.in_bozza), provenance "lo scorso mese"

    The provenance is the confession: §10.3 defines it as *the fragment of the sentence
    that produced this operation*, so a named condition whose fragment contains none of
    its terms is unfounded **by the contract's own definition** — and noticing it takes
    comparing two lists, not understanding Italian.

    **Why it compares against the provenance and not against the utterance.** A
    refinement turn carries forward the conditions of the previous turns, whose
    fragments belong to sentences nobody is saying any more. Checking them against the
    current utterance would reject the whole conversation at the second turn. The
    provenance travels with the condition, so the check is self-contained.

    **What this changes, said with the right sign.** It does not make the answer right:
    it makes the wrong one refused. Repairs go up, silently wrong filters go down, and
    accuracy may not move at all. That is the trade **D2** asks for — a wrong filter
    shows *fewer* records with confidence, and the user has no way to see it.

    `mentions(ref, text)` is injected because deciding what counts as *mentioning* a
    term belongs to the dictionary, which knows about accents, typos and abbreviations,
    and `nli_core` depends on nothing (`tools/arch/spec.py`).
    """
    failures: list[Failure] = []
    for condition in state_module.conditions(state.get("filter")):
        if condition.get("predicate") != "is_category":
            continue
        reference = condition.get("ref", "")
        text = ((condition.get("provenance") or {}).get("text") or "").strip()
        if text and mentions(reference, text):
            continue
        failures.append(_failure(
            3, "ungrounded_category", reference,
            f"the named condition {reference!r} is not mentioned by the fragment it "
            f"claims to come from ({text!r}); §10.3 defines the provenance as the "
            "fragment that produced the operation, so this condition was not asked "
            "for" if text else
            f"the named condition {reference!r} carries no provenance, so there is "
            "nothing that shows the user asked for it (§10.3)",
        ))
    return failures


def validate_types(state: dict, *, types: dict[str, str]) -> list[Failure]:
    """Level 4 — the half that needs the attribute's type (§12.5).

    Vincolarli nel contratto sposta l'errore dal momento dell'esecuzione, dove
    produce un risultato inatteso o un fallimento oscuro, al momento della
    validazione, dove produce una domanda comprensibile all'utente (§8.1).
    """
    failures: list[Failure] = []

    for condition in state_module.conditions(state.get("filter")):
        reference = condition.get("ref", "")
        predicate = condition.get("predicate")
        attribute_type = types.get(reference)
        if attribute_type is None:
            # Level 3 already reported it; saying it twice helps nobody.
            continue
        admitted = PREDICATES_BY_TYPE.get(attribute_type, frozenset())
        if predicate not in admitted:
            failures.append(_failure(
                4, "predicate_type_mismatch", reference,
                f"predicate {predicate!r} is not admitted on a {attribute_type!r} "
                f"attribute; admitted: {sorted(admitted)}",
            ))

    for index, entry in enumerate(state.get("group_by") or ()):
        if "granularity" not in entry:
            continue
        attribute_type = types.get(entry.get("ref", ""))
        if attribute_type is not None and attribute_type not in TEMPORAL_TYPES:
            failures.append(_failure(
                4, "granularity_on_non_temporal", f"group_by[{index}]",
                f"granularity {entry['granularity']!r} on a {attribute_type!r} "
                "attribute: only dates have one",
            ))

    for index, entry in enumerate(state.get("measures") or ()):
        function = entry.get("function")
        admitted = AGGREGATION_TYPES.get(function)
        if admitted is None:
            continue
        if not admitted:
            # `count` needs no attribute (§8.5).
            continue
        attribute_type = types.get(entry.get("ref", ""))
        if attribute_type is not None and attribute_type not in admitted:
            failures.append(_failure(
                4, "aggregation_type_mismatch", f"measures[{index}]",
                f"{function!r} is not admitted on a {attribute_type!r} attribute; "
                f"admitted: {sorted(admitted)}",
            ))

    return failures


def validate_cost(
    state: dict,
    *,
    category_costs: dict[str, str],
    limits: Limits = DEFAULT_LIMITS,
) -> list[Failure]:
    """Level 5 — the half that needs the dictionary: what the categories cost.

    **V-D87-2.** A category can hide an aggregate over another entity — *"clienti
    importanti"* is *revenue over the last twelve months above 50 000* — and D12 exists
    so that cost is computable a priori rather than estimated. Without this the
    estimate would be silently wrong for exactly the conditions that are expensive.

    An unsustainable interrogation is not a performance problem: it is a problem of
    availability for every other user (§12.6). The outcome is a message with a
    proposal to narrow, never a query left to run into a timeout.
    """
    failures: list[Failure] = []
    aggregating = [
        condition.get("ref", "")
        for condition in state_module.conditions(state.get("filter"))
        if category_costs.get(condition.get("ref", "")) == COST_AGGREGATE
    ]
    if len(aggregating) > MAX_AGGREGATE_CATEGORIES:
        failures.append(_failure(
            5, "too_many_aggregate_categories", "filter",
            f"{len(aggregating)} categories aggregate over another entity "
            f"({sorted(aggregating)}); at most {MAX_AGGREGATE_CATEGORIES} is "
            "sustainable. The answer is to narrow, or to move to pivot and export",
        ))
    return failures


def validate(
    state: dict,
    *,
    known_refs: frozenset[str],
    types: dict[str, str],
    category_costs: dict[str, str] | None = None,
    mentions=None,
    limits: Limits = DEFAULT_LIMITS,
) -> list[Failure]:
    """Levels 3, 4 and 5 in sequence; the first that fails stops the chain (§12.2).

    Level 4 is not run on references level 3 could not resolve: a type read from a
    reference that does not exist is not a type, and reporting both would bury the
    one failure that carries a remedy under one that does not.

    `mentions` omitted means the grounding of D105 is **not checked**. It is optional
    only because a caller with no dictionary at hand — a test on the contract alone —
    has nothing to check it with; every caller that has one passes it, and the
    pipeline is the one that matters.
    """
    level3 = validate_resolution(state, known_refs=known_refs)
    if level3:
        return level3
    if mentions is not None:
        # Same level: both ask whether what the state names exists in the user's
        # world. One asks whether the reference exists, the other whether the user
        # asked for it.
        grounding = validate_grounding(state, mentions=mentions)
        if grounding:
            return grounding
    level4 = validate_types(state, types=types)
    if level4:
        return level4
    return validate_cost(state, category_costs=category_costs or {}, limits=limits)
