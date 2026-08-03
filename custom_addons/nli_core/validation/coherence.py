"""Levels 4 and 5, the half that needs no dictionary (§12.5, §12.6).

**Pure zone.** Level 4 asks whether individually valid elements combine into
something meaningful, and level 5 whether the result is affordable. Both questions
split cleanly in two:

* the checks that need only the artefact — tree depth, number of groupings,
  measures against the view, two operations setting the same element to different
  values, a limit above the absolute ceiling, a reference with too many relation
  hops. They are here, and they run in part 2 without an ORM;
* the checks that need the **attribute's type**, and therefore the Semantic
  Dictionary — `contains` on a number, `sum` on text, `granularity: month` on
  something that is not a date. They belong to `contextual.py`, with resolution,
  in part 4.

Keeping the split explicit matters: the completion criterion of this part
includes "incoherent cases are rejected", and half of level 4 can honour it today.
Pretending the other half is done would be worse than not having it.

**A contradiction in the specification, resolved by D89.** §5.6 and §12.5 both say
a state with `measures` and the `list` view is invalid. §6.7 rule 3 derives
exactly that state: measures present, no grouping, view `list`. Taken literally the
Applicator would produce a state the Validator must refuse.

D89 rules that §6.7 rule 3 stands, and that the prohibition applies where the two
statements do not overlap: **measures with at least one grouping and the `list`
view**. That is the case §5.6 is about — an aggregation broken down by a dimension,
shown as a flat list, loses the breakdown. A measure with no grouping is one
aggregate row, which a list shows perfectly well.

The deciding argument is not that rule 3 is more specific. It is that the two
readings fail differently: this one shows an answer plus rows nobody asked for,
recoverable in one sentence, while the other **refuses** a request Odoo's own list
view satisfies natively in its column footers — and refusing a native behaviour
contradicts the additive-product principle of `02` §4.6. A reading that can
withhold an answer loses to one that cannot.
"""

from __future__ import annotations

from ..contract import state as state_module
from ..contract.failure import Failure
from ..contract.vocabulary import (
    DEFAULT_LIMITS,
    OPS_EXCLUSIVE,
    PREDICATE_ASSERTED_BOOLEAN,
    PREDICATE_VALUE_KINDS,
    PREDICATES_WITHOUT_VALUE,
    Limits,
)

#: Operations that set a singleton element of the state. Two of them in one
#: envelope with different payloads is the incoherence §4.5 names.
SINGLETON_SETTERS: dict[str, tuple[str, ...]] = {
    "set_target": ("ref",),
    "set_limit": ("value",),
    "set_view": ("view",),
    "set_fields": ("refs",),
    "set_order": ("ref", "direction"),
}


def _failure(level: int, code: str, path: str, detail: str) -> Failure:
    return Failure(level=level, code=code, path=path, detail=detail)


# ---------------------------------------------------------------------------
# Level 4 — coherence of the envelope
# ---------------------------------------------------------------------------

def validate_envelope_coherence(
    operations: list[dict],
    *,
    state: dict | None = None,
) -> list[Failure]:
    """Internal coherence of one envelope (§4.5, §12.5).

    `state` is the state the operations will be applied to, when it is known: it
    is what makes `replace_condition` on an absent identifier detectable before
    application rather than as an exception during it.
    """
    failures: list[Failure] = []

    if len(operations) > 1:
        for index, operation in enumerate(operations):
            if operation.get("op") in OPS_EXCLUSIVE:
                failures.append(_failure(
                    4,
                    "operation_not_composable",
                    f"operations[{index}]",
                    f"'{operation['op']}' must be the only operation of its "
                    "envelope: composed, its result depends on where in the "
                    "sequence it is read",
                ))

    seen: dict[str, tuple[int, tuple]] = {}
    for index, operation in enumerate(operations):
        verb = operation.get("op")
        if verb not in SINGLETON_SETTERS:
            continue
        payload = tuple(
            _hashable(operation.get(key)) for key in SINGLETON_SETTERS[verb]
        )
        if verb in seen and seen[verb][1] != payload:
            first, _ = seen[verb]
            failures.append(_failure(
                4,
                "conflicting_operations",
                f"operations[{index}]",
                f"'{verb}' already appears at operations[{first}] with a "
                "different value. This is not a conflict to resolve with a "
                "precedence rule: it is the signal of an incoherent "
                "interpretation (§4.5)",
            ))
        seen.setdefault(verb, (index, payload))

    for index, operation in enumerate(operations):
        # The predicate and the kind of value are both contract symbols, so their
        # compatibility needs no dictionary. The *attribute's* type does, and that
        # check lives in contextual.py.
        condition = operation.get("condition")
        if isinstance(condition, dict):
            failures.extend(
                _check_predicate_value(condition, f"operations[{index}].condition")
            )
        if operation.get("op") == "replace_condition" and state is not None:
            identifier = operation.get("id")
            if identifier is not None and state_module.find_condition(state, identifier) is None:
                failures.append(_failure(
                    4,
                    "unknown_condition",
                    f"operations[{index}].id",
                    f"no condition {identifier!r} in the current state",
                ))

    return failures


