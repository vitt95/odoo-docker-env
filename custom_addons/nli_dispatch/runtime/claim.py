"""Reserving a batch of queue rows, and the one statement in the product that is SQL.

`05` §3.3 specifies the acquisition as `SELECT … FOR UPDATE SKIP LOCKED`, and D20f's
scale path — *"N dispatcher records, not N instances"* — rests on it: several
dispatchers may claim concurrently only because a locked row is skipped rather than
waited for. Odoo's ORM has no way to express that, and Odoo's own scheduler writes
the same statement by hand (`ir_cron.py:140`).

**This is a derogation from V3, and it is scoped rather than granted** (D95). The rule
that raw SQL bypasses record rules stands: what makes this admissible is that the
statement selects **identifiers of the product's own queue table** — no business data,
no other table, no join — and every read that follows goes through the ORM under the
requesting user's identity. `tools/arch/spec.py` admits `cr.execute` in this file
only, and only for a statement carrying `FOR UPDATE SKIP LOCKED` on `nli_queue_item`;
any other statement here fails the build exactly as it would anywhere else, and a
test shows it failing.

**Why not avoid SQL altogether.** Two alternatives were measured against this one. An
ORM claim (`search` then `write`) is safe today, because V-A gives one dispatcher
record exactly one concurrent execution cluster-wide — and it becomes unsafe on the
day somebody adds the second dispatcher, silently, which is when nobody is looking.
Static sharding by `id % N` needs no lock at all, and strands an entire shard when
the configured N stops matching the number of dispatchers: turns nobody claims, no
error anywhere. Between one narrowly scoped statement and a misconfiguration that
quietly executes nothing, the statement is the smaller risk.
"""

from __future__ import annotations

from odoo import fields

#: The whole derogation, as one constant, so that reviewing it means reading a line.
CLAIM_STATEMENT = (
    "SELECT id FROM nli_queue_item "
    "WHERE lane = %s AND state = 'pending' "
    "ORDER BY id LIMIT %s "
    "FOR UPDATE SKIP LOCKED"
)


def claim(env, *, lane: str, size: int):
    """Lock and reserve up to `size` pending rows of `lane`.

    Returns the reserved rows, already moved to `running`. The caller commits: §3.4
    requires the reservation to be **confirmed before** the work starts, so that an
    interrupted process leaves rows in `running` for the recovery cron of §5.3 rather
    than rows in `pending` that a second dispatcher takes a second time.
    """
    if size <= 0:
        return env["nli.queue.item"].browse()

    env.cr.execute(CLAIM_STATEMENT, (lane, size))
    identifiers = [row[0] for row in env.cr.fetchall()]
    items = env["nli.queue.item"].browse(identifiers)
    for item in items:
        # Per row rather than in one write: the attempt counter is what bounds the
        # retries of §5.3, and a batch write would set them all to the same value.
        item.write({
            "state": "running",
            "started_at": fields.Datetime.now(),
            "attempts": item.attempts + 1,
        })
    return items


def pending_count(env, *, lane: str) -> int:
    """How much is left, for the decision to re-trigger at the end of a cycle."""
    return env["nli.queue.item"].search_count([
        ("lane", "=", lane), ("state", "=", "pending"),
    ])
