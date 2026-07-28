"""The seven entry types of the dictionary, and their closed vocabulary (D30, D59).

**Pure zone.**

`06` §3.1 says the vocabulary is closed here too, for the same reason it is closed
in the contract: a type nobody enumerated cannot be validated, and an entry that
validates against nothing is an entry that reaches the model unchecked.

## The distinction that governs everything else

D29 splits the entries in two classes, and `06` §3.9 assigns each type to one:

* **vocabulary** — widens what the system recognises and **changes no existing
  result**. T1, T2, T6, T7;
* **definition** — changes results, so it is versioned, its changes are tracked,
  and the owners of affected saved queries are notified (`06` §4.3, §15.6 of the
  DSL). T3, T4, T5.

The class is a property of the **type**, not of the edit, and that is what makes
the notification computable exactly rather than estimated. It is also why D87 was
decided the way it was: exposing a T5 category as a boolean attribute would have
made a definition look like vocabulary at the one layer where the difference is
enforced.

## Phase 1 needs four of the seven

The registry's §6.5 is explicit: declaring seven does not oblige implementing
seven. **T1** (naming), **T2** (enumerated value), **T3** (vagueness resolver) and
**T5** (category) are the types the interrogation path crosses. T4 becomes
necessary when aggregations are exposed; T6 and T7 are refinements of the
experience. Their declarations are here — the vocabulary closes now, additively
(C7) — and `PHASE_1_TYPES` records which ones the code must handle today.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import conditions as conditions_module

#: The four dictionary levels (`06` §2.1). L3 is a **queue**, not an active level.
LEVELS = ("L0", "L1", "L2", "L3")

#: Precedence: the customer always has the last word (`06` §2.2). L3 does not take
#: part — an automatically learned entry that applied itself would be
#: self-reinforcing, and no indicator would flag it (D28).
ACTIVE_LEVELS_BY_PRECEDENCE = ("L2", "L1", "L0")

#: The seven types (`06` §3).
TYPES = ("T1", "T2", "T3", "T4", "T5", "T6", "T7")

#: What each type is, for messages and reports.
TYPE_NAMES: dict[str, str] = {
    "T1": "naming",
    "T2": "enumerated value",
    "T3": "vagueness resolver",
    "T4": "business metric",
    "T5": "category",
    "T6": "disambiguation preference",
    "T7": "promoted reference",
}

VOCABULARY_TYPES = frozenset({"T1", "T2", "T6", "T7"})
DEFINITION_TYPES = frozenset({"T3", "T4", "T5"})

#: Implemented in phase 1 (registry §6.5). The others are declared and rejected by
#: `validate_entry` until they are needed, so an unimplemented type cannot reach
#: the catalogue and be silently ignored there.
PHASE_1_TYPES = frozenset({"T1", "T2", "T3", "T5"})

#: Resolver rule kinds (T3). Typed, because D59 forbids free text: a resolver
#: written as prose would be a rule nobody can apply and everybody can reinterpret.
RESOLVER_KINDS: dict[str, frozenset[str]] = {
    # "circa centomila" -> +/- percent
    "relative_percent": frozenset({"percent"}),
    # "gli ordini recenti" -> the last n days
    "last_n_days": frozenset({"days"}),
    # "a breve" -> the next n days
    "next_n_days": frozenset({"days"}),
    # "circa" on a count -> +/- an absolute amount
    "absolute_tolerance": frozenset({"amount"}),
}

#: Keys required and admitted per entry type.
REQUIRED_KEYS: dict[str, frozenset[str]] = {
    "T1": frozenset({"type", "level", "ref", "terms"}),
    "T2": frozenset({"type", "level", "ref", "value", "terms"}),
    "T3": frozenset({"type", "level", "name", "rule"}),
    "T4": frozenset({"type", "level", "name", "entity", "aggregate", "terms"}),
    "T5": frozenset({"type", "level", "ref", "entity", "terms", "condition"}),
    "T6": frozenset({"type", "level", "ambiguity", "chosen_ref"}),
    "T7": frozenset({"type", "level", "ref", "path", "terms"}),
}

OPTIONAL_KEYS: dict[str, frozenset[str]] = {
    # A term without a language is not an omission: internal acronyms, product
    # codes and process names have no language, and forcing one would duplicate
    # the entry in every active language (`06` §10.4).
    "T1": frozenset({"languages", "version"}),
    "T2": frozenset({"languages", "version"}),
    "T3": frozenset({"terms", "languages", "version"}),
    "T4": frozenset({"languages", "version", "condition"}),
    "T5": frozenset({"languages", "version"}),
    "T6": frozenset({"observed_share", "version"}),
    "T7": frozenset({"languages", "version"}),
}


@dataclass(frozen=True)
class EntryProblem:
    """One structural defect of one entry."""

    entry_type: str
    identifier: str
    detail: str

    def __str__(self) -> str:
        return f"{self.entry_type} {self.identifier}: {self.detail}"


def identifier_of(entry: dict) -> str:
    """What names the entry — `ref`, or `name` for the types that have no ref."""
    for key in ("ref", "name", "ambiguity"):
        if entry.get(key):
            return str(entry[key])
    return "<unnamed>"


def validate_entry(entry: object) -> list[EntryProblem]:
    """Structural validation of one entry. Empty means well formed.

    Deliberately strict about unknown keys, for the reason §15.3 of the DSL gives
    about the contract and which applies here with more force: the dictionary feeds
    the catalogue, the catalogue reaches the model, and a key nobody validated is
    an input nobody checked (`06` §2.3).
    """
    if not isinstance(entry, dict):
        return [EntryProblem("?", "<not an object>",
                             f"expected an object, found {type(entry).__name__}")]

    entry_type = entry.get("type")
    identifier = identifier_of(entry)
    if entry_type not in TYPES:
        return [EntryProblem(str(entry_type), identifier,
                             f"unknown type; admitted: {list(TYPES)}")]

    problems: list[EntryProblem] = []

    def problem(detail: str) -> None:
        problems.append(EntryProblem(entry_type, identifier, detail))

    if entry_type not in PHASE_1_TYPES:
        problem(
            f"type {entry_type} ({TYPE_NAMES[entry_type]}) is declared but not "
            "implemented in phase 1 (registry §6.5). Rejected rather than ignored: "
            "an entry silently dropped is a term the user says and the system "
            "never learns to recognise"
        )
        return problems

    required = REQUIRED_KEYS[entry_type]
    allowed = required | OPTIONAL_KEYS[entry_type]
    for key in sorted(required - entry.keys()):
        problem(f"'{key}' is required")
    for key in sorted(entry.keys() - allowed):
        problem(f"'{key}' is not part of a {entry_type} entry")

    if entry.get("level") not in LEVELS:
        problem(f"level {entry.get('level')!r} is not one of {list(LEVELS)}")
    elif entry["level"] == "L3":
        problem(
            "L3 is a queue, not an active level: an entry becomes active only by "
            "approval, and it enters as L2 (D28)"
        )

    terms = entry.get("terms")
    if "terms" in required or terms is not None:
        if not isinstance(terms, list) or not terms:
            problem("'terms' must be a non-empty list")
        elif not all(isinstance(term, str) and term.strip() for term in terms):
            problem("every term must be a non-empty string")

    if entry_type == "T3":
        problems.extend(_validate_resolver(entry, entry_type, identifier))
    if entry_type == "T5":
        problems.extend(_validate_category(entry, entry_type, identifier))

    # A definition carries a version; vocabulary does not need one. D29 makes the
    # distinction operative: without a version, a changed threshold cannot be
    # traced and the owners of the affected saved queries cannot be told.
    if entry_type in DEFINITION_TYPES and not entry.get("version"):
        problem(
            "a definition entry carries a version: without it a changed meaning "
            "cannot be traced, and the notification of D29 becomes an estimate"
        )

    return problems


def _validate_resolver(entry: dict, entry_type: str, identifier: str) -> list[EntryProblem]:
    rule = entry.get("rule")
    if not isinstance(rule, dict):
        return [EntryProblem(entry_type, identifier, "'rule' must be an object")]
    kind = rule.get("kind")
    if kind not in RESOLVER_KINDS:
        return [EntryProblem(
            entry_type, identifier,
            f"resolver kind {kind!r} is not one of {sorted(RESOLVER_KINDS)}",
        )]
    problems: list[EntryProblem] = []
    expected = RESOLVER_KINDS[kind] | {"kind"}
    for key in sorted(expected - rule.keys()):
        problems.append(EntryProblem(entry_type, identifier,
                                     f"rule of kind '{kind}' requires '{key}'"))
    for key in sorted(rule.keys() - expected):
        problems.append(EntryProblem(entry_type, identifier,
                                     f"'{key}' is not part of rule kind '{kind}'"))
    for key, value in rule.items():
        if key != "kind" and not isinstance(value, (int, float)):
            problems.append(EntryProblem(entry_type, identifier,
                                         f"rule.{key} must be a number"))
    return problems


def _validate_category(entry: dict, entry_type: str, identifier: str) -> list[EntryProblem]:
    condition = entry.get("condition")
    if condition is None:
        return []
    return [
        EntryProblem(entry_type, identifier, detail)
        for detail in conditions_module.validate(condition)
    ]


# ---------------------------------------------------------------------------
# Derived properties of a category (the three constraints of D87)
# ---------------------------------------------------------------------------

def category_implied_refs(entry: dict) -> frozenset[str]:
    """Semantic references a T5 category reads, qualified with its entity.

    **V-D87-1.** The permission filter uses this set: a category whose fields the
    user cannot read must not appear in that user's catalogue, or D87 opens a path
    towards unauthorised data with normal accuracy and normal latency.

    Derived from the condition, never declared. The declared form had already
    failed: `sottoscorta` compares `qty_available` with `reordering_min` and
    declared only the first.
    """
    entity = entry.get("entity", "")
    refs: set[str] = set()
    for field in conditions_module.implied_fields(entry.get("condition") or {}):
        # Fields reached through an aggregate are already qualified with their own
        # entity; the others belong to the category's entity.
        refs.add(field if "." in field else f"{entity}.{field}")
    return frozenset(refs)


def category_is_time_dependent(entry: dict) -> bool:
    """**V-D87-3.** Whether resolving the category needs the current instant."""
    return conditions_module.is_time_dependent(entry.get("condition") or {})


def category_cost_class(entry: dict) -> str:
    """**V-D87-2.** `simple` or `aggregate`; level 5 reads it."""
    return conditions_module.cost_class(entry.get("condition") or {})
