"""Part 6 on a database: acceptance, the queue, the cycle, and the chain.

What is asserted here is what cannot be asserted in the pure zone — that the
identity travels, that the utterance never lands in clear, that a lane cannot claim
the other's rows, and that a turn nobody executed becomes a message rather than a
spinner.

The thread pool is deliberately **not** exercised through real threads: a worker on
its own cursor cannot see rows a test transaction has not committed, so a test that
started threads would either commit into the developer's database or prove nothing.
The dispatcher's cycle is therefore run with the worker replaced by an inline call,
and the chain it would have run is tested directly, on the same code path.
"""

import json
import os
from datetime import timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet
from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.nli_core.contract import state as state_module
from odoo.addons.nli_core.contract import vocabulary
from odoo.addons.nli_engine.adapters import synthetic
from odoo.addons.nli_engine.adapters.base import AdapterError
from odoo.addons.nli_engine.adapters.recorded import RecordedAdapter

from .. import secrecy
from ..models.nli_queue_item import (
    DONE, EXPIRED, FAILED, LANE_DEFERRED, LANE_INTERACTIVE, PENDING, RUNNING,
    SUPERSEDED, QueueRefusal,
)
from ..queue import limits as limits_module
from ..runtime import claim as claim_module
from ..runtime import pipeline as pipeline_module
from ..runtime import progress as progress_module
from ..runtime import worker as worker_module

UTTERANCE = "mostrami le aziende di Cittaprova"


def set_key(value):
    """Set or clear the vault key in the environment, without `patch.dict`."""
    if value is None:
        os.environ.pop(secrecy.KEY_VARIABLE, None)
    else:
        os.environ[secrecy.KEY_VARIABLE] = value


def envelope(*operations) -> str:
    return json.dumps({
        "dsl_version": "1.0", "outcome": "operations", "confidence": 0.9,
        "operations": list(operations),
    })


def target(ref: str) -> dict:
    return {"op": "set_target", "ref": ref, "provenance": {"text": "aziende"}}


