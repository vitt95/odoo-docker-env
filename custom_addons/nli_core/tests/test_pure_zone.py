"""Runs the pure-zone suite inside the Odoo suite.

**Why a bridge is needed.** Odoo's runner skips any test that does not inherit
from its `BaseCase`: `odoo/tests/tag_selector.py:92` refuses a test with no
`test_tags`. The pure-zone tests are plain `unittest.TestCase` on purpose — they
must run without importing the platform, which is the only way they can prove the
code under them does not import it either.

So they cannot be collected directly, and importing them into `tests/__init__.py`
would bind names that never execute — a suite that looks larger than it is. This
bridge runs them explicitly instead, and reports their failures verbatim.

The pure suite also runs, faster and without a database, via
`python3 tools/pure/run.py` and in CI. This test exists so that
`./manage.sh test <db>` cannot pass while the contract is broken.
"""

import importlib
import io
import pkgutil
import unittest
from pathlib import Path

from odoo.tests.common import BaseCase, tagged

PURE_TESTS_PACKAGE = "odoo.addons.nli_core.pure_tests"
PURE_TESTS_DIR = Path(__file__).resolve().parent.parent / "pure_tests"


def _pure_suite() -> tuple[unittest.TestSuite, list[str]]:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    names: list[str] = []
    for info in sorted(pkgutil.iter_modules([str(PURE_TESTS_DIR)]), key=lambda i: i.name):
        if not info.name.startswith("test_"):
            continue
        module = importlib.import_module(f"{PURE_TESTS_PACKAGE}.{info.name}")
        suite.addTests(loader.loadTestsFromModule(module))
        names.append(info.name)
    return suite, names


@tagged("post_install", "-at_install", "nli_contract")
class TestPureZone(BaseCase):
    """The contract, the Applicator, the canonical form and the equivalences."""

    def test_the_pure_zone_suite_passes(self):
        suite, names = _pure_suite()

        # A bridge that found nothing to run would report success forever — the
        # same failure mode the boundary checks of D24 guard against.
        self.assertTrue(names, "no pure test module was discovered")
        self.assertGreater(suite.countTestCases(), 0, "the pure suite is empty")

        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
        self.assertTrue(
            result.wasSuccessful(),
            f"{len(result.failures)} failures, {len(result.errors)} errors in the "
            f"pure zone ({', '.join(names)}):\n{stream.getvalue()}",
        )
