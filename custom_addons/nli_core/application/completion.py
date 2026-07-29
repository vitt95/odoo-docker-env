"""What the chain fills in before applying, because the model must not be asked.

**P4, stated once and applied here.** Information derivable deterministically is not
asked of the model. `03` §5.9 makes the argument for the view — *«chiedere al modello
di scegliere la vista violerebbe C2/P4: è una decisione derivabile dalla forma dello
stato»* — and the direction of an ordering is the same kind of thing one step earlier:
it is derivable from the **type** of the attribute, which the Semantic Dictionary
holds and the model never sees a reason to reason about.

**D88 said where it belongs and stopped there.** The Applicator refuses an operation
with no direction rather than defaulting to `asc`, because ascending on a date turns
*"the latest five orders"* into the five oldest — an answer that looks right and is
exactly backwards. It named the Resolver as the component that would derive it. But
the Resolver reads `entry["direction"]` and never wrote one, so in practice the
direction was left to the model: the obligation existed and nothing discharged it.
This module discharges it, before application, where the operations still are.

**The rule is declared, not just applied** (§10.2). A user who did not ask for an
ordering and receives one must be able to see which rule produced it and contradict
it with a sentence — that is the whole reason `origin: inferred` exists.
"""

from __future__ import annotations

import copy

#: Types on which "no direction named" means *the most recent first*.
DATE_TYPES = frozenset({"date", "datetime"})

#: The operations that carry a direction.
ORDER_OPERATIONS = frozenset({"add_order", "set_order"})


def direction_for(attribute_type: str | None) -> str:
    """The direction an unnamed ordering takes on an attribute of this type.

    Only the direction: the **rule** that names the inference belongs to the state,
    and an operation may not carry it — §15.3 rejects unknown keys, and an operation
    is a request rather than an explanation. The Applicator derives the identifier
    from the direction and the origin, which is the same information said once.
    """
    return "desc" if attribute_type in DATE_TYPES else "asc"


def fill_inferred_directions(operations: list[dict], types: dict[str, str]) -> list[dict]:
    """Complete ordering operations the user did not give a direction for.

    A direction the model **did** name is left alone: *"dal più recente"* is the
    user's request, and overwriting it with a derivation would silently discard what
    the sentence said. Only the absent one is filled, and it is marked `inferred`.

    An unknown reference is left untouched. It is not this module's business to
    reject one — level 3 does that against the dictionary of the user who asked, and
    a reference invented here would be refused there anyway. Filling a direction for
    it would only make a broken operation look complete.
    """
    completed = []
    for operation in operations:
        if (operation.get("op") not in ORDER_OPERATIONS
                or operation.get("direction")
                or operation.get("ref") not in types):
            completed.append(operation)
            continue
        filled = copy.deepcopy(operation)
        filled["direction"] = direction_for(types[operation["ref"]])
        filled["origin"] = "inferred"
        completed.append(filled)
    return completed
