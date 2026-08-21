"""The Execution Plan — technical, ephemeral, never persisted.

**Deterministic zone.**

`03` §1.3 and `04` §4.6 both put the Plan outside the contract, and §2.1 of the
registry's table says why: contractualising it would tie the product to Odoo's
internals, which is exactly what the decoupling surface exists to avoid. So the Plan
is defined here, by the component that produces it, and no schema of it is published.

**Never persisted** (§4.6, table of artefacts). What persists is the State, in
semantic terms; the Plan is rebuilt at every execution because permissions, the
dictionary and the instant are all re-read at every execution (§1.4). A stored Plan
would be a frozen set of technical bindings and a saved query that silently stops
meaning what it meant.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Binding:
    """What a semantic reference resolves to, technically.

    Produced by whoever holds the dictionary — `nli_semantics` — and handed in.
    `nli_core` does not depend on `nli_semantics` (`04` §6.2), and this is the shape
    of that boundary: the core is told what a reference means, it does not look it up.

    A **category** carries a domain fragment rather than a field, because a T5 is a
    named condition and has no attribute. The fragment is computed for this execution
    and never stored (V-D87-3): its condition may depend on the clock —
    *"overdue"* is `due < today` — so freezing it would break both the Applicator's
    purity and the propagation §15.6 requires.
    """

    #: `attribute` or `category`.
    kind: str
    #: For an attribute: the technical field path, e.g. `partner_id.city`.
    field: str = ""
    #: For an attribute: the Odoo field type, which decides the operator.
    type: str = ""
    #: For a category: the domain fragment it expands to, already resolved.
    domain: tuple = ()
    #: True when the attribute is stored and can therefore be ordered on.
    sortable: bool = True
    #: For an attribute: **who is on the other side**, when the relation leads to a
    #: person. Today one value, `"user"`, meaning *this field says which Odoo user*.
    #:
    #: Sta qui e non nel catalogo per una ragione precisa: il catalogo dichiara
    #: `relation` e si ferma, perche' la zona che decide l'esposizione non deve sapere
    #: di Odoo (`catalogue/build.py` §126). Il **binding** invece lo costruisce chi Odoo
    #: lo conosce, e il risolutore ne ha bisogno per rifiutare `current_user` su un
    #: campo che con gli utenti non c'entra niente.
    identity: str = ""


@dataclass(frozen=True)
class Plan:
    """Everything the Executor needs, and nothing it has to interpret."""

    model: str
    domain: tuple
    fields: tuple[str, ...]
    group_by: tuple[str, ...]
    order: str
    limit: int
    view: str
    #: Aggregations, as `(function, field)`. Empty for a plain list.
    measures: tuple[tuple[str, str], ...] = ()
    #: The resolved periods, for the interpretation (D67): the interpretation shows
    #: *"1 - 31 July 2026"*, never *"this month"*, because "this month" confirms
    #: itself and a non-calendar fiscal year would never be caught.
    resolved_periods: tuple[tuple[str, str], ...] = ()

    def as_search_arguments(self) -> dict:
        """The keyword arguments of `search`, so the Executor builds no strings."""
        return {"domain": list(self.domain), "limit": self.limit, "order": self.order}


@dataclass
class ResolutionFailure:
    """A reference that could not be resolved, in the terms of §7.4.

    `unauthorised` is folded into `unresolved` on purpose and the caller cannot tell
    them apart: §7.4 says a reference the user may not see is *treated as
    unresolved*, so that no information about its existence reaches the user. The
    distinction is kept here only for the diagnostic log, never for the message.
    """

    reference: str
    reason: str
    #: Diagnostics only. Never rendered towards the user.
    unauthorised: bool = False


@dataclass
class Resolution:
    """The outcome of resolving a state: a Plan, or the references that failed."""

    plan: Plan | None = None
    failures: list[ResolutionFailure] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.plan is not None and not self.failures
