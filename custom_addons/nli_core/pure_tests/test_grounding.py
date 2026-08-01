"""A named condition must be grounded in what the user said (D105).

The measurement that produced this file: `qwen3.5:9b`, 29/07/2026, eighty openings.
Twelve failures out of twenty-one on `filter` were the same one — a fragment naming no
condition turned into a named condition, because a named condition is the cheapest
thing to write: no value, no kind, no expression.

    'voglio vedere ordini lo scorso mese i primi 5'
      -> is_category(ordini_vendita.in_bozza)   provenance: "lo scorso mese"

Nothing in that sentence says *draft*. The check compares the fragment the operation
declares as its own origin against the terms of the condition it names, which is two
lists, not a reading of Italian.
"""

from __future__ import annotations

import unittest

from ..validation import contextual

TERMS = {
    "ordini.in_bozza": ("in bozza", "da confermare", "provvisori", "non confermati"),
    "ordini.da_consegnare": ("da consegnare", "da evadere"),
}


def mentions(reference: str, text: str) -> bool:
    """A deliberately literal matcher: this file tests the **rule**, not the matching.

    Tolerance for typos, accents and abbreviations belongs to the dictionary and is
    tested where it lives (`nli_semantics`), against phase A's own index. Testing it
    twice, with two different notions of *the same word*, is how the two would drift.
    """
    return any(term in text.casefold() for term in TERMS.get(reference, ()))


def _state(*conditions):
    return {
        "dsl_version": "1.0",
        "target": {"ref": "ordini", "origin": "user"},
        "filter": ({"connective": "all", "conditions": list(conditions)}
                   if len(conditions) > 1 else conditions[0]),
        "limit": {"value": 80, "origin": "default"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }


def _category(ref, text, identifier="c1"):
    return {"id": identifier, "ref": ref, "predicate": "is_category",
            "origin": "user", "provenance": {"text": text}}


class TestGrounding(unittest.TestCase):
    def test_a_condition_the_sentence_asked_for_passes(self):
        failures = contextual.validate_grounding(
            _state(_category("ordini.in_bozza", "da confermare")), mentions=mentions)
        self.assertEqual(failures, [])

    def test_the_measured_failure_is_refused(self):
        """The case above, verbatim."""
        failures = contextual.validate_grounding(
            _state(_category("ordini.in_bozza", "lo scorso mese")), mentions=mentions)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].code, "ungrounded_category")
        self.assertEqual(failures[0].level, 3)
        self.assertIn("lo scorso mese", failures[0].detail)

    def test_a_condition_with_no_provenance_is_refused(self):
        """There is nothing that shows the user asked for it, and a condition nobody
        can trace to a fragment is exactly what §10.3 exists to prevent."""
        condition = _category("ordini.in_bozza", "")
        del condition["provenance"]
        self.assertEqual(
            len(contextual.validate_grounding(_state(condition), mentions=mentions)), 1)

    def test_each_condition_is_judged_on_its_own(self):
        failures = contextual.validate_grounding(
            _state(_category("ordini.da_consegnare", "da evadere", "c1"),
                   _category("ordini.in_bozza", "questo mese", "c2")),
            mentions=mentions)
        self.assertEqual([failure.path for failure in failures], ["ordini.in_bozza"])

    def test_only_named_conditions_are_judged(self):
        """A comparison carries a value the user said; there is no vocabulary to
        check it against, and inventing one would refuse legitimate filters."""
        comparison = {"id": "c1", "ref": "ordini.importo", "predicate": "greater_than",
                      "value": {"kind": "number", "value": 1000},
                      "origin": "user", "provenance": {"text": "sopra 1000"}}
        self.assertEqual(
            contextual.validate_grounding(_state(comparison), mentions=mentions), [])

    def test_a_condition_from_an_earlier_turn_is_not_refused(self):
        """A refinement carries forward the conditions of the previous turns, whose
        fragments belong to sentences nobody is saying any more. The check compares
        the condition against **its own** provenance, so the second turn of a
        conversation does not reject the first."""
        state = _state(_category("ordini.da_consegnare", "da evadere", "c1"),
                       _category("ordini.in_bozza", "da confermare", "c2"))
        self.assertEqual(contextual.validate_grounding(state, mentions=mentions), [])

    # --- how it is wired into the chain -----------------------------------
    def test_the_chain_runs_it_when_a_matcher_is_given(self):
        state = _state(_category("ordini.in_bozza", "lo scorso mese"))
        known = frozenset({"ordini", "ordini.in_bozza"})
        self.assertEqual(
            contextual.validate(state, known_refs=known, types={}), [],
            "without a matcher there is nothing to check the grounding with")
        failures = contextual.validate(state, known_refs=known, types={},
                                       mentions=mentions)
        self.assertEqual([failure.code for failure in failures], ["ungrounded_category"])


if __name__ == "__main__":
    unittest.main()
