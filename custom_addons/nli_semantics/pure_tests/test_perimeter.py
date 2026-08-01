"""What the user may say, derived from what the system can do (D104).

The structure only: this zone is a function of its arguments and has no language. The
wording is tested where it lives, in `nli_web`.
"""

from __future__ import annotations

import unittest

from ..catalogue import perimeter


class Attributo:
    def __init__(self, ref, terms, kind):
        self.ref, self.terms, self.type = ref, terms, kind


class Categoria:
    def __init__(self, ref, terms):
        self.ref, self.terms = ref, terms


class Catalogo:
    entity = "fatture_cliente"
    categories = (Categoria("fatture_cliente.scadute", ("scadute", "insolute")),
                  Categoria("fatture_cliente.in_bozza", ("in bozza",)))
    attributes = (Attributo("fatture_cliente.cliente", ("cliente",), "relation"),
                  Attributo("fatture_cliente.importo", ("importo", "totale"), "number"),
                  Attributo("fatture_cliente.data", ("data",), "date"))


PERIODI = frozenset({"today", "current_month", "previous_month"})


class TestPerimeter(unittest.TestCase):
    def setUp(self):
        self.groups = perimeter.grouped(Catalogo(), periods=PERIODI)

    def test_the_customer_s_own_word_is_the_one_shown(self):
        """Not the reference, and not the vendor's word: the dictionary is built from
        the installation precisely so the company's vocabulary is the one that wins."""
        conditions = self.groups[perimeter.CONDITION]
        self.assertEqual([suggestion.label for suggestion in conditions],
                         ["scadute", "in bozza"])

    def test_a_comparison_is_offered_only_where_it_means_something(self):
        """A comparison on a customer or a state is the mistake D103 made
        unexpressible; offering it would teach the user to make it."""
        compared = {suggestion.ref for suggestion in self.groups[perimeter.COMPARISON]}
        self.assertEqual(compared,
                         {"fatture_cliente.importo", "fatture_cliente.data"})

    def test_every_attribute_can_be_a_column(self):
        columns = {suggestion.ref for suggestion in self.groups[perimeter.COLUMN]}
        self.assertEqual(len(columns), len(Catalogo.attributes))

    def test_periods_carry_the_symbol_and_no_word(self):
        """The words are the product's and belong to the layer that has a user."""
        periods = self.groups[perimeter.PERIOD]
        self.assertEqual({suggestion.symbol for suggestion in periods}, PERIODI)
        self.assertEqual({suggestion.label for suggestion in periods}, {""})

    def test_no_periods_asked_for_means_none_offered(self):
        """The zone does not know the contract's vocabulary and must not invent it."""
        self.assertEqual(perimeter.grouped(Catalogo())[perimeter.PERIOD], [])

    def test_the_perimeter_contains_nothing_the_catalogue_does_not(self):
        """The whole guarantee: a suggestion that does not work would be worse than
        no suggestion, and it cannot arise because the source is the same one the
        model is shown."""
        known = ({category.ref for category in Catalogo.categories}
                 | {attribute.ref for attribute in Catalogo.attributes})
        for suggestion in perimeter.of(Catalogo(), periods=PERIODI):
            if suggestion.group != perimeter.PERIOD:
                self.assertIn(suggestion.ref, known)

    def test_an_empty_catalogue_offers_nothing_rather_than_something_generic(self):
        class Vuoto:
            entity = "x"
            categories = ()
            attributes = ()

        self.assertEqual(perimeter.of(Vuoto(), periods=()), [])


if __name__ == "__main__":
    unittest.main()
