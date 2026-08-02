"""Exposure, budget, the three phases, assembly and coverage."""

from __future__ import annotations

import unittest

from ..catalogue import build, coverage, exposure, phases
from ..catalogue.exposure import Attribute
from ..dictionary.store import Dictionary
from .. import platform_types


def naming(ref: str, terms: list[str], level: str = "L0") -> dict:
    return {"type": "T1", "level": level, "ref": ref, "terms": terms}


def category(ref: str, entity: str, terms: list[str], condition: dict) -> dict:
    return {"type": "T5", "level": "L1", "ref": ref, "entity": entity,
            "terms": terms, "condition": condition, "version": "1"}


ENTITIES = frozenset({"ordini_vendita", "ordini_acquisto", "fatture_cliente", "clienti"})


def dictionary_of_orders() -> Dictionary:
    return Dictionary.build([
        naming("ordini_vendita", ["ordini", "ordini di vendita"]),
        naming("ordini_acquisto", ["ordini di acquisto", "acquisti"]),
        naming("fatture_cliente", ["fatture"]),
        naming("clienti", ["clienti"]),
        naming("ordini_vendita.importo_totale", ["importo", "totale"]),
        naming("ordini_vendita.stato", ["stato"]),
        naming("ordini_vendita.cliente", ["cliente"]),
        {"type": "T2", "level": "L0", "ref": "ordini_vendita.stato",
         "value": "sale", "terms": ["confermato", "confermati"]},
        category("ordini_vendita.confermati", "ordini_vendita", ["confermati"],
                 {"kind": "in", "field": "state", "values": ["sale"]}),
        category("ordini_vendita.sottoscorta", "ordini_vendita", ["sottoscorta"],
                 {"kind": "compare_field", "field": "qty_available",
                  "operator": "lt", "other_field": "reordering_min"}),
    ])


# ---------------------------------------------------------------------------
# Exposure (§5.3)
# ---------------------------------------------------------------------------

class TestExposureRules(unittest.TestCase):
    def test_the_customer_decides_first(self):
        for declared in (True, False):
            with self.subTest(l2_exposed=declared):
                decision = exposure.decide(Attribute(
                    name="message_ids", label="Messaggi", type="one2many",
                    is_technical_mixin=True, l2_exposed=declared,
                ))
                self.assertEqual(decision.exposed, declared)
                self.assertEqual(decision.rule, "l2_declared")

    def test_the_nine_rules_in_order(self):
        cases = (
            ("system_field", False, Attribute("create_uid", "Creato da", "many2one",
                                              is_system=True)),
            ("technical_mixin", False, Attribute("message_ids", "Messaggi", "one2many",
                                                 is_technical_mixin=True)),
            ("unqueryable_type", False, Attribute("logo", "Logo", "binary")),
            ("not_stored_not_searchable", False, Attribute(
                "margine", "Margine", "float", stored=False, searchable=False)),
            ("no_usable_label", False, Attribute("x_studio_1", "x_studio_1", "char")),
            ("l1_relevant", True, Attribute("amount_total", "Totale", "float",
                                            l1_relevant=True)),
            ("in_default_views", True, Attribute("partner_id", "Cliente", "many2one",
                                                 in_default_views=True)),
            ("residual", True, Attribute("note", "Note interne", "text")),
        )
        for rule, expected, attribute in cases:
            with self.subTest(rule=rule):
                decision = exposure.decide(attribute)
                self.assertEqual(decision.rule, rule)
                self.assertEqual(decision.exposed, expected)

    def test_a_computed_unstored_field_never_reaches_the_catalogue(self):
        """§5.3 rule 5 turns a late failure into a non-possibility.

        An unstored computed field cannot be filtered or ordered by the ORM. In the
        catalogue the model could use it legitimately and the failure would surface
        only at execution, as an incomprehensible error after a wait.
        """
        decision = exposure.decide(Attribute("margine", "Margine", "float",
                                             stored=False, searchable=False))
        self.assertFalse(decision.exposed)

    def test_an_unstored_but_searchable_field_survives(self):
        decision = exposure.decide(Attribute("ricerca", "Ricerca", "char",
                                             stored=False, searchable=True))
        self.assertTrue(decision.exposed)

    def test_default_views_outrank_the_residuals(self):
        ordered = exposure.exposed([
            Attribute("note", "Note", "text"),
            Attribute("partner_id", "Cliente", "many2one", in_default_views=True),
        ])
        self.assertEqual(ordered[0].attribute.name, "partner_id")

    def test_historical_use_promotes_a_residual(self):
        """§5.4 — the attributes users name most become the ones offered first."""
        ordered = exposure.exposed([
            Attribute("aaa", "Primo", "char"),
            Attribute("zzz", "Ultimo", "char", historical_uses=40),
        ])
        self.assertEqual(ordered[0].attribute.name, "zzz")


