"""L'API che la chat chiama, disegnata perche' il client non debba mai aspettare.

## Perche' i metodi stanno qui e non nel client

Il documento `15` chiede una conversazione che non abbia latenza percepibile. La
latenza percepibile non nasce quasi mai dal calcolo: nasce dal **numero di andate e
ritorni** e dalla **quantita' di roba** che ognuno porta. Quindi ogni metodo qui
restituisce esattamente cio' che una schermata disegna, in una chiamata sola, e mai un
record intero.

Tre scelte, ognuna con la sua ragione:

* **La barra laterale non carica tutte le conversazioni.** Ne carica una finestra e
  chiede la successiva quando serve. Un utente con mille sessioni non e' un caso
  limite: e' un utente che usa il prodotto da un anno.
* **La cronologia si apre dal fondo.** Si leggono gli ultimi turni, non tutti, e i piu'
  vecchi arrivano scorrendo all'insu'. E' come si apre una chat, ed e' anche l'unico
  modo perche' il costo di riaprire una conversazione non cresca con la sua eta'.
* **Niente si ricalcola in lettura.** La risposta impaginata e' gia' sul turno
  (`interpretation_json`, scritta dal lavoratore quando il turno si e' concluso).
  Riderivarla vorrebbe dire ricostruire catalogo, diritti e istante di allora: aprire
  una conversazione costerebbe quanto eseguirla.

## Cosa non fa

Non filtra per utente a mano. Le regole di record di `nli.interrogation` e `nli.turn`
lo fanno gia', e una seconda via alla stessa informazione con guardie diverse e'
esattamente il modo in cui una di quelle due si dimentica.
"""

from __future__ import annotations

import json

from odoo import api, fields, models

#: Quante conversazioni per pagina nella barra laterale. Trenta riempiono uno schermo
#: alto senza costringere a una seconda chiamata prima che l'utente scorra.
CONVERSATIONS_PAGE = 30

#: Quanti turni si leggono aprendo una conversazione. Venti coprono la parte che si
#: guarda subito; il resto arriva scorrendo.
TURNS_PAGE = 20

#: Lunghezza massima del titolo derivato dalla prima frase.
TITLE_LENGTH = 60


class NliInterrogation(models.Model):
    _inherit = "nli.interrogation"

    #: Il titolo mostrato nella barra laterale. `name` resta cio' che era — il nome
    #: che l'utente da' a una **query salvata** (§9.5) — e questo e' un'altra cosa: il
    #: titolo di una conversazione, che nasce da solo dalla prima frase e che l'utente
    #: puo' cambiare. Tenerli separati evita che rinominare una chat trasformi una
    #: conversazione viva in una query salvata senza che nessuno l'abbia chiesto.
    title = fields.Char()

    def _display_title(self) -> str:
        self.ensure_one()
        if self.title:
            return self.title
        prima = self.turn_ids[:1].utterance or ""
        prima = " ".join(prima.split())
        if not prima:
            return ""
        return prima[:TITLE_LENGTH] + ("…" if len(prima) > TITLE_LENGTH else "")

    # --- la barra laterale --------------------------------------------------

    @api.model
    def aida_conversations(self, limit: int = CONVERSATIONS_PAGE, offset: int = 0):
        """Una finestra di conversazioni, gia' ordinate per ultima attivita'.

        `_order` del modello e' `write_date desc`, che e' esattamente l'ordinamento
        che il documento chiede: la conversazione toccata per ultima sta in cima senza
        che nessuno debba ordinare niente.
        """
        conversazioni = self.search([], limit=limit, offset=offset)
        return {
            "conversations": [
                {
                    "id": c.id,
                    "title": c._display_title(),
                    "last_activity": fields.Datetime.to_string(c.write_date),
                    "turn_count": c.turn_count,
                }
                for c in conversazioni
            ],
            # Il client sa se ha senso chiedere ancora senza dover contare tutto.
            "has_more": len(conversazioni) == limit,
        }

    @api.model
    def aida_start(self):
        """Una conversazione nuova, vuota. Il titolo arrivera' dalla prima frase."""
        conversazione = self.create({})
        return {"id": conversazione.id, "title": "", "turn_count": 0,
                "last_activity": fields.Datetime.to_string(conversazione.write_date)}

    def aida_rename(self, title: str):
        self.ensure_one()
        self.title = (title or "").strip()[:TITLE_LENGTH * 4]
        return {"id": self.id, "title": self._display_title()}

    def aida_delete(self):
        """Elimina la conversazione e tutto ciò che le appartiene.

        I turni cadono con lei — `ondelete="cascade"` sul turno — e con i turni cadono
        le frasi che D115 conserva in chiaro. E' l'unico modo che l'utente ha di
        cancellare le proprie parole, quindi non e' un dettaglio dell'interfaccia.
        """
        self.ensure_one()
        self.unlink()
        return True

    # --- la conversazione aperta -------------------------------------------

    def aida_turns(self, limit: int = TURNS_PAGE, before_id: int | None = None):
        """Una finestra di turni, dal piu' recente all'indietro.

        `before_id` e' il turno piu' vecchio che il client ha gia': si chiede cio' che
        viene prima. Si pagina per identificativo e non per scostamento perche' uno
        scostamento si sposta sotto i piedi quando arriva un turno nuovo, ed e' il modo
        in cui una cronologia mostra due volte lo stesso messaggio.
        """
        self.ensure_one()
        dominio = [("interrogation_id", "=", self.id)]
        if before_id:
            dominio.append(("id", "<", before_id))
        turni = self.env["nli.turn"].search(dominio, order="id desc", limit=limit)
        return {
            "turns": [t._aida_payload() for t in reversed(turni)],
            "has_more": len(turni) == limit,
        }


class NliTurn(models.Model):
    _inherit = "nli.turn"

    def _aida_payload(self) -> dict:
        """Il turno come lo disegna la chat: la domanda, la risposta, i numeri.

        Niente di piu': lo stato completo pesa e nella cronologia non si guarda. Chi
        vuole rieseguire il turno lo ricarica quando serve.
        """
        self.ensure_one()
        return {
            "id": self.id,
            "utterance": self.utterance or "",
            "outcome": self.outcome or "",
            "interpretation": json.loads(self.interpretation_json or "null"),
            "record_count": self.record_count,
            "executed_at": fields.Datetime.to_string(self.executed_at),
            # Un turno senza esito e' in corso: il client mostra l'attesa e aspetta
            # la notifica, invece di interrogare il server a ripetizione.
            "pending": not self.outcome,
        }
