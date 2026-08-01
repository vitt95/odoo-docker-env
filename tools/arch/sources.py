"""Source reading and AST helpers shared by the four checks.

Everything here is stdlib only, on purpose: the checks must run in the Odoo
container, on a developer machine and in CI without an install step. A boundary
check that needs its own environment is a boundary check that gets skipped.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SKIPPED_DIRS = {"__pycache__", ".git", "node_modules", "static"}


@dataclass(frozen=True)
class ImportedName:
    """One imported name, normalised for rule matching."""

    #: Full dotted path as written, e.g. "odoo.addons.nli_core.contract".
    dotted: str
    #: First segment, e.g. "odoo". Empty for relative imports.
    top_level: str
    #: Number of leading dots for `from . import x`; 0 for absolute imports.
    level: int
    line: int


def iter_python_files(root: Path) -> Iterator[Path]:
    """Every tracked Python file under `root`, deterministically ordered."""
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIPPED_DIRS for part in path.parts):
            continue
        yield path


def parse(path: Path) -> ast.Module:
    """Parse a Python file, attributing syntax errors to the file itself."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def parse_manifest(path: Path) -> dict:
    """Read an Odoo manifest as data.

    `ast.literal_eval` rather than `eval`: a manifest is a declaration, and a
    checker that executes the thing it is checking is not a checker.
    """
    return ast.literal_eval(path.read_text(encoding="utf-8"))


def imported_names(tree: ast.Module) -> Iterator[ImportedName]:
    """Yield every import in the tree, absolute and relative alike."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield ImportedName(
                    dotted=alias.name,
                    top_level=alias.name.split(".")[0],
                    level=0,
                    line=node.lineno,
                )
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            top_level = base.split(".")[0] if node.level == 0 and base else ""
            # `from odoo.addons import nli_core` names the module in the alias,
            # not in `node.module`: expand so both forms match the same rules.
            for alias in node.names:
                dotted = f"{base}.{alias.name}" if base else alias.name
                yield ImportedName(
                    dotted=dotted,
                    top_level=top_level,
                    level=node.level,
                    line=node.lineno,
                )


def attribute_chain(node: ast.AST) -> str:
    """Render an attribute/name chain as a dotted string, or "" if it is not one.

    `self.env.cr.execute` -> "self.env.cr.execute"; `foo().bar` -> "" for the
    call part, "bar" being unreachable without the receiver.
    """
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    elif isinstance(current, ast.Call):
        # A call in the middle of the chain: keep the suffix we could read, so
        # `record.sudo().write(...)` still exposes "sudo".
        pass
    elif not parts:
        return ""
    return ".".join(reversed(parts))


def suffixes(dotted: str) -> set[str]:
    """The one- and two-segment tails of a dotted chain.

    Rules are written against tails (`cr.execute`, `sudo`) because the receiver
    is written a dozen different ways (`self.env.cr`, `cr`, `self._cr`) and the
    receiver is not what the rule is about.
    """
    segments = dotted.split(".")
    tails = {segments[-1]}
    if len(segments) >= 2:
        tails.add(".".join(segments[-2:]))
    return tails


def relative_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)
