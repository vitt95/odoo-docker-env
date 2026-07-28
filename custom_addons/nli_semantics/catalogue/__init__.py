"""Catalogue construction — the component `06` §1.1 calls the most critical.

**Pure zone.** The platform-facing inputs are passed in, never read here: the
attribute descriptors come from introspection, the readable references from the
access rules and the company context (D39, D40). A pure function cannot read an ACL,
and a catalogue that guessed at permissions would be worse than one that says it must
be told.

| Module | Contenuto |
|---|---|
| `exposure.py` | the nine exposure rules in order, the budget derived from the context window (D31, D79) |
| `phases.py` | the three-phase strategy A / B / C, threshold **and** margin (D32, D33) |
| `build.py` | assembly of phase C — permissions first, then selection, then budget (§5.9) |
| `coverage.py` | coverage, decomposed into entity and attributes (D34) |
"""
