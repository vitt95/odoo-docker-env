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
 *
 * **Il testo non è suo.** Vive nello store, perché anche il clic su una lettura scrive
 * lì (D121). Questa casella lo mostra e lo manda; non è l'unica a riempirlo, ed è
 * l'unica cosa che la distingue da una casella qualunque.
 */

import { Component, useEffect, useRef, useState } from "@odoo/owl";

/**
 * Quanto può crescere prima di scorrere dentro di sé.
 *
 * Nel pannello conta più che a pagina intera: una casella che si prende metà
 * dell'altezza disponibile spinge fuori dallo schermo la risposta a cui si sta
 * rispondendo, ed è il momento in cui serve di più.
 */
const ALTEZZA_MASSIMA = 160;

/**
 * Oltre questo la frase non è più una domanda.
 *
 * Non è un limite del server — quello sta altrove ed è più alto — è il punto in cui
 * conviene dirlo: una domanda di duemila caratteri non è una domanda, è un documento,
 * e il modello la leggerà male comunque.
 */
const CARATTERI_MASSIMI = 2000;

/** Da qui in poi il conteggio si vede. Prima non serve a nessuno. */
const SOGLIA_CONTEGGIO = 1800;

export class AidaComposer extends Component {
    static template = "nli_web.AidaComposer";
    static props = {
        store: Object,
        state: Object,
        placeholder: { type: String, optional: true },
        /** Vero mentre AIDA sta lavorando su un turno. */
        busy: { type: Boolean, optional: true },
    };

    setup() {
        this.input = useRef("input");
        // Si prende **il proprio** riferimento allo stato condiviso invece di leggerlo
        // attraverso la proprietà. È quello che fa scattare il ridisegno su questo
        // componente e non sul padre: altrimenti ogni battitura ridisegnerebbe anche il
        // filo dei messaggi, che con una conversazione lunga si sente.
        this.chat = useState(this.props.state);
        // Il testo può arrivare da un clic invece che dalla tastiera: l'altezza va
        // ricalcolata lo stesso, altrimenti una lettura lunga resta tagliata a una riga.
        useEffect(
            () => {
                if (this.input.el) {
                    this._resize(this.input.el);
                }
            },
            () => [this.chat.draft]
        );
    }

    get text() {
        return this.chat.draft;
    }

    get canSend() {
        const lunghezza = this.text.trim().length;
        return lunghezza > 0 && lunghezza <= CARATTERI_MASSIMI && !this.chat.sending;
    }

    /**
     * Il testo grigio nella casella, che cambia con il momento.
     *
     * A conversazione vuota invita a cominciare; dopo una risposta invita a
     * continuare. Sono due situazioni diverse e un testo solo ne servirebbe male una:
     * «Chiedi qualcosa» sotto una risposta suona come se la conversazione precedente
     * non fosse successa.
     */
    get placeholder() {
        if (this.props.placeholder) {
            return this.props.placeholder;
        }
        return this.chat.turns.length
            ? "Chiedi altro, o precisa la domanda"
            : "Chiedi qualcosa sui tuoi dati";
    }

    get counter() {
        return `${this.text.length} / ${CARATTERI_MASSIMI}`;
    }

    get nearLimit() {
        return this.text.length >= SOGLIA_CONTEGGIO;
    }

    onInput(ev) {
        this.props.store.setDraft(ev.target.value);
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
        if (this.input.el) {
            this.input.el.style.height = "auto";
            this.input.el.focus();
        }
        await this.props.store.submitDraft();
    }
}