class TestBudget(unittest.TestCase):
    def test_a_wide_window_hits_the_ceiling(self):
        budget = exposure.attribute_budget(200_000)
        self.assertEqual(budget.attributes, exposure.MAX_ATTRIBUTES)
        self.assertEqual(budget.reason, "ceiling")

    def test_a_narrow_window_derives_a_smaller_budget(self):
        """D79 — the failure this prevents looks like a model defect and is a
        configuration defect: the catalogue we built was complete, the catalogue the
        model saw was cut in half."""
        budget = exposure.attribute_budget(6_000)
        self.assertLess(budget.attributes, exposure.MAX_ATTRIBUTES)
        self.assertGreater(budget.attributes, exposure.MIN_ATTRIBUTES)
        self.assertEqual(budget.reason, "window")

    def test_a_tiny_window_hits_the_floor(self):
        budget = exposure.attribute_budget(2_000)
        self.assertEqual(budget.attributes, exposure.MIN_ATTRIBUTES)
        self.assertEqual(budget.reason, "floor")

    def test_no_declared_window_falls_to_the_floor(self):
        self.assertEqual(exposure.attribute_budget(0).reason, "floor")

    def test_the_budget_grows_with_the_window(self):
        sizes = [exposure.attribute_budget(w).attributes for w in (4_000, 6_000, 16_000)]
        self.assertEqual(sizes, sorted(sizes))

    def test_truncation_is_counted_not_swallowed(self):
        """§6.4 watches *refusals for budget*: it is what tells us 60 is wrong."""
        decisions = exposure.exposed([
            Attribute(f"f{index:02d}", f"Campo {index}", "char") for index in range(20)
        ])
        kept, refused = exposure.within_budget(decisions, exposure.attribute_budget(2_000))
        self.assertEqual(len(kept), exposure.MIN_ATTRIBUTES)
        self.assertEqual(refused, 20 - exposure.MIN_ATTRIBUTES)


# ---------------------------------------------------------------------------
# Phase A (§5.5, D33)
# ---------------------------------------------------------------------------

