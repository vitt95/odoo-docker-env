"""The circuit breaker of `05` §4.4, as policy without a clock.

    Without this mechanism, a provider outage fills the queue with turns destined to
    fail after the maximum wait, saturating the pool for minutes after the problem
    has already been fixed.

The state is three numbers and the decisions are arithmetic on them, so the policy
belongs in the pure zone and the instant arrives as an argument. The *holder* of the
state — one breaker per process, mutated from several threads — lives in `runtime/`,
where a lock is allowed to exist.

**Half-open matters more than open.** A breaker that reopens all at once sends the
full pool at a provider that has been down for a minute, which is how a recovering
service is knocked over by its clients. After the cooling period exactly one turn is
let through: it either closes the circuit or reopens it for another period.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

#: `05` §6. Five consecutive failures, not five failures: an isolated timeout in a
#: healthy provider must not open the circuit, or the breaker becomes the outage.
DEFAULT_THRESHOLD = 5

#: Seconds before a probe is admitted. Long enough that the provider is not being
#: polled, short enough that a resolved outage does not keep refusing users.
DEFAULT_COOLING_SECONDS = 30.0

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


@dataclass(frozen=True)
class Breaker:
    """Immutable state; every transition returns a new one."""

    consecutive_failures: int = 0
    opened_at: float | None = None
    threshold: int = DEFAULT_THRESHOLD
    cooling_seconds: float = DEFAULT_COOLING_SECONDS

    def state(self, now: float) -> str:
        if self.opened_at is None:
            return CLOSED
        if now - self.opened_at >= self.cooling_seconds:
            return HALF_OPEN
        return OPEN

    def admits(self, now: float) -> bool:
        """Whether a turn may be attempted. Half-open admits — the probe is a turn.

        The probe is a real user's request rather than a synthetic ping, and that is
        deliberate: a ping proves the socket answers, a turn proves the provider
        answers *this* product's requests. The cost of being wrong is one turn.
        """
        return self.state(now) != OPEN

    def after_success(self) -> "Breaker":
        return replace(self, consecutive_failures=0, opened_at=None)

    def after_failure(self, now: float) -> "Breaker":
        failures = self.consecutive_failures + 1
        if failures >= self.threshold:
            return replace(self, consecutive_failures=failures, opened_at=now)
        return replace(self, consecutive_failures=failures)