def _hashable(value):
    if isinstance(value, list):
        return tuple(_hashable(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _hashable(item)) for key, item in value.items()))
    return value


def _check_predicate_value(condition: dict, path: str) -> list[Failure]:
    predicate = condition.get("predicate")
    if predicate in PREDICATE_ASSERTED_BOOLEAN and "value" in condition:
        # The value is redundant and admitted (§17.1 writes it). A value that
        # contradicts the predicate is not redundancy, it is two statements: the
        # canonical form would keep one of them and drop the other.
        asserted = PREDICATE_ASSERTED_BOOLEAN[predicate]
        given = (condition.get("value") or {}).get("value")
        if given is not None and given != asserted:
            return [_failure(
                4,
                "contradictory_boolean",
                f"{path}.value.value",
                f"predicate '{predicate}' asserts {asserted}, the value says {given}",
            )]
    if predicate is None or predicate in PREDICATES_WITHOUT_VALUE:
        return []
    admitted = PREDICATE_VALUE_KINDS.get(predicate)
    if admitted is None:
        return []
    kind = (condition.get("value") or {}).get("kind")
    if kind is None or kind in admitted:
        return []
    return [_failure(
        4,
        "predicate_value_mismatch",
        f"{path}.value.kind",
        f"predicate '{predicate}' does not admit a {kind!r} value; admitted: "
        f"{sorted(admitted)}",
    )]


# ---------------------------------------------------------------------------
# Level 4 — coherence of the resulting state
# ---------------------------------------------------------------------------

def validate_coherence(state: dict, *, limits: Limits = DEFAULT_LIMITS) -> list[Failure]:
    """Dictionary-free level 4 checks on a state."""
    failures: list[Failure] = []

    depth = state_module.depth(state.get("filter"))
    if depth > limits.max_filter_depth:
        failures.append(_failure(
            4,
            "filter_too_deep",
            "filter",
            f"depth {depth} exceeds {limits.max_filter_depth}. Beyond that the "
            "interpretation cannot be verified at a glance, and the correct road "
            "is a clarification (§5.4)",
        ))

    groups = state.get("group_by") or []
    if len(groups) > limits.max_groups:
        failures.append(_failure(
            4,
            "too_many_groups",
            "group_by",
            f"{len(groups)} levels exceed {limits.max_groups} (D12)",
        ))

    measures = state.get("measures") or []
    view = (state.get("presentation") or {}).get("view")
    if measures and groups and view == "list":
        failures.append(_failure(
            4,
            "measures_with_list_view",
            "presentation.view",
            "measures broken down by a grouping cannot be shown as a flat list: "
            "the breakdown is lost (§5.6). Expected 'graph' or 'pivot' per §6.7",
        ))

    for condition in state_module.conditions(state.get("filter")):
        failures.extend(_check_predicate_value(condition, "filter"))

    failures.extend(_check_one_period_per_attribute(state))

    return failures


