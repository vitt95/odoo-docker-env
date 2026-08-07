"""The Interrogation State as a record (D19), and the turns that produced it.

D19's delibera is worth restating, because it explains why there is no separate
store: *"no additional archive to manage for ten years. Resumption, channel change,
sharing, undo and traceability are consequences, not features to build."* All five
fall out of the state being an ordinary Odoo record.

## What is deliberately **not** persisted, and why

The state carries `provenance` — the fragment of the user's sentence that produced
each element (§10.3). Those fragments are **user text**, and D54 requires utterances
to be pseudonymised at ingress with a separate, encrypted mapping. That mechanism does
not exist yet.

Persisting the fragments now would mean writing user text in clear for the twelve
months of D26, and D54's own argument applies exactly: *"retroactive pseudonymisation
does not exist: every day without it produces clear data that no later decision
cleans up."* So provenance is **stripped on write** and the state persists without
it. The cross-highlighting of §10.3 keeps working inside the live turn, where the
envelope is still in memory; what is stored is the question, not the words.

When D54 lands, the fragments are stored pseudonymised and this stripping is removed
in the same change — not before.
"""

import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..contract import canonical, state as state_module
from ..validation import structural

#: Riesportate dal contratto, dove la funzione e' stata spostata quando le e'
#: arrivato un secondo chiamante in zona pura. Chi importava da qui continua a
#: funzionare: spostare una funzione non deve rompere chi la usava.
STRIPPED_KEYS = state_module.STRIPPED_KEYS
strip_provenance = state_module.strip_provenance


class NliInterrogation(models.Model):
    _name = "nli.interrogation"
    _description = "AIDA interrogation state"
    _order = "write_date desc"

    name = fields.Char(
        help="Set when the user saves the interrogation. An unnamed one is a live "
             "conversation; a named one is what §9.5 calls a saved query.",
    )
    user_id = fields.Many2one(
        "res.users", required=True, ondelete="cascade", index=True,
        default=lambda self: self.env.user,
    )
    dsl_version = fields.Char(required=True, default="1.0")
    state_json = fields.Text(
        required=True, default="{}",
        help="The Interrogation State in the normative form of 03 §5, without "
             "provenance fragments (D54).",
    )
    turn_ids = fields.One2many("nli.turn", "interrogation_id")
    turn_count = fields.Integer(compute="_compute_turn_count")

    @api.depends("turn_ids")
    def _compute_turn_count(self):
        for record in self:
            record.turn_count = len(record.turn_ids)

    @property
    def state(self) -> dict:
        return json.loads(self.state_json or "{}")

    @api.constrains("state_json")
    def _check_state_is_valid(self):
        """Nothing invalid is ever persisted (§12.1).

        A stored state that does not validate is a query that will fail when someone
        re-runs it in six months, with no clue as to why. Refusing the write moves the
        failure to the moment somebody can still fix it.
        """
        for record in self:
            candidate = record.state
            if not candidate or candidate == {}:
                continue
            failures = structural.validate_state(candidate)
            if failures:
                raise ValidationError(
                    "The interrogation state is not valid:\n"
                    + "\n".join(str(failure) for failure in failures[:5])
                )

    def write_state(self, state: dict):
        """Persist a state, stripping what D54 says must not be stored in clear."""
        self.ensure_one()
        self.state_json = json.dumps(strip_provenance(state), ensure_ascii=False)
        return self

    def canonical_key(self) -> str:
        """The canonical form, for deduplicating saved queries (§14.4 identity)."""
        self.ensure_one()
        return canonical.canonical_json(self.state)

    def references(self) -> list:
        self.ensure_one()
        return state_module.references(self.state)


