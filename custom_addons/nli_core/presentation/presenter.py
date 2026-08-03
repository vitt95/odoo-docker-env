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

## Native views (V4), e chi le costruisce

Un risultato conversazionale dev'essere indistinguibile dalla prima pagina di una
vista nativa (`02` §4.6), che e' anche cio' che rende ogni elemento azionabile senza
lavoro (D66) — le azioni sono di Odoo.

**Non e' pero' questo modulo a costruirla.** Qui c'era un metodo `action()` che
produceva un `ir.actions.act_window`, e **non lo chiamava nessuno**: dal 2 agosto
(`00` §33.4) la vista nativa e' *incorporata* nella conversazione dal componente
`AidaRecords` di `nli_web`, che riceve il piano risolto e lascia a Odoo tabella,
ordinamento, colonne e paginazione.

Il metodo e' stato tolto invece di essere ricollegato, perche' due strade verso lo
stesso schermo sono esattamente cio' che D124 ha appena chiuso — e una delle due era
gia' morta. Un metodo che realizza un vincolo e non gira non e' una garanzia: e' una
garanzia che sembra esserci.
"""

from ..resolution.plan import Plan


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


def interpretation_of(state: dict, plan: Plan, result) -> dict:
    """What the interface shows above the result (D64, D65, D67, D68).

    Every element carries its **origin**, because D65 grades salience by it and the
    distinction must not depend on colour; the periods are the **resolved** ones,
    because *"this month"* confirms itself (D67); and the count is the phrase of D68.
    """
    return {
        "target": _element(state.get("target") or {}),
        "conditions": [
            {
                "id": condition.get("id"),
                "ref": condition.get("ref"),
                "predicate": condition.get("predicate"),
                "value": condition.get("value"),
                **_element(condition),
            }
            for condition in _conditions(state.get("filter"))
        ],
        # §3.1 lists what must always be visible, and the three sections below were
        # missing from it. The ordering above all: *«è la sede del fraintendimento di
        # "ultimi"»* — the one element the document names as the place where
        # misunderstandings live, and the interpretation did not carry it.
        "groups": [
            {"granularity": entry.get("granularity"), **_element(entry)}
            for entry in state.get("group_by") or ()
        ],
        "order": [
            {"direction": entry.get("direction"), **_element(entry)}
            for entry in state.get("order_by") or ()
        ],
        "measures": [
            {"function": entry.get("function"), **_element(entry)}
            for entry in state.get("measures") or ()
        ],
        "fields": [_element(entry) for entry in state.get("fields") or ()],
        "periods": [
            {"ref": reference, "resolved": rendered}
            for reference, rendered in plan.resolved_periods
        ],
        "limit": state.get("limit"),
        "presentation": state.get("presentation"),
        "records": result.describe(),
        "truncated": result.truncated,
        # I numeri, quando lo stato ne ha chiesti. **Fino al 3 agosto 2026 non c'erano**
        # e la sezione `measures` qui sopra elencava le misure senza mai portarne il
        # valore: l'interpretazione diceva «media di fatturato» sopra un elenco di
        # record. Dichiarare una misura e non mostrarne il numero e' la forma di D2 che
        # costa di piu' — l'utente crede di aver letto una media.
        "results": [
            {"keys": list(group.keys),
             "measures": [{"function": function, "ref": reference or None,
                           "value": value}
                          for (function, reference), value in group.measures.items()]}
            for group in getattr(result, "groups", ()) or ()
        ],
    }


def _element(entry: dict) -> dict:
    """Reference, origin, rule and provenance — what every visible element carries.

    **Origin** because D65 grades salience by it and the distinction must not depend
    on colour. **Rule** because an inference the user cannot see the reason for is one
    they cannot contradict (§10.2). **Provenance** because §3.4 builds the cross
    highlighting on it, which is *«l'interazione più efficace dell'intero prodotto»*
    for recognising a misunderstanding — and it cannot be reconstructed later: only
    the operation that produced the element knew which words it came from.
    """
    element = {
        "ref": entry.get("ref"),
        "origin": entry.get("origin", "user"),
    }
    if entry.get("rule"):
        element["rule"] = entry["rule"]
    if (entry.get("provenance") or {}).get("text"):
        element["provenance"] = entry["provenance"]["text"]
    return element


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