#: Predicati che collocano un attributo in un intervallo di tempo. Due di questi sullo
#: stesso attributo non si sommano: si contraddicono.
_PERIOD_PREDICATES = frozenset({"within", "before", "after", "between"})


def _check_one_period_per_attribute(state: dict) -> list[Failure]:
    """Due periodi sullo stesso attributo non sono un raffinamento (D124).

    **Il caso, misurato il 2 agosto 2026.** *«mostrami i lead creati quest'anno»*, poi
    *«mostrami i lead creati da 6 mesi ad oggi»*. Il secondo turno **aggiungeva** il
    proprio periodo invece di sostituire il primo, e il risultato era l'intersezione
    dei due — un intervallo che l'utente non aveva chiesto e che nessuno gli diceva.

    **Perche' il raffinamento additivo e' giusto ovunque tranne qui.** §17.1 e' cio' che
    fa funzionare *«solo quelli attivi»* al secondo turno: la frase aggiunge un asse
    nuovo, e sommarla e' esattamente cio' che si vuole. Ma una frase che nomina di
    nuovo **lo stesso asse** non ne aggiunge uno: lo riscrive. Sommarla produce un'
    intersezione che nessuno ha chiesto, e il DSL ha gia' l'operazione giusta,
    `replace_condition`.

    **Perche' la regola sta qui e non nel prompt.** Un'istruzione al modello e'
    probabilistica; questo e' strutturale, come D89, D99 e D105. E soprattutto: il
    fallimento e' **invisibile**. Nel caso misurato i due turni hanno restituito lo
    stesso numero di record — 39 e 39 — perche' i sei mesi cadevano dentro l'anno.
    Niente da notare, nemmeno guardando. E' la forma pura del rischio di **D2**: una
    risposta sbagliata con l'aria di essere giusta.

    Il rifiuto qui diventa un chiarimento o un *«non ho capito»*, che e' cio' che D2
    chiede di preferire a un numero plausibile.
    """
    per_attribute: dict[str, int] = {}
    for condition in state_module.conditions(state.get("filter")):
        if condition.get("predicate") not in _PERIOD_PREDICATES:
            continue
        reference = condition.get("ref")
        if not reference:
            continue
        per_attribute[reference] = per_attribute.get(reference, 0) + 1

    return [
        _failure(
            4,
            "two_periods_on_one_attribute",
            f"filter.{reference}",
            f"{count} separate periods are placed on {reference!r}. Two periods on one "
            "attribute intersect instead of refining, which narrows the answer in a "
            "way nobody asked for and nothing shows: a turn that names a period "
            "already constrained replaces it (D124), it does not add to it",
        )
        for reference, count in sorted(per_attribute.items()) if count > 1
    ]


# ---------------------------------------------------------------------------
# Level 5 — cost
# ---------------------------------------------------------------------------

def validate_cost(state: dict, *, limits: Limits = DEFAULT_LIMITS) -> list[Failure]:
    """Dictionary-free level 5 checks (§12.6).

    An unsustainable interrogation is not a performance problem: it is a problem
    of availability for every other user. Treating it in the contract, with an
    outcome the user understands and a proposal to narrow, beats letting it start
    and killing it on timeout — which produces an incomprehensible error after a
    long wait.
    """
    failures: list[Failure] = []

    limit = (state.get("limit") or {}).get("value")
    if isinstance(limit, int) and limit > limits.max_records:
        failures.append(_failure(
            5,
            "limit_above_maximum",
            "limit.value",
            f"{limit} exceeds the absolute maximum of {limits.max_records} (D13). "
            "Beyond it the conversational surface is the wrong instrument: the "
            "answer is to narrow, or to move to pivot and export",
        ))

    for reference in state_module.references(state):
        hops = state_module.relation_hops(reference)
        if hops > limits.max_relation_hops:
            failures.append(_failure(
                5,
                "too_many_relation_hops",
                "references",
                f"{reference!r} traverses {hops} relations, above "
                f"{limits.max_relation_hops} (§7.3). The road is a promoted "
                "reference in the dictionary (T7), not a longer path",
            ))

    return failures
