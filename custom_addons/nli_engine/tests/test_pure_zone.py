"""Runs the engine's pure-zone suite inside the Odoo suite.

Same bridge and same reason as the other two: Odoo's runner skips a test without
`test_tags` (`odoo/tests/tag_selector.py:92`), and the engine's tests are plain
`unittest.TestCase` so they can run without a database and without a provider.
"""

import importlib
import io
import pkgutil
import unittest
from pathlib import Path

from odoo.tests.common import BaseCase, tagged

PACKAGE = "odoo.addons.nli_engine.pure_tests"
DIRECTORY = Path(__file__).resolve().parent.parent / "pure_tests"


@tagged("post_install", "-at_install", "nli_engine")
class TestPureZone(BaseCase):
    """The Interpreter, the prompt, and the controls of D76 and D77."""

    def test_the_pure_zone_suite_passes(self):
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        names: list[str] = []
        for info in sorted(pkgutil.iter_modules([str(DIRECTORY)]), key=lambda i: i.name):
            if not info.name.startswith("test_"):
                continue
            module = importlib.import_module(f"{PACKAGE}.{info.name}")
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
