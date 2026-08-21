"""The Resolver — the only component aware of time (§4.6, §7.4).

**Deterministic zone**: it *uses* the instant, it never *reads* it. The instant
arrives as an argument, so the same state and the same instant always produce the
same Plan, and the evaluation corpus can be re-run at a fixed moment (§13.3).

## What it does, and in which order

    semantic reference  ->  binding (dictionary)  ->  authorisation  ->  Plan element

Resolution happens **at every execution**, never once at save time (§1.4). Two
properties nothing else provides:

* **permissions are always the current ones.** A query saved six months ago by a
  user with more rights, run today by a user with fewer, shows what today's user may
  see. Without re-resolution a saved state would be a permanent shortcut to data no
  longer authorised — a direct violation of **V2**;
* **saved queries survive the installation evolving.** A renamed field invalidates
  one resolution, not the state, and the dictionary can absorb it in one place for
  every saved query that referenced it (**V6**).

## Vagueness is resolved here too, never by the model

§9.3: the model recognises vagueness and **names** it; the dictionary defines it; the
Resolver applies the definition. *"Circa centomila"* becomes 90 000 – 110 000 here,
and the interpretation shows the interval — so the user sees the number actually
applied and can contradict it.
"""

from __future__ import annotations

from ..contract import state as state_module
from ..contract.vocabulary import DEFAULT_LIMITS, Limits
from . import calendar as calendar_module
from .plan import Binding, Plan, Resolution, ResolutionFailure

#: Predicate -> Odoo operator, for the predicates that map one to one.
OPERATORS: dict[str, str] = {
    "equals": "=",
    "greater_than": ">",
    "greater_or_equal": ">=",
    "less_than": "<",
    "less_or_equal": "<=",
    "contains": "ilike",
    "is_one_of": "in",
    "is_not_one_of": "not in",
}

#: Views that display records one by one; the others aggregate.
RECORD_VIEWS = frozenset({"list", "kanban", "calendar", "form"})


def resolve(
    state: dict,
    *,
    bindings: dict[str, Binding],
    instant: calendar_module.Instant,
    model: str,
    resolvers: dict | None = None,
    limits: Limits = DEFAULT_LIMITS,
    actor: int | None = None,
) -> Resolution:
    """A state and an instant into an Execution Plan.

    `bindings` comes from the dictionary and already reflects this user's
    permissions: a reference the user may not read is simply absent, and its absence
    is reported as *unresolved* — §7.4 requires that no information about the
    existence of an unauthorised attribute reaches the user.
    """
    resolvers = resolvers or {}
    failures: list[ResolutionFailure] = []
    periods: list[tuple[str, str]] = []

    domain = _filter_domain(state.get("filter"), bindings, instant, resolvers,
                            failures, periods, actor)
    fields = _refs(state.get("fields"), bindings, failures)
    groups = _refs(state.get("group_by"), bindings, failures)
    order = _order(state.get("order_by"), bindings, failures)
    measures = _measures(state.get("measures"), bindings, failures)

    if failures:
        return Resolution(failures=failures)

    return Resolution(plan=Plan(
        model=model,
        domain=tuple(domain),
        fields=tuple(fields),
        group_by=tuple(groups),
        order=order,
        limit=(state.get("limit") or {}).get("value", limits.default_records),
        view=(state.get("presentation") or {}).get("view", "list"),
        measures=tuple(measures),
        resolved_periods=tuple(periods),
    ))


def _binding(reference: str, bindings: dict[str, Binding],
             failures: list[ResolutionFailure]) -> Binding | None:
    binding = bindings.get(reference)
    if binding is None:
        # §7.4: unresolved and unauthorised are the same outcome towards the user.
        # Level 3 turns this into a message with alternatives from the catalogue, and
        # registers it as a candidate enrichment of the dictionary (§12.4) — every
        # failure here is a term someone used that the dictionary does not know.
        failures.append(ResolutionFailure(reference, "not in the dictionary"))
        return None
    return binding


def _refs(section, bindings, failures) -> list[str]:
    resolved = []
    for entry in section or ():
        binding = _binding(entry["ref"], bindings, failures)
        if binding is not None:
            resolved.append(binding.field)
    return resolved


