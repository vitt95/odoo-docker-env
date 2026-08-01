"""The interpretation written for a person (`09` §3).

Four rules, all of them requirements: no technical name, no syntax, the criteria
spelled out, first person and present tense. Plus the two properties every part must
carry — its origin, for the graded salience of D65, and its provenance, for the cross
highlighting of §3.4.
"""

from odoo.tests.common import TransactionCase, tagged


class Attributo:
    def __init__(self, ref, terms, kind="text"):
        self.ref, self.terms, self.type = ref, terms, kind


class Categoria:
    def __init__(self, ref, terms):
        self.ref, self.terms = ref, terms


class Catalogo:
    entity = "ordini_vendita"
    entity_names = (("ordini_vendita", ("ordini di vendita",)),)
    attributes = (Attributo("ordini_vendita.venditore", ("venditore",)),
                  Attributo("ordini_vendita.data_ordine", ("data d'ordine",), "date"),
                  Attributo("ordini_vendita.importo", ("importo",), "number"))
    categories = (Categoria("ordini_vendita.confermati", ("confermati",)),)


INTERPRETAZIONE = {
    "target": {"ref": "ordini_vendita", "origin": "user",
               "provenance": "gli ordini"},
    "conditions": [
        {"id": "c1", "ref": "ordini_vendita.confermati", "predicate": "is_category",
         "origin": "user", "provenance": "confermati"},
        {"id": "c2", "ref": "ordini_vendita.data_ordine", "predicate": "within",
         "value": {"kind": "temporal", "expression": "current_month"},
         "origin": "user", "provenance": "di questo mese"},
    ],
    "groups": [{"ref": "ordini_vendita.venditore", "origin": "user",
                "provenance": "per venditore"}],
    "order": [{"ref": "ordini_vendita.data_ordine", "direction": "desc",
               "origin": "inferred", "rule": "latest_implies_desc_by_date"}],
    "measures": [],
    "fields": [{"ref": "ordini_vendita.importo", "origin": "user"}],
    "periods": [("ordini_vendita.data_ordine", "luglio 2026")],
    "limit": {"value": 5, "origin": "user"},
    "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    "records": "i primi 5 di 12",
    "truncated": True,
}
INTERPRETAZIONE["periods"] = [{"ref": ref, "resolved": rendered}
                              for ref, rendered in INTERPRETAZIONE["periods"]]


@tagged("post_install", "-at_install")
class TestInWords(TransactionCase):
    def setUp(self):
        super().setUp()
        self.words = self.env["nli.interpretation"].in_words(
            INTERPRETAZIONE, catalogue=Catalogo())
        self.testo = " · ".join(part["text"] for part in self.words["parts"])

    def _part(self, kind):
        return next(part for part in self.words["parts"] if part["kind"] == kind)

    # --- the four rules of §3.2 -------------------------------------------
    def test_it_speaks_in_the_first_person_and_the_present(self):
        """*«Sto mostrando»* declares that an interpretation is happening, and
        therefore that there is something to check."""
        self.assertEqual(self.words["lead"], "I am showing:")

    def test_no_technical_name_appears(self):
        for technical in ("sale.order", "ordini_vendita.venditore", "date_order",
                          "user_id", "is_category", "within", "desc"):
            self.assertNotIn(technical, self.testo)

    def test_no_syntax_appears(self):
        for symbol in ("AND", "OR", ">=", "<=", "[", "]", "&"):
            self.assertNotIn(symbol, self.testo)

    def test_the_company_s_own_words_are_used(self):
        self.assertIn("ordini di vendita", self.testo)
        self.assertIn("venditore", self.testo)
        self.assertIn("confermati", self.testo)

    # --- what §3.1 requires to be visible ---------------------------------
    def test_every_element_that_decides_the_result_is_shown(self):
        kinds = {part["kind"] for part in self.words["parts"]}
        self.assertEqual(
            kinds, {"target", "condition", "group", "order", "fields", "limit", "view"})

    def test_the_ordering_spells_out_which_and_which_way(self):
        """§3.1 calls the ordering the seat of the misunderstanding of *«ultimi»*, and
        §3.2 requires the criterion spelled out rather than named."""
        order = self._part("order")
        self.assertIn("data d'ordine", order["text"])
        self.assertIn("newest first", order["text"])

    def test_the_period_is_shown_resolved_and_never_as_written(self):
        """*«questo mese»* confirms itself; *«luglio 2026»* is what lets somebody
        notice that the fiscal year starts in July."""
        period = next(part for part in self.words["parts"]
                      if part["kind"] == "condition" and "luglio" in part["text"])
        self.assertIn("luglio 2026", period["text"])
        self.assertNotIn("current_month", period["text"])
        self.assertNotIn("questo mese", period["text"])

    def test_a_named_condition_keeps_the_company_s_word_alone(self):
        """Saying *«stato fra ...»* would replace the company's word with ours."""
        condition = next(part for part in self.words["parts"]
                         if part["kind"] == "condition")
        self.assertEqual(condition["text"], "confermati")

    # --- what every part carries -------------------------------------------
    def test_each_part_declares_its_origin(self):
        for part in self.words["parts"]:
            self.assertIn(part["origin"], ("user", "inferred", "default"))
        self.assertEqual(self._part("order")["origin"], "inferred")
        self.assertEqual(self._part("target")["origin"], "user")

    def test_an_inference_declares_the_rule_that_produced_it(self):
        """§10.2: an inference nobody can see the reason for is one nobody can
        contradict."""
        self.assertEqual(self._part("order")["rule"], "latest_implies_desc_by_date")

    def test_the_provenance_travels_with_the_part(self):
        """§3.4 builds the cross highlighting on it, and requires an explicit
        equivalent where there is no pointing device — so it cannot live in a
        tooltip."""
        self.assertEqual(self._part("target")["provenance"], "gli ordini")

    def test_an_unresolved_period_says_so_instead_of_repeating_the_user(self):
        senza = dict(INTERPRETAZIONE, periods=[])
        words = self.env["nli.interpretation"].in_words(senza, catalogue=Catalogo())
        testo = " ".join(part["text"] for part in words["parts"])
        self.assertIn("not resolved", testo)
        self.assertNotIn("current_month", testo)

    def test_it_works_without_a_catalogue_without_showing_a_reference(self):
        """A dictionary that has no word for something is a gap to fix, not a reason
        to show `ordini_vendita.venditore` to a person."""
        words = self.env["nli.interpretation"].in_words(INTERPRETAZIONE)
        testo = " ".join(part["text"] for part in words["parts"])
        self.assertIn("venditore", testo)
        self.assertNotIn("ordini_vendita.venditore", testo)
