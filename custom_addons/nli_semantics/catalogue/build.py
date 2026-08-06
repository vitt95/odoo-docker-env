"""Assembly of the phase C catalogue (§5.7, §5.9, D87).

**Pure zone.**

## The order of operations is the security property

§5.9 is emphatic: the permission filter runs **before** selection and budget, never
after. A catalogue selected and then filtered would come out poorer than intended
with nothing to say so — the budget would have been spent on attributes later
removed, and the lost coverage would be blamed on the budget instead of on
permissions. The code below therefore filters first, and the sequence is asserted by
its tests, because it is the kind of thing a later refactor reorders for tidiness.

## The catalogue is confidential

D57: terminology, custom fields and enumerated values describe processes,
segmentation and product lines. *"They are only metadata"* is true and commercially
dangerous. Nothing here narrows what a caller may do with the result, but the fact
belongs next to the code that builds it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import anchor as anchor_module
from ..dictionary import entries as entries_module
from .exposure import Attribute, Budget, Decision, attribute_budget, exposed, within_budget


@dataclass(frozen=True)
class CatalogueAttribute:
    """One attribute as the model sees it: reference, terms, type."""

    ref: str
    terms: tuple[str, ...]
    type: str
    #: Il nome con cui si parla all'utente, che non e' `terms[0]`. I termini sono le
    #: parole con cui lo si riconosce — sinonimi e flessioni compresi — e la prima non
    #: e' per forza un nome: dal 5 agosto 2026 al livello L1 ci sono `creati`,
    #: `chiusi`, `assegnati`. Mostrarli indietro fa proporre *«creazione»* dove
    #: l'utente si aspetta `Data creazione`. Vedi `store._merge`.
    label: str = ""
    #: Admitted values for enumerated attributes (T2). Schema metadata, not record
    #: content: it is what lets the catalogue give the model the valid values
    #: **without showing it a single record** (§3.3, A6).
    values: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class CatalogueCategory:
    """A T5 named condition as the model sees it — the term, never the condition.

    `cost_class` and `time_dependent` do not reach the model. They travel with the
    catalogue because level 5 needs the first (V-D87-2) and the Resolver the second
    (V-D87-3), and computing them twice from two places is how they end up
    disagreeing.
    """

    ref: str
    terms: tuple[str, ...]
    cost_class: str
    time_dependent: bool


@dataclass(frozen=True)
class Catalogue:
    """What the Interpreter may name, for one user and one entity."""

    entity: str
    attributes: tuple[CatalogueAttribute, ...]
    categories: tuple[CatalogueCategory, ...]
    #: Entity names are always present, even in phase C, so the conversation can
    #: change subject (§5.8).
    entity_names: tuple[tuple[str, tuple[str, ...]], ...]
    budget: Budget
    #: Counted, not swallowed: §6.4 watches *refusals for budget*, and D31's delibera
    #: says that indicator is what will tell us whether 60 is the wrong number.
    refused_for_budget: int = 0
    #: References dropped by the permission filter, and categories dropped with them.
    excluded_for_permissions: tuple[str, ...] = ()
    excluded_categories: tuple[tuple[str, str], ...] = ()
    #: The rule that exposed each attribute, for the diagnosis of §6.3.
    exposure_rules: tuple[tuple[str, str], ...] = ()
    #: Dove si attacca un'espressione temporale che non nomina un campo (**D110**).
    #: Calcolata dagli attributi sopravvissuti a diritti e budget, mai da quelli in
    #: ingresso: un'ancora che nominasse una data non leggibile sarebbe una seconda
    #: via alla stessa informazione, senza le stesse guardie.
    time_anchor: dict | None = None

    @property
    def refs(self) -> frozenset[str]:
        """Every reference the model may name — what coverage is measured against."""
        return frozenset(
            {self.entity}
            | {attribute.ref for attribute in self.attributes}
            | {category.ref for category in self.categories}
            | {ref for ref, _ in self.entity_names}
        )

    def __len__(self) -> int:
        return len(self.attributes) + len(self.categories)


def build(
    dictionary,
    *,
    entity: str,
    attributes: list[Attribute],
    readable_refs: frozenset[str],
    context_window: int,
    entity_refs: frozenset[str] = frozenset(),
    hop_attributes: list[Attribute] | None = None,
    type_map: dict[str, str] | None = None,
) -> Catalogue:
    """Assemble the phase C catalogue.

    `readable_refs` is the set of references this user may read — the output of the
    permission filter, computed with the platform's access rules and the company
    context (D39, D40). It is passed in rather than computed: a pure function cannot
    read an ACL, and a catalogue that guessed at permissions would be worse than one
    that admits it needs to be told.

    `type_map` translates the descriptor's type into the type vocabulary of `03`
    §8.1. It is an argument for the same reason: the mapping from `many2one` to
    `relation` is platform knowledge, and the zone that decides exposure must not
    acquire any. Absent, types pass through unchanged — which is what the corpus
    needs, since its pack already speaks the contract's language.
    """
    type_map = type_map or {}
    # --- 1. permissions, first (§5.9) --------------------------------------
    candidates = list(attributes) + list(hop_attributes or [])
    permitted: list[Attribute] = []
    excluded: list[str] = []
    for attribute in candidates:
        ref = _ref_of(entity, attribute)
        if ref in readable_refs:
            permitted.append(attribute)
        else:
            excluded.append(ref)

    # --- 2. exposure rules, then budget (§5.3, §5.4, D79) ------------------
    decisions = exposed(permitted)
    budget = attribute_budget(context_window)
    kept, refused = within_budget(decisions, budget)

    catalogue_attributes = tuple(
        CatalogueAttribute(
            ref=_ref_of(entity, decision.attribute),
            terms=tuple(dictionary.terms_of(_ref_of(entity, decision.attribute))),
            label=dictionary.display_of(_ref_of(entity, decision.attribute)),
            type=type_map.get(decision.attribute.type, decision.attribute.type),
            values=_enum_values(dictionary, _ref_of(entity, decision.attribute)),
        )
        for decision in kept
    )

    # --- 2b. l'ancora del tempo, dagli attributi rimasti (D110) --------
    time_anchor = anchor_module.time_anchor(
        anchor_module.date_refs(catalogue_attributes))

    # --- 3. categories, subject to V-D87-1 ---------------------------------
    categories, excluded_categories = _categories(dictionary, entity, readable_refs)

    return Catalogue(
        entity=entity,
        attributes=catalogue_attributes,
        categories=categories,
        entity_names=tuple(
            (ref, tuple(dictionary.terms_of(ref))) for ref in sorted(entity_refs)
        ),
        budget=budget,
        refused_for_budget=refused,
        excluded_for_permissions=tuple(sorted(excluded)),
        excluded_categories=excluded_categories,
        exposure_rules=tuple(
            (_ref_of(entity, decision.attribute), decision.rule) for decision in kept
        ),
        time_anchor=time_anchor,
    )


def _ref_of(entity: str, attribute: Attribute) -> str:
    """The semantic reference of an attribute.

    An attribute whose name already contains a dot is a hop or a promoted reference
    (T7) and carries its own path; the others belong to the entity.
    """
    return attribute.name if "." in attribute.name else f"{entity}.{attribute.name}"


def _enum_values(dictionary, ref: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (entry["value"], tuple(entry.get("terms", [])))
        for entry in dictionary.enum_values_of(ref)
    )


def _categories(
    dictionary, entity: str, readable_refs: frozenset[str]
) -> tuple[tuple[CatalogueCategory, ...], tuple[tuple[str, str], ...]]:
    """The categories of the entity the user may see (**V-D87-1**).

    A category is excluded when the user cannot read **every** field its condition
    reads. The implied set is derived from the condition, not declared — the declared
    form had already failed in the corpus lexicon, where `sottoscorta` compares
    `qty_available` with `reordering_min` and declares only the first. Under a declared
    list that user would have received the category, and D87 would have opened a path
    to unauthorised data with normal accuracy and normal latency.

    A category whose condition is missing or unreadable is excluded too: **failing
    safe**, the same rule D39 applies to the permission fingerprint.
    """
    kept: list[CatalogueCategory] = []
    dropped: list[tuple[str, str]] = []

    for entry in dictionary.categories_of(entity):
        ref = entry.get("ref", "")
        if not entry.get("condition"):
            dropped.append((ref, "no condition: the implied fields are not computable"))
            continue
        implied = entries_module.category_implied_refs(entry)
        if not implied:
            dropped.append((ref, "condition reads no field: not verifiable"))
            continue
        unreadable = sorted(implied - readable_refs)
        if unreadable:
            dropped.append((ref, f"user cannot read {unreadable}"))
            continue
        kept.append(CatalogueCategory(
            ref=ref,
            terms=tuple(entry.get("terms", [])),
            cost_class=entries_module.category_cost_class(entry),
            time_dependent=entries_module.category_is_time_dependent(entry),
        ))

    return tuple(kept), tuple(dropped)
