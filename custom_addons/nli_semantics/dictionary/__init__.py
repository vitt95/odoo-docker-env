"""The Semantic Dictionary: levels, entry types, term index (`ai/06-modello-semantico.md`).

**Pure zone.** Everything here is a function of its arguments. The dictionary's
*content* comes from three places — L0 by introspection, L1 from a package, L2 from
the customer's records — and all three arrive as flat lists of entries, so the
precedence rule of §2.2 is applied in exactly one place (`store.py`).

| Module | Contenuto |
|---|---|
| `entries.py` | the seven entry types, the vocabulary/definition split (D29, D30) |
| `conditions.py` | the typed condition language of T5 and T4 — the three constraints of D87 fall out of it |
| `store.py` | levels, precedence L2 › L1 › L0, L3 as a queue (D28) |
| `index.py` | one term index across languages (D37), and the matching of phase A |
"""
