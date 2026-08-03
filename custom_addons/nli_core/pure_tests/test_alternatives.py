"""The readings a refusal offers instead of stopping (D106).

D105 turns an invented filter into a refusal. Measured on 80 openings: eleven wrong
filters became refusals and no correct one did. But a bare refusal leaves the user
where they were — these are the options that make it a question.
"""

from __future__ import annotations

import unittest

from ..application import alternatives

CANDIDATES = ("ordini.in_bozza", "ordini.da_consegnare", "ordini.confermati",
              "ordini.da_fatturare")


def _condition(ref, text):
    return {"op": "add_condition", "combine": "all",
            "condition": {"ref": ref, "predicate": "is_category"},
            "provenance": {"text": text}}


OPERATIONS = [
    {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
    _condition("ordini.in_bozza", "lo scorso mese"),
    {"op": "set_limit", "value": 5, "provenance": {"text": "i primi 5"}},
]


class TestAlternatives(unittest.TestCase):
    def _readings(self, **overrides):
        arguments = {"ungrounded": ["ordini.in_bozza"], "candidates": CANDIDATES}
        arguments.update(overrides)
        return alternatives.for_ungrounded(OPERATIONS, **arguments)

    def test_the_first_reading_is_the_sentence_without_the_condition(self):
        """The safe one, and the only one always available: the user said nothing
        that names a condition, so not filtering is a faithful reading."""
        first = self._readings()[0]
        self.assertEqual(first.kind, "without")
        self.assertIsNone(first.ref)
        self.assertEqual([operation["op"] for operation in first.operations],
                         ["set_target", "set_limit"])

    def test_the_others_replace_the_reference_and_keep_the_rest(self):
        second = self._readings()[1]
        self.assertEqual(second.kind, "instead")
        self.assertEqual(second.ref, "ordini.da_consegnare")
        self.assertEqual(second.operations[1]["condition"]["ref"], "ordini.da_consegnare")
        self.assertEqual(second.operations[2], OPERATIONS[2])

    def test_the_condition_that_was_refused_is_not_proposed_again(self):
        proposed = {reading.ref for reading in self._readings()}
        self.assertNotIn("ordini.in_bozza", proposed)

    def test_a_condition_the_sentence_already_carries_is_not_proposed(self):
        """Offering a condition the user is already under is not a choice."""
        operations = [*OPERATIONS, _condition("ordini.confermati", "confermati")]
        readings = alternatives.for_ungrounded(
            operations, ungrounded=["ordini.in_bozza"], candidates=CANDIDATES)
        self.assertNotIn("ordini.confermati", {reading.ref for reading in readings})

    def test_the_contract_s_bounds_are_respected(self):
        """§4.4 admits from two to four options: fewer is not a question, more is a
        list nobody reads."""
        self.assertLessEqual(len(self._readings()), alternatives.MAX_OPTIONS)
        self.assertGreaterEqual(len(self._readings()), alternatives.MIN_OPTIONS)

    def test_without_candidates_there_is_no_question_to_ask(self):
        """One option is not a choice, and a refusal that pretends to offer one is
        worse than a refusal that admits there is none."""
        self.assertEqual(self._readings(candidates=()), [])

    def test_nothing_is_offered_when_the_reference_is_not_in_the_operations(self):
        self.assertEqual(self._readings(ungrounded=["ordini.mai_vista"]), [])

    def test_the_original_operations_are_not_touched(self):
        prima = [dict(operation) for operation in OPERATIONS]
        self._readings()
        self.assertEqual(OPERATIONS, prima)
        self.assertEqual(OPERATIONS[1]["condition"]["ref"], "ordini.in_bozza")

    def test_only_the_first_ungrounded_condition_is_questioned(self):
        """Two axes in one question would need a matrix of options, and the contract
        admits a list."""
        readings = self._readings(ungrounded=["ordini.in_bozza", "ordini.altro"])
        self.assertTrue(all(
            "ordini.in_bozza" not in str(reading.operations) for reading in readings))


class TestGroundedIn(unittest.TestCase):
    """An option has to be applicable as it stands, or it is not a choice (D121)."""

    def test_the_replaced_condition_is_founded_in_the_label(self):
        reading = alternatives.for_ungrounded(
            OPERATIONS, ungrounded=["ordini.in_bozza"], candidates=CANDIDATES)[1]
        grounded = alternatives.grounded_in(
            reading.operations, reading.ref, "da consegnare")
        self.assertEqual(grounded[1]["provenance"], {"text": "da consegnare"})

    def test_the_other_operations_keep_their_own_fragment(self):
        """Rewriting them all would say the user's answer produced the entity too, and
        the fragments are what §10.3 highlights back to them."""
        reading = alternatives.for_ungrounded(
            OPERATIONS, ungrounded=["ordini.in_bozza"], candidates=CANDIDATES)[1]
        grounded = alternatives.grounded_in(
            reading.operations, reading.ref, "da consegnare")
        self.assertEqual(grounded[0]["provenance"], {"text": "ordini"})
        self.assertEqual(grounded[2]["provenance"], {"text": "i primi 5"})

    def test_a_reference_no_operation_names_changes_nothing(self):
        grounded = alternatives.grounded_in(OPERATIONS, "ordini.mai_vista", "qualunque")
        self.assertEqual(grounded, list(OPERATIONS))

    def test_the_operations_given_are_not_touched(self):
        prima = [dict(operation) for operation in OPERATIONS]
        alternatives.grounded_in(OPERATIONS, "ordini.in_bozza", "da consegnare")
        self.assertEqual(OPERATIONS, prima)


class TestChosen(unittest.TestCase):
    """Which reading a sentence picks, when it picks one (D121).

    This is the whole of what separates an answer that costs nothing from an answer
    that costs a minute of model time: the operations are already here.
    """

    #: Le opzioni di D106 sono richieste intere: ognuna porta il proprio `set_target`.
    OPTIONS = [
        {"label": "senza filtrare per “lo scorso mese”",
         "operations": [{"op": "set_target"}]},
        {"label": "da consegnare",
         "operations": [{"op": "set_target"}, {"op": "add_condition"}]},
        {"label": "Anno corrente (2024)",
         "operations": [{"op": "set_target"}, {"op": "set_limit"}]},
    ]

    def _pick(self, utterance, **kwargs):
        return alternatives.chosen(self.OPTIONS, utterance, **kwargs)

    def test_the_sentence_that_is_the_label_picks_that_option(self):
        self.assertEqual(self._pick("da consegnare"),
                         [{"op": "set_target"}, {"op": "add_condition"}])

    def test_case_and_spacing_are_not_choices_the_user_made(self):
        self.assertEqual(self._pick("  Da   Consegnare "),
                         [{"op": "set_target"}, {"op": "add_condition"}])

    def test_the_quotation_marks_of_a_label_do_not_have_to_be_retyped(self):
        self.assertEqual(self._pick("senza filtrare per \"lo scorso mese\"."),
                         [{"op": "set_target"}])

    def test_the_brackets_of_a_label_do_not_have_to_be_retyped(self):
        """Misurato sul campo: l'opzione diceva *«Anno corrente (2024)»* e l'utente ha
        scritto *«anno corrente 2024»*."""
        self.assertEqual(self._pick("anno corrente 2024"),
                         [{"op": "set_target"}, {"op": "set_limit"}])

    def test_a_sentence_that_is_not_a_label_is_not_an_answer(self):
        """It falls through to the ordinary path, which interprets it with the context
        of D120. Guessing here would answer something the user did not say."""
        self.assertIsNone(self._pick("quelli di marzo"))

    def test_an_accent_is_not_noise(self):
        """Two named conditions differing by an accent are two conditions, and picking
        the wrong one silently is worse than asking again."""
        options = [{"label": "però", "operations": [{"op": "set_target"}]},
                   {"label": "pero", "operations": [{"op": "set_target"}, {"op": "b"}]}]
        self.assertEqual(alternatives.chosen(options, "pero"),
                         [{"op": "set_target"}, {"op": "b"}])

    def test_two_options_that_read_the_same_are_not_a_choice(self):
        options = [{"label": "uguale", "operations": [{"op": "set_target"}]},
                   {"label": "Uguale", "operations": [{"op": "set_target"}]}]
        self.assertIsNone(alternatives.chosen(options, "uguale"))

    def test_nothing_is_picked_by_an_empty_sentence(self):
        self.assertIsNone(self._pick("   "))
        self.assertIsNone(self._pick(""))

    def test_nothing_is_picked_when_there_are_no_options(self):
        self.assertIsNone(alternatives.chosen([], "da consegnare"))

    def test_an_option_without_operations_is_not_applicable(self):
        """Applying nothing would present the previous state as if it were an answer."""
        self.assertIsNone(
            alternatives.chosen([{"label": "vuota", "operations": []}], "vuota"))

    # --- l'opzione parziale di un chiarimento scritto dal modello ---------

    PARTIAL = [{"label": "Anno corrente (2024)", "operations": [{"op": "add_condition"}]},
               {"label": "Anno fiscale corrente", "operations": [{"op": "add_condition"}]}]

    def test_an_option_without_an_entity_is_refused_when_none_is_known(self):
        """Un chiarimento scritto dal modello e' completo quanto il modello l'ha fatto.
        Applicare un'opzione che non nomina l'entita' trasformerebbe la sua risposta
        parziale in un «non ho capito» con il nostro nome sopra."""
        self.assertIsNone(alternatives.chosen(self.PARTIAL, "anno corrente 2024"))

    def test_the_same_option_is_taken_when_the_conversation_has_an_entity(self):
        """Un raffinamento porta gia' il proprio bersaglio: li' l'operazione che
        disambigua e' tutto quello che serve."""
        self.assertEqual(
            alternatives.chosen(self.PARTIAL, "anno corrente 2024", entity_known=True),
            [{"op": "add_condition"}])

    def test_the_stored_options_are_not_handed_out(self):
        """They live on the turn, which the caller is free to mutate: handing out the
        same lists would let an application rewrite the history it came from."""
        picked = self._pick("da consegnare")
        picked[0]["op"] = "altro"
        self.assertEqual(self.OPTIONS[1]["operations"][0], {"op": "set_target"})


if __name__ == "__main__":
    unittest.main()
