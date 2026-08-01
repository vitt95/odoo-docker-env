"""References closed by the catalogue of the turn, and kept apart by genus.

Two measurements produced this file, both on `qwen3.5:9b`, 28/07/2026, forty cases.

**D101.** Twice the model emitted a reference nobody has — `oppurtunita.fase`, where
the entity is spelled `opportunita`, and a bare `importo_totale` with no entity at
all. Both passed levels 1 and 2, which know the *shape* of a reference and not the
catalogue, and both landed in the state.

**D102.** With the set closed but flat, twice more it asked for `fatture_cliente` — an
**entity** — as a column, because the catalogue lists the other entities too for the
entity resolution of phase A. A closed set that cannot tell a column from an entity
admits a request that means nothing.

`prompt.py` already claimed the property in prose: *«the model chooses, it never
invents»*. These tests are the difference between claiming it and having it.
"""

from __future__ import annotations

import unittest

from . import _jsonschema
from ..contract import schema as schema_module
from ..contract.envelope import envelope

CATALOGUE = schema_module.References(
    entities=("fatture_cliente", "opportunita"),
    attributes=("opportunita.fase", "opportunita.valore_atteso"),
    categories=("opportunita.confermati",),
)


def _operations(*operations):
    return envelope("operations", operations=list(operations))


class TestReferencesAreClosed(unittest.TestCase):
    def setUp(self):
        self.closed = schema_module.build_envelope_schema(refs=CATALOGUE)
        self.general = schema_module.build_envelope_schema()

    def _admitted(self, *operations):
        return _jsonschema.validate(_operations(*operations), self.closed) == []

    # --- D101: outside the catalogue ---------------------------------------
    def test_a_reference_of_the_catalogue_is_admitted(self):
        self.assertTrue(self._admitted(
            {"op": "set_target", "ref": "opportunita",
             "provenance": {"text": "le trattative"}}))

    def test_a_misspelt_reference_is_not_expressible(self):
        """`oppurtunita` is one transposition away from the real one, which is exactly
        why prose could not stop it."""
        self.assertFalse(self._admitted(
            {"op": "set_target", "ref": "oppurtunita",
             "provenance": {"text": "le trattative"}}))

    def test_a_reference_without_its_entity_is_not_expressible(self):
        self.assertFalse(self._admitted(
            {"op": "set_fields", "refs": ["valore_atteso"],
             "provenance": {"text": "con valore"}}))

    def test_every_element_of_a_list_of_references_is_checked(self):
        good = ["opportunita.fase", "opportunita.valore_atteso"]
        self.assertTrue(self._admitted(
            {"op": "set_fields", "refs": good, "provenance": {"text": "con fase, valore"}}))
        self.assertFalse(self._admitted(
            {"op": "set_fields", "refs": [*good, "opportunita.inventato"],
             "provenance": {"text": "con fase, valore"}}))

    # --- D102: the wrong genus ---------------------------------------------
    def test_an_entity_is_not_a_column(self):
        """Measured twice: `set_fields` with `fatture_cliente` in it. A column that is
        an entity is a request with no meaning, and the flat set admitted it."""
        self.assertFalse(self._admitted(
            {"op": "set_fields", "refs": ["fatture_cliente", "opportunita.fase"],
             "provenance": {"text": "con cliente, fase"}}))

    def test_an_entity_is_not_a_grouping_nor_an_ordering(self):
        for verb in ("add_group", "add_order"):
            with self.subTest(verb=verb):
                self.assertFalse(self._admitted(
                    {"op": verb, "ref": "fatture_cliente",
                     "provenance": {"text": "per cliente"}}))

    def test_an_attribute_is_not_the_target(self):
        """The reverse direction, and it matters as much: an interrogation whose
        subject is a column has lost its subject."""
        self.assertFalse(self._admitted(
            {"op": "set_target", "ref": "opportunita.fase",
             "provenance": {"text": "le fasi"}}))

    def test_a_category_is_a_condition_and_nothing_else(self):
        """T5 under D87: a category is the reference of a named condition. It is not a
        column — there is no field behind it to show."""
        self.assertTrue(self._admitted(
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "opportunita.confermati", "predicate": "is_category"},
             "provenance": {"text": "confermate"}}))
        self.assertFalse(self._admitted(
            {"op": "set_fields", "refs": ["opportunita.confermati"],
             "provenance": {"text": "con confermate"}}))

    def test_a_condition_admits_an_attribute_and_refuses_an_entity(self):
        self.assertTrue(self._admitted(
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "opportunita.valore_atteso", "predicate": "greater_than",
                           "value": {"kind": "number", "value": 100}},
             "provenance": {"text": "budget oltre 100"}}))
        self.assertFalse(self._admitted(
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "fatture_cliente", "predicate": "is_category"},
             "provenance": {"text": "fatture"}}))

    # --- what stays open ----------------------------------------------------
    def test_the_identifier_of_a_condition_is_not_a_reference(self):
        """`c1` names a condition inside the state. The catalogue has nothing to say
        about it, and closing it would make `remove_condition` unexpressible."""
        self.assertTrue(self._admitted(
            {"op": "remove_condition", "id": "c1",
             "provenance": {"text": "togli quel filtro"}}))

    def test_without_a_catalogue_the_schema_is_the_general_one(self):
        """What `emit_schema.py` writes to disk: a file cannot carry the enumeration
        of a turn, and a profile that does not constrain generation never sees it."""
        self.assertEqual(
            _jsonschema.validate(
                _operations({"op": "set_target", "ref": "oppurtunita",
                             "provenance": {"text": "x"}}),
                self.general),
            [])


if __name__ == "__main__":
    unittest.main()
