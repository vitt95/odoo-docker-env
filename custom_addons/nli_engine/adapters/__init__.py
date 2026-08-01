"""Provider adapters (`ai/10-adattatore-modelli.md`).

The single place in the product where an outbound call to a model may occur. That is
not a convention: the import check of `tools/arch/` makes this the only module allowed
to import provider and network libraries, which turns V5 (the provider is
substitutable) and V7 (the Interpreter cannot send data it does not hold) into
properties verifiable by reading one directory.

| Module | Contenuto |
|---|---|
| `base.py` | the interface, the declared capabilities (D78), the request shape that *is* the enforcement of A6 |
| `http.py` | the only socket in the product: allowed hosts from the environment (D77), secret from the environment (D76) |
| `openai_compatible.py` | the chat protocol both a local Ollama and a hosted provider speak (D75) |
| `recorded.py` | answers from a recording: the Interpreter tested without a model, and the regression corpus replayed without its variance (D48) |
| `synthetic.py` | a fake provider with a real latency, for the load bench of D27 only. Deliberately **not** in `PROTOCOLS`: it is not a profile and does not pass through D80 (D97) |
"""

from . import base, http, openai_compatible, recorded, synthetic

#: Protocols from a **closed set** (D75). Adding one is a change to the code, not a
#: field somebody types: an endpoint speaking an unknown protocol is an endpoint
#: nobody reviewed.
PROTOCOLS = {
    openai_compatible.PROTOCOL: openai_compatible.OpenAICompatibleAdapter,
    recorded.PROTOCOL: recorded.RecordedAdapter,
}
