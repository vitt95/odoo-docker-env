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

    def aida_turn(self, turn_id: int):
        """Un turno solo, quello appena finito (D124).

        **Perche' esiste invece di far portare la risposta all'avviso.** L'avviso sul
        bus lo costruisce `nli_dispatch`, il payload della chat lo costruisce
        `_aida_payload` qui: erano due strade verso lo stesso schermo, e sono
        divergute — l'avviso portava l'interpretazione strutturata, il template si
        aspettava le parole, e per mesi **nessun turno riuscito e' stato disegnato**.
        Ora l'avviso porta un identificativo e basta, e cio' che si disegna lo
        costruisce una funzione sola.
        """
        self.ensure_one()
        turno = self.env["nli.turn"].search(
            [("id", "=", turn_id), ("interrogation_id", "=", self.id)], limit=1)
        return turno._aida_payload() if turno else None


class NliTurn(models.Model):
    _inherit = "nli.turn"

    def _aida_payload(self) -> dict:
        """Il turno come lo disegna la chat: la domanda, la risposta, i numeri.

        Niente di piu': lo stato completo pesa e nella cronologia non si guarda. Chi
        vuole rieseguire il turno lo ricarica quando serve.
        """
        self.ensure_one()
        payload = {
            "id": self.id,
            "utterance": self.utterance or "",
            "outcome": self.outcome or "",
            "interpretation": self._aida_interpretation(),
            "record_count": self.record_count,
            "executed_at": fields.Datetime.to_string(self.executed_at),
            # Un turno senza esito e' in corso: il client mostra l'attesa e aspetta
            # la notifica, invece di interrogare il server a ripetizione.
            "pending": not self.outcome,
        }
        query = self._aida_query()
        if query is not None:
            payload["query"] = query
        traccia = self._aida_debug()
        if traccia is not None:
            payload["debug"] = traccia
        return payload

    def _aida_query(self):
        """Gli argomenti con cui la chat costruisce la tabella dei record (D124).

        **Il dominio esce, i record no.** La vista lista di Odoo li rilegge da sola con
        i diritti di chi guarda, quindi un dominio che tornasse indietro da un utente a
        cui e' stato tolto un permesso non gli farebbe vedere niente di piu' di quanto
        vedrebbe aprendo il menu. E' `00` §23: si incorpora la vista nativa invece di
        riscrivere tabella, ricerca, colonne e paginazione — che e' cio' che `15`
        chiede, ottenuto senza reimplementarlo.
        """
        self.ensure_one()
        if self.outcome != "operations" or not self.plan_json:
            return None
        try:
            piano = json.loads(self.plan_json)
        except ValueError:
            return None
        return {
            "model": piano.get("model"),
            "domain": piano.get("domain") or [],
            "fields": piano.get("fields") or [],
            "group_by": piano.get("group_by") or [],
            "order": piano.get("order") or "",
            "limit": piano.get("limit"),
            "view": piano.get("view") or "list",
            # Le misure, che il piano porta come coppie `[funzione, campo]`. Servono
            # alla vista pivot e al grafico, che senza ricadono sul conteggio — e
            # l'interpretazione sopra la tabella dice «media», non «quante».
            "measures": [{"function": funzione, "field": campo}
                         for funzione, campo in (piano.get("measures") or [])],
        }

    def _aida_interpretation(self):
        """L'interpretazione come la legge una persona (D124).

        Il Presentatore produce una **struttura**: bersaglio, condizioni, periodi
        risolti, riferimenti. Trasformarla in frasi e' `09` §3, e lo fa
        `nli.interpretation.in_words`. Nessuno lo chiamava: il turno memorizzava la
        struttura, il template cercava le parole, e ogni risposta riuscita finiva nel
        ramo di scarto. Qui e' l'unico punto in cui una risposta diventa qualcosa da
        guardare, quindi e' l'unico punto in cui la conversione puo' mancare.

        **Le parole si costruiscono alla lettura e non alla scrittura**, perche' i
        termini vengono dal catalogo dell'utente che sta leggendo: due persone con
        permessi diversi vedono lo stesso turno con vocabolari diversi, ed e' la stessa
        ragione per cui il catalogo non si mette in cache fra utenti (D39).
        """
        self.ensure_one()
        interpretazione = json.loads(self.interpretation_json or "null")
        if not isinstance(interpretazione, dict) or "target" not in interpretazione:
            # Un chiarimento o un rifiuto: portano gia' la forma che il client legge.
            return interpretazione
        return self.env["nli.interpretation"].in_words(
            interpretazione, catalogue=self._aida_catalogue(interpretazione))

    def _aida_catalogue(self, interpretazione):
        """Il catalogo dell'entita' del turno, per dire le cose con le parole di casa.

        Se non si riesce a costruirlo — permessi cambiati, entita' sparita da un
        aggiornamento — si va avanti senza: `in_words` degrada mostrando l'ultimo pezzo
        del riferimento invece del riferimento intero, che e' brutto ma leggibile. Una
        cronologia che non si apre perche' un turno di marzo nomina un campo che non
        c'e' piu' sarebbe molto peggio.
        """
        riferimento = (interpretazione.get("target") or {}).get("ref")
        if not riferimento:
            return None
        try:
            semantica = self.env["nli.semantics"].semantics(
                self.env["nli.semantics"].entity_scope())
            return self.env["nli.semantics"].catalogue_for(
                semantica, riferimento,
                context_window=self.env["nli.dispatcher"]._context_window())
        except Exception:  # noqa: BLE001 — vedi il docstring
            return None

    def _aida_debug(self):
        """La traccia di D123, a chi puo' vederla.

        **Due condizioni, non una.** Che la traccia esista sul turno vuol dire che
        qualcuno aveva acceso la modalita' diagnostica quando il turno e' corso; che si
        possa vedere adesso e' una domanda diversa, e la risposta e' *solo un
        amministratore*. Un utente ordinario che si trovasse davanti il dominio Odoo e
        i riferimenti del catalogo non ne ricaverebbe niente, e li vedrebbe per sempre
        perche' la traccia resta scritta sul turno anche dopo che l'interruttore e'
        stato rimesso a posto.
        """
        self.ensure_one()
        if not self.debug_json:
            return None
        if not self.env.user.has_group("base.group_system"):
            return None
        try:
            return json.loads(self.debug_json)
        except ValueError:
            # Una traccia illeggibile non deve impedire di leggere la conversazione:
            # e' uno strumento diagnostico, non un pezzo della risposta.
            return None
