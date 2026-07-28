"""Each of the four checks, shown failing on a fixture and passing on a clean tree.

Run with:

    python3 -m unittest discover -s tools/arch/tests -t .

The last test runs the four checks against the real repository, so this one
command is the whole gate of D24.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tools.arch import check_imports, check_manifest, check_purity, check_syntax, runner
from tools.arch.report import CheckResult
from tools.arch.spec import ModuleSpec, PureZone

MANIFEST_TEMPLATE = """\
{{
    "name": "{name}",
    "summary": "fixture",
    "version": "{version}",
    "category": "Test",
    "author": "fixture",
    "license": "{license}",
    "depends": {depends!r},
    "installable": True,
    "application": False,
}}
"""


def write_module(
    addons: Path,
    name: str,
    depends: list[str],
    *,
    version: str = "18.0.1.0.0",
    license_: str = "LGPL-3",
    packages: tuple[str, ...] = ("models",),
    sources: dict[str, str] | None = None,
) -> Path:
    """Create a minimal, loadable Odoo module in `addons`."""
    module_dir = addons / name
    module_dir.mkdir(parents=True)
    (module_dir / "__manifest__.py").write_text(
        MANIFEST_TEMPLATE.format(
            name=name, version=version, license=license_, depends=depends
        ),
        encoding="utf-8",
    )
    imports = "".join(f"from . import {package}\n" for package in packages)
    (module_dir / "__init__.py").write_text(imports, encoding="utf-8")
    for package in packages:
        (module_dir / package).mkdir()
        (module_dir / package / "__init__.py").write_text('"""fixture."""\n', encoding="utf-8")
    for relative, body in (sources or {}).items():
        path = module_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
    return module_dir


def spec_of(*modules: ModuleSpec) -> dict[str, ModuleSpec]:
    return {module.name: module for module in modules}


CORE = ModuleSpec(
    name="nli_core",
    responsibility="core",
    nli_depends=frozenset(),
    platform_depends=frozenset({"base"}),
    odoo_packages=frozenset({"models"}),
)
ENGINE = ModuleSpec(
    name="nli_engine",
    responsibility="engine",
    nli_depends=frozenset({"nli_core"}),
    platform_depends=frozenset(),
    odoo_packages=frozenset({"models"}),
)
SEMANTICS = ModuleSpec(
    name="nli_semantics",
    responsibility="semantics",
    nli_depends=frozenset({"nli_core"}),
    platform_depends=frozenset(),
    odoo_packages=frozenset({"models"}),
)
FIXTURE_SPEC = spec_of(CORE, ENGINE, SEMANTICS)


class FixtureCase(unittest.TestCase):
    """Base class giving each test an isolated addons directory."""

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.addons = Path(self._temporary.name) / "custom_addons"
        self.addons.mkdir()
        self.addCleanup(self._temporary.cleanup)

    def write_clean_tree(self) -> None:
        write_module(self.addons, "nli_core", ["base"])
        write_module(self.addons, "nli_engine", ["nli_core"])
        write_module(self.addons, "nli_semantics", ["nli_core"])

    def rules(self, result: CheckResult) -> list[str]:
        return [violation.rule for violation in result.violations]

    def assertVacuityRejected(self, result: CheckResult) -> None:
        self.assertTrue(result.vacuous)
        self.assertFalse(
            result.passed,
            "a check that inspected nothing must not report success",
        )


class TestManifestCheck(FixtureCase):
    def run_check(self) -> CheckResult:
        return check_manifest.run(
            addons_dir=self.addons, modules=FIXTURE_SPEC, repo_root=self.addons.parent
        )

    def test_clean_tree_passes(self):
        self.write_clean_tree()
        result = self.run_check()
        self.assertEqual(result.violations, [])
        self.assertEqual(result.inspected, 3)
        self.assertTrue(result.passed)

    def test_undeclared_edge_between_peers_is_reported(self):
        write_module(self.addons, "nli_core", ["base"])
        write_module(self.addons, "nli_engine", ["nli_core", "nli_semantics"])
        write_module(self.addons, "nli_semantics", ["nli_core"])
        result = self.run_check()
        self.assertIn("undeclared edge in the dependency graph", self.rules(result))
        detail = " ".join(str(violation) for violation in result.violations)
        self.assertIn("nli_engine -> nli_semantics", detail)
        self.assertIn("receives the catalogue", detail)

    def test_missing_edge_is_reported(self):
        write_module(self.addons, "nli_core", ["base"])
        write_module(self.addons, "nli_engine", [])
        write_module(self.addons, "nli_semantics", ["nli_core"])
        result = self.run_check()
        self.assertIn("missing edge in the dependency graph", self.rules(result))

    def test_undeclared_platform_dependency_is_reported(self):
        self.write_clean_tree()
        write_module(self.addons, "throwaway", [])  # not an nli_* module: ignored
        (self.addons / "nli_engine" / "__manifest__.py").write_text(
            MANIFEST_TEMPLATE.format(
                name="nli_engine",
                version="18.0.1.0.0",
                license="LGPL-3",
                depends=["nli_core", "sale"],
            ),
            encoding="utf-8",
        )
        result = self.run_check()
        self.assertIn("undeclared platform dependency", self.rules(result))

    def test_wrong_license_and_series_are_reported(self):
        write_module(self.addons, "nli_core", ["base"], license_="MIT", version="17.0.1.0.0")
        write_module(self.addons, "nli_engine", ["nli_core"])
        write_module(self.addons, "nli_semantics", ["nli_core"])
        result = self.run_check()
        self.assertIn("wrong manifest value", self.rules(result))
        self.assertIn("wrong Odoo series in version", self.rules(result))

    def test_module_directory_nobody_declared_is_reported(self):
        self.write_clean_tree()
        write_module(self.addons, "nli_smuggled", ["nli_core"])
        result = self.run_check()
        self.assertIn("undeclared module", self.rules(result))

    def test_missing_module_is_reported(self):
        write_module(self.addons, "nli_core", ["base"])
        write_module(self.addons, "nli_engine", ["nli_core"])
        result = self.run_check()
        self.assertIn("declared module is missing", self.rules(result))

    def test_package_never_imported_is_reported(self):
        self.write_clean_tree()
        (self.addons / "nli_core" / "__init__.py").write_text(
            '"""forgot to import models."""\n', encoding="utf-8"
        )
        result = self.run_check()
        self.assertIn("declared package is never imported", self.rules(result))

    def test_empty_tree_is_not_a_pass(self):
        self.assertVacuityRejected(self.run_check())


class TestImportsCheck(FixtureCase):
    def run_check(self) -> CheckResult:
        return check_imports.run(
            addons_dir=self.addons, modules=FIXTURE_SPEC, repo_root=self.addons.parent
        )

    def test_clean_tree_passes(self):
        self.write_clean_tree()
        result = self.run_check()
        self.assertEqual(result.violations, [])
        self.assertTrue(result.passed)

    def test_import_beyond_dependencies_is_reported(self):
        self.write_clean_tree()
        (self.addons / "nli_engine" / "models" / "interpreter.py").write_text(
            "from odoo.addons.nli_semantics.models import catalogue\n", encoding="utf-8"
        )
        result = self.run_check()
        self.assertIn("import beyond declared dependencies", self.rules(result))

    def test_from_odoo_addons_import_form_is_caught(self):
        self.write_clean_tree()
        (self.addons / "nli_engine" / "models" / "interpreter.py").write_text(
            "from odoo.addons import nli_semantics\n", encoding="utf-8"
        )
        result = self.run_check()
        self.assertIn("import beyond declared dependencies", self.rules(result))

    def test_provider_library_outside_the_adapter_is_reported(self):
        self.write_clean_tree()
        (self.addons / "nli_core" / "models" / "leak.py").write_text(
            "import requests\n", encoding="utf-8"
        )
        result = self.run_check()
        self.assertIn("provider or network library outside the adapter", self.rules(result))
        self.assertIn("V5, V7", str(result.violations[0]))

    def test_provider_library_inside_the_adapter_is_allowed(self):
        self.write_clean_tree()
        (self.addons / "nli_engine" / "models" / "client.py").write_text(
            "import httpx\nimport anthropic\n", encoding="utf-8"
        )
        result = self.run_check()
        self.assertEqual(result.violations, [])

    def test_relative_imports_are_never_violations(self):
        self.write_clean_tree()
        (self.addons / "nli_core" / "models" / "local.py").write_text(
            "from .. import contract\nfrom . import sibling\n", encoding="utf-8"
        )
        result = self.run_check()
        self.assertEqual(result.violations, [])

    def test_empty_tree_is_not_a_pass(self):
        self.assertVacuityRejected(self.run_check())


class TestSyntaxCheck(FixtureCase):
    def run_check(self) -> CheckResult:
        return check_syntax.run(
            addons_dir=self.addons, modules=FIXTURE_SPEC, repo_root=self.addons.parent
        )

    def write_source(self, body: str, *, module: str = "nli_core") -> None:
        (self.addons / module / "models" / "probe.py").write_text(
            textwrap.dedent(body), encoding="utf-8"
        )

    def test_clean_tree_passes(self):
        self.write_clean_tree()
        result = self.run_check()
        self.assertEqual(result.violations, [])
        self.assertTrue(result.passed)

    def test_raw_cursor_is_reported(self):
        self.write_clean_tree()
        self.write_source(
            """
            def count(env):
                env.cr.execute("SELECT count(*) FROM sale_order")
                return env.cr.fetchone()
            """
        )
        result = self.run_check()
        self.assertIn("direct PostgreSQL access", self.rules(result))
        self.assertIn("V3", str(result.violations[0]))

    def test_cursor_alias_is_reported(self):
        self.write_clean_tree()
        self.write_source(
            """
            class Probe:
                def count(self):
                    self._cr.execute("SELECT 1")
            """
        )
        result = self.run_check()
        self.assertIn("direct PostgreSQL access", self.rules(result))

    def test_psycopg2_import_is_reported(self):
        self.write_clean_tree()
        self.write_source("import psycopg2\n")
        result = self.run_check()
        self.assertIn("direct PostgreSQL access", self.rules(result))

    def test_sudo_is_reported(self):
        self.write_clean_tree()
        self.write_source(
            """
            def read_all(env):
                return env["sale.order"].sudo().search([])
            """
        )
        result = self.run_check()
        self.assertIn("privilege elevation", self.rules(result))
        self.assertIn("V2", str(result.violations[0]))

    def test_superuser_id_is_reported(self):
        self.write_clean_tree()
        self.write_source(
            """
            from odoo import SUPERUSER_ID

            def escalate(env):
                return env(user=SUPERUSER_ID)
            """
        )
        result = self.run_check()
        self.assertIn("privilege elevation", self.rules(result))

    def test_su_keyword_is_reported(self):
        self.write_clean_tree()
        self.write_source(
            """
            def escalate(env):
                return env(su=True)
            """
        )
        result = self.run_check()
        self.assertIn("privilege elevation", self.rules(result))

    def test_privilege_elevation_is_allowed_in_tests_only(self):
        """§6.3 scopes the rule to the interrogation paths, and so does the check.

        A test that verifies what another user may see has to construct that user's
        environment. Banning it there makes the property untestable, and a security
        property nobody can test is worse than one nobody can bypass.
        """
        self.write_clean_tree()
        source = """
        def peek(env, other):
            return env["res.partner"].with_user(other).search([])
        """
        (self.addons / "nli_core" / "models" / "probe.py").write_text(
            textwrap.dedent(source), encoding="utf-8")
        self.assertIn("privilege elevation", self.rules(self.run_check()))

        (self.addons / "nli_core" / "models" / "probe.py").unlink()
        tests = self.addons / "nli_core" / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (tests / "test_access.py").write_text(textwrap.dedent(source), encoding="utf-8")
        self.assertNotIn("privilege elevation", self.rules(self.run_check()))

    def test_raw_sql_is_forbidden_in_tests_too(self):
        """No such exclusion for SQL: a raw cursor in a test is a raw cursor."""
        self.write_clean_tree()
        tests = self.addons / "nli_core" / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (tests / "test_sql.py").write_text(
            "def probe(env):\n    env.cr.execute('SELECT 1')\n", encoding="utf-8")
        self.assertIn("direct PostgreSQL access", self.rules(self.run_check()))

    def test_mentions_in_prose_are_not_violations(self):
        self.write_clean_tree()
        self.write_source(
            '''
            """No sudo() and no cr.execute() anywhere in this module."""

            # Explaining why cr.execute is forbidden must not fail the build.
            FORBIDDEN = "cr.execute"
            '''
        )
        result = self.run_check()
        self.assertEqual(result.violations, [])

    def test_empty_tree_is_not_a_pass(self):
        self.assertVacuityRejected(self.run_check())


class TestPurityCheck(FixtureCase):
    ZONES = (
        PureZone(path="nli_core/application", reason="fixture", protects="D9"),
    )

    def run_check(self, zones=None, deterministic=()) -> CheckResult:
        return check_purity.run(
            addons_dir=self.addons,
            zones=self.ZONES if zones is None else zones,
            deterministic_zones=deterministic,
            repo_root=self.addons.parent,
        )

    def write_zone(self, body: str) -> None:
        zone = self.addons / "nli_core" / "application"
        zone.mkdir(parents=True, exist_ok=True)
        (zone / "__init__.py").write_text(textwrap.dedent(body), encoding="utf-8")

    def test_pure_zone_passes(self):
        self.write_clean_tree()
        self.write_zone(
            """
            def apply(state, operations):
                return {**state, "operations": list(operations)}
            """
        )
        result = self.run_check()
        self.assertEqual(result.violations, [])
        self.assertTrue(result.passed)

    def test_clock_import_is_reported(self):
        self.write_clean_tree()
        self.write_zone("import datetime\n")
        result = self.run_check()
        self.assertIn("impure import in a pure zone", self.rules(result))

    def test_platform_import_is_reported(self):
        self.write_clean_tree()
        self.write_zone("from odoo import fields\n")
        result = self.run_check()
        self.assertIn("impure import in a pure zone", self.rules(result))

    def test_clock_call_without_import_is_reported(self):
        """The call matters even when the clock arrives as an argument.

        `fields.Datetime.now()` needs no import inside the zone: this is exactly
        the shape the fourth check of §6.4 exists to catch.
        """
        self.write_clean_tree()
        self.write_zone(
            """
            def apply(state, fields):
                return {**state, "at": fields.Datetime.now()}
            """
        )
        result = self.run_check()
        self.assertIn("non-deterministic call in a pure zone", self.rules(result))

    def test_a_deterministic_zone_may_compute_with_dates(self):
        """`04` §4.6 — the Resolver is aware of time; it does not read it.

        Without the distinction the choice would be between a Resolver that cannot do
        arithmetic and a Resolver nobody checks.
        """
        self.write_clean_tree()
        self.write_zone("""
            from datetime import timedelta

            def window(start, days):
                return start + timedelta(days=days)
            """)
        result = self.run_check(zones=(), deterministic=self.ZONES)
        self.assertEqual(result.violations, [])

    def test_a_deterministic_zone_still_may_not_read_the_clock(self):
        self.write_clean_tree()
        self.write_zone("""
            from datetime import date

            def window():
                return date.today()
            """)
        result = self.run_check(zones=(), deterministic=self.ZONES)
        self.assertIn("non-deterministic call in a pure zone", self.rules(result))

    def test_a_pure_zone_may_not_import_dates_at_all(self):
        self.write_clean_tree()
        self.write_zone("from datetime import timedelta\n")
        self.assertIn("impure import in a pure zone", self.rules(self.run_check()))

    def test_missing_zone_is_reported_instead_of_silently_passing(self):
        self.write_clean_tree()
        result = self.run_check()
        self.assertIn("declared pure zone is missing", self.rules(result))
        self.assertFalse(result.passed)

    def test_zone_without_code_is_reported(self):
        self.write_clean_tree()
        (self.addons / "nli_core" / "application").mkdir(parents=True, exist_ok=True)
        result = self.run_check()
        self.assertIn("declared pure zone has no code", self.rules(result))


class TestRepository(unittest.TestCase):
    """The four checks against the real repository — the gate of D24 itself."""

    def test_all_four_checks_pass(self):
        results = runner.run_all()
        self.assertEqual(len(results), 4)
        failures = [
            f"{result.name}: " + "; ".join(str(v) for v in result.violations)
            for result in results
            if not result.passed
        ]
        self.assertEqual(
            failures,
            [],
            "\n".join(failures) or "",
        )

    def test_every_check_inspected_something(self):
        for result in runner.run_all():
            with self.subTest(check=result.name):
                self.assertGreater(
                    result.inspected,
                    0,
                    f"{result.name} inspected nothing: it would report success forever",
                )


if __name__ == "__main__":
    unittest.main()
