"""Coverage — decomposed, and the reason it is decomposed (D34, `06` §6).

**Pure zone.**

> **Catalogue coverage** = the percentage of cases in which **all** the references
> needed by the correct interpretation were present in the catalogue given to the
> Interpreter.

The quantifier is essential. A case missing one reference out of five is an
**uncovered** case, because the correct interpretation stays unreachable. Averaging
per reference instead of per case would report 80% for a case that cannot succeed.

## Why the decomposition is mandatory and not optional

The two components have different causes and different remedies (§6.3):

| Component | Phase | If low |
|---|---|---|
| entity | A / B | enrich the T1 terms of the entities |
| attributes | C | review the exposure rules (§5.3) or the budget |

And the second **should be near 100% by construction**: in phase C there is no
selection (D32). A materially lower value therefore does not mean the selection is
weak — it means the **exposure rules are wrong**, a useful attribute classified as
technical or a budget set too tight. That is a precise diagnosis, and it is why the
decomposition is required rather than encouraged.

## Read with accuracy, always

§5.4 of `07` and RC3: 87% accuracy with 92% coverage describes a completely different
situation from 87% accuracy with 99.5% coverage. In the first the room for improvement
is not in the model. Reporting one without the other invites the wrong work, so
`Report` renders both or neither.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


def is_entity_ref(ref: str) -> bool:
    """An entity reference has no dot; an attribute or category reference has one."""
    return "." not in ref


@dataclass(frozen=True)
class CaseCoverage:
    """Coverage of one case, decomposed."""

    covered: bool
    entity_covered: bool
    attributes_covered: bool
    missing: tuple[str, ...]

    @property
    def missing_entities(self) -> tuple[str, ...]:
        return tuple(ref for ref in self.missing if is_entity_ref(ref))

    @property
    def missing_attributes(self) -> tuple[str, ...]:
        return tuple(ref for ref in self.missing if not is_entity_ref(ref))


def case_coverage(necessary: frozenset[str], available: frozenset[str]) -> CaseCoverage:
    """Whether every necessary reference was available, and which were not."""
    missing = tuple(sorted(necessary - available))
    return CaseCoverage(
        covered=not missing,
        entity_covered=not any(is_entity_ref(ref) for ref in missing),
        attributes_covered=not any(not is_entity_ref(ref) for ref in missing),
        missing=missing,
    )


@dataclass
class Report:
    """Coverage over a population of cases."""

    cases: int = 0
    covered: int = 0
    entity_covered: int = 0
    attributes_covered: int = 0
    #: How often each reference was missing. It is the enrichment queue of §6.4, in
    #: frequency order: the terms users say and the dictionary does not know.
    missing: Counter = field(default_factory=Counter)

    def add(self, coverage: CaseCoverage) -> None:
        self.cases += 1
        self.covered += 1 if coverage.covered else 0
        self.entity_covered += 1 if coverage.entity_covered else 0
        self.attributes_covered += 1 if coverage.attributes_covered else 0
        for ref in coverage.missing:
            self.missing[ref] += 1

    def _share(self, count: int) -> float:
        return count / self.cases if self.cases else 0.0

    @property
    def overall(self) -> float:
        return self._share(self.covered)

    @property
    def entity(self) -> float:
        return self._share(self.entity_covered)

    @property
    def attributes(self) -> float:
        return self._share(self.attributes_covered)

    def meets(self, threshold: float = 0.99) -> bool:
        """D34 sets the threshold at >= 99%, on the decomposed measure."""
        return self.entity >= threshold and self.attributes >= threshold

    def render(self) -> str:
        return (
            f"copertura complessiva {self.overall:.1%} "
            f"(entita {self.entity:.1%}, attributi {self.attributes:.1%}) "
            f"su {self.cases} casi"
        )
