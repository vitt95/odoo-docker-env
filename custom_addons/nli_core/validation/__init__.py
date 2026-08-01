"""Validation, in five levels (`ai/03-specifica-dsl.md` §12).

The split across two files is the boundary itself, not a file-size decision:

* `structural.py` — levels 1 and 2, structure and vocabulary. **Pure zone**: no
  ORM, no permissions, no clock. Part 2;
* `coherence.py` — the half of levels 4 and 5 that needs only the artefact: tree
  depth, grouping count, conflicting operations, cost ceilings. **Pure zone**.
  Part 2;
* `contextual.py` — level 3, and the half of levels 4 and 5 that needs the
  attribute's type: catalogue, permissions, predicate against type. Needs the
  platform and the resolved instant. Part 4.

D14 governs both: an unknown symbol is rejected, never ignored. Ignoring one
produces a result less filtered than requested — the form of R1 nobody detects.
"""
