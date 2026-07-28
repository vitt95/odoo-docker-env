"""Check 1 — Manifest.

Verifies that the graph declared in `__manifest__.py` is the graph of
`ai/04-architettura.md` §6.2, exactly.

Why this check exists at all: in Odoo the dependency graph is not documentation,
it is the loader. A module that does not declare a dependency cannot use what
that dependency provides — the boundary is enforced by the platform. All this
check has to do is make sure the declaration never drifts from the design
(§6.1: an architecture described in a document is a convention).
"""

from __future__ import annotations

import ast
from pathlib import Path

from .report import CheckResult, Violation
from .sources import parse, parse_manifest, relative_to_repo
from .spec import (
    ADDONS_DIR,
    MANIFEST_VERSION_PREFIX,
    MODULE_PREFIX,
    MODULES,
    NON_DEPENDENCIES,
    REPO_ROOT,
    REQUIRED_MANIFEST_KEYS,
    ModuleSpec,
)

NAME = "Manifest"


def _imported_packages(init_path: Path) -> set[str]:
    """Sub-packages actually imported by a module's `__init__.py`.

    Read from the syntax tree rather than by searching the text: a docstring
    that merely mentions `import models` would satisfy a substring test, and a
    check that a comment can satisfy is not a check.
    """
    try:
        tree = parse(init_path)
    except SyntaxError:
        return set()

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # `from . import models`
            if node.module is None:
                imported.update(alias.name for alias in node.names)
            else:
                imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
    return imported


def _forbidden_edge_reason(source: str, target: str) -> tuple[str, str]:
    """The named product constraint behind a forbidden edge, if there is one."""
    for rule in NON_DEPENDENCIES:
        if rule.source == source and rule.target == target:
            return rule.protects, rule.rationale
    return "D18", "dependencies point towards the core, never between peers"


def _check_module(
    module: ModuleSpec,
    addons_dir: Path,
    repo_root: Path,
    result: CheckResult,
) -> None:
    module_dir = addons_dir / module.name
    manifest_path = module_dir / "__manifest__.py"
    init_path = module_dir / "__init__.py"

    if not module_dir.is_dir():
        result.add(Violation(
            rule="declared module is missing",
            location=relative_to_repo(module_dir, repo_root),
            detail=f"{module.name} is in the spec but not on disk",
            protects="D18",
        ))
        return

    for required in (manifest_path, init_path):
        if not required.is_file():
            result.add(Violation(
                rule="module is not loadable",
                location=relative_to_repo(required, repo_root),
                detail="file is required for Odoo to load the module",
                protects="D18",
            ))
    # A package Odoo never imports registers nothing, and reports no error.
    for package in sorted(module.odoo_packages):
        package_init = module_dir / package / "__init__.py"
        if not package_init.is_file():
            result.add(Violation(
                rule="declared package is not importable",
                location=relative_to_repo(package_init, repo_root),
                detail=f"{module.name} declares the '{package}' package in spec.py",
                protects="D18",
            ))
        elif init_path.is_file():
            if package not in _imported_packages(init_path):
                result.add(Violation(
                    rule="declared package is never imported",
                    location=relative_to_repo(init_path, repo_root),
                    detail=(
                        f"'{package}' exists but {module.name}/__init__.py does not "
                        "import it: Odoo would load the module and register nothing"
                    ),
                    protects="D18",
                ))

    if not manifest_path.is_file():
        return

    location = relative_to_repo(manifest_path, repo_root)
    try:
        manifest = parse_manifest(manifest_path)
    except (SyntaxError, ValueError) as error:
        result.add(Violation(
            rule="manifest is not a literal dictionary",
            location=location,
            detail=f"{type(error).__name__}: {error}",
            protects="D18",
        ))
        return

    result.inspected += 1

    if not isinstance(manifest, dict):
        result.add(Violation(
            rule="manifest is not a dictionary",
            location=location,
            detail=f"parsed as {type(manifest).__name__}",
            protects="D18",
        ))
        return

    for key, expected in REQUIRED_MANIFEST_KEYS.items():
        if key not in manifest:
            result.add(Violation(
                rule="missing manifest key",
                location=location,
                detail=f"'{key}' is required",
                protects="D18",
            ))
        elif expected is not None and manifest[key] != expected:
            result.add(Violation(
                rule="wrong manifest value",
                location=location,
                detail=f"'{key}' must be {expected!r}, found {manifest[key]!r}",
                protects="D18",
            ))

    version = manifest.get("version", "")
    if not isinstance(version, str) or not version.startswith(MANIFEST_VERSION_PREFIX):
        result.add(Violation(
            rule="wrong Odoo series in version",
            location=location,
            detail=f"version must start with {MANIFEST_VERSION_PREFIX!r}, found {version!r}",
            protects="D18",
        ))

    declared = manifest.get("depends", [])
    if not isinstance(declared, list):
        result.add(Violation(
            rule="'depends' is not a list",
            location=location,
            detail=f"found {type(declared).__name__}",
            protects="D18",
        ))
        return

    declared_nli = {name for name in declared if str(name).startswith(MODULE_PREFIX)}
    declared_platform = {name for name in declared if not str(name).startswith(MODULE_PREFIX)}

    for extra in sorted(declared_nli - module.nli_depends):
        protects, rationale = _forbidden_edge_reason(module.name, extra)
        result.add(Violation(
            rule="undeclared edge in the dependency graph",
            location=location,
            detail=f"{module.name} -> {extra} is not in 04 §6.2: {rationale}",
            protects=protects,
        ))
    for missing in sorted(module.nli_depends - declared_nli):
        result.add(Violation(
            rule="missing edge in the dependency graph",
            location=location,
            detail=f"{module.name} -> {missing} is required by 04 §6.2 but not declared",
            protects="D18",
        ))
    for extra in sorted(declared_platform - module.platform_depends):
        result.add(Violation(
            rule="undeclared platform dependency",
            location=location,
            detail=(
                f"{module.name} depends on '{extra}', which is not in the spec. "
                "Widening the platform surface is a decision: add it to spec.py"
            ),
            protects="D18",
        ))
    for missing in sorted(module.platform_depends - declared_platform):
        result.add(Violation(
            rule="missing platform dependency",
            location=location,
            detail=f"{module.name} must depend on '{missing}'",
            protects="D18",
        ))


def run(
    *,
    addons_dir: Path = ADDONS_DIR,
    modules: dict[str, ModuleSpec] | None = None,
    repo_root: Path = REPO_ROOT,
) -> CheckResult:
    modules = MODULES if modules is None else modules
    result = CheckResult(name=NAME, unit="manifests")

    for module in modules.values():
        _check_module(module, addons_dir, repo_root, result)

    # A module directory nobody declared is the exact way a five-module design
    # becomes a six-module one without a decision.
    if addons_dir.is_dir():
        for candidate in sorted(addons_dir.iterdir()):
            if not candidate.is_dir() or not candidate.name.startswith(MODULE_PREFIX):
                continue
            if candidate.name not in modules:
                result.add(Violation(
                    rule="undeclared module",
                    location=relative_to_repo(candidate, repo_root),
                    detail=(
                        f"'{candidate.name}' exists but is not in spec.py. "
                        "A new module in the product is a decision (D18)"
                    ),
                    protects="D18",
                ))

    return result
