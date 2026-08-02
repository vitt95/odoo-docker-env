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

export class AidaStore {
    constructor(orm, busService, notify) {
        this.orm = orm;
        this.bus = busService;
        this.notify = notify;

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
        });
    }

    /** Un identificativo che non puo' collidere con quelli veri, che sono interi. */
    static tempId() {
        return `temp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    }

    async start() {
        // Il canale esiste gia': `nli.queue.item.notify()` lo usa da quando la coda
        // e' asincrona, ed e' documentato proprio come alternativa al polling.
        // Aggiungerne un secondo avrebbe significato due avvisi per un evento solo.
        this.bus.subscribe("nli.turn", (payload) => this._onTurnDone(payload));
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
        this.state.waiting = "interpreting";
        this._touch(conversationId, testo);
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

    _onTurnDone(payload) {
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
        Object.assign(turno, {
            outcome: payload.outcome,
            interpretation: payload.interpretation,
            record_count: payload.record_count,
            executed_at: payload.executed_at,
        });
        turno.pending = false;
        this.state.pendingCount = Math.max(0, this.state.pendingCount - 1);
        this.state.waiting = this.state.pendingCount > 0 ? this.state.waiting : null;
    }
}
