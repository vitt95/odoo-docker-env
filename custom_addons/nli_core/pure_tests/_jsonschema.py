"""A JSON Schema evaluator covering exactly the keywords `contract.schema` emits.

Test infrastructure, not product code — hence the leading underscore, which also
keeps the pure-zone runner from collecting it as a test module.

**Why write one instead of installing `jsonschema`.** The Odoo 18 image ships
neither `jsonschema` nor `fastjsonschema` (checked), so using one would add a
dependency to `config/requirements.txt` for a test aid, and a dependency inside
the pure zone at that. The alternative — shipping a schema nobody evaluates — is
worse: a formal schema that is never run against anything is an artefact that
looks like a guarantee and is not one.

The evaluator is deliberately strict about unknown keywords: it raises rather than
skipping. A schema keyword silently ignored is a constraint silently dropped, and
the schema's job is to be the thing a provider constrains generation against.
"""

from __future__ import annotations

from typing import Any

SUPPORTED = frozenset({
    "$schema", "$id", "title", "description", "$defs", "$ref",
    "type", "const", "enum",
    "properties", "required", "additionalProperties",
    "items", "minItems", "maxItems",
    "minimum", "maximum", "minLength",
    "oneOf", "anyOf", "allOf", "not", "if", "then",
})

TYPES: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "null": (type(None),),
}


class SchemaError(Exception):
    """The schema itself uses something this evaluator does not implement."""


def validate(instance: Any, schema: dict, *, root: dict | None = None, path: str = "") -> list[str]:
    """Return a list of human-readable errors; empty means valid."""
    root = schema if root is None else root
    unknown = schema.keys() - SUPPORTED
    if unknown:
        raise SchemaError(f"{path or '<root>'}: unsupported keywords {sorted(unknown)}")

    if "$ref" in schema:
        return validate(instance, _resolve(schema["$ref"], root), root=root, path=path)

    errors: list[str] = []

    if "type" in schema:
        expected = schema["type"]
        allowed = TYPES[expected]
        # In JSON, true is not 1 and 1 is not true.
        if isinstance(instance, bool) and expected != "boolean":
            errors.append(f"{path}: expected {expected}, found boolean")
        elif not isinstance(instance, allowed):
            errors.append(f"{path}: expected {expected}, found {type(instance).__name__}")
        elif expected == "integer" and isinstance(instance, float):
            errors.append(f"{path}: expected integer, found float")

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}, found {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} above maximum {schema['maximum']}")

    if isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, root, path))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for index, item in enumerate(instance):
                errors.extend(
                    validate(item, schema["items"], root=root, path=f"{path}[{index}]")
                )

    if "oneOf" in schema:
        matches = [
            branch for branch in schema["oneOf"]
            if not validate(instance, branch, root=root, path=path)
        ]
        if len(matches) != 1:
            errors.append(f"{path}: matched {len(matches)} of oneOf branches, expected 1")

    if "anyOf" in schema:
        if not any(
            not validate(instance, branch, root=root, path=path)
            for branch in schema["anyOf"]
        ):
            errors.append(f"{path}: matched no anyOf branch")

    if "allOf" in schema:
        for index, branch in enumerate(schema["allOf"]):
            errors.extend(validate(instance, branch, root=root, path=path))

    if "not" in schema:
        if not validate(instance, schema["not"], root=root, path=path):
            errors.append(f"{path}: matched a forbidden shape")

    if "if" in schema:
        if not validate(instance, schema["if"], root=root, path=path):
            if "then" in schema:
                errors.extend(validate(instance, schema["then"], root=root, path=path))

    return errors


def _validate_object(instance: dict, schema: dict, root: dict, path: str) -> list[str]:
    errors: list[str] = []
    properties = schema.get("properties", {})

    for key in schema.get("required", []):
        if key not in instance:
            errors.append(f"{path}: missing required '{key}'")

    if schema.get("additionalProperties") is False:
        for key in sorted(instance.keys() - properties.keys()):
            errors.append(f"{path}: unexpected property '{key}'")

    for key, value in instance.items():
        if key in properties:
            errors.extend(
                validate(value, properties[key], root=root, path=f"{path}.{key}" if path else key)
            )
    return errors


def _resolve(reference: str, root: dict) -> dict:
    if not reference.startswith("#/"):
        raise SchemaError(f"only local references are supported, got {reference!r}")
    node: Any = root
    for segment in reference[2:].split("/"):
        node = node[segment]
    return node
