"""The provider adapter — the boundary that makes V5 true (`04` §8).

**The only place in the product allowed to talk to a model.** Not a convention: the
import check of `tools/arch/` gives `nli_engine` sole permission to import provider
and network libraries, so the claim *"the traffic towards the provider contains only
the utterance and the catalogue"* (A6, V7) can be verified by reading one directory
instead of trusting a policy.

## What an adapter is not allowed to be

* it does **not** build the catalogue. `nli_engine` does not depend on
  `nli_semantics` (§6.3): it receives the catalogue, it does not know how it was made;
* it does **not** decide anything about the state. Whatever comes back is a **sealed
  envelope** and nothing else — V8: no artefact from the Interpreter that is not a
  validated envelope. That constraint is what keeps phase 6's document understanding
  from eroding the defence without anyone declaring it;
* it does **not** read secrets from the database (D76) or choose which hosts it may
  reach (D77). Both come from the environment, and the reasons are in `http.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class AdapterError(Exception):
    """The provider could not be reached, or answered something unusable."""


class HostNotAllowed(AdapterError):
    """The profile points at a host the environment does not admit (D77).

    A distinct exception because it is the only adapter failure that is a **security**
    event rather than an availability one: somebody configured an endpoint nobody
    authorised, and the right response is refusal plus a diagnostic entry, never a
    fallback to a different host.
    """


class SecretUnavailable(AdapterError):
    """The profile names an environment variable that does not exist (D76)."""


@dataclass(frozen=True)
class Capabilities:
    """What the profile declares it can do (**D78**).

    Without the declaration the diagnosis of §12.3 goes dark and a degraded profile
    looks like a system defect: constrained generation off means level 1-2 failures
    become normal, and nobody can tell that from a model that has got worse.

    `context_window` is not documentation either — **D79** derives the catalogue
    budget from it, and a model with a narrow window truncates the catalogue in
    silence: high coverage, low accuracy, and a cause outside every diagnostic table.
    """

    #: Tokens the model accepts. Drives the attribute budget (D79).
    context_window: int
    #: Whether the provider can constrain generation to a JSON schema (§12.3).
    constrained_generation: bool
    #: Whether the provider accepts a system message distinct from the user's.
    system_role: bool = True


@dataclass
class Request:
    """Everything sent to the provider, and nothing else.

    The field list **is** the enforcement of A6 and V7: there is no field for record
    content, so no code path can add it by accident. `utterance` is the user's
    sentence — which A6 does *not* protect (registry §5.2), a distinction that must
    stay visible exactly here, where the sentence leaves the installation.
    """

    utterance: str
    #: The catalogue, already built for this user by `nli_semantics`.
    catalogue: dict
    #: The current state, so the model can emit a refinement (§4.3).
    state: dict | None = None
    #: The structured error of the single repair attempt (D15), when this is one.
    repair: dict | None = None


@dataclass
class Reply:
    """What came back, plus what it cost."""

    #: The raw text. Parsed and validated by the Interpreter, never here.
    text: str
    #: Diagnostics only. D60 forbids utterances and catalogues in the logs; these are
    #: numbers.
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: int = 0
    model: str = ""


class Adapter:
    """The interface every provider implements.

    Deliberately two methods. An adapter that could do more would be an adapter the
    rest of the system starts depending on, and V5 — the provider is substitutable —
    lasts exactly as long as this interface stays small.
    """

    protocol: str = ""

    def capabilities(self) -> Capabilities:
        raise NotImplementedError

    def complete(self, request: Request, *, schema: dict | None = None) -> Reply:
        """Ask the model. `schema` is passed when the provider can constrain output.

        Using a provider's constrained generation is legitimate and recommended;
        making the contract's validity *depend* on it is not (§18.1). So the schema
        is a hint here, and the envelope is validated afterwards regardless.
        """
        raise NotImplementedError
