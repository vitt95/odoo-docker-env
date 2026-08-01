"""Saved filters as category proposals (D35, `06` §7).

**Not a pure zone.**

> A public filter named *"Fatture scadute"* directly yields a **category (T5)**
> proposal: term, entity, condition. A filter named *"Ordini da evadere"* does the
> same for a concept that exists in no database field but that everyone in the
> company uses. (`06` §7)

D35 calls saved filters the lowest-cost, highest-quality source there is, and the
reason is that somebody in the company already did the work: naming a condition they
care about, in their own words, and keeping it.

## Proposals, never active entries

Everything produced here enters the **L3 queue** and is inert until approved
(D28, `06` §2.3). Three reasons, and the second is the one that matters:

* a filter's name is user-written text, and the dictionary feeds the catalogue,
  which reaches the model — an unreviewed entry here is an unvalidated input there;
* an approved category is a **definition** (D29): it changes results. Automatically
  activating one would change what saved queries return, silently;
* the review cost is small because proposals aggregate — a list of a few dozen terms
  ordered by how many users kept the filter, not thousands of events.

## The domain is not translated here

A filter's `domain` is an Odoo expression, and the condition language of `T5` is
deliberately not one (`dictionary/conditions.py`). Translating it automatically
would mean parsing arbitrary Odoo domains into a typed tree, and getting that subtly
wrong produces a category that means something **close to** what the user meant —
the exact failure mode a category is supposed to remove. So the proposal carries the
domain **verbatim, for a human to read**, and the typed condition is written during
approval. That is the step D28 says must not be skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .l0 import reference_of_model

#: Filters whose name is a bare label with no meaning outside the screen they were
#: saved on. Excluded because a proposal nobody would approve still costs a review.
UNINFORMATIVE_NAMES = frozenset({
    "", "filtro", "filter", "test", "nuovo", "new", "temp", "tmp", "prova",
})


@dataclass(frozen=True)
class CategoryProposal:
    """A candidate T5 entry, inert until approved.

    Carries the evidence for the decision, not just the candidate: how many users
    kept this filter is what orders the review queue, and `06` §2.3 says the review
    is affordable precisely because it is ordered by impact.
    """

    entity: str
    term: str
    #: The Odoo domain, verbatim. Read by a person during approval, never executed
    #: from here and never handed to the model.
    domain: str
    #: How many distinct users saved a filter with this name on this model. A shared
    #: filter — `user_id` unset — counts as the strongest evidence there is: someone
    #: published it for everyone.
    users: int = 1
    shared: bool = False

    def as_entry(self) -> dict:
        """The L3 entry, deliberately **without** a condition.

        The typed condition is written during approval. Emitting one here would mean
        guessing a translation of the domain, and a category that means something
        close to what was meant is worse than no category at all.
        """
        return {
            "type": "T5", "level": "L3",
            "ref": f"{self.entity}.{_slug(self.term)}",
            "entity": self.entity,
            "terms": [self.term],
            "version": "proposal",
        }


def _slug(term: str) -> str:
    return "_".join(
        part for part in term.casefold().replace("/", " ").replace("-", " ").split()
    )[:60]


def propose_categories(env, model_names) -> list[CategoryProposal]:
    """Category proposals from the saved filters of the given models.

    Only filters the user may see: `ir.filters` carries its own record rules, and
    reading them with the user's rights is both correct and the only thing V2 allows.
    Shared filters — those with no `user_id` — are the ones §7 is really about.
    """
    wanted = list(model_names)
    if not wanted:
        return []

    filters = env["ir.filters"].search([("model_id", "in", wanted)])

    grouped: dict[tuple[str, str], dict] = {}
    for saved in filters:
        name = (saved.name or "").strip()
        if name.casefold() in UNINFORMATIVE_NAMES:
            continue
        key = (saved.model_id, name)
        bucket = grouped.setdefault(key, {"users": set(), "shared": False,
                                          "domain": saved.domain or "[]"})
        if saved.user_id:
            bucket["users"].add(saved.user_id.id)
        else:
            bucket["shared"] = True

    proposals = [
        CategoryProposal(
            entity=reference_of_model(model_name),
            term=name,
            domain=bucket["domain"],
            users=len(bucket["users"]),
            shared=bucket["shared"],
        )
        for (model_name, name), bucket in grouped.items()
    ]
    # Ordered by impact: shared first, then by how many people kept it. It is the
    # order the review queue is worked in, and the reason the review is affordable.
    proposals.sort(key=lambda p: (not p.shared, -p.users, p.entity, p.term))
    return proposals
