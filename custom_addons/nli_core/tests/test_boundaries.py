"""Live half of the architectural check (D24, `ai/04-architettura.md` §6.4).

The division of labour with `tools/arch/` is deliberate and worth stating, because
duplicating it would be the easy mistake:

* `tools/arch/` compares the **declared** graph against the **designed** graph.
  It is static, needs no database, and is the authority on what the graph should
  be. It is the only place where the design is transcribed;
* this suite verifies what only a running registry can show — that the five
  modules actually install, and that the registry's dependency records agree
  with the manifests it loaded them from. It never restates the design, so the
  two can never disagree.

The behavioural invariants of §6.4 — the Applicator is pure over real inputs, the
Validator is always traversed, the Presenter always receives state and result
together — arrive here as their components do, in parts 2 and 4.
"""

from odoo.modules.module import get_manifest
from odoo.tests.common import TransactionCase, tagged

PRODUCT_MODULES = (
    "nli_core",
    "nli_semantics",
    "nli_engine",
    "nli_dispatch",
    "nli_web",
    "nli_observability",
)


@tagged("post_install", "-at_install", "nli_boundaries")
class TestBoundaries(TransactionCase):
    """Boundary properties that require the module registry to exist."""

    def test_declared_modules_are_installed(self):
        """Every module of the product installs.

        A skeleton that does not install is not a skeleton, and the failure
        surfaces here rather than during the first part that adds a model.
        """
        records = self.env["ir.module.module"].search(
            [("name", "in", list(PRODUCT_MODULES))]
        )
        found = {record.name: record.state for record in records}

        missing = sorted(set(PRODUCT_MODULES) - set(found))
        self.assertFalse(
            missing,
            f"modules absent from the registry: {missing}. "
            "Update the addons path or the module list.",
        )

        not_installed = sorted(
            name for name, state in found.items() if state != "installed"
        )
        self.assertFalse(
            not_installed,
            f"modules present but not installed: {not_installed}",
        )

    def test_registry_dependencies_match_the_manifests(self):
        """The registry graph is the manifest graph.

        `tools/arch/check_manifest.py` proves the manifests match the design.
        This proves the running system matches the manifests — the other half of
        the same statement, and the half a static check cannot make.
        """
        modules = self.env["ir.module.module"].search(
            [("name", "in", list(PRODUCT_MODULES))]
        )
        for module in modules:
            with self.subTest(module=module.name):
                manifest = get_manifest(module.name)
                self.assertTrue(
                    manifest,
                    f"no manifest readable for {module.name}",
                )
                declared = set(manifest.get("depends", []))
                in_registry = {
                    dependency.name for dependency in module.dependencies_id
                }
                self.assertEqual(
                    in_registry,
                    declared,
                    f"{module.name}: the registry and the manifest disagree on "
                    "the dependency graph",
                )

    def test_product_modules_are_acyclic_towards_the_core(self):
        """Dependencies point towards the core, never between peripheral modules.

        Read from the manifests, so the rule is checked against the graph the
        platform actually loaded rather than against a copy of the design.
        """
        edges = {
            name: {
                dependency
                for dependency in get_manifest(name).get("depends", [])
                if dependency in PRODUCT_MODULES
            }
            for name in PRODUCT_MODULES
        }

        self.assertEqual(
            edges["nli_core"],
            set(),
            "nli_core depends on another product module: the core would no "
            "longer be the root of the graph (V5, P5)",
        )

        # Reachability: no cycle, and every module reaches the core.
        for start in PRODUCT_MODULES:
            reached: set[str] = set()
            frontier = [start]
            while frontier:
                current = frontier.pop()
                for target in edges[current]:
                    self.assertNotEqual(
                        target,
                        start,
                        f"dependency cycle through {start}",
                    )
                    if target not in reached:
                        reached.add(target)
                        frontier.append(target)
            if start != "nli_core":
                self.assertIn(
                    "nli_core",
                    reached,
                    f"{start} does not reach nli_core: it is outside the graph "
                    "of 04 §6.2",
                )
