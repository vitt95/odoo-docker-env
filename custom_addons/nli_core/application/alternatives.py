"""The readings a refusal can offer instead of stopping (D106).

**Why this is not asked of the model.** `03` §5.9 settles the principle for the view —
*«chiedere al modello di scegliere la vista violerebbe C2/P4: è una decisione derivabile
dalla forma dello stato»* — and it applies unchanged here. Once D105 has established
that a named condition is not founded in its fragment, the plausible alternatives are
derivable: either the condition was not asked for at all, or the user meant one of the
named conditions this entity has. Asking a model that has just invented a condition to
also invent its alternatives would compound the error rather than repair it.

**Why the refusal has to propose.** D105 turns an invented filter into a refusal, which
is already the trade D2 asks for — a refusal is an error the user can see, an invented
filter is one they believe. But a bare *«non ho capito»* leaves them exactly where they
were, with no idea what to write instead. The options are also where the perimeter of
`13-perimetro-guidato.md` does its teaching: the user learns three ways of saying a
thing by choosing one.

**One question at a time.** With two ungrounded conditions the question would carry two
axes at once, and an option would have to combine a choice on each. The contract admits
from two to four options (§4.4), not a matrix.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Sequence

#: What the contract admits for a clarification (§4.4). Fewer than two is not a
#: question, more than four is a list nobody reads.
MIN_OPTIONS = 2
MAX_OPTIONS = 4


@dataclass(frozen=True)
class Alternative:
    """One reading of the sentence, and the operations that would produce it."""

    #: `without` drops the condition; `instead` replaces the reference with another.
    kind: str
    #: The named condition proposed, for `instead`. The caller turns it into words:
    #: the wording is the user's language, and this module has none.
    ref: str | None
    operations: list[dict]


def _names_condition(operation: dict, reference: str) -> bool:
    return (operation.get("op") in ("add_condition", "replace_condition")
            and (operation.get("condition") or {}).get("ref") == reference)


def for_ungrounded(
    operations: Sequence[dict],
    *,
    ungrounded: Sequence[str],
    candidates: Sequence[str],
    limit: int = MAX_OPTIONS,
) -> list[Alternative]:
    """Readings for the first ungrounded condition, or nothing.

    Returns an empty list when fewer than two readings exist — a clarification with one
    option is not a question, and a refusal that pretends to offer a choice is worse
    than one that admits there is none.
    """
    if not ungrounded:
        return []
    reference = ungrounded[0]

    #: References already used by other conditions of this same envelope: proposing one
    #: of them would offer the user a condition they are already under.
    taken = {
        (operation.get("condition") or {}).get("ref")
        for operation in operations
        if operation.get("op") in ("add_condition", "replace_condition")
    }

    without = [copy.deepcopy(operation) for operation in operations
               if not _names_condition(operation, reference)]
    if len(without) == len(operations):
        # The reference is not among the operations: nothing to drop, nothing to
        # replace, and no honest alternative to offer.
        return []
    readings = [Alternative(kind="without", ref=None, operations=without)]

    for candidate in candidates:
        if len(readings) >= limit:
            break
        if candidate == reference or candidate in taken:
            continue
        replaced = []
        for operation in operations:
            copied = copy.deepcopy(operation)
            if _names_condition(operation, reference):
                copied["condition"]["ref"] = candidate
            replaced.append(copied)
        readings.append(Alternative(kind="instead", ref=candidate, operations=replaced))

    return readings if len(readings) >= MIN_OPTIONS else []
