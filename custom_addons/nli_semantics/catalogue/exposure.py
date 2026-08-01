"""Exposure rules and budget — why the Odoo schema is not a catalogue (§5.2-5.4).

**Pure zone.** The rules take a **descriptor** per attribute and decide; producing
those descriptors from a live Odoo registry is introspection, and it lives with the
platform-facing half of this module.

## The number that motivates the whole file

`06` §5.2 counted it on the sources: `sale.order` exposes **more than 85** fields —
61 of its own, some twenty from the messaging and activity mixins, six from the
base. Of those, the ones a person might name in a sentence are of the order of
twenty.

Putting all 85 in the catalogue does three kinds of damage at once: it spends the
budget, it adds latency and cost, and it **makes the interpretation worse**. A model
offered `message_needaction_counter` next to `importo_totale` has more ways to be
wrong, not more ways to guess right.

## Why rule 5 is worth its place

A stored-nothing computed field cannot be filtered or ordered by the ORM. Were it in
the catalogue, the model could legitimately use it and the failure would surface only
at execution, as an incomprehensible error after a wait. Excluding it upstream turns
a late failure into a non-possibility — the same move as C3 in the contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Identifiers of the nine rules of §5.3, in the order they are applied. The first
#: that matches decides, and the state records which one did: an exposure the
#: catalogue cannot explain is one nobody can correct.
RULES: tuple[tuple[str, str], ...] = (
    ("l2_declared", "the customer declared it exposed or hidden — decides"),
    ("system_field", "system field (create_uid, write_date, id, …) — hidden"),
    ("technical_mixin", "field of a technical mixin (messaging, activity) — hidden"),
    ("unqueryable_type", "type not usefully queryable (binary, html) — hidden"),
    ("not_stored_not_searchable", "neither stored nor searchable — hidden"),
    ("no_usable_label", "label absent or equal to the technical name — hidden"),
    ("l1_relevant", "declared relevant for the domain in L1 — exposed"),
    ("in_default_views", "present in the entity's default views — exposed"),
    ("residual", "everything else — exposed with low priority"),
)

RULE_IDS = frozenset(identifier for identifier, _ in RULES)

#: Types that cannot be usefully filtered or ordered (rule 4).
UNQUERYABLE_TYPES = frozenset({"binary", "html", "image", "json"})

#: Priority bands for the budget ordering of §5.4, lowest number first.
PRIORITY_L2 = 0
PRIORITY_DEFAULT_VIEWS = 1
PRIORITY_HISTORICAL_USE = 2
PRIORITY_L1 = 3
PRIORITY_RESIDUAL = 4


@dataclass(frozen=True)
class Attribute:
    """What the exposure rules need to know about one attribute.

    A descriptor rather than an ORM field object, for the reason the whole pure zone
    exists: these rules must be testable, and their result reproducible, without a
    database. Introspection fills it in; §5.3 only ever reads it.
    """

    name: str
    label: str
    type: str
    stored: bool = True
    searchable: bool = True
    in_default_views: bool = False
    is_system: bool = False
    is_technical_mixin: bool = False
    l1_relevant: bool = False
    #: `True` exposed, `False` hidden, `None` the customer said nothing.
    l2_exposed: bool | None = None
    #: How often this attribute appeared in this installation's interrogations.
    #: The only criterion of §5.4 that improves over time, and it is a frequency
    #: computed from the Registry, not a prediction.
    historical_uses: int = 0


@dataclass(frozen=True)
class Decision:
    """Whether an attribute is exposed, and which rule said so."""

    attribute: Attribute
    exposed: bool
    rule: str
    priority: int


def decide(attribute: Attribute) -> Decision:
    """Apply the nine rules of §5.3 in order; the first that matches decides."""
    if attribute.l2_exposed is not None:
        return Decision(attribute, attribute.l2_exposed, "l2_declared", PRIORITY_L2)
    if attribute.is_system:
        return Decision(attribute, False, "system_field", PRIORITY_RESIDUAL)
    if attribute.is_technical_mixin:
        return Decision(attribute, False, "technical_mixin", PRIORITY_RESIDUAL)
    if attribute.type in UNQUERYABLE_TYPES:
        return Decision(attribute, False, "unqueryable_type", PRIORITY_RESIDUAL)
    if not attribute.stored and not attribute.searchable:
        return Decision(attribute, False, "not_stored_not_searchable", PRIORITY_RESIDUAL)
    if not attribute.label or attribute.label == attribute.name:
        return Decision(attribute, False, "no_usable_label", PRIORITY_RESIDUAL)
    if attribute.l1_relevant:
        return Decision(attribute, True, "l1_relevant", PRIORITY_L1)
    if attribute.in_default_views:
        # §5.3 calls rule 8 the most productive one, and it is: the fields Odoo
        # shows in its default list and form views are the ones the module's
        # designers judged relevant. A judgement of pertinence already made, free,
        # and aligned by construction with what users see every day.
        return Decision(attribute, True, "in_default_views", PRIORITY_DEFAULT_VIEWS)
    return Decision(attribute, True, "residual", PRIORITY_RESIDUAL)


def exposed(attributes: list[Attribute]) -> list[Decision]:
    """The exposed attributes, in the budget order of §5.4.

    Note the order of the two operations: decide, then sort. The permission filter
    runs **before** both (§5.9), which is why it is not here — a catalogue selected
    and then filtered would spend its budget on attributes later removed, and the
    lost coverage would be attributed to the budget instead of to permissions.
    """
    decisions = [decide(attribute) for attribute in attributes]
    kept = [decision for decision in decisions if decision.exposed]
    kept.sort(key=lambda decision: (
        _priority_with_history(decision),
        -decision.attribute.historical_uses,
        decision.attribute.name,
    ))
    return kept


def _priority_with_history(decision: Decision) -> int:
    """Historical use promotes a residual attribute above the other residuals.

    §5.4 puts historical frequency third, after L2 and the default views. An
    attribute nobody has ever named stays where it was; one users keep naming rises.
    It closes a loop worth having: **the attributes users name most become the ones
    the system offers first.**
    """
    if decision.priority == PRIORITY_RESIDUAL and decision.attribute.historical_uses > 0:
        return PRIORITY_HISTORICAL_USE
    return decision.priority


# ---------------------------------------------------------------------------
# Budget (D31, D79)
# ---------------------------------------------------------------------------

#: Absolute ceiling on exposed attributes per entity. D31 fixed 60; D79 turned it
#: into a ceiling rather than a constant, because a model with a narrow context
#: window truncates the catalogue **in silence**: high coverage, low accuracy, and a
#: cause outside every diagnostic table.
MAX_ATTRIBUTES = 60

#: Floor. Below this the catalogue stops being able to describe an entity at all,
#: and the right answer is to refuse the profile rather than to serve a catalogue
#: that cannot work — D80 forbids activating an unqualified profile, and this is the
#: same argument one level down.
MIN_ATTRIBUTES = 8

#: Tokens one catalogue line costs. A line reads like
#: `ordini_vendita.importo_totale: importo, totale, valore (numero)` — reference,
#: two or three terms, type — which is a little over twenty tokens for an Italian
#: identifier split into word pieces. Rounded up, because underestimating it is the
#: failure D79 is about: a budget that says sixty fit when forty do produces a
#: catalogue truncated by the provider instead of by us, and silently.
TOKENS_PER_ATTRIBUTE = 24

#: Share of the context window the catalogue may occupy. The rest is the request,
#: the instructions, the enumerated values, the entity list and the model's own
#: output — and the output of a constrained generation is not small.
CATALOGUE_SHARE = 0.25

#: Fixed reserve for the parts of the prompt that do not scale with the entity.
FIXED_RESERVE_TOKENS = 600


@dataclass(frozen=True)
class Budget:
    """An attribute budget and the derivation that produced it."""

    attributes: int
    context_window: int
    #: Why this number: `ceiling`, `window`, or `floor`.
    reason: str
    detail: str = ""


def attribute_budget(context_window: int) -> Budget:
    """Derive the attribute budget from the model's context window (**D79**).

    The profile declares its window (D78). Deriving the budget from it — rather than
    fixing 60 for everyone — is what keeps a local model with a 4 000-token window
    from truncating the catalogue without saying so. The failure it prevents is the
    one that looks like a model defect and is a configuration defect: coverage
    reported high because the reference *was* in the catalogue we built, accuracy low
    because the catalogue the model actually saw was cut in half.
    """
    if context_window <= 0:
        return Budget(MIN_ATTRIBUTES, context_window, "floor",
                      "no context window declared; the floor is the only safe answer")

    available = int(context_window * CATALOGUE_SHARE) - FIXED_RESERVE_TOKENS
    derived = available // TOKENS_PER_ATTRIBUTE

    if derived >= MAX_ATTRIBUTES:
        return Budget(MAX_ATTRIBUTES, context_window, "ceiling",
                      f"the window affords {derived}, capped at {MAX_ATTRIBUTES} (D31)")
    if derived <= MIN_ATTRIBUTES:
        return Budget(MIN_ATTRIBUTES, context_window, "floor",
                      f"the window affords only {derived}; below {MIN_ATTRIBUTES} a "
                      "catalogue cannot describe an entity, and the profile should "
                      "not be qualified (D80)")
    return Budget(derived, context_window, "window",
                  f"{available} tokens for the catalogue at "
                  f"{TOKENS_PER_ATTRIBUTE} per attribute")


def within_budget(decisions: list[Decision], budget: Budget) -> tuple[list[Decision], int]:
    """Truncate to the budget, returning what was kept and how many were refused.

    The count is not diagnostics: §6.4 lists *refusals for budget* as an indicator to
    watch, and D31's own delibera says it is what will tell us whether 60 is the
    wrong number. A truncation nobody counts is a coverage loss nobody can explain.
    """
    if len(decisions) <= budget.attributes:
        return decisions, 0
    return decisions[:budget.attributes], len(decisions) - budget.attributes
