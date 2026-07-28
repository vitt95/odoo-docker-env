"""The condition language of the dictionary — what a T5 category and a T4 metric mean.

**Pure zone.**

## Why the dictionary needs its own condition language

A T5 category is a *named condition* (`06` §3.6). Writing it in the DSL of `03`
would be the obvious move and does not work: the DSL compares an attribute with a
**literal** (§8.2), and real categories compare an attribute with another
attribute — `sottoscorta` is `qty_available < reordering_min` — or with an
aggregate over a related entity — `clienti importanti` is *revenue over the last
twelve months above 50 000*.

So the language here is a **superset on comparisons and a subset on everything
else**: no free paths, no expressions, no negation of arbitrary depth, and above
all no free text. D59 requires that no field of a dictionary entry be free text
toward the model, and this is what satisfies it: a condition is a typed tree, and
what reaches the model is only the **term** that names it, never the condition.

## Why it is typed rather than a string

Three properties fall out of the structure, and each one closes a constraint of
D87 by construction instead of by discipline:

* `implied_fields()` — the **complete** set of fields the condition touches, and
  the reason V-D87-1 becomes structural. The declared-list approach had already
  failed in practice: `ai/corpus/lessico_l1.json` declares `campi_implicati:
  ["qty_available"]` for a condition that also reads `reordering_min`, so a user
  without access to the second field would have received the category anyway.
  Derived, that hole cannot exist;
* `is_time_dependent()` — whether resolving the condition needs the current
  instant. `fatture_scadute` is `invoice_date_due < oggi`, and V-D87-3 forbids the
  Applicator from expanding such a thing: a state carrying a resolved "today"
  would be a snapshot, and the corpus would stop being reproducible (D82);
* `cost_class()` — whether the condition is a plain comparison or an aggregate
  over another entity. V-D87-2 puts that in level 5, because D12 exists so that
  cost is computable a priori rather than estimated, and a category that hides a
  twelve-month aggregate would break that silently.
"""

from __future__ import annotations

from typing import Iterator

#: Comparison operators. Closed, and deliberately smaller than the DSL's
#: predicate set: a dictionary condition is authored by a person who knows the
#: data, not produced by a model, so it needs precision rather than breadth.
OPERATORS = frozenset({"eq", "ne", "lt", "le", "gt", "ge"})

#: Aggregation functions admitted in an aggregate condition (T4, and the T5
#: categories that rest on a metric). Same set as `03` §8.5 minus the ones that
#: make no sense as a threshold.
AGGREGATIONS = frozenset({"sum", "avg", "min", "max", "count", "count_distinct"})

#: The node kinds. Every condition is one of these; there is no default and no
#: "other".
KINDS = frozenset({
    # field <op> literal
    "compare",
    # field <op> field — the shape the DSL cannot express and real categories need
    "compare_field",
    # field in / not in a closed set of values
    "in",
    "not_in",
    # field is set / not set
    "is_set",
    "is_not_set",
    # field <op> now — the time-dependent family, kept separate so that
    # `is_time_dependent` is a structural property and not a string search
    "compare_now",
    # aggregate over a related entity, optionally over a window of days
    "aggregate",
    # boolean composition
    "all",
    "any",
    "not",
})

COMPOSITE_KINDS = frozenset({"all", "any", "not"})

#: Required keys per kind. Used by `validate`, which is the only way a malformed
#: condition is reported — a condition that cannot be validated cannot be trusted
#: to yield a complete set of implied fields, and the whole of V-D87-1 rests on
#: that completeness.
REQUIRED_KEYS: dict[str, frozenset[str]] = {
    "compare": frozenset({"kind", "field", "operator", "value"}),
    "compare_field": frozenset({"kind", "field", "operator", "other_field"}),
    "in": frozenset({"kind", "field", "values"}),
    "not_in": frozenset({"kind", "field", "values"}),
    "is_set": frozenset({"kind", "field"}),
    "is_not_set": frozenset({"kind", "field"}),
    "compare_now": frozenset({"kind", "field", "operator"}),
    "aggregate": frozenset({"kind", "entity", "function", "field", "operator", "value"}),
    "all": frozenset({"kind", "conditions"}),
    "any": frozenset({"kind", "conditions"}),
    "not": frozenset({"kind", "conditions"}),
}

OPTIONAL_KEYS: dict[str, frozenset[str]] = {
    # A window in days makes "revenue over the last twelve months" expressible
    # without a date literal, which would age.
    "aggregate": frozenset({"window_days", "through"}),
}

