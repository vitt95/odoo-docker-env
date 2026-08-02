/** @odoo-module **/

/**
 * La casella dove si scrive.
 *
 * L'invio non aspetta il server: il messaggio compare, la casella si svuota, e si può
 * già scrivere il successivo. È la differenza fra una chat che sembra viva e una che
 * sembra un modulo.
 *
 * L'altezza cresce con il testo fino a un tetto, come in ChatGPT. Si ricalcola sul
 * campo stesso invece che misurando un elemento nascosto: una misura in più per
 * battitura è lavoro che si paga a ogni tasto.
 */

import { Component, useRef, useState } from "@odoo/owl";

const ALTEZZA_MASSIMA = 200;

export class AidaComposer extends Component {
    static template = "nli_web.AidaComposer";
    static props = {
        store: Object,
        state: Object,
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.input = useRef("input");
        this.ui = useState({ text: "", sending: false });
    }

    get canSend() {
        return this.ui.text.trim().length > 0 && !this.ui.sending;
    }

    onInput(ev) {
        this.ui.text = ev.target.value;
        this._resize(ev.target);
    }

    _resize(el) {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, ALTEZZA_MASSIMA) + "px";
    }

    onKeydown(ev) {
        // Invio manda, Maiusc+Invio va a capo: è la convenzione che chiunque abbia
        // usato una chat conosce già, e il documento chiede zero addestramento.
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.send();
        }
    }

    async send() {
        if (!this.canSend) {
            return;
        }
        const testo = this.ui.text;
        this.ui.text = "";
        this.ui.sending = true;
        if (this.input.el) {
            this.input.el.style.height = "auto";
            this.input.el.focus();
        }
        try {
            await this.props.store.send(testo);
        } finally {
            this.ui.sending = false;
        }
    }
}
