"""The first interrogation end to end, from a hand-written state (part 4).

This suite **is** the completion criterion of part 4: *"the first interrogation end
to end from a hand-written state, without a model"*. Nothing here is interpreted —
the state is written by hand, exactly as the plan requires, so what is exercised is
the deterministic engine and only that.

State -> Resolver -> validation -> Executor -> Presenter, with the state persisted as
a record (D19) and the company context travelling on the turn (D40).
"""

import json
from datetime import datetime

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from ..execution import executor
from ..models.nli_interrogation import strip_provenance
from ..presentation import presenter
from ..resolution import calendar as calendar_module
from ..resolution import resolver as resolver_module
from ..resolution.plan import Binding
from ..validation import contextual, structural

INSTANT = calendar_module.Instant(now=datetime(2026, 7, 15, 10, 30))

BINDINGS = {
    "clienti": Binding(kind="attribute", field="", type="entity"),
    "clienti.nome": Binding("attribute", "name", "text"),
    "clienti.citta": Binding("attribute", "city", "text"),
    "clienti.e_azienda": Binding("attribute", "is_company", "boolean"),
    "clienti.creato_il": Binding("attribute", "create_date", "datetime"),
}

TYPES = {
    "clienti.nome": "text",
    "clienti.citta": "text",
    "clienti.e_azienda": "boolean",
    "clienti.creato_il": "datetime",
}


def hand_written_state(**sections) -> dict:
    """*"Le aziende di Cittaprova, con nome e città, le prime 5."*"""
    state = {
        "dsl_version": "1.0",
        "target": {"ref": "clienti", "origin": "user"},
        "filter": {"connective": "all", "conditions": [
            {"id": "c1", "ref": "clienti.e_azienda", "predicate": "is_true",
             "origin": "user"},
            {"id": "c2", "ref": "clienti.citta", "predicate": "equals",
             "value": {"kind": "text", "text": "Cittaprova"}, "origin": "user"},
        ]},
        "fields": [
            {"ref": "clienti.nome", "origin": "user"},
            {"ref": "clienti.citta", "origin": "user"},
        ],
        "order_by": [{"ref": "clienti.nome", "direction": "asc", "origin": "inferred",
                      "rule": "text_attribute_implies_asc"}],
        "limit": {"value": 5, "origin": "user"},
        "presentation": {"view": "list", "origin": "inferred", "rule": "default_list"},
    }
    state.update(sections)
    return state


@tagged("post_install", "-at_install", "nli_execution")
class TestEndToEnd(TransactionCase):
    """The completion criterion of part 4."""

    def setUp(self):
        super().setUp()
        self.env["res.partner"].create([
            {"name": "Alfa SpA", "city": "Cittaprova", "is_company": True},
            {"name": "Beta Srl", "city": "Cittaprova", "is_company": True},
            {"name": "Gamma", "city": "Roma", "is_company": True},
            {"name": "Mario Rossi", "city": "Cittaprova", "is_company": False},
        ])

    def resolve(self, state):
        return resolver_module.resolve(
            state, bindings=BINDINGS, instant=INSTANT, model="res.partner")

    def test_the_whole_chain(self):
        state = hand_written_state()

        # Levels 1-2, then 3-5. Nothing invalid proceeds (§12.1).
        self.assertEqual(structural.validate_state(state), [])
        self.assertEqual(
            contextual.validate(state, known_refs=frozenset(BINDINGS), types=TYPES), [])

        outcome = self.resolve(state)
        self.assertTrue(outcome.resolved, outcome.failures)

        result = executor.execute(self.env, outcome.plan)
        names = result.records.mapped("name")
        self.assertEqual(names, ["Alfa SpA", "Beta Srl"],
                         "the domain, the order and the limit all applied")
        self.assertEqual(result.total, 2)

        shown = presenter.present(state=state, plan=outcome.plan, result=result)
        action = shown.action()
        self.assertEqual(action["res_model"], "res.partner")
        self.assertEqual(action["view_mode"], "list")
        self.assertIn(("city", "=", "Cittaprova"), action["domain"])

    def test_the_count_precedes_the_retrieval(self):
        """D68 — eighty records with no context are read as **all of them**."""
        state = hand_written_state(limit={"value": 1, "origin": "user"})
        result = executor.execute(self.env, self.resolve(state).plan)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.total, 2)
        self.assertTrue(result.truncated)
        self.assertEqual(result.describe(), "i primi 1 di 2")

    def test_a_result_cannot_exist_without_its_interpretation(self):
        """V4 and D64 made structural: there is no constructor for a bare result."""
        state = hand_written_state()
        outcome = self.resolve(state)
        result = executor.execute(self.env, outcome.plan)
        with self.assertRaises(TypeError):
            presenter.Presentation(result=result)  # pylint: disable=missing-kwoa

        shown = presenter.present(state=state, plan=outcome.plan, result=result)
        self.assertEqual(shown.interpretation["target"], "clienti")
        self.assertEqual(len(shown.interpretation["conditions"]), 2)

    def test_the_interpretation_declares_the_origin_of_every_element(self):
        """D65 grades salience by origin, and the distinction must not need colour."""
        state = hand_written_state()
        outcome = self.resolve(state)
        shown = presenter.present(state=state, plan=outcome.plan,
                                  result=executor.execute(self.env, outcome.plan))
        origins = {c["origin"] for c in shown.interpretation["conditions"]}
        self.assertEqual(origins, {"user"})
        self.assertEqual(shown.interpretation["presentation"]["origin"], "inferred")

    def test_a_temporal_condition_shows_the_resolved_period(self):
        """D67 — *"this month"* confirms itself; only the resolved period is
        verifiable, which is what makes a non-calendar fiscal year catchable."""
        state = hand_written_state(filter={
            "id": "c1", "ref": "clienti.creato_il", "predicate": "within",
            "value": {"kind": "temporal", "expression": "current_month"},
            "origin": "user"})
        outcome = self.resolve(state)
        shown = presenter.present(state=state, plan=outcome.plan,
                                  result=executor.execute(self.env, outcome.plan))
        self.assertEqual(shown.interpretation["periods"],
                         [{"ref": "clienti.creato_il",
                           "resolved": "2026-07-01 - 2026-07-31"}])

    def test_an_unresolvable_reference_stops_before_execution(self):
        state = hand_written_state(fields=[
            {"ref": "clienti.fatturato_riservato", "origin": "user"}])
        failures = contextual.validate(
            state, known_refs=frozenset(BINDINGS), types=TYPES)
        self.assertTrue(failures)
        self.assertEqual(failures[0].level, 3)
        self.assertFalse(self.resolve(state).resolved)


