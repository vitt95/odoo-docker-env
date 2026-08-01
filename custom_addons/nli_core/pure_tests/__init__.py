"""Tests of the pure zone — no platform, no database, no clock.

They run three ways, and all three matter:

* `python3 tools/pure/run.py` — plain Python, no Odoo, sub-second. This is the
  one used while writing code, and the reason the contract was built without the
  ORM (part 2 of `ai/12-piano-implementazione.md`);
* `./manage.sh test <db>` — inside the Odoo suite, via `nli_core/tests/__init__.py`;
* CI, through the first of the two.

They live outside `tests/` because Odoo's `tests` package imports
`TransactionCase`, which imports the platform. A test of a pure zone that needs
the platform to start cannot prove the code under it does not.
"""
