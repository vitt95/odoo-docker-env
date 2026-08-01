"""The OpenAI-compatible chat protocol — one adapter, local or remote (D75).

Chosen as the first protocol because it is the one both ends of the range speak:
Ollama exposes it at `/v1`, and so do the hosted providers. That is D8's answer made
concrete — *all delivery modes supported, the choice becomes configuration* — with a
single code path rather than one per vendor.

**The transport is not the contract** (§18.1, last row). The provider's structured
output feature is used when the profile declares it (D78), and the envelope is
validated by the five levels regardless. Exploiting constrained generation is
legitimate and recommended; making the contract's validity depend on it is not, and
the difference is a `schema` argument that may be ignored.
"""

from __future__ import annotations

from .base import Adapter, AdapterError, Capabilities, Reply, Request
from .http import post_json

PROTOCOL = "openai_compatible"


class OpenAICompatibleAdapter(Adapter):
    protocol = PROTOCOL

    def __init__(self, *, endpoint: str, model: str, capabilities: Capabilities,
                 secret_variable: str | None = None, temperature: float = 0.0,
                 timeout: int = 60):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._capabilities = capabilities
        self.secret_variable = secret_variable
        # Zero, and it is not a tuning choice. §1.2 of `03`: the model is the only
        # non-deterministic point in the chain, and everything else exists to keep
        # that point small. Sampling would widen it for no benefit — there is no
        # creativity wanted in choosing a predicate from a closed set.
        self.temperature = temperature
        self.timeout = timeout

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def complete(self, request: Request, *, schema: dict | None = None) -> Reply:
        payload = {
            "model": self.model,
            "messages": self._messages(request),
            "temperature": self.temperature,
            "stream": False,
        }
        if self._capabilities.reasoning_effort:
            # D98. A standard field of the protocol, sent only when the profile names
            # a value: the closed set of D75 is not widened, and a provider without a
            # reasoning mode never sees a key it would refuse.
            payload["reasoning_effort"] = self._capabilities.reasoning_effort
        if schema and self._capabilities.constrained_generation:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "aida_envelope", "strict": True,
                                "schema": schema},
            }
        elif schema:
            # The profile declared it cannot constrain generation (D78). Asking for
            # JSON at least is not the same guarantee and is not pretended to be:
            # levels 1-2 will do the work, and their failure rate is the indicator
            # §12.3 says to watch.
            payload["response_format"] = {"type": "json_object"}

        reply, duration = post_json(
            f"{self.endpoint}/chat/completions", payload,
            secret_variable=self.secret_variable, timeout=self.timeout,
        )
        return Reply(
            text=self._content(reply),
            prompt_tokens=(reply.get("usage") or {}).get("prompt_tokens", 0),
            completion_tokens=(reply.get("usage") or {}).get("completion_tokens", 0),
            duration_ms=duration,
            model=reply.get("model", self.model),
        )

    def _messages(self, request: Request) -> list[dict]:
        from ..prompt import system_message, user_message  # local: avoids a cycle

        if self._capabilities.system_role:
            return [
                {"role": "system", "content": system_message(request)},
                {"role": "user", "content": user_message(request)},
            ]
        return [{"role": "user",
                 "content": system_message(request) + "\n\n" + user_message(request)}]

    @staticmethod
    def _content(reply: dict) -> str:
        try:
            return reply["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as error:
            raise AdapterError("provider answered without a message") from error
