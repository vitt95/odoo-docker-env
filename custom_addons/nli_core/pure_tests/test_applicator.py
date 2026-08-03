"""The Applicator, against the worked examples of `ai/03-specifica-dsl.md` §17.

The specification's own examples are used as fixtures on purpose. They are the
only test data in existence that was written before the implementation and
without knowledge of it, which makes them the only data that can contradict it.
"""

from __future__ import annotations

import copy
import unittest

from ..application import applicator
from ..contract import state as state_module
from ..validation import coherence, structural

FIELDS_OF_CLIENTI = ("clienti.nome", "clienti.email")


def turn(op: str, **payload) -> dict:
    return {"op": op, **payload}


class TestConversationalSequence(unittest.TestCase):
    """§17.1 — five turns from the empty state, checked turn by turn."""

    def setUp(self) -> None:
        self.state = state_module.empty_state()

    def apply(self, *operations, **kwargs) -> applicator.Result:
        result = applicator.apply(
            self.state,
            list(operations),
            default_fields=kwargs.pop("default_fields", ()),
            **kwargs,
        )
        self.state = result.state
        return result

    def test_turn_1_target_only(self):
        self.apply(turn("set_target", ref="clienti", provenance={"text": "clienti"}))

        self.assertEqual(
            self.state,
            {
                "dsl_version": "1.0",
                "target": {
                    "ref": "clienti",
                    "origin": "user",
                    "provenance": {"text": "clienti"},
                },
                # "All customers" produces no operation: the default limit stands
                # and is shown in the interpretation. The system does not promise
                # what it will not do (§17.1).
                "limit": {"value": 80, "origin": "default"},
                "presentation": {
                    "view": "list",
                    "origin": "inferred",
                    "rule": "default_list",
                },
            },
        )
        self.assertNotIn("fields", self.state, "absent fields means entity defaults")
        self.assertEqual(structural.validate_state(self.state), [])

    def test_turn_2_condition_from_an_incomplete_sentence(self):
        self.apply(turn("set_target", ref="clienti", provenance={"text": "clienti"}))
        self.apply(turn(
            "add_condition",
            combine="all",
            condition={
                "ref": "clienti.attivo",
                "predicate": "is_true",
                "value": {"kind": "boolean", "value": True},
            },
            provenance={"text": "quelli attivi"},
        ))

        condition = self.state["filter"]
        self.assertEqual(condition["ref"], "clienti.attivo")
        self.assertEqual(condition["predicate"], "is_true")
        self.assertEqual(condition["id"], "c1")
        self.assertEqual(condition["origin"], "user")
        self.assertEqual(condition["provenance"], {"text": "quelli attivi"})
        # No part of the previous state was re-emitted by the model: that is the
        # property of §4.3, and it is visible here as the target being untouched.
        self.assertEqual(self.state["target"]["ref"], "clienti")
        self.assertEqual(structural.validate_state(self.state), [])

    def test_turn_3_order_direction_is_inferred(self):
        self.apply(turn("set_target", ref="clienti", provenance={"text": "clienti"}))
        self.apply(turn(
            "set_order",
            ref="clienti.citta",
            direction="asc",
            origin="inferred",
            provenance={"text": "per città"},
        ))

        # The worked example of §17.1 shows the envelope and says *«`asc` è inferito
        # ... registrato con origin: inferred»* without showing the state it produces.
        # §10.2 requires an inference to declare the rule that produced it, and §5.1's
        # own state example carries one on `order_by`. The example was incomplete, not
        # the rule optional — D88 had already named the identifier and nothing emitted
        # it. **D99** makes the Applicator derive it from the inferred direction.
        self.assertEqual(
            self.state["order_by"],
            [{
                "ref": "clienti.citta",
                "direction": "asc",
                "origin": "inferred",
                "provenance": {"text": "per città"},
                "rule": "text_attribute_implies_asc",
            }],
        )

    def test_turn_4_add_field_keeps_the_defaults(self):
        self.apply(turn("set_target", ref="clienti", provenance={"text": "clienti"}))
        self.apply(
            turn("add_field", ref="clienti.telefono", provenance={"text": "anche il telefono"}),
            default_fields=FIELDS_OF_CLIENTI,
        )

        self.assertEqual(
            [entry["ref"] for entry in self.state["fields"]],
            ["clienti.nome", "clienti.email", "clienti.telefono"],
            "'also' adds to what is shown; it does not replace it (§6.4)",
        )
        self.assertEqual(
            [entry["origin"] for entry in self.state["fields"]],
            ["default", "default", "user"],
            "the columns the user never named keep origin 'default' (§10.2)",
        )

    def test_turn_5_open_record_leaves_the_state_alone(self):
        self.apply(turn("set_target", ref="clienti", provenance={"text": "clienti"}))
        before = copy.deepcopy(self.state)
        result = self.apply(turn(
            "open_record",
            selector={"by": "position", "value": 1},
            provenance={"text": "il primo"},
        ))

        self.assertEqual(self.state, before, "navigation does not modify the interrogation")
        self.assertEqual(len(result.navigations), 1)
        self.assertEqual(result.navigations[0].selector, {"by": "position", "value": 1})


