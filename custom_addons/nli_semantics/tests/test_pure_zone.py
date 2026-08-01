"""Runs the pure-zone suite of nli_semantics inside the Odoo suite.

Same bridge, same reason as `nli_core/tests/test_pure_zone.py`: Odoo's runner skips
any test without `test_tags` (`odoo/tests/tag_selector.py:92`), and the pure tests are
plain `unittest.TestCase` on purpose — they must run without importing the platform,
which is the only way they can prove the code under them does not import it either.
"""

import importlib
import io
import pkgutil
import unittest
from pathlib import Path

from odoo.tests.common import BaseCase, tagged

PURE_TESTS_PACKAGE = "odoo.addons.nli_semantics.pure_tests"
PURE_TESTS_DIR = Path(__file__).resolve().parent.parent / "pure_tests"


@tagged("post_install", "-at_install", "nli_semantics")
class TestPureZone(BaseCase):
    """The dictionary and the catalogue."""

    def test_the_pure_zone_suite_passes(self):
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        names: list[str] = []
        for info in sorted(pkgutil.iter_modules([str(PURE_TESTS_DIR)]), key=lambda i: i.name):
            if not info.name.startswith("test_"):
                continue
            module = importlib.import_module(f"{PURE_TESTS_PACKAGE}.{info.name}")
            suite.addTests(loader.loadTestsFromModule(module))
            names.append(info.name)

        self.assertTrue(names, "no pure test module was discovered")
        self.assertGreater(suite.countTestCases(), 0, "the pure suite is empty")

        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
        self.assertTrue(
            result.wasSuccessful(),
            f"{len(result.failures)} failures, {len(result.errors)} errors in the "
            f"pure zone ({', '.join(names)}):\n{stream.getvalue()}",
        )
