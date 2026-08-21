"""The Resolver and the contextual validation levels."""

from __future__ import annotations

import unittest
from datetime import date, datetime

from ..resolution import calendar as calendar_module
from ..resolution import resolver as resolver_module
from ..resolution.plan import Binding
from ..validation import contextual

#: A fixed reference instant. Everything below is asserted against it, which is the
#: whole point of §9.2's requirement that the corpus run at a fixed moment.
WEDNESDAY = datetime(2026, 7, 15, 10, 30)
CALENDAR_YEAR = calendar_module.Instant(now=WEDNESDAY)
#: A company whose fiscal year starts on 1 July — the case §9.2 warns about.
FISCAL_JULY = calendar_module.Instant(
    now=WEDNESDAY, fiscal_year_start_month=7, fiscal_year_start_day=1)


def temporal(expression: str, **extra) -> dict:
    return {"kind": "temporal", "expression": expression, **extra}


class TestCalendar(unittest.TestCase):
    def resolve(self, expression: str, instant=CALENDAR_YEAR, **extra):
        return calendar_module.resolve(temporal(expression, **extra), instant)

    def test_punctual(self):
        self.assertEqual(self.resolve("today"), calendar_module.Range(
            date(2026, 7, 15), date(2026, 7, 16)))
        self.assertEqual(self.resolve("yesterday").start, date(2026, 7, 14))

    def test_current_month(self):
        window = self.resolve("current_month")
        self.assertEqual(window.start, date(2026, 7, 1))
        self.assertEqual(window.end, date(2026, 8, 1))

    def test_previous_month_does_not_overflow(self):
        """31 March minus one month is 28 February, not 3 March."""
        march = calendar_module.Instant(now=datetime(2026, 3, 31, 9, 0))
        window = calendar_module.resolve(temporal("previous_month"), march)
        self.assertEqual(window.start, date(2026, 2, 1))
        self.assertEqual(window.end, date(2026, 3, 1))

    def test_current_week_respects_the_first_weekday(self):
        monday = calendar_module.Instant(now=WEDNESDAY, first_weekday=0)
        sunday = calendar_module.Instant(now=WEDNESDAY, first_weekday=6)
        self.assertEqual(calendar_module.resolve(temporal("current_week"), monday).start,
                         date(2026, 7, 13))
        self.assertEqual(calendar_module.resolve(temporal("current_week"), sunday).start,
                         date(2026, 7, 12))

    def test_the_fiscal_year_is_not_the_calendar_year(self):
        """§9.2's warning, as an assertion.

        *"This year"* in a company whose year starts in July is July to June.
        Returning January to December would produce a wrong number of perfectly
        credible appearance — R1 on aggregated data.
        """
        calendar_window = self.resolve("current_year", CALENDAR_YEAR)
        fiscal_window = self.resolve("current_year", FISCAL_JULY)
        self.assertEqual(calendar_window.start, date(2026, 1, 1))
        self.assertEqual(fiscal_window.start, date(2026, 7, 1))
        self.assertEqual(fiscal_window.end, date(2027, 7, 1))

    def test_a_date_before_the_fiscal_start_belongs_to_the_previous_year(self):
        june = calendar_module.Instant(
            now=datetime(2026, 6, 30, 9, 0), fiscal_year_start_month=7,
            fiscal_year_start_day=1)
        self.assertEqual(calendar_module.fiscal_year_start(june), date(2025, 7, 1))

    # --- D141: named periods ------------------------------------------------

    def test_a_named_month_is_that_month(self):
        """*"In January"* — the case that answered with August.

        The reference instant is 15 July 2026, so *"January"* without a year is
        January 2026: the month inside the fiscal year in progress.
        """
        window = self.resolve("month_of_year", n=1)
        self.assertEqual(window.start, date(2026, 1, 1))
        self.assertEqual(window.end, date(2026, 2, 1))

    def test_a_named_month_takes_the_year_the_sentence_gave(self):
        """*"In March 2026"* — the worst of the four failures of §46.1, because the
        user had said the year and the product still answered August."""
        window = self.resolve("month_of_year", n=3, year=2025)
        self.assertEqual(window.start, date(2025, 3, 1))
        self.assertEqual(window.end, date(2025, 4, 1))

    def test_a_named_quarter_is_that_quarter(self):
        """*"In the first quarter"* — 26 records of the third quarter, before D141."""
        window = self.resolve("quarter_of_year", n=1)
        self.assertEqual(window.start, date(2026, 1, 1))
        self.assertEqual(window.end, date(2026, 4, 1))
        fourth = self.resolve("quarter_of_year", n=4)
        self.assertEqual(fourth.start, date(2026, 10, 1))
        self.assertEqual(fourth.end, date(2027, 1, 1))

    def test_a_named_half_is_six_months(self):
        """*"Nel secondo semestre"* — la frase che è **peggiorata** prima di essere
        riparata: era `not_understood`, e con i trimestri disponibili e i semestri no
        il modello l'ha risposta col secondo **trimestre** (§46.6)."""
        first = self.resolve("half_of_year", n=1)
        self.assertEqual(first.start, date(2026, 1, 1))
        self.assertEqual(first.end, date(2026, 7, 1))
        second = self.resolve("half_of_year", n=2)
        self.assertEqual(second.start, date(2026, 7, 1))
        self.assertEqual(second.end, date(2027, 1, 1))

    def test_a_named_half_is_two_quarters(self):
        """La proprietà che tiene insieme i due simboli: se un giorno divergono, il
        prodotto risponderà due periodi diversi alla stessa domanda detta in due modi."""
        half = self.resolve("half_of_year", n=2)
        third = self.resolve("quarter_of_year", n=3)
        fourth = self.resolve("quarter_of_year", n=4)
        self.assertEqual(half.start, third.start)
        self.assertEqual(half.end, fourth.end)

    def test_a_named_year_is_that_year(self):
        """*"In 2025"* — answered with the whole of 2026 before D141."""
        window = self.resolve("year_of", n=2025)
        self.assertEqual(window.start, date(2025, 1, 1))
        self.assertEqual(window.end, date(2026, 1, 1))

    def test_a_named_period_follows_the_fiscal_year_like_every_other(self):
        """D141 with D91's argument: in a company whose year starts in July, the
        **first quarter** is July to September and *"January"* is the January of the
        year in progress — which, on 15 July 2026, is January **2027**.

        Answering with the calendar quarter would produce a wrong number of perfectly
        credible appearance, which is the whole reason `current_year` is fiscal.
        """
        quarter = self.resolve("quarter_of_year", FISCAL_JULY, n=1)
        self.assertEqual(quarter.start, date(2026, 7, 1))
        self.assertEqual(quarter.end, date(2026, 10, 1))
        january = self.resolve("month_of_year", FISCAL_JULY, n=1)
        self.assertEqual(january.start, date(2027, 1, 1))
        self.assertEqual(january.end, date(2027, 2, 1))

    def test_a_named_year_with_a_fiscal_year_is_that_fiscal_year(self):
        """*"In 2025"* in a July company is the 2025 **exercise**: July 2025 to June
        2026. It is the same reading `current_year` already gives that company."""
        window = self.resolve("year_of", FISCAL_JULY, n=2025)
        self.assertEqual(window.start, date(2025, 7, 1))
        self.assertEqual(window.end, date(2026, 7, 1))

    def test_a_month_that_is_not_a_month_does_not_reach_a_range(self):
        """Level 2 refuses `n=13`; this is the second lock, on the Resolver's side.

        A symbol whose parameter is out of range has no window, and returning a
        plausible one — December, say — would be the failure mode of §46.1 all over
        again.
        """
        for expression, out_of_range in (("month_of_year", 13), ("quarter_of_year", 0)):
            with self.subTest(expression=expression):
                with self.assertRaises(calendar_module.UnresolvableExpression):
                    self.resolve(expression, n=out_of_range)

    def test_year_to_date_is_the_partial_year(self):
        """D91 and V-D91-1: from the fiscal start to today, not the whole year."""
        window = self.resolve("year_to_date", FISCAL_JULY)
        self.assertEqual(window.start, date(2026, 7, 1))
        self.assertEqual(window.end, date(2026, 7, 16))
        self.assertNotEqual(window, self.resolve("current_year", FISCAL_JULY))

    def test_parametric_expressions(self):
        self.assertEqual(self.resolve("last_n_days", n=30).start, date(2026, 6, 15))
        self.assertEqual(self.resolve("last_n_months", n=3).start, date(2026, 4, 15))

    def test_absolute_range_includes_the_day_the_user_said(self):
        window = self.resolve("absolute_range", **{"from": "2026-03-01", "to": "2026-04-15"})
        self.assertEqual(window.start, date(2026, 3, 1))
        self.assertEqual(window.end, date(2026, 4, 16))
        self.assertIn(date(2026, 4, 15), window)

    def test_an_inverted_range_is_refused(self):
        with self.assertRaises(calendar_module.UnresolvableExpression):
            self.resolve("absolute_range", **{"from": "2026-04-15", "to": "2026-03-01"})

    def test_resolution_is_a_function_of_the_instant(self):
        """The property the corpus depends on: same instant, same answer, always."""
        for expression in ("current_month", "current_year", "year_to_date"):
            with self.subTest(expression=expression):
                self.assertEqual(self.resolve(expression), self.resolve(expression))

    def test_the_description_shows_the_resolved_period(self):
        """D67 — *"this month"* confirms itself; only the resolved period is
        verifiable, and it is what makes a non-calendar fiscal year catchable."""
        self.assertEqual(
            calendar_module.describe(temporal("current_month"), CALENDAR_YEAR),
            "2026-07-01 - 2026-07-31",
        )

    def test_the_description_says_which_side_of_the_period_was_taken(self):
        """**Visto sul campo il 3 agosto 2026, ed e' il difetto peggiore dei tre di
        quel turno.** Lo stato diceva `after current_year`, il dominio eseguito era
        `create_date >= 2026-12-31 23:00:00` — cioe' *dopo la fine dell'anno*, zero
        record — e l'interpretazione sopra la risposta diceva
        *«crm_lead.create_date: 2026-01-01 - 2026-12-31»*.

        Cioe' il prodotto mostrava **la finestra dell'espressione** invece
        dell'insieme che aveva davvero interrogato. L'utente leggeva l'anno intero e
        riceveva nessun record: non aveva nessun modo di capire perche'. E' la forma
        pura del rischio di **D2** (il cancello che vieta le scritture finche' la Fase 2
        non e' misurata), una risposta sbagliata con l'aria di essere giusta — con
        l'aggravante che qui il pezzo che avrebbe dovuto spiegarla la nascondeva.

        Il predicato fa parte di cosa e' stato chiesto, quindi entra nella descrizione.
        """
        self.assertEqual(
            calendar_module.describe(temporal("current_year"), CALENDAR_YEAR,
                                     predicate="after"),
            "> 2026-12-31")
        self.assertEqual(
            calendar_module.describe(temporal("current_year"), CALENDAR_YEAR,
                                     predicate="before"),
            "< 2026-01-01")

    def test_a_period_taken_whole_is_described_as_before(self):
        """`on` e `within` chiedono la stessa cosa — se la data e' dentro — e la
        finestra e' la risposta giusta per tutt'e due."""
        for predicate in ("on", "within"):
            with self.subTest(predicate=predicate):
                self.assertEqual(
                    calendar_module.describe(temporal("current_month"), CALENDAR_YEAR,
                                             predicate=predicate),
                    "2026-07-01 - 2026-07-31")


