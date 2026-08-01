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
