"""Automatic verification of the architecture boundaries (D24, `04` §6.4).

Four checks, one exit code, stdlib only:

* `check_manifest` — the declared dependency graph is the graph of `04` §6.2;
* `check_imports`  — no module imports beyond its dependencies; only
  `nli_engine` imports provider libraries;
* `check_syntax`   — no direct PostgreSQL access, no privilege elevation;
* `check_purity`   — the pure zones depend on nothing but their arguments.

`spec.py` holds every rule; the checks hold only the mechanics of finding them.
"""