class TestFieldSemantics(unittest.TestCase):
    """§6.4 — the distinction between adding and replacing is semantic."""

    def base(self) -> dict:
        return applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state

    def test_set_fields_replaces(self):
        result = applicator.apply(
            self.base(),
            [turn(
                "set_fields",
                refs=["clienti.nome", "clienti.email", "clienti.telefono"],
                provenance={"text": "solamente Nome, Email e Telefono"},
            )],
            default_fields=FIELDS_OF_CLIENTI,
        )
        self.assertEqual(
            [entry["ref"] for entry in result.state["fields"]],
            ["clienti.nome", "clienti.email", "clienti.telefono"],
        )

    def test_add_field_is_idempotent(self):
        once = applicator.apply(
            self.base(),
            [turn("add_field", ref="clienti.nome", provenance={"text": "il nome"})],
            default_fields=FIELDS_OF_CLIENTI,
        ).state
        twice = applicator.apply(
            once,
            [turn("add_field", ref="clienti.nome", provenance={"text": "il nome"})],
        ).state
        self.assertEqual(once["fields"], twice["fields"])

    def test_add_field_without_defaults_is_refused(self):
        """The meaning of "show the phone too" depends on what is shown now.

        Guessing would silently drop every column the user was looking at, so the
        Applicator refuses rather than assuming an empty starting set.
        """
        with self.assertRaises(applicator.ApplicationError):
            applicator.apply(self.base(), [turn("add_field", ref="clienti.telefono")])

    def test_clear_fields_restores_the_defaults(self):
        state = applicator.apply(
            self.base(),
            [turn("set_fields", refs=["clienti.nome"])],
        ).state
        cleared = applicator.apply(state, [turn("clear_fields")]).state
        self.assertNotIn("fields", cleared)

    def test_removing_the_last_field_produces_a_state_validation_refuses(self):
        state = applicator.apply(
            self.base(),
            [turn("set_fields", refs=["clienti.nome"])],
        ).state
        emptied = applicator.apply(state, [turn("remove_field", ref="clienti.nome")]).state
        codes = {failure.code for failure in structural.validate_state(emptied)}
        self.assertIn("empty_section", codes)


class TestRestartRule(unittest.TestCase):
    """§6.2 — a different entity clears everything built on the previous one."""

    def test_target_change_clears_and_resets(self):
        state = applicator.apply(
            state_module.empty_state(),
            [
                turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
                turn(
                    "add_condition",
                    condition={"ref": "ordini_vendita.stato", "predicate": "is_one_of",
                               "value": {"kind": "enum", "items": ["confermato"]}},
                    provenance={"text": "confermati"},
                ),
                turn("add_group", ref="ordini_vendita.venditore", provenance={"text": "per venditore"}),
                turn("set_limit", value=5, provenance={"text": "i primi 5"}),
            ],
        ).state
        self.assertIn("filter", state)
        self.assertEqual(state["limit"]["value"], 5)

        after = applicator.apply(
            state,
            [turn("set_target", ref="clienti", provenance={"text": "i clienti"})],
        ).state

        self.assertEqual(after["target"]["ref"], "clienti")
        for section in ("filter", "group_by", "fields", "measures", "order_by"):
            self.assertNotIn(section, after, f"{section} survived a change of entity")
        self.assertEqual(after["limit"], {"value": 80, "origin": "default"})

    def test_same_target_changes_nothing_else(self):
        state = applicator.apply(
            state_module.empty_state(),
            [
                turn("set_target", ref="clienti", provenance={"text": "clienti"}),
                turn("set_limit", value=5, provenance={"text": "i primi 5"}),
            ],
        ).state
        again = applicator.apply(
            state, [turn("set_target", ref="clienti", provenance={"text": "clienti"})]
        ).state
        self.assertEqual(again["limit"]["value"], 5)


