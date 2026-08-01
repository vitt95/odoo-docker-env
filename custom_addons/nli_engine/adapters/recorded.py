"""An adapter that answers from a recording, for tests and for the corpus.

Not a mock in the usual sense: it opens no socket and needs no model, so the whole of
the Interpreter — prompt, parsing, validation, the single repair attempt of D15 — is
testable in a suite that runs in milliseconds and cannot fail because a provider is
down.

It also serves the regression corpus of `07`: replaying recorded answers is how a
change to the *system* is measured without the model's variance getting mixed in.
That separation is D48's whole subject — without it every fluctuation becomes a
result and the regression gate fires at random.
"""

from __future__ import annotations

from .base import Adapter, AdapterError, Capabilities, Reply, Request

PROTOCOL = "recorded"


class RecordedAdapter(Adapter):
    protocol = PROTOCOL

    def __init__(self, replies, *, capabilities: Capabilities | None = None):
        #: Either a list consumed in order, or a callable of the request.
        self.replies = list(replies) if isinstance(replies, (list, tuple)) else replies
        self.requests: list[Request] = []
        self._capabilities = capabilities or Capabilities(
            context_window=32_000, constrained_generation=True)

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def complete(self, request: Request, *, schema: dict | None = None) -> Reply:
        self.requests.append(request)
        if callable(self.replies):
            return Reply(text=self.replies(request))
        if not self.replies:
            raise AdapterError("the recording is exhausted")
        return Reply(text=self.replies.pop(0))
