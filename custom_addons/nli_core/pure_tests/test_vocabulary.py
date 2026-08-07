"""The vocabularies against themselves and against `ai/03-specifica-dsl.md`.

These tests look tautological and are not. A closed vocabulary is only closed if
every symbol in it is reachable and every symbol used elsewhere is in it: an
operation without a signature passes level 2 and fails during application, which
is the latest and least diagnosable moment available.
"""

from __future__ import annotations

import unittest

from ..contract import envelope as envelope_module
from ..contract import state as state_module
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

    # --- D141: named periods ------------------------------------------------

    def test_a_named_period_is_a_symbol_of_its_own(self):
        """*"The first quarter"* is not *"this quarter"* (D141).

        Until 6 August 2026 the vocabulary had no way of saying it, and the model —
        which has to say something — said the nearest shape: the product answered
        *"the leads created in the first quarter"* with the **third** quarter's data.
        """
        for expression in ("month_of_year", "quarter_of_year", "half_of_year",
                           "year_of"):
            with self.subTest(expression=expression):
                self.assertIn(expression, vocabulary_module.TEMPORAL_EXPRESSIONS)
                self.assertEqual(
                    vocabulary_module.TEMPORAL_REQUIRED_KEYS[expression],
                    frozenset({"n"}),
                )

    def test_a_named_period_declares_the_range_its_parameter_admits(self):
        """Thirteen is not a month, and five is not a quarter.

        The range is part of the symbol's arity, like `n` itself: without it level 2
        would pass `month_of_year(13)` on to a Resolver that can only crash.
        """
        self.assertEqual(vocabulary_module.TEMPORAL_PARAMETER_RANGE["month_of_year"],
                         (1, 12))
        self.assertEqual(vocabulary_module.TEMPORAL_PARAMETER_RANGE["quarter_of_year"],
                         (1, 4))
        self.assertEqual(vocabulary_module.TEMPORAL_PARAMETER_RANGE["half_of_year"],
                         (1, 2))

    def test_only_a_named_period_takes_a_year(self):
        """*"March 2026"* names its year; *"last 30 days"* cannot.

        `year` is optional on the two that admit it — the sentence often omits it —
        and unknown everywhere else, so a stray key is caught rather than ignored.
        """
        self.assertEqual(
            sorted(vocabulary_module.TEMPORAL_OPTIONAL_KEYS),
            ["half_of_year", "month_of_year", "quarter_of_year"],
        )
        for expression in vocabulary_module.TEMPORAL_OPTIONAL_KEYS.values():
            self.assertEqual(expression, frozenset({"year"}))


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


class TestLoStatoSalvatoNonPortaIFrammenti(unittest.TestCase):
    """`strip_provenance` in zona pura (**D54**).

    Sta qui dal 7 agosto 2026, spostata dal modello Odoo che la usava per prima. E'
    una funzione pura su uno stato, e il posto delle funzioni sullo stato e' il
    contratto — ma ci e' voluto un secondo chiamante per accorgersene: il generatore
    del dataset di addestramento deve mostrare al modello **esattamente** lo stato che
    la conduttura gli manda, e una seconda copia scritta li' per comodita' sarebbe
    divergente il giorno in cui `STRIPPED_KEYS` cresce.
    """

    def test_it_removes_the_fragment_at_every_depth(self):
        stato = {
            "target": {"ref": "ordini", "provenance": {"text": "ordini"}},
            "filter": {"conditions": [
                {"ref": "ordini.data", "provenance": {"text": "di oggi"}},
                {"ref": "ordini.stato", "provenance": {"text": "confermati"}},
            ]},
        }
        pulito = state_module.strip_provenance(stato)
        self.assertNotIn("provenance", pulito["target"])
        self.assertTrue(all("provenance" not in c
                            for c in pulito["filter"]["conditions"]))

    def test_it_leaves_everything_else_alone(self):
        stato = {"target": {"ref": "ordini", "origin": "user"},
                 "limit": {"value": 5, "origin": "default"}}
        self.assertEqual(state_module.strip_provenance(stato), stato)

    def test_it_does_not_touch_the_state_it_is_given(self):
        """*«in place-safe»*: chi la chiama tiene lo stato con i frammenti, perche'
        gli servono per la risposta di questo turno. Solo la copia che si salva li
        perde."""
        stato = {"target": {"ref": "ordini", "provenance": {"text": "ordini"}}}
        state_module.strip_provenance(stato)
        self.assertIn("provenance", stato["target"])

    def test_the_stripped_keys_are_declared_not_hidden(self):
        self.assertEqual(state_module.STRIPPED_KEYS, ("provenance",))
