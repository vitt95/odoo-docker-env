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
    DEROGATIONS,
    ENVIRONMENT_CONSTRUCTORS,
    ENVIRONMENT_UID_RULE,
    FORBIDDEN_PATTERNS,
    MODULES,
    REPO_ROOT,
    Derogation,
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


def _derogation_for(location_base: str, chain: str) -> Derogation | None:
    """The derogation covering this call in this file, if there is one (D95)."""
    normalised = location_base.replace("\\", "/")
    for derogation in DEROGATIONS:
        if not normalised.endswith(derogation.path):
            continue
        if suffixes(chain) & derogation.calls:
            return derogation
    return None


def _statement_admitted(
    node: ast.Call, derogation: Derogation, constants: dict[str, str]
) -> str | None:
    """Whether the statement matches the shape the derogation admits.

    Returns the reason it does not, or `None` when it does. A derogation with no
    declared shape — opening a cursor — admits the call and nothing more, because
    there is no statement to inspect.

    A statement written as a module-level constant is resolved from `constants`: the
    claim is spelled that way on purpose, so that reviewing the derogation means
    reading one named string. A statement this check cannot read is refused, which is
    what keeps *"build the SQL at runtime"* from becoming the way around the shape.
    """
    if not derogation.statement_must_contain:
        return None
    if not node.args:
        return "the admitted call is made without a statement"
    statement = node.args[0]
    if isinstance(statement, ast.Name):
        if statement.id not in constants:
            return (
                f"the statement comes from {statement.id!r}, which is not a "
                "module-level string constant in this file"
            )
        return _shape_violation(constants[statement.id], derogation)
    if not (isinstance(statement, ast.Constant) and isinstance(statement.value, str)):
        return "the statement is not a literal, so its shape cannot be verified"
    return _shape_violation(statement.value, derogation)


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level `NAME = "..."` bindings, so a named statement can be read."""
    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                constants[target.id] = node.value.value
    return constants


def _shape_violation(statement: str, derogation: Derogation) -> str | None:
    for fragment in derogation.statement_must_contain:
        if fragment not in statement:
            return f"the statement does not contain {fragment!r}"
    for fragment in derogation.statement_must_not_contain:
        if fragment in statement:
            return f"the statement contains {fragment!r}"
    return None


def _check_environment_uid(
    node: ast.AST,
    location_base: str,
    parts: set[str],
    result: CheckResult,
) -> None:
    """V2, second form: an environment whose identity is a constant."""
    if ENVIRONMENT_UID_RULE.excluded_directories & parts:
        return
    if not isinstance(node, ast.Call):
        return
    chain = attribute_chain(node.func)
    if not chain or not (suffixes(chain) & ENVIRONMENT_CONSTRUCTORS):
        return
    if len(node.args) < 2:
        return
    uid = node.args[1]
    if isinstance(uid, ast.Constant):
        _violate(
            ENVIRONMENT_UID_RULE,
            f"{location_base}:{getattr(node, 'lineno', 0)}",
            f"builds an environment on the literal identity {uid.value!r}: the uid "
            "must be read from the turn, never written down",
            result,
        )


def _check_node(
    node: ast.AST,
    pattern: ForbiddenPattern,
    location_base: str,
    result: CheckResult,
    constants: dict[str, str] | None = None,
) -> None:
    constants = constants or {}
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
            derogation = _derogation_for(location_base, chain)
            if derogation is None:
                _violate(pattern, location, f"calls '{chain}'", result)
            else:
                reason = _statement_admitted(node, derogation, constants)
                if reason is not None:
                    _violate(
                        pattern, location,
                        f"calls '{chain}' outside the shape {derogation.decision} "
                        f"admits: {reason}",
                        result,
                    )
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
    constants = _module_constants(tree)
    for node in ast.walk(tree):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.excluded_directories & parts:
                continue
            _check_node(node, pattern, location_base, result, constants)
        _check_environment_uid(node, location_base, parts, result)


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