@tagged("post_install", "-at_install", "nli_dispatch")
class DispatchCase(TransactionCase):
    """Shared setup: a key in the environment and a user who is not the cron."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # `patch.dict` cannot be used inside an Odoo test: the framework inspects
        # every active patcher for a `.target`, and a dict patcher has none.
        cls.key = Fernet.generate_key().decode()
        cls.addClassCleanup(set_key, os.environ.get(secrecy.KEY_VARIABLE))
        set_key(cls.key)

    def setUp(self):
        super().setUp()
        self.user = new_test_user(self.env, login="aida_user", groups="base.group_user")
        self.user_env = self.env(user=self.user)
        self.interrogation = self.user_env["nli.interrogation"].create({})

    def no_commit(self, states=None):
        """Neutralise the dispatcher's checkpoint, recording what it confirmed.

        Odoo's test cursor refuses to commit. Patching the seam is not skipping the
        assertion: `states` records the state of the claimed rows at the moment the
        reservation is made, which is exactly what the commit exists to guarantee.
        """
        dispatcher = type(self.env["nli.dispatcher"])

        def checkpoint(instance):
            if states is not None:
                # Solo le righe di questo test: la banca dati di prova puo'
                # portare code lasciate da una prova di carico, e un'asserzione
                # che le contasse fallirebbe per una ragione che non riguarda il
                # dispatcher.
                states.extend(self.env["nli.queue.item"].search(
                    [("user_id", "=", self.user.id)]).mapped("state"))

        return patch.object(dispatcher, "_checkpoint", checkpoint)

    def accept(self, utterance=UTTERANCE, *, lane=LANE_INTERACTIVE, env=None):
        env = env or self.user_env
        return env["nli.queue.item"].accept(
            self.interrogation, utterance, lane=lane)


class TestAcceptance(DispatchCase):
    """Level 1 of §3.2: three operations, and the worker is released."""

    def test_a_request_becomes_a_pending_row_and_a_turn(self):
        item = self.accept()
        self.assertEqual(item.state, PENDING)
        self.assertEqual(item.lane, LANE_INTERACTIVE)
        self.assertEqual(item.user_id, self.user)
        self.assertTrue(item.turn_id)

    def test_the_turn_carries_the_company_context(self):
        """D40: on a cron process there is no request to inherit it from."""
        item = self.accept()
        self.assertEqual(item.turn_id.company_ids, self.user_env.companies)
        context = item.turn_id.context_for_execution()
        self.assertEqual(context["allowed_company_ids"], self.user_env.companies.ids)

    def test_the_utterance_is_never_stored_in_clear(self):
        """D96, and the reason part 4 stripped provenance in the first place."""
        item = self.accept()
        self.assertNotIn("Cittaprova", item.utterance_sealed)
        self.assertNotIn(UTTERANCE, item.utterance_sealed)
        self.assertEqual(item.utterance(), UTTERANCE)

    def test_without_a_key_nothing_is_accepted(self):
        """Fail closed, like NLI_ALLOWED_HOSTS under D77."""
        set_key(None)
        self.addCleanup(set_key, self.key)
        with self.assertRaises(Exception) as caught:
            self.accept()
        self.assertIn(secrecy.KEY_VARIABLE, str(caught.exception))

    def test_a_stale_ciphertext_fails_loudly(self):
        """A key rotated under a queued turn must not read as an empty sentence."""
        item = self.accept()
        set_key(Fernet.generate_key().decode())
        self.addCleanup(set_key, self.key)
        with self.assertRaises(secrecy.VaultUnavailable):
            item.utterance()


class TestTheLoadLimits(DispatchCase):
    """D20c on a database — the limits the pure zone decided, actually applied."""

    def queue_rows(self, count, *, lane=LANE_INTERACTIVE, user=None):
        """Pending rows belonging to somebody else, unless told otherwise."""
        user = user or self.env.ref("base.user_admin")
        interrogation = self.env["nli.interrogation"].create({"user_id": user.id})
        turn = self.env["nli.turn"].create({
            "interrogation_id": interrogation.id, "user_id": user.id,
            "company_ids": [(6, 0, self.env.companies.ids)], "lang": "en_US",
        })
        return self.env["nli.queue.item"].create([{
            "turn_id": turn.id, "user_id": user.id, "lane": lane,
            "utterance_sealed": secrecy.seal("x"),
        } for _ in range(count)])

    def test_l1_cancels_the_previous_turn_of_the_session(self):
        first = self.accept()
        second = self.accept("e quelle di Roma")
        self.assertEqual(first.state, SUPERSEDED)
        self.assertEqual(second.state, PENDING)
        self.assertFalse(first.utterance_sealed, "a cancelled turn keeps nothing")

    def test_l3_refuses_when_the_queue_is_deeper_than_three_pools(self):
        limits = limits_module.Limits(pool=2)
        with patch.object(type(self.env["nli.dispatcher"]), "_limits",
                          return_value=limits):
            self.queue_rows(6)
            with self.assertRaises(QueueRefusal) as caught:
                self.accept()
            self.assertEqual(caught.exception.reason, limits_module.QUEUE_DEPTH)
            self.assertNotIn("errore", str(caught.exception).lower())

    def test_the_depth_counts_everybody_and_not_only_the_asker(self):
        """The reason the queue is a model of its own: a depth over one's own rows
        would coincide with L1 and the limit would not exist."""
        self.queue_rows(4)
        as_user = self.user_env["nli.queue.item"]
        self.assertEqual(as_user._queued(LANE_INTERACTIVE), 4)

    def test_a_user_cannot_write_another_users_queue_row(self):
        rows = self.queue_rows(1)
        with self.assertRaises(AccessError):
            rows.with_user(self.user).write({"state": EXPIRED})

    def test_l5_refuses_above_twenty_requests_a_minute(self):
        self.queue_rows(20, user=self.user)
        with self.assertRaises(QueueRefusal) as caught:
            self.accept()
        self.assertEqual(caught.exception.reason, limits_module.RATE)

    def test_an_open_circuit_refuses_before_the_queue_fills(self):
        self.env["nli.breaker"]._put(
            self.env["nli.breaker"]._get().after_failure(1.0))
        with patch.object(type(self.env["nli.dispatcher"]), "_breaker_admits",
                          return_value=False):
            with self.assertRaises(QueueRefusal) as caught:
                self.accept()
        self.assertEqual(caught.exception.reason, limits_module.PROVIDER_DOWN)


class TestTheCycle(DispatchCase):
    """Level 2 of §3.3: claiming, expiring, and the separation of the two lanes."""

    def test_the_claim_reserves_and_marks_running(self):
        item = self.accept()
        claimed = claim_module.claim(self.env, lane=LANE_INTERACTIVE, size=8)
        self.assertEqual(claimed, item)
        self.assertEqual(item.state, RUNNING)
        self.assertEqual(item.attempts, 1)
        self.assertTrue(item.started_at)

    def test_the_interactive_lane_never_claims_deferred_work(self):
        """D20d: the corpus recalculation must not be visible to a user typing."""
        deferred = self.accept(lane=LANE_DEFERRED)
        claimed = claim_module.claim(self.env, lane=LANE_INTERACTIVE, size=8)
        self.assertFalse(claimed)
        self.assertEqual(deferred.state, PENDING)
        self.assertEqual(
            claim_module.claim(self.env, lane=LANE_DEFERRED, size=8), deferred)

    def test_a_claim_of_zero_touches_nothing(self):
        self.accept()
        self.assertFalse(claim_module.claim(self.env, lane=LANE_INTERACTIVE, size=0))

    def test_an_expired_turn_is_discarded_and_the_user_is_told(self):
        """L4 — the limit that lets the queue recover instead of accumulating."""
        item = self.accept()
        item.accepted_at = fields.Datetime.subtract(fields.Datetime.now(), seconds=120)
        with patch.object(type(item), "notify") as notified, self.no_commit():
            self.env["nli.dispatcher"]._expire(
                LANE_INTERACTIVE, limits_module.Limits(pool=2))
        self.assertEqual(item.state, EXPIRED)
        self.assertEqual(item.failure_reason, limits_module.EXPIRED)
        self.assertFalse(item.utterance_sealed)
        notified.assert_called_once()

    def test_the_cycle_runs_each_claimed_row_with_the_requesting_identity(self):
        """§3.4 — the dispatcher never runs with its own privileges."""
        item = self.accept()
        seen = {}
        states = []

        def fake_worker(dbname, item_id, uid, context, **kwargs):
            seen.update(item_id=item_id, uid=uid, context=context)
            return None

        with patch("odoo.addons.nli_dispatch.runtime.worker.execute", fake_worker), \
                self.no_commit(states):
            self.env["nli.dispatcher"]._cron_dispatch()

        self.assertEqual(states, [RUNNING],
                         "the reservation is confirmed before the batch runs (§3.4)")

        self.assertEqual(seen["item_id"], item.id)
        self.assertEqual(seen["uid"], self.user.id)
        self.assertNotEqual(seen["uid"], self.env.ref("base.user_root").id,
                            "the cron identity must never reach the chain")
        self.assertEqual(seen["context"]["allowed_company_ids"],
                         item.turn_id.company_ids.ids)


class TestRecovery(DispatchCase):
    """§5.3 — a process that stopped leaves rows, and rows must not stay silent."""

    def orphan(self, attempts):
        item = self.accept()
        item.write({
            "state": RUNNING, "attempts": attempts,
            "started_at": fields.Datetime.now() - timedelta(seconds=3600),
        })
        return item

    def test_a_first_orphan_goes_back_to_the_queue(self):
        item = self.orphan(attempts=1)
        self.env["nli.dispatcher"]._cron_recover()
        self.assertEqual(item.state, PENDING)

    def test_the_second_attempt_fails_the_turn_and_tells_the_user(self):
        """Without the counter a turn that kills the process is retried forever."""
        item = self.orphan(attempts=2)
        with patch.object(type(item), "notify") as notified:
            self.env["nli.dispatcher"]._cron_recover()
        self.assertEqual(item.state, FAILED)
        self.assertEqual(item.failure_reason, "orphaned")
        self.assertFalse(item.utterance_sealed)
        notified.assert_called_once()

    def test_a_row_still_running_is_left_alone(self):
        item = self.accept()
        item.write({"state": RUNNING, "started_at": fields.Datetime.now()})
        self.env["nli.dispatcher"]._cron_recover()
        self.assertEqual(item.state, RUNNING)


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheChain(DispatchCase):
    """The pipeline itself, on a live dictionary, with a recorded provider.

    This is the first time in the project that the whole chain runs on metadata
    introspected from a database rather than on a pack written for the corpus.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create([
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True},
            {"name": "Gamma Srl", "city": "Roma", "is_company": True},
        ])
        self.scope = ("res.partner",)

    def run_pipeline(self, item, replies):
        return pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter(replies), scope=self.scope,
            context_window=32_000)

    def test_a_turn_runs_end_to_end_and_persists_its_state(self):
        item = self.accept("le aziende di Cittaprova")
        outcome = self.run_pipeline(item, [
            # Phase B: which entity? Then phase C: the whole request.
            envelope(target("res_partner")),
            envelope(
                target("res_partner"),
                {"op": "add_condition", "combine": "all",
                 "condition": {"ref": "res_partner.city", "predicate": "equals",
                               "value": {"kind": "text", "text": "Cittaprova"}},
                 "provenance": {"text": "di Cittaprova"}},
            ),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(outcome.state["target"]["ref"], "res_partner")
        self.assertEqual(outcome.record_count, 1)
        self.assertIsNotNone(outcome.interpretation)

    def test_the_types_the_model_is_shown_are_the_contract_s(self):
        """`fields_get` says `char`; §8.1 enumerates predicates over `text`."""
        semantics = self.user_env["nli.semantics"].semantics(self.scope)
        catalogue = self.user_env["nli.semantics"].catalogue_for(
            semantics, "res_partner", context_window=32_000)
        types = {attribute.type for attribute in catalogue.attributes}
        self.assertTrue(types)
        self.assertFalse(types & {"char", "many2one", "monetary", "selection"},
                         "an Odoo type in the catalogue produces predicates level 4 "
                         "then refuses, for a reason no diagnostic names")

    def test_a_reference_outside_the_catalogue_is_refused_not_ignored(self):
        """D14 — ignoring a symbol produces a less filtered result than asked for."""
        item = self.accept("le aziende")
        outcome = self.run_pipeline(item, [
            envelope(target("res_partner")),
            envelope(target("res_partner"),
                     {"op": "add_group", "ref": "res_partner.invented",
                      "provenance": {"text": "x"}}),
        ])
        self.assertEqual(outcome.outcome, "not_understood")
        self.assertTrue(outcome.failures)

    def test_an_unreachable_provider_is_a_declared_failure(self):
        item = self.accept()
        outcome = self.run_pipeline(item, [])
        self.assertTrue(outcome.provider_failed)
        self.assertFalse(outcome.executed)

    def test_a_clarification_is_not_a_failure(self):
        item = self.accept("mostrami tutto")
        outcome = self.run_pipeline(item, [
            json.dumps({"dsl_version": "1.0", "outcome": "clarification",
                        "clarification": {"question": "Che cosa?", "options": [
                            {"label": "Aziende", "operations": [target("res_partner")]},
                            {"label": "Persone", "operations": [target("res_partner")]},
                        ]}}),
        ])
        self.assertEqual(outcome.outcome, "clarification")
        self.assertIn("clarification", outcome.interpretation)

    def test_the_dictionary_is_reused_between_users_with_the_same_rights(self):
        """D39: the key is the permission fingerprint, never the user."""
        other = new_test_user(self.env, login="aida_other", groups="base.group_user")
        first = self.user_env["nli.semantics"].semantics(self.scope)
        second = self.env(user=other)["nli.semantics"].semantics(self.scope)
        self.assertIs(first, second)

    def test_the_utterance_is_erased_when_the_turn_completes(self):
        item = self.accept("le aziende di Cittaprova")
        outcome = self.run_pipeline(item, [
            envelope(target("res_partner")),
            envelope(target("res_partner")),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        item.complete()
        self.assertEqual(item.state, DONE)
        self.assertFalse(item.utterance_sealed)

    def test_the_pipeline_hands_the_matcher_to_the_interpreter(self):
        """D112 (categories admitted narrowed to what the sentence names) vive nella
        costruzione dello schema, quindi non si vede nella risposta: senza questo
        passaggio il restringimento sarebbe codice che non gira mai, e nessun altro
        test se ne accorgerebbe."""
        item = self.accept("le aziende di Cittaprova")
        visti = {}
        originale = pipeline_module.interpreter_module.interpret

        def spia(adapter, **kwargs):
            visti.update(kwargs)
            return originale(adapter, **kwargs)

        with patch.object(pipeline_module.interpreter_module, "interpret", spia):
            self.run_pipeline(item, [envelope(target("res_partner"))])

        self.assertIn("mentions", visti,
                      "senza il riconoscitore il restringimento di D112 non si "
                      "applica, e la categoria infondata torna scrivibile")
        self.assertTrue(callable(visti["mentions"]),
                        "dev'essere una funzione e non un dizionario: nli_engine "
                        "non puo' importare nli_semantics (04 §6.3, il confine fra "
                        "il motore e la semantica)")


@tagged("post_install", "-at_install", "nli_dispatch")
class TestASuccessfulTurnCanBeDrawn(DispatchCase):
    """D124 — un turno riuscito deve produrre qualcosa che la chat sappia disegnare.

    **Il buco che questa classe chiude.** Nessuna prova arrivava fin qui: si fermavano
    tutte all'esito. Cosi' il Presentatore produceva la struttura, il template cercava
    le parole, e **nessuna risposta riuscita e' mai comparsa** — finiva nel ramo di
    scarto, che diceva «non ho capito» a un turno andato a buon fine. E' lo stesso buco
    che aveva lasciato passare `dsl_version`: l'esito e' verde molto prima che lo sia
    quello che l'utente vede.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            [{"name": "Alfa SpA", "city": "Cittaprova", "is_company": True}])
        self.scope = ("res.partner",)

    def _eseguito(self):
        item = self.accept("le aziende di Cittaprova")
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([
                envelope(target("res_partner")),
                envelope(
                    target("res_partner"),
                    {"op": "add_condition", "combine": "all",
                     "condition": {"ref": "res_partner.city", "predicate": "equals",
                                   "value": {"kind": "text", "text": "Cittaprova"}},
                     "provenance": {"text": "di Cittaprova"}},
                ),
            ]),
            scope=self.scope, context_window=32_000)
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return item.turn_id.with_env(self.user_env)

    def test_the_payload_carries_words_and_not_a_structure(self):
        """Il template cerca `parts`. Senza, la risposta cade nel ramo di scarto."""
        payload = self._eseguito()._aida_payload()
        interpretazione = payload["interpretation"]
        self.assertIn("lead", interpretazione)
        self.assertTrue(interpretazione.get("parts"),
                        "il Presentatore produce una struttura: qualcuno deve "
                        "trasformarla in frasi (09 §3), o non si disegna niente")

    def test_every_part_still_declares_its_origin(self):
        """§10.2 e D65 vivono nelle parti: se si perdono qui, si perde la salienza."""
        parts = self._eseguito()._aida_payload()["interpretation"]["parts"]
        for part in parts:
            self.assertIn(part["origin"], ("user", "inferred", "default"))

    def test_the_payload_carries_the_query_for_the_table(self):
        """`00` §23: la tabella e' la vista lista di Odoo, e le serve il dominio."""
        query = self._eseguito()._aida_payload()["query"]
        self.assertEqual(query["model"], "res.partner")
        self.assertTrue(query["domain"])
        json.dumps(query)

    def test_a_turn_that_did_not_execute_carries_no_query(self):
        """Una chiave `query` vuota farebbe disegnare una tabella di niente."""
        item = self.accept("mostrami qualcosa")
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([json.dumps({
                "dsl_version": "1.0", "outcome": "out_of_scope",
                "scope_note": "prediction",
                "scope_provenance": {"text": "mostrami qualcosa"}})]),
            scope=self.scope, context_window=32_000)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        self.assertNotIn("query", item.turn_id.with_env(self.user_env)._aida_payload())

    def test_a_clarification_payload_is_left_alone(self):
        """Un chiarimento porta gia' la forma che il client legge: passarlo per le
        parole lo trasformerebbe in una risposta che non e'."""
        turno = self.user_env["nli.turn"].create({
            "interrogation_id": self.interrogation.id,
            "user_id": self.user.id,
            "company_ids": [(6, 0, self.user_env.companies.ids)],
            "utterance": "boh",
            "outcome": "clarification",
            "interpretation_json": json.dumps(
                {"outcome": "clarification",
                 "clarification": {"question": "quale?", "options": []}}),
        })
        interpretazione = turno._aida_payload()["interpretation"]
        self.assertEqual(interpretazione["clarification"]["question"], "quale?")


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheDebugTrace(DispatchCase):
    """D123 — la modalita' diagnostica: il DSL e la query, sul turno.

    Il punto della traccia e' rispondere alla sola domanda che conta quando un turno va
    storto: **e' andato storto nel modello o dopo?** Quindi deve portare la busta come
    il modello l'ha restituita **e** il piano con cui Odoo e' stato interrogato, che
    sono i due lati di quella domanda.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            [{"name": "Alfa SpA", "city": "Cittaprova", "is_company": True}])
        self.scope = ("res.partner",)

    def _turno(self, *, debug, context_window=32_000):
        item = self.accept("le aziende di Cittaprova")
        return pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([
                envelope(target("res_partner")),
                envelope(
                    target("res_partner"),
                    {"op": "add_condition", "combine": "all",
                     "condition": {"ref": "res_partner.city", "predicate": "equals",
                                   "value": {"kind": "text", "text": "Cittaprova"}},
                     "provenance": {"text": "di Cittaprova"}},
                ),
            ]),
            scope=self.scope, context_window=context_window, debug=debug), item

    def test_without_the_switch_nothing_is_collected(self):
        """Spenta non costa niente e non conserva niente: e' cio' che le permette di
        portare la busta per intero quando e' accesa."""
        outcome, _item = self._turno(debug=False)
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertIsNone(outcome.debug)

    def test_the_trace_carries_the_envelope_the_model_returned(self):
        outcome, _item = self._turno(debug=True)
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        busta = outcome.debug["interpret"]["envelope"]
        self.assertEqual(busta["outcome"], "operations")
        self.assertTrue(busta["operations"])

    def test_the_trace_carries_the_query_odoo_was_asked(self):
        """Non una descrizione della query: gli argomenti stessi."""
        outcome, _item = self._turno(debug=True)
        piano = outcome.debug["plan"]
        self.assertEqual(piano["model"], "res.partner")
        self.assertTrue(piano["domain"])
        self.assertIn("limit", piano)
        # Il dominio dev'essere scrivibile in JSON, o non arriva al client.
        json.dumps(piano)

    def test_the_trace_carries_the_phases_and_their_cost(self):
        outcome, _item = self._turno(debug=True)
        for fase in ("phase_a", "phase_b", "phase_c", "interpret", "execute"):
            self.assertIn(fase, outcome.debug, fase)
        self.assertIsInstance(outcome.debug["interpret"]["seconds"], float)

    def test_the_trace_says_how_much_catalogue_the_budget_threw_away(self):
        """D79 conta i rifiuti per budget da sempre, e non li leggeva nessuno.

        Misurato il 3 agosto 2026: con la finestra di 4096 che il profilo in servizio
        dichiara, il budget vale **17** attributi contro il tetto di 60 di D31. Decine
        di attributi non arrivano al modello, e con loro se ne va la proprieta' con cui
        **D32** chiude **RC3** — *«in fase C non c'e' selezione, la copertura sugli
        attributi e' esatta per costruzione»*. Nessuna tabella diagnostica lo diceva:
        e' il guasto che D79 e' nata per rendere visibile, rimasto invisibile.

        **La finestra e' stretta di proposito, e la ragione vale piu' della prova.**

        La prima versione di questo test girava con la finestra larga di tutti gli
        altri, dove il budget non rifiuta niente: il contatore valeva **zero**, e zero
        e' il solo valore su cui il difetto che avevo appena introdotto non scattava —
        avevo scritto `len()` intorno a un numero, e `0 or ()` diventa una tupla vuota
        mentre `40 or ()` resta `40`. La prova passava verde e ogni turno vero moriva
        con un `TypeError` prima di arrivare al modello.

        E' la stessa forma di §38 un giro piu' stretto: non codice scollegato, ma una
        **prova che esercita il caso in cui il difetto non si vede**. Un contatore si
        prova dove conta qualcosa.
        """
        outcome, _item = self._turno(debug=True, context_window=4096)
        fase = outcome.debug["phase_c"]
        self.assertGreater(fase["refused_for_budget"], 0,
                           "con 4096 gettoni il budget deve scartare attributi")
        self.assertEqual(fase["budget"]["attributes"], 17)
        self.assertEqual(fase["budget"]["reason"], "window")

    def test_the_trace_compares_what_was_read_with_what_was_declared(self):
        """Due numeri diversi che nessuno metteva vicini.

        `context_window` e' cio' che il **profilo dichiara**; `prompt_tokens` e' cio'
        che il **server dice di aver letto**. L'adattatore non manda la finestra al
        fornitore — il protocollo OpenAI non ha un campo per dirla — quindi le due
        possono divergere, e quando divergono il server taglia il prompt in silenzio:
        HTTP 200, nessun errore, una risposta costruita su meta' catalogo. Misurato su
        `ollama` con la finestra a 4096: dodicimila gettoni mandati, 2050 letti.
        """
        outcome, _item = self._turno(debug=True)
        interpretazione = outcome.debug["interpret"]
        self.assertIn("prompt_tokens", interpretazione)
        self.assertEqual(interpretazione["context_window"], 32_000)

    def test_it_is_written_on_the_turn_only_when_collected(self):
        outcome, item = self._turno(debug=True)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        self.assertTrue(item.turn_id.debug_json)

        outcome2, item2 = self._turno(debug=False)
        worker_module._persist(self.user_env, item2.with_env(self.user_env), outcome2)
        self.assertFalse(item2.turn_id.debug_json)

    def test_a_chosen_reading_says_it_took_the_short_path(self):
        """Un turno istantaneo senza spiegazione sembra un turno saltato."""
        item = self.accept("qualunque cosa")
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([envelope(target("res_partner"))]),
            scope=self.scope, context_window=32_000, debug=True)
        self.assertEqual(outcome.debug["path"], "model")


class PassiRegistrati:
    """Un reporter che raccoglie invece di scrivere sul bus.

    Il vero `Reporter` apre un cursore per evento, e quel cursore e' provato altrove
    (`pure_tests/test_progress.py`). Qui interessa una cosa diversa e che solo un
    turno vero puo' dire: **quali passi il pipeline emette, e in quale ordine.**
    """

    def __init__(self):
        self.passi = []

    def __call__(self, step, *, detail=None, force=False):
        self.passi.append((step, detail or ""))

    @property
    def chiavi(self):
        return [chiave for chiave, _ in self.passi]


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheProgressSteps(DispatchCase):
    """Che cosa sta facendo il turno, detto mentre lo fa.

    L'avanzamento non cambia una virgola di cio' che un turno produce — e' proprio
    per questo che si puo' spegnere senza cautele — ma **e' l'unica cosa che sta
    sullo schermo** durante i secondi in cui il modello pensa: mediana 8,8 s, p95
    16,3 s sulle 414 chiamate misurate. Un passo che sparisce non rompe nessuna
    risposta, quindi non c'e' nessun altro test che se ne accorga: o e' asserito qui
    o non e' asserito da nessuna parte.

    **Le parole non si provano qui.** Il server manda chiavi, il client le traduce;
    provare le chiavi e' provare il contratto, provare le parole sarebbe provare la
    lingua dell'interfaccia dentro il dispatcher.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            [{"name": "Alfa SpA", "city": "Cittaprova", "is_company": True}])
        self.scope = ("res.partner",)

    def _turno(self, frase="le aziende di Cittaprova"):
        passi = PassiRegistrati()
        item = self.accept(frase)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([
                envelope(target("res_partner")),
                envelope(
                    target("res_partner"),
                    {"op": "add_condition", "combine": "all",
                     "condition": {"ref": "res_partner.city", "predicate": "equals",
                                   "value": {"kind": "text", "text": "Cittaprova"}},
                     "provenance": {"text": "di Cittaprova"}},
                ),
            ]),
            scope=self.scope, context_window=32_000, reporter=passi)
        return outcome, passi

    def test_senza_reporter_il_turno_gira_uguale(self):
        """L'interruttore a `None` e' la stessa forma della traccia diagnostica: il
        turno non deve accorgersi di non essere guardato."""
        item = self.accept("le aziende di Cittaprova")
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([
                envelope(target("res_partner")),
                envelope(target("res_partner")),
            ]),
            scope=self.scope, context_window=32_000)
        self.assertIn(outcome.outcome, ("operations", "not_understood"))

    def test_il_primo_passo_e_il_dizionario(self):
        """E' quello che toglie dallo schermo l'attesa muta, quindi viene per primo."""
        _outcome, passi = self._turno()
        self.assertEqual(passi.chiavi[0], "dictionary")

    def test_i_passi_coprono_il_turno_dal_dizionario_all_esecuzione(self):
        outcome, passi = self._turno()
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        for atteso in ("dictionary", "catalogue", "interpret", "validate", "execute"):
            self.assertIn(atteso, passi.chiavi, passi.chiavi)

    def test_i_passi_arrivano_nell_ordine_in_cui_il_turno_li_percorre(self):
        """Un elenco fuori ordine racconta un lavoro che non e' stato fatto cosi'."""
        _outcome, passi = self._turno()
        posizioni = [passi.chiavi.index(chiave)
                     for chiave in ("dictionary", "catalogue", "interpret",
                                    "validate", "execute")]
        self.assertEqual(posizioni, sorted(posizioni), passi.chiavi)

    def test_ogni_passo_emesso_e_dichiarato_nel_contratto(self):
        """Una chiave che il client non conosce e' una riga vuota sullo schermo, e
        nessuna risposta sbagliata da nessuna parte che lo faccia notare."""
        _outcome, passi = self._turno()
        for chiave in passi.chiavi:
            self.assertIn(chiave, progress_module.PASSI, chiave)

    def test_l_interpretazione_dice_di_che_cosa_ha_capito_che_si_parla(self):
        """Il passo lungo porta il nome di casa dell'entita', non il riferimento.

        E' l'unico momento in cui il sistema puo' dire *«sto cercando fra i
        contatti»* mentre lo sta ancora facendo — dopo, la risposta parla da se'.
        """
        _outcome, passi = self._turno()
        dettaglio = dict(passi.passi)["interpret"]
        self.assertTrue(dettaglio)
        self.assertNotIn("res_partner", dettaglio)

    def test_nessun_passo_porta_la_frase_dell_utente(self):
        """D60 letto come principio: il payload minimo che funziona e' quello che non
        puo' diventare un archivio di cio' che la gente ha scritto."""
        _outcome, passi = self._turno("le aziende di Cittaprova")
        for chiave, dettaglio in passi.passi:
            self.assertNotIn("Cittaprova", dettaglio, chiave)


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheProviderThatDoesNotAnswer(DispatchCase):
    """`04` §11 — un fornitore che non risponde e' un modo di fallire dichiarato.

    Misurato sul campo il 2 agosto: il modello impiegava 60,1 s, l'adattatore ne
    concedeva 60, e ogni turno arrivava all'utente come *«non ho capito la domanda,
    puoi riformularla?»*. Riformulare non serviva a niente: la frase era giusta e non
    l'aveva letta nessuno. `worker.execute` diceva gia' `unavailable` quando a mancare
    era il **profilo**; il percorso che si percorre sempre — la chiamata che scade —
    diceva l'altra cosa.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            [{"name": "Alfa SpA", "city": "Cittaprova", "is_company": True}])
        self.scope = ("res.partner",)

    def _muto(self, utterance="le aziende di Cittaprova"):
        item = self.accept(utterance)
        return pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([]),   # la registrazione e' esaurita: il fornitore tace
            scope=self.scope, context_window=32_000)

    def test_a_silent_provider_is_not_a_sentence_nobody_understood(self):
        outcome = self._muto()
        self.assertEqual(
            outcome.outcome, "unavailable",
            "«non ho capito» invita a riformulare, e riformulare non serve a niente "
            "quando il modello non ha risposto")
        self.assertTrue(outcome.provider_failed)

    def test_it_still_reaches_the_breaker(self):
        """L'esito cambia nome, non smette di essere il guasto che apre il circuito."""
        outcome = self._muto()
        self.assertTrue(outcome.provider_failed)
        self.assertTrue(outcome.failures)

    def test_the_queue_row_records_it_as_a_provider_failure(self):
        item = self.accept()
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([]), scope=self.scope, context_window=32_000)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        self.assertEqual(item.state, FAILED)
        self.assertEqual(item.turn_id.outcome, "unavailable")


