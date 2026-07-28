"""The platform-facing half of the catalogue, against a real registry.

These need a database, which is the whole reason they are here and not in
`pure_tests/`: L0 is generated from the registry, the readable references come from
the access rules, and the fingerprint is a statement about both. Nothing here can be
verified against a fixture — a fixture would be a second opinion about what Odoo
does, and the failures worth catching are the ones where our opinion is wrong.
"""

from odoo.tests.common import TransactionCase, new_test_user, tagged

from ..catalogue import build, exposure
from ..dictionary.store import Dictionary
from ..introspection import filters, l0, permissions

MODEL = "res.partner"


@tagged("post_install", "-at_install", "nli_semantics")
class TestL0(TransactionCase):
    """The derived level (D84)."""

    def test_references_are_identifiers_not_labels(self):
        self.assertEqual(l0.reference_of_model("sale.order"), "sale_order")
        self.assertEqual(
            l0.reference_of_field("sale.order", "amount_total"),
            "sale_order.amount_total",
        )

    def test_generation_is_reproducible(self):
        """D84: L0 is regenerated at every module update, so two runs on the same
        registry must produce the same list — otherwise a diff between regenerations
        is unreadable and nobody notices what an update did to the dictionary."""
        first = l0.generate(self.env, [MODEL])
        second = l0.generate(self.env, [MODEL])
        self.assertEqual(first, second)
        self.assertTrue(first)

    def test_the_entity_carries_its_translated_label_as_a_term(self):
        entries = l0.naming_entries(self.env, MODEL)
        entity = next(e for e in entries if e["ref"] == "res_partner")
        self.assertTrue(entity["terms"][0])
        self.assertNotEqual(entity["terms"][0], "res_partner")

    def test_system_and_mixin_fields_produce_no_terms(self):
        refs = {entry["ref"] for entry in l0.naming_entries(self.env, MODEL)}
        for name in ("create_uid", "write_date", "id", "display_name"):
            self.assertNotIn(f"res_partner.{name}", refs)
        for name in self.env[MODEL].fields_get():
            if name.startswith("message_") or name.startswith("activity_"):
                self.assertNotIn(f"res_partner.{name}", refs)

    def test_enumerated_values_come_with_their_labels(self):
        entries = l0.enum_entries(self.env, MODEL)
        self.assertTrue(entries, "res.partner has selection fields")
        for entry in entries:
            self.assertEqual(entry["type"], "T2")
            self.assertTrue(entry["terms"][0])

    def test_l0_entries_are_valid_dictionary_entries(self):
        """The two halves must agree: what introspection produces, the pure
        dictionary must accept. A silent mismatch here would show up as an empty
        catalogue much later."""
        dictionary = Dictionary.build(l0.generate(self.env, [MODEL]))
        self.assertEqual(dictionary.problems, [])
        self.assertTrue(dictionary.terms_of("res_partner"))

    def test_descriptors_mark_what_the_exposure_rules_need(self):
        descriptors = l0.attribute_descriptors(self.env, MODEL)
        by_name = {descriptor.name: descriptor for descriptor in descriptors}
        self.assertTrue(by_name["create_uid"].is_system)
        self.assertTrue(by_name["name"].label)
        if "message_ids" in by_name:
            self.assertTrue(by_name["message_ids"].is_technical_mixin)

    def test_the_exposure_rules_cut_the_schema_down(self):
        """§5.2's number, on the real registry: the schema is not a catalogue."""
        descriptors = l0.attribute_descriptors(self.env, MODEL)
        kept = exposure.exposed(descriptors)
        self.assertLess(
            len(kept), len(descriptors),
            "the rules of §5.3 removed nothing, which means they are not running",
        )

    def test_transient_and_abstract_models_are_never_entities(self):
        self.assertFalse(l0.is_candidate_entity(self.env["base.language.install"]))
        self.assertTrue(l0.is_candidate_entity(self.env[MODEL]))


