"""The dictionary a live installation actually has, assembled from the platform.

Parts 2 to 5 built every piece of this and never joined them on a real database: the
dictionary was read from a JSON pack written for the corpus, and the resolver's
bindings were written by hand in a test. Part 6 has to execute turns on a cron
process, so somebody has to answer, for this database and this user: *which entities
exist, what are they called, and what does each reference mean technically?*

Three things had to be decided here, and each is a seam the earlier parts left.

**The scope of entities is declared, not discovered.** `candidate_entities` returns
every non-transient model of the registry — several hundred on a plain installation,
each costing a `fields_get`. Building a dictionary over all of them per turn is not a
performance detail, it is the difference between a product and a demonstration. The
scope is therefore an `ir.config_parameter`, with a default list of the entities a
business user names out loud. Widening it is configuration; the cost of widening it
is visible because the build is cached per fingerprint and shows up once.

**Odoo types are not contract types.** `fields_get` says `char`, `many2one`,
`monetary`; `03` §8.1 enumerates predicates over `text`, `relation`, `number`. Until
now the two never met — the corpus pack already spoke the contract's language — and a
catalogue advertising `char` would have the model emit predicates that level 4 then
rejects, for a reason no diagnostic would name. The mapping lives here because it is
platform knowledge, and it is *passed* to the pure zone rather than looked up there.

**The cache is keyed on the permission fingerprint (D39).** Not on the user: two
users with the same rights get the same dictionary, which is what makes reuse safe
under V2. When the fingerprint cannot be computed the answer is to rebuild, never to
serve from a key that might be stale — D39's *fail safe*, applied to the level of
the product where it is cheapest to obey.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from odoo import fields as odoo_fields

from ..catalogue import build as build_module
from ..catalogue import exposure, phases
from ..dictionary import conditions as conditions_module
from ..dictionary import domains
from ..dictionary.store import Dictionary
from ..platform_types import CONTRACT_TYPE_BY_ODOO_TYPE
from . import l0, permissions

#: `CONTRACT_TYPE_BY_ODOO_TYPE` is imported above and used twice below; it also stays
#: readable as `runtime.CONTRACT_TYPE_BY_ODOO_TYPE` for the callers written before it
#: moved. It lives in the pure `platform_types` because it is a platform fact that
#: needs no ORM, and the tools that build a catalogue without a database need it.

#: The entities of the phase 1 scope, when nothing is configured.
#:
#: Chosen as the models a person names in a sentence in a standard installation, not
#: as a technical criterion — the technical criterion is `candidate_entities`, and it
#: returns hundreds. Models absent from the installation are dropped silently: a
#: default scope that failed on an installation without CRM would be a default
#: nobody could use.
DEFAULT_ENTITY_SCOPE: tuple[str, ...] = (
    "res.partner",
    "sale.order",
    "sale.order.line",
    "purchase.order",
    "account.move",
    "account.move.line",
    "product.template",
    "stock.picking",
    "stock.quant",
    "crm.lead",
    "project.task",
    "hr.employee",
    "mrp.production",
)

#: The parameter that overrides it, comma separated.
SCOPE_PARAMETER = "nli.entities"


@dataclass(frozen=True)
class Semantics:
    """Everything the chain needs to turn words into a query, for one user.

    Built once per permission fingerprint and shared by every turn that follows.
    """

    dictionary: Dictionary
    #: References that *are* entities — phase A must not resolve an entity from the
    #: name of one of its fields, and the D93 guard needs to tell them apart.
    entity_refs: frozenset[str]
    #: Semantic reference -> technical meaning, for the Resolver.
    bindings: dict
    #: Entity reference -> Odoo model name. The reverse of `reference_of_model` is
    #: kept rather than recomputed: `stock_quant_package` has two readings and
    #: guessing at the right one would be a silent wrong query.
    models_by_ref: dict
    #: References this user may read (D39, D40), already filtered.
    readable_refs: frozenset[str]
    #: Riferimento di condizione nominata -> classe di costo, `simple` o `aggregate`.
    #:
    #: **Serve al livello 5, e finora nessuno lo costruiva.** `contextual.validate` ha
    #: sempre avuto il parametro `category_costs`; il pipeline non lo passava, quindi
    #: valeva `{}` e `too_many_aggregate_categories` — la regola con cui **V-D87-2**
    #: (il vincolo di D87 per cui una condizione nominata che aggrega su un'altra
    #: entita' e' affare del livello 5) si giustifica — non poteva scattare mai.
    #:
    #: Si costruisce qui e non nel pipeline perche' la classe di costo si legge dalla
    #: **definizione** della condizione, che sta nel dizionario: `nli_core` riceve la
    #: risposta e non il vocabolario, come per `mentions` di D105.
    category_costs: dict = field(default_factory=dict)

    def model_of(self, entity_ref: str) -> str | None:
        return self.models_by_ref.get(entity_ref)


def entity_scope(env) -> tuple[str, ...]:
    """The models in scope, configured or default, restricted to what exists.

    Called with the **dispatcher's** environment, not the user's: reading
    `ir.config_parameter` needs the system group, and an ordinary user must not have
    it. Configuration is read once per cycle by the process that owns the cycle and
    handed to the workers — which is also the right shape, since the scope is a
    property of the installation and not of whoever is asking.
    """
    configured = env["ir.config_parameter"].get_param(SCOPE_PARAMETER, "")
    names = [name.strip() for name in (configured or "").split(",") if name.strip()]
    if not names:
        names = list(DEFAULT_ENTITY_SCOPE)
    return tuple(name for name in names if name in env.registry)


def fingerprint(env, scope) -> str | None:
    """D39's key, or `None` meaning *rebuild, do not reuse*."""
    return permissions.fingerprint_or_rebuild(env, scope)


