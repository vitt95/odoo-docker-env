"""Check 4 — Architectural (static half).

`ai/04-architettura.md` §6.4 calls this the most valuable and the most
neglected of the four, and says why: a test that the Applicator returns the same
result for the same inputs *is a test of the architecture*. It fails at the
exact moment someone introduces a dependency on the clock — while the fix is
still cheap.

That test cannot be written yet: there is no Applicator. What can be written
today, and must be, is the invariant it rests on — the pure zones of
`spec.PURE_ZONES` neither import the platform nor reach for anything that
changes between two runs. This is the half of the fourth check that does not
need the product to exist, and it is the half that protects the corpus (D82,
D84): a corpus whose expected states depend on when they were computed is not a
key, it is a snapshot.

The behavioural half — Applicator purity over real inputs, Validator always
traversed, Presenter always receiving state and result together — lives in the
Odoo test suites under each module's `tests/`, and grows as the components do.
"""

from __future__ import annotations

import ast
from pathlib import Path

from .report import CheckResult, Violation
from .sources import (
    attribute_chain,
    imported_names,
    iter_python_files,
    parse,
    relative_to_repo,
    suffixes,
)
from .spec import (
    ADDONS_DIR,
    DETERMINISTIC_ZONE_ALLOWED_IMPORTS,
    DETERMINISTIC_ZONES,
    PURE_ZONE_FORBIDDEN_CALLS,
    PURE_ZONE_FORBIDDEN_IMPORTS,
    PURE_ZONES,
    REPO_ROOT,
    PureZone,
)

NAME = "Architectural (pure zones)"


class _DeterministicMarker(PureZone):
    """A zone checked for clock reads but allowed to import the date libraries."""

    def __init__(self, zone: PureZone) -> None:
        super().__init__(path=zone.path, reason=zone.reason, protects=zone.protects)


def _zone_files(root: Path) -> list[Path]:
    """The Python files of a zone, which may be a directory or a single file."""
    if root.is_file():
        return [root]
    return list(iter_python_files(root))


def _check_file(path: Path, zone: PureZone, repo_root: Path, result: CheckResult,
                *, allowed_imports: frozenset[str] = frozenset()) -> None:
    location_base = relative_to_repo(path, repo_root)
    try:
        tree = parse(path)
    except SyntaxError as error:
        result.add(Violation(
            rule="file does not parse",
            location=f"{location_base}:{error.lineno or 0}",
            detail=str(error.msg),
            protects=zone.protects,
        ))
        return

    result.inspected += 1

    for imported in imported_names(tree):
        if imported.level > 0:
            continue
        if (imported.top_level in PURE_ZONE_FORBIDDEN_IMPORTS
                and imported.top_level not in allowed_imports):
            result.add(Violation(
                rule="impure import in a pure zone",
                location=f"{location_base}:{imported.line}",
                detail=(
                    f"'{imported.dotted}' is not allowed in {zone.path}: {zone.reason}"
                ),
                protects=zone.protects,
            ))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = attribute_chain(node.func)
        if not chain:
            continue
        hit = suffixes(chain) & PURE_ZONE_FORBIDDEN_CALLS
        if hit:
            result.add(Violation(
                rule="non-deterministic call in a pure zone",
                location=f"{location_base}:{node.lineno}",
                detail=(
                    f"'{chain}' reaches outside its arguments. {zone.reason}"
                ),
                protects=zone.protects,
            ))


def run(
    *,
    addons_dir: Path = ADDONS_DIR,
    zones: tuple[PureZone, ...] = PURE_ZONES,
    deterministic_zones: tuple[PureZone, ...] = DETERMINISTIC_ZONES,
    repo_root: Path = REPO_ROOT,
) -> CheckResult:
    result = CheckResult(name=NAME, unit="python files in pure zones")

    # Deterministic zones are checked with the same call bans and a wider import
    # allowance: computing with dates is not reading the clock (04 §4.6).
    for zone in list(zones) + [
        _DeterministicMarker(zone) for zone in deterministic_zones
    ]:
        root = addons_dir / zone.path
        if not root.exists():
            # A pure zone that does not exist is how this check becomes vacuous:
            # it would report zero violations forever, for the wrong reason.
            result.add(Violation(
                rule="declared pure zone is missing",
                location=relative_to_repo(root, repo_root),
                detail=(
                    f"{zone.path} is declared pure in spec.py but absent. "
                    "Either create it or remove the declaration"
                ),
                protects=zone.protects,
            ))
            continue

        files = _zone_files(root)
        if not files:
            result.add(Violation(
                rule="declared pure zone has no code",
                location=relative_to_repo(root, repo_root),
                detail=f"{zone.path} contains no Python file to verify",
                protects=zone.protects,
            ))
            continue

        allowed = (DETERMINISTIC_ZONE_ALLOWED_IMPORTS
                   if isinstance(zone, _DeterministicMarker) else frozenset())
        for path in files:
            _check_file(path, zone, repo_root, result, allowed_imports=allowed)

    return result