#: Cost classes, ordered from cheapest. `aggregate` is what V-D87-2 exists for.
COST_SIMPLE = "simple"
COST_AGGREGATE = "aggregate"


def validate(condition: object, path: str = "condition") -> list[str]:
    """Structural errors of a condition, empty when it is well formed."""
    errors: list[str] = []
    if not isinstance(condition, dict):
        return [f"{path}: expected an object, found {type(condition).__name__}"]

    kind = condition.get("kind")
    if kind not in KINDS:
        return [f"{path}.kind: {kind!r} is not one of {sorted(KINDS)}"]

    required = REQUIRED_KEYS[kind]
    allowed = required | OPTIONAL_KEYS.get(kind, frozenset())
    for key in sorted(required - condition.keys()):
        errors.append(f"{path}: '{key}' is required for kind '{kind}'")
    for key in sorted(condition.keys() - allowed):
        errors.append(f"{path}: '{key}' is not part of kind '{kind}'")

    if "operator" in condition and condition["operator"] not in OPERATORS:
        errors.append(
            f"{path}.operator: {condition['operator']!r} is not one of {sorted(OPERATORS)}"
        )
    if kind == "aggregate" and condition.get("function") not in AGGREGATIONS:
        errors.append(
            f"{path}.function: {condition.get('function')!r} is not one of "
            f"{sorted(AGGREGATIONS)}"
        )
    for key in ("field", "other_field", "entity"):
        if key in condition and (not isinstance(condition[key], str) or not condition[key]):
            errors.append(f"{path}.{key}: must be a non-empty string")
    if kind in ("in", "not_in"):
        values = condition.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"{path}.values: must be a non-empty list")

    if kind in COMPOSITE_KINDS:
        children = condition.get("conditions")
        if not isinstance(children, list) or not children:
            errors.append(f"{path}.conditions: must be a non-empty list")
        else:
            if kind == "not" and len(children) != 1:
                errors.append(f"{path}: 'not' takes exactly one condition")
            for index, child in enumerate(children):
                errors.extend(validate(child, f"{path}.conditions[{index}]"))
    return errors


def walk(condition: dict) -> Iterator[dict]:
    """Every node of the condition, parents before children."""
    yield condition
    if condition.get("kind") in COMPOSITE_KINDS:
        for child in condition.get("conditions", []):
            yield from walk(child)


def implied_fields(condition: dict) -> frozenset[str]:
    """**Every** field the condition reads.

    The completeness is the point. V-D87-1 says a category must not appear in the
    catalogue of a user who cannot read the fields that define it, and a declared
    list gets that wrong the first time someone adds a comparison — which is
    exactly what happened to `sottoscorta` in the corpus lexicon. Derived from the
    structure, the set cannot be incomplete unless the structure is.
    """
    found: set[str] = set()
    for node in walk(condition):
        # An aggregate reads its field on the *other* entity, so the name is
        # qualified: `fatture_cliente.imponibile` is not a field of the entity the
        # category belongs to, and the permission filter has to know that.
        prefix = f"{node['entity']}." if node.get("kind") == "aggregate" else ""
        for key in ("field", "other_field"):
            value = node.get(key)
            if isinstance(value, str) and value:
                found.add(prefix + value)
    return frozenset(found)


def implied_entities(condition: dict) -> frozenset[str]:
    """Entities other than the one the category belongs to, reached by aggregates.

    They matter for two reasons: the permission filter has to consider them too,
    and they are what makes the cost of a category non-local.
    """
    return frozenset(
        node["entity"] for node in walk(condition)
        if node.get("kind") == "aggregate" and isinstance(node.get("entity"), str)
    )


def is_time_dependent(condition: dict) -> bool:
    """Whether resolving the condition needs the current instant (V-D87-3).

    A structural property, not a search for the word "today": `compare_now` is its
    own kind precisely so this function cannot be fooled, and a windowed aggregate
    is time-dependent too — "the last twelve months" moves.
    """
    for node in walk(condition):
        if node.get("kind") == "compare_now":
            return True
        if node.get("kind") == "aggregate" and node.get("window_days") is not None:
            return True
    return False


def cost_class(condition: dict) -> str:
    """`aggregate` when the condition aggregates over another entity, else `simple`.

    Level 5 reads this (V-D87-2). It is the difference between a category that adds
    a `WHERE` clause and one that adds a twelve-month roll-up over a second table —
    and D12 exists so that difference is known before the query runs, not after.
    """
    for node in walk(condition):
        if node.get("kind") == "aggregate":
            return COST_AGGREGATE
    return COST_SIMPLE
