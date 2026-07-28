"""The Resolver — semantic references and the instant into an Execution Plan.

**Deterministic zone**, and the distinction is the point (`04` §4.6): this is *"the
only component aware of time"*, and being aware of time is not reading it. The
instant arrives as an argument, so the same state at the same instant always yields
the same Plan — which is what lets the evaluation corpus be re-run at a fixed moment
(§13.3) and what keeps the Applicator above it pure.

| Module | Contenuto |
|---|---|
| `calendar.py` | temporal expressions into half-open ranges, against the **fiscal** year (§9.2, V-D91-1) |
| `plan.py` | the Execution Plan and the bindings it is built from — technical, ephemeral, never persisted |
| `resolver.py` | reference resolution, vagueness, the domain (§7.4, §9.3) |
"""
