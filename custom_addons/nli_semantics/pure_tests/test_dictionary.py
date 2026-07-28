"""The dictionary: entry types, condition language, precedence, term index."""

from __future__ import annotations

import unittest

from ..dictionary import conditions, entries, index
from ..dictionary.store import Dictionary


def naming(ref: str, terms: list[str], level: str = "L0") -> dict:
    return {"type": "T1", "level": level, "ref": ref, "terms": terms}


def category(ref: str, entity: str, terms: list[str], condition: dict,
             level: str = "L1", version: str = "1") -> dict:
    return {"type": "T5", "level": level, "ref": ref, "entity": entity,
            "terms": terms, "condition": condition, "version": version}


def resolver(name: str, rule: dict, level: str = "L1", version: str = "1") -> dict:
    return {"type": "T3", "level": level, "name": name, "rule": rule, "version": version}


# ---------------------------------------------------------------------------
# The condition language — where the three constraints of D87 come from
# ---------------------------------------------------------------------------

class TestConditionLanguage(unittest.TestCase):
    def test_a_field_to_field_comparison_is_expressible(self):
        """The shape the DSL cannot express and real categories need.

        `sottoscorta` is `qty_available < reordering_min`: two attributes, no
        literal. §8.2 of the contract compares an attribute with a literal, which is
        right for the model and insufficient for the dictionary.
        """
        condition = {"kind": "compare_field", "field": "qty_available",
                     "operator": "lt", "other_field": "reordering_min"}
        self.assertEqual(conditions.validate(condition), [])

    def test_implied_fields_includes_both_sides(self):
        """The bug this design exists to make impossible.

        `ai/corpus/lessico_l1.json` declares `campi_implicati: ["qty_available"]` for
        this very condition, omitting `reordering_min`. Under V-D87-1 a user without
        access to the second field would still have received the category. Derived,
        the omission cannot happen.
        """
        condition = {"kind": "compare_field", "field": "qty_available",
                     "operator": "lt", "other_field": "reordering_min"}
        self.assertEqual(
            conditions.implied_fields(condition),
            frozenset({"qty_available", "reordering_min"}),
        )

    def test_implied_fields_walks_the_whole_tree(self):
        condition = {"kind": "all", "conditions": [
            {"kind": "in", "field": "payment_state", "values": ["not_paid", "partial"]},
            {"kind": "compare_now", "field": "invoice_date_due", "operator": "lt"},
        ]}
        self.assertEqual(
            conditions.implied_fields(condition),
            frozenset({"payment_state", "invoice_date_due"}),
        )

    def test_an_aggregate_qualifies_its_field_with_its_entity(self):
        condition = {"kind": "aggregate", "entity": "fatture_cliente",
                     "function": "sum", "field": "imponibile",
                     "operator": "gt", "value": 50000, "window_days": 365}
        self.assertIn("fatture_cliente.imponibile", conditions.implied_fields(condition))
        self.assertEqual(
            conditions.implied_entities(condition), frozenset({"fatture_cliente"})
        )

    def test_time_dependence_is_structural(self):
        """V-D87-3 — not a search for the word "today"."""
        overdue = {"kind": "compare_now", "field": "invoice_date_due", "operator": "lt"}
        draft = {"kind": "in", "field": "state", "values": ["draft"]}
        self.assertTrue(conditions.is_time_dependent(overdue))
        self.assertFalse(conditions.is_time_dependent(draft))

    def test_a_window_makes_an_aggregate_time_dependent(self):
        condition = {"kind": "aggregate", "entity": "fatture_cliente", "function": "sum",
                     "field": "imponibile", "operator": "gt", "value": 50000,
                     "window_days": 365}
        self.assertTrue(conditions.is_time_dependent(condition))

    def test_cost_class_separates_a_clause_from_a_roll_up(self):
        """V-D87-2 — the difference level 5 needs to know before the query runs."""
        simple = {"kind": "in", "field": "state", "values": ["sale"]}
        aggregate = {"kind": "aggregate", "entity": "fatture_cliente", "function": "sum",
                     "field": "imponibile", "operator": "gt", "value": 50000}
        self.assertEqual(conditions.cost_class(simple), conditions.COST_SIMPLE)
        self.assertEqual(conditions.cost_class(aggregate), conditions.COST_AGGREGATE)

    def test_malformed_conditions_are_reported(self):
        for name, condition in (
            ("unknown kind", {"kind": "regex", "field": "x", "value": "^a"}),
            ("missing key", {"kind": "compare", "field": "x", "operator": "lt"}),
            ("unknown key", {"kind": "compare", "field": "x", "operator": "lt",
                             "value": 1, "domain": "[]"}),
            ("bad operator", {"kind": "compare", "field": "x", "operator": "like",
                              "value": 1}),
            ("empty composite", {"kind": "all", "conditions": []}),
            ("not with two children", {"kind": "not", "conditions": [
                {"kind": "is_set", "field": "a"}, {"kind": "is_set", "field": "b"}]}),
        ):
            with self.subTest(case=name):
                self.assertNotEqual(conditions.validate(condition), [])

    def test_no_free_text_anywhere(self):
        """D59 — every field of an entry is typed. A condition as prose would be a
        rule nobody can apply and everybody can reinterpret."""
        self.assertNotIn("expression", conditions.KINDS)
        self.assertNotIn("domain", conditions.KINDS)
        self.assertNotIn("sql", conditions.KINDS)