class TestViewDerivation(unittest.TestCase):
    """§6.7 — the five rules, in order, as a table."""

    def state_with(self, measures: int, groups: int) -> dict:
        operations = [turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"})]
        for index in range(measures):
            operations.append(turn(
                "add_measure",
                function="sum",
                ref=f"ordini_vendita.importo_{index}",
                provenance={"text": "somma"},
            ))
        for index in range(groups):
            operations.append(turn(
                "add_group",
                ref=f"ordini_vendita.dimensione_{index}",
                provenance={"text": "per dimensione"},
            ))
        return applicator.apply(state_module.empty_state(), operations).state

    def test_the_table(self):
        cases = (
            (1, 2, "pivot", "measures_multi_group_implies_pivot"),
            (1, 1, "graph", "measures_single_group_implies_graph"),
            (1, 0, "list", "measures_without_group_implies_list"),
            (0, 1, "list", "grouping_without_measure_implies_list"),
            (0, 0, "list", "default_list"),
        )
        for measures, groups, view, rule in cases:
            with self.subTest(measures=measures, groups=groups):
                state = self.state_with(measures, groups)
                self.assertEqual(state["presentation"]["view"], view)
                self.assertEqual(state["presentation"]["rule"], rule)
                self.assertEqual(state["presentation"]["origin"], "inferred")

    def test_section_17_3_derives_a_graph(self):
        """§17.3 — one measure and one grouping, and the state says which rule."""
        state = applicator.apply(
            state_module.empty_state(),
            [
                turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
                turn("add_measure", ref="ordini_vendita.importo_totale", function="sum",
                     provenance={"text": "somma degli importi"}),
                turn("add_group", ref="ordini_vendita.venditore",
                     provenance={"text": "per venditore"}),
            ],
        ).state
        self.assertEqual(state["presentation"]["view"], "graph")
        self.assertEqual(
            state["presentation"]["rule"], "measures_single_group_implies_graph"
        )
        self.assertEqual(coherence.validate_coherence(state), [])

    def test_an_explicit_view_survives_further_turns(self):
        state = applicator.apply(
            state_module.empty_state(),
            [
                turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
                turn("set_view", view="calendar", provenance={"text": "sul calendario"}),
            ],
        ).state
        self.assertEqual(state["presentation"]["origin"], "user")
        after = applicator.apply(
            state, [turn("add_group", ref="ordini_vendita.stato", provenance={"text": "per stato"})]
        ).state
        self.assertEqual(
            after["presentation"]["view"],
            "calendar",
            "a view the user asked for is not re-derived behind their back",
        )

    def test_calendar_is_never_inferred(self):
        for measures in (0, 1):
            for groups in (0, 1, 2):
                with self.subTest(measures=measures, groups=groups):
                    view, _ = applicator.derive_view(
                        self.state_with(measures, groups)
                    )
                    self.assertNotEqual(view, "calendar")


class TestOrderDirection(unittest.TestCase):
    """D88 — the direction is derived from the attribute's type, or refused."""

    def base(self) -> dict:
        return applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"})],
        ).state

    def test_set_order_without_a_direction_is_refused(self):
        """Defaulting to `asc` would sort "the latest five orders" oldest first.

        An answer that looks right and is exactly backwards is the failure mode
        this refusal exists for: ascending is natural for text and descending for
        dates, and only the attribute's type says which — so the component that
        holds the type derives it, not this one.
        """
        with self.assertRaises(applicator.ApplicationError) as raised:
            applicator.apply(
                self.base(),
                [turn("set_order", ref="ordini_vendita.data_ordine",
                      provenance={"text": "per data"})],
            )
        self.assertIn("D88", str(raised.exception))

    def test_add_order_without_a_direction_is_refused(self):
        with self.assertRaises(applicator.ApplicationError):
            applicator.apply(
                self.base(),
                [turn("add_order", ref="ordini_vendita.cliente",
                      provenance={"text": "e per cliente"})],
            )

    def test_a_resolved_direction_carries_its_rule(self):
        state = applicator.apply(self.base(), [turn(
            "set_order", ref="ordini_vendita.data_ordine", direction="desc",
            origin="inferred", provenance={"text": "gli ultimi"},
        )]).state
        entry = state["order_by"][0]
        self.assertEqual(entry["direction"], "desc")
        self.assertEqual(entry["origin"], "inferred")
        self.assertEqual(structural.validate_state(state), [])

    def test_the_text_rule_is_a_declared_identifier(self):
        """The rule of §17.1 turn 3, named by D88 because rule ids are closed."""
        state = applicator.apply(self.base(), [turn(
            "set_order", ref="ordini_vendita.cliente", direction="asc",
            origin="inferred", provenance={"text": "per cliente"},
        )]).state
        state["order_by"][0]["rule"] = "text_attribute_implies_asc"
        self.assertEqual(structural.validate_state(state), [])


