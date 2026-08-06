"""Validation levels 1 and 2 (§12.3).

Two halves, both necessary. The envelopes of §17 must pass — a specification whose
own worked examples are rejected has been misread. And every failure class must
fire on something: a validator nobody has seen refuse anything is indistinguishable
from a validator that accepts everything, and §12.1 leaves no room for that.
"""

from __future__ import annotations

import unittest

from ..contract.envelope import envelope
from ..validation import structural


def codes(failures) -> set[str]:
    return {failure.code for failure in failures}


def levels(failures) -> set[int]:
    return {failure.level for failure in failures}


class TestWorkedExamplesPass(unittest.TestCase):
    def test_section_17_1_turn_1(self):
        candidate = envelope(
            "operations",
            confidence=0.96,
            operations=[{
                "op": "set_target", "ref": "clienti",
                "provenance": {"text": "clienti"},
            }],
        )
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_section_17_1_turn_2_boolean_with_a_redundant_value(self):
        candidate = envelope(
            "operations",
            confidence=0.94,
            operations=[{
                "op": "add_condition", "combine": "all",
                "condition": {
                    "ref": "clienti.attivo", "predicate": "is_true",
                    "value": {"kind": "boolean", "value": True},
                },
                "provenance": {"text": "quelli attivi"},
            }],
        )
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_section_17_2_vagueness_with_a_resolver(self):
        candidate = envelope(
            "operations",
            confidence=0.89,
            operations=[
                {"op": "set_target", "ref": "veicoli", "provenance": {"text": "le auto"}},
                {"op": "add_condition", "condition": {
                    "ref": "veicoli.chilometraggio", "predicate": "approximately",
                    "value": {"kind": "number", "value": 100000,
                              "resolver": "approx_relative"},
                }, "provenance": {"text": "circa centomila chilometri"}},
            ],
        )
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_section_17_4_clarification(self):
        candidate = envelope(
            "clarification",
            confidence=0.42,
            clarification={
                "question": "Rossi come cliente o come venditore?",
                "provenance": {"text": "di Rossi"},
                "options": [
                    {"label": "Come cliente", "operations": [{
                        "op": "add_condition", "condition": {
                            "ref": "ordini_vendita.cliente", "predicate": "is_one_of",
                            "value": {"kind": "reference", "text": "Rossi"},
                        }}]},
                    {"label": "Come venditore", "operations": [{
                        "op": "add_condition", "condition": {
                            "ref": "ordini_vendita.venditore", "predicate": "is_one_of",
                            "value": {"kind": "reference", "text": "Rossi"},
                        }}]},
                ],
            },
        )
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_section_17_5_out_of_scope(self):
        candidate = envelope("out_of_scope", confidence=0.97, scope_note="modifica_dati",
                            scope_provenance={"text": "modifica i prezzi"})
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_not_understood_carries_no_payload(self):
        self.assertEqual(structural.validate_envelope(envelope("not_understood")), [])

    def test_section_5_1_state(self):
        state = {
            "dsl_version": "1.0",
            "target": {"ref": "ordini_vendita", "origin": "user"},
            "filter": {"connective": "all", "conditions": [
                {"id": "c1", "ref": "ordini_vendita.stato", "predicate": "is_one_of",
                 "value": {"kind": "enum", "items": ["confermato"]},
                 "origin": "user", "provenance": {"text": "confermati"},
                 "confidence": 0.97},
                {"id": "c2", "ref": "ordini_vendita.data_ordine", "predicate": "within",
                 "value": {"kind": "temporal", "expression": "current_month"},
                 "origin": "user", "provenance": {"text": "di questo mese"},
                 "confidence": 0.94},
            ]},
            "fields": [
                {"ref": "ordini_vendita.cliente", "origin": "user"},
                {"ref": "ordini_vendita.importo_totale", "origin": "user"},
            ],
            "group_by": [{"ref": "ordini_vendita.venditore", "origin": "user"}],
            "order_by": [{"ref": "ordini_vendita.data_ordine", "direction": "desc",
                          "origin": "inferred", "rule": "latest_implies_desc_by_date"}],
            "limit": {"value": 5, "origin": "user"},
            "presentation": {"view": "list", "origin": "inferred",
                             "rule": "grouping_without_measure_implies_list"},
        }
        self.assertEqual(structural.validate_state(state), [])


