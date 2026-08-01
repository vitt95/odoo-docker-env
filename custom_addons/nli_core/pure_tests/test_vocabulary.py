"""The vocabularies against themselves and against `ai/03-specifica-dsl.md`.

These tests look tautological and are not. A closed vocabulary is only closed if
every symbol in it is reachable and every symbol used elsewhere is in it: an
operation without a signature passes level 2 and fails during application, which
is the latest and least diagnosable moment available.
"""

from __future__ import annotations

import unittest

from ..contract import envelope as envelope_module
from ..contract import vocabulary as vocabulary_module


class TestOperations(unittest.TestCase):
    def test_every_operation_has_a_signature(self):
        missing = sorted(
            vocabulary_module.OPERATIONS - envelope_module.OPERATION_SIGNATURES.keys()
        )
        self.assertEqual(missing, [], "operations without a signature")

    def test_every_signature_names_a_known_operation(self):
        unknown = sorted(
            envelope_module.OPERATION_SIGNATURES.keys() - vocabulary_module.OPERATIONS
        )
        self.assertEqual(unknown, [], "signatures for operations that do not exist")

    def test_families_do_not_overlap(self):
        families = (
            vocabulary_module.OPS_ENTITY,
            vocabulary_module.OPS_CONDITION,
            vocabulary_module.OPS_PRESENTATION,
            vocabulary_module.OPS_ORGANISATION,
            vocabulary_module.OPS_SESSION,
        )
        total = sum(len(family) for family in families)
        self.assertEqual(
            total,
            len(vocabulary_module.OPERATIONS),
            "an operation appears in two families",
        )

    def test_the_five_tables_of_section_6_enumerate_twenty_two(self):
        """§6.1 and §21 say eighteen; the five tables list twenty-two.

        Asserted so the discrepancy cannot be silently absorbed later: if the
        Architect rules that four operations leave the contract, this test fails
        and names the decision.
        """
        self.assertEqual(len(vocabulary_module.OPERATIONS), 22)


class TestPredicates(unittest.TestCase):
    def test_predicates_by_type_covers_every_predicate(self):
        union: set[str] = set()
        for predicates in vocabulary_module.PREDICATES_BY_TYPE.values():
            union |= set(predicates)
        self.assertEqual(union, set(vocabulary_module.PREDICATES))

    def test_no_not_equals(self):
        """§8.1: negation is the `not` connective, so that one condition has one
        shape and the canonical form stays unique (C8)."""
        self.assertNotIn("not_equals", vocabulary_module.PREDICATES)

    def test_predicates_with_a_value_declare_which_kinds(self):
        needing_value = vocabulary_module.PREDICATES - vocabulary_module.PREDICATES_WITHOUT_VALUE
        missing = sorted(needing_value - vocabulary_module.PREDICATE_VALUE_KINDS.keys())
        self.assertEqual(missing, [], "predicates without a declared value kind")

    def test_declared_value_kinds_exist(self):
        for predicate, kinds in vocabulary_module.PREDICATE_VALUE_KINDS.items():
            with self.subTest(predicate=predicate):
                unknown = sorted(set(kinds) - vocabulary_module.VALUE_KINDS.keys())
                self.assertEqual(unknown, [])

    def test_category_predicate_is_the_only_one_for_categories(self):
        self.assertEqual(
            vocabulary_module.PREDICATES_BY_TYPE["category"],
            frozenset({vocabulary_module.CATEGORY_PREDICATE}),
        )
        self.assertIn(
            vocabulary_module.CATEGORY_PREDICATE,
            vocabulary_module.PREDICATES_WITHOUT_VALUE,
            "a named condition is the whole condition: it takes no value",
        )


class TestValuesAndTemporals(unittest.TestCase):
    def test_every_value_kind_declares_optional_keys(self):
        self.assertEqual(
            sorted(vocabulary_module.VALUE_KINDS),
            sorted(vocabulary_module.VALUE_OPTIONAL_KEYS),
        )

    def test_parametric_temporals_require_their_parameter(self):
        for expression in vocabulary_module.TEMPORAL_PARAMETRIC:
            with self.subTest(expression=expression):
                self.assertEqual(
                    vocabulary_module.TEMPORAL_REQUIRED_KEYS[expression],
                    frozenset({"n"}),
                )

    def test_temporal_required_keys_name_known_expressions(self):
        unknown = sorted(
            vocabulary_module.TEMPORAL_REQUIRED_KEYS.keys()
            - vocabulary_module.TEMPORAL_EXPRESSIONS
        )
        self.assertEqual(unknown, [])


class TestInferenceRules(unittest.TestCase):
    def test_view_rules_are_all_inference_rules(self):
        for identifier, _ in vocabulary_module.VIEW_DERIVATION_RULES:
            with self.subTest(rule=identifier):
                self.assertIn(identifier, vocabulary_module.INFERENCE_RULES)

    def test_five_view_rules(self):
        """§6.7 has exactly five rows, applied in order."""
        self.assertEqual(len(vocabulary_module.VIEW_DERIVATION_RULES), 5)


class TestLimits(unittest.TestCase):
    def test_declared_values_of_d13_and_d12(self):
        limits = vocabulary_module.DEFAULT_LIMITS
        self.assertEqual(limits.default_records, 80)
        self.assertEqual(limits.max_records, 500)
        self.assertEqual(limits.max_filter_depth, 3)
        self.assertEqual(limits.max_groups, 3)
        self.assertEqual(limits.max_relation_hops, 2)


if __name__ == "__main__":
    unittest.main()
