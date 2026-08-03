"""The Interpreter and the two controls that guard the boundary."""

from __future__ import annotations

import json
import os
import unittest

from odoo.addons.nli_core.contract import vocabulary

from ..adapters import http as http_module
from ..adapters.base import Capabilities, HostNotAllowed, Request, SecretUnavailable
from ..adapters.recorded import RecordedAdapter
from ..interpreter import interpret
from ..prompt import catalogue_payload, system_message, user_message


class Attribute:
    def __init__(self, ref, terms, kind="char", values=()):
        self.ref, self.terms, self.type, self.values = ref, terms, kind, values


class Category:
    def __init__(self, ref, terms):
        self.ref, self.terms = ref, terms


class Catalogue:
    entity = "clienti"
    attributes = (Attribute("clienti.citta", ("città", "comune")),)
    categories = (Category("clienti.attivi", ("attivi", "operativi")),)
    entity_names = (("clienti", ("clienti", "anagrafiche")),)
    time_anchor = None


VALID = json.dumps({
    "dsl_version": "1.0", "outcome": "operations", "operations": [
        {"op": "set_target", "ref": "clienti", "provenance": {"text": "i clienti"}},
    ],
})


class TestPrompt(unittest.TestCase):
    def test_the_vocabularies_come_from_the_validator_s_own_source(self):
        """C1 is only real if the prompt and the validator read the same sets: a
        symbol admitted by one and not the other is not expressible."""
        message = system_message(Request(utterance="x", catalogue={}))
        for operation in vocabulary.OPERATIONS:
            self.assertIn(operation, message)
        for view in vocabulary.VIEWS:
            self.assertIn(view, message)

    def test_the_shape_of_an_operation_is_shown_not_implied(self):
        """The measurement that produced this test: without the shape the model
        emitted `type` and `field`, structurally plausible and entirely wrong."""
        message = system_message(Request(utterance="x", catalogue={}))
        self.assertIn('"op":"set_target"', message)
        self.assertIn('Never "field"', message)

    def test_nothing_but_the_utterance_and_the_catalogue_leaves(self):
        """A6 and V7, as a property of the message rather than of a policy."""
        request = Request(utterance="i clienti di Milano",
                          catalogue=catalogue_payload(Catalogue()))
        message = user_message(request)
        self.assertIn("i clienti di Milano", message)
        self.assertIn("clienti.citta", message)
        self.assertNotIn("res.partner", message, "no technical name reaches the model")

    def test_the_state_travels_only_from_the_second_turn(self):
        empty = user_message(Request(utterance="x", catalogue={}))
        self.assertNotIn("Current state", empty)
        with_state = user_message(Request(
            utterance="x", catalogue={},
            state={"target": {"ref": "clienti", "origin": "user"}}))
        self.assertIn("Current state", with_state)

    def test_the_catalogue_payload_carries_no_construction_detail(self):
        """§6.3 — the engine receives the catalogue, it does not know how it was made."""
        payload = catalogue_payload(Catalogue())
        self.assertEqual(set(payload), {"entity", "attributes", "categories", "entities", "time_anchor"})