class TestLevel1(unittest.TestCase):
    def test_not_an_object(self):
        self.assertIn("not_an_object", codes(structural.validate_envelope("{}")))

    def test_unknown_version_is_refused(self):
        candidate = {"dsl_version": "2.0", "outcome": "not_understood"}
        self.assertIn("unsupported_version", codes(structural.validate_envelope(candidate)))

    def test_unknown_outcome(self):
        candidate = {"dsl_version": "1.0", "outcome": "maybe"}
        self.assertIn("unknown_outcome", codes(structural.validate_envelope(candidate)))

    def test_unknown_key_is_rejected_never_ignored(self):
        """§15.3 — the failure mode this rule exists for is invisible otherwise."""
        candidate = envelope("not_understood", hint="be nice")
        self.assertIn("unknown_key", codes(structural.validate_envelope(candidate)))

    def test_empty_operation_list(self):
        candidate = envelope("operations", operations=[])
        self.assertIn("empty_operations", codes(structural.validate_envelope(candidate)))

    def test_missing_payload(self):
        candidate = envelope("operations")
        self.assertIn("missing_payload", codes(structural.validate_envelope(candidate)))

    def test_foreign_payload(self):
        candidate = envelope("not_understood", scope_note="modifica_dati")
        self.assertIn("foreign_payload", codes(structural.validate_envelope(candidate)))

    def test_missing_operation_parameter(self):
        candidate = envelope("operations", operations=[{"op": "set_target"}])
        self.assertIn("missing_key", codes(structural.validate_envelope(candidate)))

    def test_unknown_operation_parameter(self):
        candidate = envelope("operations", operations=[
            {"op": "set_target", "ref": "clienti", "model": "res.partner"},
        ])
        self.assertIn("unknown_key", codes(structural.validate_envelope(candidate)))

    def test_ambiguous_addressing(self):
        candidate = envelope("operations", operations=[
            {"op": "remove_condition", "id": "c1", "ref": "clienti.citta"},
        ])
        self.assertIn(
            "ambiguous_addressing", codes(structural.validate_envelope(candidate))
        )

    def test_remove_condition_needs_one_way_to_address(self):
        candidate = envelope("operations", operations=[{"op": "remove_condition"}])
        self.assertIn("missing_key", codes(structural.validate_envelope(candidate)))

    def test_value_forbidden_on_a_valueless_predicate(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "clienti.telefono", "predicate": "is_empty",
                "value": {"kind": "text", "text": ""},
            },
        }])
        self.assertIn("unexpected_value", codes(structural.validate_envelope(candidate)))

    def test_value_required_by_a_predicate_that_takes_one(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition",
            "condition": {"ref": "clienti.citta", "predicate": "equals"},
        }])
        self.assertIn("missing_key", codes(structural.validate_envelope(candidate)))

    def test_confidence_out_of_range(self):
        candidate = envelope("not_understood", confidence=1.4)
        self.assertIn("out_of_range", codes(structural.validate_envelope(candidate)))

    def test_clarification_with_one_option_is_a_confirmation_in_disguise(self):
        candidate = envelope("clarification", clarification={
            "question": "Come cliente?",
            "options": [{"label": "Sì", "operations": [{"op": "clear_filter"}]}],
        })
        self.assertIn("option_count", codes(structural.validate_envelope(candidate)))

    def test_clarification_option_without_operations(self):
        candidate = envelope("clarification", clarification={
            "question": "Cliente o venditore?",
            "options": [
                {"label": "Cliente", "operations": []},
                {"label": "Venditore", "operations": [{"op": "clear_filter"}]},
            ],
        })
        self.assertIn("empty_set", codes(structural.validate_envelope(candidate)))

    def test_state_needs_target_limit_and_presentation(self):
        failures = structural.validate_state({"dsl_version": "1.0"})
        self.assertEqual(codes(failures), {"missing_key"})
        self.assertEqual(len(failures), 3)

    def test_explicitly_empty_section_is_not_valid(self):
        state = {
            "dsl_version": "1.0",
            "target": {"ref": "clienti", "origin": "user"},
            "fields": [],
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
        }
        self.assertIn("empty_section", codes(structural.validate_state(state)))

    def test_state_condition_needs_identifier_and_origin(self):
        state = {
            "dsl_version": "1.0",
            "target": {"ref": "clienti", "origin": "user"},
            "filter": {"ref": "clienti.attivo", "predicate": "is_true"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
        }
        self.assertIn("missing_key", codes(structural.validate_state(state)))

    def test_not_takes_one_child(self):
        state = {
            "dsl_version": "1.0",
            "target": {"ref": "clienti", "origin": "user"},
            "filter": {"connective": "not", "conditions": [
                {"id": "c1", "ref": "a", "predicate": "is_true", "origin": "user"},
                {"id": "c2", "ref": "b", "predicate": "is_true", "origin": "user"},
            ]},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
        }
        self.assertIn("arity", codes(structural.validate_state(state)))


class TestLevel2(unittest.TestCase):
    """Vocabulary membership — the "invented symbol" defect (§12.2)."""

    def test_invented_operation(self):
        candidate = envelope("operations", operations=[{"op": "set_raw_domain", "ref": "x"}])
        failures = structural.validate_envelope(candidate)
        self.assertEqual(levels(failures), {2})
        self.assertIn("unknown_operation", codes(failures))

    def test_invented_predicate(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "clienti.citta", "predicate": "sounds_like",
                "value": {"kind": "text", "text": "Milano"},
            },
        }])
        self.assertIn("unknown_predicate", codes(structural.validate_envelope(candidate)))

    def test_invented_value_kind(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "clienti.citta", "predicate": "equals",
                "value": {"kind": "regex", "text": "^Mi"},
            },
        }])
        self.assertIn("unknown_value_kind", codes(structural.validate_envelope(candidate)))

    def test_invented_temporal_expression(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", "expression": "last_fortnight"},
            },
        }])
        self.assertIn(
            "unknown_temporal_expression", codes(structural.validate_envelope(candidate))
        )

    def test_parametric_temporal_without_its_parameter(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", "expression": "last_n_days"},
            },
        }])
        self.assertIn(
            "missing_temporal_parameter", codes(structural.validate_envelope(candidate))
        )

    def test_year_to_date_is_a_symbol(self):
        """D91 — the partial year. `current_year` is the whole year, a different
        period, and returning it for "since the start of the year" would be a
        wrong number of entirely credible appearance."""
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", "expression": "year_to_date"},
            },
        }])
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_month_to_date_is_deliberately_absent(self):
        """§3.9 — expressiveness is added when the data asks, and it asked for one."""
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", "expression": "month_to_date"},
            },
        }])
        self.assertIn(
            "unknown_temporal_expression", codes(structural.validate_envelope(candidate))
        )

    def test_parametric_temporal_with_its_parameter_passes(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", "expression": "last_n_days", "n": 30},
            },
        }])
        self.assertEqual(structural.validate_envelope(candidate), [])

    # --- D141: named periods ------------------------------------------------

    def temporale(self, **value):
        return envelope("operations", operations=[{
            "op": "add_condition", "condition": {
                "ref": "ordini.data", "predicate": "within",
                "value": {"kind": "temporal", **value},
            },
        }])

    def test_a_named_period_passes_with_and_without_its_year(self):
        """D141 — *"in the first quarter"*, *"in March 2026"*."""
        self.assertEqual(structural.validate_envelope(
            self.temporale(expression="quarter_of_year", n=1)), [])
        self.assertEqual(structural.validate_envelope(
            self.temporale(expression="month_of_year", n=3, year=2026)), [])
        self.assertEqual(structural.validate_envelope(
            self.temporale(expression="year_of", n=2025)), [])

    def test_a_named_period_without_which_one_names_nothing(self):
        """`quarter_of_year` alone is `current_quarter` with extra steps."""
        self.assertIn("missing_temporal_parameter", codes(
            structural.validate_envelope(self.temporale(expression="quarter_of_year"))))

    def test_a_month_outside_the_twelve_is_refused_here(self):
        """Thirteen is not a month, and five is not a quarter.

        The range belongs to level 2 because it is part of what the symbol means, not
        of what the data contains: no installation has a thirteenth month. Letting it
        through would leave the Resolver to either crash or pick something plausible,
        and §46.1 is a page about what plausible costs.
        """
        for expression, out_of_range in (("month_of_year", 13), ("month_of_year", 0),
                                         ("quarter_of_year", 5)):
            with self.subTest(expression=expression, n=out_of_range):
                self.assertIn("temporal_parameter_out_of_range", codes(
                    structural.validate_envelope(
                        self.temporale(expression=expression, n=out_of_range))))

    def test_a_year_on_an_expression_that_has_no_year_is_refused(self):
        """*"the last 30 days of 2025"* is not a period this vocabulary can say, and
        accepting the key while ignoring it is how a dropped fragment happens."""
        self.assertIn("unknown_temporal_parameter", codes(
            structural.validate_envelope(
                self.temporale(expression="last_n_days", n=30, year=2025))))

    def test_a_year_that_is_not_a_year_is_refused(self):
        self.assertIn("temporal_parameter_out_of_range", codes(
            structural.validate_envelope(
                self.temporale(expression="month_of_year", n=3, year=26))))

    def test_invented_aggregation(self):
        candidate = envelope("operations", operations=[
            {"op": "add_measure", "ref": "ordini.importo", "function": "median"},
        ])
        self.assertIn("unknown_aggregation", codes(structural.validate_envelope(candidate)))

    def test_invented_view(self):
        candidate = envelope("operations", operations=[{"op": "set_view", "view": "gantt"}])
        self.assertIn("unknown_view", codes(structural.validate_envelope(candidate)))

    def test_invented_scope_note(self):
        candidate = envelope("out_of_scope", scope_note="qualcosa_altro",
                            scope_provenance={"text": "fai una cosa"})
        self.assertIn("unknown_scope_note", codes(structural.validate_envelope(candidate)))

    def test_invented_rule_identifier_in_a_state(self):
        state = {
            "dsl_version": "1.0",
            "target": {"ref": "clienti", "origin": "user"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "graph", "origin": "inferred",
                             "rule": "looked_nicer_as_a_chart"},
        }
        self.assertIn("unknown_rule", codes(structural.validate_state(state)))

    def test_clarification_options_are_validated_too(self):
        candidate = envelope("clarification", clarification={
            "question": "Cliente o venditore?",
            "options": [
                {"label": "Cliente", "operations": [{"op": "set_raw_domain", "ref": "x"}]},
                {"label": "Venditore", "operations": [{"op": "clear_filter"}]},
            ],
        })
        self.assertIn("unknown_operation", codes(structural.validate_envelope(candidate)))

    def test_level_2_does_not_run_when_level_1_failed(self):
        """§12.2 — a symbol read from a malformed structure is not a symbol.

        The envelope below has one defect of each level: an unknown key (1) and an
        invented view (2). Only the first level is reported.
        """
        candidate = {"dsl_version": "1.0", "outcome": "operations", "hint": "please",
                     "operations": [{"op": "set_view", "view": "gantt"}]}
        failures = structural.validate_envelope(candidate)
        self.assertEqual(levels(failures), {1})
        self.assertEqual(codes(failures), {"unknown_key"})


