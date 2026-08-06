"""Un periodo appoggiato su una data che la frase non nomina si chiede (D135).

**Il fallimento misurato.** Batteria del 3 agosto 2026, modello e banca dati veri:
*«mostrami i lead creati quest'anno»* ha risposto `not_understood` tre volte su tre,
e *«mostrami gli ordini di vendita di questo mese»* pure. Sono le due entita' che
espongono piu' di una data, cioe' le due domande che chiunque farebbe per prime.

La causa non e' il modello: e' il compito che gli era stato dato. Il prompt gli
chiedeva di **scrivere lui** il chiarimento quando l'ancora del tempo (D110) dichiara
`choices`, cioe' di inventare due-quattro opzioni complete e applicabili. D128 ha
dovuto aggiungere una validazione perche' quelle opzioni arrivavano rotte.

Qui il compito torna dalla parte giusta: il modello risponde **normalmente** — cosa
che sa fare, *«creati quest'anno»* ha dato 39 record il 3 agosto mattina — e la data
indovinata la riconosciamo noi, con la stessa regola di D105 (una condizione nominata
che il proprio frammento non nomina non e' stata chiesta) applicata alle date invece
che alle categorie.
"""

from __future__ import annotations

import unittest

from ..application import alternatives
from ..contract import state as state_module
from ..validation import contextual

#: I termini di due date, come il dizionario li porta. Riconoscitore letterale di
#: proposito: questo file prova la **regola**, non la tolleranza ai refusi, che vive
#: in `nli_semantics` e li' e' provata.
TERMS = {
    "lead.create_date": ("data di creazione", "creazione"),
    "lead.date_deadline": ("data di scadenza", "scadenza"),
}

ANCHOR = {"choices": ["lead.create_date", "lead.date_deadline"]}


def names(reference: str, text: str) -> bool:
    return any(term in (text or "").casefold() for term in TERMS.get(reference, ()))


def _period(ref, text, identifier="c1", predicate="within"):
    return {"id": identifier, "ref": ref, "predicate": predicate, "origin": "user",
            "value": {"kind": "temporal", "expression": "current_year"},
            "provenance": {"text": text}}


