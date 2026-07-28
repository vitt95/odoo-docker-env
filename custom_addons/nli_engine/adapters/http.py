"""Outbound HTTP, with the two controls that D77 and D76 make structural.

**This is the only module in the product that opens a socket.** Everything about
where the traffic may go and what credential it carries is decided here, from the
**environment**, and neither can be widened from the administration panel.

## D77 — the allowed hosts live in the environment

D77 is marked *blocking*, and its argument is the sharpest in the registry:

> The panel creates a channel that did not exist before: a compromised administrator
> would send every utterance and catalogue elsewhere, **with normal accuracy and
> normal latency**. No metric in `07` would detect it.

So the endpoint of a profile is administered, and the set of hosts it may point at is
not: it comes from `NLI_ALLOWED_HOSTS`, and a profile pointing anywhere else is
refused before a connection is attempted. Someone with database access cannot widen
it; someone with shell access already has everything.

## D76 — the secret is not in the database

The original rule said secrets are never stored. D76 corrected it to the intent: a
**database dump must not yield credentials**. So the profile stores the *name* of an
environment variable, never its value. A dump contains `NLI_OPENAI_KEY`, which is
worth nothing.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .base import AdapterError, HostNotAllowed, SecretUnavailable

#: Environment variable holding the comma-separated list of admitted hosts,
#: each as `host` or `host:port`.
ALLOWED_HOSTS_VARIABLE = "NLI_ALLOWED_HOSTS"

#: Seconds before an unanswered request is abandoned. A model that does not answer is
#: an availability problem; one that answers in four minutes is the same problem with
#: a queue behind it (D20c).
DEFAULT_TIMEOUT = 60


def allowed_hosts() -> frozenset[str]:
    """The hosts this installation may reach, from the environment (D77)."""
    raw = os.environ.get(ALLOWED_HOSTS_VARIABLE, "")
    return frozenset(
        entry.strip().casefold() for entry in raw.split(",") if entry.strip()
    )


def check_endpoint(url: str) -> str:
    """Refuse an endpoint the environment does not admit. Returns the host checked.

    Refusal comes **before** the connection, not after a failure: a request that
    leaves and is then regretted has already left.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HostNotAllowed(f"{url!r}: only http and https are admitted")
    host = (parsed.netloc or "").casefold()
    admitted = allowed_hosts()
    if not admitted:
        raise HostNotAllowed(
            f"{ALLOWED_HOSTS_VARIABLE} is not set: no outbound host is admitted. "
            "The list lives in the environment, not in the panel (D77)"
        )
    if host not in admitted:
        raise HostNotAllowed(
            f"{host!r} is not in {ALLOWED_HOSTS_VARIABLE}. Admitted: "
            f"{sorted(admitted)}. Widening it is a deployment change, deliberately "
            "not an administration one (D77)"
        )
    return host


def secret_from_environment(variable: str | None) -> str | None:
    """The credential, read from the environment at call time (D76).

    Returns `None` when the profile declares no variable — a local model needs no
    credential, and requiring one would make the safest configuration the most
    awkward.
    """
    if not variable:
        return None
    value = os.environ.get(variable)
    if not value:
        raise SecretUnavailable(
            f"the profile names {variable!r} and the environment does not define it. "
            "The value is deliberately not in the database: a dump must not yield "
            "credentials (D76)"
        )
    return value


def post_json(url: str, payload: dict, *, secret_variable: str | None = None,
              timeout: int = DEFAULT_TIMEOUT) -> tuple[dict, int]:
    """POST a JSON body to an admitted endpoint. Returns the reply and the duration.

    `urllib` rather than a client library, and the reason is not minimalism: the
    boundary check lists the network libraries `nli_engine` alone may import, and
    every one added is a line in that list. One stdlib module keeps the surface at
    one.
    """
    check_endpoint(url)
    secret = secret_from_environment(secret_variable)

    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        # The body may carry the provider's explanation; the credential never appears
        # in it, and D60 forbids the utterance from reaching the log — so the message
        # carries the status and nothing of the request.
        raise AdapterError(f"provider answered {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise AdapterError(f"provider unreachable: {error}") from error

    duration = int((time.monotonic() - started) * 1000)
    try:
        return json.loads(raw), duration
    except json.JSONDecodeError as error:
        raise AdapterError("provider answered something that is not JSON") from error