@tagged("post_install", "-at_install", "nli_dispatch")
class TestChoosingAReading(DispatchCase):
    """D121 — chi sceglie una lettura non ripassa dal modello.

    Le operazioni di ogni opzione sono gia' nella busta: e' cio' che D106 ci ha messo.
    Una risposta che ne sceglie una non ha niente da interpretare, e interpretarla
    costerebbe un minuto di modello per riscoprire una lista che abbiamo scritto noi —
    e potrebbe riscoprirla diversa, che e' il difetto che questa strada chiude.

    Il turno di chiarimento viene **davvero eseguito e scritto**, non simulato: e' il
    solo modo di provare che le opzioni sopravvivono alla persistenza, che e' il punto
    in cui la strada del clic si sarebbe rotta in silenzio.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create([
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True, "vat": False},
        ])
        # Due condizioni nominate, perche' una sola non fa una domanda: l'opzione
        # «senza quel filtro» c'e' sempre, ma la seconda dev'essere un'altra categoria
        # dello stesso catalogo (D106 le prende da li', mai dal modello).
        self.env["nli.dictionary.entry"].create([
            {"entry_type": "T5", "level": "L2", "entity_ref": "res_partner",
             "ref": "res_partner.senza_partita_iva",
             "terms": "senza partita iva",
             "condition": '{"kind": "is_not_set", "field": "vat"}'},
            {"entry_type": "T5", "level": "L2", "entity_ref": "res_partner",
             "ref": "res_partner.con_partita_iva",
             "terms": "con partita iva",
             "condition": '{"kind": "is_set", "field": "vat"}'},
        ])
        # Il dizionario vive in una cache la cui chiave guarda i permessi, non le voci
        # approvate: senza questo la prova girerebbe sul dizionario di prima.
        self.env.registry.clear_cache()
        self.scope = ("res.partner",)

    def _run(self, item, replies):
        adapter = RecordedAdapter(replies)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env), adapter=adapter,
            scope=self.scope, context_window=32_000)
        return outcome, adapter

    def _ask_and_persist(self, utterance, replies):
        """Un turno intero, scritto come lo scrive il lavoratore."""
        item = self.accept(utterance)
        outcome, adapter = self._run(item, replies)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return outcome, adapter

    def _clarify(self):
        """Il turno che finisce con una domanda, e le sue opzioni."""
        outcome, _adapter = self._ask_and_persist("le aziende quelle strane", [
            envelope(target("res_partner")),
            envelope(
                target("res_partner"),
                {"op": "add_condition", "combine": "all",
                 "condition": {"ref": "res_partner.senza_partita_iva",
                               "predicate": "is_category"},
                 "provenance": {"text": "quelle strane"}},
            ),
        ])
        self.assertEqual(outcome.outcome, "clarification", outcome.failures)
        return outcome.interpretation["clarification"]["options"]

    @staticmethod
    def _condition_refs(outcome):
        """Un filtro con una condizione sola *e'* quella condizione: non c'e' un
        connettivo attorno, e leggerlo per chiave lo darebbe per assente."""
        return [condition.get("ref") for condition
                in state_module.conditions((outcome.state or {}).get("filter"))]

    # --- la lettura scelta si applica ------------------------------------

    def test_answering_with_a_label_executes_without_calling_the_model(self):
        options = self._clarify()
        etichetta = [o["label"] for o in options if o["label"] == "con partita iva"]
        self.assertTrue(etichetta, [o["label"] for o in options])

        item = self.accept("con partita iva")
        outcome, adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(
            adapter.requests, [],
            "la lettura scelta porta gia' le sue operazioni: chiamare il modello "
            "vorrebbe dire riscoprire una lista che abbiamo scritto noi")
        self.assertEqual(self._condition_refs(outcome), ["res_partner.con_partita_iva"])

    def test_the_chosen_condition_is_founded_in_the_answer(self):
        """Senza questo la lettura scelta fallirebbe di nuovo il livello 3, e per la
        ragione giusta: il frammento di prima non nomina *questa* condizione. Adesso il
        frammento e' la risposta, che e' quello che l'utente ha davvero detto."""
        self._clarify()
        item = self.accept("con partita iva")
        outcome, _adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)

    def test_the_option_that_drops_the_filter_leaves_no_condition(self):
        options = self._clarify()
        item = self.accept(options[0]["label"])
        outcome, adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(self._condition_refs(outcome), [])

    def test_case_and_spacing_do_not_have_to_be_reproduced(self):
        """Chi clicca manda l'etichetta esatta; chi la riscrive no, ed e' la stessa
        strada."""
        self._clarify()
        item = self.accept("  Con Partita IVA ")
        outcome, adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(adapter.requests, [])

    # --- e quando non e' una scelta, non lo diventa ----------------------

    def test_a_sentence_that_is_not_an_option_goes_back_to_the_model(self):
        """Con il contesto di D120, non da un foglio bianco: il modello riceve la frase
        di prima e la domanda posta."""
        self._clarify()
        item = self.accept("quelle di Cittaprova")
        outcome, adapter = self._run(item, [
            # Il chiarimento non ha scritto stato — non ha prodotto operazioni — quindi
            # l'entita' e' di nuovo da determinare: fase B, poi fase C.
            envelope(target("res_partner")),
            envelope(
                target("res_partner"),
                {"op": "add_condition", "combine": "all",
                 "condition": {"ref": "res_partner.city", "predicate": "equals",
                               "value": {"kind": "text", "text": "Cittaprova"}},
                 "provenance": {"text": "di Cittaprova"}},
            ),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertTrue(adapter.requests)
        self.assertIsNotNone(adapter.requests[-1].pending,
                             "la frase risponde a una domanda: il modello deve "
                             "riceverla insieme alla domanda (D120)")

    def test_a_turn_the_queue_threw_away_does_not_hide_the_question(self):
        """Visto sul campo il 2 agosto: fra il chiarimento e la risposta c'era un turno
        scaduto in coda, e con lui erano spariti sia D120 sia D121. Un turno che abbiamo
        buttato via non dice che l'utente ha cambiato argomento — dice che la sua frase
        e' andata persa."""
        self._clarify()
        scartato = self.accept("con partita iva")
        scartato.expire()
        self.assertEqual(scartato.turn_id.outcome, "expired",
                         "una riga di coda che finisce senza esecuzione deve chiudere "
                         "anche il turno, o la cronologia resta in attesa per sempre")

        item = self.accept("con partita iva")
        outcome, adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(adapter.requests, [])

    def test_the_state_a_turn_produced_can_actually_be_written(self):
        """Il buco che ha lasciato passare il difetto: nessuna prova persisteva uno
        stato **eseguito**, si fermavano tutte all'esito. Cosi' il primo turno che
        riusciva di ogni conversazione moriva scrivendo, con un errore di validazione
        che parlava di una chiave mancante invece che di una risposta."""
        options = self._clarify()
        item = self.accept(options[0]["label"])
        outcome, _adapter = self._run(item, [])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)

        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        stato = self.interrogation.state
        self.assertEqual(stato["dsl_version"], "1.0")
        self.assertTrue(stato.get("target"))

    def test_a_completed_turn_keeps_the_outcome_the_pipeline_wrote(self):
        """Chiudere la riga di coda non deve sovrascrivere la risposta con il nome
        dello stato della coda che l'ha seguita."""
        options = self._clarify()
        self.assertTrue(options)
        precedente = self.interrogation.turn_ids.sorted("id")[-1]
        self.assertEqual(precedente.outcome, "clarification")

    def test_a_label_from_a_turn_that_is_no_longer_the_last_is_not_an_answer(self):
        """Una domanda a cui l'utente non ha risposto subito non e' piu' in sospeso: ha
        cambiato argomento, e trascinarsela dietro applicherebbe una lettura che
        risponde a una domanda vecchia."""
        self._clarify()
        self._ask_and_persist("le aziende di Cittaprova", [envelope(
            target("res_partner"),
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "res_partner.city", "predicate": "equals",
                           "value": {"kind": "text", "text": "Cittaprova"}},
             "provenance": {"text": "di Cittaprova"}},
        )])
        item = self.accept("con partita iva")
        _outcome, adapter = self._run(item, [envelope(target("res_partner"))])
        self.assertTrue(adapter.requests,
                        "l'etichetta di un turno sorpassato non sceglie piu' niente: "
                        "va interpretata come una frase qualunque")


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheLoadBench(DispatchCase):
    """D97 — il banco di prova esiste solo se qualcuno lo accende, e si vede."""

    def set_bench(self, value):
        if value is None:
            os.environ.pop(synthetic.VARIABLE, None)
        else:
            os.environ[synthetic.VARIABLE] = value
        self.addCleanup(os.environ.pop, synthetic.VARIABLE, None)

    def test_it_is_off_unless_the_variable_is_set(self):
        self.set_bench(None)
        self.assertFalse(synthetic.enabled())
        with self.assertRaises(AdapterError):
            synthetic.SyntheticAdapter.from_environment()

    def test_off_the_dispatcher_asks_the_active_profile(self):
        """Il ramo non deve poter deviare l'esecuzione ordinaria.

        **Lo stato se lo costruisce.** Prima diceva «nessun profilo attivo su questa
        base» e lo dava per buono: verde su una base di prova, rosso sulla base dove
        il prodotto gira davvero, che un profilo attivo ce l'ha per definizione. La
        transazione del test torna indietro, quindi il ritiro non esce di qui.
        """
        self.set_bench(None)
        self.env["nli.profile"].search([("state", "=", "active")]).action_retire()
        factory = self.env["nli.dispatcher"]._adapter_factory()
        with self.assertRaises(Exception):
            # Senza banco e senza profilo, l'errore che arriva e' quello del profilo
            # mancante, non un adattatore sintetico silenzioso.
            factory(self.env)

    def test_on_it_answers_after_the_declared_latency(self):
        self.set_bench("0.05")
        adapter = self.env["nli.dispatcher"]._adapter_factory()(self.env)
        self.assertIsInstance(adapter, synthetic.SyntheticAdapter)
        self.assertEqual(adapter.latency, 0.05)

    def test_the_failure_mode_of_the_bench_is_a_provider_failure(self):
        """La prova §7.2 sul fornitore irraggiungibile ha bisogno di questo."""
        self.set_bench("0:fail")
        adapter = synthetic.SyntheticAdapter.from_environment()
        with self.assertRaises(AdapterError):
            adapter.complete(None)


