"""From a typed condition to an Odoo domain (D108).

The direction that matters for the approval path: a human writes the typed condition
while approving a saved filter, and this turns it into what the ORM executes. The
opposite direction — parsing an arbitrary Odoo domain into a typed condition — stays
forbidden by `06` §7, because that one is a guess and this one is mechanical.
"""

from __future__ import annotations

import unittest
from datetime import date, datetime

from ..dictionary import domains

OGGI = date(2026, 7, 29)


class TestDomainOf(unittest.TestCase):
    def _domain(self, condition, instant=OGGI):
        return domains.domain_of(condition, instant=instant)

    def test_a_comparison(self):
        self.assertEqual(
            self._domain({"kind": "compare", "field": "amount_total",
                          "operator": "gt", "value": 1000}),
            [("amount_total", ">", 1000)])

    def test_membership_and_its_negation(self):
        self.assertEqual(
            self._domain({"kind": "in", "field": "state", "values": ["draft"]}),
            [("state", "in", ["draft"])])
        self.assertEqual(
            self._domain({"kind": "not_in", "field": "payment_state",
                          "values": ["paid"]}),
            [("payment_state", "not in", ["paid"])])

    def test_set_and_unset(self):
        self.assertEqual(self._domain({"kind": "is_set", "field": "vat"}),
                         [("vat", "!=", False)])
        self.assertEqual(self._domain({"kind": "is_not_set", "field": "vat"}),
                         [("vat", "=", False)])

    def test_a_comparison_between_two_fields(self):
        """The shape the DSL cannot express and real categories need."""
        self.assertEqual(
            self._domain({"kind": "compare_field", "field": "amount_invoiced",
                          "operator": "lt", "other_field": "amount_total"}),
            [("amount_invoiced", "<", "amount_total")])

    # --- the clock ---------------------------------------------------------
    def test_the_instant_is_an_argument_and_not_a_clock(self):
        """*«Scadute»* is *due before today*: a domain frozen at approval time would
        be wrong the next morning (V-D87-3)."""
        condition = {"kind": "compare_now", "field": "invoice_date_due",
                     "operator": "lt"}
        self.assertEqual(self._domain(condition),
                         [("invoice_date_due", "<", OGGI)])
        self.assertEqual(self._domain(condition, instant=date(2027, 1, 1)),
                         [("invoice_date_due", "<", date(2027, 1, 1))])

    def test_a_datetime_instant_is_narrowed_to_its_date(self):
        self.assertEqual(
            self._domain({"kind": "compare_now", "field": "invoice_date_due",
                          "operator": "lt"},
                         instant=datetime(2026, 7, 29, 15, 30)),
            [("invoice_date_due", "<", OGGI)])

    # --- composition -------------------------------------------------------
    def test_a_conjunction_uses_odoo_s_prefix_notation(self):
        self.assertEqual(
            self._domain({"kind": "all", "conditions": [
                {"kind": "not_in", "field": "payment_state", "values": ["paid"]},
                {"kind": "compare_now", "field": "invoice_date_due", "operator": "lt"},
            ]}),
            ["&", ("payment_state", "not in", ["paid"]),
             ("invoice_date_due", "<", OGGI)])

    def test_a_disjunction(self):
        self.assertEqual(
            self._domain({"kind": "any", "conditions": [
                {"kind": "in", "field": "state", "values": ["draft"]},
                {"kind": "in", "field": "state", "values": ["sent"]},
            ]}),
            ["|", ("state", "in", ["draft"]), ("state", "in", ["sent"])])

    def test_three_operands_take_two_joiners(self):
        domain = self._domain({"kind": "all", "conditions": [
            {"kind": "is_set", "field": "vat"},
            {"kind": "is_set", "field": "email"},
            {"kind": "is_set", "field": "phone"},
        ]})
        self.assertEqual(domain[:2], ["&", "&"])
        self.assertEqual(len(domain), 5)

    def test_a_negation(self):
        self.assertEqual(
            self._domain({"kind": "not", "conditions": [
                {"kind": "in", "field": "state", "values": ["cancel"]}]}),
            ["!", ("state", "in", ["cancel"])])

    # --- what it refuses ---------------------------------------------------
    def test_an_invalid_condition_is_refused_before_anything_is_built(self):
        with self.assertRaises(domains.UntranslatableCondition):
            self._domain({"kind": "compare", "field": "amount_total"})

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(domains.UntranslatableCondition):
            self._domain({"kind": "telepathy", "field": "x"})

    def test_an_aggregate_is_refused_rather_than_approximated(self):
        """V-D87-2: an aggregate over a related entity is the reason level 5 exists.
        Translating it into something cheaper would answer a different question."""
        with self.assertRaises(domains.UntranslatableCondition) as refused:
            self._domain({"kind": "aggregate", "entity": "sale.order",
                          "field": "amount_total", "function": "sum",
                          "operator": "gt", "value": 50000})
        self.assertIn("level 5", str(refused.exception))


if __name__ == "__main__":
    unittest.main()
