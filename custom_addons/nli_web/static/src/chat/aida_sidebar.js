/** @odoo-module **/

/**
 * L'elenco delle conversazioni.
 *
 * Carica una finestra alla volta e chiede la successiva quando lo scorrimento arriva
 * in fondo. Non si carica tutto: un utente che usa il prodotto da un anno ha centinaia
 * di sessioni, e disegnarle tutte per mostrarne dodici e' lavoro che si paga a ogni
 * apertura del pannello.
 */

import { Component, useState } from "@odoo/owl";

export class AidaSidebar extends Component {
    static template = "nli_web.AidaSidebar";
    static props = {
        store: Object,
        state: Object,
        onOpen: Function,
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
            this.ui.renamingId = null;
        }
    }

    async remove(conversation) {
        // Cancellare una conversazione cancella anche le frasi che vi sono dentro
        // (D115 le conserva in chiaro), quindi la domanda e' dovuta: e' l'unico modo
        // che l'utente ha di ritirare le proprie parole.
        const testo = conversation.title || this.env._t("questa conversazione");
        if (!window.confirm(`Eliminare «${testo}» e tutti i suoi messaggi?`)) {
            return;
        }
        await this.props.store.remove(conversation.id);
    }
}
