"""The pool size is derived, never chosen (D20b, registry §6.4).

RE4 is the risk this file exists to close: *"the pool is sized as though the work
were computation"*. It is not — it is almost entirely network wait, so threads are
the right tool and the CPU is not the ceiling. The real ceiling is the **number of
PostgreSQL connections**: every thread in the pool holds one, and a pool chosen by
feel exhausts them. The failure then shows up on the ERP, not on the product, which
is precisely the class of failure this whole part exists to prevent.

    connessioni_totali = (worker_http x 1)
                       + (max_cron_threads x 1)
                       + (N_dispatcher x dimensione_pool)

    vincolo:  connessioni_totali <= 0,8 x db_maxconn

The 20% margin is for the service processes, and it is not negotiable by rounding:
`connections_within_budget` is what the eighth row of the load proof (§7.2) asserts.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Registry §6.4. A fraction rather than a subtraction because the margin has to
#: scale with the configuration: 20% of 100 connections is not 20% of 20.
SAFETY_FRACTION = 0.8

#: `05` §6. The ceiling is not a limit of the formula, it is a limit of the design:
#: a pool wider than this on one dispatcher record adds latency variance rather than
#: capacity, and the way to add capacity is N dispatcher records (D20f, registry §5.1).
DEFAULT_POOL_CEILING = 8


@dataclass(frozen=True)
class Deployment:
    """The connection consumers of one Odoo installation."""

    db_maxconn: int
    http_workers: int
    max_cron_threads: int
    dispatchers: int = 1

    @property
    def budget(self) -> int:
        """Connections available to the dispatcher pools, after everything else."""
        allowed = int(self.db_maxconn * SAFETY_FRACTION)
        return allowed - self.http_workers - self.max_cron_threads


def pool_size(deployment: Deployment, *, ceiling: int = DEFAULT_POOL_CEILING) -> int:
    """The pool size this installation can afford, per dispatcher record.

    Returns at least 1. A configuration too tight to afford even one thread is a
    configuration error, and the honest answer there is a dispatcher that runs one
    turn at a time — not one that refuses to start, leaving every turn `pending`
    with no explanation anywhere.
    """
    if deployment.dispatchers < 1:
        raise ValueError("an installation with no dispatcher executes nothing")
    per_dispatcher = deployment.budget // deployment.dispatchers
    return max(1, min(ceiling, per_dispatcher))


def connections_used(deployment: Deployment, pool: int) -> int:
    return (
        deployment.http_workers
        + deployment.max_cron_threads
        + deployment.dispatchers * pool
    )


def connections_within_budget(deployment: Deployment, pool: int) -> bool:
    """The constraint of §6.4, as a predicate the load proof can assert."""
    return connections_used(deployment, pool) <= int(
        deployment.db_maxconn * SAFETY_FRACTION
    )
