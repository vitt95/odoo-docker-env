"""Make the pure zones importable without Odoo.

Under Odoo a pure zone is `odoo.addons.nli_core.contract`; its modules use relative
imports so they work there unchanged. Standalone, the addon's `__init__.py` cannot be
the entry point — it imports the Odoo models — so a **synthetic package** is
registered whose `__path__` points at the addon directory. The relative imports then
resolve exactly as they do in production, against the same files: the code under test
is the code that ships, not a copy adapted for testing.

The synthetic package deliberately takes the addon's own name, so a traceback reads
`nli_core.contract.canonical` and not some testing alias.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADDONS = REPO_ROOT / "custom_addons"
PREFIX = "nli_"

#: The addon directory of `nli_core`, kept for the callers that only need that one.
ADDON = ADDONS / "nli_core"


def install(module: str) -> Path:
    """Register a synthetic package for one `nli_*` addon and return its path."""
    path = ADDONS / module
    if not path.is_dir():
        raise SystemExit(f"{module}: no such addon under {ADDONS}")
    if module not in sys.modules:
        package = types.ModuleType(module)
        package.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[module] = package
    return path


def install_all() -> list[str]:
    """Register every `nli_*` addon present, in a stable order."""
    modules = sorted(
        candidate.name for candidate in ADDONS.iterdir()
        if candidate.is_dir() and candidate.name.startswith(PREFIX)
    )
    for module in modules:
        install(module)
    return modules


def modules_with_pure_tests() -> list[str]:
    """The addons that have a `pure_tests` package."""
    return [
        module for module in install_all()
        if (ADDONS / module / "pure_tests" / "__init__.py").is_file()
    ]


# Backwards-compatible alias for the callers written before this module existed.
def install_synthetic_package() -> None:
    install("nli_core")


def install_odoo_alias() -> None:
    """Make `odoo.addons.nli_*` resolve to the addon directories, without Odoo.

    `nli_engine` imports the contract the way it must under the platform —
    `from odoo.addons.nli_core.contract import vocabulary` — because that is the
    import Odoo resolves at runtime and writing anything else would mean two import
    styles for one dependency.

    Standalone, a synthetic `odoo.addons` package makes the same line work against the
    same files. Deliberately **nothing else** is provided: `from odoo import fields`
    fails, which is correct — a module needing the ORM has no business running here,
    and the failure says so immediately instead of at the first query.
    """
    if "odoo.addons" in sys.modules:
        return
    odoo = sys.modules.get("odoo") or types.ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    addons = types.ModuleType("odoo.addons")
    addons.__path__ = [str(ADDONS)]  # type: ignore[attr-defined]
    odoo.addons = addons  # type: ignore[attr-defined]
    sys.modules["odoo"] = odoo
    sys.modules["odoo.addons"] = addons

    # Point `odoo.addons.nli_x` at the synthetic package already registered for
    # `nli_x`, so the addon's own `__init__.py` — which imports the ORM — is never
    # executed. Without this the alias would resolve the addon the normal way and
    # fail on the first `from odoo import fields`, which is the very thing the
    # synthetic package exists to avoid.
    for module in list(sys.modules):
        if module.startswith(PREFIX) and "." not in module:
            sys.modules[f"odoo.addons.{module}"] = sys.modules[module]
            setattr(addons, module, sys.modules[module])
