"""The formal schema (D11) against the specification's examples and the validator.

Three things are checked, and the third is the one that earns the file's keep:

1. the worked envelopes and states of §17 and §5.1 validate against the schema;
2. the shapes the schema must refuse are refused — an invented predicate, a
   foreign payload, an empty operation list;
3. the schema and `validation.structural` **agree**. They are two derivations of
   the same vocabularies, and a disagreement means a model can be constrained to
   produce something the validator then refuses — the exact failure §12.3 warns
   about, where a constrained-generation defect shows up as a validation problem.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from . import _jsonschema
from ..contract import schema as schema_module
from ..contract.envelope import envelope
from ..validation import structural

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contract" / "schema"


def valid_envelopes() -> list[tuple[str, dict]]:
    return [
        ("17.1 turn 1", envelope("operations", confidence=0.96, operations=[
            {"op": "set_target", "ref": "clienti", "provenance": {"text": "clienti"}},
        ])),
        ("17.1 turn 2", envelope("operations", confidence=0.94, operations=[
            {"op": "add_condition", "combine": "all", "condition": {
                "ref": "clienti.attivo", "predicate": "is_true",
                "value": {"kind": "boolean", "value": True},
            }, "provenance": {"text": "quelli attivi"}},
        ])),
        ("17.1 turn 3", envelope("operations", confidence=0.97, operations=[
            {"op": "set_order", "ref": "clienti.citta", "direction": "asc",
             "origin": "inferred", "provenance": {"text": "per città"}},
        ])),
        ("17.1 turn 4", envelope("operations", confidence=0.98, operations=[
            {"op": "add_field", "ref": "clienti.telefono",
             "provenance": {"text": "anche il telefono"}},
        ])),
        ("17.1 turn 5", envelope("operations", confidence=0.95, operations=[
            {"op": "open_record", "selector": {"by": "position", "value": 1},
             "provenance": {"text": "il primo"}},
        ])),
        ("17.2 vagueness", envelope("operations", confidence=0.89, operations=[
            {"op": "set_target", "ref": "veicoli", "provenance": {"text": "le auto"}},
            {"op": "add_condition", "condition": {
                "ref": "veicoli.chilometraggio", "predicate": "approximately",
                "value": {"kind": "number", "value": 100000, "resolver": "approx_relative"},
            }, "provenance": {"text": "circa centomila chilometri"}},
        ])),
        ("17.3 aggregation", envelope("operations", confidence=0.93, operations=[
            {"op": "add_measure", "ref": "ordini_vendita.importo_totale", "function": "sum",
             "provenance": {"text": "somma degli importi"}},
            {"op": "add_group", "ref": "ordini_vendita.venditore",
             "provenance": {"text": "per venditore"}},
        ])),
        ("17.4 clarification", envelope("clarification", confidence=0.42, clarification={
            "question": "Rossi come cliente o come venditore?",
            "provenance": {"text": "di Rossi"},
            "options": [
                {"label": "Come cliente", "operations": [{
                    "op": "add_condition", "condition": {
                        "ref": "ordini_vendita.cliente", "predicate": "is_one_of",
                        "value": {"kind": "reference", "text": "Rossi"}}}]},
                {"label": "Come venditore", "operations": [{
                    "op": "add_condition", "condition": {
                        "ref": "ordini_vendita.venditore", "predicate": "is_one_of",
                        "value": {"kind": "reference", "text": "Rossi"}}}]},
            ],
        })),
        ("17.5 out of scope", envelope("out_of_scope", confidence=0.97,
                                       scope_note="modifica_dati")),
        ("not understood", envelope("not_understood")),
        ("D87 category", envelope("operations", operations=[
            {"op": "add_condition", "condition": {
                "ref": "ordini_vendita.da_fatturare", "predicate": "is_category"},
             "provenance": {"text": "da fatturare"}},
        ])),
    ]


def invalid_envelopes() -> list[tuple[str, dict]]:
    return [
        ("invented operation", envelope("operations", operations=[
            {"op": "set_raw_domain", "ref": "x"},
        ])),
        ("invented predicate", envelope("operations", operations=[
            {"op": "add_condition", "condition": {
                "ref": "clienti.citta", "predicate": "sounds_like",
                "value": {"kind": "text", "text": "Milano"}}},
        ])),
        ("invented view", envelope("operations", operations=[
            {"op": "set_view", "view": "gantt"},
        ])),
        ("empty operations", envelope("operations", operations=[])),
        ("foreign payload", envelope("not_understood", scope_note="modifica_dati")),
        ("unknown key", envelope("not_understood", hint="be nice")),
        ("both addressing forms", envelope("operations", operations=[
            {"op": "remove_condition", "id": "c1", "ref": "clienti.citta"},
        ])),
        ("neither addressing form", envelope("operations", operations=[
            {"op": "remove_condition"},
        ])),
        ("confidence above one", envelope("not_understood", confidence=1.4)),
        ("one clarification option", envelope("clarification", clarification={
            "question": "Cliente?",
            "options": [{"label": "Sì", "operations": [{"op": "clear_filter"}]}],
        })),
        ("technical name where a value belongs", envelope("operations", operations=[
            {"op": "add_condition", "condition": {
                "ref": "clienti.citta", "predicate": "equals",
                "value": {"kind": "text", "text": "Milano", "domain": "[('x','=',1)]"}}},
        ])),
    ]


class TestEnvelopeSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = schema_module.build_envelope_schema()

    def test_worked_examples_validate(self):
        for name, candidate in valid_envelopes():
            with self.subTest(example=name):
                self.assertEqual(
                    _jsonschema.validate(candidate, self.schema), [], f"{name} rejected"
                )

    def test_invalid_shapes_are_refused(self):
        for name, candidate in invalid_envelopes():
            with self.subTest(example=name):
                self.assertNotEqual(
                    _jsonschema.validate(candidate, self.schema), [], f"{name} accepted"
                )

    def test_the_schema_and_the_validator_agree(self):
        """Both derive from `vocabulary.py`; a disagreement means one has drifted."""
        for name, candidate in valid_envelopes():
            with self.subTest(example=name, expectation="both accept"):
                self.assertEqual(structural.validate_envelope(candidate), [])
                self.assertEqual(_jsonschema.validate(candidate, self.schema), [])
        for name, candidate in invalid_envelopes():
            with self.subTest(example=name, expectation="both refuse"):
                self.assertNotEqual(structural.validate_envelope(candidate), [])
                self.assertNotEqual(_jsonschema.validate(candidate, self.schema), [])


class TestStateSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = schema_module.build_state_schema()

    def state_of_section_5_1(self) -> dict:
        return {
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

    def test_section_5_1_validates(self):
        self.assertEqual(
            _jsonschema.validate(self.state_of_section_5_1(), self.schema), []
        )

    def test_provenance_on_the_limit_is_admitted_by_both(self):
        """"The first 5" is a fragment of the user's sentence (§10.3).

        This fixture exists because the corpus found the disagreement the
        agreement test above had missed: the schema admitted provenance on
        `limit`, the validator did not, and no example carried one.
        """
        state = self.state_of_section_5_1()
        state["limit"] = {"value": 5, "origin": "user",
                          "provenance": {"text": "gli ultimi 5"}}
        self.assertEqual(_jsonschema.validate(state, self.schema), [])
        self.assertEqual(structural.validate_state(state), [])

    def test_provenance_on_the_presentation_is_admitted_by_both(self):
        state = self.state_of_section_5_1()
        state["presentation"] = {"view": "pivot", "origin": "user",
                                 "provenance": {"text": "come tabella pivot"}}
        self.assertEqual(_jsonschema.validate(state, self.schema), [])
        self.assertEqual(structural.validate_state(state), [])

    def test_a_state_needs_limit_and_presentation(self):
        state = self.state_of_section_5_1()
        del state["limit"]
        self.assertNotEqual(_jsonschema.validate(state, self.schema), [])

    def test_a_state_condition_needs_an_identifier(self):
        state = self.state_of_section_5_1()
        del state["filter"]["conditions"][0]["id"]
        self.assertNotEqual(_jsonschema.validate(state, self.schema), [])

    def test_an_explicitly_empty_section_is_refused(self):
        state = self.state_of_section_5_1()
        state["fields"] = []
        self.assertNotEqual(_jsonschema.validate(state, self.schema), [])

    def test_no_odoo_names_are_expressible_as_extra_keys(self):
        state = self.state_of_section_5_1()
        state["model"] = "sale.order"
        self.assertNotEqual(_jsonschema.validate(state, self.schema), [])

    def test_a_limit_above_the_maximum_is_refused(self):
        state = self.state_of_section_5_1()
        state["limit"] = {"value": 5000, "origin": "user"}
        self.assertNotEqual(_jsonschema.validate(state, self.schema), [])


class TestCommittedArtefacts(unittest.TestCase):
    """The files under `contract/schema/` are derived: they must match the generator.

    Committed rather than generated on demand because part 5 hands them to a
    provider for constrained generation, and because a schema in the repository can
    be read and diffed by someone who is not running our tooling (§18.1).
    """

    def test_every_artefact_exists_and_matches(self):
        for name, build in schema_module.ARTEFACTS.items():
            with self.subTest(artefact=name):
                path = SCHEMA_DIR / name
                self.assertTrue(
                    path.is_file(),
                    f"{name} is missing — run python3 tools/dsl/emit_schema.py --write",
                )
                committed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    committed,
                    build(),
                    f"{name} is stale — run python3 tools/dsl/emit_schema.py --write",
                )

    def test_no_stray_artefacts(self):
        if not SCHEMA_DIR.is_dir():
            self.fail("contract/schema/ does not exist")
        present = {path.name for path in SCHEMA_DIR.glob("*.json")}
        self.assertEqual(present, set(schema_module.ARTEFACTS))


if __name__ == "__main__":
    unittest.main()
