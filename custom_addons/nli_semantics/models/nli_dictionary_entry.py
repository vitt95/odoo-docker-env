"""The dictionary entries somebody approved (D108).

Until this model existed the live dictionary was **L0 only**: what introspection reads
from the platform. The saved filters of D35 were proposed into the L3 queue and stayed
there, because L3 is not a level — `store.py` ignores it and `validate_entry` refuses
it outright. There was proposal and there was nothing to approve *into*.

This is that place. One record is one entry of `06` §2: a term, its level, and — for a
named condition — the typed condition that defines it.

## Why approval cannot be a click

`filters.py` says it in full: a saved filter carries an Odoo domain, and the condition
language of a T5 is deliberately not one. Translating the domain automatically would
mean parsing an arbitrary expression and getting it subtly wrong, producing a category
that means something **close to** what the user meant — the exact failure a category
exists to remove. So the domain travels with the proposal *for a person to read*, and
the typed condition is **written** during approval. The machine then translates the
typed condition into a domain (`dictionary/domains.py`), which is mechanical and has
one reading.

## Why a malformed entry cannot be stored

The constraint runs the dictionary's own validator, the same one `Dictionary.build`
runs. An entry that would be silently dropped at build time is refused at write time
instead: a definition that exists in a table and not in the dictionary is the kind of
divergence nobody notices until a result changes.

## What an ordinary user may see

Read for every internal user, write for the administrator. The read is not a courtesy:
the interrogation path is forbidden from using `sudo` (§6.3), so the runtime that
assembles the dictionary reads these rows with the asking user's rights. What protects
the user's catalogue is not the row being invisible — it is that the runtime keeps only
the entries whose entity that user may read.
"""

from __future__ import annotations

import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..dictionary import conditions as conditions_module
from ..dictionary import entries as entries_module

#: The types an approval can produce today. The others are declared in the dictionary
#: and rejected by `validate_entry` until they are needed (registry §6.5), and offering
#: them here would let somebody store what the dictionary will not read.
APPROVABLE_TYPES = [
    ("T1", "Naming"),
    ("T2", "Enumerated value"),
    ("T5", "Named condition"),
]

#: L3 is deliberately absent: it is a queue, not a level, and an entry that reached
#: this table has by definition left it.
LEVELS = [("L1", "L1 — domain"), ("L2", "L2 — installation")]


class NliDictionaryEntry(models.Model):
    _name = "nli.dictionary.entry"
    _description = "AIDA approved dictionary entry"
    _order = "entity_ref, ref"

    entry_type = fields.Selection(APPROVABLE_TYPES, required=True, default="T5",
                                  string="Type", index=True)
    level = fields.Selection(LEVELS, required=True, default="L2", index=True)
    ref = fields.Char(required=True, index=True,
                      help="The semantic reference, e.g. fatture_cliente.scadute.")
    entity_ref = fields.Char(required=True, string="Entity",
                             help="The entity this entry belongs to.")
    terms = fields.Text(
        required=True,
        help="One term per line. These are the words the user may say; the first is "
             "the one shown back to them.")
    condition = fields.Text(
        help="For a named condition (T5): the typed condition, as JSON. Written by "
             "the person approving, never derived from the filter's domain.")
    version = fields.Char(required=True, default="1")

    #: Traceability of the approval, and of what it was approved *from*.
    source_domain = fields.Text(
        readonly=True,
        help="The Odoo domain of the saved filter this entry came from, verbatim. "
             "Kept so the approval can be re-read, never executed from here.")
    approved_uid = fields.Many2one("res.users", string="Approved by", readonly=True)
    approved_on = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("ref_unique_per_type", "UNIQUE(entry_type, ref, level)",
         "An entry already exists for this reference at this level."),
    ]

    # --- what the dictionary reads ----------------------------------------
    def to_entry(self) -> dict:
        """The record in the shape `Dictionary.build` expects."""
        self.ensure_one()
        entry = {
            "type": self.entry_type,
            "level": self.level,
            "ref": self.ref,
            "terms": [line.strip() for line in (self.terms or "").splitlines()
                      if line.strip()],
            "version": self.version,
        }
        # `entity` solo per i tipi che la dichiarano (T5, T4). Per un **T1** e' una
        # chiave in piu' e il validatore la rifiuta — cioe' il registro dichiarava T1
        # fra i tipi approvabili e poi non ne accettava **nemmeno uno**. L'entita' di
        # un T1 e' gia' nel suo riferimento: `res_partner` la nomina, `res_partner.city`
        # la contiene.
        if self.entity_ref and self.entry_type not in ("T1", "T2"):
            entry["entity"] = self.entity_ref
        if self.entry_type == "T5":
            entry["condition"] = self.condition_value()
        return entry

    def condition_value(self):
        """The typed condition as data, or an empty mapping.

        Returned rather than raised on malformed JSON because the constraint below is
        what refuses it: this function is read by the runtime, and a runtime that
        raises on a row somebody managed to write takes the whole dictionary down for
        every user.
        """
        self.ensure_one()
        try:
            return json.loads(self.condition or "{}")
        except ValueError:
            return {}

    # --- what cannot be stored --------------------------------------------
    @api.constrains("entry_type", "level", "ref", "entity_ref", "terms",
                    "condition", "version")
    def _check_the_dictionary_would_accept_it(self):
        """The dictionary's own validator, run at write time.

        An entry that `Dictionary.build` would drop is refused here instead. A
        definition that exists in a table and not in the dictionary is a divergence
        nobody notices until a result changes.
        """
        for record in self:
            if record.entry_type == "T5" and record.condition:
                try:
                    json.loads(record.condition)
                except ValueError as error:
                    raise ValidationError(
                        _("The condition is not valid JSON: %s") % error) from error
                problems = conditions_module.validate(record.condition_value())
                if problems:
                    raise ValidationError(
                        _("The typed condition is not admitted:\n%s")
                        % "\n".join(problems))
            problems = entries_module.validate_entry(record.to_entry())
            if problems:
                raise ValidationError(
                    _("The dictionary would refuse this entry:\n%s")
                    % "\n".join(str(problem) for problem in problems))

    # --- approval ----------------------------------------------------------
    @api.model_create_multi
    def create(self, values_list):
        records = super().create(values_list)
        records._stamp_approval()
        return records

    def _stamp_approval(self):
        """Who approved, and when. Written by the system, not offered as a field.

        An approval whose author is a text somebody typed is not traceability.
        """
        self.write({"approved_uid": self.env.user.id,
                    "approved_on": fields.Datetime.now()})

    @api.model
    def approved_entries(self) -> list[dict]:
        """Every active entry, in dictionary shape.

        Read with the caller's rights: §6.3 forbids the interrogation path from
        elevating, and the runtime filters by what the user may read anyway.
        """
        return [record.to_entry() for record in self.search([])]