def semantics(env, scope) -> Semantics:
    """Assemble the dictionary, the entity references and the bindings.

    The permission filter runs **before** anything else (§5.9): a reference the user
    may not read is absent from the dictionary, so it cannot be named, cannot be
    matched by phase A and cannot be resolved. That is D10 as a property of the
    vocabulary rather than a check somebody has to remember to apply.
    """
    readable = frozenset().union(
        *(permissions.readable_references(env, name) for name in scope)
    ) if scope else frozenset()

    entries = [
        entry for entry in l0.generate(env, scope)
        if entry["ref"] in readable
    ]
    # D108: the entries somebody approved, on top of what introspection reads. Kept
    # only when the entity they belong to is readable by this user — the row being
    # visible is not what protects a catalogue, this filter is.
    approved = [
        entry for entry in env["nli.dictionary.entry"].approved_entries()
        if (entry.get("entity") or entry["ref"]) in readable
    ]
    entries.extend(approved)

    models_by_ref = {}
    bindings = {}
    for model_name in scope:
        entity_ref = l0.reference_of_model(model_name)
        if entity_ref not in readable:
            continue
        models_by_ref[entity_ref] = model_name
        bindings[entity_ref] = _binding(kind="attribute", field="", type_="entity")
        for name, info in env[model_name].fields_get().items():
            ref = l0.reference_of_field(model_name, name)
            if ref not in readable:
                continue
            contract_type = CONTRACT_TYPE_BY_ODOO_TYPE.get(info.get("type") or "")
            if contract_type is None:
                # A type with no predicate is a reference nothing can be asked
                # about. Leaving it bindable would let a query resolve and then fail
                # at execution, which is the late failure C3 exists to prevent.
                continue
            # **Chi c'e' dall'altra parte**, quando c'e' qualcuno. `fields_get` lo dice
            # gia' (`relation` porta il comodello) e finora nessuno lo leggeva: serve
            # al risolutore per sapere su quali campi `current_user` ha senso.
            bindings[ref] = _binding(
                kind="attribute", field=name, type_=contract_type,
                identity="user" if info.get("relation") == "res.users" else "")

    # A named condition has no field: its binding carries the domain its typed
    # condition produces (V-D87-3), computed at every build and never stored. An entry
    # whose condition cannot be executed as a domain — an aggregate, level 5's
    # business — is left unbound, and level 3 refuses it by name instead of letting it
    # fail late at execution.
    # La classe di costo si legge sempre, anche quando la condizione **non** si lega:
    # un aggregato e' esattamente il caso che resta senza binding, ed e' anche l'unico
    # che il livello 5 deve poter contare. Leggerla solo dalle condizioni legate
    # avrebbe costruito una tabella dei costi con dentro tutto tranne cio' che costa.
    category_costs: dict[str, str] = {}
    for entry in approved:
        if entry["type"] != "T5":
            continue
        condition = entry.get("condition") or {}
        category_costs[entry["ref"]] = conditions_module.cost_class(condition)
        if entry["ref"] in bindings:
            continue
        try:
            domain = domains.domain_of(condition,
                                       instant=odoo_fields.Date.context_today(env.user))
        except domains.UntranslatableCondition:
            continue
        bindings[entry["ref"]] = _category_binding(domain)

    return Semantics(
        dictionary=Dictionary.build(entries),
        entity_refs=frozenset(models_by_ref),
        bindings=bindings,
        models_by_ref=models_by_ref,
        readable_refs=readable,
        category_costs=category_costs,
    )