def bindings_of_orders() -> dict[str, Binding]:
    return {
        "ordini_vendita": Binding(kind="attribute", field="", type="entity"),
        "ordini_vendita.data_ordine": Binding("attribute", "date_order", "date"),
        "ordini_vendita.importo_totale": Binding("attribute", "amount_total", "float"),
        "ordini_vendita.stato": Binding("attribute", "state", "selection"),
        "ordini_vendita.cliente": Binding("attribute", "partner_id", "many2one"),
        "ordini_vendita.margine": Binding("attribute", "margin", "float", sortable=False),
        "ordini_vendita.confermati": Binding(
            kind="category", domain=(("state", "=", "sale"),)),
    }


def state_with(**sections) -> dict:
    state = {
        "dsl_version": "1.0",
        "target": {"ref": "ordini_vendita", "origin": "user"},
        "limit": {"value": 80, "origin": "default"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }
    state.update(sections)
    return state


def condition(ref: str, predicate: str, value=None, identifier="c1") -> dict:
    node = {"id": identifier, "ref": ref, "predicate": predicate, "origin": "user"}
    if value is not None:
        node["value"] = value
    return node


class TestResolver(unittest.TestCase):
    def resolve(self, state, **kwargs):
        return resolver_module.resolve(
            state, bindings=bindings_of_orders(), instant=CALENDAR_YEAR,
            model="sale.order", **kwargs)

    def test_a_temporal_condition_becomes_a_half_open_domain(self):
        outcome = self.resolve(state_with(filter=condition(
            "ordini_vendita.data_ordine", "within", temporal("current_month"))))
        self.assertTrue(outcome.resolved)
        self.assertEqual(outcome.plan.domain, (
            "&", ("date_order", ">=", "2026-07-01"), ("date_order", "<", "2026-08-01")))

    def test_the_resolved_period_travels_for_the_interpretation(self):
        outcome = self.resolve(state_with(filter=condition(
            "ordini_vendita.data_ordine", "within", temporal("current_month"))))
        self.assertEqual(outcome.plan.resolved_periods,
                         (("ordini_vendita.data_ordine", "2026-07-01 - 2026-07-31"),))

    def test_a_category_is_expanded_here_and_not_before(self):
        """V-D87-3 — the Applicator never expands one; its condition may depend on
        the clock, and a state carrying a resolved "today" is a snapshot."""
        outcome = self.resolve(state_with(
            filter=condition("ordini_vendita.confermati", "is_category")))
        self.assertEqual(outcome.plan.domain, (("state", "=", "sale"),))

    def test_a_conjunction_uses_odoo_prefix_notation(self):
        outcome = self.resolve(state_with(filter={"connective": "all", "conditions": [
            condition("ordini_vendita.confermati", "is_category"),
            condition("ordini_vendita.importo_totale", "greater_than",
                      {"kind": "number", "value": 1000}, "c2"),
        ]}))
        self.assertEqual(outcome.plan.domain[0], "&")
        self.assertIn(("amount_total", ">", 1000), outcome.plan.domain)

    def test_a_disjunction_and_a_negation(self):
        any_of = self.resolve(state_with(filter={"connective": "any", "conditions": [
            condition("ordini_vendita.confermati", "is_category"),
            condition("ordini_vendita.importo_totale", "less_than",
                      {"kind": "number", "value": 10}, "c2"),
        ]}))
        self.assertEqual(any_of.plan.domain[0], "|")
        negated = self.resolve(state_with(filter={"connective": "not", "conditions": [
            condition("ordini_vendita.confermati", "is_category"),
        ]}))
        self.assertEqual(negated.plan.domain[0], "!")

    def test_vagueness_is_resolved_from_the_dictionary_never_invented(self):
        """§9.3 — the model declared *that* it is approximate and *which* rule."""
        outcome = self.resolve(
            state_with(filter=condition(
                "ordini_vendita.importo_totale", "approximately",
                {"kind": "number", "value": 100000, "resolver": "approx_relative"})),
            resolvers={"approx_relative": {"kind": "relative_percent", "percent": 10}},
        )
        self.assertEqual(outcome.plan.domain, (
            "&", ("amount_total", ">=", 90000.0), ("amount_total", "<=", 110000.0)))

    def test_an_undefined_resolver_is_not_guessed(self):
        """*"I clienti importanti"* has no objective meaning: absent a defined
        resolver the correct outcome is a clarification, not a tolerance invented
        on the spot."""
        outcome = self.resolve(state_with(filter=condition(
            "ordini_vendita.importo_totale", "approximately",
            {"kind": "number", "value": 100000, "resolver": "importante"})))
        self.assertFalse(outcome.resolved)
        self.assertIn("importante", outcome.failures[0].reason)

    def test_an_unknown_reference_fails_resolution(self):
        outcome = self.resolve(state_with(filter=condition(
            "ordini_vendita.colore", "equals", {"kind": "text", "text": "rosso"})))
        self.assertFalse(outcome.resolved)
        self.assertEqual(outcome.failures[0].reference, "ordini_vendita.colore")

    def test_an_unauthorised_reference_is_indistinguishable_from_an_unknown_one(self):
        """§7.4 — no refusal may reveal that an attribute the user cannot see exists.

        The catalogue simply does not contain it, so resolution reports the same
        thing it reports for a term the dictionary never knew.
        """
        outcome = self.resolve(state_with(filter=condition(
            "ordini_vendita.margine_riservato", "greater_than",
            {"kind": "number", "value": 0})))
        self.assertFalse(outcome.resolved)
        self.assertFalse(outcome.failures[0].unauthorised,
                         "the distinction exists only in the diagnostic log")

    def test_an_unsortable_attribute_is_refused_before_the_orm_sees_it(self):
        outcome = self.resolve(state_with(order_by=[{
            "ref": "ordini_vendita.margine", "direction": "desc", "origin": "user"}]))
        self.assertFalse(outcome.resolved)
        self.assertIn("cannot be ordered", outcome.failures[0].reason)

    def test_the_plan_carries_fields_groups_order_and_limit(self):
        outcome = self.resolve(state_with(
            fields=[{"ref": "ordini_vendita.cliente", "origin": "user"}],
            group_by=[{"ref": "ordini_vendita.stato", "origin": "user"}],
            order_by=[{"ref": "ordini_vendita.data_ordine", "direction": "desc",
                       "origin": "inferred", "rule": "latest_implies_desc_by_date"}],
            limit={"value": 5, "origin": "user"},
        ))
        plan = outcome.plan
        self.assertEqual(plan.fields, ("partner_id",))
        self.assertEqual(plan.group_by, ("state",))
        self.assertEqual(plan.order, "date_order desc")
        self.assertEqual(plan.limit, 5)

    def test_resolution_is_deterministic(self):
        state = state_with(filter=condition(
            "ordini_vendita.data_ordine", "within", temporal("current_month")))
        self.assertEqual(self.resolve(state).plan, self.resolve(state).plan)


class TestContextualValidation(unittest.TestCase):
    KNOWN = frozenset({
        "ordini_vendita", "ordini_vendita.data_ordine",
        "ordini_vendita.importo_totale", "ordini_vendita.stato",
        "ordini_vendita.confermati",
    })
    TYPES = {
        "ordini_vendita.data_ordine": "date",
        "ordini_vendita.importo_totale": "number",
        "ordini_vendita.stato": "enum",
        "ordini_vendita.confermati": "category",
    }

    def codes(self, failures):
        return {failure.code for failure in failures}

    def test_level_3_reports_what_the_catalogue_does_not_contain(self):
        failures = contextual.validate_resolution(
            state_with(filter=condition("ordini_vendita.colore", "is_set")),
            known_refs=self.KNOWN)
        self.assertIn("unresolved_reference", self.codes(failures))
        self.assertIn("candidate enrichment", str(failures[0]))

    def test_level_4_refuses_a_predicate_the_type_does_not_admit(self):
        failures = contextual.validate_types(
            state_with(filter=condition("ordini_vendita.importo_totale", "contains",
                                        {"kind": "text", "text": "mille"})),
            types=self.TYPES)
        self.assertIn("predicate_type_mismatch", self.codes(failures))

    def test_level_4_admits_the_right_predicate(self):
        failures = contextual.validate_types(
            state_with(filter=condition("ordini_vendita.importo_totale", "greater_than",
                                        {"kind": "number", "value": 10})),
            types=self.TYPES)
        self.assertEqual(failures, [])

    def test_granularity_only_applies_to_dates(self):
        failures = contextual.validate_types(
            state_with(group_by=[{"ref": "ordini_vendita.stato", "origin": "user",
                                  "granularity": "month"}]),
            types=self.TYPES)
        self.assertIn("granularity_on_non_temporal", self.codes(failures))

    def test_an_aggregation_on_the_wrong_type(self):
        failures = contextual.validate_types(
            state_with(measures=[{"function": "sum", "ref": "ordini_vendita.stato",
                                  "origin": "user"}]),
            types=self.TYPES)
        self.assertIn("aggregation_type_mismatch", self.codes(failures))

    def test_count_needs_no_attribute(self):
        failures = contextual.validate_types(
            state_with(measures=[{"function": "count", "origin": "user"}]),
            types=self.TYPES)
        self.assertEqual(failures, [])

    def test_level_5_counts_the_aggregating_categories(self):
        """V-D87-2 — a category can hide a twelve-month roll-up over another entity,
        and D12 exists so that cost is known before the query runs."""
        state = state_with(filter={"connective": "all", "conditions": [
            condition("ordini_vendita.importanti", "is_category", identifier="c1"),
            condition("ordini_vendita.grossi", "is_category", identifier="c2"),
        ]})
        failures = contextual.validate_cost(state, category_costs={
            "ordini_vendita.importanti": "aggregate",
            "ordini_vendita.grossi": "aggregate",
        })
        self.assertIn("too_many_aggregate_categories", self.codes(failures))

    def test_one_aggregating_category_is_an_ordinary_question(self):
        state = state_with(filter=condition("ordini_vendita.importanti", "is_category"))
        self.assertEqual(
            contextual.validate_cost(
                state, category_costs={"ordini_vendita.importanti": "aggregate"}),
            [],
        )

    # -- il livello 5 sul percorso vivo ------------------------------------
    #
    # **Queste quattro prove interrogano `validate` e non le funzioni sotto**, ed e' il
    # punto. Le regole del livello 5 erano gia' provate una per una e passavano tutte,
    # mentre nessuna girava sul prodotto: `coherence.validate_cost` non era chiamata da
    # nessuno e `category_costs` non lo passava nessuno. Una prova che chiama la regola
    # direttamente non puo' accorgersene. Queste falliscono se qualcuno la scollega.

    def test_the_absolute_record_ceiling_is_on_the_path(self):
        """D13 fissa il massimo assoluto a 500, e fino a oggi non lo applicava nessuno.

        Misurato prima della correzione: `set_limit` a un milione passava la struttura,
        passava lo stato, passava i livelli 3-5 e arrivava all'Esecutore, che chiedeva
        un milione di record a Odoo su un processo cron condiviso. Nessun privilegio da
        scalare: bastava scriverlo in italiano.
        """
        failures = contextual.validate(
            state_with(limit={"value": 501, "origin": "user"}),
            known_refs=self.KNOWN, types=self.TYPES)
        self.assertIn("limit_above_maximum", self.codes(failures))

    def test_a_limit_at_the_ceiling_is_admitted(self):
        """E la prova gemella: il controllo non deve scattare a 500 (`restart.md`)."""
        failures = contextual.validate(
            state_with(limit={"value": 500, "origin": "user"}),
            known_refs=self.KNOWN, types=self.TYPES)
        self.assertEqual(failures, [])

    def test_the_relation_hop_limit_is_on_the_path(self):
        """§7.3 e D12: oltre due salti la strada e' un riferimento promosso (T7)."""
        reference = "ordini_vendita.cliente.paese.codice.zona"
        failures = contextual.validate(
            state_with(fields=[{"ref": reference, "origin": "user"}]),
            known_refs=self.KNOWN | {reference}, types=self.TYPES)
        self.assertIn("too_many_relation_hops", self.codes(failures))

    def test_the_cost_of_the_categories_is_on_the_path(self):
        """V-D87-2 attraverso l'unica porta che il pipeline apre."""
        state = state_with(filter={"connective": "all", "conditions": [
            condition("ordini_vendita.confermati", "is_category", identifier="c1"),
            condition("ordini_vendita.importanti", "is_category", identifier="c2"),
        ]})
        failures = contextual.validate(
            state,
            known_refs=self.KNOWN | {"ordini_vendita.importanti"},
            types={**self.TYPES, "ordini_vendita.importanti": "category"},
            category_costs={"ordini_vendita.confermati": "aggregate",
                            "ordini_vendita.importanti": "aggregate"})
        self.assertIn("too_many_aggregate_categories", self.codes(failures))

    def test_level_4_does_not_run_when_level_3_failed(self):
        """§12.2 — a type read from a reference that does not exist is not a type."""
        state = state_with(filter=condition("ordini_vendita.colore", "contains",
                                            {"kind": "text", "text": "x"}))
        failures = contextual.validate(state, known_refs=self.KNOWN, types=self.TYPES)
        self.assertEqual({failure.level for failure in failures}, {3})


if __name__ == "__main__":
    unittest.main()


class TestChiStaChiedendo(unittest.TestCase):
    """D147 — `current_user` diventa un identificatore qui, e solo qui.

    Il modello scrive un **simbolo**. Chi lo trasforma in un numero e' il risolutore,
    con l'utente che sta davvero chiedendo — la stessa divisione dei periodi, dove il
    modello dice *«quest'anno»* e il risolutore sa che giorno e'.

    Una busta che portasse `user_id = 42` sarebbe una fotografia: vera per un utente e
    falsa per chiunque altro rieseguisse la stessa domanda. E per scriverla il modello
    dovrebbe **conoscere** l'identificatore di una persona, che non gli e' mai stato
    mostrato.
    """

    @staticmethod
    def _bindings() -> dict[str, Binding]:
        legami = bindings_of_orders()
        legami["ordini_vendita.commerciale"] = Binding(
            "attribute", "user_id", "many2one", identity="user")
        return legami

    def _resolve(self, ref, *, actor):
        stato = state_with(filter={"id": "c1", "ref": ref, "predicate": "equals",
                                   "origin": "user",
                                   "value": {"kind": "identity",
                                             "reference": "current_user"}})
        return resolver_module.resolve(
            stato, bindings=self._bindings(), instant=CALENDAR_YEAR,
            model="sale.order", actor=actor)

    def test_diventa_l_utente_che_sta_chiedendo(self):
        """Il caso per cui esiste: «i miei ordini» filtra sul commerciale, con
        l'identificatore che il modello non ha mai visto."""
        esito = self._resolve("ordini_vendita.commerciale", actor=42)
        self.assertTrue(esito.resolved, [str(f) for f in esito.failures])
        self.assertIn(("user_id", "=", 42), esito.plan.domain)

    def test_non_su_un_campo_che_non_nomina_una_persona(self):
        """Il lato che deve scattare. `current_user` su una data o su un importo non e'
        una condizione strana: e' un confronto fra un numero e qualcosa che numero non
        e'. Si ferma qui, dichiarato, invece di arrivare a Odoo."""
        esito = self._resolve("ordini_vendita.data_ordine", actor=42)
        self.assertFalse(esito.resolved)
        self.assertIn("does not name a user", str(esito.failures[0]))

    def test_senza_un_utente_non_si_indovina(self):
        """Meglio un turno che fallisce di uno che filtra sull'utente sbagliato: e'
        la stessa prudenza di D39, dove senza impronta non si riusa la cache."""
        esito = self._resolve("ordini_vendita.commerciale", actor=None)
        self.assertFalse(esito.resolved)
        self.assertIn("no user to resolve to", str(esito.failures[0]))

    def test_un_riferimento_inventato_non_si_risolve(self):
        """Insieme chiuso: il livello 2 prende `boss` e `my_team` prima di qui, ma il
        risolutore non deve fidarsi di essere il secondo a guardare."""
        stato = state_with(filter={"id": "c1", "ref": "ordini_vendita.commerciale",
                                   "predicate": "equals", "origin": "user",
                                   "value": {"kind": "identity", "reference": "boss"}})
        esito = resolver_module.resolve(
            stato, bindings=self._bindings(), instant=CALENDAR_YEAR,
            model="sale.order", actor=42)
        self.assertFalse(esito.resolved)
        self.assertIn("has no resolution", str(esito.failures[0]))