class NliTurn(models.Model):
    _name = "nli.turn"
    _description = "AIDA interrogation turn"
    _order = "sequence, id"

    interrogation_id = fields.Many2one(
        "nli.interrogation", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")

    # --- D40: the execution context travels on the turn -------------------
    #
    # In Odoo the perimeter of visible records depends on the user's **active
    # companies**, not only on their groups. With the asynchronous execution of D20a
    # the turn runs on a cron process, where the context has to be rebuilt from the
    # turn. An execution that restores the user but not their companies returns the
    # same orders plus those of a company they had deselected: no error, no warning,
    # a different number.
    company_ids = fields.Many2many(
        "res.company", required=True,
        help="The user's active companies at the moment of the request (D40).")
    lang = fields.Char(required=True, default=lambda self: self.env.lang or "en_US")
    tz = fields.Char(default=lambda self: self.env.user.tz or "UTC")

    state_json = fields.Text(
        required=True, default="{}",
        help="The state this turn produced, without provenance fragments (D54).")
    #: What the user wrote, kept **in clear** (**D115**).
    #:
    #: D54 forbade this, and D115 supersedes it for the turn alone with the reason
    #: written down: a conversational product whose history cannot show the user their
    #: own words is a different product, and the Architect chose the history. What is
    #: given up is stated in the register and not hidden here: **a dump of this
    #: database contains the sentences people typed**. The record rule of `nli.turn`
    #: is what keeps them from colleagues; encryption no longer is.
    #:
    #: The queue keeps its own sealed copy (D96) and still erases it: that copy exists
    #: to cross to the cron process, not to be read again.
    utterance = fields.Text(
        help="Quello che l'utente ha scritto, in chiaro (D115). La coda ne tiene una "
             "copia cifrata e transitoria per il solo passaggio al processo cron.")
    #: L'esito del turno, come lo ha visto l'utente: `operations`, `clarification`,
    #: `out_of_scope`, `not_understood`. Serve alla cronologia per rimostrare la
    #: risposta senza doverla ricalcolare.
    outcome = fields.Char()
    #: La risposta gia' impaginata per una persona, come l'ha prodotta il Presentatore
    #: (`presenter.present(...).interpretation`).
    #:
    #: Conservata invece di essere riderivata a ogni apertura della cronologia: per
    #: ricostruirla servirebbero il catalogo, i diritti e l'istante di quel momento, e
    #: rileggere una conversazione tornerebbe a costare quanto eseguirla. Cosi' invece
    #: riaprire una sessione e' una lettura e basta — che e' cio' che tiene la chat
    #: reattiva quando i turni diventano centinaia.
    interpretation_json = fields.Text()
    #: Il piano risolto: modello, dominio, campi, ordine, limite (D124). **Non e'
    #: diagnostica**: e' cio' con cui la chat costruisce la tabella dei record, quindi
    #: si scrive sempre per un turno eseguito e non solo a modalita' accesa.
    #:
    #: Non porta parole dell'utente — i valori sono gia' risolti in date e numeri — ma
    #: porta nomi tecnici, e per questo esce solo verso il proprietario del turno.
    plan_json = fields.Text()
    #: La traccia diagnostica del turno: la busta del modello, lo stato e **la query**
    #: (D123). Scritta solo quando la modalita' diagnostica e' accesa, quindi
    #: un'installazione ordinaria non ne conserva nessuna.
    #:
    #: **Contiene testo dell'utente in chiaro**, perche' la busta porta la provenienza
    #: di ogni operazione, cioe' i frammenti della frase. E' lo stesso prezzo che D115
    #: ha gia' pagato per `utterance`, con la stessa protezione: la regola di record di
    #: `nli.turn` e la cancellazione a cascata con la conversazione. Non e' un registro
    #: diagnostico e non finisce nei log — D60 vieta frasi e cataloghi li' dentro, e
    #: questo e' il motivo per cui la traccia sta sul turno e non in un file.
    debug_json = fields.Text()
    executed_at = fields.Datetime()
    record_count = fields.Integer(
        help="Total matching records, counted before retrieval (D68).")

    @property
    def interpretation(self) -> dict:
        return json.loads(self.interpretation_json or "{}")

    # **Nessun vincolo SQL qui, e la ragione va scritta.** C'era, si chiamava
    # `companies_required` e verificava `CHECK (true)`: un vincolo che dichiara una
    # garanzia e non ne verifica nessuna. E' la stessa forma di `00` §20.2 — il `CHECK`
    # di `nli_profile` che PostgreSQL rifiutava per una virgola e che non e' mai
    # esistito in nessun database — con l'aggravante che qui il testo era valido, quindi
    # non c'era nemmeno un `ERROR` nei log a tradirlo.
    #
    # La versione giusta **non e' scrivibile**: `company_ids` e' un many2many, le righe
    # stanno in un'altra tabella, e un `CHECK` di riga non puo' contare le righe di una
    # relazione. La garanzia di D40 la da' il `@api.constrains` qui sotto, che gira
    # sull'ORM ed e' provato. Togliere il vincolo finto e dirlo vale piu' che tenerlo.

    @api.constrains("company_ids")
    def _check_company_context(self):
        """A turn without a company context is **refused, never executed** (D40).

        Listed in §9 of the decision registry among what is binding from now on, and
        verified by test P-3 of the security document.
        """
        for record in self:
            if not record.company_ids:
                raise ValidationError(
                    "A turn carries the user's active companies (D40): without them "
                    "the execution would return a plausible and wrong perimeter."
                )

    def context_for_execution(self) -> dict:
        """The context the Executor must run under, rebuilt from the turn.

        This is the whole point of storing it: on the cron process of D20a there is
        no request to inherit it from.
        """
        self.ensure_one()
        return {
            "allowed_company_ids": self.company_ids.ids,
            "lang": self.lang,
            "tz": self.tz,
        }
