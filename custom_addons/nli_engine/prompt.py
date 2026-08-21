"""What is sent to the model, and — more importantly — what is not.

Two rules govern this file, and both are checkable by reading it.

**Only the utterance and the catalogue leave** (A6, V7). There is no branch that adds
record content, because `Request` has no field for it. What does leave that people
assume does not is **the user's sentence**: registry §5.2 is explicit that A6 protects
record content and not the utterance, and *"mostrami gli ordini di Mario Rossi"*
carries a personal datum. Saying so here, where the sentence is assembled, is the
only place it cannot be overlooked.

**The model chooses, it never invents** (C1). The vocabularies are enumerated in the
prompt from `nli_core.contract.vocabulary` — the same source the validator reads — so
a symbol admitted by one and not the other is not expressible. The constrained
generation of §12.3 does the same job upstream when the profile can (D78); the prompt
is what makes a profile that cannot still workable.
"""

from __future__ import annotations

import json

from odoo.addons.nli_core.contract import schema as schema_module
from odoo.addons.nli_core.contract import vocabulary

from .adapters.base import Request

#: The instruction. Written once, in English, because it is read by a model and not
#: by a person, and every provider's tokeniser handles it identically.
INSTRUCTIONS = """\
You translate a user's request about business data into a single JSON envelope.

Answer with ONE JSON object and nothing else: no prose, no markdown fence, nothing
after the closing brace.

ENVELOPE SHAPE — every key spelled exactly as shown:

{"dsl_version":"1.0","outcome":"operations","confidence":<0 to 1, your own>,"operations":[
  {"op":"set_target","ref":"<entity ref>","provenance":{"text":"<user words>"}},
  {"op":"add_condition","combine":"all","condition":{
      "ref":"<attribute ref>","predicate":"is_one_of",
      "value":{"kind":"enum","items":["draft"]}},
   "provenance":{"text":"<user words>"}},
  {"op":"add_condition","condition":{"ref":"<category ref>","predicate":"is_category"},
   "provenance":{"text":"<user words>"}},
  {"op":"add_group","ref":"<attribute ref>","provenance":{"text":"<user words>"}},
  {"op":"add_measure","function":"count","ref":"<attribute ref>",
   "provenance":{"text":"<user words>"}},
  {"op":"set_fields","refs":["<attribute ref>"],"provenance":{"text":"<user words>"}},
  {"op":"add_order","ref":"<attribute ref>","provenance":{"text":"<user words>"}},
  {"op":"set_limit","value":5,"provenance":{"text":"<user words>"}}]}

Rules, all of them absolute:
- an operation names its verb in "op". Never "type", never "action";
- an operation names its target in "ref". Never "field", never "entity", never "name";
- always begin with set_target when the entity is not already set;
- "ref" values come ONLY from the catalogue below, copied exactly. If the reference
  you need is not there, the answer is a clarification, never a guess;
- there is no "filter" key in an operation: conditions are added one at a time with
  add_condition;
- every operation carries provenance.text: the fragment of the user's sentence that
  produced it;
- never resolve a date. "this month" is
  {"kind":"temporal","expression":"current_month"};
- a time expression that names no attribute is a condition on the catalogue's
  "time_anchor". If it declares "ref", the condition is on that attribute. If it
  declares "choices", put the condition on the choice the sentence names, and on the
  first of them when the sentence names none: the system compares the fragment with
  the date and asks the user itself when they did not choose (D135). Do NOT write that
  question yourself. If it is null, this entity exposes no date at all: answer with a
  clarification;
- a period is taken WHOLE unless the sentence says otherwise: the predicate is
  "within". "before" and "after" have to be earned by words — "prima di", "dopo",
  "entro" — and they take one side of the period, not the period. "i lead di
  quest'anno" is within(current_year); after(current_year) means AFTER the end of
  2026, which is a different question and almost always empty;
- NEVER drop a time expression. If you cannot place it, ask. A sentence that names a
  period and an answer that does not is a wrong answer, not a shorter one;
- "primo/secondo/terzo/quarto trimestre" is
  {"kind":"temporal","expression":"quarter_of_year","n":1}, a month by name is
  {"kind":"temporal","expression":"month_of_year","n":1}, a year by number is
  {"kind":"temporal","expression":"year_of","n":2025}. Add "year" only when the
  sentence gives it: "a marzo 2026" is {"kind":"temporal",
  "expression":"month_of_year","n":3,"year":2026}. "Primo/secondo semestre" is
  {"kind":"temporal","expression":"half_of_year","n":2}. This chooses WHICH period,
  never which attribute carries it: that stays the rule above;
- a period none of these can say — "bimestre", "quadrimestre" — is a clarification.
  Never the nearest one: three months of the wrong data look exactly like three months
  of the right data;
- never choose a direction for an ordering. "ordinati per data" names no direction:
  add_order carries only the ref, and the system derives the direction from the type
  of the attribute. Add "direction" ONLY when the user said which way: "dal piu'
  recente" is "desc", "crescente" is "asc";
- a term in the catalogue may be several words, and the longest match wins. "fatture
  attive" is the name of an entity, not "fatture" plus a condition about being
  active; "in attesa di fattura" is one category, not two;
- when the sentence names two categories, EACH one is its own add_condition:
  "in attesa di spedizione da confermare" is two conditions, not one;
- never decide a tolerance. "about 100000" is
  {"kind":"number","value":100000,"resolver":"approx_relative"};
- never choose the view unless the user asked for one;
- COUNTING AND ARITHMETIC. A question that asks HOW MANY, or for a total, an average
  or an extreme, is answered with add_measure, and it is NOT optional: without it the
  answer is a list of records where the user asked for a number. "quanti", "quante",
  "il numero di" -> function "count"; "somma", "totale di" -> "sum"; "media", "medio"
  -> "avg"; "piu' alto", "massimo", "piu' grande" -> "max"; "piu' basso", "minimo" ->
  "min". English works the same way;
- add_measure always carries "function" AND "ref". For "count" the ref is the entity's
  own reference — count counts records, not values. For every other function the ref is
  the attribute being summed or averaged, and it must be a number in the catalogue;
- counting and grouping are two different words and two different operations. "quanti
  lead per stato" is BOTH: add_measure count and add_group on the state. Emitting only
  the grouping answers a question nobody asked;
- EMIT ONLY WHAT THE WORDS REQUIRE. Do not add set_fields, set_limit, add_order or
  set_view that the user did not ask for. Silence is not a request;
- COLUMNS. set_fields answers ONE thing: an explicit list of attribute terms after
  "con". No such list, NO set_fields — the system already has its default columns and
  you never choose them. "vediamo ordini con totale oltre 5000" has no list: the words
  after "con" are an attribute, a comparison and a number, so that is a condition and
  there are no columns;
- the list runs to the end of the sentence and every term in it is a column, in the
  order named. Abbreviations count: "con cl., stato" is two columns. Never turn the
  first term of the list into a grouping;
- a term in the list stays a column EVEN IF the same attribute is already the
  ordering or the grouping. "ordinati per intestatario con anagrafica, situazione" is
  add_order on the customer AND set_fields with [customer, state]. Repeat the ref, do
  not deduplicate;
- "ordinati per X con A, B" orders by X alone. What follows "con" is never more
  ordering;
- "i primi 20" is set_limit with value 20. No number in the sentence, no set_limit;
- a reference listed under "categories" in the catalogue is a named condition: use it
  as {"op":"add_condition","condition":{"ref":"<category ref>","predicate":"is_category"}}
  with no value. Never as an enum, never as a field;
- out_of_scope is about the OPERATIONS, never about a word. Answer it only when the
  request needs something these operations cannot do — a forecast of what will happen,
  a write, a computation ACROSS time such as a trend or a growth rate. A period that
  selects records that already exist is NOT one of those: "orders last month" is a
  condition on a date, and it belongs in the answer. A word you do not recognise is not
  out of scope: it is misspelled, abbreviated, foreign or trade jargon, and the
  catalogue holds the term it belongs to. Match it to the nearest one and go on;
- a refusal for scope must QUOTE the fragment that asks for the impossible thing, in
  "scope_provenance": {"text":"<the words>"}. If no part of the sentence asks to write,
  to delete, to send, or to predict, then the request is NOT out of scope and you must
  answer it. Refusing is not the safe choice: it is an answer, and it must be earned by
  the same evidence any other answer needs;
- if the request is understandable but cannot be expressed with these operations,
  answer {"dsl_version":"1.0","outcome":"out_of_scope","scope_note":"<category>",
  "scope_provenance":{"text":"<the words that ask for it>"}};
- if two readings are plausible, answer with outcome "clarification" and a
  "clarification" object holding "question" and 2 to 4 "options", each with a "label"
  and the "operations" it would produce.

WORKED EXAMPLE — "cerca ordini da evadere ordinati per intestatario con anagrafica, stato"

{"dsl_version":"1.0","outcome":"operations","confidence":0.82,"operations":[
 {"op":"set_target","ref":"ordini","provenance":{"text":"cerca ordini"}},
 {"op":"add_condition","condition":{"ref":"ordini.da_evadere","predicate":"is_category"},
  "provenance":{"text":"da evadere"}},
 {"op":"add_order","ref":"ordini.cliente","provenance":{"text":"ordinati per intestatario"}},
 {"op":"set_fields","refs":["ordini.cliente","ordini.stato"],
  "provenance":{"text":"con anagrafica, stato"}}]}

"ordini.cliente" appears TWICE on purpose: once as the ordering, once as a column,
because the sentence names it in both places. The list after "con" is columns and did
not continue the ordering. Had the sentence stopped at "ordinati per intestatario",
there would be no set_fields at all.

WORKED EXAMPLE — "il totale medio degli ordini per intestatario"

{"dsl_version":"1.0","outcome":"operations","confidence":0.9,"operations":[
 {"op":"set_target","ref":"ordini","provenance":{"text":"degli ordini"}},
 {"op":"add_measure","function":"avg","ref":"ordini.totale",
  "provenance":{"text":"il totale medio"}},
 {"op":"add_group","ref":"ordini.cliente","provenance":{"text":"per intestatario"}}]}

The measure comes from "medio" and the grouping from "per": two words, two operations.
Answering with the grouping alone would return a list where a number was asked for.
Had the sentence said "quanti ordini per intestatario", the measure would be
{"op":"add_measure","function":"count","ref":"ordini"} — count counts records, so its
ref is the entity itself and not one of its attributes.
"""


