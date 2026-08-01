"""The direction the user did not name, derived instead of guessed (D99).

The measurement that produced this file: `qwen3.5:9b`, 28/07/2026, twenty opening
cases. Two of the six `order_by` losses were not the model's — the corpus demanded
`desc` on `documenti_trasporto.stato` and on `opportunita.team`, neither of which is a
date, under a rule whose own name says *by date*. The contract had already named the
other rule (`text_attribute_implies_asc`, D88); nothing used it.
"""

from __future__ import annotations

import unittest

from ..application import applicator, completion
from ..contract import state as state_module
from ..contract.vocabulary import RULE_LATEST_DESC, RULE_TEXT_ASC
from ..validation import structural

TYPES = {
    "ordini_vendita.data_ordine": "date",
    "ordini_vendita.stato": "selection",
    "ordini_vendita.cliente": "many2one",
}


def _order(ref, **extra):
    return {"op": "add_order", "ref": ref,
            "provenance": {"text": "ordinati per x"}, **extra}


def _apply(operations):
    state = state_module.empty_state()
    state["target"] = {"ref": "ordini_vendita", "origin": "user"}
    return applicator.apply(state, operations).state


class TestDirectionCompletion(unittest.TestCase):
    def test_a_date_orders_from_the_most_recent(self):
        """"the latest orders" sorted ascending returns the oldest: an answer that
        looks right and is exactly backwards (D88)."""
        filled = completion.fill_inferred_directions(
            [_order("ordini_vendita.data_ordine")], TYPES)
        self.assertEqual(filled[0]["direction"], "desc")
        self.assertEqual(filled[0]["origin"], "inferred")

    def test_everything_that_is_not_a_date_orders_upwards(self):
        for ref in ("ordini_vendita.stato", "ordini_vendita.cliente"):
            with self.subTest(ref=ref):
                filled = completion.fill_inferred_directions([_order(ref)], TYPES)
                self.assertEqual(filled[0]["direction"], "asc")

    def test_a_direction_the_user_named_is_not_overwritten(self):
        """*"dal più recente"* is a request. Deriving over it would discard what the
        sentence said and leave no trace that it had been said."""
        filled = completion.fill_inferred_directions(
            [_order("ordini_vendita.stato", direction="desc", origin="user")], TYPES)
        self.assertEqual(filled[0]["direction"], "desc")
        self.assertEqual(filled[0]["origin"], "user")

    def test_an_unknown_reference_is_left_for_the_level_that_rejects_it(self):
        """Filling a direction for an invented reference would make a broken
        operation look complete. The Applicator still refuses it (D88), and level 3
        would refuse the reference itself."""
        operations = completion.fill_inferred_directions(
            [_order("oppurtunita.fase")], TYPES)
        self.assertNotIn("direction", operations[0])
        with self.assertRaises(applicator.ApplicationError):
            _apply(operations)

    def test_operations_that_carry_no_direction_are_untouched(self):
        original = [{"op": "set_limit", "value": 5},
                    {"op": "set_target", "ref": "ordini_vendita"}]
        self.assertEqual(completion.fill_inferred_directions(original, TYPES), original)

    # --- what reaches the state ------------------------------------------
    def test_the_state_declares_the_rule_that_produced_the_order(self):
        """§10.2: an inference the interface cannot name is one the user cannot
        contradict."""
        for ref, direction, rule in (
                ("ordini_vendita.data_ordine", "desc", RULE_LATEST_DESC),
                ("ordini_vendita.stato", "asc", RULE_TEXT_ASC)):
            with self.subTest(ref=ref):
                state = _apply(completion.fill_inferred_directions([_order(ref)], TYPES))
                entry = state["order_by"][0]
                self.assertEqual(entry["direction"], direction)
                self.assertEqual(entry["rule"], rule)

    def test_an_order_the_user_asked_for_declares_no_rule(self):
        """There is nothing to explain: the user said it."""
        state = _apply([_order("ordini_vendita.stato", direction="asc", origin="user")])
        self.assertNotIn("rule", state["order_by"][0])

    def test_the_completed_operations_still_satisfy_the_envelope(self):
        """The completion must not smuggle a key into an operation: §15.3 rejects
        unknown keys there, which is why the rule is derived and not carried."""
        envelope = {"dsl_version": "1.0", "outcome": "operations",
                    "operations": completion.fill_inferred_directions(
                        [_order("ordini_vendita.data_ordine")], TYPES)}
        self.assertEqual(structural.validate_envelope(envelope), [])


if __name__ == "__main__":
    unittest.main()
