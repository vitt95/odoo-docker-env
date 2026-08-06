"""The dictionary itself: levels, precedence, and the resolved view (D28, D29).

**Pure zone.**

## Two different meanings of "precedence"

`06` §2.2 fixes **L2 › L1 › L0**, and the rule works differently for the two
classes of D29 — which is not a subtlety, it is the reason the split exists:

* **vocabulary** (T1, T2, T6, T7) **merges** across levels. Adding a synonym at L2
  widens what the system recognises and changes no existing result, so there is
  nothing for a higher level to override. Replacing instead of merging would make a
  customer's new synonym *delete* the base package's synonyms, which is the
  opposite of what §2.2 promises;
* **definition** (T3, T4, T5) is **replaced** by the highest level present. If the
  customer defines `recent_orders` as sixty days, the base package's thirty days is
  gone, not averaged. This is where "the customer has the last word" is literal.

Getting this backwards in either direction produces the failure mode `06` §2.2
calls the most serious the system can have: a sudden, unexplained degradation after
an update.

## L3 is not a level

It is a queue. Entries in it are never active and never resolved — `resolve()`
ignores them entirely, and `validate_entry` refuses `level: "L3"` outright. An
automatically learned entry that applied itself would be self-reinforcing: users
who get a plausible result do not correct it, the mistake becomes the norm, and no
indicator points at it (D28).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import entries as entries_module
from .index import TermIndex

#: Types whose entries merge across levels, and types whose entries are replaced.
MERGING_TYPES = entries_module.VOCABULARY_TYPES
REPLACING_TYPES = entries_module.DEFINITION_TYPES


@dataclass
class Dictionary:
    """A validated, level-resolved dictionary.

    Built from a flat list of entries — which is how L0 arrives from introspection,
    L1 from a package and L2 from the customer's records — because keeping them flat
    means the precedence rule is applied in exactly one place.
    """

    #: The entries as given, in order. Kept so that a report can name the level an
    #: entry came from.
    raw: list[dict] = field(default_factory=list)
    #: Structural problems found while building. Never raised: a dictionary with a
    #: bad entry is still usable without it, and refusing to build would take the
    #: whole catalogue down for one malformed synonym. The problems are reported.
    problems: list[entries_module.EntryProblem] = field(default_factory=list)
    #: Resolved entries by (type, key), where key is the ref or the name.
    resolved: dict[tuple[str, str], dict] = field(default_factory=dict)

    @classmethod
    def build(cls, entries: list[dict]) -> "Dictionary":
        dictionary = cls()
        for entry in entries:
            problems = entries_module.validate_entry(entry)
            if problems:
                dictionary.problems.extend(problems)
                continue
            dictionary.raw.append(entry)
        dictionary._resolve()
        return dictionary

    # -- precedence ---------------------------------------------------------

    def _resolve(self) -> None:
        by_key: dict[tuple[str, str], list[dict]] = {}
        for entry in self.raw:
            if entry["level"] == "L3":
                continue  # a queue, not a level
            key = (entry["type"], self._key_of(entry))
            by_key.setdefault(key, []).append(entry)

        for key, candidates in by_key.items():
            entry_type = key[0]
            ordered = sorted(
                candidates,
                key=lambda e: entries_module.ACTIVE_LEVELS_BY_PRECEDENCE.index(e["level"]),
            )
            if entry_type in REPLACING_TYPES:
                # The highest level wins whole. A definition is one statement about
                # meaning, and two statements merged would be a third nobody made.
                self.resolved[key] = dict(ordered[0])
            else:
                self.resolved[key] = self._merge(ordered)

    @staticmethod
    def _key_of(entry: dict) -> str:
        return str(entry.get("ref") or entry.get("name") or entry.get("ambiguity") or "")

    @staticmethod
    def _merge(ordered: list[dict]) -> dict:
        """Union of terms, most authoritative level first.

        The order of `terms` is not decoration: it is the order the interpretation
        prefers when showing the reference back to the user, so the customer's word
        for a thing comes before the vendor's.
        """
        merged = dict(ordered[0])
        seen = {term.casefold() for term in merged.get("terms", [])}
        for entry in ordered[1:]:
            for term in entry.get("terms", []):
                if term.casefold() not in seen:
                    merged.setdefault("terms", []).append(term)
                    seen.add(term.casefold())
        # The merged entry reports the highest level that contributed, because that
        # is what governs who may edit it (D38).
        merged["level"] = ordered[0]["level"]
        merged["contributing_levels"] = sorted({entry["level"] for entry in ordered})

        # **Il nome con cui si parla all'utente, che non e' la prima parola con cui lo
        # si riconosce.** Sono due cose diverse e fino al 5 agosto 2026 erano una sola.
        #
        # Quel giorno sono entrate al livello L1 le forme verbali delle date —
        # `creati`, `chiusi`, `assegnati` — perche' una persona dice *«i lead creati
        # questo mese»* e non *«con data creazione»*. Servono a **capire**. Ma
        # prendendosi il primo posto fra i termini si sono prese anche il posto di
        # cio' che si mostra, e la domanda di chiarimento ha iniziato a proporre
        # *«creazione»* e *«chiusura»* al posto di `Data creazione` e `Data chiusura`.
        #
        # La regola: si mostra il nome che **qualcuno ha scelto per questa cosa** —
        # quello del cliente (L2) se c'e', altrimenti quello della piattaforma (L0),
        # che per giunta Odoo traduce gia' da solo. L1 e' un livello di dominio: porta
        # sinonimi e flessioni, cioe' parole per riconoscere, e non nomina niente.
        for livello in ("L2", "L0"):
            per_livello = [entry for entry in ordered if entry["level"] == livello]
            if per_livello and per_livello[0].get("terms"):
                merged["display"] = per_livello[0]["terms"][0]
                break
        else:
            # Solo L1: nessuno ha dato un nome a questa cosa, e la prima parola con
            # cui la si riconosce e' meglio di un riferimento tecnico.
            merged["display"] = (merged.get("terms") or [""])[0]
        return merged

    # -- lookups ------------------------------------------------------------

    def entry(self, entry_type: str, key: str) -> dict | None:
        return self.resolved.get((entry_type, key))

    def of_type(self, entry_type: str) -> list[dict]:
        return [
            entry for (candidate_type, _), entry in sorted(self.resolved.items())
            if candidate_type == entry_type
        ]

    def terms_of(self, ref: str) -> list[str]:
        entry = self.entry("T1", ref)
        return list(entry.get("terms", [])) if entry else []

    def display_of(self, ref: str) -> str:
        """Il nome da mostrare a una persona, che non e' `terms_of(ref)[0]`.

        I termini servono a riconoscere cio' che l'utente scrive; questo serve a
        parlargli. Vedi `_merge`: il nome e' quello del cliente (L2) o quello della
        piattaforma (L0), mai un sinonimo di dominio (L1).
        """
        entry = self.entry("T1", ref)
        if not entry:
            return ""
        return entry.get("display") or (entry.get("terms") or [""])[0]

    def categories_of(self, entity_ref: str) -> list[dict]:
        return [
            entry for entry in self.of_type("T5")
            if entry.get("entity") == entity_ref
        ]

    def enum_values_of(self, ref: str) -> list[dict]:
        return [
            entry for entry in self.of_type("T2")
            if entry.get("ref") == ref
        ]

    def resolver(self, name: str) -> dict | None:
        return self.entry("T3", name)

    # -- index --------------------------------------------------------------

    def term_index(self, *, entry_types: frozenset[str] | None = None) -> TermIndex:
        """A term index over the resolved entries.

        Built from the resolved view, not from the raw list: an index over the raw
        entries would let a superseded definition's terms keep matching, which is
        the drift §2.2 forbids.
        """
        index = TermIndex()
        for (entry_type, key), entry in sorted(self.resolved.items()):
            if entry_types is not None and entry_type not in entry_types:
                continue
            index.add_entry(entry, ref=key)
        return index
