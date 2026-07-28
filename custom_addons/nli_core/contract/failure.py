"""Typed validation failures.

§12.7 assigns each level a different treatment: levels 1-2 are a **system
defect** to be analysed, level 3 is material for enriching the dictionary,
level 5 is expected behaviour. A failure therefore has to carry its level and a
stable code — a message string cannot be counted, and what §12.7 asks for is
counting.

The code is stable on purpose. It is what the metrics of `07` aggregate on, and
what the structured error handed back for the single repair attempt (D15) names.

**Pure zone.**
"""

from __future__ import annotations

from dataclasses import dataclass

#: Level names, for reports (§12.2).
LEVEL_NAMES: dict[int, str] = {
    1: "structure",
    2: "vocabulary",
    3: "resolution",
    4: "coherence",
    5: "cost",
}


@dataclass(frozen=True)
class Failure:
    """One validation failure.

    `path` locates the failure inside the artefact using a dotted/indexed path
    (`operations[2].condition.value.kind`). Without it, a failure in the third
    operation of an envelope is a needle in a haystack for whoever has to fix it,
    and unusable in the structured error of the repair attempt.
    """

    level: int
    code: str
    path: str
    detail: str

    def __str__(self) -> str:
        name = LEVEL_NAMES.get(self.level, str(self.level))
        return f"L{self.level} {name} [{self.code}] {self.path}: {self.detail}"


def failed(failures: list[Failure]) -> bool:
    return bool(failures)


def first_failing_level(failures: list[Failure]) -> int | None:
    """The lowest level that failed.

    §12.2: the levels apply in sequence and the first that fails stops the chain.
    The caller decides what to do with the outcome by level (§12.7), so the level
    has to be answerable without inspecting every failure.
    """
    return min((failure.level for failure in failures), default=None)
