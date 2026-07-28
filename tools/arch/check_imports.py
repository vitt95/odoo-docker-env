"""Check 2 — Imports.

Two rules from `ai/04-architettura.md` §6.3:

* no module imports beyond its declared dependencies. The manifest check proves
  the *declaration* is right; this one proves the code stays inside it. Odoo
  enforces the graph at load time only for what it loads — a plain
  `from odoo.addons.nli_engine import ...` inside a helper crosses the boundary
  without the loader ever objecting;
* only `nli_engine` imports provider libraries. This is what makes V5 (the
  provider is substitutable) and V7 (the Interpreter cannot send data it does
  not hold) verifiable rather than asserted: if outbound network access exists
  in exactly one module, the traffic can be reasoned about by reading one file.
"""

from __future__ import annotations

from pathlib import Path

from .report import CheckResult, Violation
from .sources import imported_names, iter_python_files, parse, relative_to_repo
from .spec import (
    ADDONS_DIR,
    MODULE_PREFIX,
    MODULES,
    PROVIDER_LIBRARIES,
    PROVIDER_LIBRARY_OWNER,
    REPO_ROOT,
    ModuleSpec,
    transitive_nli_depends,
)

NAME = "Imports"

ODOO_ADDONS_PREFIX = "odoo.addons."


def _reachable_addons(module: str, modules: dict[str, ModuleSpec]) -> set[str]:
    """Addons `module` may import from: itself, its `nli_*` closure, platform deps.

    The closure — not just the direct edges — because that is what Odoo actually
    permits at runtime. Forbidding what the platform allows would make the check
    a style rule; forbidding exactly what the platform allows keeps it a
    statement about the architecture.
    """
    reachable = {module}
    reachable |= set(modules[module].platform_depends)
    for dependency in transitive_nli_depends(module, modules):
        reachable.add(dependency)
        reachable |= set(modules[dependency].platform_depends)
    return reachable


def _check_file(
    path: Path,
    module: ModuleSpec,
    reachable: set[str],
    repo_root: Path,
    result: CheckResult,
) -> None:
    location_base = relative_to_repo(path, repo_root)
    try:
        tree = parse(path)
    except SyntaxError as error:
        result.add(Violation(
            rule="file does not parse",
            location=f"{location_base}:{error.lineno or 0}",
            detail=str(error.msg),
            protects="D24",
        ))
        return

    result.inspected += 1

    for imported in imported_names(tree):
        location = f"{location_base}:{imported.line}"

        if imported.level > 0:
            # Relative import: cannot leave the module by construction.
            continue

        if imported.dotted.startswith(ODOO_ADDONS_PREFIX):
            addon = imported.dotted[len(ODOO_ADDONS_PREFIX):].split(".")[0]
            if addon and addon not in reachable:
                kind = (
                    "product module" if addon.startswith(MODULE_PREFIX)
                    else "Odoo addon"
                )
                result.add(Violation(
                    rule="import beyond declared dependencies",
                    location=location,
                    detail=(
                        f"{module.name} imports {kind} '{addon}', which it does "
                        "not depend on (04 §6.2)"
                    ),
                    protects="D18",
                ))
            continue

        if imported.top_level in PROVIDER_LIBRARIES and module.name != PROVIDER_LIBRARY_OWNER:
            result.add(Violation(
                rule="provider or network library outside the adapter",
                location=location,
                detail=(
                    f"'{imported.dotted}' may only be imported by "
                    f"{PROVIDER_LIBRARY_OWNER} (04 §6.3)"
                ),
                protects="V5, V7",
            ))


def run(
    *,
    addons_dir: Path = ADDONS_DIR,
    modules: dict[str, ModuleSpec] | None = None,
    repo_root: Path = REPO_ROOT,
) -> CheckResult:
    modules = MODULES if modules is None else modules
    result = CheckResult(name=NAME, unit="python files")

    for name, module in modules.items():
        module_dir = addons_dir / name
        reachable = _reachable_addons(name, modules)
        for path in iter_python_files(module_dir):
            _check_file(path, module, reachable, repo_root, result)

    return result
