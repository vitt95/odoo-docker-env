"""Levels 4 and 5, the dictionary-free half (§12.5, §12.6).

The completion criterion of part 2 includes "incoherent cases are rejected".
These are the incoherences detectable without the Semantic Dictionary; the ones
that need an attribute's type — `contains` on a number, `sum` on text — arrive in
part 4 with resolution, and their absence here is deliberate rather than
overlooked.
"""

from __future__ import annotations

import unittest

from ..application import applicator
from ..contract import state as state_module
from ..contract.vocabulary import Limits
from ..validation import coherence


def codes(failures) -> set[str]:
    return {failure.code for failure in failures}


def base_state(**sections) -> dict:
    state = {
        "dsl_version": "1.0",
        "target": {"ref": "ordini_vendita", "origin": "user"},
        "limit": {"value": 80, "origin": "default"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }
    state.update(sections)
    return state


def leaf(ref: str, predicate: str = "is_true", identifier: str = "c1", **extra) -> dict:
    return {"id": identifier, "ref": ref, "predicate": predicate, "origin": "user", **extra}


class TestEnvelopeCoherence(unittest.TestCase):
    def test_two_set_limit_with_different_values(self):
        """§4.5 — not a conflict to resolve with a precedence rule.

        A precedence rule would consolidate an arbitrary convention that hides a
        defect of the model. Rejecting keeps the defect visible in the metrics.
        """
        failures = coherence.validate_envelope_coherence([
            {"op": "set_limit", "value": 5},
            {"op": "set_limit", "value": 10},
        ])
        self.assertIn("conflicting_operations", codes(failures))

    def test_two_set_limit_with_the_same_value_is_only_redundant(self):
        failures = coherence.validate_envelope_coherence([
            {"op": "set_limit", "value": 5},
            {"op": "set_limit", "value": 5},
        ])
        self.assertEqual(failures, [])

    def test_two_set_target_with_different_entities(self):
        failures = coherence.validate_envelope_coherence([
            {"op": "set_target", "ref": "clienti"},
            {"op": "set_target", "ref": "ordini_vendita"},
        ])
        self.assertIn("conflicting_operations", codes(failures))

    def test_revert_last_does_not_compose(self):
        failures = coherence.validate_envelope_coherence([
            {"op": "revert_last"},
            {"op": "set_limit", "value": 5},
        ])
        self.assertIn("operation_not_composable", codes(failures))

    def test_revert_last_alone_is_fine(self):
        self.assertEqual(coherence.validate_envelope_coherence([{"op": "revert_last"}]), [])

    def test_predicate_and_value_kind_must_agree(self):
        failures = coherence.validate_envelope_coherence([{
            "op": "add_condition",
            "condition": {"ref": "ordini_vendita.importo_totale", "predicate": "contains",
                          "value": {"kind": "number", "value": 1000}},
        }])
        self.assertIn("predicate_value_mismatch", codes(failures))

    def test_a_temporal_predicate_rejects_a_text_value(self):
        failures = coherence.validate_envelope_coherence([{
            "op": "add_condition",
            "condition": {"ref": "ordini_vendita.data_ordine", "predicate": "within",
                          "value": {"kind": "text", "text": "questo mese"}},
        }])
        self.assertIn("predicate_value_mismatch", codes(failures))

    def test_between_accepts_both_a_range_and_a_temporal(self):
        for value in (
            {"kind": "range", "from": 1, "to": 5},
            {"kind": "temporal", "expression": "absolute_range",
             "from": "2026-03-01", "to": "2026-04-15"},
        ):
            with self.subTest(kind=value["kind"]):
                failures = coherence.validate_envelope_coherence([{
                    "op": "add_condition",
                    "condition": {"ref": "ordini_vendita.data_ordine",
                                  "predicate": "between", "value": value},
                }])
                self.assertEqual(failures, [])

    def test_contradictory_boolean_value(self):
        failures = coherence.validate_envelope_coherence([{
            "op": "add_condition",
            "condition": {"ref": "clienti.attivo", "predicate": "is_true",
                          "value": {"kind": "boolean", "value": False}},
        }])
        self.assertIn("contradictory_boolean", codes(failures))

    def test_a_redundant_but_consistent_boolean_value_passes(self):
        failures = coherence.validate_envelope_coherence([{
            "op": "add_condition",
            "condition": {"ref": "clienti.attivo", "predicate": "is_true",
                          "value": {"kind": "boolean", "value": True}},
        }])
        self.assertEqual(failures, [])


class TestStateCoherence(unittest.TestCase):
    def test_filter_depth_above_three(self):
        deep = base_state(filter={"connective": "all", "conditions": [
            {"connective": "any", "conditions": [
                {"connective": "not", "conditions": [leaf("a")]},
            ]},
        ]})
        self.assertEqual(state_module.depth(deep["filter"]), 4)
        self.assertIn("filter_too_deep", codes(coherence.validate_coherence(deep)))

    def test_filter_depth_of_three_passes(self):
        state = base_state(filter={"connective": "all", "conditions": [
            {"connective": "any", "conditions": [leaf("a"), leaf("b", identifier="c2")]},
        ]})
        self.assertEqual(state_module.depth(state["filter"]), 3)
        self.assertEqual(coherence.validate_coherence(state), [])

    def test_more_than_three_groupings(self):
        state = base_state(group_by=[
            {"ref": f"ordini_vendita.d{index}", "origin": "user"} for index in range(4)
        ])
        self.assertIn("too_many_groups", codes(coherence.validate_coherence(state)))

    def test_measures_broken_down_by_a_grouping_cannot_be_a_list(self):
        state = base_state(
            measures=[{"function": "sum", "ref": "ordini_vendita.importo", "origin": "user"}],
            group_by=[{"ref": "ordini_vendita.venditore", "origin": "user"}],
            presentation={"view": "list", "origin": "user"},
        )
        self.assertIn("measures_with_list_view", codes(coherence.validate_coherence(state)))

    def test_measures_without_a_grouping_may_be_a_list(self):
        """§6.7 rule 3 derives exactly this state, so refusing it would make the
        Applicator and the Validator contradict each other."""
        state = base_state(
            measures=[{"function": "sum", "ref": "ordini_vendita.importo", "origin": "user"}],
            presentation={"view": "list", "origin": "inferred",
                          "rule": "measures_without_group_implies_list"},
        )
        self.assertEqual(coherence.validate_coherence(state), [])

    def test_every_state_the_applicator_derives_a_view_for_is_coherent(self):
        """The two modules are checked against each other, not only in isolation."""
        for measures in (0, 1, 2):
            for groups in (0, 1, 2, 3):
                with self.subTest(measures=measures, groups=groups):
                    operations = [{"op": "set_target", "ref": "ordini_vendita",
                                   "provenance": {"text": "ordini"}}]
                    operations += [
                        {"op": "add_measure", "function": "sum",
                         "ref": f"ordini_vendita.importo_{index}",
                         "provenance": {"text": "somma"}}
                        for index in range(measures)
                    ]
                    operations += [
                        {"op": "add_group", "ref": f"ordini_vendita.d{index}",
                         "provenance": {"text": "per dimensione"}}
                        for index in range(groups)
                    ]
                    state = applicator.apply(state_module.empty_state(), operations).state
                    self.assertEqual(coherence.validate_coherence(state), [])


class TestCost(unittest.TestCase):
    def test_limit_above_the_absolute_maximum(self):
        state = base_state(limit={"value": 5000, "origin": "user"})
        self.assertIn("limit_above_maximum", codes(coherence.validate_cost(state)))

    def test_limit_at_the_maximum_passes(self):
        state = base_state(limit={"value": 500, "origin": "user"})
        self.assertEqual(coherence.validate_cost(state), [])

    def test_the_maximum_is_a_parameter_not_a_constant(self):
        """RC4 — the limits are declared parameters, recalibrated on the corpus."""
        state = base_state(limit={"value": 400, "origin": "user"})
        strict = Limits(max_records=300)
        self.assertIn("limit_above_maximum", codes(coherence.validate_cost(state, limits=strict)))

    def test_too_many_relation_hops(self):
        state = base_state(fields=[
            {"ref": "ordini_vendita.cliente.paese.regione.capoluogo", "origin": "user"},
        ])
        failures = coherence.validate_cost(state)
        self.assertIn("too_many_relation_hops", codes(failures))

    def test_two_hops_pass(self):
        state = base_state(fields=[
            {"ref": "ordini_vendita.cliente.paese.codice", "origin": "user"},
        ])
        self.assertEqual(coherence.validate_cost(state), [])

    def test_hop_counting(self):
        self.assertEqual(state_module.relation_hops("ordini_vendita"), 0)
        self.assertEqual(state_module.relation_hops("ordini_vendita.stato"), 0)
        self.assertEqual(state_module.relation_hops("ordini_vendita.cliente.citta"), 1)
        self.assertEqual(
            state_module.relation_hops("ordini_vendita.cliente.paese.codice"), 2
        )


if __name__ == "__main__":
    unittest.main()
