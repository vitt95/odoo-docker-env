"""The formal JSON Schema of the Envelope and the State (D11, §18.1).

**Why generated rather than hand-written.** The schema and the level 1-2 validator
would otherwise be two transcriptions of the same vocabularies, and they would
drift — the drift being invisible until a model produces something one accepts and
the other refuses. Here `vocabulary.py` is the single source and the schema is
derived from it, so a new predicate reaches both at once.

**Why the schema exists at all**, given that `validation.structural` is the
authority. Three uses, none of them decorative:

* **constrained generation.** §12.3 notes that failures at levels 1-2 should be
  rare precisely because the model's output can be constrained upstream to the
  schema and the vocabularies. That is the practical benefit of C1, and it needs a
  machine-readable schema to hand to a provider (part 5, D78);
* **inspection.** §18.1 chose JSON with a formal schema so the contract is
  readable without our tooling;
* **the transport/contract distinction.** A provider's structured-output feature is
  a usable transport, never the contract (§18.1, last row). Exporting the schema is
  what keeps that true: the same artefact can be handed to any provider.

The derived artefact is committed at `contract/schema/dsl-1.0.json` and a test
asserts the file matches this generator, so the two cannot part company.

**Pure zone.**
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import envelope as envelope_module
from .vocabulary import (
    AGGREGATIONS,
    CONNECTIVES,
    DIRECTIONS,
    DSL_VERSION,
    GRANULARITIES,
    INFERENCE_RULES,
    OPERATIONS,
    ORIGINS,
    OUTCOME_PAYLOAD,
    OUTCOMES,
    PREDICATES,
    PREDICATES_BY_TYPE,
    SCOPE_NOTES,
    SELECTORS,
    TEMPORAL_EXPRESSIONS,
    VALUE_KINDS,
    VALUE_OPTIONAL_KEYS,
    VIEWS,
    DEFAULT_LIMITS,
    Limits,
)

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
ENVELOPE_ID = f"https://aida.local/dsl/{DSL_VERSION}/envelope.json"
STATE_ID = f"https://aida.local/dsl/{DSL_VERSION}/state.json"


def _sorted(values) -> list[str]:
    return sorted(values)


def _provenance() -> dict:
    return {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
        "additionalProperties": False,
        "description": "The fragment of the user's sentence that produced this "
                       "element (§10.3). The fragment, never the message.",
    }


def _value() -> dict:
    """One `$defs` entry per value kind, combined with `oneOf`.

    Written as a disjunction rather than one permissive object so that constrained
    generation cannot produce `{"kind": "number", "text": "..."}` — a shape that
    would pass a looser schema and fail level 1.
    """
    variants = []
    for kind in _sorted(VALUE_KINDS):
        properties: dict = {"kind": {"const": kind}}
        for key in _sorted(VALUE_KINDS[kind]):
            properties[key] = _value_property(kind, key)
        for key in _sorted(VALUE_OPTIONAL_KEYS[kind]):
            properties[key] = _value_property(kind, key)
        variants.append({
            "type": "object",
            "properties": properties,
            "required": ["kind", *_sorted(VALUE_KINDS[kind])],
            "additionalProperties": False,
        })
    return {"oneOf": variants}


def _value_property(kind: str, key: str) -> dict:
    if key == "expression":
        return {"enum": _sorted(TEMPORAL_EXPRESSIONS)}
    if key == "items":
        return {"type": "array", "items": {"type": "string"}, "minItems": 1}
    if key == "resolver":
        return {
            "type": "string",
            "description": "Names a resolver defined in the Semantic Dictionary "
                           "(§9.3). The model declares that the value is "
                           "approximate and which rule applies; it never decides "
                           "the tolerance.",
        }
    if key in ("text", "date"):
        return {"type": "string"}
    if key == "n":
        return {"type": "integer", "minimum": 1}
    if kind == "boolean" and key == "value":
        return {"type": "boolean"}
    if kind == "temporal" and key in ("from", "to"):
        return {"type": "string"}
    return {"type": "number"}


@dataclass(frozen=True)
class References:
    """The references of one catalogue, kept apart by **genus** (D102).

    D101 closed `ref` on the catalogue and stopped there, and the measurement showed
    what the omission costs: `set_fields` with `["fatture_cliente", ...]` — an
    **entity** asked for as a column. It was admitted because the catalogue lists the
    other entities too, for the entity resolution of phase A, and one flat set cannot
    tell a column from an entity.

    Three genera, and every operation admits only the one that belongs to it: an
    entity is the target, an attribute is a column, a grouping, an ordering or a
    measure, and a category is only ever the reference of a condition.
    """

    entities: tuple[str, ...] = ()
    attributes: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    #: Attribute reference → type of §8.1, for the predicates of **D103**. An
    #: attribute missing from here keeps the whole predicate set: a type nobody
    #: declared is not a licence to guess which comparisons make sense on it.
    types: dict[str, str] = field(default_factory=dict)

    @property
    def conditionable(self) -> tuple[str, ...]:
        """What a condition may name: an attribute, or a category (T5, D87)."""
        return tuple(sorted({*self.attributes, *self.categories}))

    def by_type(self) -> dict[str | None, tuple[str, ...]]:
        """Attributes grouped by declared type; `None` collects the undeclared."""
        grouped: dict[str | None, list[str]] = {}
        for ref in self.attributes:
            grouped.setdefault(self.types.get(ref), []).append(ref)
        return {tipo: tuple(sorted(refs)) for tipo, refs in grouped.items()}

    def __bool__(self) -> bool:
        return bool(self.entities or self.attributes or self.categories)


#: Which genus each verb's `ref`/`refs` belongs to. A verb absent from here carries no
#: reference; a verb present carries exactly one genus, and the mapping is the whole
#: decision of D102 written as data instead of as branches.
REFERENCE_GENUS = {
    "set_target": "entities",
    "set_fields": "attributes",
    "add_field": "attributes",
    "remove_field": "attributes",
    "add_group": "attributes",
    "remove_group": "attributes",
    "add_order": "attributes",
    "set_order": "attributes",
    "add_measure": "attributes",
    "remove_measure": "attributes",
    # A condition addressed by reference rather than by identifier: same genus as the
    # condition it removes.
    "remove_condition": "conditionable",
}


def _genus(refs: References | None, genus: str):
    return getattr(refs, genus) if refs else None


def _reference(refs) -> dict:
    """The schema of a single `ref`.

    **C1 made structural** (D101). `prompt.py` says *«the model chooses, it never
    invents»* and, until this function, said it only in prose: `ref` was any non-empty
    string, so constrained generation could not refuse an invented one. It did not
    refuse `oppurtunita.fase` — the entity is spelled `opportunita` — and nothing
    downstream of the envelope caught it either, because levels 1 and 2 know the shape
    of a reference and not the catalogue.

    Given the catalogue of the turn, the admitted references are a closed set, and a
    reference outside it stops being expressible instead of being reprimanded. That is
    C3, the criterion this project prefers to every rule somebody has to remember.

    Without `refs` the schema is the general one, which is what `emit_schema.py` writes
    and what a profile without constrained generation gets: the enumeration depends on
    the turn and a file on disk cannot carry it.
    """
    if not refs:
        return {"type": "string", "minLength": 1}
    return {"enum": _sorted(refs)}


def _condition_shape(*, in_state: bool, ref_schema: dict, predicates) -> dict:
    properties: dict = {
        "ref": ref_schema,
        "predicate": {"enum": _sorted(predicates)},
        "value": {"$ref": "#/$defs/value"},
        "origin": {"enum": _sorted(ORIGINS)},
        "provenance": {"$ref": "#/$defs/provenance"},
        "confidence": {"$ref": "#/$defs/confidence"},
    }
    required = ["ref", "predicate"]
    if in_state:
        properties["id"] = {"type": "string", "minLength": 1}
        required = ["id", "ref", "predicate", "origin"]
    else:
        properties["combine"] = {"enum": ["all", "any"]}
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _condition(*, in_state: bool, refs: References | None = None) -> dict:
    """One condition, with the predicate tied to the type of what it names (**D103**).

    §8.1 already pairs each type with the predicates that mean something on it: the
    validator reads that table at level 2 and refuses the rest. Until this function
    the **schema** did not, so a profile with constrained generation could still write
    `less_than` on a name or `contains` on an amount, and the refusal arrived one
    level later — as a repair, or as a wrong answer when the pair happened to be
    admissible and wrong.

    With a catalogue the condition becomes one branch per type: the references of that
    type, and only the predicates §8.1 grants it. A comparison that means nothing on
    an attribute stops being writable, which is the same move D101 and D102 made on
    the reference, applied to what is said **about** it.

    An attribute whose type nobody declared keeps the whole set. Guessing which
    comparisons suit an unknown type would be inventing the table §8.1 already owns.
    """
    if not refs or not refs.conditionable:
        return _condition_shape(in_state=in_state,
                                ref_schema=_reference(_genus(refs, "conditionable")),
                                predicates=PREDICATES)

    branches = []
    for tipo, attributes in sorted(refs.by_type().items(), key=lambda pair: pair[0] or ""):
        predicates = PREDICATES_BY_TYPE.get(tipo or "", PREDICATES)
        branches.append(_condition_shape(in_state=in_state,
                                         ref_schema=_reference(attributes),
                                         predicates=predicates))
    if refs.categories:
        # T5 under D87: a named condition takes `is_category` and nothing else —
        # there is no value to compare, the definition is in the dictionary.
        branches.append(_condition_shape(
            in_state=in_state, ref_schema=_reference(refs.categories),
            predicates=PREDICATES_BY_TYPE.get("category", ("is_category",))))
    return {"oneOf": branches} if len(branches) > 1 else branches[0]


def _operation_schema(verb: str, signature: envelope_module.Signature,
                      refs: References | None = None) -> dict:
    properties: dict = {
        "op": {"const": verb},
        "provenance": {"$ref": "#/$defs/provenance"},
        "confidence": {"$ref": "#/$defs/confidence"},
        "origin": {"enum": _sorted(ORIGINS)},
    }
    admitted = _genus(refs, REFERENCE_GENUS[verb]) if verb in REFERENCE_GENUS else None
    for key in sorted(signature.allowed - envelope_module.COMMON_OPERATION_KEYS):
        properties[key] = _parameter_schema(key, admitted)
    schema: dict = {
        "type": "object",
        "properties": properties,
        "required": ["op", *_sorted(signature.required)],
        "additionalProperties": False,
    }
    # `remove_condition` and `remove_measure` admit two ways of addressing, exactly
    # one of which must be present (§6.3).
    for group in signature.one_of:
        schema.setdefault("allOf", []).append({
            "oneOf": [{"required": [key]} for key in _sorted(group)]
        })
    return schema


def _parameter_schema(key: str, refs=None) -> dict:
    if key == "condition":
        return {"$ref": "#/$defs/operation_condition"}
    if key == "refs":
        return {"type": "array", "items": _reference(refs), "minItems": 1}
    if key == "ref":
        return _reference(refs)
    if key == "id":
        # Not a reference: `c1` is the identifier of a condition inside the state, and
        # the catalogue has nothing to say about it.
        return {"type": "string", "minLength": 1}
    if key == "view":
        return {"enum": _sorted(VIEWS)}
    if key == "direction":
        return {"enum": _sorted(DIRECTIONS)}
    if key == "granularity":
        return {"enum": _sorted(GRANULARITIES)}
    if key == "function":
        return {"enum": _sorted(AGGREGATIONS)}
    if key == "combine":
        return {"enum": ["all", "any"]}
    if key == "selector":
        return {"$ref": "#/$defs/selector"}
    if key == "value":
        return {"type": "integer", "minimum": 1}
    if key == "position":
        return {"type": "integer", "minimum": 0}
    raise AssertionError(f"no schema for operation parameter {key!r}")


def _selector() -> dict:
    return {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "by": {"const": "position"},
                    "value": {"type": "integer", "minimum": 1},
                },
                "required": ["by", "value"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "by": {"const": "attribute"},
                    "ref": {"type": "string", "minLength": 1},
                    "value": {"$ref": "#/$defs/value"},
                },
                "required": ["by", "ref", "value"],
                "additionalProperties": False,
            },
        ],
        "description": "No selection by technical identifier: the user does not "
                       "know identifiers and the model must not invent them (§6.6). "
                       f"Admitted: {_sorted(SELECTORS)}",
    }


def build_envelope_schema(*, refs: References | None = None) -> dict:
    """The schema of the Interpretation Envelope (§4.4).

    With `refs` — the references of the catalogue sent this turn, kept apart by genus
    — every `ref` becomes an enumeration instead of a string (**D101**), and the
    enumeration is the one that belongs to the operation (**D102**). The envelope
    remains the same envelope: nothing is added and nothing is relaxed, open sets are
    narrowed to the closed ones the catalogue already defines. A profile that
    constrains generation therefore cannot emit a reference nobody has, nor ask for an
    entity as a column; a profile that cannot is unaffected, and levels 3 to 5 keep
    rejecting what reaches them.
    """
    outcome_branches = []
    payload_keys = _sorted({key for key in OUTCOME_PAYLOAD.values() if key})
    for outcome in _sorted(OUTCOMES):
        payload = OUTCOME_PAYLOAD[outcome]
        # D118: il rifiuto per portata porta anche la propria provenienza. E' l'unico
        # esito con due chiavi obbligatorie, e la ragione e' che e' l'unico che
        # afferma qualcosa sulla domanda invece che sui dati.
        obbligatorie = ["outcome"] + ([payload] if payload else [])
        if outcome == "out_of_scope":
            obbligatorie.append("scope_provenance")
        branch: dict = {
            "if": {"properties": {"outcome": {"const": outcome}}, "required": ["outcome"]},
            "then": {
                "required": obbligatorie,
                # The four outcomes are mutually exclusive: a foreign payload is a
                # level 1 failure, not a tolerated extra (§4.4).
                "not": {"anyOf": [
                    {"required": [key]} for key in payload_keys if key != payload
                ]} if any(key != payload for key in payload_keys) else False,
            },
        }
        if branch["then"]["not"] is False:
            del branch["then"]["not"]
        outcome_branches.append(branch)

    return {
        "$schema": SCHEMA_DIALECT,
        "$id": ENVELOPE_ID,
        "title": f"AIDA interpretation envelope, DSL {DSL_VERSION}",
        "description": (
            "The model's whole output for one turn. Generated from "
            "nli_core/contract/vocabulary.py — edit that, not this file."
        ),
        "type": "object",
        "properties": {
            "dsl_version": {"const": DSL_VERSION},
            "outcome": {"enum": _sorted(OUTCOMES)},
            "confidence": {"$ref": "#/$defs/confidence"},
            "operations": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/operation"},
                "description": "An empty list is not valid: an unchanged state "
                               "presented as a success is indistinguishable from "
                               "an ignored request (§4.4).",
            },
            "clarification": {"$ref": "#/$defs/clarification"},
            "scope_note": {"enum": _sorted(SCOPE_NOTES)},
            # D118: un rifiuto per portata deve indicare **il pezzo di frase** che
            # chiede la cosa impossibile. Senza, `out_of_scope` costa quanto una
            # risposta, ed e' l'uscita che il modello prende ogni volta che fatica —
            # misurato: nove rifiuti su 414 con nota `previsione`, e «mostrami i lead
            # di quest'anno» classificato come cancellazione di record.
            "scope_provenance": {"$ref": "#/$defs/provenance"},
        },
        "required": ["dsl_version", "outcome"],
        "additionalProperties": False,
        "allOf": outcome_branches,
        "$defs": {
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "An ordering signal, not a probability (§10.5). "
                               "No security decision depends on it.",
            },
            "provenance": _provenance(),
            "value": _value(),
            "operation_condition": _condition(in_state=False, refs=refs),
            "selector": _selector(),
            "operation": {
                "oneOf": [
                    _operation_schema(verb, envelope_module.OPERATION_SIGNATURES[verb],
                                      refs)
                    for verb in _sorted(OPERATIONS)
                ]
            },
            "clarification": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "minLength": 1},
                    "provenance": {"$ref": "#/$defs/provenance"},
                    "options": {
                        "type": "array",
                        "minItems": DEFAULT_LIMITS.min_clarification_options,
                        "maxItems": DEFAULT_LIMITS.max_clarification_options,
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string", "minLength": 1},
                                "operations": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {"$ref": "#/$defs/operation"},
                                },
                            },
                            "required": ["label", "operations"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["question", "options"],
                "additionalProperties": False,
                "description": "Two to four mutually exclusive options, each "
                               "carrying the operations it would produce (§11.2). "
                               "One option would be a confirmation in disguise.",
            },
        },
    }


def build_state_schema(*, limits: Limits = DEFAULT_LIMITS) -> dict:
    """The schema of the Interrogation State (§5.2)."""
    element = {
        "origin": {"enum": _sorted(ORIGINS)},
        "provenance": {"$ref": "#/$defs/provenance"},
        "confidence": {"$ref": "#/$defs/confidence"},
        "rule": {"enum": _sorted(INFERENCE_RULES)},
    }
    return {
        "$schema": SCHEMA_DIALECT,
        "$id": STATE_ID,
        "title": f"AIDA interrogation state, DSL {DSL_VERSION}",
        "description": (
            "The interrogation in semantic terms: persistable, shareable, and "
            "containing no Odoo model or field name (§5.10)."
        ),
        "type": "object",
        "properties": {
            "dsl_version": {"const": DSL_VERSION},
            "target": {
                "type": "object",
                "properties": {"ref": {"type": "string", "minLength": 1}, **element},
                "required": ["ref", "origin"],
                "additionalProperties": False,
            },
            "filter": {"$ref": "#/$defs/node"},
            "fields": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {"ref": {"type": "string", "minLength": 1}, **element},
                    "required": ["ref", "origin"],
                    "additionalProperties": False,
                },
            },
            "group_by": {
                "type": "array",
                "minItems": 1,
                "maxItems": limits.max_groups,
                "items": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "minLength": 1},
                        "granularity": {"enum": _sorted(GRANULARITIES)},
                        **element,
                    },
                    "required": ["ref", "origin"],
                    "additionalProperties": False,
                },
            },
            "measures": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "function": {"enum": _sorted(AGGREGATIONS)},
                        "ref": {"type": "string", "minLength": 1},
                        **element,
                    },
                    "required": ["function", "origin"],
                    "additionalProperties": False,
                },
            },
            "order_by": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "minLength": 1},
                        "direction": {"enum": _sorted(DIRECTIONS)},
                        **element,
                    },
                    "required": ["ref", "direction", "origin"],
                    "additionalProperties": False,
                },
            },
            "limit": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer", "minimum": 1, "maximum": limits.max_records},
                    **element,
                },
                "required": ["value", "origin"],
                "additionalProperties": False,
            },
            "presentation": {
                "type": "object",
                "properties": {"view": {"enum": _sorted(VIEWS)}, **element},
                "required": ["view", "origin"],
                "additionalProperties": False,
            },
        },
        # `limit` and `presentation` are mandatory and always carry their effective
        # value, even when derived (§5.8, §14.3 rule 5, §15.7).
        "required": ["dsl_version", "target", "limit", "presentation"],
        "additionalProperties": False,
        "$defs": {
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "provenance": _provenance(),
            "value": _value(),
            "condition": _condition(in_state=True),
            "node": {
                "oneOf": [
                    {"$ref": "#/$defs/condition"},
                    {
                        "type": "object",
                        "properties": {
                            "connective": {"enum": _sorted(CONNECTIVES)},
                            "conditions": {
                                "type": "array",
                                "minItems": 1,
                                "items": {"$ref": "#/$defs/node"},
                            },
                        },
                        "required": ["connective", "conditions"],
                        "additionalProperties": False,
                    },
                ],
                "description": (
                    "A tree with closed connectives and a maximum depth of "
                    f"{limits.max_filter_depth} (§5.4). The depth is checked at "
                    "level 4: JSON Schema can express recursion but not a bound "
                    "on it."
                ),
            },
        },
    }


#: The two artefacts, by file name, as written under `contract/schema/`.
ARTEFACTS = {
    f"dsl-{DSL_VERSION}-envelope.json": build_envelope_schema,
    f"dsl-{DSL_VERSION}-state.json": build_state_schema,
}