def _vocabularies() -> str:
    """The closed sets, from the same module the validator reads.

    Rendered as compact lines rather than nested JSON, and the reason is measured:
    the prompt is processed at every turn, most of the latency of a local model is
    prompt processing, and a nested structure costs tokens for punctuation that
    carries no meaning here. Same content, fewer tokens.
    """
    lines = [
        "operations: " + " ".join(sorted(vocabulary.OPERATIONS)),
        "value kinds: " + " ".join(sorted(vocabulary.VALUE_KINDS)),
        "temporal: " + " ".join(sorted(vocabulary.TEMPORAL_EXPRESSIONS)),
        "aggregations: " + " ".join(sorted(vocabulary.AGGREGATIONS)),
        "views: " + " ".join(sorted(vocabulary.VIEWS)),
        "scope_note: " + " ".join(sorted(vocabulary.SCOPE_NOTES)),
    ]
    for name, values in sorted(vocabulary.PREDICATES_BY_TYPE.items()):
        lines.append(f"predicates on {name}: " + " ".join(sorted(values)))
    return "\n".join(lines)


def system_message(request: Request) -> str:
    return f"{INSTRUCTIONS}\nClosed vocabularies:\n{_vocabularies()}"


def user_message(request: Request) -> str:
    parts = [f"Catalogue:\n{json.dumps(request.catalogue, ensure_ascii=False)}"]
    if request.state and request.state.get("target"):
        # From the second turn on, the state is what makes an elliptical sentence
        # interpretable — *"only the active ones"* means nothing without it (§17.1).
        parts.append(f"Current state:\n{json.dumps(request.state, ensure_ascii=False)}")
    if request.pending:
        # D120: il turno prima si e' chiuso con una domanda, e questa frase la
        # risponde. Senza, «anno corrente» e' un frammento senza senso: il modello
        # riparte da zero e richiede la stessa cosa, che e' il modo piu' rapido di
        # far sembrare stupido un sistema che aveva capito.
        frase, domanda = request.pending
        parts.append(
            "The previous turn ended with a question. The sentence below ANSWERS it: "
            "combine the two into one complete request, do not ask again.\n"
            f"Earlier sentence: {frase}\nQuestion asked: {domanda}"
        )
    if request.repair:
        # D15: one attempt, with the error in structured form. A second attempt would
        # mask a systematic defect and take it out of the metrics.
        parts.append(
            "Your previous answer was refused by validation. Correct it.\n"
            f"{json.dumps(request.repair, ensure_ascii=False)}"
        )
    parts.append(f"Request:\n{request.utterance}")
    return "\n\n".join(parts)


