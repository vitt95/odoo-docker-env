"""The Applicator: the only component that turns operations into a new state.

**Pure zone** (`tools/arch/spec.py`). The Applicator is a function of the state
it receives and the operations it is given — nothing else. D9 makes the model
emit operations while the system owns the state; that separation is worth
nothing if applying an operation can depend on today's date.

This is the invariant the fourth check of `04` §6.4 exists to protect, and the
one the 1 200 cases of `ai/corpus/corpus_fondativo.jsonl` are already a test
suite for (D82).

Filled in part 2.
"""
