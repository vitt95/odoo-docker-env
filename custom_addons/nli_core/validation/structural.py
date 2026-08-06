"""Validation levels 1-2: structure and vocabulary (`03` §12.3).

**Pure zone.** Whether an envelope is well formed, and whether its symbols belong
to the closed vocabularies, are questions with exact answers that depend on
neither the platform, nor the user's permissions, nor the time of day. Levels 3
to 5 do depend on those, and live in `contextual.py` and `coherence.py`.

Two rules of §12 shape the interface of this module.

**Nothing invalid proceeds** (§12.1). Validation is total and precedes
application; there is no partial validation and no permissive mode — a
permissive mode is a code path that eventually reaches production.

**The first failing level stops the chain** (§12.2). Level 2 does not run if
level 1 failed, because a symbol read from a malformed structure is not a symbol.
Within a level every failure is reported, so the single repair attempt of D15
gets the whole picture instead of one error at a time.

An unknown key is **rejected, never ignored** (§15.3, D14). Tolerating unknown
fields is the most dangerous choice available here: a reader that ignores a
condition it does not understand runs a query *less filtered* than the one
requested and returns more records than it should, with no signal at all.
"""

from __future__ import annotations

from ..contract import envelope as envelope_module
from ..contract import state as state_module
from ..contract.failure import Failure
from ..contract.vocabulary import (
    AGGREGATIONS,
    CONNECTIVES,
    DIRECTIONS,
    GRANULARITIES,
    INFERENCE_RULES,
    OPERATIONS,
    ORIGINS,
    OUTCOME_PAYLOAD,
    OUTCOMES,
    PREDICATES,
    PREDICATES_VALUE_FORBIDDEN,
    PREDICATES_WITH_OPTIONAL_VALUE,
    SCOPE_NOTES,
    SELECTORS,
    SUPPORTED_VERSIONS,
    TEMPORAL_EXPRESSIONS,
    TEMPORAL_OPTIONAL_KEYS,
    TEMPORAL_PARAMETER_RANGE,
    TEMPORAL_REQUIRED_KEYS,
    VALUE_KINDS,
    VALUE_OPTIONAL_KEYS,
    VIEWS,
    Limits,
)
from ..contract.vocabulary import DEFAULT_LIMITS

#: `combine` on `add_condition` admits only the two binary connectives: `not` is
#: expressed as a node of the tree, never as a way of combining an addition.
COMBINE_VALUES = frozenset({"all", "any"})

REQUIRED_STATE_SECTIONS = frozenset({"target", "limit", "presentation"})
KNOWN_STATE_KEYS = frozenset({"dsl_version", *state_module.SECTIONS})


class _Collector:
    """Accumulates failures for one level, so a level reports all of its own."""

    def __init__(self, level: int) -> None:
        self.level = level
        self.failures: list[Failure] = []

    def add(self, code: str, path: str, detail: str) -> None:
        self.failures.append(
            Failure(level=self.level, code=code, path=path, detail=detail)
        )

    @property
    def clean(self) -> bool:
        return not self.failures


# ---------------------------------------------------------------------------
# Level 1 — structure
# ---------------------------------------------------------------------------

def _check_object(candidate: object, path: str, out: _Collector) -> bool:
    if not isinstance(candidate, dict):
        out.add(
            "not_an_object",
            path,
            f"expected an object, found {type(candidate).__name__}",
        )
        return False
    return True


def _check_keys(
    candidate: dict,
    path: str,
    required: frozenset[str],
    allowed: frozenset[str],
    out: _Collector,
) -> None:
    for key in sorted(required - candidate.keys()):
        out.add("missing_key", path, f"'{key}' is required")
    for key in sorted(candidate.keys() - allowed):
        out.add(
            "unknown_key",
            path,
            f"'{key}' is not part of the contract; unknown keys are rejected, "
            "never ignored (§15.3)",
        )


