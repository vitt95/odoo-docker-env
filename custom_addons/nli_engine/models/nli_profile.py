"""Model profiles, administered — and the two things administration cannot do.

**D75** closes D8 in the widest sense: local models and remote ones, chosen from the
panel. The architecture needed no change to allow it, which is the return on the
investment made in V5 and the Adapter — at the test, it was already substitutable.

Moving the choice from the environment to the panel **moves the trust boundary**,
though, and D76, D77 and D80 are what pay for it:

* the endpoint is administered, **the set of hosts it may point at is not** (D77);
* the credential is named here, **its value lives in the environment** (D76);
* a profile that has not been qualified **cannot be activated** (D80).

## Why the last one is a structural prohibition and not a procedure

D51 lays out an eight-step qualification protocol, and D80's whole delibera is one
line: it *"makes D51 impossible to bypass by inattention"*. A procedure that depends on
somebody remembering is a procedure that holds until the afternoon somebody is in a
hurry. So the state machine refuses, and the refusal is a constraint on the record.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..adapters import PROTOCOLS
from ..adapters.base import Capabilities
from ..adapters.http import allowed_hosts, check_endpoint
from ..adapters.base import HostNotAllowed

#: The states of D80, in the only order they may be traversed.
STATES = [
    ("draft", "Bozza"),
    ("qualified", "Qualificato"),
    ("active", "Attivo"),
    ("retired", "Ritirato"),
]


class NliProfile(models.Model):
    _name = "nli.profile"
    _description = "AIDA model profile"
    _order = "state, name"

    name = fields.Char(required=True)
    #: Closed set (D75): an endpoint speaking an unknown protocol is an endpoint
    #: nobody reviewed. Adding one is a code change, deliberately.
    protocol = fields.Selection(
        selection=[(key, key) for key in sorted(PROTOCOLS)],
        required=True, default="openai_compatible")
    endpoint = fields.Char(
        required=True,
        help="Base URL of the provider. The host must appear in NLI_ALLOWED_HOSTS, "
             "which lives in the environment and cannot be widened from here (D77).")
    model_name = fields.Char(required=True)

    #: D76 — the **name** of an environment variable, never a value. A database dump
    #: yields `NLI_OPENAI_KEY`, which is worth nothing.
    secret_env_var = fields.Char(
        string="Secret environment variable",
        help="Name of the environment variable holding the credential. The value is "
             "never stored: a database dump must not yield credentials (D76).")

    # --- D78: the profile declares what it can do -------------------------
    context_window = fields.Integer(
        required=True, default=8192,
        help="Tokens the model accepts. The catalogue budget is derived from it "
             "(D79): a narrow window truncates the catalogue in silence.")
    constrained_generation = fields.Boolean(
        default=False,
        help="Whether the provider can constrain output to a JSON schema (§12.3). "
             "Without the declaration a degraded profile looks like a system defect.")
    system_role = fields.Boolean(default=True)
    reasoning_effort = fields.Selection(
        [("none", "None"), ("minimal", "Minimal"), ("low", "Low"),
         ("medium", "Medium"), ("high", "High")],
        help="How much the model may reason before answering (D98). Left empty the "
             "field is not sent, for providers that do not have the feature. A model "
             "whose reasoning mode is on by default spends the window before reaching "
             "the envelope and answers nothing at all — measured, not feared.")

    # --- D80: the state machine -------------------------------------------
    state = fields.Selection(STATES, required=True, default="draft", index=True)
    qualified_on = fields.Datetime(readonly=True)
    qualification_note = fields.Text(
        help="What was measured, on which corpus, at which reference instant. A "
             "qualification nobody can reconstruct is not one (D51).")

    _sql_constraints = [
        ("context_window_positive", "CHECK (context_window > 0),",
         "A profile declares its context window (D78)."),
    ]

    @api.constrains("endpoint", "protocol")
    def _check_endpoint_is_admitted(self):
        """The host must be in the environment's list (**D77**).

        Checked on write, not only on call: a profile pointing somewhere unadmitted is
        a configuration mistake that should surface when it is made, not on the first
        interrogation of the morning. The `recorded` protocol opens no socket and is
        exempt — there is nothing to reach.
        """
        for profile in self:
            if profile.protocol == "recorded":
                continue
            try:
                check_endpoint(profile.endpoint or "")
            except HostNotAllowed as error:
                raise ValidationError(str(error)) from error

    @api.constrains("state")
    def _check_only_one_active(self):
        """One active profile (D75). Two would make the answer depend on which."""
        for profile in self.filtered(lambda p: p.state == "active"):
            others = self.search([
                ("state", "=", "active"), ("id", "!=", profile.id),
            ])
            if others:
                raise ValidationError(
                    f"{others[0].name!r} is already active. One profile is active at "
                    "a time (D75): with two, which one answered would be a question "
                    "nobody could answer afterwards."
                )

    def action_qualify(self, note: str = ""):
        """Record that the protocol of D51 was run. Draft -> qualified."""
        for profile in self:
            if profile.state not in ("draft", "retired"):
                raise UserError("Only a draft or retired profile can be qualified.")
            profile.write({
                "state": "qualified",
                "qualified_on": fields.Datetime.now(),
                "qualification_note": note or profile.qualification_note,
            })
        return True

    def action_activate(self):
        """Activate. **Refused for a profile that was never qualified** (D80).

        This is the structural prohibition: not a warning, not a checklist item, a
        refusal. D51's eight steps include the isolation proof — a slower model halves
        the dispatcher's capacity and the consequence lands on the ERP, not on us.
        """
        for profile in self:
            if profile.state != "qualified":
                raise UserError(
                    f"{profile.name!r} is in state {profile.state!r}. A profile that "
                    "has not been qualified cannot be activated (D80): the "
                    "qualification of D51 includes the isolation proof, and a model "
                    "that has not passed it can degrade the ERP for everyone."
                )
            self.search([("state", "=", "active")]).write({"state": "qualified"})
            profile.state = "active"
        return True

    def action_retire(self):
        self.write({"state": "retired"})
        return True

    @api.model
    def active_profile(self):
        """The profile in use, or nothing.

        Returning empty rather than raising: §11 of `04` lists *model unavailable* as
        a declared failure mode in which the system stays partially usable — saved
        queries and editing the interpretation keep working — and an exception here
        would take those down too.
        """
        return self.search([("state", "=", "active")], limit=1)

    def capabilities(self) -> Capabilities:
        self.ensure_one()
        return Capabilities(
            context_window=self.context_window,
            constrained_generation=self.constrained_generation,
            system_role=self.system_role,
            reasoning_effort=self.reasoning_effort or None,
        )

    def adapter(self):
        """Build the adapter for this profile.

        The only place a profile becomes a connection. Everything about where it may
        connect and with what credential was decided in `adapters/http.py`, from the
        environment.
        """
        self.ensure_one()
        builder = PROTOCOLS.get(self.protocol)
        if builder is None:
            raise UserError(f"Unknown protocol {self.protocol!r}.")
        if self.protocol == "recorded":
            raise UserError(
                "The recorded protocol is for tests and for replaying the regression "
                "corpus; it is not built from a profile."
            )
        return builder(
            endpoint=self.endpoint,
            model=self.model_name,
            capabilities=self.capabilities(),
            secret_variable=self.secret_env_var or None,
        )

    @api.model
    def admitted_hosts(self) -> list:
        """What the environment admits, for the administration screen to show.

        Shown and not editable: an administrator who can see the list can tell why an
        endpoint was refused, without being able to widen it (D77).
        """
        return sorted(allowed_hosts())