class TestTimeAnchorInThePrompt(unittest.TestCase):
    """Il modello deve sapere dove si attacca un periodo (D110) e che non puo'
    lasciarlo cadere (D111)."""

    def test_the_payload_carries_the_anchor(self):
        catalogo = Catalogue()
        catalogo.time_anchor = {"ref": "clienti.creato_il"}
        self.assertEqual(catalogue_payload(catalogo)["time_anchor"],
                         {"ref": "clienti.creato_il"})

    def test_an_absent_anchor_travels_as_null_not_as_a_missing_key(self):
        """Una chiave assente e una chiave nulla sono due cose diverse per chi
        legge: la prima si puo' scambiare per una versione vecchia del catalogo,
        la seconda dice esplicitamente che date non ce ne sono."""
        payload = catalogue_payload(Catalogue())
        self.assertIn("time_anchor", payload)
        self.assertIsNone(payload["time_anchor"])

    def test_the_instructions_say_where_a_period_attaches(self):
        """Non basta che la parola compaia: la regola deve ancora **dire** cosa
        fare quando l'ancora non e' unica, che e' il caso per cui D110 esiste.

        **D135 ha cambiato la risposta, non la domanda.** Prima il modello doveva
        scrivere lui il chiarimento, e sulle due entita' che ne hanno bisogno —
        `crm.lead` e `sale.order` — l'esito misurato il 3 agosto 2026 e' stato
        `not_understood` tre volte su tre. Adesso colloca la condizione e la domanda
        la facciamo noi dall'ancora, quindi la riga deve dire **di non scriverla**:
        un modello lasciato libero di farlo comunque rimetterebbe in circolo le
        opzioni rotte che D128 ha dovuto imparare a rifiutare.

        Il confronto e' su una forma a spazi normalizzati perche' mandare a capo
        una riga del prompt non ne cambia il senso, e un test che si rompesse per
        quello verrebbe aggiornato senza leggerlo.
        """
        message = " ".join(
            system_message(Request(utterance="x", catalogue={})).split())
        self.assertIn("time_anchor", message)
        self.assertIn('If it declares "choices", put the condition on the choice the '
                      "sentence names", message)
        self.assertIn("Do NOT write that question yourself.", message)

    def test_the_instructions_forbid_dropping_a_period(self):
        """La regola che conta: oggi lasciar cadere un pezzo di frase non costa
        niente al modello, perche' la busta resta valida lo stesso."""
        message = system_message(Request(utterance="x", catalogue={}))
        self.assertIn("NEVER drop a time expression", message)


class TestInterpreter(unittest.TestCase):
    def test_a_valid_envelope_passes_through(self):
        outcome = interpret(RecordedAdapter([VALID]), utterance="i clienti",
                            catalogue=Catalogue())
        self.assertTrue(outcome.understood)
        self.assertEqual(outcome.outcome, "operations")
        self.assertEqual(outcome.repairs, 0)

    def test_a_markdown_fence_is_tolerated_and_prose_is_not(self):
        fenced = interpret(RecordedAdapter([f"```json\n{VALID}\n```"]),
                           utterance="x", catalogue=Catalogue())
        self.assertTrue(fenced.understood)
        chatty = interpret(RecordedAdapter([f"Certo! Ecco:\n{VALID}", VALID]),
                           utterance="x", catalogue=Catalogue())
        self.assertEqual(chatty.repairs, 1, "prose is a refusal, then one repair")

    def test_exactly_one_repair(self):
        """D15 — a second attempt masks a systematic defect and takes it out of the
        metrics."""
        adapter = RecordedAdapter(["not json", "still not json", VALID])
        outcome = interpret(adapter, utterance="x", catalogue=Catalogue())
        self.assertEqual(outcome.repairs, 1)
        self.assertEqual(len(adapter.requests), 2, "two calls, never three")
        self.assertEqual(outcome.outcome, "not_understood")

    def test_the_repair_carries_the_error_in_structured_form(self):
        adapter = RecordedAdapter(["{}", VALID])
        interpret(adapter, utterance="x", catalogue=Catalogue())
        repair = adapter.requests[1].repair
        self.assertIsNotNone(repair)
        self.assertIn("level", repair)
        self.assertTrue(repair["failures"])

    def test_a_repaired_answer_is_accepted(self):
        outcome = interpret(RecordedAdapter(["{}", VALID]), utterance="x",
                            catalogue=Catalogue())
        self.assertTrue(outcome.understood)
        self.assertEqual(outcome.repairs, 1)

    def test_an_invented_symbol_never_becomes_a_state(self):
        """V8 — nothing leaves the Interpreter that is not a validated envelope."""
        invented = json.dumps({"dsl_version": "1.0", "outcome": "operations",
                               "operations": [{"op": "set_raw_domain", "ref": "x"}]})
        outcome = interpret(RecordedAdapter([invented, invented]), utterance="x",
                            catalogue=Catalogue())
        self.assertEqual(outcome.outcome, "not_understood")

    def test_an_unavailable_provider_is_a_declared_failure_mode(self):
        """§11 — saved queries and editing the interpretation stay available, which
        is why an exception must not escape here."""
        class Down(RecordedAdapter):
            def complete(self, request, *, schema=None):
                from ..adapters.base import AdapterError
                raise AdapterError("connection refused")

        outcome = interpret(Down([]), utterance="x", catalogue=Catalogue())
        self.assertIsNone(outcome.envelope)
        self.assertIn("provider unavailable", outcome.failures[0])

    def test_no_repair_when_none_is_allowed(self):
        outcome = interpret(RecordedAdapter(["{}"]), utterance="x",
                            catalogue=Catalogue(), max_repairs=0)
        self.assertEqual(outcome.repairs, 0)
        self.assertEqual(outcome.outcome, "not_understood")


