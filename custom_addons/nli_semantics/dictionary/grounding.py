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


def mentions_of(dictionary) -> Callable[[str, str], bool]:
    """Build the `mentions(ref, text)` the level-3 grounding check needs.

    The index is built once and captured: it is read at every condition of every turn,
    and rebuilding it per call would put the dictionary's whole term list inside the
    request path for nothing.
    """
    index = dictionary.term_index(entry_types=NAMED_CONDITION_TYPES)

    def mentions(reference: str, text: str) -> bool:
        if not reference or not text:
            return False
        return any(match.ref == reference
                   for match in index.match(text, entry_types=NAMED_CONDITION_TYPES))

    return mentions