# ---------------------------------------------------------------------------
# Entry types
# ---------------------------------------------------------------------------

class TestEntries(unittest.TestCase):
    def test_the_seven_types_split_in_two_classes(self):
        self.assertEqual(
            entries.VOCABULARY_TYPES | entries.DEFINITION_TYPES, set(entries.TYPES)
        )
        self.assertEqual(entries.VOCABULARY_TYPES & entries.DEFINITION_TYPES, frozenset())

    def test_t5_is_a_definition_not_vocabulary(self):
        """The classification D87 turns on: a definition exposed as vocabulary would
        lose the notification of D29 at the layer where it is enforced."""
        self.assertIn("T5", entries.DEFINITION_TYPES)
        self.assertIn("T1", entries.VOCABULARY_TYPES)

    def test_phase_one_implements_four_types(self):
        """Registry §6.5 — declaring seven does not oblige implementing seven."""
        self.assertEqual(entries.PHASE_1_TYPES, frozenset({"T1", "T2", "T3", "T5"}))

    def test_a_valid_naming_entry_passes(self):
        self.assertEqual(entries.validate_entry(naming("ordini_vendita", ["ordini"])), [])

    def test_a_type_not_in_phase_one_is_refused_not_ignored(self):
        entry = {"type": "T4", "level": "L2", "name": "fatturato",
                 "entity": "fatture_cliente", "aggregate": {}, "terms": ["fatturato"]}
        problems = entries.validate_entry(entry)
        self.assertTrue(problems)
        self.assertIn("not implemented in phase 1", str(problems[0]))

    def test_l3_is_refused(self):
        problems = entries.validate_entry(naming("x", ["y"], level="L3"))
        self.assertTrue(any("queue" in str(p) for p in problems))

    def test_a_definition_without_a_version_is_refused(self):
        entry = category("clienti.importanti", "clienti", ["importanti"],
                         {"kind": "is_set", "field": "vat"})
        del entry["version"]
        problems = entries.validate_entry(entry)
        self.assertTrue(any("version" in str(p) for p in problems))

    def test_vocabulary_needs_no_version(self):
        self.assertEqual(entries.validate_entry(naming("clienti", ["clienti"])), [])

    def test_unknown_keys_are_refused(self):
        entry = naming("clienti", ["clienti"])
        entry["model"] = "res.partner"
        self.assertTrue(entries.validate_entry(entry))

    def test_empty_terms_are_refused(self):
        self.assertTrue(entries.validate_entry(naming("clienti", [])))

    def test_resolver_rules_are_typed(self):
        self.assertEqual(
            entries.validate_entry(resolver("approx_relative",
                                            {"kind": "relative_percent", "percent": 10})),
            [],
        )
        self.assertTrue(entries.validate_entry(
            resolver("approx_relative", {"kind": "gut_feeling", "note": "circa"})))
        self.assertTrue(entries.validate_entry(
            resolver("recent_orders", {"kind": "last_n_days", "days": "trenta"})))

    def test_category_derived_properties(self):
        entry = category(
            "fatture_cliente.scadute", "fatture_cliente", ["scadute", "insoluti"],
            {"kind": "all", "conditions": [
                {"kind": "in", "field": "payment_state", "values": ["not_paid"]},
                {"kind": "compare_now", "field": "invoice_date_due", "operator": "lt"},
            ]},
        )
        self.assertEqual(entries.validate_entry(entry), [])
        self.assertEqual(
            entries.category_implied_refs(entry),
            frozenset({"fatture_cliente.payment_state",
                       "fatture_cliente.invoice_date_due"}),
        )
        self.assertTrue(entries.category_is_time_dependent(entry))
        self.assertEqual(entries.category_cost_class(entry), conditions.COST_SIMPLE)


