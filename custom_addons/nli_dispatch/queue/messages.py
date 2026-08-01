"""The refusal messages of D69, and the three properties they must have.

D69's delibera says why this file is not decoration:

    **D20c** survives or falls with these messages. Written as faults, they generate
    support tickets, and support tickets get the limits raised — back to RA3.

So a refusal message here obeys three rules, and each of them is asserted in a test
rather than trusted to whoever writes the next one:

1. **no fault tone.** The system is busy, nothing is broken;
2. **no attribution to the user.** Never *"you sent too many requests"*: the user did
   nothing wrong by asking a question;
3. **always an action.** A message that leaves the reader with nothing to do is a
   dead end, and a dead end is what makes a limit look like a defect.

The messages are Italian because they are read by the user, unlike the model prompt
of `nli_engine`, which is English because it is read by a model. D72 draws the same
line for dictionary names: the language follows the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import limits as limits_module


@dataclass(frozen=True)
class Refusal:
    """What the user is told, and what they can do about it."""

    reason: str
    text: str
    action: str

    def __post_init__(self):
        if not self.action:
            raise ValueError("a refusal without an action is a dead end (D69)")


#: Keyed on the closed set of `limits.REFUSAL_REASONS`. Completeness is asserted:
#: a reason with no message would surface as an empty refusal, which is the worst of
#: the three failures above because it looks like a bug.
MESSAGES: dict[str, Refusal] = {
    limits_module.QUEUE_DEPTH: Refusal(
        reason=limits_module.QUEUE_DEPTH,
        text="In questo momento ci sono molte richieste in corso.",
        action="Riprova fra qualche secondo.",
    ),
    limits_module.RATE: Refusal(
        reason=limits_module.RATE,
        text="Le richieste di questa sessione arrivano piu' rapidamente di quanto "
             "il sistema le elabori.",
        action="Attendi qualche secondo e riprova.",
    ),
    limits_module.PROVIDER_DOWN: Refusal(
        reason=limits_module.PROVIDER_DOWN,
        text="Il servizio di interpretazione non risponde in questo momento. Le "
             "interrogazioni salvate restano disponibili.",
        action="Riapri un'interrogazione salvata, oppure riprova fra qualche minuto.",
    ),
    limits_module.EXPIRED: Refusal(
        reason=limits_module.EXPIRED,
        text="La richiesta e' rimasta in attesa piu' a lungo di quanto abbia senso, "
             "e non e' stata eseguita.",
        action="Riproponi la domanda.",
    ),
}

#: Words that would break rule 1 or rule 2. Deliberately short and deliberately
#: checked: the list is not a style guide, it is the tripwire for the next message
#: somebody adds in a hurry while an installation is under load.
FORBIDDEN_WORDS = (
    "errore",
    "fallit",
    "hai superato",
    "troppe richieste",
    "non puoi",
    "non e' consentito",
    "limite superato",
)


def refusal(reason: str) -> Refusal:
    """The message for a reason, or an explicit failure if there is none."""
    try:
        return MESSAGES[reason]
    except KeyError:
        raise KeyError(
            f"no refusal message for {reason!r}: a refusal the user cannot read is a "
            "refusal they will report as a defect (D69)"
        ) from None


def rendered(reason: str) -> str:
    message = refusal(reason)
    return f"{message.text} {message.action}"