def _check_value_structure(value: object, path: str, out: _Collector) -> None:
    if not _check_object(value, path, out):
        return
    assert isinstance(value, dict)
    if "kind" not in value:
        out.add("missing_key", path, "'kind' is required")
        return
    kind = value["kind"]
    if kind not in VALUE_KINDS:
        # Membership is a level 2 concern; without a known kind the key check
        # below has no reference set, so it is skipped rather than guessed.
        return
    _check_keys(
        value,
        path,
        VALUE_KINDS[kind] | {"kind"},
        VALUE_KINDS[kind] | VALUE_OPTIONAL_KEYS[kind] | {"kind"},
        out,
    )
    if kind == "enum":
        items = value.get("items")
        if not isinstance(items, list) or not items:
            out.add("empty_set", f"{path}.items", "must be a non-empty list")
    if kind == "range":
        for edge in ("from", "to"):
            if edge in value and not isinstance(value[edge], (int, float)):
                out.add("not_a_number", f"{path}.{edge}", "must be a number")
    if kind == "number" and not isinstance(value.get("value"), (int, float)):
        out.add("not_a_number", f"{path}.value", "must be a number")
    if kind == "boolean" and not isinstance(value.get("value"), bool):
        out.add("not_a_boolean", f"{path}.value", "must be true or false")
    if kind in ("text", "reference") and not isinstance(value.get("text"), str):
        out.add("not_a_string", f"{path}.text", "must be a string")


def _check_condition_structure(condition: object, path: str, out: _Collector) -> None:
    if not _check_object(condition, path, out):
        return
    assert isinstance(condition, dict)
    _check_keys(
        condition,
        path,
        envelope_module.REQUIRED_CONDITION_KEYS,
        envelope_module.REQUIRED_CONDITION_KEYS
        | envelope_module.OPTIONAL_CONDITION_KEYS
        | {"id"},
        out,
    )
    if not isinstance(condition.get("ref", ""), str) or not condition.get("ref", ""):
        out.add("not_a_string", f"{path}.ref", "must be a non-empty string")
    predicate = condition.get("predicate")
    if predicate in PREDICATES_VALUE_FORBIDDEN:
        if "value" in condition:
            out.add(
                "unexpected_value",
                f"{path}.value",
                f"predicate '{predicate}' takes no value",
            )
    elif predicate in PREDICATES_WITH_OPTIONAL_VALUE:
        if "value" in condition:
            _check_value_structure(condition["value"], f"{path}.value", out)
    elif predicate in PREDICATES:
        if "value" not in condition:
            out.add(
                "missing_key",
                path,
                f"predicate '{predicate}' requires a value",
            )
        else:
            _check_value_structure(condition["value"], f"{path}.value", out)
    elif "value" in condition:
        # Unknown predicate: level 2 reports it. Still check the value's own
        # shape, so one unknown symbol does not hide a second defect.
        _check_value_structure(condition["value"], f"{path}.value", out)


def _check_operation_structure(operation: object, index: int, out: _Collector) -> None:
    path = f"operations[{index}]"
    if not _check_object(operation, path, out):
        return
    assert isinstance(operation, dict)
    verb = operation.get("op")
    if not isinstance(verb, str):
        out.add("missing_key", path, "'op' is required and must be a string")
        return
    signature = envelope_module.OPERATION_SIGNATURES.get(verb)
    if signature is None:
        # Unknown verb: level 2 reports it; there is no signature to check against.
        return

    _check_keys(operation, path, signature.required, signature.allowed, out)
    for group in signature.one_of:
        present = sorted(group & operation.keys())
        if not present:
            out.add(
                "missing_key",
                path,
                f"exactly one of {sorted(group)} is required",
            )
        elif len(present) > 1:
            out.add(
                "ambiguous_addressing",
                path,
                f"only one of {sorted(group)} may be given, found {present}",
            )

    if "condition" in operation:
        _check_condition_structure(operation["condition"], f"{path}.condition", out)
    if "refs" in operation:
        refs = operation["refs"]
        if not isinstance(refs, list) or not refs:
            out.add("empty_set", f"{path}.refs", "must be a non-empty list")
        elif not all(isinstance(ref, str) and ref for ref in refs):
            out.add("not_a_string", f"{path}.refs", "every entry must be a reference")
    if "value" in operation and verb == "set_limit":
        limit = operation["value"]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            out.add("not_a_number", f"{path}.value", "must be a positive integer")
    if "selector" in operation:
        _check_selector_structure(operation["selector"], f"{path}.selector", out)
    if "position" in operation:
        position = operation["position"]
        if not isinstance(position, int) or isinstance(position, bool) or position < 0:
            out.add(
                "not_a_number",
                f"{path}.position",
                "must be a non-negative integer",
            )
    _check_confidence(operation, path, out)