class SpiaDelloSchema(RecordedAdapter):
    """Registra gli schemi ricevuti: il restringimento di D112 e' invisibile nella
    risposta e visibile solo nell'alfabeto che il modello ha ricevuto."""

    def __init__(self, replies, **kwargs):
        super().__init__(replies, **kwargs)
        self.schemas = []

    def complete(self, request, *, schema=None):
        self.schemas.append(schema)
        return super().complete(request, schema=schema)


class TestCategoryNarrowing(unittest.TestCase):
    """Una categoria che la frase non nomina non deve essere scrivibile (D112).

    D112 e' la decisione per cui le categorie ammesse dalla generazione vincolata
    sono quelle nominate dalla frase, non tutte quelle del catalogo.
    """

    def _refs_ammessi(self, schema) -> str:
        """Grossolano per disegno: basta serializzare lo schema e cercarci il
        riferimento per sapere se e' citabile, senza navigare la sua struttura."""
        return json.dumps(schema)

    def test_a_category_the_sentence_does_not_name_disappears(self):
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: False)
        self.assertNotIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_a_category_the_sentence_names_stays(self):
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti attivi",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: ref == "clienti.attivi")
        self.assertIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_without_a_recognizer_nothing_is_narrowed(self):
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti", catalogue=Catalogue())
        self.assertIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_attributes_are_never_narrowed(self):
        """Un attributo si nomina da se' nella frase — *«con importo oltre
        500»* — non dal riconoscitore delle categorie; restringerlo toglierebbe
        colonne e raggruppamenti che nella frase compaiono altrove."""
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: False)
        self.assertIn("clienti.citta", self._refs_ammessi(spia.schemas[0]))


class TestAllowedHosts(unittest.TestCase):
    """D77 — the list lives in the environment, and nothing in the panel widens it."""

    def setUp(self):
        self._saved = os.environ.get(http_module.ALLOWED_HOSTS_VARIABLE)
        self.addCleanup(self._restore)

    def _restore(self):
        if self._saved is None:
            os.environ.pop(http_module.ALLOWED_HOSTS_VARIABLE, None)
        else:
            os.environ[http_module.ALLOWED_HOSTS_VARIABLE] = self._saved

    def test_an_empty_list_admits_nothing(self):
        """Fail closed. An installation that forgot to set it reaches nobody, which
        is the safe direction: the alternative is reaching everybody."""
        os.environ[http_module.ALLOWED_HOSTS_VARIABLE] = ""
        with self.assertRaises(HostNotAllowed):
            http_module.check_endpoint("https://api.example.com/v1")

    def test_only_the_listed_hosts(self):
        os.environ[http_module.ALLOWED_HOSTS_VARIABLE] = "localhost:11434"
        self.assertEqual(
            http_module.check_endpoint("http://localhost:11434/v1"), "localhost:11434")
        with self.assertRaises(HostNotAllowed):
            http_module.check_endpoint("https://api.example.com/v1")

    def test_the_scheme_is_checked_too(self):
        os.environ[http_module.ALLOWED_HOSTS_VARIABLE] = "localhost:11434"
        with self.assertRaises(HostNotAllowed):
            http_module.check_endpoint("file:///etc/passwd")

    def test_a_compromised_panel_cannot_widen_the_list(self):
        """The argument of D77, as an assertion: a redirected endpoint would send
        every utterance and catalogue elsewhere **with normal accuracy and normal
        latency**, and no metric in `07` would notice."""
        os.environ[http_module.ALLOWED_HOSTS_VARIABLE] = "localhost:11434"
        for hostile in ("https://evil.example.com/v1",
                        "http://localhost:11434.evil.com/v1",
                        "http://127.0.0.1:11434/v1"):
            with self.subTest(endpoint=hostile):
                with self.assertRaises(HostNotAllowed):
                    http_module.check_endpoint(hostile)