def _state(*conditions):
    return {
        "dsl_version": "1.0",
        "target": {"ref": "lead", "origin": "user"},
        "filter": ({"connective": "all", "conditions": list(conditions)}
                   if len(conditions) > 1 else conditions[0]),
        "limit": {"value": 80, "origin": "default"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }


class TestAnchoring(unittest.TestCase):
    # --- la regola --------------------------------------------------------
    def test_a_period_on_a_date_the_sentence_did_not_name_is_refused(self):
        """*«mostrami i lead di quest'anno»*: due date esposte, il frammento non ne
        nomina nessuna, quindi la data e' stata scelta dal modello e non dall'utente."""
        failures = contextual.validate_anchoring(
            _state(_period("lead.create_date", "di quest'anno")),
            names=names, time_anchor=ANCHOR)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].code, "unanchored_period")
        self.assertEqual(failures[0].level, 3)
        self.assertEqual(failures[0].path, "lead.create_date")
        self.assertIn("quest'anno", failures[0].detail)

    def test_a_period_on_the_date_the_sentence_names_passes(self):
        """*«i lead con data di creazione di quest'anno»*: la scelta e' dell'utente."""
        self.assertEqual(
            contextual.validate_anchoring(
                _state(_period("lead.create_date", "con data di creazione quest'anno")),
                names=names, time_anchor=ANCHOR),
            [])

    def test_a_single_date_is_never_asked_about(self):
        """Con una data sola non c'e' niente da scegliere: l'ancora di D110 dichiara
        `ref`, il periodo va li' per costruzione, e chiedere sarebbe una domanda con
        una risposta sola."""
        self.assertEqual(
            contextual.validate_anchoring(
                _state(_period("lead.create_date", "di quest'anno")),
                names=names, time_anchor={"ref": "lead.create_date"}),
            [])

    def test_no_anchor_at_all_is_not_this_rule_s_business(self):
        """Un'entita' senza date e' il ramo aperto di D110, non questo."""
        self.assertEqual(
            contextual.validate_anchoring(
                _state(_period("lead.create_date", "di quest'anno")),
                names=names, time_anchor=None),
            [])

    def test_a_condition_that_is_not_a_period_is_left_alone(self):
        """Una condizione su un attributo che non e' fra le date dell'ancora non
        porta un periodo, e giudicarla qui rifiuterebbe filtri legittimi."""
        condition = {"id": "c1", "ref": "lead.expected_revenue",
                     "predicate": "greater_than",
                     "value": {"kind": "number", "value": 1000},
                     "origin": "user", "provenance": {"text": "sopra 1000"}}
        self.assertEqual(
            contextual.validate_anchoring(_state(condition), names=names,
                                          time_anchor=ANCHOR),
            [])

    def test_a_condition_with_no_provenance_is_refused(self):
        condition = _period("lead.create_date", "")
        del condition["provenance"]
        self.assertEqual(
            len(contextual.validate_anchoring(_state(condition), names=names,
                                              time_anchor=ANCHOR)),
            1)

    def test_each_condition_is_judged_on_its_own(self):
        failures = contextual.validate_anchoring(
            _state(_period("lead.date_deadline", "con scadenza a maggio", "c1"),
                   _period("lead.create_date", "di quest'anno", "c2")),
            names=names, time_anchor=ANCHOR)
        self.assertEqual([failure.path for failure in failures], ["lead.create_date"])

    # --- la data nominata dalla frase, fuori dal frammento -----------------
    #
    # Misurato il 5 agosto 2026, batteria intera sul database vero: **diciotto frasi
    # su diciotto** della famiglia `date` finivano in chiarimento, e in tutte e
    # diciotto il modello aveva gia' scelto la data giusta. Il motivo e' sempre lo
    # stesso: la frase dice *«i lead **creati** negli ultimi 30 giorni»*, il modello
    # dichiara come provenienza *«negli ultimi 30 giorni»* — che e' il pezzo che porta
    # il tempo — e la parola che ancora resta fuori.
    #
    # La via d'uscita e' in **accettazione**, non in rifiuto: nessun turno che oggi
    # passa comincia a fallire. Questo e' cio' che la tiene compatibile con la ragione
    # per cui D105 guarda il frammento e non la frase — un turno di raffinamento porta
    # condizioni di frasi che nessuno sta piu' dicendo, e verificarle contro la frase
    # corrente le rifiuterebbe tutte.
    #
    # Ed e' stretta: la frase deve nominare **una sola** data fra quelle in scelta, e
    # dev'essere quella su cui il periodo e' caduto. Con due date nominate torna a
    # decidere il frammento, perche' li' la scelta e' di nuovo del modello.

    def test_the_sentence_names_the_date_outside_the_fragment(self):
        """*«i lead con creazione degli ultimi 30 giorni»*: il frammento porta il
        tempo, la frase porta la data, e insieme dicono cosa l'utente ha chiesto."""
        self.assertEqual(
            contextual.validate_anchoring(
                _state(_period("lead.create_date", "degli ultimi 30 giorni")),
                names=names, time_anchor=ANCHOR,
                utterance="i lead con creazione degli ultimi 30 giorni"),
            [])

    def test_two_dates_named_by_the_sentence_leave_the_choice_to_the_fragment(self):
        """Se la frase nomina creazione **e** scadenza, quale delle due porti il
        periodo torna a essere una scelta, e la fa il modello: si chiede."""
        failures = contextual.validate_anchoring(
            _state(_period("lead.create_date", "degli ultimi 30 giorni")),
            names=names, time_anchor=ANCHOR,
            utterance="i lead con creazione e scadenza degli ultimi 30 giorni")
        self.assertEqual([failure.code for failure in failures], ["unanchored_period"])

    def test_a_sentence_naming_another_date_does_not_anchor_this_one(self):
        """La frase nomina la scadenza, il periodo e' caduto sulla creazione: e'
        esattamente il caso in cui la data l'ha scelta il modello."""
        failures = contextual.validate_anchoring(
            _state(_period("lead.create_date", "degli ultimi 30 giorni")),
            names=names, time_anchor=ANCHOR,
            utterance="i lead con scadenza negli ultimi 30 giorni")
        self.assertEqual([failure.code for failure in failures], ["unanchored_period"])

    def test_without_the_sentence_the_rule_is_what_it_was(self):
        """La frase e' un argomento con un valore predefinito: chi non la passa —
        ogni chiamante che non e' stato aggiornato — ottiene la regola di prima."""
        failures = contextual.validate_anchoring(
            _state(_period("lead.create_date", "degli ultimi 30 giorni")),
            names=names, time_anchor=ANCHOR)
        self.assertEqual([failure.code for failure in failures], ["unanchored_period"])

    def test_the_chain_carries_the_sentence_through(self):
        """**Fallisce se qualcuno la scollega**: se `validate` smette di passare la
        frase, questa torna rossa."""
        state = _state(_period("lead.create_date", "degli ultimi 30 giorni"))
        known = frozenset({"lead", "lead.create_date", "lead.date_deadline"})
        types = {"lead.create_date": "datetime", "lead.date_deadline": "date"}
        self.assertEqual(
            contextual.validate(state, known_refs=known, types=types, names=names,
                                time_anchor=ANCHOR,
                                utterance="i lead con creazione degli ultimi 30 giorni"),
            [])

    # --- la condizione che c'era gia' non si rigiudica ----------------------
    #
    # **Trovato al primo uso vero del pannello, il 5 agosto 2026 sera.** Dopo una
    # risposta filtrata per data, *«ordinameli per email»* rispondeva *«non ho
    # capito»* — e il rifiuto non parlava dell'ordinamento: parlava del filtro del
    # turno prima, *«carries no provenance»*.
    #
    # E' un vicolo cieco per costruzione. Lo stato salvato **non ha** i frammenti:
    # `strip_provenance` li toglie di proposito finche' D54 non li pseudonimizza. Una
    # condizione ereditata quindi non puo' portare la prova che il livello 3 pretende,
    # e rigiudicarla ogni turno vuol dire condannarla sempre. Il risultato era che
    # dopo un filtro sulle date **ogni** raffinamento moriva: l'ordinamento, una
    # colonna in piu', un altro filtro.
    #
    # La regola giusta e' quella che D135 gia' dice a parole: il livello 3 giudica
    # cio' che **il modello ha appena scelto**. Una condizione accettata in un turno
    # passato e' stata giudicata allora, con le prove che allora c'erano.

    def test_a_condition_from_an_earlier_turn_is_not_judged_again(self):
        """Il filtro c'era gia' e non ha provenienza: e' stato accettato prima."""
        stato = _state(_period("lead.create_date", ""))
        self.assertEqual(
            contextual.validate_anchoring(
                stato, names=names, time_anchor=ANCHOR,
                utterance="ordinameli per email",
                already_judged=frozenset(state_module.condition_ids(stato))),
            [])

    def test_a_condition_of_this_turn_is_still_judged(self):
        """Con l'insieme vuoto — un turno che non eredita niente — nulla cambia."""
        failures = contextual.validate_anchoring(
            _state(_period("lead.create_date", "")),
            names=names, time_anchor=ANCHOR, already_judged=frozenset())
        self.assertEqual([failure.code for failure in failures], ["unanchored_period"])

    def test_only_the_inherited_one_is_spared(self):
        """Due condizioni, una vecchia e una nuova: si giudica la nuova."""
        stato = _state(_period("lead.create_date", ""),
                       _period("lead.date_deadline", "entro fine mese",
                               identifier="c2"))
        failures = contextual.validate_anchoring(
            stato, names=names, time_anchor=ANCHOR,
            already_judged=frozenset({"c1"}))
        self.assertEqual([(f.code, f.path) for f in failures],
                         [("unanchored_period", "lead.date_deadline")])

    # --- quando vale la pena di costruire il catalogo ----------------------
    def test_a_state_with_a_period_says_so(self):
        self.assertTrue(
            contextual.carries_period(_state(_period("lead.create_date", "quest'anno"))))

    def test_a_state_without_one_says_so_too(self):
        """Il ramo che risparmia la fase C: un turno senza periodo non ha niente da
        ancorare, e costruire il catalogo per scoprirlo sarebbe un quarto di secondo
        speso ogni volta per i pochi turni che ne hanno bisogno."""
        condition = {"id": "c1", "ref": "lead.expected_revenue",
                     "predicate": "greater_than",
                     "value": {"kind": "number", "value": 1000},
                     "origin": "user", "provenance": {"text": "sopra 1000"}}
        self.assertFalse(contextual.carries_period(_state(condition)))
        self.assertFalse(contextual.carries_period({"dsl_version": "1.0"}))

    # --- come e' agganciata alla catena -----------------------------------
    def test_the_chain_runs_it_when_an_anchor_is_given(self):
        """La prova che §38 chiede: **fallisce se qualcuno la scollega**. Senza
        `time_anchor` la regola non ha di che scattare, con l'ancora scatta, e
        toglierla da `validate` fa diventare rossa la seconda meta'."""
        state = _state(_period("lead.create_date", "di quest'anno"))
        known = frozenset({"lead", "lead.create_date", "lead.date_deadline"})
        types = {"lead.create_date": "datetime", "lead.date_deadline": "date"}
        self.assertEqual(
            contextual.validate(state, known_refs=known, types=types, names=names), [],
            "senza ancora non c'e' niente da cui vedere che la data e' indovinata")
        failures = contextual.validate(state, known_refs=known, types=types,
                                       names=names, time_anchor=ANCHOR)
        self.assertEqual([failure.code for failure in failures], ["unanchored_period"])

    def test_an_unresolved_reference_still_comes_first(self):
        """Il livello 3 ha due meta' e la prima non e' questa: una data che il
        catalogo non conosce e' un riferimento irrisolto, e dirlo due volte non
        aiuta nessuno."""
        state = _state(_period("lead.altro", "di quest'anno"))
        failures = contextual.validate(
            state, known_refs=frozenset({"lead"}), types={}, names=names,
            time_anchor={"choices": ["lead.altro", "lead.create_date"]})
        self.assertEqual([failure.code for failure in failures],
                         ["unresolved_reference"])


