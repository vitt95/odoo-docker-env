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

from ..resolution.plan import Plan


class Result:
    """What an execution produced, with the count that gives it meaning.

    `total` is not decoration: `records` is at most `limit` long, and without the
    total the user cannot tell a complete answer from a truncated one.
    """

    def __init__(self, records, total: int, plan: Plan):
        self.records = records
        self.total = total
        self.plan = plan

    @property
    def truncated(self) -> bool:
        return self.total > len(self.records)

    def describe(self) -> str:
        """The phrase of D68: *"the first 80 of 1 243"*, or just the number."""
        if not self.truncated:
            return f"{self.total}"
        return f"i primi {len(self.records)} di {self.total}"


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


def aggregate(env, plan: Plan):
    """Grouped aggregation, for the pivot and graph views.

    Uses `_read_group`, which is the ORM's own aggregation: doing the grouping in
    Python would read every record to add up a column, which is the difference
    between a query and an outage.
    """
    model = env[plan.model]
    aggregates = [
        f"{field}:{function}" for function, field in plan.measures if field
    ]
    if any(not field for _, field in plan.measures):
        aggregates.append("__count")
    return model._read_group(
        domain=list(plan.domain),
        groupby=list(plan.group_by),
        aggregates=aggregates or ["__count"],
        limit=plan.limit,
    )