# ---------------------------------------------------------------------------
# Levels and precedence
# ---------------------------------------------------------------------------

class TestPrecedence(unittest.TestCase):
    def test_vocabulary_merges_across_levels(self):
        """Adding a synonym at L2 must not delete the base package's synonyms."""
        dictionary = Dictionary.build([
            naming("ordini_vendita", ["ordini", "ordini di vendita"], level="L0"),
            naming("ordini_vendita", ["ordini cliente"], level="L1"),
            naming("ordini_vendita", ["pratiche"], level="L2"),
        ])
        terms = dictionary.terms_of("ordini_vendita")
        self.assertIn("pratiche", terms)
        self.assertIn("ordini", terms)
        self.assertIn("ordini cliente", terms)
        self.assertEqual(terms[0], "pratiche",
                         "the customer's word comes first (it is shown first)")

    def test_definitions_are_replaced_not_merged(self):
        """Sixty days replaces thirty; it is not averaged into forty-five."""
        dictionary = Dictionary.build([
            resolver("recent_orders", {"kind": "last_n_days", "days": 30}, level="L1"),
            resolver("recent_orders", {"kind": "last_n_days", "days": 60}, level="L2"),
        ])
        self.assertEqual(dictionary.resolver("recent_orders")["rule"]["days"], 60)

    def test_l3_never_participates(self):
        dictionary = Dictionary.build([
            naming("clienti", ["clienti"], level="L0"),
            naming("clienti", ["anagrafiche"], level="L3"),
        ])
        self.assertNotIn("anagrafiche", dictionary.terms_of("clienti"))
        self.assertTrue(dictionary.problems, "an L3 entry is reported, not silently kept")

    def test_a_malformed_entry_does_not_take_the_dictionary_down(self):
        dictionary = Dictionary.build([
            naming("clienti", ["clienti"]),
            {"type": "T1", "level": "L0", "ref": "rotto"},
        ])
        self.assertEqual(dictionary.terms_of("clienti"), ["clienti"])
        self.assertTrue(dictionary.problems)

    def test_the_merged_entry_reports_its_contributing_levels(self):
        dictionary = Dictionary.build([
            naming("clienti", ["clienti"], level="L0"),
            naming("clienti", ["anagrafiche"], level="L2"),
        ])
        entry = dictionary.entry("T1", "clienti")
        self.assertEqual(entry["level"], "L2", "who may edit it (D38)")
        self.assertEqual(entry["contributing_levels"], ["L0", "L2"])


# ---------------------------------------------------------------------------
# The term index
# ---------------------------------------------------------------------------

