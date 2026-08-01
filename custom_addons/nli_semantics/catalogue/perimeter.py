"""What the user may say, taken from what the system can do (D104).

**Pure zone.** This builds the *structure* of the perimeter — which references, of
which kind — and not one word of it. The words come from two places and neither is
here: the customer's terms travel with the catalogue, and the product's phrasings for
periods and comparisons belong to the layer that has the user's language.

## Why the perimeter exists

The measured failure it answers is not the model's. `13-perimetro-guidato.md` §1.2: the
user faces an empty box with **no indication of what the system can do**, has to guess,
and when the guess fails the refusal does not say what to write instead. Meanwhile the
system already holds the list of words it knows — and shows it only to the model.

## Why it is suggested and never imposed

Restricting the admitted language would turn the product into a dropdown form with a
text box in front, and Odoo has dropdown forms. The person this exists for is the one
who does **not** know where the filter is. Restricting would also raise the measured
accuracy by removing the hard cases, which is a number that means nothing.

## What is deliberately left out

A period that needs an argument — *«ultimi N giorni»* — is not a suggestion: offering
it without the N would produce a phrase the user has to finish and the system cannot
execute. The same for absolute dates, which are the user's to write. Only the
self-contained expressions are offered.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The kinds of suggestion, which are also the groups the interface shows.
CONDITION = "condition"
PERIOD = "period"
COMPARISON = "comparison"
COLUMN = "column"

#: Types on which a comparison can be offered. A comparison on a text or a relation is
#: not a suggestion, it is the mistake D103 made unexpressible.
COMPARABLE_TYPES = frozenset({"number", "date", "datetime"})


@dataclass(frozen=True)
class Suggestion:
    """One thing the user may say, and what it would name."""

    group: str
    #: The semantic reference, for everything that comes from the catalogue.
    ref: str = ""
    #: The customer's own word for it, first of the catalogue's terms. Empty for a
    #: period, whose wording is the product's and not the customer's.
    label: str = ""
    #: The temporal expression, for a period.
    symbol: str = ""


def of(catalogue, *, periods=()) -> list[Suggestion]:
    """The perimeter of one entity, in the order the interface shows it.

    Conditions first because they are the shortest thing a user can say and the one
    that most often answers the whole question; columns last because they refine an
    answer rather than produce one.

    `periods` is handed in rather than read from the contract because this zone is *«a
    function of its arguments»* (`tools/arch/spec.py`): the exposure rules, the budget
    and the three phases must be reproducible without a database, and an import of the
    contract here would be the first crack in that. The caller passes the expressions
    that **mean something on their own** — the punctual ones, the current and previous
    periods, and year-to-date. `last_n_days` and the absolute dates are excluded on
    purpose: a suggestion the user has to finish is not a suggestion.
    """
    suggestions: list[Suggestion] = []

    for category in catalogue.categories:
        suggestions.append(Suggestion(
            group=CONDITION, ref=category.ref,
            label=category.terms[0] if category.terms else category.ref))

    for symbol in sorted(periods):
        suggestions.append(Suggestion(group=PERIOD, symbol=symbol))

    for attribute in catalogue.attributes:
        label = attribute.terms[0] if attribute.terms else attribute.ref
        if attribute.type in COMPARABLE_TYPES:
            suggestions.append(Suggestion(
                group=COMPARISON, ref=attribute.ref, label=label))
        suggestions.append(Suggestion(group=COLUMN, ref=attribute.ref, label=label))

    return suggestions


def grouped(catalogue, *, periods=()) -> dict[str, list[Suggestion]]:
    """The same, keyed by group, for an interface that renders one block each."""
    groups: dict[str, list[Suggestion]] = {
        CONDITION: [], PERIOD: [], COMPARISON: [], COLUMN: []}
    for suggestion in of(catalogue, periods=periods):
        groups[suggestion.group].append(suggestion)
    return groups
