/** @odoo-module **/

/**
 * L'azione client di AIDA: barra laterale, conversazione, casella di scrittura.
 *
 * Il montaggio e' volutamente povero: un componente radice che tiene lo store e tre
 * figli che leggono da li'. Ogni figlio disegna una parte sola dello stato, quindi un
 * messaggio nuovo ridisegna il filo dei messaggi e **non** la barra laterale.
 */

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { AidaStore } from "./aida_store";
import { AidaSidebar } from "./aida_sidebar";
import { AidaThread } from "./aida_thread";
import { AidaComposer } from "./aida_composer";

export class AidaChat extends Component {
    static template = "nli_web.AidaChat";
    static components = { AidaSidebar, AidaThread, AidaComposer };
    static props = {
        "*": true,
    };

    setup() {
        const orm = useService("orm");
        const bus = useService("bus_service");
        this.store = new AidaStore(orm, bus);
        this.state = useState(this.store.state);
        this.ui = useState({ sidebarOpen: true });

        onWillStart(() => this.store.start());
    }

    get currentConversation() {
        return this.state.conversations.find((c) => c.id === this.state.currentId);
    }

    get isEmpty() {
        return !this.state.currentId || this.state.turns.length === 0;
    }

    toggleSidebar() {
        this.ui.sidebarOpen = !this.ui.sidebarOpen;
    }
}

registry.category("actions").add("nli_web.chat", AidaChat);
