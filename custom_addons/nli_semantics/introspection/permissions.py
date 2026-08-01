"""Readable references and the permission fingerprint (D39, D40).

**Not a pure zone.** This is the component that answers the one question the
catalogue cannot answer for itself: *what may this user, in this company context,
read?*

## Why the fingerprint exists at all

`04` §7.6 puts a *permission version* in the catalogue's memoisation key, and §10.4
founds a security property on it: two users share a catalogue only if they have the
same permissions, so reuse between users does not violate **V2**.

**Odoo exposes no such version.** It is not a datum that exists — it has to be
built, and if it is built badly the property decays **with no signal at all**: a
catalogue memoised before a revocation would keep exposing references the user may
no longer name. D39 is that decision, and it makes two properties normative:

* **fail safe** — if the fingerprint is not computable, the catalogue is rebuilt.
  Never served from memory with an uncertain fingerprint;
* **event invalidation stays, as an optimisation.** Correctness depends on the
  fingerprint, not on the notification. A lost notification must not be able to
  produce a violation of V2.

## Why the company context is in it (D40)

In Odoo the perimeter of visible records depends on the user's **active companies**,
not only on their groups. An execution that restores the user but not their active
companies returns a **plausible and wrong** result: the same orders the user would
see, plus those of a company they had deselected in the interface. No error, no
warning, a different number.

It is the infrastructural form of R1, and more insidious than the linguistic one: it
does not come from a misunderstanding of language, so no analysis of misunderstandings
would ever find it.
"""

from __future__ import annotations

import hashlib
import json

from .l0 import reference_of_field, reference_of_model


class FingerprintUnavailable(Exception):
    """The fingerprint could not be computed, so nothing may be reused.

    Raised rather than returned as `None` because the safe behaviour is a rebuild,
    and a `None` that a caller forgets to check is precisely the silent decay D39
    exists to prevent.
    """


def readable_references(env, model_name: str) -> frozenset[str]:
    """The references of `model_name` this user may read, plus the entity itself.

    `fields_get` is the primitive: it already drops the fields whose `groups` the
    user does not hold, which is field-level access applied **before** selection as
    §5.9 requires. Model-level access is checked first — a user with no read access
    to the model has no readable references on it at all, and the entity must not
    appear in their catalogue either.

    Note what is **not** done here: no `sudo`, no privileged context. The whole point
    is to see what the user sees; asking with more rights than the user has would
    answer a different question, and V2 forbids a privileged path anywhere in the
    interrogation chain.
    """
    if not env[model_name].has_access("read"):
        return frozenset()
    entity = reference_of_model(model_name)
    references = {entity}
    for name in env[model_name].fields_get():
        references.add(reference_of_field(model_name, name))
    return frozenset(references)


def readable_entities(env, model_names) -> frozenset[str]:
    """The subset of `model_names` this user may read.

    The first line of defence of **V2** is the vocabulary itself (D10, §7.2): what a
    user cannot see does not enter the space of possible interpretations, so the
    model cannot name it and no refusal has to reveal that it exists.
    """
    return frozenset(
        reference_of_model(name) for name in model_names
        if env[name].has_access("read")
    )


def _observable_state(env, model_names) -> dict:
    """What the user can actually see of their own permissions.

    **A finding from running this against a real database.** The first version read
    `ir.model.access` and `ir.rule` directly, as D39's wording suggests. An ordinary
    internal user cannot: *"You are not allowed to access 'Model Access'
    (ir.model.access) records."* And `sudo` is not available — the syntactic check of
    D24 forbids it, correctly, because a privileged read here would be a privileged
    path inside the interrogation chain (V2).

    So the fingerprint is built from **observable effects** rather than from the rule
    tables, and the substitution turns out to be not a workaround but the more
    correct construction:

    * **model access** -> `has_access("read")`, which is the question itself rather
      than the configuration that answers it;
    * **field-level access** -> the key set of `fields_get()`, which already drops
      the fields whose `groups` the user does not hold. It is the same call the
      catalogue makes, so the fingerprint cannot disagree with the thing it
      fingerprints — reading the ACL table separately could;
    * **record rules** -> deliberately absent, and this is the part worth arguing.

    **Why record rules do not belong in a catalogue key.** A record rule changes
    which *records* are returned. The catalogue contains **references** — entity and
    attribute names — and never a record: A6 and V7 see to that. A change to a record
    rule therefore cannot change the catalogue's contents, and putting it in the key
    would invalidate the memoisation on an event that cannot affect the result.

    The rules of course still apply, at execution, where the records are. D39 lists
    them because its fingerprint also keys the reuse of *interpretations*; if that
    reuse is ever built, it needs a key of its own, and this note is where the
    difference is recorded.
    """
    return {
        "access": {
            name: env[name].has_access("read") for name in sorted(model_names)
        },
        "fields": {
            name: sorted(env[name].fields_get())
            for name in sorted(model_names)
            if env[name].has_access("read")
        },
    }


def fingerprint(env, model_names) -> str:
    """A computed value that changes whenever what the user may **name** could change.

    Composed of the user's groups, the company context (D40), the language, and the
    observable access state of each model — see `_observable_state` for why the rule
    tables are not read and why record rules are deliberately absent.
    """
    try:
        material = {
            # **The user's identity is deliberately absent**, and part 6 is what
            # made the omission necessary rather than merely defensible. D39's
            # delibera states the property the fingerprint is supposed to buy:
            # *"two users share a catalogue fingerprint only if they have the same
            # permissions, so reuse between them does not violate V2"*. With the uid
            # in the material no two users ever share one, and the dictionary is
            # rebuilt per user — on an installation with two hundred users, two
            # hundred builds of the same thing.
            #
            # The uid adds nothing about what a user may *name*: that is decided by
            # groups, companies, language and the observable access state below. Two
            # users identical in all four can name exactly the same references, which
            # is the whole content of the catalogue.
            "groups": sorted(env.user.groups_id.ids),
            # D40. `env.companies` is the set of **active** companies, which is what
            # governs the perimeter — not `env.company`, which is only the current
            # one and would make two different perimeters look identical.
            "companies": sorted(env.companies.ids),
            "company": env.company.id,
            "lang": env.lang or "",
            **_observable_state(env, model_names),
        }
    except Exception as error:  # noqa: BLE001 — any failure means "do not reuse"
        raise FingerprintUnavailable(str(error)) from error

    rendered = json.dumps(material, sort_keys=True, separators=(",", ":"),
                          default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def fingerprint_or_rebuild(env, model_names) -> str | None:
    """The fingerprint, or `None` meaning **rebuild, do not reuse**.

    The two ways of expressing failure exist for different callers: a component that
    must not proceed uses `fingerprint` and lets the exception travel; one that has a
    safe fallback — rebuilding — uses this and treats `None` as "no key". Both lead to
    the same place, which is the point of D39's *fail safe*.
    """
    try:
        return fingerprint(env, model_names)
    except FingerprintUnavailable:
        return None
