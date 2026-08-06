"""The profile state machine — the three prohibitions administration cannot lift.

D75 moved the choice of model into the panel, and that **moved the trust boundary**.
D76, D77 and D80 are what pay for the move, and all three are verified here against a
real registry rather than described in a manual.
"""

import os

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..adapters.http import ALLOWED_HOSTS_VARIABLE

LOCAL = "http://localhost:11434/v1"


@tagged("post_install", "-at_install", "nli_engine")
class TestProfile(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = os.environ.get(ALLOWED_HOSTS_VARIABLE)
        os.environ[ALLOWED_HOSTS_VARIABLE] = "localhost:11434"
        self.addCleanup(self._restore)

    def _restore(self):
        if self._saved is None:
            os.environ.pop(ALLOWED_HOSTS_VARIABLE, None)
        else:
            os.environ[ALLOWED_HOSTS_VARIABLE] = self._saved

    def profile(self, **values):
        return self.env["nli.profile"].create({
            "name": values.pop("name", "Locale"),
            "protocol": "openai_compatible",
            "endpoint": values.pop("endpoint", LOCAL),
            "model_name": values.pop("model_name", "qwen2.5:latest"),
            "context_window": values.pop("context_window", 32000),
            **values,
        })

    # --- D77 ---------------------------------------------------------------

    def test_an_endpoint_outside_the_environment_list_is_refused(self):
        """The panel cannot widen what the environment admits.

        A compromised administrator would otherwise send every utterance and
        catalogue elsewhere, with normal accuracy and normal latency, and no metric
        in `07` would detect it.
        """
        with self.assertRaises(ValidationError):
            self.profile(endpoint="https://api.altrove.example/v1")

    def test_the_admitted_hosts_are_visible_and_not_editable(self):
        """An administrator who can see the list can tell why an endpoint was
        refused, without being able to widen it."""
        self.assertEqual(self.env["nli.profile"].admitted_hosts(), ["localhost:11434"])

    # --- D76 ---------------------------------------------------------------

    def test_the_database_holds_the_name_of_a_variable_never_a_value(self):
        profile = self.profile(secret_env_var="NLI_TEST_KEY")
        self.assertEqual(profile.secret_env_var, "NLI_TEST_KEY")
        stored = " ".join(str(value) for value in profile.read()[0].values())
        self.assertNotIn("sk-", stored, "a dump must not yield credentials")

    # --- D75 and D80 -------------------------------------------------------

    def test_a_profile_starts_in_draft(self):
        self.assertEqual(self.profile().state, "draft")

    def test_an_unqualified_profile_cannot_be_activated(self):
        """**D80** — a structural prohibition, not a checklist item.

        D51's qualification includes the isolation proof, and a model that has not
        passed it can degrade the ERP for everyone. A procedure that depends on
        somebody remembering holds until the afternoon somebody is in a hurry.
        """
        profile = self.profile()
        with self.assertRaises(UserError) as raised:
            profile.action_activate()
        self.assertIn("D80", str(raised.exception))
        self.assertEqual(profile.state, "draft")

    def test_qualification_then_activation(self):
        profile = self.profile()
        profile.action_qualify("corpus fondativo, 20 casi, istante 2026-07-15")
        self.assertEqual(profile.state, "qualified")
        self.assertTrue(profile.qualified_on)
        profile.action_activate()
        self.assertEqual(profile.state, "active")

    def test_a_qualification_records_what_was_measured(self):
        """A qualification nobody can reconstruct is not one (D51)."""
        profile = self.profile()
        profile.action_qualify("qwen2.5 locale, 20 casi di apertura")
        self.assertIn("20 casi", profile.qualification_note)

    def test_activating_a_second_profile_retires_the_first(self):
        """One active at a time (D75): with two, which one answered would be a
        question nobody could answer afterwards."""
        first = self.profile(name="Primo")
        second = self.profile(name="Secondo")
        first.action_qualify()
        first.action_activate()
        second.action_qualify()
        second.action_activate()
        self.assertEqual(first.state, "qualified")
        self.assertEqual(second.state, "active")
        self.assertEqual(self.env["nli.profile"].active_profile(), second)

    def test_no_active_profile_is_a_declared_state_not_an_exception(self):
        """§11 — the model being unavailable leaves the system partially usable, and
        raising here would take saved queries down with it.

        **The state is built, not assumed.** This used to read the registry as it
        found it, so it only passed on a database where nobody had ever put a model
        in service — green on a fresh test database, red on the one the product runs
        on. A test that passes only on an empty database is not a test.
        """
        registry = self.env["nli.profile"]
        registry.search([("state", "=", "active")]).action_retire()
        self.assertFalse(registry.active_profile())

    # --- D78 ---------------------------------------------------------------

    def test_the_profile_declares_its_capabilities(self):
        profile = self.profile(context_window=8192, constrained_generation=True)
        capabilities = profile.capabilities()
        self.assertEqual(capabilities.context_window, 8192)
        self.assertTrue(capabilities.constrained_generation)

    def test_a_window_that_is_not_positive_is_refused(self):
        """The declared window is the divisor of D79's budget: at zero the catalogue
        would derive a budget from nothing, and the panel would be a way to break the
        thing that reads it one table away.

        The guard is a `CHECK`, and for a while it was written with a stray comma
        inside the SQL: Odoo logged the failed `ALTER TABLE`, carried on, and **no
        database ever had the constraint**. Nothing failed, because nothing was
        watching it fail. Hence this test, and the error is matched by name so that a
        constraint dropped again cannot pass as some other refusal.
        """
        with self.assertRaises(Exception) as refusal:
            self.profile(context_window=0)
            self.env.flush_all()
        self.assertIn("context_window_positive", str(refusal.exception))

    def test_a_positive_window_passes_the_same_guard(self):
        """The other half: a check that refuses everything is not a check either."""
        self.assertEqual(self.profile(context_window=1).context_window, 1)

    # --- D122 --------------------------------------------------------------

    def test_the_adapter_is_built_with_the_declared_timeout(self):
        """Misurato il 2 agosto: il modello locale impiegava 60,1 s per una chiamata e
        l'adattatore ne concedeva 60 fissi, quindi **ogni** turno scadeva. Il valore
        deve arrivare dal profilo, o non c'e' modo di usare il prodotto con un modello
        piu' lento di quanto qualcuno ha scritto in una costante."""
        profile = self.profile(timeout_seconds=240)
        self.assertEqual(profile.adapter().timeout, 240)

    def test_the_default_is_generous_enough_for_a_local_model(self):
        """Il valore che si prende senza scegliere non deve essere quello che rompe il
        caso su cui si sviluppa."""
        self.assertGreaterEqual(self.profile().timeout_seconds, 180)

    def test_a_timeout_that_is_not_positive_is_refused(self):
        with self.assertRaises(Exception) as refusal:
            self.profile(timeout_seconds=0)
            self.env.flush_all()
        self.assertIn("timeout_positive", str(refusal.exception))

    # The obvious next assertion — that the declared window drives the catalogue
    # budget (D79) — is **not** here, and the boundary check is what said so: it
    # would import `nli_semantics` from `nli_engine`, and §6.3 forbids that edge.
    # The engine declares the window; who derives a budget from it is not the
    # engine's business. The assertion lives in `nli_semantics/pure_tests`, where the
    # budget does.

    def test_an_adapter_is_built_from_the_profile(self):
        adapter = self.profile().adapter()
        self.assertEqual(adapter.protocol, "openai_compatible")
        self.assertEqual(adapter.temperature, 0.0,
                         "sampling would widen the only non-deterministic point")
