"""The term index — one index, across languages (D37, `06` §10.3).

**Pure zone.** Normalisation, base forms and edit distance are functions, not
estimates: the fast path of phase A has to be deterministic, or it becomes a second
probabilistic component in front of the interpreter and RC3 gets worse instead of
better.

## Why one index and not one per language

If there were separate indexes the system would first have to decide which
language the sentence is in — ambiguous on a mixed sentence, which is the normal
case in an Italian company that says *"chiudi il deal"*, and one more failure
point. A single index makes the question irrelevant: *"deal"* and *"trattativa"*
lead to the same reference and nobody has to decide anything. The user's language
comes back only as a tie-break and as the language the interpretation is shown in.

## Why the matching weights are what they are

From `06` §5.5: exact 1.00, base form 0.90, approximate 0.70. The last one carries
two guards that are part of the rule and not tuning: never applied to a term that
already matches something else exactly, and never to short words, where a single
substitution changes the word instead of correcting a typo — *"casa"* and
*"cassa"* are one insertion apart and mean different things, and so are
*"conto"* and *"conti"* in a sentence where only one of them is the entity.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

#: Weights of `06` §5.5.
WEIGHT_EXACT = 1.00
WEIGHT_BASE_FORM = 0.90
WEIGHT_APPROXIMATE = 0.70

#: Approximate matching applies only from this length up. Below it, an edit
#: distance of one is a different word rather than a typo.
MIN_LENGTH_FOR_APPROXIMATE = 5

#: Levels in decreasing precedence (`06` §2.2). The customer has the last word.
LEVEL_PRECEDENCE = {"L2": 0, "L1": 1, "L0": 2}

_PUNCTUATION = str.maketrans({c: " " for c in "\"'`.,;:!?()[]{}<>/\\|-–—_=+*&%$#@~^"})


def strip_accents(text: str) -> str:
    return "".join(
        character for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )


def normalise(text: str) -> list[str]:
    """Lowercase, accent-free, punctuation-free tokens.

    The same normalisation the corpus perturbs against (D83): it deliberately
    produces lowercased and accent-stripped variants, so the fast path has to be
    insensitive to both or the perturbation would measure the normaliser instead of
    the dictionary.
    """
    folded = strip_accents(text).casefold().translate(_PUNCTUATION)
    return [token for token in folded.split() if token]


def base_form(token: str) -> str:
    """A crude, deterministic Italian base form: drop the final vowel.

    `ordini` and `ordine` both become `ordin`, `fatture` and `fattura` become
    `fattur`. It is not morphology and does not pretend to be — it is the cheapest
    rule that collapses the plural/singular pairs the weights of §5.5 are about,
    and being deterministic matters more here than being linguistically right.
    Words of three characters or fewer are left alone.
    """
    if len(token) <= 3:
        return token
    return token[:-1] if token[-1] in "aeiou" else token


def edit_distance_at_most_one(
    left: str, right: str, *, allow_transposition: bool = True
) -> bool:
    """True when one insertion, deletion, substitution or adjacent transposition
    turns one into the other.

    **A defect in §5.5, and the reason the rule is not changed.** The section
    illustrates the approximate weight with *"mostrami le fatuere scadute"* matching
    *fatture*. Those two words are **two** edits apart under every standard metric,
    transposition included: `fatuere` -> `fatture` needs `u`->`t` and `e`->`u`, which
    is not a swap of adjacent characters. So the example does not satisfy the rule it
    illustrates.

    The rule stands and the example is wrong, not the other way round. Raising the
    bound to two would make `letture` match `fatture` — two substitutions, an
    unrelated word, and precisely the silent wrong match that no error surfaces and
    the margin cannot always catch.

    **Transposition is included**, and that is a widening the document did not ask
    for, so it is a parameter rather than a decision: transposing two adjacent keys
    is the most common typing error there is, and `tools/` measures phase A's
    resolution rate with and without it. A widening chosen on intuition is what §3.9
    forbids; one chosen on the corpus is what it asks for.

    Written as a bounded check rather than a full distance matrix because the rule
    only ever asks about one.
    """
    if left == right:
        return True
    length_left, length_right = len(left), len(right)
    if abs(length_left - length_right) > 1:
        return False

    if length_left == length_right:
        differing = [index for index, (a, b) in enumerate(zip(left, right)) if a != b]
        if len(differing) <= 1:
            return True
        if len(differing) == 2 and allow_transposition:
            first, second = differing
            return (
                second == first + 1
                and left[first] == right[second]
                and left[second] == right[first]
            )
        return False

    # One is shorter: it must be the other with one character removed.
    shorter, longer = (left, right) if length_left < length_right else (right, left)
    index = 0
    for position, character in enumerate(longer):
        if index < len(shorter) and shorter[index] == character:
            index += 1
        elif position != index:
            return False
    return True


@dataclass(frozen=True)
class IndexedTerm:
    """One term of the dictionary, ready to be matched."""

    tokens: tuple[str, ...]
    ref: str
    level: str
    entry_type: str
    #: The term as written, for the interpretation shown to the user.
    surface: str

    @property
    def base_tokens(self) -> tuple[str, ...]:
        return tuple(base_form(token) for token in self.tokens)


@dataclass(frozen=True)
class Match:
    """One term matched inside a request."""

    ref: str
    score: float
    term: IndexedTerm
    #: Position of the match in the request's token list, for provenance.
    start: int
    length: int

    @property
    def level(self) -> str:
        return self.term.level


@dataclass
class TermIndex:
    """Term -> references, across levels and languages."""

    terms: list[IndexedTerm] = field(default_factory=list)

    def add(self, surface: str, ref: str, *, level: str, entry_type: str) -> None:
        tokens = tuple(normalise(surface))
        if not tokens:
            return
        self.terms.append(IndexedTerm(
            tokens=tokens, ref=ref, level=level, entry_type=entry_type,
            surface=surface,
        ))

    def add_entry(self, entry: dict, *, ref: str | None = None) -> None:
        """Index every term of a dictionary entry."""
        target = ref or entry.get("ref") or entry.get("name") or ""
        for term in entry.get("terms") or []:
            self.add(term, target, level=entry["level"], entry_type=entry["type"])

    def match(self, request: str, *, entry_types: frozenset[str] | None = None) -> list[Match]:
        """Every term found in `request`, best score per (ref, span) first.

        `entry_types` restricts the search — phase A looks only at the T1 terms of
        entities, because determining the entity is the whole of its job (`06`
        §5.5) and matching an attribute term there would answer a question nobody
        asked.
        """
        tokens = normalise(request)
        if not tokens:
            return []

        exact_hits = self._exact_token_set(tokens, entry_types)
        matches: list[Match] = []
        for term in self.terms:
            if entry_types is not None and term.entry_type not in entry_types:
                continue
            best = self._best_span(term, tokens, exact_hits)
            if best is not None:
                matches.append(best)

        # Longest match first, then score, then level precedence: "ordini di
        # vendita" must win over "ordini" when both are present, because the more
        # specific term is the one the user actually said.
        matches.sort(key=lambda m: (-m.length, -m.score, LEVEL_PRECEDENCE.get(m.level, 9)))
        return matches

    def _exact_token_set(
        self, tokens: list[str], entry_types: frozenset[str] | None
    ) -> frozenset[str]:
        """Tokens of the request that match some indexed term exactly.

        Used to enforce the guard of §5.5: approximate matching is never applied to
        a token that already matches something exactly, or a correctly spelled word
        would be "corrected" into a different reference.
        """
        indexed: set[str] = set()
        for term in self.terms:
            if entry_types is not None and term.entry_type not in entry_types:
                continue
            indexed.update(term.tokens)
        return frozenset(token for token in tokens if token in indexed)

    def _best_span(
        self, term: IndexedTerm, tokens: list[str], exact_hits: frozenset[str]
    ) -> Match | None:
        width = len(term.tokens)
        best: Match | None = None
        for start in range(0, len(tokens) - width + 1):
            window = tokens[start:start + width]
            score = self._score(term, window, exact_hits)
            if score is None:
                continue
            if best is None or score > best.score:
                best = Match(ref=term.ref, score=score, term=term,
                             start=start, length=width)
        return best

    def _score(
        self, term: IndexedTerm, window: list[str], exact_hits: frozenset[str]
    ) -> float | None:
        """Score of one candidate span, or None when it does not match at all.

        The score of a multi-token term is the **weakest** of its tokens: a term
        matches as well as its worst part, because a phrase half-guessed is a phrase
        guessed.
        """
        weakest = WEIGHT_EXACT
        for expected, expected_base, actual in zip(term.tokens, term.base_tokens, window):
            if actual == expected:
                weight = WEIGHT_EXACT
            elif base_form(actual) == expected_base:
                weight = WEIGHT_BASE_FORM
            elif (
                actual not in exact_hits
                and len(actual) >= MIN_LENGTH_FOR_APPROXIMATE
                and len(expected) >= MIN_LENGTH_FOR_APPROXIMATE
                and edit_distance_at_most_one(actual, expected)
            ):
                weight = WEIGHT_APPROXIMATE
            else:
                return None
            weakest = min(weakest, weight)
        return weakest