class TestCategoryPredicate(unittest.TestCase):
    """The T5 named condition — D87, adopted with three constraints."""

    def test_a_category_condition_validates(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition",
            "condition": {"ref": "ordini_vendita.da_fatturare", "predicate": "is_category"},
            "provenance": {"text": "da fatturare"},
        }])
        self.assertEqual(structural.validate_envelope(candidate), [])

    def test_a_category_takes_no_value(self):
        candidate = envelope("operations", operations=[{
            "op": "add_condition",
            "condition": {
                "ref": "ordini_vendita.da_fatturare", "predicate": "is_category",
                "value": {"kind": "boolean", "value": True},
            },
        }])
        self.assertIn("unexpected_value", codes(structural.validate_envelope(candidate)))


if __name__ == "__main__":
    unittest.main()


class TestIlRifiutoSiGuadagna(unittest.TestCase):
    """Un rifiuto per portata deve citare il frammento che lo giustifica (**D118**).

    Misurato: nove rifiuti su 414 uscivano con nota `previsione` (`00` §21.7), e sul
    campo *«mostrami i lead di quest'anno»* usciva come **cancellazione di record**.
    Il `scope_note` e' un insieme chiuso di cinque valori, tutti legali, e il modello
    ne sceglieva uno qualunque quando faticava: l'uscita costava quanto una risposta.
    """

    def test_a_refusal_without_its_fragment_is_refused(self):
        fallimenti = structural.validate_envelope(envelope(
            "out_of_scope", scope_note="cancellazione_record"))
        self.assertIn("ungrounded_scope", {f.code for f in fallimenti})

    def test_an_empty_fragment_does_not_count(self):
        """Uno spazio bianco e' un rifiuto senza motivo con la forma del motivo."""
        fallimenti = structural.validate_envelope(envelope(
            "out_of_scope", scope_note="cancellazione_record",
            scope_provenance={"text": "   "}))
        self.assertIn("ungrounded_scope", {f.code for f in fallimenti})

    def test_a_refusal_that_quotes_its_fragment_passes(self):
        """L'altra meta': un controllo che rifiuta ogni rifiuto non e' un controllo."""
        fallimenti = structural.validate_envelope(envelope(
            "out_of_scope", scope_note="cancellazione_record",
            scope_provenance={"text": "cancella tutti i lead"}))
        self.assertEqual(fallimenti, [])


class TestIlFrammentoDeveDirlo(unittest.TestCase):
    """Il controllo che usa il riconoscitore iniettato (**D119**)."""

    def test_a_fragment_that_does_not_justify_is_refused(self):
        fallimenti = structural.validate_scope_grounding(
            envelope("out_of_scope", scope_note="cancellazione_record",
                     scope_provenance={"text": "mostrami i lead"}),
            justifies=lambda nota, testo: False)
        self.assertEqual([f.code for f in fallimenti], ["scope_not_justified"])

    def test_a_fragment_that_justifies_passes(self):
        fallimenti = structural.validate_scope_grounding(
            envelope("out_of_scope", scope_note="cancellazione_record",
                     scope_provenance={"text": "cancella i lead"}),
            justifies=lambda nota, testo: True)
        self.assertEqual(fallimenti, [])

    def test_other_outcomes_are_not_touched(self):
        """Un controllo che parlasse anche delle risposte non sarebbe questo
        controllo: qui si giudica solo chi rifiuta."""
        fallimenti = structural.validate_scope_grounding(
            envelope("not_understood"), justifies=lambda nota, testo: False)
        self.assertEqual(fallimenti, [])