class TestPhaseA(unittest.TestCase):
    def index(self):
        return dictionary_of_orders().term_index()

    def determine(self, request: str, **kwargs) -> phases.PhaseA:
        return phases.determine_entity(
            request, self.index(), entity_refs=ENTITIES, **kwargs)

    def test_a_clear_request_resolves_without_the_model(self):
        outcome = self.determine("mostrami i clienti")
        self.assertTrue(outcome.resolved)
        self.assertEqual(outcome.entity, "clienti")

    def test_a_longer_term_resolves_to_the_specific_entity(self):
        outcome = self.determine("gli ordini di acquisto di marzo")
        self.assertTrue(outcome.resolved)
        self.assertEqual(outcome.entity, "ordini_acquisto")

    def test_nothing_matching_goes_to_phase_b(self):
        outcome = self.determine("mostrami le pratiche ferme")
        self.assertEqual(outcome.outcome, phases.NO_CANDIDATE)
        self.assertIsNone(outcome.entity)
        self.assertFalse(outcome.needs_clarification,
                         "nothing matched: the next step is the model, not a question")

    def test_two_candidates_too_close_produce_a_clarification(self):
        """D33 — the margin is what stops the fast path guessing in silence.

        With *"ordine"* matching sales orders and purchase orders equally well,
        taking the best by a hair is the shape of R1 that no error surfaces.
        """
        local = Dictionary.build([
            naming("ordini_vendita", ["ordini"]),
            naming("ordini_acquisto", ["ordini"]),
        ])
        outcome = phases.determine_entity(
            "mostrami gli ordini", local.term_index(),
            entity_refs=frozenset({"ordini_vendita", "ordini_acquisto"}),
        )
        self.assertTrue(outcome.needs_clarification)
        self.assertIsNone(outcome.entity)
        self.assertIn("margin", outcome.explain())

    def test_a_weak_match_alone_is_not_enough(self):
        outcome = self.determine("mostrami i clienti", threshold=1.01)
        self.assertEqual(outcome.outcome, phases.BELOW_THRESHOLD)

    def test_raising_the_threshold_stops_the_fast_path_resolving_typos(self):
        """The threshold's real job: at 0.90 the approximate tier cannot decide.

        A legitimate configuration for an installation that would rather ask than
        guess — and the reason the value is a parameter measured on the corpus rather
        than a constant argued in a document.
        """
        self.assertEqual(self.determine("mostrami i clineti").entity, "clienti")
        self.assertIsNone(self.determine("mostrami i clineti", threshold=0.90).entity)

    def test_an_attribute_term_never_determines_the_entity(self):
        """Phase A's job is the entity; matching a field name here would answer a
        question nobody asked."""
        outcome = self.determine("mostrami lo stato")
        self.assertIsNone(outcome.entity)

    def test_an_attribute_term_outranks_an_entity_on_the_same_span(self):
        """The guard the corpus asked for, and the alternative it beat.

        Italian morphology collapses the attribute *cliente* into the entity
        *clienti*: same base form. In *"fatt. cliente raggruppati per cliente"* —
        a request whose head noun the user abbreviated — the only surviving match
        used to be *cliente*, and phase A resolved `clienti`: a different, plausible
        entity, no error anywhere. On the corpus that shape was **every** residual
        wrong determination.

        The obvious alternative was raising the threshold to 1.00, which removes them
        by removing the base-form tier entirely — measured cost 78.4% resolved against
        86.2% with the guard, both at zero wrong determinations.
        """
        local = Dictionary.build([
            naming("fatture_cliente", ["fatture cliente"]),
            naming("clienti", ["clienti"]),
            naming("fatture_cliente.cliente", ["cliente"], level="L1"),
        ])
        outcome = phases.determine_entity(
            "elenca fatuere raggruppati per cliente", local.term_index(),
            entity_refs=frozenset({"fatture_cliente", "clienti"}),
        )
        self.assertIsNone(
            outcome.entity,
            "the head noun is damaged beyond recovery: the honest outcome is the "
            "model, not a plausible other entity",
        )

    def test_the_guard_does_not_block_a_legitimate_entity(self):
        """*"Mostrami i clienti"* must still resolve: the entity term matches the
        span exactly, the attribute term only by base form."""
        local = Dictionary.build([
            naming("clienti", ["clienti"]),
            naming("fatture_cliente.cliente", ["cliente"], level="L1"),
        ])
        outcome = phases.determine_entity(
            "mostrami i clienti", local.term_index(),
            entity_refs=frozenset({"clienti"}),
        )
        self.assertEqual(outcome.entity, "clienti")

    def test_perturbations_of_the_corpus_still_resolve(self):
        """D83 produces lowercased, accent-stripped and mistyped variants."""
        for request in ("MOSTRAMI I CLIENTI", "mostrami i clienti!", "mostrami i clineti"):
            with self.subTest(request=request):
                self.assertEqual(self.determine(request).entity, "clienti")

    def test_the_outcome_explains_itself(self):
        self.assertIn("clienti", self.determine("i clienti").explain())


class TestPhaseB(unittest.TestCase):
    def test_the_catalogue_holds_entity_names_only(self):
        """§5.6 — hundreds of short entries, and the task is picking one from a list."""
        catalogue = phases.entity_catalogue(dictionary_of_orders(), entity_refs=ENTITIES)
        self.assertEqual(catalogue.refs, ENTITIES)
        for _, terms in catalogue.entities:
            self.assertTrue(terms)


# ---------------------------------------------------------------------------
# Phase C assembly (§5.7, §5.9, D87)
# ---------------------------------------------------------------------------

