"""The four boundary checks of D24, run together with one exit code.

Ordering is not cosmetic: the manifest check comes first because the other three
interpret the graph it validates. A failure there makes the rest ambiguous, so
it is reported first and named first.
"""

from __future__ import annotations

import argparse
from typing import Callable, Sequence

from . import (check_imports, check_manifest, check_owl, check_purity,
               check_syntax)
from .report import CheckResult

CHECKS: tuple[Callable[[], CheckResult], ...] = (
    check_manifest.run,
    check_imports.run,
    check_syntax.run,
    check_purity.run,
    check_owl.run,
)

_GREEN = "\033[32m"
_RED = "\033[31m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def run_all() -> list[CheckResult]:
    return [check() for check in CHECKS]


def format_report(results: Sequence[CheckResult], *, colour: bool = True) -> str:
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if colour else text

    lines: list[str] = [paint("Boundary checks — D24, 04 §6.4", _BOLD), ""]

    for result in results:
        if result.passed:
            status = paint("PASS", _GREEN)
        else:
            status = paint("FAIL", _RED)
        lines.append(
            f"  {status}  {result.name}  "
            f"({result.inspected} {result.unit}, {len(result.violations)} violations)"
        )
        if result.vacuous:
            lines.append(
                "        inspected nothing — a check with no subject reports "
                "success forever"
            )
        for violation in result.violations:
            lines.append(f"        {violation}")

    failed = [result for result in results if not result.passed]
    lines.append("")
    if failed:
        names = ", ".join(result.name for result in failed)
        lines.append(paint(f"FAILED: {names}", _RED))
    else:
        lines.append(paint(f"All {len(results)} boundary checks pass.", _GREEN))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools/arch/run.py",
        description="Verify the architecture boundaries of the nli_* modules (D24).",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="plain output, for logs and CI",
    )
    arguments = parser.parse_args(argv)

    results = run_all()
    print(format_report(results, colour=not arguments.no_colour))
    return 0 if all(result.passed for result in results) else 1