@tagged("post_install", "-at_install", "nli_dispatch")
class TestANewQuestionRestarts(DispatchCase):
    """D127 — chi nomina la propria entita' fa una domanda nuova.

    **Il caso, portato dall'Architect il 2 agosto 2026.** *«quelli che hanno per mail
    md@...»*, poi *«MOSTRAMI DI NUOVO I LEAD DI quest anno»*: la seconda frase non
    c'entrava niente con la mail, e rispondeva sul residuo della prima. Lo stato si
    accumulava e non c'era modo di ricominciare parlando.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create([
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True},
            {"name": "Beta Srl", "city": "Roma", "is_company": True},
        ])
        self.scope = ("res.partner",)
        # Il nome con cui la fase A riconosce l'entita' senza chiamare il modello.
        # Voce approvata L2 (D108): e' la strada che il progetto ha gia' per dare a
        # un'entita' le parole di casa, e non dipende da quali menu l'utente di prova
        # riesce a vedere.
        self.env["nli.dictionary.entry"].create({
            "entry_type": "T1", "level": "L2", "ref": "res_partner",
            "entity_ref": "res_partner", "terms": "aziende"})
        self.env.registry.clear_cache()

    def _run(self, utterance, replies):
        item = self.accept(utterance)
        adapter = RecordedAdapter(replies)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env), adapter=adapter,
            scope=self.scope, context_window=32_000, debug=True)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return outcome, adapter

    @staticmethod
    def _condizione(ref, testo, valore):
        return {"op": "add_condition", "combine": "all",
                "condition": {"ref": ref, "predicate": "equals",
                              "value": {"kind": "text", "text": valore}},
                "provenance": {"text": testo}}

    def _prima_domanda(self):
        return self._run("mostrami le aziende di Cittaprova", [envelope(
            target("res_partner"),
            self._condizione("res_partner.city", "di Cittaprova", "Cittaprova"))])

    # --- la domanda nuova ---------------------------------------------------

    def test_naming_the_entity_starts_from_scratch(self):
        """Il filtro del turno prima non resta attaccato a una domanda che non lo
        nomina."""
        self._prima_domanda()
        outcome, _adapter = self._run("mostrami le aziende di Roma", [envelope(
            target("res_partner"),
            self._condizione("res_partner.city", "di Roma", "Roma"))])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        citta = [c["value"]["text"]
                 for c in state_module.conditions(outcome.state.get("filter"))]
        self.assertEqual(citta, ["Roma"], "Cittaprova non doveva sopravvivere")

    def test_it_does_not_ask_the_model_which_entity(self):
        """La fase A basta: la domanda nuova non costa la chiamata di fase B."""
        self._prima_domanda()
        _outcome, adapter = self._run("mostrami le aziende di Roma", [envelope(
            target("res_partner"),
            self._condizione("res_partner.city", "di Roma", "Roma"))])
        self.assertEqual(len(adapter.requests), 1,
                         "una sola chiamata: l'entita' l'ha decisa il dizionario")

    def test_the_model_is_not_handed_the_previous_state(self):
        """Ripartire vuol dire anche togliergli di dosso un contesto che non c'entra."""
        self._prima_domanda()
        _outcome, adapter = self._run("mostrami le aziende di Roma", [envelope(
            target("res_partner"),
            self._condizione("res_partner.city", "di Roma", "Roma"))])
        self.assertIsNone(adapter.requests[-1].state)

    # --- il raffinamento ----------------------------------------------------

    def test_a_sentence_without_a_subject_still_refines(self):
        """§17.1: *«solo quelli di Roma»* non nomina l'entita' e continua la domanda
        di prima. E' cio' che fa funzionare una conversazione, e non va rotto."""
        self._prima_domanda()
        outcome, adapter = self._run("solo quelli attivi", [envelope(
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "res_partner.active", "predicate": "is_true"},
             "provenance": {"text": "attivi"}})])
        refs = sorted(c["ref"] for c
                      in state_module.conditions(outcome.state.get("filter")))
        self.assertEqual(refs, ["res_partner.active", "res_partner.city"])
        self.assertIsNotNone(adapter.requests[-1].state,
                             "un raffinamento ha bisogno dello stato per essere letto")

    def test_the_trace_says_when_it_restarted(self):
        """Un turno che riparte e uno che continua si distinguono solo dal risultato:
        la traccia e' l'unico posto in cui la decisione si vede."""
        self._prima_domanda()
        outcome, _adapter = self._run("mostrami le aziende di Roma", [envelope(
            target("res_partner"),
            self._condizione("res_partner.city", "di Roma", "Roma"))])
        self.assertEqual(outcome.debug.get("state_restarted"), "res_partner")


