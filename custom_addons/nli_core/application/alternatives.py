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

**An option must be applicable as it stands.** `for_ungrounded` builds the operations;
`grounded_in` gives the replaced condition the words the user will have said when they
pick it, and `chosen` recognises the answer that picks one. The three together are what
lets a chosen reading run without going back to the model — see D121.
"""

from __future__ import annotations

import copy
import re
import unicodedata
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


def for_unanchored(
    operations: Sequence[dict],
    *,
    reference: str,
    choices: Sequence[str],
    limit: int = MAX_OPTIONS,
) -> list[Alternative]:
    """Readings for a period the sentence did not anchor, one per exposed date (**D135**).

    **Why these are built here and not asked of the model.** Same argument as
    `for_ungrounded`, and with a measurement behind it: the prompt used to ask the model
    to write this very question, and on the two entities that need it — `crm.lead` and
    `sale.order` — the answer was `not_understood` three times out of three (batteria del
    3 agosto 2026). The options are not a judgement call: they are the anchor of D110,
    one option each, with the period the model already placed correctly.

    **Every date is offered, including the one the model chose.** This is where it
    parts company with `for_ungrounded`, and the reason is that the two failures are not
    the same. There, the refused condition was invented and proposing it again would be
    proposing a mistake; here it is one of the dates the entity really exposes, and
    dropping it would put the right answer out of reach whenever the guess happened to
    be right.

    **And no reading drops the period.** D111: a time expression is not let fall. The
    first option of D106 — *«senza quel filtro»* — has no counterpart here, because the
    sentence does say a period; what it does not say is where it goes.
    """
    if not any(_names_condition(operation, reference) for operation in operations):
        # The reference is not among the operations: nothing to move, and no honest
        # alternative to offer.
        return []

    readings: list[Alternative] = []
    for candidate in choices:
        if len(readings) >= limit:
            break
        replaced = []
        for operation in operations:
            copied = copy.deepcopy(operation)
            if _names_condition(operation, reference):
                copied["condition"]["ref"] = candidate
            replaced.append(copied)
        readings.append(Alternative(kind="instead", ref=candidate, operations=replaced))

    return readings if len(readings) >= MIN_OPTIONS else []


def grounded_in(operations: Sequence[dict], reference: str, fragment: str) -> list[dict]:
    """The same operations, with the named condition founded in `fragment`.

    **Why an option needs this to be usable.** The `instead` reading keeps the fragment
    of the sentence that produced the refused condition — *«lo scorso mese»* — while
    replacing the reference with another one. Applied as it stands it fails level 3
    again, and for the right reason: that fragment does not mention this condition
    either. The option would be a choice that cannot be taken.

    **Why the fragment is the label, and why that is true and not a trick.** The option
    is picked by saying its label: clicking writes the label into the box and sends it
    (D121), and typing it by hand arrives at the same place. So at the moment the
    reading is applied, the fragment that produced the condition really is those words —
    §10.3 asks for the fragment of the user's sentence, and that is what this is. The
    condition stops being something the model asserted and becomes something the user
    said, which is exactly the difference D105 was written to detect.
    """
    grounded = []
    for operation in operations:
        copied = copy.deepcopy(operation)
        if _names_condition(operation, reference):
            copied["provenance"] = {"text": fragment}
        grounded.append(copied)
    return grounded


#: Punctuation that decorates a label rather than distinguishing it, dropped wherever
#: it occurs and not only at the ends. Quotation marks because a label quotes the
#: user's own fragment inside itself — *«senza filtrare per “lo scorso mese”»* — and
#: nobody retyping it reproduces the typographic pair. Brackets because a label
#: qualifies itself with them — *«Anno corrente (2024)»* — and somebody answering
#: writes *«anno corrente 2024»*. Two labels that differ only by these characters are
#: caught by the ambiguity rule below, which asks instead of guessing.
_DECORATION = str.maketrans({character: None for character in "«»\"'“”‘’`()[]"})


def _comparable(text: str) -> str:
    """A sentence reduced to what matters for recognising an answer.

    Case, spacing, brackets, quotation marks and a final full stop are not choices the
    user made — accepting *«Da consegnare»* for *«da consegnare»* costs nothing and
    refusing it would make the option look broken. Accents are **kept**: two named
    conditions that differ only by an accent are two different conditions, and
    collapsing them here would pick the wrong one silently.
    """
    normalised = unicodedata.normalize("NFC", text or "").casefold()
    normalised = normalised.translate(_DECORATION)
    normalised = re.sub(r"\s+", " ", normalised).strip()
    return normalised.rstrip(".!?… ").strip()


def chosen(options: Sequence[dict], utterance: str, *,
           entity_known: bool = False) -> list[dict] | None:
    """The operations of the option this sentence picks, or `None`.

    **Why the answer is compared here and not sent to the model.** The operations of
    every option are already in the envelope — that is what D106 put there. A sentence
    that picks one needs no interpretation: interpreting it would spend a minute of
    model time to rediscover a list we wrote ourselves, and could rediscover it
    differently, which is the failure this closes.

    **Why an ambiguous match is not a match.** Two options that read the same are a
    defect in how they were worded, and guessing between them would answer a question
    the user did not settle. It falls through to the ordinary path, which asks.

    **Why an option without an entity is not taken.** The readings of D106 are whole
    requests, because they are built from one. A clarification the *model* wrote is
    only as complete as the model made it: an option carrying the disambiguating
    operation alone, with no `set_target`, applies to nothing. `entity_known` says the
    conversation already has an entity to apply it to; without it and without a target
    of its own, the option is refused here and the sentence takes the ordinary path,
    which can still answer it. Applying it and failing would turn a model's partial
    answer into *«non ho capito»*, which is the same defect wearing our name.
    """
    wanted = _comparable(utterance)
    if not wanted:
        return None
    matching = [option for option in options
                if _comparable(option.get("label") or "") == wanted]
    if len(matching) != 1:
        return None
    operations = matching[0].get("operations") or []
    if not operations:
        return None
    if not entity_known and not any(
            operation.get("op") == "set_target" for operation in operations):
        return None
    return copy.deepcopy(operations)
