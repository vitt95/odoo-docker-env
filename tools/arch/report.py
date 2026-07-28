"""Shared result types for the boundary checks.

The `inspected` counter is not decoration. A check that reports zero violations
because it looked at zero files is indistinguishable, in a pipeline, from a
check that passed — and it stays green forever. Every check therefore declares
what it inspected, and the runner treats an empty inspection as a failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Violation:
    """One broken rule, located precisely enough to fix without searching."""

    rule: str
    location: str
    detail: str
    protects: str

    def __str__(self) -> str:
        return f"{self.location}: {self.rule} [{self.protects}] — {self.detail}"


@dataclass
class CheckResult:
    """Outcome of one of the four checks of `04` §6.4."""

    name: str
    #: What the check looked at, and how much of it. Used to reject vacuity.
    inspected: int = 0
    #: Human-readable unit of inspection, e.g. "manifests", "python files".
    unit: str = "items"
    violations: list[Violation] = field(default_factory=list)

    def add(self, violation: Violation) -> None:
        self.violations.append(violation)

    @property
    def vacuous(self) -> bool:
        return self.inspected == 0

    @property
    def passed(self) -> bool:
        return not self.violations and not self.vacuous