class TestPhaseC(unittest.TestCase):
    def attributes(self) -> list[Attribute]:
        return [
            Attribute("importo_totale", "Totale", "float", in_default_views=True),
            Attribute("stato", "Stato", "selection", in_default_views=True),
            Attribute("cliente", "Cliente", "many2one", in_default_views=True),
            Attribute("create_uid", "Creato da", "many2one", is_system=True),
            Attribute("message_ids", "Messaggi", "one2many", is_technical_mixin=True),
        ]

    def readable(self, *refs: str) -> frozenset[str]:
        return frozenset(refs)

    def build(self, readable: frozenset[str], context_window: int = 128_000):
        return build.build(
            dictionary_of_orders(),
            entity="ordini_vendita",
            attributes=self.attributes(),
            readable_refs=readable,
            context_window=context_window,
            entity_refs=ENTITIES,
        )

    def all_readable(self) -> frozenset[str]:
        return self.readable(
            "ordini_vendita.importo_totale", "ordini_vendita.stato",
            "ordini_vendita.cliente", "ordini_vendita.create_uid",
            "ordini_vendita.message_ids", "ordini_vendita.state",
            "ordini_vendita.qty_available", "ordini_vendita.reordering_min",
        )

    def test_no_selection_in_phase_c(self):
        """D32 — every exposed attribute is present, so coverage on attributes is
        exact by construction and the only point of loss is the entity."""
        catalogue = self.build(self.all_readable())
        refs = {attribute.ref for attribute in catalogue.attributes}
        self.assertEqual(refs, {
            "ordini_vendita.importo_totale", "ordini_vendita.stato",
            "ordini_vendita.cliente",
        })
        self.assertEqual(catalogue.refused_for_budget, 0)

    def test_entity_names_are_present_even_in_phase_c(self):
        """§5.8 — so the conversation can change subject."""
        catalogue = self.build(self.all_readable())
        self.assertEqual({ref for ref, _ in catalogue.entity_names}, ENTITIES)

    def test_enumerated_values_travel_without_a_single_record(self):
        """§3.3, A6 — schema metadata, not content."""
        catalogue = self.build(self.all_readable())
        state = next(a for a in catalogue.attributes if a.ref == "ordini_vendita.stato")
        self.assertEqual(state.values, (("sale", ("confermato", "confermati")),))

    def test_permissions_are_applied_before_selection(self):
        """§5.9, and the reason the order is a security property.

        The budget below fits exactly two attributes. Of the three exposed ones, one
        is unreadable. Filtering first spends the budget on the two the user can see;
        filtering afterwards would have spent it on three and delivered one, and the
        lost coverage would have been blamed on the budget.
        """
        readable = self.readable("ordini_vendita.stato", "ordini_vendita.cliente")
        catalogue = build.build(
            dictionary_of_orders(),
            entity="ordini_vendita",
            attributes=self.attributes(),
            readable_refs=readable,
            context_window=128_000,
            entity_refs=ENTITIES,
        )
        refs = {attribute.ref for attribute in catalogue.attributes}
        self.assertEqual(refs, {"ordini_vendita.stato", "ordini_vendita.cliente"})
        self.assertIn("ordini_vendita.importo_totale", catalogue.excluded_for_permissions)

    def test_a_category_the_user_cannot_read_is_excluded(self):
        """V-D87-1 — otherwise D87 opens a path to unauthorised data with normal
        accuracy and normal latency."""
        readable = self.readable(
            "ordini_vendita.stato", "ordini_vendita.cliente",
            "ordini_vendita.importo_totale", "ordini_vendita.state",
        )
        catalogue = self.build(readable)
        refs = {category.ref for category in catalogue.categories}
        self.assertIn("ordini_vendita.confermati", refs)
        self.assertNotIn(
            "ordini_vendita.sottoscorta", refs,
            "the category compares qty_available with reordering_min, and this user "
            "can read neither",
        )
        dropped = dict(catalogue.excluded_categories)
        self.assertIn("ordini_vendita.sottoscorta", dropped)
        self.assertIn("reordering_min", dropped["ordini_vendita.sottoscorta"])

    def test_the_second_implied_field_is_what_excludes_it(self):
        """The exact hole the corpus lexicon had: declaring only the first field.

        With `qty_available` readable and `reordering_min` not, a declared list would
        have admitted the category. The derived set refuses it.
        """
        readable = self.all_readable() - {"ordini_vendita.reordering_min"}
        catalogue = self.build(readable)
        refs = {category.ref for category in catalogue.categories}
        self.assertNotIn("ordini_vendita.sottoscorta", refs)

    def test_a_category_without_a_condition_fails_safe(self):
        dictionary = Dictionary.build([
            naming("ordini_vendita", ["ordini"]),
            {"type": "T5", "level": "L1", "ref": "ordini_vendita.misteriosi",
             "entity": "ordini_vendita", "terms": ["misteriosi"],
             "condition": {"kind": "all", "conditions": [{"kind": "is_set",
                                                          "field": "state"}]},
             "version": "1"},
        ])
        catalogue = build.build(
            dictionary, entity="ordini_vendita", attributes=[],
            readable_refs=frozenset(), context_window=128_000,
        )
        self.assertEqual(catalogue.categories, ())
        self.assertTrue(catalogue.excluded_categories)

    def test_cost_class_and_time_dependence_travel_with_the_catalogue(self):
        """V-D87-2 and V-D87-3 — computed once, where the condition is."""
        dictionary = Dictionary.build([
            naming("clienti", ["clienti"]),
            category("clienti.importanti", "clienti", ["importanti"],
                     {"kind": "aggregate", "entity": "fatture_cliente",
                      "function": "sum", "field": "imponibile",
                      "operator": "gt", "value": 50000, "window_days": 365}),
        ])
        catalogue = build.build(
            dictionary, entity="clienti", attributes=[],
            readable_refs=frozenset({"fatture_cliente.imponibile"}),
            context_window=128_000,
        )
        self.assertEqual(len(catalogue.categories), 1)
        entry = catalogue.categories[0]
        self.assertEqual(entry.cost_class, "aggregate")
        self.assertTrue(entry.time_dependent)

    def test_the_budget_truncates_and_says_so(self):
        catalogue = self.build(self.all_readable(), context_window=2_000)
        self.assertEqual(catalogue.budget.reason, "floor")
        self.assertLessEqual(len(catalogue.attributes), catalogue.budget.attributes)

    def test_the_exposure_rule_of_every_attribute_is_recorded(self):
        """§6.3 — a low attribute coverage is a diagnosis about the rules, and the
        diagnosis needs to know which rule fired."""
        catalogue = self.build(self.all_readable())
        rules = dict(catalogue.exposure_rules)
        self.assertEqual(rules["ordini_vendita.stato"], "in_default_views")