class TestConditionOperations(unittest.TestCase):
    def base(self) -> dict:
        return applicator.apply(
            state_module.empty_state(),
            [
                turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
                turn("add_condition", condition={
                    "ref": "ordini_vendita.data_ordine", "predicate": "within",
                    "value": {"kind": "temporal", "expression": "previous_month"},
                }, provenance={"text": "di febbraio"}),
            ],
        ).state

    def test_replace_condition_keeps_identifier_and_position(self):
        state = self.base()
        replaced = applicator.apply(state, [turn(
            "replace_condition",
            id="c1",
            condition={
                "ref": "ordini_vendita.data_ordine", "predicate": "within",
                "value": {"kind": "temporal", "expression": "current_month"},
            },
            provenance={"text": "anzi, di marzo"},
        )]).state

        condition = replaced["filter"]
        self.assertEqual(condition["id"], "c1", "the element changes value, it does not "
                                               "disappear and reappear (§6.3)")
        self.assertEqual(condition["value"]["expression"], "current_month")

    def test_replace_condition_on_an_unknown_identifier_is_refused_before_application(self):
        state = self.base()
        operations = [turn("replace_condition", id="c9", condition={
            "ref": "ordini_vendita.stato", "predicate": "is_one_of",
            "value": {"kind": "enum", "items": ["bozza"]},
        })]
        failures = coherence.validate_envelope_coherence(operations, state=state)
        self.assertIn("unknown_condition", {failure.code for failure in failures})
        with self.assertRaises(applicator.ApplicationError):
            applicator.apply(state, operations)

    def test_remove_condition_by_reference(self):
        state = self.base()
        removed = applicator.apply(
            state,
            [turn("remove_condition", ref="ordini_vendita.data_ordine",
                  provenance={"text": "togli il filtro sulla data"})],
        ).state
        self.assertNotIn("filter", removed)

    def test_identifiers_do_not_collide_after_a_removal(self):
        state = self.base()
        state = applicator.apply(state, [turn("add_condition", condition={
            "ref": "ordini_vendita.stato", "predicate": "is_one_of",
            "value": {"kind": "enum", "items": ["confermato"]},
        }, provenance={"text": "confermati"})]).state
        self.assertEqual(state_module.condition_ids(state), ["c1", "c2"])

        state = applicator.apply(state, [turn("remove_condition", id="c1")]).state
        state = applicator.apply(state, [turn("add_condition", condition={
            "ref": "ordini_vendita.importo_totale", "predicate": "greater_than",
            "value": {"kind": "number", "value": 1000},
        }, provenance={"text": "sopra mille"})]).state
        self.assertEqual(
            sorted(state_module.condition_ids(state)),
            ["c2", "c3"],
            "a removed identifier is not reused: the interpretation shown to the "
            "user would silently re-anchor to a different condition",
        )

    def test_any_nests_rather_than_flattening(self):
        state = self.base()
        state = applicator.apply(state, [turn("add_condition", combine="any", condition={
            "ref": "ordini_vendita.stato", "predicate": "is_one_of",
            "value": {"kind": "enum", "items": ["confermato"]},
        }, provenance={"text": "o confermati"})]).state
        self.assertEqual(state["filter"]["connective"], "any")
        self.assertEqual(len(state["filter"]["conditions"]), 2)

    def test_clear_filter_removes_the_section(self):
        state = applicator.apply(self.base(), [turn("clear_filter")]).state
        self.assertNotIn("filter", state)


