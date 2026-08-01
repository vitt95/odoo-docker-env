"""The platform's field types, translated into the type vocabulary of the contract.

**Why this table lives alone, outside `introspection`.** It is the one piece of
platform knowledge in `nli_semantics` that is a *fact*, not a *reading*: the rest of
introspection asks a live registry what it holds — models, fields, rights, a clock —
and cannot exist without the ORM. This mapping asks nothing. It is the same twelve
pairs in every installation, on every database, at every hour.

Keeping it inside `introspection/runtime.py` made every reader of the table a reader
of the ORM, because importing that module imports `odoo.fields`. The measuring tools
of `ai/corpus` are exactly such readers: they build a catalogue from the corpus, with
no database behind them, and they need the table to do it. Under D24 (the decision
that a zone declares what it may import, and the checker enforces it) that dependency
was upside down — a pure caller reaching through an impure module for a constant.

So the table moves here and `introspection.runtime` re-exports it. Nothing changes for
the callers under Odoo; what changes is that the catalogue can be built off-platform,
which is what the accuracy measurement of `07` §5.4 needs to run at all.
"""

from __future__ import annotations

#: `fields_get` type -> the type vocabulary of `03` §8.1.
#:
#: `monetary` and `float` collapse into `number` on purpose: a predicate that is
#: valid on an amount is valid on a quantity, and the currency is a presentation
#: concern the Presenter handles from the field, not a semantic distinction the model
#: should have to reason about.
CONTRACT_TYPE_BY_ODOO_TYPE: dict[str, str] = {
    "char": "text",
    "text": "text",
    "selection": "enum",
    "boolean": "boolean",
    "integer": "number",
    "float": "number",
    "monetary": "number",
    "date": "date",
    "datetime": "datetime",
    "many2one": "relation",
    "one2many": "relation",
    "many2many": "relation",
}
