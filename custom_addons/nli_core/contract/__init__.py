"""The contract: the Envelope, the Interrogation State, the canonical form.

**Pure zone** (`tools/arch/spec.py`). Nothing here imports `odoo`, and nothing
here reads the clock. Two reasons, both structural:

* `ai/04-architettura.md` §6.5 — the Validator, the Applicator and the
  Interpreter would operate identically on another platform. Keeping that true
  is what confines the Odoo upgrade surface to two components instead of nine;
* the canonical form (`03` §14.3) and the equivalence registry (D43) are the
  measurement instrument of `07`. An instrument whose output depends on when it
  ran cannot detect a regression.

Filled in part 2, together with the JSON schema of D11.
"""