class TestSessionOperations(unittest.TestCase):
    def test_reset_returns_to_the_empty_state(self):
        state = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state
        after = applicator.apply(state, [turn("reset")]).state
        self.assertNotIn("target", after)
        self.assertEqual(after["dsl_version"], "1.0")

    def test_reset_composes_with_a_new_target(self):
        """"No, let's look at customers instead" is one intention, two operations."""
        state = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"})],
        ).state
        after = applicator.apply(state, [
            turn("reset"),
            turn("set_target", ref="clienti", provenance={"text": "i clienti"}),
        ]).state
        self.assertEqual(after["target"]["ref"], "clienti")
        self.assertEqual(coherence.validate_envelope_coherence([
            turn("reset"), turn("set_target", ref="clienti"),
        ]), [])

    def test_revert_last_reports_the_request(self):
        state = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state
        result = applicator.apply(state, [turn("revert_last", provenance={"text": "torna indietro"})])
        self.assertTrue(result.revert_requested)
        self.assertEqual(
            result.state["target"]["ref"],
            "clienti",
            "the Applicator has no history: restoring is the orchestrator's job",
        )


class TestApplicationRules(unittest.TestCase):
    """§4.5 — the four rules, as properties rather than as prose."""

    def test_the_starting_state_is_never_mutated(self):
        state = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state
        snapshot = copy.deepcopy(state)
        applicator.apply(state, [
            turn("set_limit", value=5, provenance={"text": "i primi 5"}),
            turn("add_condition", condition={
                "ref": "clienti.citta", "predicate": "equals",
                "value": {"kind": "text", "text": "Milano"},
            }, provenance={"text": "di Milano"}),
        ])
        self.assertEqual(state, snapshot, "atomicity: no partially modified state is observable")

    def test_a_failing_sequence_leaves_the_original_untouched(self):
        state = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state
        snapshot = copy.deepcopy(state)
        with self.assertRaises(applicator.ApplicationError):
            applicator.apply(state, [
                turn("set_limit", value=5, provenance={"text": "i primi 5"}),
                turn("replace_condition", id="c1", condition={
                    "ref": "clienti.citta", "predicate": "equals",
                    "value": {"kind": "text", "text": "Milano"},
                }),
            ])
        self.assertEqual(state, snapshot)

    def test_order_is_significant(self):
        base = applicator.apply(
            state_module.empty_state(),
            [turn("set_target", ref="clienti", provenance={"text": "clienti"})],
        ).state
        forward = applicator.apply(base, [
            turn("set_limit", value=5, provenance={"text": "5"}),
            turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
        ]).state
        backward = applicator.apply(base, [
            turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
            turn("set_limit", value=5, provenance={"text": "5"}),
        ]).state
        self.assertEqual(forward["limit"]["value"], 80, "the restart rule reset the limit")
        self.assertEqual(backward["limit"]["value"], 5)

    def test_application_is_a_function_of_its_arguments(self):
        """Same inputs, same output — the property the corpus depends on (D82)."""
        operations = [
            turn("set_target", ref="ordini_vendita", provenance={"text": "ordini"}),
            turn("add_condition", condition={
                "ref": "ordini_vendita.data_ordine", "predicate": "within",
                "value": {"kind": "temporal", "expression": "current_month"},
            }, provenance={"text": "di questo mese"}),
            turn("add_measure", ref="ordini_vendita.importo_totale", function="sum",
                 provenance={"text": "somma"}),
            turn("add_group", ref="ordini_vendita.venditore", provenance={"text": "per venditore"}),
        ]
        first = applicator.apply(state_module.empty_state(), operations).state
        second = applicator.apply(state_module.empty_state(), operations).state
        self.assertEqual(first, second)

    def test_unknown_operation_raises_instead_of_being_skipped(self):
        with self.assertRaises(applicator.ApplicationError):
            applicator.apply(state_module.empty_state(), [turn("set_raw_domain", value="[]")])


