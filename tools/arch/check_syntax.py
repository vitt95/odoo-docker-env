"""Check 3 — Syntactic.

Forbids, across every `nli_*` module, the two constructs of
`ai/04-architettura.md` §6.3 that erode a product constraint without producing
an error:

* **direct PostgreSQL access** (V3). A raw cursor bypasses record rules, and a
  query that bypasses record rules returns *more* rows, not fewer — the failure
  mode nobody reports;
* **privilege elevation** (V2). `sudo()` in an interrogation path turns the
  catalogue restriction of D10 into decoration: the vocabulary is filtered by
  permissions, then the execution ignores them. The registry states the rule
  without an exception, dispatcher included.

The check is AST-based rather than textual so that a mention inside a comment or
a docstring does not fail the build, while `self._cr.execute(...)` does.
"""

from __future__ import annotations

import ast
from pathlib import Path

from .report import CheckResult, Violation
from .sources import attribute_chain, iter_python_files, parse, relative_to_repo, suffixes
from .spec import (
    ADDONS_DIR,
    FORBIDDEN_PATTERNS,
    MODULES,
    REPO_ROOT,
    ForbiddenPattern,
    ModuleSpec,
)

NAME = "Syntactic"


def _violate(
    pattern: ForbiddenPattern,
    location: str,
    detail: str,
    result: CheckResult,
) -> None:
    result.add(Violation(
        rule=pattern.label,
        location=location,
        detail=detail,
        protects=pattern.protects,
    ))


def _check_node(
    node: ast.AST,
    pattern: ForbiddenPattern,
    location_base: str,
    result: CheckResult,
) -> None:
    line = getattr(node, "lineno", 0)
    location = f"{location_base}:{line}"

    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.split(".")[0] in pattern.imports:
                _violate(pattern, location, f"imports '{alias.name}'", result)
        return

    if isinstance(node, ast.ImportFrom):
        if node.level == 0 and node.module and node.module.split(".")[0] in pattern.imports:
            _violate(pattern, location, f"imports from '{node.module}'", result)
        return

    if isinstance(node, ast.Call):
        chain = attribute_chain(node.func)
        if chain and suffixes(chain) & pattern.call_suffixes:
            _violate(pattern, location, f"calls '{chain}'", result)
        for keyword in node.keywords:
            if keyword.arg is None:
                continue
            rendered = ast.unparse(keyword.value)
            if (keyword.arg, rendered) in pattern.keywords:
                _violate(
                    pattern,
                    location,
                    f"passes {keyword.arg}={rendered} to '{chain or 'a call'}'",
                    result,
                )
        return

    if isinstance(node, ast.Name) and node.id in pattern.names:
        _violate(pattern, location, f"references '{node.id}'", result)
        return

    if isinstance(node, ast.Attribute) and node.attr in pattern.names:
        _violate(pattern, location, f"references '{attribute_chain(node)}'", result)


def _check_file(path: Path, repo_root: Path, result: CheckResult) -> None:
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
    parts = set(path.parts)
    for node in ast.walk(tree):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.excluded_directories & parts:
                continue
            _check_node(node, pattern, location_base, result)


def run(
    *,
    addons_dir: Path = ADDONS_DIR,
    modules: dict[str, ModuleSpec] | None = None,
    repo_root: Path = REPO_ROOT,
) -> CheckResult:
    modules = MODULES if modules is None else modules
    result = CheckResult(name=NAME, unit="python files")

    for name in modules:
        for path in iter_python_files(addons_dir / name):
            _check_file(path, repo_root, result)

    return result
