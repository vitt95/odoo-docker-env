/** @odoo-module **/

/**
 * Lo stato della chat, e l'unico punto che parla con il server.
 *
 * Sta tutto qui per una ragione sola: se ogni componente chiedesse i propri dati,
 * aprire una conversazione farebbe partire tre chiamate invece di una, e le tre
 * arriverebbero in ordine imprevedibile. Un punto solo rende l'ordine un fatto invece
 * che una speranza.
 *
 * Le tre regole che tengono la chat senza scatti:
 *
 * 1. **Niente attese sulla propria scrittura.** Quando l'utente invia, il suo
 *    messaggio compare subito, prima che il server risponda. La risposta arrivera'
 *    dopo, e nel frattempo la conversazione e' gia' andata avanti.
 * 2. **Niente interrogazioni a ripetizione.** L'esito arriva dal bus di Odoo quando il
 *    turno si conclude. Un `setInterval` che chiede «e' pronto?» ogni secondo e' lavoro
 *    sprecato su ogni client connesso, e diventa peggiore proprio quando gli utenti
 *    sono tanti.
 * 3. **Niente liste intere.** Conversazioni e turni arrivano a finestre. Il costo di
 *    aprire il pannello non cresce con quanto lo si e' usato.
 */

import { reactive } from "@odoo/owl";

/**
 * Gli avanzamenti arrivati per un turno che il client non ha ancora numerato.
 *
 * `accept_request` restituisce l'identificativo del turno, e il dispatcher puo'
 * cominciare a lavorarlo **prima** che quella risposta arrivi: il primo passo viene
 * emesso appena il turno parte, e viaggia sul bus, che e' un'altra strada con i suoi
 * tempi. Senza questa memoria il primo passo — proprio quello che toglie di mezzo
 * l'attesa muta — si perderebbe nella meta' dei casi, e si perderebbe *di piu'*
 * quando il server e' veloce.
 *
 * Tenerli da parte e riversarli quando il numero arriva costa una mappa con dentro
 * al massimo una manciata di voci, e toglie una corsa che altrimenti si vede.
 */
const MASSIMO_IN_ATTESA = 40;

export class AidaStore {
    constructor(orm, busService, notify) {
        this.orm = orm;
        this.bus = busService;
        this.notify = notify;
        /** Passi arrivati prima del loro turno, per identificativo. */
        this._passiOrfani = new Map();

        this.state = reactive({
            conversations: [],
            hasMoreConversations: false,
            loadingConversations: false,

            currentId: null,
            turns: [],
            hasMoreTurns: false,
            loadingTurns: false,
            /** Turni inviati e non ancora risposti, per identificativo temporaneo. */
            pendingCount: 0,
            /** Testo dello stato d'attesa, mostrato mentre il turno viaggia. */
            waiting: null,
            /**
             * Quello che c'e' nella casella di scrittura.
             *
             * Sta qui e non dentro la casella perche' **anche il clic scrive qui**
             * (D121): scegliere una lettura mette la sua etichetta nella casella e la
             * invia, e da li' in poi e' una frase come le altre. Se la casella si
             * tenesse il testo per se', il clic avrebbe bisogno di una strada propria
             * verso il server — due strade per la stessa cosa, che restano allineate
             * finche' qualcuno se ne ricorda.
             */
            draft: "",
            /** Vero mentre una frase sta partendo. Vale per la casella e per il clic. */
            sending: false,
        });
    }

    /**
     * Quanto si aspetta prima di dire che ci sta mettendo troppo.
     *
     * Misurato su 414 chiamate vere al modello locale: mediana 8,8 s, p95 16,3 s,
     * massimo 40,2 s. Con la riparazione singola di **D15** un turno puo' fare due
     * chiamate, quindi il caso peggiore plausibile sfiora gli ottanta secondi.
     * Novanta lascia margine senza far credere a nessuno che si sia rotto qualcosa
     * mentre sta solo lavorando.
     */
    static ATTESA_MASSIMA_MS = 90_000;

