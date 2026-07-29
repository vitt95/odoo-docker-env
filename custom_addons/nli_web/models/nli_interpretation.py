"""The interpretation, written for a person (D64, D65, D67, `09` §3).

> Sto mostrando: **Ordini di vendita** · confermati · di **luglio 2026** ·
> raggruppati per **venditore** · ordinati per data d'ordine, dal più recente · primi 5

`09` §3.2 gives four rules for this sentence, and they are requirements rather than
style. **No technical name** — not a model, not a field, not an operator: the words are
the Semantic Dictionary's, which is to say the company's. **No syntax** — no brackets,
no literal `AND`, no comparison symbols. **The criteria are spelled out**: *«ordinati
per data»* is not enough, which date and in which direction. **First person, present
tense**: *«sto mostrando»* declares that an interpretation is happening and therefore
that there is something to check.

## Every part carries its origin, and the distinction must survive the loss of colour

D65 grades salience by `origin`: what the user asked for confirms itself, what the
system inferred has to be visible at a glance, what came from a default is discreet but
present. §3.3 adds the constraint that decides the shape: **it must work without
colour** — colour blindness, high contrast, print, cheap screens — so the parts carry
the origin as data and the interface marks it with form, position or text, using colour
only as reinforcement.

## Every part carries its provenance, for the cross-highlighting

§3.4 calls it *«l'interazione più efficace dell'intero prodotto»* for recognising a
misunderstanding: hovering *«luglio 2026»* lights up *«di questo mese»* in the sentence
the user wrote. It needs a pointing device, so §3.4 also requires an explicit
equivalent on mobile and for keyboard navigation — which is why the provenance travels
with the part rather than living in a tooltip.

## The period is shown resolved, and that is a requirement

§3.1: *«luglio 2026»*, not *«questo mese»*. An expression shown as the user wrote it
confirms itself and cannot be checked; the resolved period is what lets somebody notice
that the fiscal year starts in July, or that *«questa settimana»* began on Monday.
"""

from __future__ import annotations

from odoo import _, api, models

#: Two names are reserved by every Odoo model — `_fields` holds the field definitions
#: and `_order` the default ordering — so the parts that build those two pieces of the
#: sentence are named for what they produce instead. Shadowing either one breaks the
#: ORM at module load, which is exactly what it did.

#: How a predicate is said in words. Comparison symbols are forbidden by §3.2, and a
#: predicate the table does not know is shown by name rather than guessed: a wrong word
#: here is a misunderstanding manufactured by us.
PREDICATE_PHRASES = {
    "equals": lambda value: _("equal to %s") % value,
    "contains": lambda value: _("containing %s") % value,
    "starts_with": lambda value: _("starting with %s") % value,
    "is_one_of": lambda value: _("among %s") % value,
    "is_not_one_of": lambda value: _("not among %s") % value,
    "greater_than": lambda value: _("above %s") % value,
    "greater_or_equal": lambda value: _("from %s upwards") % value,
    "less_than": lambda value: _("below %s") % value,
    "less_or_equal": lambda value: _("up to %s") % value,
    "between": lambda value: _("between %s") % value,
    "approximately": lambda value: _("around %s") % value,
    "on": lambda value: _("on %s") % value,
    "before": lambda value: _("before %s") % value,
    "after": lambda value: _("after %s") % value,
    "within": lambda value: _("in %s") % value,
    "is_true": lambda value: _("yes"),
    "is_false": lambda value: _("no"),
    "is_set": lambda value: _("filled in"),
    "is_not_set": lambda value: _("empty"),
    "is_empty": lambda value: _("empty"),
    "is_not_empty": lambda value: _("filled in"),
}


