#!/usr/bin/env python3
"""Entry point for the four boundary checks.

Runnable both ways, because both get used:

    python3 tools/arch/run.py
    python3 -m tools.arch.run
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.arch.runner import main  # noqa: E402  (path bootstrap must come first)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