@tagged("post_install", "-at_install", "nli_dispatch")
class TestAQuestionMustHaveAnswersThatWork(DispatchCase):
    """D128 — un'opzione che non si puo' applicare non si offre.

    Visto sul campo il 3 agosto 2026: il modello ha chiesto per quale data filtrare e
    dietro *«Filtra per Data creazione»* c'era un `within` **senza periodo**, piu' una
    condizione sulla data di chiusura. L'utente ha cliccato, D121 ha riconosciuto
    l'etichetta e ha applicato fedelmente qualcosa che non era applicabile.
    """

    def setUp(self):
        super().setUp()
        self.scope = ("res.partner",)

    @staticmethod
    def _clarification(*options):
        return json.dumps({
            "dsl_version": "1.0", "outcome": "clarification",
            "clarification": {"question": "Per quale data?", "options": list(options)},
        })

    @staticmethod
    def _option(label, *operations):
        return {"label": label, "operations": list(operations)}

    def _rotta(self, ref="res_partner.create_date"):
        """L'operazione esatta della trascrizione: `within` senza periodo."""
        return {"op": "add_condition", "combine": "all",
                "condition": {"ref": ref, "predicate": "within"}}

    def _buona(self, testo="di Cittaprova"):
        return {"op": "add_condition", "combine": "all",
                "condition": {"ref": "res_partner.city", "predicate": "equals",
                              "value": {"kind": "text", "text": "Cittaprova"}},
                "provenance": {"text": testo}}

    def _run(self, replies):
        item = self.accept("mostrami le aziende")
        return pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter(replies), scope=self.scope,
            context_window=32_000, debug=True)

    def test_an_option_that_cannot_be_applied_is_not_offered(self):
        outcome = self._run([self._clarification(
            self._option("rotta", target("res_partner"), self._rotta()),
            self._option("buona 1", target("res_partner"), self._buona()),
            self._option("buona 2", target("res_partner"), self._buona("a Roma")),
        )])
        self.assertEqual(outcome.outcome, "clarification", outcome.failures)
        etichette = [o["label"] for o
                     in outcome.interpretation["clarification"]["options"]]
        self.assertEqual(etichette, ["buona 1", "buona 2"])

    def test_a_question_with_no_usable_answer_is_not_a_question(self):
        """Meglio un «non ho capito» subito che quattro opzioni che non funzionano:
        l'utente lo scopre mentre sta ancora leggendo la propria frase, invece che dopo
        un clic e due minuti."""
        outcome = self._run([self._clarification(
            self._option("rotta 1", self._rotta()),
            self._option("rotta 2", self._rotta("res_partner.write_date")),
        )])
        self.assertEqual(outcome.outcome, "not_understood")
        self.assertTrue(outcome.failures)

    def test_one_survivor_is_a_confirmation_in_disguise(self):
        """`01` §11.2: sotto due opzioni non e' una domanda."""
        outcome = self._run([self._clarification(
            self._option("rotta", self._rotta()),
            self._option("buona", target("res_partner"), self._buona()),
        )])
        self.assertEqual(outcome.outcome, "not_understood")

    def test_a_sound_clarification_passes_through_untouched(self):
        busta = self._clarification(
            self._option("buona 1", target("res_partner"), self._buona()),
            self._option("buona 2", target("res_partner"), self._buona("a Roma")),
        )
        outcome = self._run([busta])
        self.assertEqual(outcome.outcome, "clarification")
        self.assertEqual(
            len(outcome.interpretation["clarification"]["options"]), 2)

    def test_the_trace_says_which_option_was_refused_and_why(self):
        outcome = self._run([self._clarification(
            self._option("rotta", self._rotta()),
            self._option("buona 1", target("res_partner"), self._buona()),
            self._option("buona 2", target("res_partner"), self._buona("a Roma")),
        )])
        rifiutata = outcome.debug.get("clarification_option_refused")
        self.assertEqual(rifiutata["label"], "rotta")
        self.assertTrue(rifiutata["why"])