def catalogue_references(payload: dict, *, utterance: str = "",
                          mentions=None) -> schema_module.References:
    """The references this catalogue admits, kept apart by genus (D101, D102).

    Read from the payload rather than from the catalogue object because the payload is
    exactly what the model was shown: a reference admitted by the schema and absent
    from the message would be a reference the model is allowed to emit and has no way
    to know, which is worse than either.

    The entity of the turn travels with the other entities: `set_target` may change
    the subject, and a catalogue that admitted only the current one would make the
    change unexpressible.

    **D112 — the categories admitted are narrowed to the ones the sentence names.** A
    named condition is the one condition whose reference the sentence does not have to
    spell: no field, no value, no type. Measured on 80 openings, that made it the place
    where every fragment the model could not place ended up — *"prelievi"*, the name of
    the entity itself, became *"in bozza"*. The utterance is known before the schema is
    built, so a category the sentence does not mention can be made **inexpressible**
    instead of being refused after the fact.

    `mentions` is the same recognizer D105 uses to require that a named condition be
    grounded in the fragment that justifies it, passed as an argument because
    `nli_engine` does not depend on `nli_semantics` (§6.3). Absent, nothing is
    narrowed — the same shape `contextual.validate` already gives this argument, and
    the reason the engine's own pure tests can run without a dictionary.

    Only the categories. An attribute names itself in the sentence — *"con importo
    oltre 500"* — and narrowing it would take away the columns and the groupings,
    which the sentence names somewhere else entirely.
    """
    entities = {payload["entity"], *(entity["ref"] for entity in payload["entities"])}
    categories = tuple(sorted(category["ref"] for category in payload["categories"]))
    if mentions is not None:
        categories = tuple(ref for ref in categories if mentions(ref, utterance))
    return schema_module.References(
        entities=tuple(sorted(ref for ref in entities if ref)),
        attributes=tuple(sorted(attribute["ref"] for attribute in payload["attributes"])),
        categories=categories,
        # D103: the type each attribute carries in the catalogue is the one §8.1 pairs
        # with its predicates. An attribute whose type the catalogue does not declare
        # is simply absent here, and keeps the whole predicate set.
        types={attribute["ref"]: attribute["type"]
               for attribute in payload["attributes"] if attribute.get("type")},
    )


def catalogue_payload(catalogue) -> dict:
    """A catalogue in the shape the prompt sends.

    Flattened deliberately: the model gets references, terms and types, and nothing
    about how the catalogue was built. `nli_engine` does not depend on
    `nli_semantics` (§6.3) — it receives the catalogue, it does not know what a
    exposure rule is.
    """
    return {
        "entity": catalogue.entity,
        # D110: dove si attacca un periodo che non nomina un campo. Viaggia sempre,
        # anche nulla: una chiave assente si scambia per un catalogo vecchio, una
        # chiave nulla dice che date non ce ne sono.
        "time_anchor": catalogue.time_anchor,
        "attributes": [
            {"ref": attribute.ref, "terms": list(attribute.terms),
             "type": attribute.type,
             **({"values": [{"value": value, "terms": list(terms)}
                            for value, terms in attribute.values]}
                if attribute.values else {})}
            for attribute in catalogue.attributes
        ],
        "categories": [
            {"ref": category.ref, "terms": list(category.terms)}
            for category in catalogue.categories
        ],
        "entities": [
            {"ref": ref, "terms": list(terms)} for ref, terms in catalogue.entity_names
        ],
    }