    /** Un identificativo che non puo' collidere con quelli veri, che sono interi. */
    static tempId() {
        return `temp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    }

    async start() {
        // Il canale esiste gia': `nli.queue.item.notify()` lo usa da quando la coda
        // e' asincrona, ed e' documentato proprio come alternativa al polling.
        // Aggiungerne un secondo avrebbe significato due avvisi per un evento solo.
        this.bus.subscribe("nli.turn", (payload) => this._onTurnDone(payload));
        // Il secondo canale: che cosa sta facendo il turno **mentre** lo fa. Sono due
        // messaggi con due destini diversi — questo si puo' perdere senza danno,
        // quello no — e tenerli separati e' cio' che permette di trattarli cosi'.
        this.bus.subscribe("nli.turn.progress", (payload) => this._onTurnProgress(payload));
        this.bus.start();
        await this.loadConversations({ reset: true });
        // Si riapre l'ultima conversazione, come fa una chat: tornare su AIDA e
        // trovare una schermata vuota costringe a ricordarsi dove si era rimasti, e
        // l'elenco e' gia' ordinato per ultima attivita' — la prima e' quella giusta.
        const ultima = this.state.conversations[0];
        if (ultima) {
            await this.open(ultima.id);
        }
    }

    // --- barra laterale ---------------------------------------------------

    async loadConversations({ reset = false } = {}) {
        if (this.state.loadingConversations) {
            return;
        }
        this.state.loadingConversations = true;
        try {
            const offset = reset ? 0 : this.state.conversations.length;
            const data = await this.orm.call(
                "nli.interrogation", "aida_conversations", [], { offset }
            );
            this.state.conversations = reset
                ? data.conversations
                : this.state.conversations.concat(data.conversations);
            this.state.hasMoreConversations = data.has_more;
        } finally {
            this.state.loadingConversations = false;
        }
    }

    async newConversation() {
        const conversation = await this.orm.call("nli.interrogation", "aida_start", []);
        this.state.conversations.unshift(conversation);
        this.state.currentId = conversation.id;
        this.state.turns = [];
        this.state.hasMoreTurns = false;
        return conversation;
    }

    async rename(id, title) {
        const updated = await this.orm.call("nli.interrogation", "aida_rename", [[id], title]);
        const found = this.state.conversations.find((c) => c.id === id);
        if (found) {
            found.title = updated.title;
        }
    }

    async remove(id) {
        await this.orm.call("nli.interrogation", "aida_delete", [[id]]);
        this.state.conversations = this.state.conversations.filter((c) => c.id !== id);
        if (this.state.currentId === id) {
            this.state.currentId = null;
            this.state.turns = [];
        }
    }

    // --- conversazione aperta ---------------------------------------------

    async open(id) {
        if (this.state.currentId === id) {
            return;
        }
        this.state.currentId = id;
        this.state.turns = [];
        this.state.waiting = null;
        // La casella appartiene alla conversazione: una risposta scritta qui e inviata
        // altrove risponderebbe a una domanda che non e' stata posta.
        this.state.draft = "";
        await this.loadTurns({ reset: true });
    }

    async loadTurns({ reset = false } = {}) {
        const id = this.state.currentId;
        if (!id || this.state.loadingTurns) {
            return;
        }
        this.state.loadingTurns = true;
        try {
            // Si pagina per identificativo del turno piu' vecchio che abbiamo, non per
            // scostamento: uno scostamento si sposta quando arriva un turno nuovo, ed
            // e' cosi' che una cronologia mostra due volte lo stesso messaggio.
            const oldest = reset ? null : this.state.turns.find((t) => Number.isInteger(t.id));
            const data = await this.orm.call(
                "nli.interrogation", "aida_turns", [[id]],
                { before_id: oldest ? oldest.id : false }
            );
            if (this.state.currentId !== id) {
                return; // L'utente ha cambiato conversazione mentre leggevamo.
            }
            this.state.turns = reset ? data.turns : data.turns.concat(this.state.turns);
            this.state.hasMoreTurns = data.has_more;
        } finally {
            this.state.loadingTurns = false;
        }
    }

    /**
     * Scrive una frase nella casella. E' cio' che fa il clic su una lettura (D121).
     */
    setDraft(text) {
        this.state.draft = text || "";
    }

    /**
     * Invia quello che c'e' nella casella, e la svuota.
     *
     * **Unico punto di partenza di una frase.** Ci passa chi scrive e chi clicca, per
     * costruzione: non esiste un secondo modo di far partire un turno, quindi non
     * esiste un secondo modo che possa comportarsi diversamente.
     *
     * La guardia sul doppio invio sta **qui** e non nella casella per la stessa
     * ragione: un doppio clic su una lettura manderebbe due turni identici, e una
     * guardia che protegge una sola delle due strade protegge quella che nessuno usa
     * per sbaglio.
     */
    async submitDraft() {
        if (this.state.sending || !this.state.draft.trim()) {
            return;
        }
        const testo = this.state.draft;
        this.state.draft = "";
        this.state.sending = true;
        try {
            await this.send(testo);
        } finally {
            this.state.sending = false;
        }
    }

    /**
     * Invia una domanda. Il messaggio compare subito; la risposta arrivera' dal bus.
     */
    async send(utterance) {
        const testo = (utterance || "").trim();
        if (!testo) {
            return;
        }
        if (!this.state.currentId) {
            await this.newConversation();
        }
        const conversationId = this.state.currentId;

        const provvisorio = {
            id: AidaStore.tempId(),
            utterance: testo,
            outcome: "",
            interpretation: null,
            record_count: 0,
            executed_at: false,
            pending: true,
            /**
             * I passi che il server annuncia mentre lavora.
             *
             * Nasce vuoto e non `null`: il componente che lo disegna non deve avere
             * due casi da distinguere, e «nessun passo ancora» e «nessun passo mai»
             * si disegnano uguali — l'attesa senza elenco.
             */
            steps: [],
            /** Vero quando l'elenco si e' chiuso perche' la risposta e' arrivata. */
            stepsCollapsed: false,
        };
        this.state.turns.push(provvisorio);
        this.state.pendingCount += 1;
        this.state.waiting = "accepted";

        const esito = await this.orm.call(
            "nli.queue.item", "accept_request", [conversationId, testo]
        );

        if (!esito.accepted) {
            // Un rifiuto per carico e' una risposta, non un errore da nascondere
            // (D69): il turno resta visibile e dice perche' non e' partito.
            provvisorio.pending = false;
            provvisorio.outcome = "refused";
            provvisorio.interpretation = { refusal: esito.reason, retry_after: esito.retry_after };
            this.state.pendingCount -= 1;
            this.state.waiting = null;
            return;
        }
        // Da qui in poi il turno ha un identificativo vero: la notifica lo trovera'.
        provvisorio.id = esito.turn_id;
        this._riversaPassi(provvisorio);
        this.state.waiting = "interpreting";
        this._touch(conversationId, testo);
        this._armaLaSveglia(provvisorio);
    }

    /**
     * Smette di aspettare dopo un tempo, e lo dice.
     *
     * Il turno viaggia su una coda e un processo separato, quindi la risposta puo'
     * non arrivare: il modello e' lento, il turno scade in coda (L4), il processo
     * muore. Il server se ne accorge, ma il recupero degli orfani guarda ogni cinque
     * minuti — che per un server e' ragionevole e davanti a una chat e' un'eternita'.
     *
     * Senza questa sveglia l'animazione dell'attesa girava all'infinito, ed e'
     * peggio di un errore: un errore si legge e si decide, un'attesa senza fine si
     * fissa. Qui l'attesa ha un limite, e alla scadenza si dice cosa e' successo e
     * cosa si puo' fare.
     *
     * Non annulla niente sul server: il turno puo' ancora concludersi, e se lo fa la
     * notifica arriva lo stesso e sostituisce questo messaggio. E' una sveglia per
     * chi guarda, non un ordine di smettere.
     */
    _armaLaSveglia(turno) {
        const atteso = AidaStore.ATTESA_MASSIMA_MS;
        setTimeout(() => {
            if (!turno.pending) {
                return;
            }
            turno.slow = true;
        }, atteso);
    }

    /** Porta la conversazione in cima e le da' un titolo se non ne aveva. */
    _touch(conversationId, firstUtterance) {
        const indice = this.state.conversations.findIndex((c) => c.id === conversationId);
        if (indice === -1) {
            return;
        }
        const [conversazione] = this.state.conversations.splice(indice, 1);
        if (!conversazione.title) {
            conversazione.title = firstUtterance.slice(0, 60);
        }
        conversazione.turn_count += 1;
        this.state.conversations.unshift(conversazione);
    }

    /**
     * Un turno è finito (D124).
     *
     * L'avviso dice **che** è finito, non cosa dice: la risposta si chiede al server,
     * che la costruisce con la stessa funzione che serve la cronologia. Prima l'avviso
     * portava anche l'interpretazione, ed era la seconda strada verso questo schermo —
     * quella che portava la struttura invece delle parole, e per cui nessuna risposta
     * riuscita è mai comparsa.
     */
    async _onTurnDone(payload) {
        // L'avviso arriva per ogni turno dell'utente, anche di conversazioni che non
        // sta guardando: quelle si ignorano qui invece di ridisegnare qualcosa che
        // nessuno vede.
        if (payload.interrogation_id !== this.state.currentId) {
            return;
        }
        const turno = this.state.turns.find((t) => t.id === payload.turn_id);
        if (!turno) {
            return;
        }
        let completo = null;
        try {
            completo = await this.orm.call(
                "nli.interrogation", "aida_turn",
                [[this.state.currentId], payload.turn_id]);
        } catch {
            // Se la lettura non riesce, l'attesa non deve restare accesa per sempre:
            // si mostra l'esito che l'avviso portava, che è poco ma è vero.
        }
        // I passi non stanno nel payload del server e non devono sparire: quello che
        // arriva descrive il turno **concluso**, e `Object.assign` sovrascriverebbe
        // solo le chiavi che porta. Si conservano e si chiudono, perche' «Completati
        // sei passi» e' l'unico modo di poter tornare a guardare come ci è arrivato.
        const passi = turno.steps || [];
        Object.assign(turno, completo || { outcome: payload.outcome });
        turno.steps = passi;
        turno.stepsCollapsed = true;
        turno.pending = false;
        this.state.pendingCount = Math.max(0, this.state.pendingCount - 1);
        this.state.waiting = this.state.pendingCount > 0 ? this.state.waiting : null;
        this._passiOrfani.delete(payload.turn_id);
    }

    /**
     * Un passo di un turno in corso.
     *
     * **Il passo si scarta, il turno no.** Un avanzamento perso non toglie niente
     * alla risposta: e' cortesia, e la cortesia che non arriva non e' un guasto. Per
     * questo qui non c'e' nessun tentativo di recupero, nessuna richiesta al server
     * e nessun errore mostrato — sarebbero tutte cose che costano di piu' di quello
     * che proteggono.
     */
    _onTurnProgress(payload) {
        if (payload.interrogation_id !== this.state.currentId) {
            return;
        }
        const turno = this.state.turns.find((t) => t.id === payload.turn_id);
        if (!turno) {
            // Il passo ha battuto la risposta di `accept_request`: si tiene da parte
            // finche' il turno non ha il suo numero. Vedi `MASSIMO_IN_ATTESA`.
            this._ricordaOrfano(payload);
            return;
        }
        if (!turno.pending) {
            return; // Arrivato dopo la risposta: non ha piu' niente da annunciare.
        }
        this._aggiungiPasso(turno, payload);
    }

    _aggiungiPasso(turno, payload) {
        // L'indice arriva dal server e non si ricalcola qui: e' lui a sapere quanti
        // ne ha mandati, e due passi con lo stesso numero vorrebbero dire che il bus
        // ne ha consegnato uno due volte — cosa che puo' succedere, e che si scarta.
        if (turno.steps.some((passo) => passo.index === payload.index)) {
            return;
        }
        turno.steps.push({
            index: payload.index,
            step: payload.step,
            detail: payload.detail || "",
        });
        // Il bus non promette l'ordine. Ordinare qui costa niente su una manciata di
        // voci, e toglie di mezzo un elenco che racconta il lavoro al contrario.
        turno.steps.sort((a, b) => a.index - b.index);
    }

    _ricordaOrfano(payload) {
        const attesa = this._passiOrfani.get(payload.turn_id) || [];
        attesa.push(payload);
        this._passiOrfani.set(payload.turn_id, attesa);
        // Un tetto, perche' una mappa che cresce senza limite in una scheda lasciata
        // aperta tutto il giorno e' una perdita di memoria con un'altra faccia. Il
        // caso vero e' una voce sola: qualunque numero ben oltre e' sufficiente.
        if (this._passiOrfani.size > MASSIMO_IN_ATTESA) {
            this._passiOrfani.delete(this._passiOrfani.keys().next().value);
        }
    }

    /** Riversa nel turno i passi che erano arrivati prima del suo numero. */
    _riversaPassi(turno) {
        const attesa = this._passiOrfani.get(turno.id);
        if (!attesa) {
            return;
        }
        this._passiOrfani.delete(turno.id);
        for (const payload of attesa) {
            this._aggiungiPasso(turno, payload);
        }
    }
}