class NliInterpretation(models.AbstractModel):
    _name = "nli.interpretation"
    _description = "AIDA interpretation, written for a person"

    @api.model
    def in_words(self, interpretation: dict, *, catalogue=None) -> dict:
        """The sentence, as parts an interface can mark up one by one.

        Returned as parts rather than as a string because §3.3 needs each one to carry
        its own origin and §3.4 its own provenance. A rendered sentence would force the
        interface to parse back out what this already knows.
        """
        terms = self._terms(catalogue)
        periods = {period["ref"]: period["resolved"]
                   for period in interpretation.get("periods") or ()}

        parts = [self._target(interpretation, terms)]
        parts += [self._condition(condition, terms, periods)
                  for condition in interpretation.get("conditions") or ()]
        parts += [self._group(entry, terms) for entry in interpretation.get("groups") or ()]
        parts += [self._measure(entry, terms)
                  for entry in interpretation.get("measures") or ()]
        parts += [self._ordering_part(entry, terms)
                  for entry in interpretation.get("order") or ()]
        if interpretation.get("fields"):
            parts.append(self._columns_part(interpretation["fields"], terms))
        if interpretation.get("limit"):
            parts.append(self._limit(interpretation["limit"]))
        if interpretation.get("presentation"):
            parts.append(self._view(interpretation["presentation"]))

        return {
            "lead": _("I am showing:"),
            "parts": [part for part in parts if part],
            "records": interpretation.get("records"),
            "truncated": interpretation.get("truncated", False),
        }

    # --- the parts ---------------------------------------------------------
    def _part(self, entry: dict, text: str, kind: str) -> dict:
        part = {"kind": kind, "text": text,
                "origin": entry.get("origin", "user"),
                "ref": entry.get("ref")}
        if entry.get("rule"):
            # §10.2: an inference declares the rule that produced it, or the user
            # cannot contradict it.
            part["rule"] = entry["rule"]
        if entry.get("provenance"):
            part["provenance"] = entry["provenance"]
        return part

    def _target(self, interpretation, terms):
        target = interpretation.get("target") or {}
        return self._part(target, self._word(target.get("ref"), terms), "target")

    def _condition(self, condition, terms, periods):
        reference = condition.get("ref")
        word = self._word(reference, terms)
        predicate = condition.get("predicate")

        if predicate == "is_category":
            # A named condition is already a word: *«scadute»*. Saying "state among
            # ..." would replace the company's word with the vendor's.
            return self._part(condition, word, "condition")

        value = self._value(condition, reference, periods)
        phrase = PREDICATE_PHRASES.get(predicate)
        said = phrase(value) if phrase else _("%(predicate)s %(value)s") % {
            "predicate": predicate, "value": value}
        return self._part(condition, f"{word} {said}".strip(), "condition")

    def _group(self, entry, terms):
        text = _("grouped by %s") % self._word(entry.get("ref"), terms)
        if entry.get("granularity"):
            text = _("%(text)s (%(granularity)s)") % {
                "text": text, "granularity": entry["granularity"]}
        return self._part(entry, text, "group")

    def _measure(self, entry, terms):
        return self._part(
            entry,
            _("%(function)s of %(what)s") % {"function": entry.get("function"),
                                             "what": self._word(entry.get("ref"), terms)},
            "measure")

    def _ordering_part(self, entry, terms):
        """*«ordinati per data»* is not enough: which date, and in which direction.

        §3.1 calls the ordering *«la sede del fraintendimento di "ultimi"»*, and §3.2
        requires the criterion to be spelled out rather than named.
        """
        direction = (_("newest first") if entry.get("direction") == "desc"
                     else _("oldest first"))
        return self._part(
            entry,
            _("ordered by %(what)s, %(direction)s") % {
                "what": self._word(entry.get("ref"), terms), "direction": direction},
            "order")

    def _columns_part(self, entries, terms):
        words = ", ".join(self._word(entry.get("ref"), terms) for entry in entries)
        origins = {entry.get("origin", "user") for entry in entries}
        return self._part(
            {"origin": "user" if origins == {"user"} else "inferred"},
            _("showing %s") % words, "fields")

    def _limit(self, limit):
        return self._part(limit, _("first %s") % limit.get("value"), "limit")

    def _view(self, presentation):
        return self._part(presentation, _("as %s") % presentation.get("view"), "view")

    # --- words --------------------------------------------------------------
    def _value(self, condition, reference, periods):
        """The value in words, with the period **resolved** (§3.1)."""
        if reference in periods:
            return periods[reference]
        value = condition.get("value") or {}
        kind = value.get("kind")
        if kind == "enum":
            return ", ".join(str(item) for item in value.get("items") or ())
        if kind == "temporal":
            # No resolved period reached us: showing the symbol would be a technical
            # name, and showing the user's own words would confirm itself. Saying that
            # the period is unresolved is the only honest option left.
            return _("(period not resolved)")
        for key in ("text", "value"):
            if key in value:
                return str(value[key])
        return ""

    def _terms(self, catalogue) -> dict:
        """Reference -> the company's own first word for it."""
        if catalogue is None:
            return {}
        terms = {}
        for attribute in getattr(catalogue, "attributes", ()):
            if attribute.terms:
                terms[attribute.ref] = attribute.terms[0]
        for category in getattr(catalogue, "categories", ()):
            if category.terms:
                terms[category.ref] = category.terms[0]
        for ref, names in getattr(catalogue, "entity_names", ()):
            if names:
                terms[ref] = names[0]
        return terms

    def _word(self, reference, terms) -> str:
        """The company's word, or the reference made readable.

        Never the technical name and never a guess: with no term for a reference the
        last resort is the reference itself with its separators softened, which is
        wrong-looking enough that somebody fixes the dictionary.
        """
        if not reference:
            return ""
        if reference in terms:
            return terms[reference]
        return reference.split(".")[-1].replace("_", " ")
