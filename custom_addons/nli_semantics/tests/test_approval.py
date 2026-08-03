"""The approval path: from a saved filter to a named condition that works (D108).

Until this existed the live dictionary was **L0 only**. The proposals of D35 went into
the L3 queue, which is not a level, and there was nothing to approve them *into* — so
no installation had a single named condition, the model could not emit `is_category`,
and the two protections of D105 and D106 had nothing to act on.
"""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestApproval(TransactionCase):
    def setUp(self):
        super().setUp()
        self.entries = self.env["nli.dictionary.entry"]
        self.partner_entity = "res_partner"

    def _approve(self, **overrides):
        values = {
            "entry_type": "T5",
            "level": "L2",
            "ref": f"{self.partner_entity}.senza_partita_iva",
            "entity_ref": self.partner_entity,
            "terms": "senza partita iva\nsenza p.iva",
            "condition": '{"kind": "is_not_set", "field": "vat"}',
            "source_domain": "[('vat', '=', False)]",
        }
        values.update(overrides)
        return self.entries.create(values)

    # --- what cannot be stored --------------------------------------------
    def test_a_condition_that_is_not_valid_json_is_refused(self):
        with self.assertRaises(ValidationError):
            self._approve(condition="{kind: is_not_set}")

    def test_a_condition_the_language_does_not_admit_is_refused(self):
        """`telepathy` is not a kind, and the refusal happens at write time rather
        than at build time: an entry that exists in a table and not in the dictionary
        is a divergence nobody notices until a result changes."""
        with self.assertRaises(ValidationError):
            self._approve(condition='{"kind": "telepathy", "field": "vat"}')

    def test_a_condition_missing_a_required_key_is_refused(self):
        with self.assertRaises(ValidationError):
            self._approve(condition='{"kind": "compare", "field": "vat"}')

    def test_the_same_reference_cannot_be_approved_twice_at_one_level(self):
        self._approve()
        with self.assertRaises(Exception):
            self._approve()
            self.env.flush_all()

    # --- traceability -------------------------------------------------------
    def test_the_approval_records_who_and_when(self):
        """An approval whose author is a text somebody typed is not traceability."""
        entry = self._approve()
        self.assertEqual(entry.approved_uid, self.env.user)
        self.assertTrue(entry.approved_on)

    def test_the_filter_s_domain_is_kept_verbatim_and_never_executed(self):
        entry = self._approve()
        self.assertEqual(entry.source_domain, "[('vat', '=', False)]")

    # --- what reaches the dictionary ---------------------------------------
    def test_an_approved_condition_becomes_usable(self):
        """The whole point: before the approval the reference does not exist for the
        chain, after it the chain can resolve and execute it."""
        scope = ("res.partner",)
        before = self.env["nli.semantics"].semantics(scope)
        reference = f"{self.partner_entity}.senza_partita_iva"
        self.assertNotIn(reference, before.bindings)

        self._approve()
        self.env.registry.clear_cache()

        after = self.env["nli.semantics"].semantics(scope)
        self.assertIn(reference, after.bindings)
        binding = after.bindings[reference]
        self.assertEqual(binding.kind, "category")
        self.assertEqual(list(binding.domain), [("vat", "=", False)])

    def test_the_terms_reach_the_dictionary_and_ground_a_condition(self):
        """The terms are what D105 checks a fragment against: without them in the
        dictionary the grounding of a legitimate condition would refuse it."""
        from odoo.addons.nli_semantics.dictionary import grounding

        self._approve()
        self.env.registry.clear_cache()
        semantics = self.env["nli.semantics"].semantics(("res.partner",))

        reference = f"{self.partner_entity}.senza_partita_iva"
        self.assertIn(reference,
                      [entry["ref"] for entry
                       in semantics.dictionary.categories_of(self.partner_entity)])

        mentions = grounding.mentions_of(semantics.dictionary)
        self.assertTrue(mentions(reference, "quelli senza partita iva"))
        self.assertFalse(mentions(reference, "lo scorso mese"))

    def test_an_aggregate_is_stored_but_left_unbound(self):
        """V-D87-2: an aggregate is level 5's business, not a domain. Storing it and
        leaving it unbound makes level 3 refuse it by name, instead of letting it fail
        late at execution — which is the failure C3 exists to prevent."""
        self._approve(
            ref=f"{self.partner_entity}.importanti",
            terms="importanti",
            condition='{"kind": "aggregate", "entity": "sale.order", '
                      '"field": "amount_total", "function": "sum", '
                      '"operator": "gt", "value": 50000}')
        self.env.registry.clear_cache()
        semantics = self.env["nli.semantics"].semantics(("res.partner",))
        self.assertNotIn(f"{self.partner_entity}.importanti", semantics.bindings)

    def test_an_entry_for_an_entity_out_of_reach_does_not_enter(self):
        """The row is readable by every internal user on purpose — the interrogation
        path may not elevate (§6.3) — so what protects the catalogue is this filter,
        not the visibility of the record."""
        self._approve(ref="mai_vista.qualcosa", entity_ref="mai_vista",
                      terms="qualcosa")
        self.env.registry.clear_cache()
        semantics = self.env["nli.semantics"].semantics(("res.partner",))
        self.assertNotIn("mai_vista.qualcosa", semantics.bindings)

    # --- the proposals it is fed from --------------------------------------
    def test_a_proposal_is_still_inert_until_approved(self):
        """D28: an entry that applied itself would be self-reinforcing."""
        self.env["ir.filters"].create({
            "name": "Clienti da richiamare",
            "model_id": "res.partner",
            "domain": "[('phone', '!=', False)]",
            "user_id": False,
        })
        self.env.registry.clear_cache()
        semantics = self.env["nli.semantics"].semantics(("res.partner",))
        self.assertFalse(
            [ref for ref in semantics.bindings if "richiamare" in ref],
            "a saved filter must not become a category on its own")


