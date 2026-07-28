#!/usr/bin/env python3
"""Run the pure-zone tests with plain Python — no Odoo, no database, no network.

    python3 tools/pure/run.py             # every pure test of every nli_* module
    python3 tools/pure/run.py canonical   # only modules whose name matches

Discovery is by directory, not by list: every `nli_*/pure_tests/test_*.py` runs. A
list would go stale the first time a module gains a suite nobody remembered to
register, and a suite that silently stops running is worse than one that never
existed.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pure import bootstrap  # noqa: E402  (path bootstrap must come first)

# `nli_engine` imports the contract as Odoo resolves it; the alias makes the same
# line work here against the same files.
bootstrap.install_all()
bootstrap.install_odoo_alias()


def build_suite(pattern: str | None) -> tuple[unittest.TestSuite, list[str]]:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    found: list[str] = []

    for module in bootstrap.modules_with_pure_tests():
        directory = bootstrap.ADDONS / module / "pure_tests"
        for info in sorted(pkgutil.iter_modules([str(directory)]), key=lambda i: i.name):
            if not info.name.startswith("test_"):
                continue
            name = f"{module}.pure_tests.{info.name}"
            if pattern and pattern not in name:
                continue
            suite.addTests(loader.loadTestsFromModule(importlib.import_module(name)))
            found.append(name)

    if not found:
        raise SystemExit(
            f"no pure test module matched {pattern!r} — a run that tests nothing "
            "must not look like a run that passed"
        )
    return suite, found


def main(argv: list[str]) -> int:
    pattern = argv[0] if argv else None
    suite, found = build_suite(pattern)
    if pattern:
        print("running: " + ", ".join(found))
    runner = unittest.TextTestRunner(verbosity=2 if pattern else 1)
    return 0 if runner.run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