# ---------------------------------------------------------------------------
# Coverage (§6, D34)
# ---------------------------------------------------------------------------

class TestCoverage(unittest.TestCase):
    def test_the_quantifier_is_all(self):
        """One reference missing out of five is an uncovered case: the correct
        interpretation stays unreachable."""
        result = coverage.case_coverage(
            frozenset({"a", "a.b", "a.c", "a.d", "a.e"}),
            frozenset({"a", "a.b", "a.c", "a.d"}),
        )
        self.assertFalse(result.covered)
        self.assertEqual(result.missing, ("a.e",))

    def test_the_decomposition_separates_the_two_causes(self):
        entity_missing = coverage.case_coverage(
            frozenset({"ordini_vendita", "ordini_vendita.stato"}),
            frozenset({"ordini_vendita.stato"}),
        )
        self.assertFalse(entity_missing.entity_covered)
        self.assertTrue(entity_missing.attributes_covered)

        attribute_missing = coverage.case_coverage(
            frozenset({"ordini_vendita", "ordini_vendita.stato"}),
            frozenset({"ordini_vendita"}),
        )
        self.assertTrue(attribute_missing.entity_covered)
        self.assertFalse(attribute_missing.attributes_covered)

    def test_the_report_keeps_the_enrichment_queue_in_frequency_order(self):
        report = coverage.Report()
        for _ in range(3):
            report.add(coverage.case_coverage(frozenset({"a.b"}), frozenset()))
        report.add(coverage.case_coverage(frozenset({"a.c"}), frozenset()))
        report.add(coverage.case_coverage(frozenset({"a.d"}), frozenset({"a.d"})))
        self.assertEqual(report.cases, 5)
        self.assertEqual(report.covered, 1)
        self.assertEqual(report.missing.most_common(1), [("a.b", 3)])

    def test_the_threshold_of_d34_is_on_the_decomposed_measure(self):
        report = coverage.Report()
        for _ in range(99):
            report.add(coverage.case_coverage(frozenset({"a", "a.b"}),
                                              frozenset({"a", "a.b"})))
        report.add(coverage.case_coverage(frozenset({"a", "a.b"}), frozenset({"a.b"})))
        self.assertTrue(report.meets(0.99))
        self.assertFalse(report.meets(1.0))



