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
        """Il ramo non deve poter deviare l'esecuzione ordinaria."""
        self.set_bench(None)
        factory = self.env["nli.dispatcher"]._adapter_factory()
        with self.assertRaises(Exception):
            # Nessun profilo attivo su questa base: l'errore che arriva e' quello
            # del profilo mancante, non un adattatore sintetico silenzioso.
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