class TestSecrets(unittest.TestCase):
    """D76 — a database dump must not yield credentials."""

    def test_the_value_comes_from_the_environment(self):
        os.environ["NLI_TEST_SECRET"] = "sk-not-a-real-key"
        self.addCleanup(os.environ.pop, "NLI_TEST_SECRET", None)
        self.assertEqual(
            http_module.secret_from_environment("NLI_TEST_SECRET"), "sk-not-a-real-key")

    def test_a_missing_variable_is_refused_not_defaulted(self):
        with self.assertRaises(SecretUnavailable):
            http_module.secret_from_environment("NLI_ABSENT_SECRET")

    def test_no_variable_is_a_legitimate_configuration(self):
        """A local model needs no credential, and requiring one would make the safest
        configuration the most awkward."""
        self.assertIsNone(http_module.secret_from_environment(None))


if __name__ == "__main__":
    unittest.main()


class TestAPeriodIsNotAForecast(unittest.TestCase):
    """La via d'uscita non deve inghiottire i periodi (**D114**).

    Misurato il 2 agosto su 414 aperture: undici casi finivano in `out_of_scope`, e
    nove di quelli portavano `scope_note: "previsione"`. Fra questi *«ordini lo scorso
    mese»*, che e' un filtro su una data passata. L'elenco delle cose fuori portata
    nominava *«una previsione»* e *«un calcolo nel tempo»*, e un'espressione temporale
    ci finiva dentro per somiglianza.

    Il confronto e' su forma a spazi normalizzati: mandare a capo una riga del prompt
    non ne cambia il senso, e un test che si rompesse per quello verrebbe aggiornato
    senza leggerlo.
    """

    def test_the_instructions_say_a_period_is_not_out_of_scope(self):
        message = " ".join(
            system_message(Request(utterance="x", catalogue={})).split())
        self.assertIn(
            'A period that selects records that already exist is NOT one of those: '
            '"orders last month" is a condition on a date, and it belongs in the '
            'answer.', message)

    def test_the_instructions_still_declare_what_is_out_of_scope(self):
        """L'altra meta': una regola che non esclude piu' niente non e' una regola.
        La previsione, la scrittura e il calcolo nel tempo restano fuori portata."""
        message = " ".join(
            system_message(Request(utterance="x", catalogue={})).split())
        self.assertIn("a forecast of what will happen, a write, a computation ACROSS "
                      "time such as a trend or a growth rate", message)


class TestIlContestoDellaConversazione(unittest.TestCase):
    """La frase che risponde a una domanda non riparte da zero (**D120**).

    Segnalato dal campo: ad «anno corrente (2024)», detto subito dopo che AIDA aveva
    chiesto quale periodo si intendesse per «i lead di quest'anno», il sistema
    ripartiva da capo e richiedeva la stessa cosa. Una richiesta di chiarimento non
    produce operazioni, quindi non scrive stato — e il contesto spariva esattamente nel
    punto in cui serviva di piu'.
    """

    def test_the_previous_exchange_reaches_the_model(self):
        message = user_message(Request(
            utterance="anno corrente", catalogue={},
            pending=("mostrami i lead di quest'anno", "Quale periodo intendi?")))
        self.assertIn("mostrami i lead di quest'anno", message)
        self.assertIn("Quale periodo intendi?", message)
        self.assertIn("ANSWERS it", message)

    def test_without_a_pending_question_nothing_is_added(self):
        """L'altra meta': un contesto che si aggiunge sempre gonfierebbe ogni prompt
        con una conversazione che non c'e'."""
        message = user_message(Request(utterance="mostrami i lead", catalogue={}))
        self.assertNotIn("ANSWERS it", message)
