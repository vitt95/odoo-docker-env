"""The perimeter with its words, on a live catalogue (D104).

The structure is tested in the pure zone. What is tested here is the half that needs a
user: the product's phrasings, the customer's terms left alone, and the guarantee that
the suggestions are derived from the same catalogue the model is shown — so a user who
cannot read a field is never offered it.
"""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPerimeter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.perimeter = self.env["nli.perimeter"]
        semantics_model = self.env["nli.semantics"]
        self.semantics = semantics_model.semantics(("res.partner",))
        self.catalogue = semantics_model.catalogue_for(
            self.semantics, "res_partner", context_window=32_000)

    def _groups(self, payload):
        return {group["kind"]: group for group in payload["groups"]}

    def test_the_periods_are_words_and_not_symbols(self):
        """`year_to_date` is not a phrase anybody says."""
        groups = self._groups(self.perimeter.of_catalogue(self.catalogue))
        labels = {item["label"] for item in groups["period"]["items"]}
        self.assertIn("this month", labels)
        self.assertNotIn("current_month", labels)

    def test_every_period_keeps_its_symbol_alongside_the_word(self):
        """The interface shows the word; what it sends back is the symbol, because a
        word is what a user says and a symbol is what the contract admits."""
        groups = self._groups(self.perimeter.of_catalogue(self.catalogue))
        for item in groups["period"]["items"]:
            self.assertTrue(item["symbol"])
            self.assertTrue(item["label"])

    def test_the_periods_that_need_an_argument_are_not_offered(self):
        """*«ultimi N giorni»* without the N is a phrase the user has to finish."""
        groups = self._groups(self.perimeter.of_catalogue(self.catalogue))
        symbols = {item["symbol"] for item in groups["period"]["items"]}
        self.assertNotIn("last_n_days", symbols)
        self.assertNotIn("absolute", symbols)

    def test_a_comparison_shows_the_shape_and_not_a_value(self):
        groups = self._groups(self.perimeter.of_catalogue(self.catalogue))
        if "comparison" not in groups:
            self.skipTest("this catalogue exposes no comparable attribute")
        for item in groups["comparison"]["items"]:
            self.assertIn("…", item["label"])

    def test_the_columns_are_the_catalogue_s_own_terms(self):
        """Untranslated on purpose: replacing the company's vocabulary with ours is
        the opposite of what a dictionary built from the installation is for."""
        groups = self._groups(self.perimeter.of_catalogue(self.catalogue))
        offered = {item["ref"] for item in groups["column"]["items"]}
        self.assertEqual(offered, {attribute.ref
                                   for attribute in self.catalogue.attributes})

    def test_nothing_is_offered_that_the_model_is_not_also_shown(self):
        """The guarantee that makes a suggestion safe: same source, same limits — the
        exposure rules and the budget of D31/D79 have already been applied."""
        payload = self.perimeter.of_catalogue(self.catalogue)
        known = ({category.ref for category in self.catalogue.categories}
                 | {attribute.ref for attribute in self.catalogue.attributes})
        for group in payload["groups"]:
            for item in group["items"]:
                if item["kind"] != "period":
                    self.assertIn(item["ref"], known)

    def test_it_is_built_on_the_asking_user_s_catalogue(self):
        """A perimeter assembled anywhere else would be a second, unguarded path to
        the same information."""
        payload = self.perimeter.for_entity("res_partner")
        self.assertEqual(payload["entity"], "res_partner")
        self.assertTrue(payload["groups"])