class TestUnanchoredAlternatives(unittest.TestCase):
    """Le opzioni le costruiamo noi dall'ancora, non le chiede nessuno al modello."""

    OPERATIONS = [
        {"op": "set_target", "ref": "lead", "provenance": {"text": "i lead"}},
        {"op": "add_condition", "combine": "all",
         "condition": {"ref": "lead.create_date", "predicate": "within",
                       "value": {"kind": "temporal", "expression": "current_year"}},
         "provenance": {"text": "di quest'anno"}},
        {"op": "set_limit", "value": 5, "provenance": {"text": "i primi 5"}},
    ]

    def _readings(self, **overrides):
        arguments = {"reference": "lead.create_date",
                     "choices": ["lead.create_date", "lead.date_deadline"]}
        arguments.update(overrides)
        return alternatives.for_unanchored(self.OPERATIONS, **arguments)

    def test_one_reading_per_date_and_the_period_travels_with_it(self):
        readings = self._readings()
        self.assertEqual([reading.ref for reading in readings],
                         ["lead.create_date", "lead.date_deadline"])
        for reading in readings:
            condition = reading.operations[1]["condition"]
            self.assertEqual(condition["ref"], reading.ref)
            self.assertEqual(condition["value"],
                             {"kind": "temporal", "expression": "current_year"})

    def test_the_date_the_model_chose_is_offered_too(self):
        """Diversamente da D106, dove la condizione rifiutata era inventata: qui la
        data e' una delle due possibili, e toglierla renderebbe irraggiungibile la
        risposta giusta meta' delle volte."""
        self.assertIn("lead.create_date", [reading.ref for reading in self._readings()])

    def test_the_rest_of_the_sentence_is_untouched(self):
        reading = self._readings()[1]
        self.assertEqual(reading.operations[0], self.OPERATIONS[0])
        self.assertEqual(reading.operations[2], self.OPERATIONS[2])

    def test_no_reading_drops_the_period(self):
        """D111: un'espressione di tempo non si lascia cadere. Nel chiarimento di
        D106 la prima lettura e' *«senza quel filtro»*; qui non puo' esistere, perche'
        la frase il periodo lo dice."""
        self.assertEqual([reading.kind for reading in self._readings()],
                         ["instead", "instead"])

    def test_more_dates_than_the_contract_admits_are_capped(self):
        """§4.4 ammette da due a quattro opzioni. Cinque date non diventano cinque
        opzioni: chi non trova la propria puo' ancora nominarla scrivendola."""
        readings = self._readings(choices=[f"lead.d{index}" for index in range(5)]
                                  + ["lead.create_date"])
        self.assertEqual(len(readings), alternatives.MAX_OPTIONS)

    def test_a_period_the_operations_do_not_carry_has_no_readings(self):
        """Niente da sostituire, nessuna opzione onesta da offrire."""
        self.assertEqual(self._readings(reference="lead.date_deadline"), [])

    def test_a_single_choice_is_not_a_question(self):
        self.assertEqual(self._readings(choices=["lead.create_date"]), [])

    def test_the_chosen_reading_is_founded_in_its_own_label(self):
        """D121: cliccare scrive l'etichetta nella casella e la invia, quindi al
        momento in cui la lettura si applica il frammento e' davvero quelle parole —
        ed e' cio' che fa passare il livello 3 al secondo giro invece di aggirarlo."""
        reading = self._readings()[1]
        grounded = alternatives.grounded_in(
            reading.operations, reading.ref, "data di scadenza")
        self.assertEqual(grounded[1]["provenance"], {"text": "data di scadenza"})
        self.assertTrue(names(reading.ref, grounded[1]["provenance"]["text"]))


if __name__ == "__main__":
    unittest.main()
