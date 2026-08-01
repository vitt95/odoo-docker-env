"""The dictionary as a service, with the one cache the product needs.

Building the dictionary of an installation costs a `fields_get` per entity in scope
plus a view read: tens of milliseconds, paid on every turn if nothing remembers it.
Under the load control of D20c that is not merely slow, it is the pool's throughput.

**The cache key is the permission fingerprint of D39, and nothing else.** Not the
user: two users with identical rights see an identical dictionary, and reuse between
them is precisely what D39's delibera authorises — *"two users share a catalogue
fingerprint only if they have the same permissions, so reuse between users does not
violate V2"*. When the fingerprint cannot be computed the answer is to rebuild, never
to reuse a key that might be stale. That is D39's fail-safe, and here it costs one
`if`.

Held in `ormcache` rather than a module dictionary for a reason that shows up on the
day somebody upgrades a module: Odoo clears its caches when the registry is rebuilt,
so a new field appears in the dictionary without anyone remembering to invalidate
anything. A hand-rolled cache would keep serving yesterday's schema — the failure
mode D84 exists to prevent, reintroduced one level lower.
"""

from odoo import api, models, tools

from ..introspection import runtime


class NliSemantics(models.AbstractModel):
    _name = "nli.semantics"
    _description = "AIDA dictionary and catalogue for the current user"

    @api.model
    def entity_scope(self) -> tuple:
        """The configured entity scope. Needs the system group — see `runtime`."""
        return runtime.entity_scope(self.env)

    @api.model
    def semantics(self, scope) -> runtime.Semantics:
        """The dictionary, entity references and bindings for the calling user."""
        scope = tuple(scope)
        fingerprint = runtime.fingerprint(self.env, scope)
        if fingerprint is None:
            # D39: no key, no reuse. The build is the expensive path and taking it is
            # the point — a catalogue served under an uncertain fingerprint is how a
            # revoked permission keeps being exposed with no signal at all.
            return runtime.semantics(self.env, scope)
        return self._semantics_cached(fingerprint, scope)

    @tools.ormcache("fingerprint", "scope")
    def _semantics_cached(self, fingerprint, scope):
        return runtime.semantics(self.env, scope)

    @api.model
    def catalogue_for(self, semantics, entity_ref: str, *, context_window: int):
        return runtime.catalogue_for(
            self.env, semantics, entity_ref, context_window=context_window
        )

    @api.model
    def entity_catalogue(self, semantics, *, context_window: int):
        return runtime.entity_catalogue(semantics, context_window=context_window)
