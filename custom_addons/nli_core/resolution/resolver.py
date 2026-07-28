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
                            failures, periods)
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


def _filter_domain(node, bindings, instant, resolvers, failures, periods) -> list:
    if node is None:
        return []
    if state_module.is_connective(node):
        children = [
            _filter_domain(child, bindings, instant, resolvers, failures, periods)
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
    return _condition_domain(node, bindings, instant, resolvers, failures, periods)


def _condition_domain(condition, bindings, instant, resolvers, failures, periods) -> list:
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
                                failures)

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


def _temporal_domain(field, predicate, value, instant, condition, periods, failures):
    try:
        window = calendar_module.resolve(value, instant)
    except calendar_module.UnresolvableExpression as error:
        failures.append(ResolutionFailure(condition["ref"], str(error)))
        return []

    # D67: the interpretation shows the **resolved** period, not the expression.
    periods.append((condition["ref"], calendar_module.describe(value, instant)))

    start, end = window.start.isoformat(), window.end.isoformat()
    if predicate == "before":
        return [(field, "<", start)]
    if predicate == "after":
        return [(field, ">=", end)]
    # `on`, `within` and a temporal `between` are all the same question: is the date
    # inside the resolved period. Half-open, so the upper bound is strict.
    return ["&", (field, ">=", start), (field, "<", end)]
