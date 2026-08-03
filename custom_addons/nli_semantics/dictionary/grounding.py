"""Whether a fragment of the user's sentence mentions a named condition (D105).

The check itself lives at level 3, in `nli_core`, which depends on nothing and
therefore cannot know that *«provvisore»* is *«provvisorie»* misspelled. Deciding what
counts as **mentioning** a term is the dictionary's job, and this module is the whole
of it: one function, handed to the validator as a callable.

**It reuses phase A's matcher on purpose.** The corpus perturbs its own sentences with
typos, missing accents, abbreviations and lowercasing (D83), and users do the same
without being asked. A literal comparison would refuse correct answers — turning a
protection into a defect. Phase A already resolves the entity through `TermIndex`,
measured at 86,2% with zero wrong determinations: a second, different notion of *the
same word* would be a worse failure than the one being fixed.
"""

from __future__ import annotations

from typing import Callable

#: Named conditions are T5 entries (`06` §4, D87). Their terms are what a fragment
#: has to contain for the condition to be founded.
NAMED_CONDITION_TYPES = frozenset({"T5"})

#: Entities and attributes are T1 entries — *naming*. They are what D135 asks about:
#: whether the fragment that carried a period named the date it landed on.
NAMING_TYPES = frozenset({"T1"})


def _recogniser(dictionary, entry_types) -> Callable[[str, str], bool]:
    """`(ref, text) -> bool` over one family of entries.

    The index is built once and captured: it is read at every condition of every turn,
    and rebuilding it per call would put the dictionary's whole term list inside the
    request path for nothing.
    """
    index = dictionary.term_index(entry_types=entry_types)

    def recognises(reference: str, text: str) -> bool:
        if not reference or not text:
            return False
        return any(match.ref == reference
                   for match in index.match(text, entry_types=entry_types))

    return recognises


def mentions_of(dictionary) -> Callable[[str, str], bool]:
    """Build the `mentions(ref, text)` the level-3 grounding check needs (D105)."""
    return _recogniser(dictionary, NAMED_CONDITION_TYPES)


def names_of(dictionary) -> Callable[[str, str], bool]:
    """Build the `names(ref, text)` the level-3 anchoring check needs (**D135**).

    **Why a second recogniser and not the same one.** `mentions_of` indexes T5 only,
    which is right for a named condition and blind to an attribute: asking it whether
    *«con data di creazione»* names `create_date` would always answer no, and the check
    would refuse every period including the ones the user anchored themselves.

    The two are separate on purpose rather than merged into one index over both
    families. A fragment naming a category would then also count as naming an
    attribute of the same reference, and the two rules would start passing each
    other's cases — which is the failure mode of every shared matcher.
    """
    return _recogniser(dictionary, NAMING_TYPES)
