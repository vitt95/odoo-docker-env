"""The canonical form (§14.3) and the equivalence levels (§14.4).

The seven rules are tested one by one, and then three properties are tested that
no single rule states but on which the whole measurement of `07` rests:
idempotence, stability under permutation of the conditions, and the fact that
`origin` does not affect equality while the reference does.
"""

from __future__ import annotations

import unittest

from ..contract import canonical, equivalence


def state_with(filter_node=None, **sections) -> dict:
    state = {
        "dsl_version": "1.0",
        "target": {"ref": "ordini_vendita", "origin": "user"},
        "limit": {"value": 80, "origin": "default"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }
    if filter_node is not None:
        state["filter"] = filter_node
    state.update(sections)
    return state


def condition(identifier: str, ref: str, predicate: str, value=None, **extra) -> dict:
    node = {"id": identifier, "ref": ref, "predicate": predicate, "origin": "user", **extra}
    if value is not None:
        node["value"] = value
    return node


class TestRule1Metadata(unittest.TestCase):
    def test_metadata_is_removed(self):
        state = state_with(condition(
            "c1", "ordini_vendita.stato", "is_one_of",
            {"kind": "enum", "items": ["confermato"]},
            provenance={"text": "confermati"}, confidence=0.97,
        ))
        result = canonical.canonicalise(state)
        self.assertEqual(
            result["filter"],
            {"ref": "ordini_vendita.stato", "predicate": "is_one_of",
             "value": {"kind": "enum", "items": ["confermato"]}},
        )

    def test_origin_does_not_affect_equality(self):
        """Two states differing only in who decided the ordering are equivalent.

        Correct for interpretive accuracy, and incomplete: a system that inferred
        everything and declared nothing would score perfectly while violating P3.
        Provenance correctness is a separate indicator (D53) — asserted here so the
        limitation is recorded in the tests and not only in prose.
        """
        asked = state_with(order_by=[
            {"ref": "ordini_vendita.data_ordine", "direction": "desc", "origin": "user"},
        ])
        inferred = state_with(order_by=[
            {"ref": "ordini_vendita.data_ordine", "direction": "desc",
             "origin": "inferred", "rule": "latest_implies_desc_by_date"},
        ])
        self.assertTrue(canonical.identical(asked, inferred))

    def test_the_reference_does_affect_equality(self):
        left = state_with(order_by=[
            {"ref": "ordini_vendita.data_ordine", "direction": "desc", "origin": "user"},
        ])
        right = state_with(order_by=[
            {"ref": "ordini_vendita.data_conferma", "direction": "desc", "origin": "user"},
        ])
        self.assertFalse(canonical.identical(left, right))


class TestRule2ConditionOrder(unittest.TestCase):
    def test_conditions_are_ordered_within_a_connective(self):
        forward = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
            condition("c2", "ordini_vendita.data_ordine", "within",
                      {"kind": "temporal", "expression": "current_month"}),
        ]})
        backward = state_with({"connective": "all", "conditions": [
            condition("c2", "ordini_vendita.data_ordine", "within",
                      {"kind": "temporal", "expression": "current_month"}),
            condition("c1", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
        ]})
        self.assertTrue(canonical.identical(forward, backward))

    def test_stability_under_every_permutation(self):
        state = state_with({"connective": "all", "conditions": [
            condition("c1", "a", "is_true"),
            condition("c2", "b", "is_true"),
            condition("c3", "c", "is_true"),
        ]})
        reference = canonical.canonical_json(state)
        variants = canonical.permutations_of_conditions(state)
        self.assertTrue(variants)
        for variant in variants:
            self.assertEqual(canonical.canonical_json(variant), reference)

    def test_field_order_is_not_normalised(self):
        """§5.5 — the order of `fields` is the presentation order, so it is semantic."""
        left = state_with(fields=[
            {"ref": "ordini_vendita.cliente", "origin": "user"},
            {"ref": "ordini_vendita.importo_totale", "origin": "user"},
        ])
        right = state_with(fields=[
            {"ref": "ordini_vendita.importo_totale", "origin": "user"},
            {"ref": "ordini_vendita.cliente", "origin": "user"},
        ])
        self.assertFalse(canonical.identical(left, right))

    def test_group_order_is_not_normalised(self):
        """§5.6 — grouping levels are nested in order."""
        left = state_with(group_by=[
            {"ref": "a", "origin": "user"}, {"ref": "b", "origin": "user"},
        ])
        right = state_with(group_by=[
            {"ref": "b", "origin": "user"}, {"ref": "a", "origin": "user"},
        ])
        self.assertFalse(canonical.identical(left, right))


class TestRule3Sets(unittest.TestCase):
    def test_enum_items_are_ordered(self):
        left = state_with(condition("c1", "ordini_vendita.stato", "is_one_of",
                                    {"kind": "enum", "items": ["fatturato", "confermato"]}))
        right = state_with(condition("c1", "ordini_vendita.stato", "is_one_of",
                                     {"kind": "enum", "items": ["confermato", "fatturato"]}))
        self.assertTrue(canonical.identical(left, right))


class TestRule4Connectives(unittest.TestCase):
    def test_single_child_connective_is_replaced_by_the_child(self):
        wrapped = state_with({"connective": "all", "conditions": [
            condition("c1", "a", "is_true"),
        ]})
        bare = state_with(condition("c1", "a", "is_true"))
        self.assertTrue(canonical.identical(wrapped, bare))

    def test_nested_same_connectives_are_flattened(self):
        nested = state_with({"connective": "all", "conditions": [
            condition("c1", "a", "is_true"),
            {"connective": "all", "conditions": [
                condition("c2", "b", "is_true"),
                condition("c3", "c", "is_true"),
            ]},
        ]})
        flat = state_with({"connective": "all", "conditions": [
            condition("c1", "a", "is_true"),
            condition("c2", "b", "is_true"),
            condition("c3", "c", "is_true"),
        ]})
        self.assertTrue(canonical.identical(nested, flat))

    def test_different_connectives_are_not_flattened(self):
        any_of = state_with({"connective": "any", "conditions": [
            condition("c1", "a", "is_true"),
            condition("c2", "b", "is_true"),
        ]})
        all_of = state_with({"connective": "all", "conditions": [
            condition("c1", "a", "is_true"),
            condition("c2", "b", "is_true"),
        ]})
        self.assertFalse(canonical.identical(any_of, all_of))


class TestRule5And7Defaults(unittest.TestCase):
    def test_limit_and_view_are_always_present(self):
        result = canonical.canonicalise({
            "dsl_version": "1.0",
            "target": {"ref": "clienti", "origin": "user"},
        })
        self.assertEqual(result["limit"], 80)
        self.assertEqual(result["presentation"], "list")

    def test_empty_sections_are_absent(self):
        result = canonical.canonicalise(state_with(fields=[], group_by=[]))
        self.assertNotIn("fields", result)
        self.assertNotIn("group_by", result)


class TestRule6Literals(unittest.TestCase):
    def test_case_and_whitespace_are_normalised(self):
        left = state_with(condition("c1", "clienti.citta", "equals",
                                    {"kind": "text", "text": "MILANO"}))
        right = state_with(condition("c1", "clienti.citta", "equals",
                                     {"kind": "text", "text": "  milano  "}))
        self.assertTrue(canonical.identical(left, right))

    def test_accents_compare_equal_across_normal_forms(self):
        # Escapes, not literals: the two strings are indistinguishable in an
        # editor, which is exactly why rule 6 exists. The corpus deliberately
        # contains accent-stripped and lowercased perturbations (D83).
        composed = state_with(condition("c1", "clienti.citta", "equals",
                                        {"kind": "text", "text": "Citt\u00e0"}))
        decomposed = state_with(condition("c1", "clienti.citta", "equals",
                                          {"kind": "text", "text": "Citta\u0300"}))
        self.assertNotEqual(
            composed["filter"]["value"]["text"],
            decomposed["filter"]["value"]["text"],
            "the fixture must hold two different byte sequences to prove anything",
        )
        self.assertTrue(canonical.identical(composed, decomposed))

    def test_integral_floats_and_integers_are_the_same_threshold(self):
        left = state_with(condition("c1", "ordini_vendita.importo_totale", "greater_than",
                                    {"kind": "number", "value": 1000}))
        right = state_with(condition("c1", "ordini_vendita.importo_totale", "greater_than",
                                     {"kind": "number", "value": 1000.0}))
        self.assertTrue(canonical.identical(left, right))


class TestRedundantBooleanValue(unittest.TestCase):
    def test_is_true_with_and_without_a_value_are_the_same_condition(self):
        with_value = state_with(condition("c1", "clienti.attivo", "is_true",
                                          {"kind": "boolean", "value": True}))
        without = state_with(condition("c1", "clienti.attivo", "is_true"))
        self.assertTrue(canonical.identical(with_value, without))


class TestProperties(unittest.TestCase):
    def test_canonicalisation_is_idempotent(self):
        state = state_with({"connective": "any", "conditions": [
            condition("c1", "b", "equals", {"kind": "text", "text": "X"}),
            {"connective": "all", "conditions": [
                condition("c2", "a", "is_true"),
                condition("c3", "c", "is_one_of", {"kind": "enum", "items": ["z", "a"]}),
            ]},
        ]}, fields=[{"ref": "f", "origin": "user"}])
        once = canonical.canonicalise(state)
        twice = canonical.canonicalise(once)
        self.assertEqual(once, twice)

    def test_canonical_json_is_byte_stable(self):
        state = state_with(condition("c1", "a", "is_true"))
        self.assertEqual(canonical.canonical_json(state), canonical.canonical_json(state))

    def test_section_comparison_names_the_section_that_differs(self):
        expected = state_with(
            condition("c1", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
            group_by=[{"ref": "ordini_vendita.venditore", "origin": "user"}],
        )
        produced = state_with(
            condition("c1", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
            group_by=[{"ref": "ordini_vendita.cliente", "origin": "user"}],
        )
        comparison = canonical.section_comparison(expected, produced)
        self.assertTrue(comparison["filter"])
        self.assertFalse(comparison["group_by"])
        self.assertTrue(comparison["target"])


class TestEquivalenceRegistry(unittest.TestCase):
    """§14.4 semantic equivalence, D43."""

    def test_e1_between_equals_a_pair_of_bounds(self):
        between = state_with(condition(
            "c1", "ordini_vendita.importo_totale", "between",
            {"kind": "range", "from": 1000, "to": 5000},
        ))
        bounds = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "greater_or_equal",
                      {"kind": "number", "value": 1000}),
            condition("c2", "ordini_vendita.importo_totale", "less_or_equal",
                      {"kind": "number", "value": 5000}),
        ]})
        self.assertFalse(canonical.identical(between, bounds), "different canonical forms")
        self.assertTrue(equivalence.equivalent(between, bounds), "same question (E1)")

    def test_e1_keeps_the_other_conditions(self):
        between = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "between",
                      {"kind": "range", "from": 1000, "to": 5000}),
            condition("c2", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
        ]})
        bounds = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "greater_or_equal",
                      {"kind": "number", "value": 1000}),
            condition("c2", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["confermato"]}),
            condition("c3", "ordini_vendita.importo_totale", "less_or_equal",
                      {"kind": "number", "value": 5000}),
        ]})
        self.assertTrue(equivalence.equivalent(between, bounds))

    def test_e1_does_not_merge_bounds_on_different_references(self):
        mixed = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "greater_or_equal",
                      {"kind": "number", "value": 1000}),
            condition("c2", "ordini_vendita.quantita", "less_or_equal",
                      {"kind": "number", "value": 5000}),
        ]})
        between = state_with(condition(
            "c1", "ordini_vendita.importo_totale", "between",
            {"kind": "range", "from": 1000, "to": 5000},
        ))
        self.assertFalse(equivalence.equivalent(mixed, between))

    def test_e1_does_not_merge_bounds_under_any(self):
        """`x >= a OR x <= b` is not a range: it is almost everything."""
        disjunction = state_with({"connective": "any", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "greater_or_equal",
                      {"kind": "number", "value": 1000}),
            condition("c2", "ordini_vendita.importo_totale", "less_or_equal",
                      {"kind": "number", "value": 5000}),
        ]})
        between = state_with(condition(
            "c1", "ordini_vendita.importo_totale", "between",
            {"kind": "range", "from": 1000, "to": 5000},
        ))
        self.assertFalse(equivalence.equivalent(disjunction, between))

    def test_e2_is_not_one_of_equals_a_negated_membership(self):
        direct = state_with(condition("c1", "ordini_vendita.stato", "is_not_one_of",
                                      {"kind": "enum", "items": ["bozza", "annullato"]}))
        negated = state_with({"connective": "not", "conditions": [
            condition("c1", "ordini_vendita.stato", "is_one_of",
                      {"kind": "enum", "items": ["bozza", "annullato"]}),
        ]})
        self.assertFalse(canonical.identical(direct, negated))
        self.assertTrue(equivalence.equivalent(direct, negated))

    def test_different_interrogations_are_not_equivalent(self):
        left = state_with(condition("c1", "ordini_vendita.stato", "is_one_of",
                                    {"kind": "enum", "items": ["confermato"]}))
        right = state_with(condition("c1", "ordini_vendita.stato", "is_not_one_of",
                                     {"kind": "enum", "items": ["confermato"]}))
        self.assertFalse(equivalence.equivalent(left, right))

    def test_normal_form_is_idempotent(self):
        bounds = state_with({"connective": "all", "conditions": [
            condition("c1", "ordini_vendita.importo_totale", "greater_or_equal",
                      {"kind": "number", "value": 1000}),
            condition("c2", "ordini_vendita.importo_totale", "less_or_equal",
                      {"kind": "number", "value": 5000}),
        ]})
        once = equivalence.normal_form(bounds)
        self.assertEqual(once, equivalence.normal_form(once))

    def test_the_registry_is_small_and_versioned(self):
        """D43: adding an entry is a change to the measurement, not a tweak."""
        self.assertEqual(equivalence.REGISTRY_VERSION, "1.0")
        self.assertEqual(
            [entry.identifier for entry in equivalence.REGISTRY], ["E1", "E2"]
        )
        for entry in equivalence.REGISTRY:
            with self.subTest(entry=entry.identifier):
                self.assertTrue(entry.rationale, "an equivalence without an argument")


if __name__ == "__main__":
    unittest.main()