class TestTheDateThatWasNotChosen(DispatchCase):
    """D135 — un periodo su una data che la frase non nomina diventa una domanda.

    **Il fallimento che questa classe chiude.** Batteria del 3 agosto 2026, modello e
    banca dati veri: *«mostrami i lead creati quest'anno»* e *«mostrami gli ordini di
    vendita di questo mese»* hanno risposto `not_understood`, tre volte su tre. Sono le
    due entita' che espongono piu' di una data, cioe' le prime due domande che chiunque
    farebbe, e la causa non era il modello: il prompt gli chiedeva di **scrivere lui**
    la domanda con due-quattro opzioni complete e applicabili.

    Adesso il modello colloca la condizione e basta; la domanda la costruiamo noi
    dall'ancora di D110, e sceglierla esegue senza chiamare il modello (D121).

    **La prova che §38 chiede** — quella che diventa rossa se qualcuno scollega — e' la
    coppia: la domanda arriva quando la data e' indovinata, e **non** arriva quando la
    frase la nomina. Togliere `names`, `time_anchor` o `carries_period` dalla conduttura
    fa cadere la prima; togliere il riconoscitore T1 fa cadere la seconda.
    """

    #: **Perche' gli utenti e non le aziende.** Questa regola vive o muore sull'ancora
    #: di D110, e l'ancora dipende da quante date l'entita' espone: `res.partner` ne
    #: espone **una** (`create_date`), quindi non ha nessuna scelta da offrire.
    #: `res.users` ne espone due — creazione e ultimo accesso — ed e' installata
    #: ovunque, quindi il banco non dipende da un modulo applicativo.
    ENTITY = "res_users"

    def setUp(self):
        super().setUp()
        self.scope = ("res.users",)

    def _catalogue(self):
        semantics = self.user_env["nli.semantics"].semantics(self.scope)
        return self.user_env["nli.semantics"].catalogue_for(
            semantics, self.ENTITY, context_window=32_000)

    def _dates(self):
        return list((self._catalogue().time_anchor or {}).get("choices") or ())

    def _label_of(self, ref):
        for attribute in self._catalogue().attributes:
            if attribute.ref == ref:
                return attribute.terms[0] if attribute.terms else attribute.ref
        return ref

    def _period(self, ref, text):
        return {"op": "add_condition", "combine": "all",
                "condition": {"ref": ref, "predicate": "within",
                              "value": {"kind": "temporal",
                                        "expression": "current_year"}},
                "provenance": {"text": text}}

    def _run(self, item, replies):
        return pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter(replies), scope=self.scope,
            context_window=32_000)

    def _ask(self, utterance, replies, *, phase_b=True):
        """Un turno intero, scritto come lo scrive il lavoratore.

        La prima risposta e' quella della fase B — *di quale entita' si parla* — che
        gira sempre quando la fase A non riconosce il soggetto nella frase. Le frasi
        di questo banco non lo nominano di proposito: cosi' il numero di chiamate al
        modello e' lo stesso a ogni giro, e non dipende da quali termini il dizionario
        dell'installazione ha raccolto per gli utenti (D126).

        `phase_b=False` per il **secondo** turno di una conversazione: li' lo stato ha
        gia' un bersaglio, la frase non ne nomina un altro, e quindi e' un raffinamento
        — la fase B non gira e il modello viene chiamato una volta sola.
        """
        item = self.accept(utterance)
        prima = [envelope(target(self.ENTITY))] if phase_b else []
        outcome = self._run(item, [*prima, *replies])
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return outcome

    # --- il banco non passa a vuoto ---------------------------------------

    def test_the_entity_this_bench_uses_really_exposes_two_dates(self):
        """Nessun controllo passa a vuoto. Se un domani il catalogo esponesse una data
        sola su questa entita', le prove sotto passerebbero **senza provare niente**:
        la regola non scatterebbe perche' non c'e' nulla da scegliere, non perche'
        funziona."""
        dates = self._dates()
        self.assertGreaterEqual(
            len(dates), 2,
            "l'ancora di D110 deve dichiarare `choices`, altrimenti questa classe "
            f"non esercita nulla: ancora = {self._catalogue().time_anchor!r}")

    # --- scatta ------------------------------------------------------------

    def test_a_period_the_sentence_did_not_anchor_becomes_a_question(self):
        dates = self._dates()
        outcome = self._ask("mostrami quelli di quest'anno", [
            envelope(target(self.ENTITY),
                     self._period(dates[0], "di quest'anno")),
        ])
        self.assertEqual(outcome.outcome, "clarification", outcome.failures)
        options = outcome.interpretation["clarification"]["options"]
        self.assertEqual([option["label"] for option in options],
                         [self._label_of(ref) for ref in dates[:4]])
        self.assertIn("quest'anno", outcome.interpretation["clarification"]["question"])

    def test_every_option_keeps_the_period_and_moves_only_the_date(self):
        """D111: un'espressione di tempo non si lascia cadere. Nessuna opzione la
        toglie — quella di D106 (*«senza quel filtro»*) qui non esiste."""
        dates = self._dates()
        outcome = self._ask("mostrami quelli di quest'anno", [
            envelope(target(self.ENTITY), self._period(dates[0], "di quest'anno")),
        ])
        options = outcome.interpretation["clarification"]["options"]
        for option, ref in zip(options, dates):
            conditions = [operation for operation in option["operations"]
                          if operation.get("op") == "add_condition"]
            self.assertEqual(len(conditions), 1)
            self.assertEqual(conditions[0]["condition"]["ref"], ref)
            self.assertEqual(conditions[0]["condition"]["value"],
                             {"kind": "temporal", "expression": "current_year"})

    def test_answering_with_a_date_executes_without_calling_the_model(self):
        """Il pezzo che vale il turno: da un minuto e mezzo d'attesa a niente."""
        dates = self._dates()
        self._ask("mostrami quelli di quest'anno", [
            envelope(target(self.ENTITY), self._period(dates[0], "di quest'anno")),
        ])
        seconda = self._label_of(dates[1])
        item = self.accept(seconda)
        adapter = RecordedAdapter([])
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env), adapter=adapter,
            scope=self.scope, context_window=32_000)
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(adapter.requests, [],
                         "l'opzione porta gia' le sue operazioni (D121)")
        refs = [condition.get("ref") for condition
                in state_module.conditions((outcome.state or {}).get("filter"))]
        self.assertEqual(refs, [dates[1]])

    def test_choosing_a_date_does_not_drag_the_previous_question_along(self):
        """**Visto sul campo il 3 agosto 2026.** Chi risponde a una domanda applica le
        operazioni dell'opzione, e fino a oggi le applicava allo stato che la
        conversazione aveva **prima**. Ma la domanda era nata da una frase che nominava
        il proprio soggetto, e **D127** dice che quella frase ricomincia: lo stato di
        prima era gia' stato buttato via nel turno che ha posto la domanda — solo che un
        turno che chiede non scrive stato, quindi il vecchio era ancora li'.

        Sul campo si e' visto come un ordinamento di troppo. Il caso che conta e' un
        altro: se il turno di prima filtrava per una citta', la risposta alla domanda
        esce **ristretta a quella citta'**, senza che niente lo dica. Una risposta
        sbagliata con l'aria di essere giusta, che e' cio' che il prodotto non deve fare.

        La regola non e' nuova, e' D127 applicata dove non arrivava: **un'opzione che si
        porta il proprio `set_target` e' una richiesta intera** — D106 le costruisce da
        una — quindi riparte. Una che non ce l'ha e' un raffinamento e continua.
        """
        self._ask("mostrami quelli che si chiamano Alfa", [
            envelope(target(self.ENTITY),
                     {"op": "add_condition", "combine": "all",
                      "condition": {"ref": f"{self.ENTITY}.name",
                                    "predicate": "contains",
                                    "value": {"kind": "text", "text": "Alfa"}},
                      "provenance": {"text": "che si chiamano Alfa"}}),
        ])
        dates = self._dates()
        chiarimento = self._ask("mostrami quelli di quest'anno", [
            envelope(target(self.ENTITY), self._period(dates[0], "di quest'anno")),
        ], phase_b=False)
        self.assertEqual(chiarimento.outcome, "clarification", chiarimento.failures)

        item = self.accept(self._label_of(dates[1]))
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([]), scope=self.scope, context_window=32_000)
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        refs = [condition.get("ref") for condition
                in state_module.conditions((outcome.state or {}).get("filter"))]
        self.assertEqual(refs, [dates[1]],
                         "la condizione del turno di prima non doveva sopravvivere")

    # --- e non scatta quando la frase la data la dice ----------------------

    def test_a_period_on_the_date_the_sentence_names_is_answered(self):
        """*«le aziende con data di creazione di quest'anno»*: la scelta e'
        dell'utente, e chiedergliela di nuovo sarebbe non averla ascoltata."""
        dates = self._dates()
        outcome = self._ask(
            f"mostrami quelli con {self._label_of(dates[0])} di quest'anno",
            [envelope(target(self.ENTITY),
                      self._period(dates[0],
                                   f"con {self._label_of(dates[0])} di quest'anno"))])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)

    def test_a_turn_with_no_period_is_answered_as_before(self):
        """La regola nuova non tocca chi non porta un periodo. Il risparmio — non
        costruire il catalogo per cercarci un'ancora che non serve — e' provato dove
        vive, cioe' su `carries_period` in zona pura."""
        outcome = self._ask("mostrami quelli che si chiamano Alfa", [
            envelope(target(self.ENTITY),
                     {"op": "add_condition", "combine": "all",
                      "condition": {"ref": f"{self.ENTITY}.name",
                                    "predicate": "contains",
                                    "value": {"kind": "text", "text": "Alfa"}},
                      "provenance": {"text": "che si chiamano Alfa"}}),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)


class TestTheNearestPeriodIsNotTheAnsweredOne(DispatchCase):
    """D144 — un periodo che il frammento non nomina non passa la conduttura.

    **Il fallimento che questa classe chiude.** Sessione del 6 agosto 2026, modello e
    banca dati veri: appena D141 ha dato al modello `quarter_of_year`, *«nel secondo
    semestre»* e' tornata con il **secondo trimestre**, tre giri su tre. Una riga di
    prompt che lo vietava per nome non ha retto. La classe di guasto non e' il simbolo
    che manca: e' il **ripiego silenzioso** su quello vicino.

    **La prova che §38 chiede** — quella che diventa rossa se qualcuno scollega — e' la
    coppia: il ripiego non passa, e una risposta giusta passa lo stesso. Togliere
    `names_period` dalla conduttura fa cadere la prima; scrivere una rete troppo larga
    fa cadere la seconda, che e' il modo peggiore di sbagliare.

    Il banco usa `res.partner` di proposito: espone **una sola** data, quindi la
    domanda sull'ancora del tempo di **D135** non si mette di mezzo e cio' che si
    misura e' solo questa rete.
    """

    ENTITY = "res_partner"

    def setUp(self):
        super().setUp()
        self.scope = ("res.partner",)

    def _catalogue(self):
        semantics = self.user_env["nli.semantics"].semantics(self.scope)
        return self.user_env["nli.semantics"].catalogue_for(
            semantics, self.ENTITY, context_window=32_000)

    def _date(self):
        for attribute in self._catalogue().attributes:
            if attribute.type in ("date", "datetime"):
                return attribute.ref
        return None

    def _period(self, expression, text, **parameters):
        value = {"kind": "temporal", "expression": expression}
        value.update(parameters)
        return {"op": "add_condition", "combine": "all",
                "condition": {"ref": self._date(), "predicate": "within",
                              "value": value},
                "provenance": {"text": text}}

    def _ask(self, utterance, replies):
        item = self.accept(utterance)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env),
            adapter=RecordedAdapter([envelope(target(self.ENTITY)), *replies]),
            scope=self.scope, context_window=32_000)
        worker_module._persist(
            self.user_env, item.with_env(self.user_env), outcome)
        return outcome

    # --- il banco non passa vuoto -------------------------------------------

    def test_the_entity_this_bench_uses_exposes_a_date(self):
        """Nessun controllo passa vuoto: senza una data nel catalogo ogni asserzione
        qui sotto misurerebbe l'assenza dell'attributo invece della rete."""
        self.assertTrue(self._date(), "il catalogo non espone alcuna data")

    def test_the_entity_this_bench_uses_exposes_only_one_date(self):
        """Se `res.partner` un domani ne esponesse due, la domanda di D135 arriverebbe
        prima e queste prove misurerebbero quella invece di questa rete."""
        self.assertFalse(
            (self._catalogue().time_anchor or {}).get("choices"),
            "l'entita' del banco ha piu' di una data: D135 si mette di mezzo")

    # --- la coppia -----------------------------------------------------------

    def test_the_nearest_period_does_not_pass(self):
        """*«Nel secondo semestre»* risposto con il secondo trimestre: il caso
        misurato in §46.7. Il modello ha il giro di riparazione di **D15**, insiste, e
        la conduttura esce con un rifiuto — che e' l'esito onesto di partenza."""
        sbagliata = self._period("quarter_of_year", "nel secondo semestre", n=2)
        outcome = self._ask("mostrami quelli del secondo semestre", [
            envelope(target(self.ENTITY), sbagliata),
            envelope(target(self.ENTITY), sbagliata),
        ])
        self.assertEqual(outcome.outcome, "not_understood")

    def test_the_period_the_words_carry_passes(self):
        """La meta' che conta di piu': `half_of_year(2)` sullo stesso frammento e' la
        risposta giusta, e la rete non deve toccarla."""
        outcome = self._ask("mostrami quelli del secondo semestre", [
            envelope(target(self.ENTITY),
                     self._period("half_of_year", "nel secondo semestre", n=2)),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)

    def test_a_relative_window_is_left_alone(self):
        """Una finestra relativa non nomina un periodo, e la rete tace."""
        outcome = self._ask("mostrami quelli degli ultimi 30 giorni", [
            envelope(target(self.ENTITY),
                     self._period("last_n_days", "negli ultimi 30 giorni", n=30)),
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)


@tagged("post_install", "-at_install", "nli_dispatch")
class TestARefinementReconsiders(DispatchCase):
    """D145 — un raffinamento che non si capisce si ricrede, una volta sola.

    **Il caso, misurato il 20 agosto 2026 sul database vero** (conversazione 964).
    Dopo *«dammi il numero di lead creati quest'anno»* arriva *«mostrami le vendite con
    totale superiore a 2000»*. La fase A non conosceva la parola *vendite*, quindi il
    turno e' stato letto come un raffinamento dei lead: catalogo dei lead, dove *Totale*
    non esiste, e `not_understood` dopo 67,7 secondi.

    La fase B — che esiste esattamente per «il dizionario non conosce questa parola» —
    non girava mai, perche' era raggiungibile solo quando non c'era nessuno stato. Il
    modello, interrogato, risolve *vendite* al primo colpo.

    Queste prove fissano i due lati: dove la seconda lettura deve scattare, e i due
    casi in cui non deve costare niente.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True})
        self.scope = ("res.partner", "res.country")
        # `aziende` la fase A la conosce; `paesi` no — ed e' la parola su cui il
        # dizionario resta muto, come *vendite* nel caso vero.
        self.env["nli.dictionary.entry"].create({
            "entry_type": "T1", "level": "L2", "ref": "res_partner",
            "entity_ref": "res_partner", "terms": "aziende"})
        self.env.registry.clear_cache()

    def _run(self, utterance, replies):
        item = self.accept(utterance)
        adapter = RecordedAdapter(replies)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env), adapter=adapter,
            scope=self.scope, context_window=32_000, debug=True)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return outcome, adapter

    @staticmethod
    def _non_capito() -> str:
        return json.dumps({"dsl_version": "1.0", "outcome": "not_understood"})

    def _prima_domanda(self):
        return self._run("mostrami le aziende", [envelope(target("res_partner"))])

    # --- dove deve scattare -------------------------------------------------

    def test_a_failed_refinement_asks_the_model_which_entity(self):
        """Il caso vero: la frase nomina un soggetto che il dizionario non ha, la
        lettura sull'entita' assunta fallisce, e la fase B la corregge."""
        self._prima_domanda()
        outcome, adapter = self._run("mostrami i paesi", [
            self._non_capito(),                        # la lettura sui contatti
            envelope(target("res_country")),           # fase B: di che parla la frase
            envelope(target("res_country")),           # la lettura buona
        ])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        self.assertEqual(outcome.state.get("target", {}).get("ref"), "res_country")
        self.assertEqual(len(adapter.requests), 3)

    def test_the_second_reading_does_not_inherit_the_old_state(self):
        """Ricominciare vuol dire togliersi di dosso il contesto di prima: portarsi
        dietro il filtro dei contatti sarebbe il difetto di partenza con un'entita' in
        piu'."""
        self._prima_domanda()
        _outcome, adapter = self._run("mostrami i paesi", [
            self._non_capito(),
            envelope(target("res_country")),
            envelope(target("res_country")),
        ])
        self.assertIsNone(adapter.requests[-1].state)

    # --- dove non deve costare niente ---------------------------------------

    def test_a_sentence_that_names_its_entity_does_not_reconsider(self):
        """Se la fase A ha riconosciuto il soggetto, l'entita' non e' un'assunzione:
        il rifiuto e' del modello e ripeterlo costerebbe e basta."""
        self._prima_domanda()
        outcome, adapter = self._run("mostrami le aziende", [self._non_capito()])
        self.assertEqual(outcome.outcome, "not_understood")
        self.assertEqual(len(adapter.requests), 1,
                         "nessuna seconda lettura: la frase il soggetto lo ha detto")

    def test_when_phase_b_confirms_the_entity_the_first_refusal_stands(self):
        """La fase B dice la stessa entita': non c'e' niente da ricredersi, e una
        seconda lettura identica costerebbe un minuto per lo stesso esito."""
        self._prima_domanda()
        outcome, adapter = self._run("solo quelli attivi", [
            self._non_capito(),
            envelope(target("res_partner")),
        ])
        self.assertEqual(outcome.outcome, "not_understood")
        self.assertEqual(len(adapter.requests), 2)


@tagged("post_install", "-at_install", "nli_dispatch")
class TestTheAssumedEntityIsDeclared(DispatchCase):
    """D146 — l'entita' ereditata arriva allo schermo come dedotta, non come detta.

    E' la meta' di §49.4 che D145 non chiude. *«mostrami le anagrafiche di Roma»*,
    chiesta dopo una domanda sui lead, il 21 agosto 2026 ha risposto **un record di
    lead**: il modello e' riuscito a leggere la frase sul catalogo sbagliato — i lead
    una citta' ce l'hanno — e non c'e' stato nessun rifiuto a cui attaccare una seconda
    lettura. Un turno cosi' non ha **nessun** segnale d'errore: l'unico rimedio e' che
    chi legge veda su che cosa gli si sta rispondendo.
    """

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create(
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True})
        self.scope = ("res.partner",)
        self.env["nli.dictionary.entry"].create({
            "entry_type": "T1", "level": "L2", "ref": "res_partner",
            "entity_ref": "res_partner", "terms": "aziende"})
        self.env.registry.clear_cache()

    def _run(self, utterance, replies):
        item = self.accept(utterance)
        adapter = RecordedAdapter(replies)
        outcome = pipeline_module.run(
            self.user_env, item.with_env(self.user_env), adapter=adapter,
            scope=self.scope, context_window=32_000, debug=True)
        worker_module._persist(self.user_env, item.with_env(self.user_env), outcome)
        return outcome, adapter

    def _prima_domanda(self):
        return self._run("mostrami le aziende", [envelope(target("res_partner"))])

    def test_a_carried_target_is_shown_as_inferred(self):
        """Il caso per cui D146 esiste: nessuno ha nominato le aziende in questo turno,
        e l'interpretazione deve dirlo con la regola che l'ha prodotto."""
        self._prima_domanda()
        outcome, _adapter = self._run("solo quelli di Cittaprova", [envelope(
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "res_partner.city", "predicate": "equals",
                           "value": {"kind": "text", "text": "Cittaprova"}},
             "provenance": {"text": "di Cittaprova"}})])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        mostrato = outcome.interpretation["target"]
        self.assertEqual(mostrato["origin"], "inferred")
        self.assertEqual(mostrato["rule"], vocabulary.RULE_TARGET_CARRIED)

    def test_an_entity_the_sentence_names_is_not_an_inference(self):
        """Il lato che non deve scattare: qui l'utente l'entita' l'ha detta, e
        marcarla dedotta sarebbe una bugia nell'altra direzione — chi legge
        smetterebbe di fidarsi del bordo tratteggiato proprio dove e' vero."""
        self._prima_domanda()
        outcome, _adapter = self._run("mostrami le aziende", [envelope(
            target("res_partner"))])
        self.assertEqual(outcome.outcome, "operations", outcome.failures)
        mostrato = outcome.interpretation["target"]
        self.assertEqual(mostrato["origin"], "user")
        self.assertNotIn("rule", mostrato)
