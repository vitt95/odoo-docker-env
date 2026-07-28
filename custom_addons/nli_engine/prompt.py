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

from odoo.addons.nli_core.contract import vocabulary

from .adapters.base import Request

#: The instruction. Written once, in English, because it is read by a model and not
#: by a person, and every provider's tokeniser handles it identically.
INSTRUCTIONS = """\
You translate a user's request about business data into a single JSON envelope.

Answer with ONE JSON object and nothing else: no prose, no markdown fence, nothing
after the closing brace.

ENVELOPE SHAPE — every key spelled exactly as shown:

{"dsl_version":"1.0","outcome":"operations","confidence":0.9,"operations":[
  {"op":"set_target","ref":"<entity ref>","provenance":{"text":"<user words>"}},
  {"op":"add_condition","combine":"all","condition":{
      "ref":"<attribute ref>","predicate":"is_one_of",
      "value":{"kind":"enum","items":["draft"]}},
   "provenance":{"text":"<user words>"}},
  {"op":"add_condition","condition":{"ref":"<category ref>","predicate":"is_category"},
   "provenance":{"text":"<user words>"}},
  {"op":"add_group","ref":"<attribute ref>","provenance":{"text":"<user words>"}},
  {"op":"set_fields","refs":["<attribute ref>"],"provenance":{"text":"<user words>"}},
  {"op":"add_order","ref":"<attribute ref>","direction":"desc",
   "provenance":{"text":"<user words>"}},
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
- never decide a tolerance. "about 100000" is
  {"kind":"number","value":100000,"resolver":"approx_relative"};
- never choose the view unless the user asked for one;
- EMIT ONLY WHAT THE WORDS REQUIRE. Do not add set_fields, set_limit, add_order or
  set_view that the user did not ask for. No number in the sentence means no
  set_limit; no list of columns means no set_fields. Silence is not a request;
- a reference listed under "categories" in the catalogue is a named condition: use it
  as {"op":"add_condition","condition":{"ref":"<category ref>","predicate":"is_category"}}
  with no value. Never as an enum, never as a field;
- if the request is understandable but cannot be expressed with these operations,
  answer {"dsl_version":"1.0","outcome":"out_of_scope","scope_note":"<category>"};
- if two readings are plausible, answer with outcome "clarification" and a
  "clarification" object holding "question" and 2 to 4 "options", each with a "label"
  and the "operations" it would produce.
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
    if request.repair:
        # D15: one attempt, with the error in structured form. A second attempt would
        # mask a systematic defect and take it out of the metrics.
        parts.append(
            "Your previous answer was refused by validation. Correct it.\n"
            f"{json.dumps(request.repair, ensure_ascii=False)}"
        )
    parts.append(f"Request:\n{request.utterance}")
    return "\n\n".join(parts)


def catalogue_payload(catalogue) -> dict:
    """A catalogue in the shape the prompt sends.

    Flattened deliberately: the model gets references, terms and types, and nothing
    about how the catalogue was built. `nli_engine` does not depend on
    `nli_semantics` (§6.3) — it receives the catalogue, it does not know what a
    exposure rule is.
    """
    return {
        "entity": catalogue.entity,
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