def _order(section, bindings, failures) -> str:
    parts = []
    for entry in section or ():
        binding = _binding(entry["ref"], bindings, failures)
        if binding is None:
            continue
        if not binding.sortable:
            # Rule 5 of §5.3 should have kept this out of the catalogue; if it got
            # here the catalogue is wrong, and failing now beats an ORM error later.
            failures.append(ResolutionFailure(
                entry["ref"], "not stored: cannot be ordered on"))
            continue
        parts.append(f"{binding.field} {entry['direction']}")
    return ", ".join(parts)


def _measures(section, bindings, failures) -> list[tuple[str, str]]:
    resolved = []
    for entry in section or ():
        if "ref" not in entry:
            resolved.append((entry["function"], ""))
            continue
        binding = _binding(entry["ref"], bindings, failures)
        if binding is not None:
            resolved.append((entry["function"], binding.field))
    return resolved


def _filter_domain(node, bindings, instant, resolvers, failures, periods,
                   actor=None) -> list:
    if node is None:
        return []
    if state_module.is_connective(node):
        children = [
            _filter_domain(child, bindings, instant, resolvers, failures, periods,
                           actor)
            for child in node.get("conditions", [])
        ]
        children = [child for child in children if child]
        if not children:
            return []
        connective = node["connective"]
        if connective == "not":
            return ["!"] + children[0]
        prefix = "&" if connective == "all" else "|"
        # Odoo's prefix notation: n children need n-1 operators.
        domain: list = [prefix] * (len(children) - 1)
        for child in children:
            domain.extend(child)
        return domain
    return _condition_domain(node, bindings, instant, resolvers, failures, periods,
                             actor)


def _condition_domain(condition, bindings, instant, resolvers, failures, periods,
                      actor=None) -> list:
    binding = _binding(condition["ref"], bindings, failures)
    if binding is None:
        return []

    predicate = condition.get("predicate")

    if binding.kind == "category":
        # V-D87-3: expanded **here**, at execution, never by the Applicator. The
        # condition may depend on the clock, and a state carrying a resolved "today"
        # would be a snapshot instead of a question.
        return list(binding.domain)

    field = binding.field
    value = condition.get("value") or {}

    # **L'identita' diventa un numero qui, e solo qui** (D147). Il modello ha scritto
    # un simbolo — `{"kind":"identity","reference":"current_user"}` — e chi lo trasforma
    # in un identificatore e' il risolutore, con l'utente che sta davvero chiedendo. E'
    # la stessa divisione dei periodi: il modello dice *«quest'anno»*, il risolutore sa
    # che giorno e'.
    #
    # Due rifiuti, e sono la ragione per cui la cosa e' sicura:
    #
    # * **senza un utente non si indovina.** Se chi ha chiamato non ha passato l'attore
    #   la condizione non si risolve: meglio un turno che fallisce di uno che filtra
    #   sull'utente sbagliato;
    # * **non su un campo qualunque.** `current_user` ha senso solo dove dall'altra
    #   parte c'e' un utente Odoo, e lo dice il binding, non il modello. Su
    #   `crm_lead.city` e' un errore, e un errore dichiarato — non un dominio che
    #   confronta una citta' con il numero 2.
    if value.get("kind") == "identity":
        if value.get("reference") != "current_user":
            failures.append(ResolutionFailure(
                condition["ref"],
                f"identity {value.get('reference')!r} has no resolution"))
            return []
        if binding.identity != "user":
            failures.append(ResolutionFailure(
                condition["ref"],
                "current_user was asked of an attribute that does not name a user"))
            return []
        if actor is None:
            failures.append(ResolutionFailure(
                condition["ref"], "current_user has no user to resolve to"))
            return []
        return [(field, "=", actor)]

    if predicate in ("is_true", "is_false"):
        return [(field, "=", predicate == "is_true")]
    if predicate == "is_set":
        return [(field, "!=", False)]
    if predicate == "is_not_set":
        return [(field, "=", False)]
    if predicate == "is_empty":
        return [(field, "in", [False, ""])]
    if predicate == "is_not_empty":
        return ["!", (field, "in", [False, ""])]
    if predicate == "starts_with":
        return [(field, "=ilike", f"{value.get('text', '')}%")]

    if predicate == "approximately":
        low, high = _approximate(value, resolvers, condition["ref"], failures)
        if low is None:
            return []
        return ["&", (field, ">=", low), (field, "<=", high)]

    if predicate in ("on", "before", "after", "within") or (
            predicate == "between" and value.get("kind") == "temporal"):
        return _temporal_domain(field, predicate, value, instant, condition, periods,
                                failures, is_instant=binding.type == "datetime")

    if predicate == "between":
        return ["&", (field, ">=", value.get("from")), (field, "<=", value.get("to"))]

    operator = OPERATORS.get(predicate)
    if operator is None:
        failures.append(ResolutionFailure(
            condition["ref"], f"predicate {predicate!r} has no resolution"))
        return []
    return [(field, operator, _literal(value))]


