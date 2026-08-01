#!/usr/bin/env python3
"""Write the derived JSON Schema artefacts of the contract (D11).

    python3 tools/dsl/emit_schema.py            # report whether they are current
    python3 tools/dsl/emit_schema.py --write    # regenerate

The source of truth is `nli_core/contract/vocabulary.py`; these files are output.
Editing them by hand is a mistake the pure test `test_schema.py` catches, which is
why the command to regenerate is named in its failure message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from pure.bootstrap import ADDON, install  # noqa: E402

SCHEMA_DIR = ADDON / "contract" / "schema"


def main(argv: list[str]) -> int:
    write = "--write" in argv
    install("nli_core")
    from nli_core.contract import schema as schema_module  # noqa: PLC0415

    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []

    for name, build in schema_module.ARTEFACTS.items():
        path = SCHEMA_DIR / name
        rendered = json.dumps(build(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == rendered:
            print(f"  current  {path.relative_to(REPO_ROOT)}")
            continue
        if write:
            path.write_text(rendered, encoding="utf-8")
            print(f"  written  {path.relative_to(REPO_ROOT)}")
        else:
            stale.append(str(path.relative_to(REPO_ROOT)))
            print(f"  STALE    {path.relative_to(REPO_ROOT)}")

    if stale:
        print("\nRun with --write to regenerate.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