def _category_binding(domain):
    """The binding of a named condition: a domain fragment, never a field (V-D87-3)."""
    from odoo.addons.nli_core.resolution.plan import Binding

    return Binding(kind="category", field="", type="category",
                   domain=tuple(tuple(part) if isinstance(part, (list, tuple)) else part
                                for part in domain))


def _binding(*, kind: str, field: str, type_: str, identity: str = ""):
    """Built here rather than imported at module scope for one reason.

    `nli_semantics` may import from `nli_core` — the graph allows it — but the import
    of a dataclass used in a hot loop is worth keeping local to the function that
    needs it, so the module stays importable when only the type map is wanted.
    """
    from odoo.addons.nli_core.resolution.plan import Binding

    return Binding(kind=kind, field=field, type=type_, identity=identity)


def determine_entity(semantics_: Semantics, utterance: str):
    """Phase A on a live dictionary: the fast path, or an honest decline."""
    return phases.determine_entity(
        utterance,
        semantics_.dictionary.term_index(),
        entity_refs=semantics_.entity_refs,
    )


def catalogue_for(env, semantics_: Semantics, entity_ref: str, *, context_window: int):
    """The phase C catalogue for a determined entity (D32)."""
    model_name = semantics_.model_of(entity_ref)
    if model_name is None:
        raise ValueError(f"{entity_ref} is not an entity of this installation")
    return build_module.build(
        semantics_.dictionary,
        entity=entity_ref,
        attributes=l0.attribute_descriptors(env, model_name),
        readable_refs=semantics_.readable_refs,
        context_window=context_window,
        entity_refs=semantics_.entity_refs,
        type_map=CONTRACT_TYPE_BY_ODOO_TYPE,
    )


def entity_catalogue(semantics_: Semantics, *, context_window: int):
    """The phase B catalogue — entity names only — shaped as the prompt expects.

    A `Catalogue` with no attributes *is* the phase B catalogue once it reaches the
    prompt: same payload, one shape to maintain instead of two.
    """
    rows = phases.entity_catalogue(
        semantics_.dictionary, entity_refs=semantics_.entity_refs
    )
    return build_module.Catalogue(
        entity="",
        attributes=(),
        categories=(),
        entity_names=rows.entities,
        budget=exposure.attribute_budget(context_window),
        refused_for_budget=(),
        excluded_for_permissions=(),
        excluded_categories=(),
        exposure_rules=(),
    )