def _check_selector_structure(selector: object, path: str, out: _Collector) -> None:
    if not _check_object(selector, path, out):
        return
    assert isinstance(selector, dict)
    by = selector.get("by")
    if by is None:
        out.add("missing_key", path, "'by' is required")
        return
    if by not in SELECTORS:
        return  # level 2
    if by == "position":
        _check_keys(selector, path, frozenset({"by", "value"}), frozenset({"by", "value"}), out)
        position = selector.get("value")
        if not isinstance(position, int) or isinstance(position, bool) or position < 1:
            out.add("not_a_number", f"{path}.value", "must be a positive position")
    else:
        _check_keys(
            selector,
            path,
            frozenset({"by", "ref", "value"}),
            frozenset({"by", "ref", "value"}),
            out,
        )
        if "value" in selector:
            _check_value_structure(selector["value"], f"{path}.value", out)


def _check_confidence(carrier: dict, path: str, out: _Collector) -> None:
    if "confidence" not in carrier:
        return
    confidence = carrier["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        out.add("not_a_number", f"{path}.confidence", "must be a number")
    elif not 0.0 <= float(confidence) <= 1.0:
        out.add(
            "out_of_range",
            f"{path}.confidence",
            "must be between 0 and 1 — it is a scalar signal, not a probability (§10.5)",
        )


def _check_clarification_structure(
    clarification: object,
    limits: Limits,
    out: _Collector,
) -> None:
    path = "clarification"
    if not _check_object(clarification, path, out):
        return
    assert isinstance(clarification, dict)
    _check_keys(
        clarification,
        path,
        envelope_module.REQUIRED_CLARIFICATION_KEYS,
        envelope_module.REQUIRED_CLARIFICATION_KEYS
        | envelope_module.OPTIONAL_CLARIFICATION_KEYS,
        out,
    )
    if not isinstance(clarification.get("question", ""), str):
        out.add("not_a_string", f"{path}.question", "must be a string")

    options = clarification.get("options")
    if not isinstance(options, list):
        out.add("not_a_list", f"{path}.options", "must be a list")
        return
    if not limits.min_clarification_options <= len(options) <= limits.max_clarification_options:
        out.add(
            "option_count",
            f"{path}.options",
            f"{len(options)} options: admitted range is "
            f"{limits.min_clarification_options}-{limits.max_clarification_options}. "
            "A single option would be a confirmation in disguise (§11.2)",
        )
    for index, option in enumerate(options):
        option_path = f"{path}.options[{index}]"
        if not _check_object(option, option_path, out):
            continue
        _check_keys(
            option,
            option_path,
            envelope_module.REQUIRED_OPTION_KEYS,
            envelope_module.REQUIRED_OPTION_KEYS,
            out,
        )
        if not isinstance(option.get("label", ""), str) or not option.get("label", ""):
            out.add("not_a_string", f"{option_path}.label", "must be a non-empty string")
        operations = option.get("operations")
        if not isinstance(operations, list) or not operations:
            out.add(
                "empty_set",
                f"{option_path}.operations",
                "every option carries the operations it would produce (§11.2)",
            )


def _level1_envelope(candidate: object, limits: Limits) -> list[Failure]:
    out = _Collector(1)
    if not _check_object(candidate, "", out):
        return out.failures
    assert isinstance(candidate, dict)

    outcome = candidate.get("outcome")
    payload_keys = {key for key in OUTCOME_PAYLOAD.values() if key}
    _check_keys(
        candidate,
        "",
        envelope_module.REQUIRED_ENVELOPE_KEYS,
        envelope_module.REQUIRED_ENVELOPE_KEYS
        | envelope_module.OPTIONAL_ENVELOPE_KEYS
        | payload_keys,
        out,
    )

    version = candidate.get("dsl_version")
    if version is not None and version not in SUPPORTED_VERSIONS:
        out.add(
            "unsupported_version",
            "dsl_version",
            f"{version!r} is not among {sorted(SUPPORTED_VERSIONS)}",
        )

    if outcome is not None and outcome not in OUTCOMES:
        out.add("unknown_outcome", "outcome", f"{outcome!r} is not an admitted outcome")
    _check_confidence(candidate, "", out)

    if outcome in OUTCOME_PAYLOAD:
        expected = OUTCOME_PAYLOAD[outcome]
        for key in sorted(payload_keys):
            if key == expected:
                if key not in candidate:
                    out.add(
                        "missing_payload",
                        "",
                        f"outcome '{outcome}' requires '{key}'",
                    )
            elif key in candidate:
                out.add(
                    "foreign_payload",
                    key,
                    f"'{key}' does not belong to outcome '{outcome}': the four "
                    "outcomes are mutually exclusive (§4.4)",
                )

    if outcome == "operations":
        operations = candidate.get("operations")
        if operations is None:
            pass  # already reported as a missing payload
        elif not isinstance(operations, list):
            out.add("not_a_list", "operations", "must be a list")
        elif not operations:
            out.add(
                "empty_operations",
                "operations",
                "an empty operation list is not valid: an unchanged state "
                "presented as a success is indistinguishable from an ignored "
                "request, and the correct outcome is 'not_understood' (§4.4)",
            )
        else:
            for index, operation in enumerate(operations):
                _check_operation_structure(operation, index, out)

    if outcome == "clarification" and "clarification" in candidate:
        _check_clarification_structure(candidate["clarification"], limits, out)

    if outcome == "out_of_scope" and "scope_note" in candidate:
        if not isinstance(candidate["scope_note"], str):
            out.add("not_a_string", "scope_note", "must be a string")

    return out.failures


# ---------------------------------------------------------------------------
# Level 2 — vocabulary
# ---------------------------------------------------------------------------

def _check_symbol(
    value: object,
    allowed: frozenset[str],
    code: str,
    path: str,
    out: _Collector,
) -> None:
    if value is None:
        return
    if value not in allowed:
        out.add(
            code,
            path,
            f"{value!r} is not in the closed vocabulary; the model chooses, "
            f"it does not invent (C1). Admitted: {sorted(allowed)}",
        )


#: A year is four digits. Not a judgement about the data — 1912 is a year and this
#: system has nothing to say about whether records exist there — only about what is a
#: year at all: `year: 26` is a typo, and executing it as the year 26 would answer a
#: question nobody asked.
_YEAR_RANGE = (1000, 9999)


def _named_period_parameters(
    value: dict, expression: object, path: str, out: _Collector
) -> None:
    """The parameters of a named period, D141.

    Two checks, and both are about the **symbol**, not about the data. `n` outside its
    interval names no period: there is no thirteenth month in any installation, and a
    `month_of_year(13)` that got through would leave the Resolver to either crash or
    pick something plausible. And a key an expression does not admit — `year` on
    `last_n_days` — is a fragment of the sentence that would be silently dropped, which
    is the one thing **D111** forbids for time.
    """
    admitted = TEMPORAL_PARAMETER_RANGE.get(expression)
    if admitted and "n" in value:
        low, high = admitted
        which = value["n"]
        if not isinstance(which, int) or isinstance(which, bool) or not low <= which <= high:
            out.add(
                "temporal_parameter_out_of_range",
                f"{path}.n",
                f"'{expression}' admits {low}-{high}, not {which!r}",
            )

    optional = TEMPORAL_OPTIONAL_KEYS.get(expression, frozenset())
    if "year" in value:
        if "year" not in optional:
            out.add(
                "unknown_temporal_parameter",
                f"{path}.year",
                f"'{expression}' takes no year; only "
                f"{sorted(TEMPORAL_OPTIONAL_KEYS)} do",
            )
        else:
            year = value["year"]
            if (not isinstance(year, int) or isinstance(year, bool)
                    or not _YEAR_RANGE[0] <= year <= _YEAR_RANGE[1]):
                out.add(
                    "temporal_parameter_out_of_range",
                    f"{path}.year",
                    f"{year!r} is not a four-digit year",
                )


def _level2_value(value: object, path: str, out: _Collector) -> None:
    if not isinstance(value, dict):
        return
    kind = value.get("kind")
    _check_symbol(kind, frozenset(VALUE_KINDS), "unknown_value_kind", f"{path}.kind", out)
    if kind == "temporal":
        expression = value.get("expression")
        _check_symbol(
            expression,
            TEMPORAL_EXPRESSIONS,
            "unknown_temporal_expression",
            f"{path}.expression",
            out,
        )
        # The parameter of a parametric expression is part of the symbol's arity:
        # `last_n_days` without `n` names nothing.
        if expression in TEMPORAL_REQUIRED_KEYS:
            for key in sorted(TEMPORAL_REQUIRED_KEYS[expression]):
                if key not in value:
                    out.add(
                        "missing_temporal_parameter",
                        f"{path}",
                        f"'{expression}' requires '{key}'",
                    )
        _named_period_parameters(value, expression, path, out)
    if "resolver" in value:
        resolver = value["resolver"]
        # A resolver is a rule declared in the dictionary (§9.3), not a symbol of
        # the contract: its existence is a level 3 question. Level 2 can only
        # require that it is named.
        if not isinstance(resolver, str) or not resolver:
            out.add(
                "not_a_string",
                f"{path}.resolver",
                "must name a resolver defined in the dictionary",
            )


def _level2_condition(condition: object, path: str, out: _Collector) -> None:
    if not isinstance(condition, dict):
        return
    _check_symbol(
        condition.get("predicate"),
        PREDICATES,
        "unknown_predicate",
        f"{path}.predicate",
        out,
    )
    _check_symbol(condition.get("origin"), ORIGINS, "unknown_origin", f"{path}.origin", out)
    _check_symbol(
        condition.get("combine"),
        COMBINE_VALUES,
        "unknown_connective",
        f"{path}.combine",
        out,
    )
    if "value" in condition:
        _level2_value(condition["value"], f"{path}.value", out)


def _level2_envelope(candidate: dict) -> list[Failure]:
    out = _Collector(2)

    if candidate.get("outcome") == "out_of_scope":
        _check_symbol(
            candidate.get("scope_note"),
            SCOPE_NOTES,
            "unknown_scope_note",
            "scope_note",
            out,
        )
        # D118: il frammento che giustifica il rifiuto dev'esserci e non essere vuoto.
        # Uno spazio bianco e' un rifiuto senza motivo con la forma del motivo.
        frammento = (candidate.get("scope_provenance") or {}).get("text")
        if not isinstance(frammento, str) or not frammento.strip():
            out.add(
                "ungrounded_scope",
                "scope_provenance.text",
                "a refusal for scope must quote the fragment that asks for the "
                "impossible thing: without it, refusing costs nothing and becomes "
                "the exit the model takes whenever it struggles (D118)",
            )

    operations = candidate.get("operations") or []
    if candidate.get("outcome") == "clarification":
        clarification = candidate.get("clarification")
        if isinstance(clarification, dict):
            for index, option in enumerate(clarification.get("options") or []):
                if not isinstance(option, dict):
                    continue
                for inner, operation in enumerate(option.get("operations") or []):
                    _level2_operation(
                        operation,
                        f"clarification.options[{index}].operations[{inner}]",
                        out,
                    )

    for index, operation in enumerate(operations):
        _level2_operation(operation, f"operations[{index}]", out)

    return out.failures


def _level2_operation(operation: object, path: str, out: _Collector) -> None:
    if not isinstance(operation, dict):
        return
    _check_symbol(operation.get("op"), OPERATIONS, "unknown_operation", f"{path}.op", out)
    _check_symbol(operation.get("origin"), ORIGINS, "unknown_origin", f"{path}.origin", out)
    _check_symbol(operation.get("view"), VIEWS, "unknown_view", f"{path}.view", out)
    _check_symbol(
        operation.get("direction"), DIRECTIONS, "unknown_direction", f"{path}.direction", out
    )
    _check_symbol(
        operation.get("granularity"),
        GRANULARITIES,
        "unknown_granularity",
        f"{path}.granularity",
        out,
    )
    _check_symbol(
        operation.get("function"), AGGREGATIONS, "unknown_aggregation", f"{path}.function", out
    )
    _check_symbol(
        operation.get("combine"), COMBINE_VALUES, "unknown_connective", f"{path}.combine", out
    )
    selector = operation.get("selector")
    if isinstance(selector, dict):
        _check_symbol(selector.get("by"), SELECTORS, "unknown_selector", f"{path}.selector.by", out)
        if "value" in selector:
            _level2_value(selector["value"], f"{path}.selector.value", out)
    if "condition" in operation:
        _level2_condition(operation["condition"], f"{path}.condition", out)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def validate_envelope(
    candidate: object,
    *,
    limits: Limits = DEFAULT_LIMITS,
) -> list[Failure]:
    """Levels 1 and 2 on an interpretation envelope.

    Returns every failure of the first level that failed, and an empty list when
    both pass. Levels 3 to 5 are the caller's next step, in that order (§12.2).
    """
    level1 = _level1_envelope(candidate, limits)
    if level1:
        return level1
    assert isinstance(candidate, dict)
    return _level2_envelope(candidate)


def _level1_state(candidate: object) -> list[Failure]:
    out = _Collector(1)
    if not _check_object(candidate, "", out):
        return out.failures
    assert isinstance(candidate, dict)

    _check_keys(
        candidate,
        "",
        REQUIRED_STATE_SECTIONS | {"dsl_version"},
        KNOWN_STATE_KEYS,
        out,
    )
    version = candidate.get("dsl_version")
    if version is not None and version not in SUPPORTED_VERSIONS:
        out.add(
            "unsupported_version",
            "dsl_version",
            f"{version!r} is not among {sorted(SUPPORTED_VERSIONS)}",
        )

    target = candidate.get("target")
    if target is not None and _check_object(target, "target", out):
        assert isinstance(target, dict)
        _check_keys(
            target,
            "target",
            frozenset({"ref", "origin"}),
            frozenset({"ref", "origin", "provenance", "confidence", "rule"}),
            out,
        )

    # An absent section means "no elements"; an explicitly empty one is not valid
    # (§5.5). The distinction is normative: absent `fields` means the entity's
    # default fields apply, empty `fields` would mean a view with no columns.
    for section in state_module.LIST_SECTIONS:
        if section not in candidate:
            continue
        entries = candidate[section]
        if not isinstance(entries, list):
            out.add("not_a_list", section, "must be a list")
            continue
        if not entries:
            out.add(
                "empty_section",
                section,
                "an absent section means 'no elements'; an explicitly empty one "
                "is not valid (§5.5)",
            )
        for index, entry in enumerate(entries):
            _check_state_entry(section, entry, f"{section}[{index}]", out)

    if "filter" in candidate:
        _check_filter_structure(candidate["filter"], "filter", out)

    limit = candidate.get("limit")
    if limit is not None and _check_object(limit, "limit", out):
        assert isinstance(limit, dict)
        # `provenance` belongs here as much as anywhere: "the first 5" is a
        # fragment of the user's sentence that produced the limit, and §10.3 puts
        # the fragment on *every* element produced by an expression of the user.
        _check_keys(
            limit,
            "limit",
            frozenset({"value", "origin"}),
            frozenset({"value", "origin", "rule", "provenance", "confidence"}),
            out,
        )
        value = limit.get("value")
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            out.add("not_a_number", "limit.value", "must be a positive integer")

    presentation = candidate.get("presentation")
    if presentation is not None and _check_object(presentation, "presentation", out):
        assert isinstance(presentation, dict)
        _check_keys(
            presentation,
            "presentation",
            frozenset({"view", "origin"}),
            frozenset({"view", "origin", "rule", "provenance", "confidence"}),
            out,
        )

    return out.failures


def _check_state_entry(section: str, entry: object, path: str, out: _Collector) -> None:
    if not _check_object(entry, path, out):
        return
    assert isinstance(entry, dict)
    common = frozenset({"origin", "provenance", "confidence", "rule"})
    if section == "measures":
        # `count` needs no attribute (§8.5), so `ref` is optional here alone.
        _check_keys(entry, path, frozenset({"function", "origin"}), common | {"function", "ref"}, out)
    elif section == "order_by":
        _check_keys(
            entry,
            path,
            frozenset({"ref", "direction", "origin"}),
            common | {"ref", "direction"},
            out,
        )
    elif section == "group_by":
        _check_keys(
            entry, path, frozenset({"ref", "origin"}), common | {"ref", "granularity"}, out
        )
    else:
        _check_keys(entry, path, frozenset({"ref", "origin"}), common | {"ref"}, out)
    if "ref" in entry and (not isinstance(entry["ref"], str) or not entry["ref"]):
        out.add("not_a_string", f"{path}.ref", "must be a non-empty string")
    _check_confidence(entry, path, out)


def _check_filter_structure(node: object, path: str, out: _Collector) -> None:
    if not _check_object(node, path, out):
        return
    assert isinstance(node, dict)
    if state_module.is_connective(node):
        _check_keys(
            node,
            path,
            frozenset({"connective", "conditions"}),
            frozenset({"connective", "conditions"}),
            out,
        )
        children = node.get("conditions")
        if not isinstance(children, list):
            out.add("not_a_list", f"{path}.conditions", "must be a list")
            return
        if not children:
            out.add(
                "empty_section",
                path,
                "a connective with no children is not valid: an empty filter is "
                "an absent section (§14.3 rule 7)",
            )
        if node.get("connective") == "not" and len(children) > 1:
            out.add(
                "arity",
                path,
                "'not' takes exactly one child",
            )
        for index, child in enumerate(children):
            _check_filter_structure(child, f"{path}.conditions[{index}]", out)
        return

    _check_condition_structure(node, path, out)
    if "id" not in node:
        out.add(
            "missing_key",
            path,
            "a condition in the state carries a stable identifier: it is what "
            "lets the user remove one condition without rephrasing (§5.4)",
        )
    if "origin" not in node:
        out.add("missing_key", path, "'origin' is required on every state element (§10.2)")


def _level2_state(candidate: dict) -> list[Failure]:
    out = _Collector(2)

    target = candidate.get("target")
    if isinstance(target, dict):
        _check_symbol(target.get("origin"), ORIGINS, "unknown_origin", "target.origin", out)

    for index, condition in enumerate(state_module.conditions(candidate.get("filter"))):
        _level2_condition(condition, f"filter.conditions[{index}]", out)
    for node in state_module.walk(candidate.get("filter")):
        if state_module.is_connective(node):
            _check_symbol(
                node.get("connective"), CONNECTIVES, "unknown_connective", "filter", out
            )

    for section in state_module.LIST_SECTIONS:
        for index, entry in enumerate(candidate.get(section) or []):
            if not isinstance(entry, dict):
                continue
            path = f"{section}[{index}]"
            _check_symbol(entry.get("origin"), ORIGINS, "unknown_origin", f"{path}.origin", out)
            _check_symbol(entry.get("rule"), INFERENCE_RULES, "unknown_rule", f"{path}.rule", out)
            if section == "group_by":
                _check_symbol(
                    entry.get("granularity"),
                    GRANULARITIES,
                    "unknown_granularity",
                    f"{path}.granularity",
                    out,
                )
            if section == "order_by":
                _check_symbol(
                    entry.get("direction"),
                    DIRECTIONS,
                    "unknown_direction",
                    f"{path}.direction",
                    out,
                )
            if section == "measures":
                _check_symbol(
                    entry.get("function"),
                    AGGREGATIONS,
                    "unknown_aggregation",
                    f"{path}.function",
                    out,
                )

    for section in ("limit", "presentation"):
        entry = candidate.get(section)
        if not isinstance(entry, dict):
            continue
        _check_symbol(entry.get("origin"), ORIGINS, "unknown_origin", f"{section}.origin", out)
        _check_symbol(entry.get("rule"), INFERENCE_RULES, "unknown_rule", f"{section}.rule", out)

    presentation = candidate.get("presentation")
    if isinstance(presentation, dict):
        _check_symbol(presentation.get("view"), VIEWS, "unknown_view", "presentation.view", out)

    return out.failures


def validate_state(candidate: object) -> list[Failure]:
    """Levels 1 and 2 on an Interrogation State.

    Applied to the state produced by application, not only to the envelope: §4.2
    puts validation on the operation **and** on the resulting state, because an
    individually valid operation can produce a state that is not.
    """
    level1 = _level1_state(candidate)
    if level1:
        return level1
    assert isinstance(candidate, dict)
    return _level2_state(candidate)


def validate_scope_grounding(candidate: dict, *, justifies) -> list[Failure]:
    """Il frammento citato deve **dire** la cosa che il rifiuto dichiara (**D119**).

    **D118** ha reso obbligatorio citare un frammento; questo verifica che il frammento
    citato contenga le parole di quella categoria. Senza, restava possibile rifiutare
    citando un pezzo qualunque della frase — che e' il rifiuto libero di prima con un
    passaggio in piu'.

    `justifies(scope_note, fragment)` arriva come argomento e non come import: il
    lessico e' di lingua e `nli_core` non ne ha, esattamente come per il riconoscitore
    di **D105**. Omesso, il controllo non si applica — la stessa forma che
    `validate_contextual` gia' ha, e cio' che lascia girare i test del contratto senza
    un vocabolario.
    """
    if candidate.get("outcome") != "out_of_scope":
        return []
    nota = candidate.get("scope_note")
    frammento = (candidate.get("scope_provenance") or {}).get("text") or ""
    if not isinstance(nota, str) or justifies(nota, frammento):
        return []
    return [Failure(
        2,
        "scope_not_justified",
        "scope_provenance.text",
        f"the quoted fragment {frammento!r} does not ask for {nota!r}: a refusal has "
        "to be earned by the words the user actually wrote (D119)",
    )]


#: Expressions that carry a date the user wrote instead of a period they named.
#:
#: D105 already says why they are out: a comparison carries a value the user said, and
#: there is no vocabulary to check it against. *"dal 1 gennaio 2025"* names a month and
#: a year on its way to an explicit date, and judging it as a named period would refuse
#: a correct answer.
_TEMPORAL_WRITTEN_OUT = frozenset({"absolute", "absolute_range"})


def validate_temporal_grounding(candidate: dict, *, names_period) -> list[Failure]:
    """The period the fragment **names** has to be the period the envelope says (D144).

    D105 applied to the value instead of to the reference. The failure this closes is
    not a missing symbol, it is the fallback: when the word is not in the vocabulary the
    model reaches for the nearest one and says nothing. *"nel secondo semestre"* came
    back as the second **quarter**, three runs out of three, against a prompt line that
    forbade it by name (§46.7).

    `names_period(fragment)` arrives as an argument and not as an import: the lexicon is
    language and `nli_core` has none, exactly as for D119 and D105. Omitted, the check
    does not apply.

    Three failures, all level 2:

    * **the fragment names a period no symbol can say** — *"nel primo bimestre"*. Any
      expression at all is a fallback, and the honest answer is a clarification;
    * **the fragment names a different period** — *"nel primo trimestre"* answered with
      `quarter_of_year(3)`, or with `month_of_year`;
    * **the value carries a year the fragment does not name.** A fragment naming both a
      period and a year names two periods, and then the check abstains — so this can
      only fire on a year nobody wrote.
    """
    failures: list[Failure] = []
    for index, operation in enumerate(candidate.get("operations") or []):
        if not isinstance(operation, dict):
            continue
        condition = operation.get("condition")
        if not isinstance(condition, dict):
            continue
        value = condition.get("value")
        if not isinstance(value, dict) or value.get("kind") != "temporal":
            continue
        expression = value.get("expression")
        if expression in _TEMPORAL_WRITTEN_OUT:
            continue

        fragment = (operation.get("provenance") or {}).get("text") or ""
        claim = names_period(fragment)
        if claim is None:
            continue
        symbol, parameter = claim
        path = f"operations[{index}].condition.value"

        if symbol is None:
            failures.append(Failure(
                2,
                "temporal_not_expressible",
                path,
                f"the fragment {fragment!r} names a period no expression can say: "
                f"{expression!r} is the nearest one, not the one asked for. Answer "
                "clarification instead of the closest period (D144)",
            ))
        elif (expression, value.get("n")) != (symbol, parameter):
            failures.append(Failure(
                2,
                "temporal_period_mismatch",
                path,
                f"the fragment {fragment!r} names {symbol}({parameter}), the envelope "
                f"says {expression}({value.get('n')!r}): the period has to be the one "
                "the words carry (D144)",
            ))
        elif "year" in value:
            failures.append(Failure(
                2,
                "temporal_year_not_grounded",
                f"{path}.year",
                f"the fragment {fragment!r} names no year, the envelope says "
                f"{value.get('year')!r}: a year nobody wrote is a guess (D144)",
            ))
    return failures
