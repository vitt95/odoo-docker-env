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


def _condition(*, in_state: bool) -> dict:
    properties: dict = {
        "ref": {"type": "string", "minLength": 1},
        "predicate": {"enum": _sorted(PREDICATES)},
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


def _operation_schema(verb: str, signature: envelope_module.Signature) -> dict:
    properties: dict = {
        "op": {"const": verb},
        "provenance": {"$ref": "#/$defs/provenance"},
        "confidence": {"$ref": "#/$defs/confidence"},
        "origin": {"enum": _sorted(ORIGINS)},
    }
    for key in sorted(signature.allowed - envelope_module.COMMON_OPERATION_KEYS):
        properties[key] = _parameter_schema(key)
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


def _parameter_schema(key: str) -> dict:
    if key == "condition":
        return {"$ref": "#/$defs/operation_condition"}
    if key == "refs":
        return {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1}
    if key == "ref" or key == "id":
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


def build_envelope_schema() -> dict:
    """The schema of the Interpretation Envelope (§4.4)."""
    outcome_branches = []
    payload_keys = _sorted({key for key in OUTCOME_PAYLOAD.values() if key})
    for outcome in _sorted(OUTCOMES):
        payload = OUTCOME_PAYLOAD[outcome]
        branch: dict = {
            "if": {"properties": {"outcome": {"const": outcome}}, "required": ["outcome"]},
            "then": {
                "required": ["outcome"] + ([payload] if payload else []),
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
            "operation_condition": _condition(in_state=False),
            "selector": _selector(),
            "operation": {
                "oneOf": [
                    _operation_schema(verb, envelope_module.OPERATION_SIGNATURES[verb])
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