def _literal(value: dict):
    kind = value.get("kind")
    if kind == "enum":
        return list(value.get("items", []))
    if kind in ("text", "reference"):
        return value.get("text")
    return value.get("value")


def _approximate(value, resolvers, reference, failures):
    """*"Circa centomila"* into 90 000 - 110 000, from the dictionary's rule (§9.3).

    The model declared **that** the value is approximate and **which** rule applies;
    it never decided the tolerance. If the named rule does not exist, nothing is
    invented: *"i clienti importanti"* has no objective meaning, and in the absence of
    a defined resolver the correct outcome is a clarification, not a guess.
    """
    name = value.get("resolver")
    rule = (resolvers or {}).get(name)
    if rule is None:
        failures.append(ResolutionFailure(
            reference, f"resolver {name!r} is not defined in the dictionary"))
        return None, None
    amount = value.get("value", 0)
    if rule.get("kind") == "relative_percent":
        delta = abs(amount) * rule["percent"] / 100.0
    elif rule.get("kind") == "absolute_tolerance":
        delta = rule["amount"]
    else:
        failures.append(ResolutionFailure(
            reference, f"resolver {name!r} is not applicable to a number"))
        return None, None
    return amount - delta, amount + delta


def _temporal_domain(field, predicate, value, instant, condition, periods, failures,
                     *, is_instant: bool = False):
    """Un periodo in due estremi, nell'unita' della colonna che interroga.

    **`is_instant` e' la correzione del 3 agosto 2026, e vale un numero sbagliato al
    giorno.** Odoo conserva i `datetime` in **UTC**; il calendario qui sopra lavora
    sull'ora dell'utente, perche' *«questo mese»* deve voler dire il suo mese (§9.2).
    Fino a oggi i due non si incontravano: gli estremi uscivano come date nude —
    `('create_date', '>=', '2026-08-03')` — e finivano confrontati con una colonna in
    UTC, senza che nessuno convertisse.

    Su un'installazione italiana d'estate lo scarto e' di due ore: *«i lead creati
    oggi»* **escludeva** quelli inseriti fra mezzanotte e le due e **includeva** quelli
    di ieri sera dopo le 22. Un numero plausibile, vicino a quello giusto, e sbagliato —
    e su una finestra corta e' l'8% delle righe. Il campo colpito e' `create_date`, cioe'
    proprio quello che **D117** (la decisione che lo toglie dai campi tecnici perche'
    *«quando e' stato creato»* e' la prima cosa che si intende) ha appena rimesso nel
    catalogo.

    Su un campo `date` non c'e' niente da convertire: un giorno e' un giorno in ogni
    fuso, e il confronto resta quello di prima.
    """
    try:
        window = calendar_module.resolve(value, instant)
    except calendar_module.UnresolvableExpression as error:
        failures.append(ResolutionFailure(condition["ref"], str(error)))
        return []

    # D67: the interpretation shows the **resolved** period, not the expression. Si
    # mostra il periodo **locale**, che e' quello che l'utente ha chiesto: dirgli che
    # «oggi» va dal 2 alle 22:00 sarebbe esatto e incomprensibile.
    periods.append(
        (condition["ref"], calendar_module.describe(value, instant, predicate)))

    if is_instant:
        start, end = instant.as_utc(window.start), instant.as_utc(window.end)
    else:
        start, end = window.start.isoformat(), window.end.isoformat()
    if predicate == "before":
        return [(field, "<", start)]
    if predicate == "after":
        return [(field, ">=", end)]
    # `on`, `within` and a temporal `between` are all the same question: is the date
    # inside the resolved period. Half-open, so the upper bound is strict.
    return ["&", (field, ">=", start), (field, "<", end)]
