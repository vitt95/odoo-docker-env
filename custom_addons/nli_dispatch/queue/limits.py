"""The five load limits of D20c, as decisions about numbers.

| | Limit | Value | On exceeding |
|---|---|---|---|
| L1 | interpretations in flight per session | 1 | the previous one is cancelled |
| L2 | global concurrency | = pool size | by construction, see `pool.py` |
| L3 | queue depth | 3 x pool | immediate refusal at acceptance |
| L4 | maximum age of a turn | 30 s | discarded without being interpreted |
| L5 | requests per user per minute | 20 | refusal, declared temporary |

**L1 cancels rather than queues.** A person does not ask two questions at once: if
they write a second one while the first is running, they changed their mind. Queueing
would buy two interpretations of which the first is already of no interest — wasted
cost and, worse, a result that appears and is immediately replaced.

**L4 is the one that lets the queue recover.** A turn queued for more than thirty
seconds has lost its recipient: the user gave up, rephrased or changed page.
Interpreting it costs money and holds the pool against live requests. Discarding
expired turns is what turns a spike into a delay instead of a permanent backlog.

**Ages arrive as numbers, not as timestamps.** The zone may not read a clock (D82),
and that is not an inconvenience here: it is what makes "expires at exactly 30
seconds" a test rather than a nap.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Refusal reasons. A closed set: the message table of `messages.py` is keyed on it,
#: and a reason with no message would reach the user as a blank refusal.
QUEUE_DEPTH = "queue_depth"
RATE = "rate"
PROVIDER_DOWN = "provider_down"
EXPIRED = "expired"

REFUSAL_REASONS = frozenset({QUEUE_DEPTH, RATE, PROVIDER_DOWN, EXPIRED})


@dataclass(frozen=True)
class Limits:
    """The five values of `05` §6.

    None of them is a project constant — §6 says so in as many words — which is why
    they are a record passed in rather than module-level integers. What is normative
    is that they exist and that exceeding one produces an explicit refusal.
    """

    #: L1 — interpretations in flight for one session.
    in_flight_per_session: int = 1
    #: L2 — the pool is the global concurrency; see `pool.py`.
    pool: int = 8
    #: L3 — queue depth, as a multiple of the pool.
    queue_depth_factor: int = 3
    #: L4 — seconds a turn may wait before it is discarded unexecuted.
    max_age_seconds: int = 30
    #: L5 — requests per user per minute.
    requests_per_minute: int = 20

    @property
    def queue_depth(self) -> int:
        return self.pool * self.queue_depth_factor


DEFAULT_LIMITS = Limits()


@dataclass(frozen=True)
class Admission:
    """What acceptance decided, and why.

    `supersedes` is not a refusal and must not be presented as one: the request was
    accepted, and an earlier one for the same session is being cancelled (L1).
    """

    accepted: bool
    reason: str | None = None
    supersedes: bool = False

    def __post_init__(self):
        if self.reason is not None and self.reason not in REFUSAL_REASONS:
            raise ValueError(f"unknown refusal reason: {self.reason!r}")
        if not self.accepted and self.reason is None:
            raise ValueError("a refusal without a reason cannot be explained to anyone")


def admit(
    *,
    in_flight_for_session: int,
    queued: int,
    requests_last_minute: int,
    provider_available: bool = True,
    limits: Limits = DEFAULT_LIMITS,
) -> Admission:
    """Decide whether a new turn is accepted, in the order the limits are checked.

    The order is itself a decision. Rate first, because a client looping produces
    both a high rate *and* a deep queue, and telling it that the system is busy would
    describe the consequence of its own behaviour as a property of the system. Depth
    second, because it protects everyone already waiting. L1 last, because it is not
    a refusal at all.
    """
    if not provider_available:
        # §4.4: with the circuit open, accepting means filling the queue with turns
        # that will fail after the maximum wait, saturating the pool for minutes
        # after the provider has recovered.
        return Admission(accepted=False, reason=PROVIDER_DOWN)
    if requests_last_minute >= limits.requests_per_minute:
        return Admission(accepted=False, reason=RATE)
    if queued >= limits.queue_depth:
        return Admission(accepted=False, reason=QUEUE_DEPTH)
    return Admission(
        accepted=True,
        supersedes=in_flight_for_session >= limits.in_flight_per_session,
    )


def expired(age_seconds: float, *, limits: Limits = DEFAULT_LIMITS) -> bool:
    """Whether a turn has waited past L4.

    Strictly greater: a turn that has waited exactly the maximum has not exceeded it.
    The boundary is asserted in a test because "off by one second" is invisible in
    production and obvious in a spike.
    """
    return age_seconds > limits.max_age_seconds


def batch_size(*, pending: int, limits: Limits = DEFAULT_LIMITS) -> int:
    """How many turns to claim in one round: never more than can be executed.

    `05` §6: *"no benefit in acquiring more than can be run"*. Claiming more would
    park turns in `running` with nobody running them, which is exactly the state the
    recovery cron of §5.3 exists to clean up — manufacturing work for the mechanism
    that repairs failures is a poor way to use it.
    """
    return max(0, min(pending, limits.pool))
