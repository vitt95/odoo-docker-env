"""The readings a refusal offers instead of stopping (D106).

D105 turns an invented filter into a refusal. Measured on 80 openings: eleven wrong
filters became refusals and no correct one did. But a bare refusal leaves the user
where they were — these are the options that make it a question.
"""

from __future__ import annotations

import unittest

from ..application import alternatives

CANDIDATES = ("ordini.in_bozza", "ordini.da_consegnare", "ordini.confermati",
              "ordini.da_fatturare")


def _condition(ref, text):
    return {"op": "add_condition", "combine": "all",
            "condition": {"ref": ref, "predicate": "is_category"},
            "provenance": {"text": text}}


OPERATIONS = [
    {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
    _condition("ordini.in_bozza", "lo scorso mese"),
    {"op": "set_limit", "value": 5, "provenance": {"text": "i primi 5"}},
]


class TestAlternatives(unittest.TestCase):
    def _readings(self, **overrides):
        arguments = {"ungrounded": ["ordini.in_bozza"], "candidates": CANDIDATES}
        arguments.update(overrides)
        return alternatives.for_ungrounded(OPERATIONS, **arguments)

    def test_the_first_reading_is_the_sentence_without_the_condition(self):
        """The safe one, and the only one always available: the user said nothing
        that names a condition, so not filtering is a faithful reading."""
        first = self._readings()[0]
        self.assertEqual(first.kind, "without")
        self.assertIsNone(first.ref)
        self.assertEqual([operation["op"] for operation in first.operations],
                         ["set_target", "set_limit"])

    def test_the_others_replace_the_reference_and_keep_the_rest(self):
        second = self._readings()[1]
        self.assertEqual(second.kind, "instead")
        self.assertEqual(second.ref, "ordini.da_consegnare")
        self.assertEqual(second.operations[1]["condition"]["ref"], "ordini.da_consegnare")
        self.assertEqual(second.operations[2], OPERATIONS[2])

    def test_the_condition_that_was_refused_is_not_proposed_again(self):
        proposed = {reading.ref for reading in self._readings()}
        self.assertNotIn("ordini.in_bozza", proposed)

    def test_a_condition_the_sentence_already_carries_is_not_proposed(self):
        """Offering a condition the user is already under is not a choice."""
        operations = [*OPERATIONS, _condition("ordini.confermati", "confermati")]
        readings = alternatives.for_ungrounded(
            operations, ungrounded=["ordini.in_bozza"], candidates=CANDIDATES)
        self.assertNotIn("ordini.confermati", {reading.ref for reading in readings})

    def test_the_contract_s_bounds_are_respected(self):
        """§4.4 admits from two to four options: fewer is not a question, more is a
        list nobody reads."""
        self.assertLessEqual(len(self._readings()), alternatives.MAX_OPTIONS)
        self.assertGreaterEqual(len(self._readings()), alternatives.MIN_OPTIONS)

    def test_without_candidates_there_is_no_question_to_ask(self):
        """One option is not a choice, and a refusal that pretends to offer one is
        worse than a refusal that admits there is none."""
        self.assertEqual(self._readings(candidates=()), [])

    def test_nothing_is_offered_when_the_reference_is_not_in_the_operations(self):
        self.assertEqual(self._readings(ungrounded=["ordini.mai_vista"]), [])

    def test_the_original_operations_are_not_touched(self):
        prima = [dict(operation) for operation in OPERATIONS]
        self._readings()
        self.assertEqual(OPERATIONS, prima)
        self.assertEqual(OPERATIONS[1]["condition"]["ref"], "ordini.in_bozza")

    def test_only_the_first_ungrounded_condition_is_questioned(self):
        """Two axes in one question would need a matrix of options, and the contract
        admits a list."""
        readings = self._readings(ungrounded=["ordini.in_bozza", "ordini.altro"])
        self.assertTrue(all(
            "ordini.in_bozza" not in str(reading.operations) for reading in readings))


if __name__ == "__main__":
    unittest.main()
