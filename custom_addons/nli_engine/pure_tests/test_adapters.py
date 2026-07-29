"""What the OpenAI-compatible adapter puts on the wire, and what it leaves off.

The payload is where three declarations of D78 and D98 become bytes. Each of them is
a claim that can be false in a way nothing else would catch: a profile can declare
constrained generation against a provider that ignores it, or a reasoning effort
against a provider that refuses the key. So each declaration has a test that shows it
both appear and stay away.
"""

from __future__ import annotations

import json
import unittest

from ..adapters import openai_compatible as protocol_module
from ..adapters.base import Capabilities, Request

SCHEMA = {"type": "object", "properties": {"outcome": {"type": "string"}}}
REPLY = {"choices": [{"message": {"content": "{}"}}], "usage": {}}


class Spia:
    """Records the payload instead of opening a socket.

    Substituted for `post_json` in the module, which is where the adapter binds it:
    the test exercises the real `complete()` rather than a re-implementation of it,
    and a change to the payload that skipped this file would fail here.
    """

    def __init__(self):
        self.payload = None

    def __call__(self, url, payload, *, secret_variable=None, timeout=None):
        self.payload = payload
        return REPLY, 1


class TestPayload(unittest.TestCase):
    def setUp(self):
        self.spia = Spia()
        self.originale = protocol_module.post_json
        protocol_module.post_json = self.spia
        self.addCleanup(setattr, protocol_module, "post_json", self.originale)

    def _adapter(self, **capacita):
        base = {"context_window": 32000, "constrained_generation": False}
        base.update(capacita)
        return protocol_module.OpenAICompatibleAdapter(
            endpoint="http://localhost:11434/v1", model="m",
            capabilities=Capabilities(**base))

    def _chiama(self, adapter, schema=SCHEMA):
        adapter.complete(Request(utterance="x", catalogue={}), schema=schema)
        return self.spia.payload

    # --- D78: constrained generation -------------------------------------
    def test_the_schema_travels_when_the_profile_declares_it(self):
        payload = self._chiama(self._adapter(constrained_generation=True))
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertEqual(payload["response_format"]["json_schema"]["schema"], SCHEMA)

    def test_a_degraded_profile_asks_for_json_and_does_not_pretend_more(self):
        """Measured on ollama 0.32: the constraint is honoured, and the answer to a
        question about the weather came back as the only value the schema admitted.
        A profile that cannot do this is admitted and marked degraded (§5.1 of `10`),
        never described as if it could."""
        payload = self._chiama(self._adapter(constrained_generation=False))
        self.assertEqual(payload["response_format"], {"type": "json_object"})

    # --- D98: reasoning effort -------------------------------------------
    def test_the_reasoning_key_stays_off_the_wire_when_unnamed(self):
        """A provider without a reasoning mode answers 400 to a key it does not know.
        The declaration is therefore an opt-in, not a default."""
        self.assertNotIn("reasoning_effort", self._chiama(self._adapter()))

    def test_the_reasoning_effort_travels_when_the_profile_names_it(self):
        """qwen3.5:9b, catalogue of `sale.order`, same prompt in both runs: reasoning
        left on burnt 2397 tokens against a 4096 window and returned **empty
        content**; at `none`, 179 tokens and a valid envelope in 20,6 s."""
        payload = self._chiama(self._adapter(reasoning_effort="none"))
        self.assertEqual(payload["reasoning_effort"], "none")

    def test_the_temperature_is_zero_and_the_stream_is_off(self):
        """Not tuning: the model is the only non-deterministic point in the chain
        (§1.2 of `03`), and sampling would widen it for no benefit."""
        payload = self._chiama(self._adapter())
        self.assertEqual(payload["temperature"], 0.0)
        self.assertIs(payload["stream"], False)

    def test_the_payload_carries_the_utterance_and_nothing_technical(self):
        adapter = self._adapter()
        adapter.complete(Request(utterance="gli ordini di questo mese", catalogue={}))
        inviato = json.dumps(self.spia.payload, ensure_ascii=False)
        self.assertIn("gli ordini di questo mese", inviato)
        self.assertNotIn("sale.order", inviato)


if __name__ == "__main__":
    unittest.main()
