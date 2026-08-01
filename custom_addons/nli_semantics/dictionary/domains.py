"""From a typed condition to the Odoo domain that executes it (D108).

**Pure zone.** The typed condition language of `conditions.py` names Odoo fields but
knows nothing about Odoo, and this module is the same: it turns a validated tree into
the list of tuples the ORM expects, and takes the instant as an argument rather than
reading a clock. That is what lets the whole translation be tested without a database
and what keeps the Applicator's purity intact (V-D87-3).

## Why the translation lives here and not in the approval form

`06` §7 and `filters.py` say the **domain of a saved filter is never translated
automatically** into a typed condition: parsing arbitrary Odoo expressions and getting
it subtly wrong produces a category that means something *close to* what was meant,
which is the failure a category exists to remove. That rule governs the direction
`domain -> typed condition`, which is a guess.

This module goes the **other way**, and the other way is mechanical: a validated typed
condition has one reading, and there is nothing to guess. The human writes the typed
condition during approval; the machine turns it into a domain, every time, identically.

## The clock is an argument

*«Scadute»* is *due date before today*, and a domain frozen at approval time would be
wrong the next morning. `compare_now` is resolved at every execution against the
instant handed in — the same reason V-D87-3 forbids the Applicator from expanding a
category.
"""

from __future__ import annotations

from . import conditions as conditions_module

#: Typed operator -> Odoo operator. `eq` and `ne` are spelled out rather than mapped
#: through a dictionary comprehension so that an operator added to the language
#: without a translation here fails loudly instead of silently producing `=`.
OPERATORS = {
    "eq": "=", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">=",
}


class UntranslatableCondition(Exception):
    """The condition cannot be executed as a domain, and saying so is the answer.

    Raised rather than returned because there is no partial domain worth having: a
    category that filters on half of its own definition returns records that look
    right and are not.
    """


def domain_of(condition: dict, *, instant) -> list:
    """The Odoo domain of a validated typed condition.

    The condition **must** have passed `conditions.validate` first: this function
    reads keys it assumes are there, and validating twice in two places is how the
    two validations end up disagreeing.
    """
    problems = conditions_module.validate(condition)
    if problems:
        raise UntranslatableCondition("; ".join(problems))
    return _node(condition, instant)


def _node(condition: dict, instant) -> list:
    kind = condition["kind"]

    if kind == "all":
        return _composite(condition, instant, joiner="&")
    if kind == "any":
        return _composite(condition, instant, joiner="|")
    if kind == "not":
        return ["!", *_node(condition["conditions"][0], instant)] \
            if len(condition["conditions"]) == 1 \
            else ["!", *_composite(condition, instant, joiner="&")]

    if kind == "compare":
        return [(condition["field"], OPERATORS[condition["operator"]],
                 condition["value"])]
    if kind == "compare_field":
        # `field <op> other_field` — the shape the DSL cannot express and real
        # categories need: *"invoiced less than ordered"*.
        return [(condition["field"], OPERATORS[condition["operator"]],
                 condition["other_field"])]
    if kind == "in":
        return [(condition["field"], "in", list(condition["values"]))]
    if kind == "not_in":
        return [(condition["field"], "not in", list(condition["values"]))]
    if kind == "is_set":
        return [(condition["field"], "!=", False)]
    if kind == "is_not_set":
        return [(condition["field"], "=", False)]
    if kind == "compare_now":
        return [(condition["field"], OPERATORS[condition["operator"]],
                 _now(instant))]

    if kind == "aggregate":
        # V-D87-2: an aggregate over a related entity is not a domain fragment. It is
        # the reason level 5 exists and the reason `cost_class` travels with the
        # catalogue — a category resting on one is refused before it is executed, not
        # translated into something cheaper that means something else.
        raise UntranslatableCondition(
            "an aggregate category cannot be executed as a domain: it needs the "
            "cost path of level 5 (V-D87-2), not a translation"
        )

    raise UntranslatableCondition(f"no domain for a condition of kind {kind!r}")


def _composite(condition: dict, instant, *, joiner: str) -> list:
    """Odoo's prefix notation: n-1 joiners in front of n operands."""
    parts = [_node(child, instant) for child in condition["conditions"]]
    if not parts:
        raise UntranslatableCondition("a composite condition with no operands")
    domain: list = [joiner] * (len(parts) - 1)
    for part in parts:
        domain.extend(part)
    return domain


def _now(instant):
    """The instant in the shape a comparison against a date field expects.

    A `date` field compared against a `datetime` is a comparison Odoo will make
    surprising, so a datetime is narrowed to its date. Recognised by asking the value
    what it can do rather than by importing `datetime`: this zone is *«a function of
    its arguments»* (`tools/arch/spec.py`), and the clock enters it as one.
    """
    narrow = getattr(instant, "date", None)
    return narrow() if callable(narrow) else instant
