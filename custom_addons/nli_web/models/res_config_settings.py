"""La sezione AIDA nelle impostazioni generali.

## Perche' e' qui e non nel motore

`nli_engine` possiede il profilo, ma la sua responsabilita' dichiarata e' *interprete e
adattatori*, e non dichiara nessuna dipendenza dalla piattaforma: ci arriva attraverso
il nucleo. Un pannello di amministrazione e' interfaccia, e l'interfaccia sta in
`nli_web`. Cosi' il motore resta una cosa che si puo' esercitare senza Odoo davanti,
che e' il motivo per cui i suoi test girano in millisecondi.

## Cosa fa, e cosa non fa

Fa: raccoglie in un posto solo i parametri del modello con cui AIDA parla — dove sta,
come si chiama, quanto testo regge, se sa generare in modo vincolato, quanto deve
ragionare. Sono i campi di **D78** (il profilo dichiara le proprie capacita'), che
finora si potevano scrivere solo da codice.

**Non fa**: attivare il profilo di nascosto. Il pannello scrive su una bozza e mostra i
due pulsanti del percorso vero — qualifica e attivazione — che restano quelli di
sempre. **D80** (un profilo mai qualificato non puo' essere attivato) continua a
rifiutare, e il rifiuto arriva all'amministratore come messaggio invece che come
silenzio.

Questa e' la parte che vale la pena non sbagliare. Una sezione delle impostazioni che
avesse scritto `state = "active"` avrebbe reso il cancello una formalita' aggirabile
con due clic — e il cancello esiste perche' un modello non qualificato puo' degradare
l'ERP per tutti, non solo per chi lo ha scelto.
"""

from __future__ import annotations

from odoo import api, fields, models

