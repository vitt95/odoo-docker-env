"""Machine-readable form of the architecture boundaries.

This module is the single source of truth for the four automatic checks
required by decision D24. It intentionally holds *no logic*: every rule below
transcribes a line of `ai/04-architettura.md` §6.2 and §6.3, so a reviewer can
diff the document against this file and see the whole delta.

Two properties are deliberate:

* the graph is declared **exactly**, not as an upper bound. Adding a
  dependency — even a platform one — is a one-line change here plus a review.
  That is the point of D24: boundaries move on purpose, never by accident;
* there is **no exemption mechanism**. A rule that can be waived inline is a
  convention again (§6.1). Waiving a rule requires a new decision in
  `ai/00-registro-decisioni.md`, numbered from D87.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Repository root: tools/arch/spec.py -> tools/arch -> tools -> root
REPO_ROOT = Path(__file__).resolve().parents[2]
ADDONS_DIR = REPO_ROOT / "custom_addons"

# The technical prefix of the product. `ai/00-registro-decisioni.md` D6 keeps it
# independent from the commercial name ("AIDA").
MODULE_PREFIX = "nli_"


@dataclass(frozen=True)
class ModuleSpec:
    """One `nli_*` Odoo module and the edges it is allowed to declare."""

    name: str
    responsibility: str
    #: Edges towards other `nli_*` modules — the graph of `04` §6.2.
    nli_depends: frozenset[str]
    #: Odoo platform modules. Exact, not a permissive allow-list.
    platform_depends: frozenset[str]
    #: Packages Odoo must import at load time (`__init__.py` chain).
    odoo_packages: frozenset[str] = field(default_factory=frozenset)


#: The dependency graph of `04` §6.2. Dependencies point towards the core;
#: never between peripheral modules.
MODULES: dict[str, ModuleSpec] = {
    "nli_core": ModuleSpec(
        name="nli_core",
        responsibility="contract, state, validation, application, execution",
        nli_depends=frozenset(),
        platform_depends=frozenset({"base"}),
        odoo_packages=frozenset({"models"}),
    ),
    # The peripheral modules declare no platform dependency of their own: they
    # reach `base` through the core. Declaring only what a module uses directly
    # is what makes a new platform dependency visible in review.
    "nli_semantics": ModuleSpec(
        name="nli_semantics",
        responsibility="dictionary, catalogue, resolution",
        nli_depends=frozenset({"nli_core"}),
        platform_depends=frozenset(),
        odoo_packages=frozenset({"models"}),
    ),
    "nli_engine": ModuleSpec(
        name="nli_engine",
        responsibility="interpreter, provider adapters",
        nli_depends=frozenset({"nli_core"}),
        platform_depends=frozenset(),
        odoo_packages=frozenset({"models"}),
    ),
    "nli_observability": ModuleSpec(
        name="nli_observability",
        responsibility="registry, metrics, corpus",
        nli_depends=frozenset({"nli_core"}),
        platform_depends=frozenset(),
        odoo_packages=frozenset({"models"}),
    ),
    "nli_web": ModuleSpec(
        name="nli_web",
        responsibility="chat channel, presentation",
        nli_depends=frozenset({"nli_semantics"}),
        platform_depends=frozenset({"web"}),
        odoo_packages=frozenset({"models"}),
    ),
}

#: Manifest keys every module must carry, with the expected value where the
#: value itself is normative.
REQUIRED_MANIFEST_KEYS: dict[str, object | None] = {
    "name": None,
    "summary": None,
    "version": None,
    "category": None,
    "author": None,
    "license": "LGPL-3",
    "depends": None,
    "installable": True,
    "application": False,
}

#: Odoo 18 series. A module declaring another series would install on the wrong
#: platform version without any error at import time.
MANIFEST_VERSION_PREFIX = "18.0."


# ---------------------------------------------------------------------------
# §6.3 — non-dependency rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NonDependency:
    """A forbidden edge, with the product constraint it protects."""

    source: str
    target: str
    protects: str
    rationale: str


#: Transcribed from `04` §6.3. Any `nli_*` edge absent from MODULES is already
#: a violation; these entries exist so the four that carry a named product
#: constraint are reported with their reason instead of a generic message.
NON_DEPENDENCIES: tuple[NonDependency, ...] = (
    NonDependency(
        source="nli_engine",
        target="nli_semantics",
        protects="separation between who knows the data and who talks to the model",
        rationale="the engine receives the catalogue, it does not build it",
    ),
    NonDependency(
        source="nli_core",
        target="nli_engine",
        protects="V5",
        rationale="the core ignores the existence of models — provider substitutability",
    ),
    NonDependency(
        source="nli_core",
        target="nli_web",
        protects="P5",
        rationale="the core ignores channels — channel independence",
    ),
    NonDependency(
        source="nli_core",
        target="nli_semantics",
        protects="D18",
        rationale="dependencies point towards the core, never away from it",
    ),
    NonDependency(
        source="nli_core",
        target="nli_observability",
        protects="D18",
        rationale="dependencies point towards the core, never away from it",
    ),
)

#: Provider and network libraries. Only `nli_engine` may import them: it is
#: what makes V5 (provider substitutability) and V7 (the interpreter cannot
#: send data it does not hold) verifiable instead of asserted.
PROVIDER_LIBRARIES: frozenset[str] = frozenset({
    # Model providers and inference clients
    "anthropic",
    "openai",
    "ollama",
    "mistralai",
    "cohere",
    "google",
    "litellm",
    "langchain",
    "langchain_core",
    "llama_cpp",
    "transformers",
    "huggingface_hub",
    "sentence_transformers",
    "tiktoken",
    "vllm",
    # Outbound network primitives. An adapter is a boundary only if the traffic
    # cannot leave from anywhere else.
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "ftplib",
    "smtplib",
    "telnetlib",
    "websocket",
    "websockets",
})

PROVIDER_LIBRARY_OWNER = "nli_engine"


# ---------------------------------------------------------------------------
# Syntactic check — V3 (no ORM bypass) and V2 (no privileged path)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ForbiddenPattern:
    """A source-level construct forbidden across every `nli_*` module."""

    label: str
    protects: str
    #: Dotted attribute or call names, matched on the last two segments.
    call_suffixes: frozenset[str] = field(default_factory=frozenset)
    #: Bare names (identifiers) whose mere appearance is a violation.
    names: frozenset[str] = field(default_factory=frozenset)
    #: Top-level modules that must not be imported.
    imports: frozenset[str] = field(default_factory=frozenset)
    #: Keyword arguments whose presence is a violation, as (kwarg, value_repr).
    keywords: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    #: Directory names under which the pattern does not apply.
    #:
    #: Used by exactly one rule, and the reason is in `04` §6.3 itself: the rule
    #: reads *"no privileged context **in the interrogation paths**"*. Applying it
    #: to `tests/` as well makes the property untestable — a test that checks what
    #: another user may see has to construct that user's environment — and a
    #: security property nobody can test is worse than one nobody can bypass.
    #: SQL access carries no such exclusion: a raw cursor in a test is a raw cursor.
    excluded_directories: frozenset[str] = field(default_factory=frozenset)


FORBIDDEN_PATTERNS: tuple[ForbiddenPattern, ...] = (
    ForbiddenPattern(
        label="direct PostgreSQL access",
        protects="V3",
        call_suffixes=frozenset({
            # Odoo exposes the cursor under several names; the rule is about the
            # call, not about which alias reached it.
            "cr.execute",
            "cr.executemany",
            "cr.copy_expert",
            "cr.copy_from",
            "_cr.execute",
            "_cr.executemany",
            "_cr.copy_expert",
            "cursor.execute",
            "cursor.executemany",
            "registry.cursor",
            "sql_db.db_connect",
            "sql_db.connect",
        }),
        imports=frozenset({"psycopg2", "psycopg", "asyncpg", "sqlalchemy"}),
    ),
    ForbiddenPattern(
        label="privilege elevation",
        protects="V2",
        call_suffixes=frozenset({"sudo", "with_user", "_with_user"}),
        names=frozenset({"SUPERUSER_ID"}),
        keywords=frozenset({("su", "True")}),
        excluded_directories=frozenset({"tests", "pure_tests"}),
    ),
)


# ---------------------------------------------------------------------------
# Architectural check — the pure zones
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PureZone:
    """A directory whose code must be a function of its arguments alone.

    `04` §6.5 states that the Validator, the Applicator and the Interpreter
    would operate identically on another platform. §6.4 turns that into the
    fourth check: the Applicator must not reach for the current date and time,
    because that is what makes the corpus reproducible (D82, D84).

    The zone therefore forbids two families at once: the platform (`odoo`) and
    every source of non-determinism.
    """

    path: str
    reason: str
    protects: str


#: Zones that may compute with dates but must never **read** the clock.
#:
#: `04` §4.6 draws a line the pure-zone rule alone cannot: the Resolver is *"the only
#: component aware of time"*, and being aware of time is not the same as reading it.
#: The reference instant is an **input** — that is precisely what lets the evaluation
#: corpus be re-run at a fixed instant without contrivance (§13.3) — so the module
#: needs `datetime` arithmetic while remaining a function of its arguments.
#:
#: A deterministic zone therefore forbids the same **calls** as a pure zone (`now`,
#: `today`, `utcnow`, random, environment) and the platform, but admits the date
#: libraries. Without this distinction the choice would be between a Resolver that
#: cannot do arithmetic and a Resolver nobody checks.
DETERMINISTIC_ZONES: tuple[PureZone, ...] = (
    PureZone(
        path="nli_core/resolution",
        reason="the Resolver receives the instant and never reads it; the corpus is "
               "re-run at a fixed instant, and that only works if no line here calls "
               "the clock (04 §4.6, D82)",
        protects="D82, C5",
    ),
    # The test suites are deterministic zones rather than pure ones for a reason the
    # Resolver made obvious: a test that asserts what `current_month` resolves to has
    # to **build** an instant. It must not be able to **read** one — a test that calls
    # `date.today()` passes today and fails in eleven months, and finding out why is
    # the worst afternoon in the calendar.
    PureZone(
        path="nli_core/pure_tests",
        reason="tests may construct an instant and must never read one; they must "
               "need no platform, or they cannot prove the code under them needs none",
        protects="D9, D82",
    ),
)

#: Imports a deterministic zone may make that a pure zone may not.
DETERMINISTIC_ZONE_ALLOWED_IMPORTS: frozenset[str] = frozenset({
    "datetime", "calendar", "zoneinfo", "dateutil", "pytz",
})


PURE_ZONES: tuple[PureZone, ...] = (
    PureZone(
        path="nli_core/contract",
        reason="the Envelope and the State are the normative form (D11); "
               "their canonical form must be stable across runs (03 §14.3)",
        protects="D11, D43",
    ),
    PureZone(
        path="nli_core/application",
        reason="the Applicator is pure: same inputs, same state, forever. "
               "This is what keeps the corpus reproducible",
        protects="D9, D82",
    ),
    PureZone(
        path="nli_core/validation/structural.py",
        reason="levels 1-2 validate structure and vocabulary only — no ORM, "
               "no permissions, no clock (03 §12.3)",
        protects="D14",
    ),
    PureZone(
        path="nli_core/validation/coherence.py",
        reason="the dictionary-free half of levels 4-5: tree depth, grouping "
               "count, conflicting operations, cost ceilings (03 §12.5-12.6)",
        protects="D12, D13",
    ),
    PureZone(
        path="nli_semantics/dictionary",
        reason="levels, entry types and the term index are functions of their "
               "arguments; the platform enters only as introspected descriptors "
               "(06 §2.4, §5.3)",
        protects="D28, D30, D37",
    ),
    PureZone(
        path="nli_semantics/catalogue",
        reason="exposure, budget, the three phases and coverage must be "
               "reproducible without a database, or the fast path of phase A "
               "becomes a second unmeasured probabilistic component (D32, RC3)",
        protects="D32, D33, D34, D79",
    ),
    PureZone(
        path="nli_core/validation/contextual.py",
        reason="levels 3-5 need the dictionary and the types, and receive both as "
               "arguments: resolution is a lookup, not a database call (03 §12.4-12.6)",
        protects="D14, D12",
    ),
)

#: Imports banned inside a pure zone. `odoo` is banned because the zone must be
#: platform-independent; the rest because they are sources of non-determinism.
PURE_ZONE_FORBIDDEN_IMPORTS: frozenset[str] = frozenset({
    "odoo",
    "datetime",
    "time",
    "calendar",
    "zoneinfo",
    "pytz",
    "dateutil",
    "random",
    "secrets",
    "uuid",
    "os",
    "sys",
    "socket",
    "subprocess",
    "threading",
    "asyncio",
    "psycopg2",
    "requests",
})

#: Call suffixes banned inside a pure zone even when reached without an import
#: (for example through an object passed in as an argument).
PURE_ZONE_FORBIDDEN_CALLS: frozenset[str] = frozenset({
    "now",
    "utcnow",
    "today",
    "fromtimestamp",
    "monotonic",
    "perf_counter",
    "time_ns",
    "uuid1",
    "uuid4",
    "getenv",
    "randint",
    "choice",
    "shuffle",
    "random",
})


def module_dirs() -> list[Path]:
    """The `nli_*` module directories declared in the spec, in graph order."""
    return [ADDONS_DIR / name for name in MODULES]


def transitive_nli_depends(
    module: str,
    modules: dict[str, ModuleSpec] | None = None,
) -> frozenset[str]:
    """Every `nli_*` module reachable from `module` through declared edges.

    `modules` is injectable so the checks can be exercised against fixture
    graphs — a check nobody has ever seen fail is not a check.
    """
    graph = MODULES if modules is None else modules
    seen: set[str] = set()
    frontier = [module]
    while frontier:
        current = frontier.pop()
        for dependency in graph[current].nli_depends:
            if dependency not in seen:
                seen.add(dependency)
                frontier.append(dependency)
    return frozenset(seen)
