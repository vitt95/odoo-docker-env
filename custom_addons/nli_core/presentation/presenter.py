"""The Presenter — native views, and never a result without its interpretation.

**V4 and D64 are the same statement from two sides.** The interpretation is always
visible above the result, without interaction, and the way to make that structural
rather than hoped-for is a return type that **cannot carry one without the other**.

    "An action required to verify something that is usually right does not get
    performed. Behind a panel, **A9 is false by construction** and the defence
    against R1 is designed but not effective." (D64)

So `Presentation` holds the state, the interpretation and the result together, and
there is no constructor that takes only the result. The architectural check of §6.4
asks exactly this: that the Presenter receive state and result together.

## Native views (V4)

The result is an `ir.actions.act_window` on the entity, with the resolved domain and
the derived view. Not a rendering of our own: a conversational result must be
indistinguishable from the first page of a native view (`02` §4.6), which is also
what makes every element actionable for free (D66) — the actions are Odoo's.
"""

from ..resolution.plan import Plan

#: Contract view names to Odoo view types. `list` is Odoo 18's name for what earlier
#: versions called `tree`.
VIEW_TYPES = {
    "list": "list",
    "kanban": "kanban",
    "calendar": "calendar",
    "pivot": "pivot",
    "graph": "graph",
    "form": "form",
}


class Presentation:
    """A result and the interpretation that produced it, inseparable.

    Every argument is required. That is the whole design: a presentation without an
    interpretation is not representable, so no code path can produce one by
    forgetting.
    """

    def __init__(self, *, state: dict, plan: Plan, result, interpretation: dict):
        self.state = state
        self.plan = plan
        self.result = result
        self.interpretation = interpretation

    def action(self) -> dict:
        """The native Odoo action that shows the result (V4)."""
        view_type = VIEW_TYPES.get(self.plan.view, "list")
        return {
            "type": "ir.actions.act_window",
            "res_model": self.plan.model,
            "domain": list(self.plan.domain),
            "view_mode": view_type,
            "views": [(False, view_type)],
            "limit": self.plan.limit,
            "context": {"create": False},
            "target": "current",
        }


def interpretation_of(state: dict, plan: Plan, result) -> dict:
    """What the interface shows above the result (D64, D65, D67, D68).

    Every element carries its **origin**, because D65 grades salience by it and the
    distinction must not depend on colour; the periods are the **resolved** ones,
    because *"this month"* confirms itself (D67); and the count is the phrase of D68.
    """
    return {
        "target": (state.get("target") or {}).get("ref"),
        "conditions": [
            {
                "id": condition.get("id"),
                "ref": condition.get("ref"),
                "predicate": condition.get("predicate"),
                "origin": condition.get("origin", "user"),
            }
            for condition in _conditions(state.get("filter"))
        ],
        "periods": [
            {"ref": reference, "resolved": rendered}
            for reference, rendered in plan.resolved_periods
        ],
        "limit": state.get("limit"),
        "presentation": state.get("presentation"),
        "records": result.describe(),
        "truncated": result.truncated,
    }


def _conditions(node):
    if not node:
        return []
    if "connective" in node:
        found = []
        for child in node.get("conditions", []):
            found.extend(_conditions(child))
        return found
    return [node]


def present(*, state: dict, plan: Plan, result) -> Presentation:
    """Build the presentation. There is no way to build one without a state."""
    return Presentation(
        state=state, plan=plan, result=result,
        interpretation=interpretation_of(state, plan, result),
    )