#: I campi che descrivono il modello. Elencati una volta sola: il pannello li legge e
#: li riscrive tutti insieme, e due elenchi che divergono sono un campo che si perde.
CAMPI_PROFILO = (
    "endpoint", "model_name", "context_window", "timeout_seconds",
    "constrained_generation", "reasoning_effort",
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    #: Campi normali, non calcolati. `res.config.settings` costruisce il proprio
    #: record con `default_get`, che **non esegue i calcoli**: un campo `compute` qui
    #: si presenta vuoto nel pannello anche quando il valore c'e', e l'ho visto —
    #: `create({})` restituiva i valori giusti mentre la pagina mostrava caselle
    #: vuote. Riempirli in `default_get` e riscriverli in `set_values` e' il modo che
    #: la piattaforma usa per se stessa, e non dipende da quando girano i calcoli.
    aida_profile_id = fields.Many2one("nli.profile", string="Profilo del modello",
                                      readonly=True)
    aida_profile_state = fields.Selection(
        selection=[("draft", "Bozza"), ("qualified", "Qualificato"),
                   ("active", "In servizio"), ("retired", "Ritirato")],
        string="Stato", readonly=True)

    aida_endpoint = fields.Char(
        string="Indirizzo del modello",         help="Per esempio http://host.docker.internal:11434/v1 per un ollama che gira "
             "sulla macchina che ospita Odoo.")
    aida_model_name = fields.Char(
        string="Nome del modello")
    aida_context_window = fields.Integer(
        string="Finestra di contesto",         help="Quanti gettoni regge il modello (D78). Da qui si ricava il budget del "
             "catalogo, quindi un valore ottimistico si paga in risposte troncate.")
    aida_timeout_seconds = fields.Integer(
        string="Tempo concesso per rispondere (secondi)",
        help="Quanto si aspetta una risposta del modello (D122). Un modello da nove "
             "miliardi di parametri sul processore di un portatile impiega minuti; uno "
             "ospitato altrove impiega secondi. Se questo valore e' piu' corto di "
             "quanto il modello impiega davvero, **ogni** domanda finisce con «il "
             "modello non ha risposto».")
    aida_debug = fields.Boolean(
        string="Modalità diagnostica",
        help="Ogni turno conserva e mostra come è stato costruito: la busta DSL che il "
             "modello ha restituito, lo stato che ne è uscito e **la query** con cui "
             "Odoo è stato interrogato, con i tempi di ogni fase (D123). Serve a capire "
             "se un turno è andato storto nel modello o dopo. Da tenere spenta quando "
             "non serve: accesa, ogni turno conserva la frase dell'utente dentro la "
             "busta, e la traccia la vede solo un amministratore.")
    aida_constrained_generation = fields.Boolean(
        string="Generazione vincolata",         help="Il modello sa rispettare uno schema JSON imposto. Senza, l'interprete "
             "riceve testo libero e la maggior parte dei turni fallisce.")
    aida_reasoning_effort = fields.Selection(
        selection=[("none", "Nessuno"), ("minimal", "Minimo"), ("low", "Basso"),
                   ("medium", "Medio"), ("high", "Alto")],
        string="Sforzo di ragionamento",         help="D98: dichiararlo e' obbligatorio per i modelli che ragionano. Con una "
             "finestra stretta, un ragionamento alto consuma lo spazio della risposta "
             "e la busta torna vuota.")

    # --- lettura -----------------------------------------------------------

    def _profilo(self):
        """Il profilo che il pannello configura.

        L'attivo se c'e'; altrimenti l'ultimo creato, che e' quello che
        l'amministratore stava preparando. Mai crearne uno qui dentro: `_compute` gira
        anche solo aprendo le impostazioni, e aprire una pagina non deve lasciare
        record in giro.
        """
        profilo = self.env["nli.profile"].active_profile()
        return profilo or self.env["nli.profile"].search([], order="id desc", limit=1)

    @api.model
    def default_get(self, campi):
        valori = super().default_get(campi)
        profilo = self._profilo()
        valori["aida_profile_id"] = profilo.id if profilo else False
        valori["aida_profile_state"] = profilo.state if profilo else False
        for campo in CAMPI_PROFILO:
            valori[f"aida_{campo}"] = profilo[campo] if profilo else False
        valori["aida_debug"] = self.env["nli.dispatcher"]._debug_enabled()
        return valori

    # --- scrittura ---------------------------------------------------------

    def set_values(self):
        """Scrive i parametri sul profilo, creandolo alla prima configurazione.

        Il profilo nasce **in bozza**, come vuole la macchina a stati: la
        qualificazione (D51) e l'attivazione (D80) restano due azioni esplicite, e
        questa non le anticipa.
        """
        super().set_values()
        for impostazioni in self:
            # D123: parametro di sistema e non campo del profilo — non e' una proprieta'
            # del modello, e' una scelta di chi sta guardando.
            # Senza `sudo` (V2): il pannello delle impostazioni lo apre solo un
            # amministratore, che il parametro puo' gia' scriverlo.
            self.env["ir.config_parameter"].set_param(
                "aida.debug", "True" if impostazioni.aida_debug else "False")
            valori = {campo: impostazioni[f"aida_{campo}"] for campo in CAMPI_PROFILO}
            profilo = impostazioni._profilo()
            if profilo:
                profilo.write(valori)
                continue
            if not valori.get("endpoint") or not valori.get("model_name"):
                # Niente da salvare: aprire e chiudere le impostazioni senza toccare
                # nulla non deve creare un profilo vuoto che poi qualcuno trova e non
                # sa da dove viene.
                continue
            self.env["nli.profile"].create({
                "name": valori["model_name"],
                "protocol": "openai_compatible",
                **valori,
            })

    # --- le due azioni del percorso vero ------------------------------------

    def action_aida_qualify(self):
        """Registra che il protocollo di D51 e' stato eseguito.

        Non lo esegue: lo **registra**. La differenza e' tutta, e per questo il
        pulsante chiede una nota — chi la scrive sta dichiarando di aver fatto le otto
        verifiche, e quella dichiarazione resta sul profilo con la sua data.
        """
        self.ensure_one()
        profilo = self._profilo()
        if profilo:
            profilo.action_qualify()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_aida_activate(self):
        """Attiva il profilo qualificato. Rifiutata da D80 se non lo e'."""
        self.ensure_one()
        profilo = self._profilo()
        if profilo:
            profilo.action_activate()
        return {"type": "ir.actions.client", "tag": "reload"}
