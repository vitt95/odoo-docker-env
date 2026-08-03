"""The three-phase catalogue strategy (D32, D33, `06` §5.5-5.8).

**Pure zone.**

Phase A determines the entity **without calling the model**, by matching the request
against the T1 terms of the entities. Phase B hands the model a small catalogue —
entity names only — when A does not decide. Phase C, the entity now known, hands it
**every** exposed attribute of that entity.

## What D32 buys, stated precisely

> **In phase C there is no selection.** All exposed attributes of the entity are
> present, so coverage on attributes is **exact by construction**, and the only
> remaining point of loss is determining the entity.

That is what turns RC3 — an invisible ceiling on accuracy that no model improvement
can raise — into a small, isolated, separately measurable problem. It is also the
architectural pay-off of the contract's single-entity restriction: with more than one
entity per interrogation this decomposition is impossible, and the selection would
need a retrieval component, i.e. a second probabilistic component nobody measures.

## Why phase A needs a threshold **and** a margin (D33)

A strong match is not enough. If *"ordine"* matches both *ordini di vendita* and
*ordini di acquisto* well, taking the best by a hair is **guessing in silence** — the
shape of R1 that no error surfaces. The margin turns that case into a clarification,
which costs the user a moment and the system an honest question.

The two values are **declared initial parameters**, calibrated on the corpus, not
constants of the design: `tools/` reports phase A's resolution rate and its wrong
determinations at candidate values, which is the only defensible way to choose them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..dictionary.index import Match, TermIndex, WEIGHT_EXACT

#: Minimum score for a candidate to be considered at all.
#:
#: **0.70, and the value is a finding.** §5.5 admits three tiers — exact 1.00, base
#: form 0.90, approximate 0.70 — and then asks for a threshold. Set anywhere above
#: 0.70 the approximate tier can never decide anything, which makes the tier that
#: §5.5 illustrates with a typo dead code. So either the threshold is at the weakest
#: admitted tier, or the tier is decoration.
#:
#: It follows that **the threshold is not the protection — the margin is.** The
#: threshold's real job is to be raisable: at 0.90 the fast path stops resolving
#: typos, which is a legitimate configuration for an installation that would rather
#: ask than guess. Which value is right is measured on the corpus, not argued.
DEFAULT_THRESHOLD = 0.70

#: Minimum distance between the best and the second candidate. Below it the answer
#: is a clarification, never the best guess. This is what protects against R1
#: (D33).
DEFAULT_MARGIN = 0.15

#: Phase A looks only at the naming entries of entities. Matching an attribute term
#: here would answer a question nobody asked — the job is the entity (§5.5).
ENTITY_TERM_TYPES = frozenset({"T1"})

#: Outcomes of phase A.
RESOLVED = "resolved"
NO_CANDIDATE = "no_candidate"
BELOW_THRESHOLD = "below_threshold"
BELOW_MARGIN = "below_margin"


@dataclass(frozen=True)
class Candidate:
    ref: str
    score: float
    term: str
    level: str


@dataclass(frozen=True)
class PhaseA:
    """The outcome of the deterministic fast path."""

    outcome: str
    entity: str | None
    candidates: tuple[Candidate, ...] = ()
    threshold: float = DEFAULT_THRESHOLD
    margin: float = DEFAULT_MARGIN

    @property
    def resolved(self) -> bool:
        return self.outcome == RESOLVED

    @property
    def needs_clarification(self) -> bool:
        """Two candidates too close to separate — an honest question, not a guess.

        Distinguished from `BELOW_THRESHOLD`, where nothing matched well enough and
        the right next step is the model (phase B), not a question. Collapsing the two
        would either ask the user about something the model could have handled, or
        hand the model a case where the ambiguity is already known.
        """
        return self.outcome == BELOW_MARGIN

    def explain(self) -> str:
        if self.outcome == RESOLVED:
            best = self.candidates[0]
            return (f"'{best.term}' -> {best.ref} (score {best.score:.2f}, "
                    f"level {best.level})")
        if self.outcome == NO_CANDIDATE:
            return "no entity term matched the request"
        if self.outcome == BELOW_THRESHOLD:
            best = self.candidates[0]
            return (f"best candidate {best.ref} at {best.score:.2f}, below the "
                    f"threshold of {self.threshold:.2f}")
        best, second = self.candidates[0], self.candidates[1]
        return (f"{best.ref} at {best.score:.2f} and {second.ref} at "
                f"{second.score:.2f}: distance {best.score - second.score:.2f} below "
                f"the margin of {self.margin:.2f}")


def _is_exact(match) -> bool:
    """Se il termine sta nella frase **come e' scritto**, non per morfologia.

    E' la distinzione che rende usabile il guardiano di V-D93-1 senza spegnere i
    riconoscimenti giusti — vedi `determine_entity`.
    """
    return match.score >= WEIGHT_EXACT


def determine_entity(
    request: str,
    index: TermIndex,
    *,
    entity_refs: frozenset[str],
    threshold: float = DEFAULT_THRESHOLD,
    margin: float = DEFAULT_MARGIN,
) -> PhaseA:
    """Phase A — determine the entity deterministically, or decline to.

    `entity_refs` is the set of references that *are* entities: the index also holds
    attribute and category terms, and phase A must not resolve an entity from the
    name of one of its fields.
    """
    matches = index.match(request, entry_types=ENTITY_TERM_TYPES)

    # D93, V-D93-1: a span is entity evidence only if no **non-entity** term — an
    # attribute or a T5 category — matches that same span at least as well. Same span,
    # never a sentence-wide best: "ordini di vendita raggruppati per cliente" names an
    # attribute and still names an entity, and a global comparison would lose it.
    #
    # **Vale solo contro le prove morfologiche, non contro quelle esatte.** Misurato
    # sul database vero il 3 agosto 2026: *«le fatture non pagate»* non risolveva
    # niente, perche' l'entita' `account_move` porta il termine *Fatture* — esatto,
    # 1.00 — e sullo stesso pezzo di frase lo portano anche `res_partner.invoice_ids`
    # e `sale_order.invoice_ids`, che si chiamano *Fatture* pure loro. Tre prove
    # esatte identiche, e il guardiano le buttava tutte.
    #
    # La differenza col caso che il guardiano esiste per prendere: li' l'entita'
    # arrivava dal livello morfologico — *clienti* contro l'attributo *cliente*, stessa
    # forma base — cioe' da un'evidenza **piu' debole** di quella che le si opponeva.
    # Qui l'entita' e' scritta nella frase come si scrive. Un pareggio fra due prove
    # esatte non e' una ragione per buttare quella dell'entita': se l'utente ha detto
    # *«fatture»* e le fatture sono un'entita', le fatture sono un candidato — e se ce
    # ne sono due, decide il margine, che e' li' apposta.
    #
    # This guard is not a refinement, it is what makes the base-form tier usable at
    # all, and the corpus is what showed it. Italian morphology collapses the
    # attribute *cliente* into the entity *clienti* — same base form — so a request
    # like *"fatt. cliente ... raggruppati per cliente"*, whose head noun the user
    # abbreviated, used to resolve to `clienti`: a different, plausible entity, with
    # no error anywhere. Measured on the corpus it was every one of the residual
    # wrong determinations.
    #
    # The alternative was to raise the threshold to 1.00, which removes the wrong
    # determinations by removing the whole base-form tier — and with it the resolution
    # of *"mostrami la fattura"*, where nothing is being guessed: singular and plural
    # of one word are one word. Discarding ambiguous **evidence** is better than
    # discarding a whole tier of correct matches.
    best_non_entity: dict[tuple[int, int], float] = {}
    for match in matches:
        if match.ref in entity_refs:
            continue
        span = (match.start, match.length)
        best_non_entity[span] = max(best_non_entity.get(span, 0.0), match.score)

    best_by_ref: dict[str, Match] = {}
    for match in matches:
        if match.ref not in entity_refs:
            continue
        span = (match.start, match.length)
        if best_non_entity.get(span, 0.0) >= match.score and not _is_exact(match):
            continue
        current = best_by_ref.get(match.ref)
        if current is None or (match.length, match.score) > (current.length, current.score):
            best_by_ref[match.ref] = match

    if not best_by_ref:
        return PhaseA(NO_CANDIDATE, None, (), threshold, margin)

    ranked = sorted(
        best_by_ref.values(),
        key=lambda m: (-m.length, -m.score, m.ref),
    )
    candidates = tuple(
        Candidate(ref=m.ref, score=m.score, term=m.term.surface, level=m.level)
        for m in ranked
    )

    best = candidates[0]
    if best.score < threshold:
        return PhaseA(BELOW_THRESHOLD, None, candidates, threshold, margin)

    # A longer match wins outright: "ordini di vendita" against "ordini" is not a
    # close call between two readings, it is the specific term the user said. The
    # margin exists for candidates matched by the *same* span.
    same_span = [c for c in candidates if len(c.term.split()) == len(best.term.split())]
    if len(same_span) > 1 and (best.score - same_span[1].score) < margin:
        return PhaseA(BELOW_MARGIN, None, candidates, threshold, margin)

    return PhaseA(RESOLVED, best.ref, candidates, threshold, margin)


@dataclass(frozen=True)
class PhaseBCatalogue:
    """The catalogue of phase B: entity names only, no attributes (§5.6).

    Small — hundreds of short entries — and the task is circumscribed: pick one item
    from a list. It is the class of task models are most reliable at, which is why
    the expensive path is *also* the narrow one.
    """

    entities: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def refs(self) -> frozenset[str]:
        return frozenset(ref for ref, _ in self.entities)

    def __len__(self) -> int:
        return len(self.entities)


def entity_catalogue(
    dictionary, *, entity_refs: frozenset[str]
) -> PhaseBCatalogue:
    """Build the phase B catalogue from the dictionary's T1 entries."""
    rows = []
    for ref in sorted(entity_refs):
        terms = tuple(dictionary.terms_of(ref))
        if terms:
            rows.append((ref, terms))
    return PhaseBCatalogue(entities=tuple(rows))
