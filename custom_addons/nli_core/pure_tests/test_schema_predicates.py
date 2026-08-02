"""Predicates tied to the type of what the condition names (D103).

§8.1 has always paired each type with the comparisons that mean something on it, and
the validator has always read that table at level 2. The **schema** did not: a profile
with constrained generation could write `less_than` on a name or `contains` on an
amount, and the refusal arrived a level later — as a repair when the pair was
impossible, as a wrong answer when it was merely wrong.

`filter` was the last section under the threshold of D44 when this was written:
**72,5%** against 87,2% for `fields` and 98,0% for `target`, measured on all 444
openings of the corpus with `qwen3.5:9b`.
"""

from __future__ import annotations

import unittest

from . import _jsonschema
from ..contract import schema as schema_module
from ..contract.envelope import envelope

CATALOGUE = schema_module.References(
    entities=("ordini_vendita",),
    attributes=("ordini_vendita.cliente", "ordini_vendita.data_ordine",
                "ordini_vendita.importo_totale", "ordini_vendita.note",
                "ordini_vendita.stato"),
    categories=("ordini_vendita.confermati",),
    types={"ordini_vendita.cliente": "relation",
           "ordini_vendita.data_ordine": "date",
           "ordini_vendita.importo_totale": "number",
           "ordini_vendita.stato": "enum"},
    # `ordini_vendita.note` is deliberately absent from `types`.
)


class TestPredicatesFollowTheType(unittest.TestCase):
    def setUp(self):
        self.closed = schema_module.build_envelope_schema(refs=CATALOGUE)
        self.general = schema_module.build_envelope_schema()

    def _admitted(self, ref, predicate, *, schema=None, value=None):
        condition = {"ref": ref, "predicate": predicate}
        if value is not None:
            condition["value"] = value
        operation = {"op": "add_condition", "combine": "all", "condition": condition,
                     "provenance": {"text": "x"}}
        return _jsonschema.validate(
            envelope("operations", operations=[operation]),
            schema if schema is not None else self.closed) == []

    def test_a_number_admits_the_comparisons_of_a_number(self):
        for predicate in ("greater_than", "greater_or_equal", "less_than", "between"):
            with self.subTest(predicate=predicate):
                self.assertTrue(
                    self._admitted("ordini_vendita.importo_totale", predicate,
                                   value={"kind": "number", "value": 100}))

    def test_a_number_refuses_the_comparisons_of_a_text(self):
        """`contains` on an amount is not a wrong answer waiting to be validated: it
        is a sentence the contract has no reading for."""
        for predicate in ("contains", "starts_with"):
            with self.subTest(predicate=predicate):
                self.assertFalse(
                    self._admitted("ordini_vendita.importo_totale", predicate))

    def test_a_relation_refuses_an_ordering_comparison(self):
        """*"customers above 1000"* means nothing: a customer is not on a scale."""
        self.assertFalse(self._admitted("ordini_vendita.cliente", "less_than",
                                        value={"kind": "number", "value": 1000}))
        self.assertTrue(self._admitted("ordini_vendita.cliente", "is_set"))

    def test_a_date_takes_the_temporal_predicates_and_not_the_numeric_ones(self):
        self.assertTrue(self._admitted(
            "ordini_vendita.data_ordine", "within",
            value={"kind": "temporal", "expression": "current_month"}))
        self.assertFalse(self._admitted("ordini_vendita.data_ordine", "greater_than",
                                        value={"kind": "number", "value": 5}))

    def test_an_enumeration_takes_membership_and_nothing_else(self):
        self.assertTrue(self._admitted(
            "ordini_vendita.stato", "is_one_of",
            value={"kind": "enum", "items": ["confermato"]}))
        self.assertFalse(self._admitted("ordini_vendita.stato", "contains"))

    # --- the two directions of the category ------------------------------
    def test_a_category_takes_is_category_and_nothing_else(self):
        self.assertTrue(self._admitted("ordini_vendita.confermati", "is_category"))
        self.assertFalse(self._admitted(
            "ordini_vendita.confermati", "is_one_of",
            value={"kind": "enum", "items": ["confermato"]}))

    def test_an_attribute_does_not_take_is_category(self):
        """The mistake in the other direction, and the more tempting one: a category
        looks like a value of the field behind it, and it is not (D87)."""
        self.assertFalse(self._admitted("ordini_vendita.stato", "is_category"))

    # --- what stays open --------------------------------------------------
    def test_an_undeclared_type_keeps_the_whole_set(self):
        """Guessing which comparisons suit an unknown type would be inventing the
        table §8.1 already owns."""
        for predicate in ("contains", "greater_than", "is_set"):
            with self.subTest(predicate=predicate):
                self.assertTrue(self._admitted("ordini_vendita.note", predicate))

    def test_without_a_catalogue_nothing_is_narrowed(self):
        self.assertTrue(self._admitted("qualunque.cosa", "contains",
                                       schema=self.general))


if __name__ == "__main__":
    unittest.main()


class TestOneWayToSayAPeriod(unittest.TestCase):
    """Su una data, `between` e `within` dicevano la stessa cosa (**D113**).

    Il contratto ammetteva entrambi con un valore temporale, e il corpus ne accetta uno
    solo. Finche' il modello sbagliava il campo a cui attaccare il periodo, la
    differenza non emergeva mai da sola. Con l'ancora di **D110** (il catalogo dichiara
    dove si attacca un'espressione temporale) il campo e' giusto, e il predicato e'
    rimasto l'unica differenza: undici casi su 414 nella rimisura del 2 agosto,
    misurati come sbagliati mentre erano legali.
    """

    def setUp(self):
        self.closed = schema_module.build_envelope_schema(refs=CATALOGUE)

    def _admitted(self, ref, predicate, value):
        condition = {"ref": ref, "predicate": predicate, "value": value}
        operation = {"op": "add_condition", "combine": "all", "condition": condition,
                     "provenance": {"text": "x"}}
        return _jsonschema.validate(
            envelope("operations", operations=[operation]), self.closed) == []

    def test_a_date_no_longer_admits_between(self):
        """Inesprimibile, non rifiutato dopo: e' la stessa scelta di D112 (la categoria
        che la frase non nomina non entra nell'alfabeto del modello)."""
        self.assertFalse(self._admitted(
            "ordini_vendita.data_ordine", "between",
            {"kind": "temporal", "expression": "current_year"}))

    def test_a_date_still_admits_within(self):
        """L'altra meta': un vincolo che toglie anche il modo giusto di dirlo non e'
        un vincolo, e' un guasto."""
        self.assertTrue(self._admitted(
            "ordini_vendita.data_ordine", "within",
            {"kind": "temporal", "expression": "current_year"}))

    def test_a_number_still_admits_between(self):
        """`between` resta l'intervallo numerico, che non e' un doppione di niente:
        `canonical`/`equivalence` fonde `>= X` e `<= Y` proprio in quella forma."""
        self.assertTrue(self._admitted(
            "ordini_vendita.importo_totale", "between",
            {"kind": "range", "from": 100, "to": 500}))
