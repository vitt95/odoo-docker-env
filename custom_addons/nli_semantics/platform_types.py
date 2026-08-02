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


#: I nomi che Odoo mette su **ogni** modello. Regola 2 di `06` §5.3.
#:
#: Sta qui e non in `introspection/l0.py` per la stessa ragione della tabella dei tipi
#: (**D109**): e' un fatto, non la lettura di un registro vivo — gli stessi sei nomi in
#: ogni installazione — e chiuderlo dietro un modulo che importa l'ORM lo rendeva
#: illeggibile a chi non ha Odoo davanti, compresi i test puri che devono verificarlo.
#:
#: **`create_date` non e' in questo elenco** (**D117**). Ci stava, e non e' della stessa
#: famiglia degli altri: `id` e `create_uid` non significano niente per una persona,
#: mentre *«quando e' stato creato»* e' la prima cosa che si intende con «i lead di
#: quest'anno». Misurato sul campo: a quella domanda l'ancora del tempo offriva quattro
#: date e non quella giusta.
SYSTEM_FIELDS = frozenset({
    "id", "create_uid", "write_uid", "write_date",
    "display_name", "__last_update",
})

#: Prefissi dei mixin tecnici — messaggistica, attivita', valutazioni, sito. Regola 3
#: di §5.3. Per prefisso e non per elenco esatto: l'elenco cresce a ogni versione di
#: Odoo, e una voce dimenticata allarga il catalogo in silenzio.
MIXIN_PREFIXES = (
    "message_", "activity_", "rating_", "website_", "access_",
)