@tagged("post_install", "-at_install")
class TestEntityNaming(TransactionCase):
    """D126 — un'entita' ha i nomi con cui la gente la chiama, non l'etichetta grezza.

    Misurato sul database vero il 2 agosto 2026: la fase A non riconosceva **nessuna**
    entita', perche' `crm.lead` aveva un termine solo — `Lead/Opportunità` — e nessuna
    frase italiana contiene quella stringa.

    **Le prove guardano il meccanismo, non i dati dell'installazione.** Asserire che
    `res.partner` si chiama *Contatti* legherebbe la prova ai moduli installati e alla
    lingua della banca dati, e la prima volta che cambiano fallisce per una ragione che
    non riguarda questo codice. Il menu se lo costruisce la prova.
    """

    def setUp(self):
        super().setUp()
        from odoo.addons.nli_semantics.introspection import l0
        self.l0 = l0

    def _terms(self, model_name):
        return self.l0.naming_entries(self.env, model_name)[0]["terms"]

    # --- l'etichetta composta ---------------------------------------------

    def test_a_composite_label_becomes_several_names(self):
        """`Lead/Opportunità` sono due nomi, non uno: chi dice «i lead» deve trovarlo.

        Il normalizzatore riduce l'etichetta ai gettoni `lead opportunita`, e come
        termine unico pretende di trovarli tutti e due di fila — cosa che nessuna frase
        fa."""
        self.assertEqual(
            self.l0._split_label("Lead/Opportunità"),
            ["Lead/Opportunità", "Lead", "Opportunità"])

    def test_the_whole_label_is_kept_too(self):
        """Il vocabolario si somma (`06` §2.2): i pezzi non sostituiscono l'intero."""
        self.assertIn("Ordine, preventivo", self.l0._split_label("Ordine, preventivo"))

    def test_a_plain_label_stays_one_name(self):
        self.assertEqual(self.l0._split_label("Contatto"), ["Contatto"])

    def test_an_empty_label_produces_nothing_instead_of_an_empty_term(self):
        self.assertEqual(self.l0._split_label("   "), [])

    # --- i nomi che vengono dai menu --------------------------------------

    def test_the_name_in_the_menu_becomes_a_term(self):
        """Il modello si chiama *Contatto*, il menu *Le mie rubriche*, e la gente dice
        quello che preme. Leggerlo evita di costruire i plurali con regole di
        morfologia, che sbagliano sulle parole straniere e sui femminili irregolari."""
        azione = self.env["ir.actions.act_window"].create({
            "name": "Rubriche aziendali", "res_model": "res.partner",
            "view_mode": "list,form",
        })
        self.env["ir.ui.menu"].create({
            "name": "Rubriche aziendali", "action": f"ir.actions.act_window,{azione.id}",
        })
        self.assertIn("Rubriche aziendali", self._terms("res.partner"))

    def test_an_action_nobody_reaches_from_a_menu_is_not_a_name(self):
        """`act_window` ne esiste una pila per ogni modello, molte di servizio. Quelle
        appese a un menu sono quelle che una persona ha davanti."""
        self.env["ir.actions.act_window"].create({
            "name": "Azione tecnica di servizio", "res_model": "res.partner",
            "view_mode": "list",
        })
        self.assertNotIn("Azione tecnica di servizio", self._terms("res.partner"))

    def test_a_name_too_short_is_not_a_name(self):
        """Sotto quattro caratteri e' un'abbreviazione o un verbo: indicizzarlo produce
        collisioni invece di riconoscimenti."""
        azione = self.env["ir.actions.act_window"].create({
            "name": "Ok", "res_model": "res.partner", "view_mode": "list"})
        self.env["ir.ui.menu"].create({
            "name": "Ok", "action": f"ir.actions.act_window,{azione.id}"})
        self.assertNotIn("Ok", self._terms("res.partner"))

    # --- cio' che non deve rompersi ---------------------------------------

    def test_a_model_nobody_reaches_still_has_its_label(self):
        """Un'entita' senza nomi non e' nominabile: meglio l'etichetta grezza di
        niente."""
        self.assertTrue(self._terms("ir.attachment"))

    def test_no_term_is_repeated(self):
        azione = self.env["ir.actions.act_window"].create({
            "name": "Contatto", "res_model": "res.partner", "view_mode": "list"})
        self.env["ir.ui.menu"].create({
            "name": "Contatto", "action": f"ir.actions.act_window,{azione.id}"})
        terms = self._terms("res.partner")
        self.assertEqual(len(terms), len(set(terms)), terms)

    def test_the_fields_keep_their_single_label(self):
        """L'arricchimento riguarda l'entita': un campo si chiama come si chiama."""
        voci = self.l0.naming_entries(self.env, "res.partner")
        campi = [v for v in voci if "." in v["ref"]]
        self.assertTrue(campi)
        self.assertTrue(all(len(v["terms"]) == 1 for v in campi))