@tagged("post_install", "-at_install", "nli_semantics")
class TestPermissions(TransactionCase):
    """Readable references and the fingerprint (D39, D40)."""

    def setUp(self):
        super().setUp()
        self.internal = new_test_user(self.env, login="nli_internal")

    def test_a_user_without_read_access_has_no_references(self):
        """The first line of V2 is the vocabulary: what the user cannot see does not
        enter the space of possible interpretations, and no refusal reveals that it
        exists (D10, §7.2)."""
        env = self.env(user=self.internal)
        readable = permissions.readable_references(env, "ir.module.module")
        installed = self.env["ir.module.module"].with_user(self.internal)
        if not installed.has_access("read"):
            self.assertEqual(readable, frozenset())

    def test_readable_references_include_the_entity(self):
        readable = permissions.readable_references(self.env, MODEL)
        self.assertIn("res_partner", readable)
        self.assertIn("res_partner.name", readable)

    def test_the_fingerprint_is_stable_for_an_unchanged_situation(self):
        first = permissions.fingerprint(self.env, [MODEL])
        second = permissions.fingerprint(self.env, [MODEL])
        self.assertEqual(first, second)

    def test_two_users_with_different_groups_do_not_share_a_fingerprint(self):
        """The property §10.4 of `04` founds the reuse of a catalogue on."""
        other = new_test_user(self.env, login="nli_other",
                              groups="base.group_user,base.group_partner_manager")
        mine = permissions.fingerprint(self.env(user=self.internal), [MODEL])
        theirs = permissions.fingerprint(self.env(user=other), [MODEL])
        self.assertNotEqual(mine, theirs)

    def test_revoking_access_changes_the_fingerprint(self):
        """The failure D39 exists to prevent: a catalogue memoised before a
        revocation would keep exposing references the user may no longer name, and
        nothing would signal it."""
        env = self.env(user=self.internal)
        before = permissions.fingerprint(env, [MODEL])
        self.internal.write({"groups_id": [(3, self.env.ref("base.group_user").id)]})
        env.invalidate_all()
        after = permissions.fingerprint(env, [MODEL])
        self.assertNotEqual(before, after)

    def test_the_company_context_is_part_of_it(self):
        """D40 — the infrastructural form of R1.

        An execution that restores the user but not their active companies returns
        the same orders plus those of a company they had deselected: no error, no
        warning, a different number. No analysis of linguistic misunderstandings
        would ever find it, which is why it has to be in the key.
        """
        second = self.env["res.company"].create({"name": "NLI Seconda"})
        self.internal.write({"company_ids": [(4, second.id)]})
        one = permissions.fingerprint(
            self.env(user=self.internal, context={"allowed_company_ids":
                                                  [self.env.company.id]}), [MODEL])
        both = permissions.fingerprint(
            self.env(user=self.internal, context={"allowed_company_ids":
                                                  [self.env.company.id, second.id]}),
            [MODEL])
        self.assertNotEqual(
            one, both,
            "two different perimeters must not produce the same catalogue key",
        )

    def test_an_uncomputable_fingerprint_means_rebuild(self):
        """Fail safe: never served from memory with an uncertain fingerprint."""
        self.assertIsNone(permissions.fingerprint_or_rebuild(self.env, ["no.such.model"]))
        with self.assertRaises(permissions.FingerprintUnavailable):
            permissions.fingerprint(self.env, ["no.such.model"])


@tagged("post_install", "-at_install", "nli_semantics")
class TestSavedFilters(TransactionCase):
    """Saved filters as category proposals (D35)."""

    def test_a_shared_filter_becomes_a_proposal(self):
        self.env["ir.filters"].create({
            "name": "Clienti da richiamare",
            "model_id": MODEL,
            "domain": "[('customer_rank', '>', 0)]",
            "user_id": False,
        })
        proposals = filters.propose_categories(self.env, [MODEL])
        found = next(p for p in proposals if p.term == "Clienti da richiamare")
        self.assertEqual(found.entity, "res_partner")
        self.assertTrue(found.shared)

    def test_a_proposal_is_inert_until_approved(self):
        """It enters the L3 queue, and `validate_entry` refuses L3 outright: an
        automatically activated category would change what saved queries return,
        silently (D28)."""
        from ..dictionary import entries as entries_module

        proposal = filters.CategoryProposal(
            entity="res_partner", term="Clienti da richiamare", domain="[]")
        entry = proposal.as_entry()
        self.assertEqual(entry["level"], "L3")
        self.assertTrue(entries_module.validate_entry(entry))
        self.assertNotIn("condition", entry,
                         "the typed condition is written by a person at approval")

    def test_uninformative_names_do_not_reach_the_queue(self):
        self.env["ir.filters"].create({
            "name": "test", "model_id": MODEL, "domain": "[]", "user_id": False,
        })
        terms = {p.term for p in filters.propose_categories(self.env, [MODEL])}
        self.assertNotIn("test", terms)

    def test_shared_filters_are_reviewed_first(self):
        self.env["ir.filters"].create({
            "name": "Privato mio", "model_id": MODEL, "domain": "[]",
            "user_id": self.env.user.id,
        })
        self.env["ir.filters"].create({
            "name": "Pubblico a tutti", "model_id": MODEL, "domain": "[]",
            "user_id": False,
        })
        proposals = filters.propose_categories(self.env, [MODEL])
        self.assertTrue(proposals[0].shared,
                        "the review queue is ordered by impact (§2.3)")


@tagged("post_install", "-at_install", "nli_semantics")
class TestEndToEnd(TransactionCase):
    """Registry to catalogue, with the two halves joined."""

    def test_a_catalogue_from_the_live_registry(self):
        dictionary = Dictionary.build(l0.generate(self.env, [MODEL]))
        catalogue = build.build(
            dictionary,
            entity="res_partner",
            attributes=l0.attribute_descriptors(self.env, MODEL),
            readable_refs=permissions.readable_references(self.env, MODEL),
            context_window=128_000,
            entity_refs=frozenset({"res_partner"}),
        )
        self.assertTrue(catalogue.attributes)
        self.assertIn("res_partner", catalogue.refs)
        self.assertLessEqual(len(catalogue.attributes), catalogue.budget.attributes)
        for attribute in catalogue.attributes:
            self.assertTrue(attribute.terms, f"{attribute.ref} reached the model "
                                             "with no term to name it by")

    def test_what_the_user_cannot_read_is_not_in_the_catalogue(self):
        """§5.9 on real data: the filter runs before selection, so the budget is
        never spent on attributes that are then removed."""
        dictionary = Dictionary.build(l0.generate(self.env, [MODEL]))
        readable = permissions.readable_references(self.env, MODEL)
        restricted = frozenset(list(sorted(readable))[:5])
        catalogue = build.build(
            dictionary, entity="res_partner",
            attributes=l0.attribute_descriptors(self.env, MODEL),
            readable_refs=restricted, context_window=128_000,
        )
        for attribute in catalogue.attributes:
            self.assertIn(attribute.ref, restricted)
        self.assertTrue(catalogue.excluded_for_permissions)