# ---------------------------------------------------------------------------
# Time anchor (D110)
# ---------------------------------------------------------------------------

class TestTimeAnchor(unittest.TestCase):
    """L'ancora nasce dagli attributi che sono sopravvissuti ai diritti (D110)."""

    def _dictionary(self):
        return Dictionary.build([
            naming("ordini_vendita.data_ordine", ["data ordine", "data"]),
            naming("ordini_vendita.data_consegna", ["data consegna"]),
            naming("ordini_vendita.importo_totale", ["totale", "importo"]),
        ])

    def _attributes(self):
        return [
            Attribute(name="data_ordine", label="Data ordine", type="date",
                      in_default_views=True),
            Attribute(name="data_consegna", label="Data consegna", type="date",
                      in_default_views=True),
            Attribute(name="importo_totale", label="Totale", type="number",
                      in_default_views=True),
        ]

    def test_two_dates_make_the_anchor_a_question(self):
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=self._attributes(),
            readable_refs=frozenset({"ordini_vendita.data_ordine",
                                     "ordini_vendita.data_consegna",
                                     "ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertEqual(
            catalogue.time_anchor,
            {"choices": ["ordini_vendita.data_consegna",
                         "ordini_vendita.data_ordine"]})

    def test_a_date_the_user_cannot_read_is_not_offered(self):
        """La garanzia che rende sicuro il suggerimento: l'ancora nasce dopo il
        filtro dei permessi (§5.9), quindi non puo' nominare cio' che l'utente non
        vede. Senza questo test la regola potrebbe leggere gli attributi in ingresso,
        invece di quelli sopravvissuti, e nessuno se ne accorgerebbe."""
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=self._attributes(),
            readable_refs=frozenset({"ordini_vendita.data_ordine",
                                     "ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertEqual(catalogue.time_anchor,
                         {"ref": "ordini_vendita.data_ordine"})

    def test_no_date_exposed_is_no_anchor(self):
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=[Attribute(name="importo_totale", label="Totale",
                                  type="number", in_default_views=True)],
            readable_refs=frozenset({"ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertIsNone(catalogue.time_anchor)


if __name__ == "__main__":
    unittest.main()


class TestLaDataDiCreazione(unittest.TestCase):
    """`create_date` e' una domanda di lavoro, non un campo tecnico (**D117**).

    La regola 2 di §5.3 esclude i campi che Odoo mette su ogni modello. Li trattava
    tutti allo stesso modo, ma non lo sono: `id` e `create_uid` non significano niente
    per una persona, mentre *«quando e' stato creato»* e' la prima cosa che si intende
    con «i lead di quest'anno».

    Misurato sul campo: a quella domanda l'ancora del tempo (**D110**) offriva chiusura,
    conversione, scadenza e assegnazione — quattro date, e non quella giusta.

    Il controllo e' sull'elenco di `l0`, che e' dove la regola vive davvero:
    `exposure.decide` riceve gia' il verdetto in un campo booleano, quindi provarlo li'
    sarebbe passato per il motivo sbagliato.
    """

    def test_creation_date_is_no_longer_a_system_field(self):
        self.assertNotIn("create_date", platform_types.SYSTEM_FIELDS)

    def test_the_other_system_fields_stay_out(self):
        """L'altra meta': togliere uno dal gruppo non apre il gruppo. Senza questo,
        svuotare l'elenco per sbaglio passerebbe inosservato."""
        for nome in ("id", "create_uid", "write_uid", "display_name", "__last_update"):
            with self.subTest(campo=nome):
                self.assertIn(nome, platform_types.SYSTEM_FIELDS)

    def test_an_attribute_marked_system_is_still_refused(self):
        """E la regola che li scarta continua a scartarli."""
        decisione = exposure.decide(Attribute(
            name="create_uid", label="Creato da", type="relation", is_system=True))
        self.assertFalse(decisione.exposed)
        self.assertEqual(decisione.rule, "system_field")
