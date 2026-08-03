"""The Executor — one of the two components that know Odoo exists (§6.5, D68).

Surface: the ORM's search, read and aggregate, and nothing else. Together with the
Catalogue this is the **whole** upgrade surface of the product across Odoo major
versions, which is why it stays thin even when enriching it would be convenient.

## Count before retrieval (D68)

    "Eighty records with no context are read as **all of them**. It is a plausible
    misunderstanding produced by the interface rather than by the model."

So the total is counted first and travels with the result, and the interpretation
says *"the first 80 of 1 243"*. Two queries instead of one, and the second is a
`search_count` — the cheapest question the ORM answers.

## No privileged path, anywhere

The Executor runs with the identity and the permissions of the user, and with the
company context rebuilt from the turn (D40). Record rules apply because the ORM
applies them: there is no `sudo` here and the syntactic check of D24 makes sure there
never is. That is what makes "record access is always bound to the user's
permissions" a property of the code rather than a promise.
"""

from dataclasses import dataclass, field

from ..resolution.plan import Plan


@dataclass(frozen=True)
class Group:
    """Una riga di aggregazione: i valori dei raggruppamenti e le misure calcolate.

    `keys` segue l'ordine di `plan.group_by`, `measures` e' indicizzata come la misura
    e' scritta nello stato — `("avg", "expected_revenue")` — piu' `("count", "")` che
    c'e' sempre, perche' un aggregato senza il numero di righe che lo compongono e' un
    numero di cui non si sa quanto fidarsi.
    """

    keys: tuple = ()
    measures: dict = field(default_factory=dict)


class Result:
    """What an execution produced, with the count that gives it meaning.

    `total` is not decoration: `records` is at most `limit` long, and without the
    total the user cannot tell a complete answer from a truncated one.

    `groups` e' vuoto per un elenco semplice e pieno quando lo stato porta misure o
    raggruppamenti. **Fino al 3 agosto 2026 era sempre vuoto**, perche' la funzione che
    lo riempie non era chiamata da nessuno: `SUM`, `AVG`, `MIN` e `MAX` esistevano nel
    contratto, nel piano e nell'interpretazione mostrata all'utente, e non venivano
    calcolati in nessun punto. *«Qual e' il fatturato medio dei lead»* restituiva
    l'elenco dei lead.
    """

    def __init__(self, records, total: int, plan: Plan, groups=()):
        self.records = records
        self.total = total
        self.plan = plan
        self.groups = tuple(groups)

    @property
    def truncated(self) -> bool:
        return self.total > len(self.records)

    def describe(self) -> str:
        """The phrase of D68: *"the first 80 of 1 243"*, or just the number."""
        if not self.truncated:
            return f"{self.total}"
        return f"i primi {len(self.records)} di {self.total}"


def run(env, plan: Plan) -> Result:
    """Il piano eseguito per intero: le righe, il totale e — se ce ne sono — i numeri.

    **L'unica porta.** Prima ce n'erano due, `execute` e `aggregate`, e il pipeline ne
    conosceva una sola: l'aggregazione era scritta, provata e senza chiamanti. Una
    funzione sola toglie al chiamante la scelta che sbagliava, ed e' lo stesso rimedio
    di `_apply_and_present` (D121) applicato un gradino piu' in basso.

    **Le righe si leggono sempre**, anche quando ci sono misure, perche' **D89** (la
    delibera che risolve la contraddizione fra §5.6 e §6.7: una misura senza
    raggruppamento resta una lista) dice che quella e' una lista, e una lista senza
    righe non e' niente. Il costo in piu' e' una `_read_group`, e solo quando lo stato
    porta misure o raggruppamenti.
    """
    result = execute(env, plan)
    if not (plan.measures or plan.group_by):
        return result
    return Result(records=result.records, total=result.total, plan=plan,
                  groups=aggregate(env, plan))


def execute(env, plan: Plan) -> Result:
    """Run a Plan with the user's rights and return the records plus the total.

    `env` carries the identity and the company context; building it from the turn is
    the caller's job, because on the cron process of D20a there is no request to
    inherit it from and pretending otherwise is how D40 gets violated.
    """
    model = env[plan.model]

    # D68: the count first. It is also the cheapest way to refuse an interrogation
    # that would return a hundred thousand rows before any of them are read.
    total = model.search_count(list(plan.domain))

    records = model.search(
        list(plan.domain),
        limit=plan.limit,
        order=plan.order or None,
    )
    return Result(records=records, total=total, plan=plan)


#: La misura che c'e' sempre, qualunque cosa lo stato chieda. `_read_group` la sa dare
#: gratis, ed e' cio' che dice quante righe stanno dietro una media.
COUNT_MEASURE = ("count", "")


def aggregate(env, plan: Plan) -> tuple:
    """Grouped aggregation, for the pivot and graph views.

    Uses `_read_group`, which is the ORM's own aggregation: doing the grouping in
    Python would read every record to add up a column, which is the difference
    between a query and an outage.

    Restituisce righe gia' leggibili — `Group` — e non le tuple grezze dell'ORM: chi
    legge un risultato non deve sapere che `_read_group` mette prima i raggruppamenti e
    poi le misure, nell'ordine in cui gliele hai chieste.
    """
    model = env[plan.model]
    # `count` non nomina un attributo (§8.5) e nell'ORM si chiede come `__count`.
    wanted = [measure for measure in plan.measures if measure[1]]
    aggregates = [f"{field}:{function}" for function, field in wanted]
    aggregates.append("__count")

    rows = model._read_group(
        domain=list(plan.domain),
        groupby=list(plan.group_by),
        aggregates=aggregates,
        limit=plan.limit,
    )

    depth = len(plan.group_by)
    groups = []
    for row in rows:
        values = list(row)
        keys, measured = tuple(values[:depth]), values[depth:]
        measures = {measure: value for measure, value in zip(wanted, measured)}
        measures[COUNT_MEASURE] = measured[-1]
        groups.append(Group(keys=keys, measures=measures))
    return tuple(groups)
