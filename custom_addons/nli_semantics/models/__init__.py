"""Dictionary, catalogue and resolution (`ai/06-modello-semantico.md`).

Part 3. Four levels with precedence L2 > L1 > L0, L3 inactive (D28); seven
entry types, four of them implemented in phase 1 (D30); catalogue budget derived
from the model's context window, 60 as the ceiling (D79); permission fingerprint
computed and failing safe (D39); catalogue stored deduplicated (D41).
"""

from . import nli_dictionary_entry, nli_semantics
