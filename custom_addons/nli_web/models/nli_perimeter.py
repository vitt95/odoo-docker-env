"""The perimeter as the interface shows it: the structure, plus the words (D104).

`nli_semantics/catalogue/perimeter.py` decides **what** may be suggested and cannot say
it: that zone is a function of its arguments and has no language. This is the other
half — the wording — and it lives here because here there is a user, and a user has a
language.

## Two kinds of word, and only one of them is ours

The customer's terms — *«scadute»*, *«da evadere»*, the name of a column — come from
the catalogue and are shown **as the customer wrote them**. Translating them would
replace the company's vocabulary with the vendor's, which is the opposite of what a
dictionary built from the installation is for.

The product's phrasings — the periods, the shape of a comparison — are ours, closed,
and the same for every installation. They go through `_()` like any other product
string.

## What it is not

It is not a filter builder. Everything here is a suggestion the user may ignore, and
the box stays free text: `13-perimetro-guidato.md` §3 gives the three arguments for
which restricting the language would remove the reason this product exists.
"""

from __future__ import annotations

from odoo import _, api, models
from odoo.addons.nli_core.contract import vocabulary
from odoo.addons.nli_semantics.catalogue import perimeter as perimeter_module

#: Periods worth suggesting: the ones that mean something on their own. The parametric
#: family (`last_n_days`) and the absolute dates are excluded — a suggestion the user
#: has to finish is not a suggestion. The rule is argued in `perimeter.of`.
OFFERED_PERIODS = frozenset(
    vocabulary.TEMPORAL_PUNCTUAL
    | vocabulary.TEMPORAL_CURRENT
    | vocabulary.TEMPORAL_PREVIOUS
    | vocabulary.TEMPORAL_TO_DATE
)


def _period_labels() -> dict:
    """The product's words for the closed set of periods.

    Written out one by one rather than generated from the symbol: *«year_to_date»* is
    not *«anno a data»*, and a rule that produced that would be a rule nobody could
    correct without changing code.
    """
    return {
        "today": _("today"),
        "yesterday": _("yesterday"),
        "tomorrow": _("tomorrow"),
        "current_week": _("this week"),
        "current_month": _("this month"),
        "current_quarter": _("this quarter"),
        "current_year": _("this year"),
        "previous_week": _("last week"),
        "previous_month": _("last month"),
        "previous_quarter": _("last quarter"),
        "previous_year": _("last year"),
        "year_to_date": _("since the start of the year"),
    }


class NliPerimeter(models.AbstractModel):
    _name = "nli.perimeter"
    _description = "AIDA guided perimeter — what the user may say"

    @api.model
    def for_entity(self, entity_ref: str, *, context_window: int = 32_000) -> dict:
        """The suggestions for one entity, ready to render.

        Built on the **caller's** catalogue: the perimeter of a user who cannot read
        the amounts must not contain the amounts, and the way to guarantee that is to
        derive it from the same catalogue the model is shown rather than from a list
        assembled anywhere else.
        """
        semantics_model = self.env["nli.semantics"]
        semantics = semantics_model.semantics(semantics_model.entity_scope())
        catalogue = semantics_model.catalogue_for(
            semantics, entity_ref, context_window=context_window)
        return self.of_catalogue(catalogue)

    @api.model
    def of_catalogue(self, catalogue) -> dict:
        """The same, from a catalogue already built. Separated so the wording can be
        tested without a scope, a fingerprint and a database behind it."""
        labels = _period_labels()
        groups = perimeter_module.grouped(catalogue, periods=OFFERED_PERIODS)

        def rendered(suggestion):
            if suggestion.group == perimeter_module.PERIOD:
                return {"kind": suggestion.group, "symbol": suggestion.symbol,
                        "label": labels.get(suggestion.symbol, suggestion.symbol)}
            if suggestion.group == perimeter_module.COMPARISON:
                # The shape of what to say, not a value: the number is the user's.
                return {"kind": suggestion.group, "ref": suggestion.ref,
                        "label": _("%s above …") % suggestion.label}
            return {"kind": suggestion.group, "ref": suggestion.ref,
                    "label": suggestion.label}

        return {
            "entity": catalogue.entity,
            "groups": [
                {"kind": kind, "title": title,
                 "items": [rendered(suggestion) for suggestion in groups[kind]]}
                for kind, title in (
                    (perimeter_module.CONDITION, _("ready conditions")),
                    (perimeter_module.PERIOD, _("periods")),
                    (perimeter_module.COMPARISON, _("comparisons")),
                    (perimeter_module.COLUMN, _("columns")),
                )
                if groups[kind]
            ],
        }
