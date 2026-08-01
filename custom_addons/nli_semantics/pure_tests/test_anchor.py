"""Dove si attacca un'espressione temporale che non nomina un campo (D110).

D110 e' la decisione per cui il catalogo dichiara l'ancora del tempo: una data se ne
espone una sola, l'insieme delle scelte se sono due o piu', nulla se non ce ne sono.
"""

from __future__ import annotations

import unittest

from ..catalogue import anchor


class Attributo:
    """Il minimo che la regola legge: un riferimento e un tipo."""

    def __init__(self, ref: str, tipo: str):
        self.ref, self.type = ref, tipo


class TestDateRefs(unittest.TestCase):

    def test_only_the_two_time_types_count(self):
        attributi = [
            Attributo("fatture.data_fattura", "date"),
            Attributo("fatture.creato_il", "datetime"),
            Attributo("fatture.importo_totale", "number"),
            Attributo("fatture.cliente", "relation"),
            Attributo("fatture.note", "text"),
        ]
        self.assertEqual(
            anchor.date_refs(attributi),
            ("fatture.creato_il", "fatture.data_fattura"))

    def test_a_catalogue_without_dates_yields_nothing(self):
        """Il controllo non deve passare a vuoto: senza date la lista e' vuota,
        e l'ancora nulla che ne deriva e' un caso reale — i clienti non hanno date."""
        attributi = [Attributo("clienti.citta", "text")]
        self.assertEqual(anchor.date_refs(attributi), ())


class TestTimeAnchor(unittest.TestCase):

    def test_one_date_is_the_anchor(self):
        self.assertEqual(
            anchor.time_anchor(("ordini.data_ordine",)),
            {"ref": "ordini.data_ordine"})

    def test_two_dates_are_a_question_not_a_choice_we_make(self):
        """Sceglierne una fra due plausibili sarebbe indovinare: l'ancora porta
        entrambe e la risposta diventa un chiarimento."""
        self.assertEqual(
            anchor.time_anchor(("fatture.scadenza", "fatture.data_fattura")),
            {"choices": ["fatture.data_fattura", "fatture.scadenza"]})

    def test_no_date_is_no_anchor(self):
        self.assertIsNone(anchor.time_anchor(()))

    def test_the_order_is_stable(self):
        """Due catalogui uguali devono produrre lo stesso payload: un ordine che
        cambia fa cambiare il prompt a parita' di installazione."""
        uno = anchor.time_anchor(["b.due", "a.uno"])
        due = anchor.time_anchor(["a.uno", "b.due"])
        self.assertEqual(uno, due)
        self.assertEqual(uno, {"choices": ["a.uno", "b.due"]})
