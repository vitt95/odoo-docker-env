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

    def test_level_4_does_not_run_when_level_3_failed(self):
        """§12.2 — a type read from a reference that does not exist is not a type."""
        state = state_with(filter=condition("ordini_vendita.colore", "contains",
                                            {"kind": "text", "text": "x"}))
        failures = contextual.validate(state, known_refs=self.KNOWN, types=self.TYPES)
        self.assertEqual({failure.level for failure in failures}, {3})


if __name__ == "__main__":
    unittest.main()