@tagged("post_install", "-at_install", "nli_execution")
class TestPersistedState(TransactionCase):
    """The state as a record (D19) and the turn's company context (D40)."""

    def test_a_state_is_persisted_and_read_back(self):
        interrogation = self.env["nli.interrogation"].create({})
        interrogation.write_state(hand_written_state())
        self.assertEqual(interrogation.state["target"]["ref"], "clienti")

    def test_an_invalid_state_is_never_persisted(self):
        """§12.1 — a stored state that does not validate is a query that will fail
        when somebody re-runs it in six months, with no clue as to why."""
        with self.assertRaises(ValidationError):
            self.env["nli.interrogation"].create({
                "state_json": json.dumps({"dsl_version": "1.0", "target": {}}),
            })

    def test_provenance_is_stripped_on_write(self):
        """D54 — retroactive pseudonymisation does not exist.

        The fragments are the user's words. Until the pseudonymisation of D54 exists,
        storing them would write user text in clear for the twelve months of D26.
        """
        state = hand_written_state()
        state["filter"]["conditions"][0]["provenance"] = {"text": "le aziende"}
        interrogation = self.env["nli.interrogation"].create({})
        interrogation.write_state(state)
        stored = interrogation.state
        self.assertNotIn("provenance", stored["filter"]["conditions"][0])
        self.assertEqual(stored["filter"]["conditions"][0]["ref"], "clienti.e_azienda")

    def test_stripping_leaves_everything_else_alone(self):
        state = hand_written_state()
        self.assertEqual(strip_provenance(state), state,
                         "a state without provenance is unchanged")

    def test_a_turn_without_a_company_context_is_refused(self):
        """D40, and §9 of the registry: refused, never executed.

        An execution that restores the user but not their active companies returns
        the same orders plus those of a company they had deselected. No error, no
        warning, a different number — the infrastructural form of R1.
        """
        interrogation = self.env["nli.interrogation"].create({})
        with self.assertRaises(ValidationError):
            self.env["nli.turn"].create({
                "interrogation_id": interrogation.id,
                "user_id": self.env.user.id,
                "company_ids": [(5, 0, 0)],
            })

    def test_the_turn_rebuilds_the_execution_context(self):
        """On the cron process of D20a there is no request to inherit it from."""
        interrogation = self.env["nli.interrogation"].create({})
        turn = self.env["nli.turn"].create({
            "interrogation_id": interrogation.id,
            "user_id": self.env.user.id,
            "company_ids": [(6, 0, self.env.companies.ids)],
            "lang": "it_IT",
        })
        context = turn.context_for_execution()
        self.assertEqual(context["allowed_company_ids"], self.env.companies.ids)
        self.assertEqual(context["lang"], "it_IT")

    def test_an_interrogation_belongs_to_its_author(self):
        """A question somebody asked is not readable by default: §5.10 makes the
        state shareable **by an explicit act**, and a default of readable would
        share it by omission."""
        mine = self.env["nli.interrogation"].create({})
        other = new_test_user(self.env, login="nli_other_user")
        with self.assertRaises(AccessError):
            mine.with_user(other).read(["state_json"])
