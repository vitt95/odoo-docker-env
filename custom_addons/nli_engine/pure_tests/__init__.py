"""Tests of the engine that need neither a model nor a socket.

The Interpreter — prompt, parsing, validation, the single repair of D15 — is
exercised through the recorded adapter, so the suite runs in milliseconds and cannot
fail because a provider is down. What needs a real model is measured separately, by
`ai/corpus/misura_accuratezza.py`, and reported as a measurement rather than asserted
as a test: a threshold on a model's accuracy in a unit suite would turn a bad
afternoon at the provider into a red build.
"""