class TestNormalisation(unittest.TestCase):
    def test_single_child_connectives_are_reduced(self):
        node = {"connective": "all", "conditions": [
            {"connective": "all", "conditions": [
                {"id": "c1", "ref": "x", "predicate": "is_true", "origin": "user"},
            ]},
        ]}
        self.assertEqual(
            applicator.reduce_filter(node),
            {"id": "c1", "ref": "x", "predicate": "is_true", "origin": "user"},
        )

    def test_nested_same_connectives_are_flattened(self):
        node = {"connective": "all", "conditions": [
            {"id": "c1", "ref": "a", "predicate": "is_true", "origin": "user"},
            {"connective": "all", "conditions": [
                {"id": "c2", "ref": "b", "predicate": "is_true", "origin": "user"},
                {"id": "c3", "ref": "c", "predicate": "is_true", "origin": "user"},
            ]},
        ]}
        reduced = applicator.reduce_filter(node)
        self.assertEqual(len(reduced["conditions"]), 3)

    def test_not_is_never_reduced_away(self):
        node = {"connective": "not", "conditions": [
            {"id": "c1", "ref": "a", "predicate": "is_true", "origin": "user"},
        ]}
        self.assertEqual(applicator.reduce_filter(node)["connective"], "not")


if __name__ == "__main__":
    unittest.main()


class TestAPeriodSupersedesThePrevious(unittest.TestCase):
    """D125 — un periodo nuovo prende il posto di quello sullo stesso attributo.

    Visto sul campo: tre turni di seguito sulla data di creazione lasciavano tre
    periodi in AND, il livello 4 li rifiutava, e ogni tentativo di uscirne ne
    aggiungeva un quarto. **La stessa frase che aveva funzionato al primo turno non
    funzionava piu' al terzo.**
    """

    @staticmethod
    def _add(ref, expression, predicate="within", combine="all"):
        return {"op": "add_condition", "combine": combine,
                "condition": {"ref": ref, "predicate": predicate,
                              "value": {"kind": "temporal", "expression": expression}},
                "provenance": {"text": expression}}

    def _periods(self, state, ref):
        return [c for c in state_module.conditions(state.get("filter"))
                if c.get("ref") == ref]

    def _apply(self, *operations):
        return applicator.apply({"dsl_version": "1.0"}, list(operations)).state

    def test_the_second_period_replaces_the_first(self):
        state = self._apply(
            {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
            self._add("ordini.data", "current_year"),
            self._add("ordini.data", "current_month"),
        )
        periods = self._periods(state, "ordini.data")
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["value"]["expression"], "current_month")

    def test_a_state_already_spoiled_repairs_itself(self):
        """Le conversazioni guaste da prima della regola guariscono al turno dopo."""
        state = self._apply(
            {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
            self._add("ordini.data", "current_year"),
        )
        # Due periodi messi a mano, come li porta uno stato scritto prima di D125.
        state["filter"] = {"connective": "all", "conditions": [
            {"id": "c1", "ref": "ordini.data", "predicate": "within",
             "value": {"kind": "temporal", "expression": "current_year"}},
            {"id": "c2", "ref": "ordini.data", "predicate": "within",
             "value": {"kind": "temporal", "expression": "last_n_months"}},
        ]}
        risanato = applicator.apply(
            state, [self._add("ordini.data", "current_quarter")]).state
        periods = self._periods(risanato, "ordini.data")
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["value"]["expression"], "current_quarter")

    def test_a_period_on_another_attribute_is_still_added(self):
        """§17.1: un asse nuovo si somma, ed e' cio' che fa funzionare la conversazione."""
        state = self._apply(
            {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
            self._add("ordini.data", "current_year"),
            self._add("ordini.consegna", "current_month"),
        )
        self.assertEqual(len(self._periods(state, "ordini.data")), 1)
        self.assertEqual(len(self._periods(state, "ordini.consegna")), 1)

    def test_a_condition_that_is_not_a_period_is_still_added(self):
        state = self._apply(
            {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
            self._add("ordini.data", "current_year"),
            {"op": "add_condition", "combine": "all",
             "condition": {"ref": "ordini.confermati", "predicate": "is_category"},
             "provenance": {"text": "confermati"}},
        )
        refs = [c.get("ref") for c in state_module.conditions(state.get("filter"))]
        self.assertEqual(sorted(refs), ["ordini.confermati", "ordini.data"])

    def test_under_any_two_periods_are_a_union_and_survive(self):
        """*«di marzo o di settembre»* e' una cosa che si puo' voler dire davvero."""
        state = self._apply(
            {"op": "set_target", "ref": "ordini", "provenance": {"text": "ordini"}},
            self._add("ordini.data", "current_year", combine="any"),
            self._add("ordini.data", "current_month", combine="any"),
        )
        self.assertEqual(len(self._periods(state, "ordini.data")), 2)
