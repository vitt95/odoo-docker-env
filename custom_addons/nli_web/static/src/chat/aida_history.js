/** @odoo-module **/

/**
 * Le conversazioni, in un pannello che entra da sinistra.
 *
 * ## Perché non è una colonna fissa
 *
 * Nella versione a pagina intera l'elenco stava sempre lì, e ci stava: c'era tutta
 * la larghezza dello schermo. Dentro una colonna da quattrocentoquaranta pixel una
 * barra laterale permanente lascerebbe alla conversazione meno di trecento — sotto
 * la soglia in cui una riga di testo si legge invece di scansionarsi.
 *
 * Quindi copre la conversazione quando serve e se ne va quando non serve più. È lo
 * stesso compromesso del riferimento, e nasce dallo stesso vincolo: chi apre la
 * cronologia sta cercando *un'altra* conversazione, quindi in quel momento non gli
 * serve vedere questa.
 *
 * ## Perché carica a finestre
 *
 * Un utente che usa il prodotto da un anno ha centinaia di sessioni. Disegnarle
 * tutte per mostrarne dodici è lavoro che si paga a ogni apertura del pannello, e si
 * paga di più proprio a chi lo usa di più.
 */

import { Component, useState } from "@odoo/owl";

export class AidaHistory extends Component {
    static template = "nli_web.AidaHistory";
    static props = {
        store: Object,
        state: Object,
        onOpen: Function,
        onClose: Function,
    };

    setup() {
        this.ui = useState({ renamingId: null, draftTitle: "" });
    }

    /** Chiede la pagina successiva quando mancano meno di due schermate al fondo. */
    onScroll(ev) {
        const el = ev.target;
        if (!this.props.state.hasMoreConversations || this.props.state.loadingConversations) {
            return;
        }
        if (el.scrollHeight - el.scrollTop - el.clientHeight < el.clientHeight * 2) {
            this.props.store.loadConversations();
        }
    }

    startRename(conversation) {
        this.ui.renamingId = conversation.id;
        this.ui.draftTitle = conversation.title || "";
    }

    async confirmRename() {
        const id = this.ui.renamingId;
        if (id) {
            await this.props.store.rename(id, this.ui.draftTitle);
        }
        this.ui.renamingId = null;
    }

    onRenameKeydown(ev) {
        if (ev.key === "Enter") {
            this.confirmRename();
        } else if (ev.key === "Escape") {
            // Si ferma qui: senza, `Escape` arriverebbe anche alla scorciatoia del
            // pannello e annullare una rinomina chiuderebbe AIDA.
            ev.stopPropagation();
            this.ui.renamingId = null;
        }
    }

    async remove(conversation) {
        // Cancellare una conversazione cancella anche le frasi che vi sono dentro
        // (D115 le conserva in chiaro), quindi la domanda è dovuta: è l'unico modo
        // che l'utente ha di ritirare le proprie parole.
        const testo = conversation.title || "questa conversazione";
        if (!window.confirm(`Eliminare «${testo}» e tutti i suoi messaggi?`)) {
            return;
        }
        await this.props.store.remove(conversation.id);
    }
}