class TestNormalisation(unittest.TestCase):
    def test_case_accents_and_punctuation_go(self):
        self.assertEqual(index.normalise("Mostrami le FATTURE, scadute!"),
                         ["mostrami", "le", "fatture", "scadute"])
        self.assertEqual(index.normalise("attività"), ["attivita"])

    def test_base_form_collapses_singular_and_plural(self):
        self.assertEqual(index.base_form("ordini"), index.base_form("ordine"))
        self.assertEqual(index.base_form("fatture"), index.base_form("fattura"))

    def test_base_form_leaves_short_words_alone(self):
        self.assertEqual(index.base_form("ddt"), "ddt")

    def test_substitution_insertion_and_deletion(self):
        self.assertTrue(index.edit_distance_at_most_one("fatture", "fatuure"))
        self.assertTrue(index.edit_distance_at_most_one("fatture", "fature"))
        self.assertTrue(index.edit_distance_at_most_one("fature", "fatture"))

    def test_adjacent_transposition_counts_as_one(self):
        """A widening the document did not ask for, hence a parameter."""
        self.assertTrue(index.edit_distance_at_most_one("fattrue", "fatture"))
        self.assertTrue(index.edit_distance_at_most_one("ordnii", "ordini"))
        self.assertFalse(index.edit_distance_at_most_one(
            "fattrue", "fatture", allow_transposition=False))

    def test_two_unrelated_substitutions_do_not(self):
        self.assertFalse(index.edit_distance_at_most_one("fatture", "faccure"))
        self.assertFalse(index.edit_distance_at_most_one("fatture", "faccture2"))

    def test_the_example_of_section_5_5_does_not_match_its_own_rule(self):
        """`fatuere` is two edits from `fatture`, transposition included.

        Asserted so the defect in the document cannot be quietly absorbed by a later
        loosening: raising the bound to two would make `letture` match `fatture`, an
        unrelated word and exactly the silent wrong match nothing surfaces.
        """
        self.assertFalse(index.edit_distance_at_most_one("fatuere", "fatture"))
        self.assertFalse(index.edit_distance_at_most_one("letture", "fatture"))


class TestTermIndex(unittest.TestCase):
    def build(self) -> index.TermIndex:
        dictionary = Dictionary.build([
            naming("ordini_vendita", ["ordini", "ordini di vendita"]),
            naming("ordini_acquisto", ["ordini di acquisto", "acquisti"]),
            naming("fatture_cliente", ["fatture", "fatture cliente"]),
            naming("clienti", ["clienti"]),
        ])
        return dictionary.term_index()

    def test_exact_match_scores_one(self):
        matches = self.build().match("mostrami i clienti")
        self.assertEqual(matches[0].ref, "clienti")
        self.assertEqual(matches[0].score, index.WEIGHT_EXACT)

    def test_inflected_match_scores_the_base_form_weight(self):
        matches = [m for m in self.build().match("mostrami la fattura") if m.ref == "fatture_cliente"]
        self.assertTrue(matches)
        self.assertEqual(matches[0].score, index.WEIGHT_BASE_FORM)

    def test_a_typo_scores_the_approximate_weight(self):
        matches = [m for m in self.build().match("le fattrue scadute")
                   if m.ref == "fatture_cliente"]
        self.assertTrue(matches)
        self.assertEqual(matches[0].score, index.WEIGHT_APPROXIMATE)

    def test_a_longer_term_wins(self):
        matches = self.build().match("mostrami gli ordini di acquisto")
        self.assertEqual(matches[0].ref, "ordini_acquisto")
        self.assertGreater(matches[0].length, 1)

    def test_a_correctly_spelled_word_is_never_corrected_into_another_reference(self):
        """The guard of §5.5: approximate matching never touches a token that
        already matches something exactly."""
        matches = [m for m in self.build().match("mostrami i clienti")
                   if m.score == index.WEIGHT_APPROXIMATE]
        self.assertEqual(matches, [])

    def test_short_words_are_never_matched_approximately(self):
        local = index.TermIndex()
        local.add("ddt", "documenti_trasporto", level="L0", entry_type="T1")
        self.assertEqual(local.match("mostrami i ddd"), [])

    def test_one_index_across_languages(self):
        """D37 — "deal" and "trattativa" lead to the same reference, and nobody has
        to decide which language the sentence is in."""
        dictionary = Dictionary.build([
            naming("opportunita", ["trattativa"], level="L1"),
            naming("opportunita", ["deal"], level="L1"),
        ])
        index_of = dictionary.term_index()
        for request in ("le trattative aperte", "i deal aperti"):
            with self.subTest(request=request):
                self.assertEqual(index_of.match(request)[0].ref, "opportunita")


if __name__ == "__main__":
    unittest.main()
