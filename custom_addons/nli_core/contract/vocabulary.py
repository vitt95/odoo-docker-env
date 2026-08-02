"""The closed vocabularies of DSL 1.0, transcribed from `ai/03-specifica-dsl.md`.

Criterion **C1** — the model chooses, it never invents — is only real if the sets
it chooses from exist in one place and are enumerable. That is what this module
is. It holds no logic: every set below is a line of the specification, and a
reviewer can diff the two.

**Pure zone.** No platform, no clock, no configuration. The two installation
parameters that look like they belong here (the default and maximum record
limit, D13) are not constants of the contract: they are passed in as `Limits`.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The version of the contract this module describes (`03` §15.2, `MAJOR.MINOR`).
DSL_VERSION = "1.0"

#: Versions a reader of this contract accepts. §15.4: a reader must support every
#: earlier MINOR of its own MAJOR.
SUPPORTED_VERSIONS = frozenset({"1.0"})


# ---------------------------------------------------------------------------
# The envelope (§4.4)
# ---------------------------------------------------------------------------

#: `outcome` — four mutually exclusive values. `clarification` and `out_of_scope`
#: are first-class outcomes, not errors: a system that asks, or that declares a
#: limit, is operating correctly (§4.4).
OUTCOMES = frozenset({
    "operations",
    "clarification",
    "out_of_scope",
    "not_understood",
})

#: The field each outcome carries. An outcome with the wrong companion field is a
#: level 1 failure, not a tolerated variation.
OUTCOME_PAYLOAD: dict[str, str | None] = {
    "operations": "operations",
    "clarification": "clarification",
    "out_of_scope": "scope_note",
    "not_understood": None,
}

#: `scope_note` categories (§11.4) — a closed set, never free text, because its
#: distribution is the quantitative evidence for what to extend next.
SCOPE_NOTES = frozenset({
    "modifica_dati",
    "invio_esterno",
    "creazione_record",
    "cancellazione_record",
    "previsione",
})


# ---------------------------------------------------------------------------
# Operations (§6)
# ---------------------------------------------------------------------------

#: Family 1 — entity (§6.2).
OPS_ENTITY = frozenset({"set_target"})

#: Family 2 — conditions (§6.3).
OPS_CONDITION = frozenset({
    "add_condition",
    "replace_condition",
    "remove_condition",
    "clear_filter",
})

#: Family 3 — presentation (§6.4).
OPS_PRESENTATION = frozenset({
    "add_field",
    "remove_field",
    "set_fields",
    "clear_fields",
    "set_view",
})

#: Family 4 — organisation (§6.5).
OPS_ORGANISATION = frozenset({
    "add_group",
    "remove_group",
    "clear_groups",
    "set_order",
    "add_order",
    "clear_order",
    "add_measure",
    "remove_measure",
    "set_limit",
})

#: Family 5 — session and navigation (§6.6).
OPS_SESSION = frozenset({"reset", "revert_last", "open_record"})

#: The whole vocabulary. §6.1 and the glossary of §21 both say "eighteen"; the
#: five tables of §6.2-6.6 enumerate twenty-two (1 + 4 + 5 + 9 + 3). The tables
#: are the normative content — a count in prose cannot remove an operation that
#: has a row, a signature and a rationale — so twenty-two is what is implemented
#: and the count in the document needs correcting.
OPERATIONS = (
    OPS_ENTITY
    | OPS_CONDITION
    | OPS_PRESENTATION
    | OPS_ORGANISATION
    | OPS_SESSION
)

#: Operations that leave the state untouched (§6.6): `open_record` navigates,
#: `revert_last` is served from the state history the system owns.
OPS_WITHOUT_STATE_CHANGE = frozenset({"open_record"})

#: Operations that may appear only as the single operation of an envelope.
#:
#: `revert_last` alone. Its meaning is "undo the envelope before this one", and
#: composing it with a refinement makes the result depend on whether the undo
#: happens before or after — expressible under §4.5 rule 1, and surprising in
#: both readings. `reset` is deliberately *not* here: "no, let's look at customers
#: instead" is one intention that produces `reset` followed by `set_target`, and
#: refusing it would refuse a natural sentence.
OPS_EXCLUSIVE = frozenset({"revert_last"})


# ---------------------------------------------------------------------------
# Predicates and values (§8)
# ---------------------------------------------------------------------------

#: Predicates admitted **per attribute type** (§8.1). A predicate on a type that
#: does not admit it is a level 4 failure, not a tolerated extension.
#:
#: `category` is not in the table of §8.1: see `CATEGORY_PREDICATE` below.
PREDICATES_BY_TYPE: dict[str, frozenset[str]] = {
    "text": frozenset({
        "equals", "contains", "starts_with", "is_one_of",
        "is_empty", "is_not_empty",
    }),
    "number": frozenset({
        "equals", "greater_than", "greater_or_equal",
        "less_than", "less_or_equal", "between", "approximately",
    }),
    # D113: su una data l'intervallo si dice `within`, e basta. `between` diceva la
    # stessa cosa con un'altra parola, e un contratto che ammette due modi di dire
    # un fatto ha due posti in cui due componenti possono divergere. Tolto qui, e non
    # solo fra i tipi di valore ammessi, perche' la generazione vincolata derivi i
    # predicati dal tipo (D103) e il periodo scritto male sia inesprimibile invece che
    # rifiutato un livello dopo.
    "date": frozenset({"on", "before", "after", "within"}),
    "datetime": frozenset({"on", "before", "after", "within"}),
    "enum": frozenset({"is_one_of", "is_not_one_of"}),
    "boolean": frozenset({"is_true", "is_false"}),
    "relation": frozenset({"is_one_of", "is_set", "is_not_set"}),
    # D87 — see CATEGORY_PREDICATE.
    "category": frozenset({"is_category"}),
}

#: The predicate that names a **T5 category** — a condition the organisation has
#: a word for (`06-modello-semantico.md` §3.6: "condizione nominata").
#:
#: This symbol is **not** in `03` §8.1, and its absence was a gap between two
#: documents rather than a decision: §8.1 enumerates predicates per *attribute*
#: type, while T5 is a named condition with no attribute, no operator and no
#: value. D30 requires T5 in phase 1, and 68.8% of the `operations` cases of the
#: foundational corpus use one, so the contract could not express two thirds of
#: its own test suite without it.
#:
#: **Adopted as D87** on 2026-07-28 (`ai/00-registro-decisioni.md` §14), with
#: three constraints that are part of the decision:
#:
#: 1. a category never appears in the catalogue of a user who cannot read the
#:    fields that define it. If the set of implied fields is not computable, the
#:    category is excluded — fail safe, as for the permission fingerprint of D39;
#: 2. the cost of a category enters level 5 validation. A category can hide an
#:    aggregate over another entity, and D12 exists so that cost is computable a
#:    priori rather than estimated;
#: 3. the Applicator never expands a category. Its condition can depend on the
#:    clock — "overdue invoices" is `due < today` — so expansion would break both
#:    this module's purity and the reproducibility of the corpus (D82). The
#:    Resolver, the single component aware of time, turns it into a condition
#:    fragment at execution.
#:
#: The alternative that costs nothing was looked for and rejected: exposing the
#: category as a **boolean attribute** of the dictionary needs no new symbol, but
#: a boolean admits `is_false`, and the negation of a named condition is not the
#: negation of a field — "invoices not overdue" would also return the paid ones,
#: with no error and a plausible number. It would also make a *definition*
#: indistinguishable from *vocabulary*, reopening the failure mode D29 closes.
CATEGORY_PREDICATE = "is_category"

#: Every predicate, for the level 2 membership check.
PREDICATES = frozenset().union(*PREDICATES_BY_TYPE.values())

#: Predicates that take no value: the predicate *is* the whole condition.
PREDICATES_WITHOUT_VALUE = frozenset({
    "is_empty", "is_not_empty",
    "is_true", "is_false",
    "is_set", "is_not_set",
    CATEGORY_PREDICATE,
})

#: Predicates that carry no information in a value but are written with one in the
#: specification's own worked example (§17.1 turn 2 emits `is_true` together with
#: `{"kind": "boolean", "value": true}`).
#:
#: A worked example that fails validation would mean the reading is wrong, so the
#: value is admitted here and **dropped by canonicalisation**: two envelopes that
#: differ only by a redundant value are the same condition, and C8 requires them
#: to have one canonical form. A value that *contradicts* the predicate —
#: `is_true` with `false` — is a level 4 failure, not a tolerated redundancy.
PREDICATES_WITH_OPTIONAL_VALUE = frozenset({"is_true", "is_false"})

#: Predicates for which a value is a structural error.
PREDICATES_VALUE_FORBIDDEN = PREDICATES_WITHOUT_VALUE - PREDICATES_WITH_OPTIONAL_VALUE

#: The boolean each predicate of `PREDICATES_WITH_OPTIONAL_VALUE` asserts.
PREDICATE_ASSERTED_BOOLEAN = {"is_true": True, "is_false": False}

#: Value kinds (§8.2), with the keys each one carries.
VALUE_KINDS: dict[str, frozenset[str]] = {
    "text": frozenset({"text"}),
    "number": frozenset({"value"}),
    "range": frozenset({"from", "to"}),
    "enum": frozenset({"items"}),
    "boolean": frozenset({"value"}),
    "temporal": frozenset({"expression"}),
    "reference": frozenset({"text"}),
}

#: Optional keys per value kind. `resolver` names a vagueness rule defined in the
#: dictionary (§9.3): the model declares *that* the value is approximate and
#: *which* rule applies. It never decides the tolerance.
VALUE_OPTIONAL_KEYS: dict[str, frozenset[str]] = {
    "text": frozenset(),
    "number": frozenset({"resolver"}),
    "range": frozenset(),
    "enum": frozenset(),
    "boolean": frozenset(),
    "temporal": frozenset({"n", "date", "from", "to"}),
    "reference": frozenset(),
}

#: The value kind each predicate expects. Absent from the table means the
#: predicate takes no value (`PREDICATES_WITHOUT_VALUE`).
PREDICATE_VALUE_KINDS: dict[str, frozenset[str]] = {
    "equals": frozenset({"text", "number", "boolean", "reference"}),
    "contains": frozenset({"text"}),
    "starts_with": frozenset({"text"}),
    "is_one_of": frozenset({"enum", "reference"}),
    "is_not_one_of": frozenset({"enum"}),
    "greater_than": frozenset({"number"}),
    "greater_or_equal": frozenset({"number"}),
    "less_than": frozenset({"number"}),
    "less_or_equal": frozenset({"number"}),
    # D113: `between` resta l'intervallo **numerico** — `equivalence.py` fonde in
    # quella forma un `>= X` e un `<= Y` sullo stesso riferimento. Il valore temporale
    # se ne va: era il doppione di `within`. Questa riga e' la rete per le condizioni
    # che arrivano da altre strade (una query salvata, un'interpretazione modificata a
    # mano), dove lo schema della generazione non passa.
    "between": frozenset({"range"}),
    "approximately": frozenset({"number"}),
    "on": frozenset({"temporal"}),
    "before": frozenset({"temporal"}),
    "after": frozenset({"temporal"}),
    "within": frozenset({"temporal"}),
}


# ---------------------------------------------------------------------------
# Temporal expressions (§9.2)
# ---------------------------------------------------------------------------

#: Symbolic, never resolved into absolute dates unless the user said them.
#: "This month" stays `current_month` so that a query saved in July shows August
#: in August — the condition for phase 4 to be an extension and not a rewrite.
TEMPORAL_PUNCTUAL = frozenset({"today", "yesterday", "tomorrow"})
TEMPORAL_CURRENT = frozenset({
    "current_week", "current_month", "current_quarter", "current_year",
})
TEMPORAL_PREVIOUS = frozenset({
    "previous_week", "previous_month", "previous_quarter", "previous_year",
})

#: The year so far — **D91**. `current_year` is the whole year, which is a
#: different period, and "revenue since the start of the year" is the most common
#: management comparison there is. Resolved against the **fiscal** year start, like
#: `current_year` (§9.2): in a company whose year is not the calendar year,
#: returning January-to-date would produce a wrong number of entirely credible
#: appearance.
#:
#: Only this one, not the family. `month_to_date` and `quarter_to_date` are the
#: natural extension and are deliberately absent: §3.9 adds expressiveness when
#: the data asks for it, and the data asks for one. The elicitation of D85 is the
#: instrument that would show whether the others are used.
TEMPORAL_TO_DATE = frozenset({"year_to_date"})

#: Parametric expressions carry their parameter in `n`, e.g.
#: `{"kind": "temporal", "expression": "last_n_days", "n": 30}`. The
#: specification writes them as `last_n_days(n)`; the JSON form has to name the
#: parameter, and naming it is what makes it validatable at level 1.
TEMPORAL_PARAMETRIC = frozenset({
    "last_n_days", "last_n_weeks", "last_n_months", "next_n_days",
})

#: Absolute expressions carry `date`, or `from` and `to`. They appear only when
#: the user gave a date (§9.2).
TEMPORAL_ABSOLUTE_SINGLE = frozenset({"absolute"})
TEMPORAL_ABSOLUTE_RANGE = frozenset({"absolute_range"})

TEMPORAL_EXPRESSIONS = (
    TEMPORAL_PUNCTUAL
    | TEMPORAL_CURRENT
    | TEMPORAL_PREVIOUS
    | TEMPORAL_TO_DATE
    | TEMPORAL_PARAMETRIC
    | TEMPORAL_ABSOLUTE_SINGLE
    | TEMPORAL_ABSOLUTE_RANGE
)

#: Required extra keys per temporal expression.
TEMPORAL_REQUIRED_KEYS: dict[str, frozenset[str]] = {
    **{name: frozenset({"n"}) for name in TEMPORAL_PARAMETRIC},
    "absolute": frozenset({"date"}),
    "absolute_range": frozenset({"from", "to"}),
}


# ---------------------------------------------------------------------------
# Aggregation, views, organisation (§8.5, §5.6, §5.9)
# ---------------------------------------------------------------------------

AGGREGATIONS = frozenset({"sum", "avg", "min", "max", "count", "count_distinct"})

#: Attribute types each aggregation admits (§8.5). `count` needs no attribute.
AGGREGATION_TYPES: dict[str, frozenset[str]] = {
    "sum": frozenset({"number"}),
    "avg": frozenset({"number"}),
    "min": frozenset({"number", "date", "datetime"}),
    "max": frozenset({"number", "date", "datetime"}),
    "count": frozenset(),
    "count_distinct": frozenset({
        "text", "number", "date", "datetime", "enum", "boolean", "relation",
    }),
}

VIEWS = frozenset({"list", "kanban", "calendar", "pivot", "graph", "form"})

CONNECTIVES = frozenset({"all", "any", "not"})

GRANULARITIES = frozenset({"day", "week", "month", "quarter", "year"})

DIRECTIONS = frozenset({"asc", "desc"})

#: `by` values of an `open_record` selector (§6.6). No selection by technical
#: identifier: the user does not know identifiers and the model must not invent
#: them.
SELECTORS = frozenset({"position", "attribute"})


# ---------------------------------------------------------------------------
# Provenance (§10)
# ---------------------------------------------------------------------------

ORIGINS = frozenset({"user", "inferred", "default"})

#: Identifiers of the rules the system may declare when `origin` is `inferred`
#: or `default`. Closed, like every other vocabulary: a rule identifier the
#: interface cannot explain is an inference the user cannot contradict.
#:
#: The five view rules are normative (§6.7) and versioned with the contract —
#: changing one changes the view of states already saved. The two ordering rules
#: appear in the worked examples of §17.1 and §5.1.
VIEW_DERIVATION_RULES: tuple[tuple[str, str], ...] = (
    ("measures_multi_group_implies_pivot", "measures present and >= 2 group_by"),
    ("measures_single_group_implies_graph", "measures present and 1 group_by"),
    ("measures_without_group_implies_list", "measures present, no group_by"),
    ("grouping_without_measure_implies_list", "group_by present, no measures"),
    ("default_list", "none of the above"),
)

#: Only the identifiers the specification actually names are admitted. Inferences
#: made by components that know the attribute *type* — ascending for text,
#: descending by date for "the latest" — declare their own rule from this set;
#: adding one is a contract change (§6.7, §15.2), which is why the set is closed
#: rather than a free string.
#:
#: The installation defaults for `limit` and `presentation` carry no rule: their
#: origin is `default`, which already says everything there is to say (§5.8).
#: "the latest five orders" implies a descending order by date that the user did not
#: name but without which "latest" has no meaning (§5.1, §5.7).
RULE_LATEST_DESC = "latest_implies_desc_by_date"

#: Ascending is the natural reading for a text attribute (§17.1 turn 3, where the rule
#: is described and left unnamed). Named here because rule identifiers are a closed
#: set: an inference the interface cannot name is one the user cannot contradict. D88.
RULE_TEXT_ASC = "text_attribute_implies_asc"

INFERENCE_RULES = frozenset(
    {identifier for identifier, _ in VIEW_DERIVATION_RULES}
    | {RULE_LATEST_DESC, RULE_TEXT_ASC}
)


# ---------------------------------------------------------------------------
# Structural limits (D12, D13)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Limits:
    """Structural and cost limits.

    Declared parameters, not implicit assumptions (RC4): they are recalibrated on
    the corpus with an additive change. The defaults are the values fixed in
    `ai/00-registro-decisioni.md` §6.2 for D13, and in D12 for the rest.

    They are arguments rather than module constants because the record limits are
    per-installation configuration, and the pure zone must not read
    configuration — it would make the Applicator depend on something other than
    its inputs.
    """

    #: D13: coincides with the native list view pagination, so a conversational
    #: result is indistinguishable from the first page of a native view.
    default_records: int = 80
    #: D13: beyond this the conversational surface is the wrong instrument.
    max_records: int = 500
    #: D12: filter tree depth.
    max_filter_depth: int = 3
    #: D12: group_by levels.
    max_groups: int = 3
    #: D12: relation hops inside a semantic reference (§7.3).
    max_relation_hops: int = 2
    #: §11.2: a clarification with one option would be a confirmation in disguise.
    min_clarification_options: int = 2
    max_clarification_options: int = 4


DEFAULT_LIMITS = Limits()
