/** @odoo-module **/

/**
 * Il filo dei messaggi.
 *
 * Due cose lo tengono fluido, e sono entrambe questioni di scorrimento più che di
 * disegno:
 *
 * * **I turni più vecchi si caricano scorrendo all'insù, ancorando la posizione.**
 *   Aggiungere righe sopra a quelle che si stanno leggendo sposta il contenuto sotto
 *   gli occhi: si misura l'altezza prima, si rimette dopo, e l'utente non se ne
 *   accorge.
 * * **Si scorre in fondo solo se ci si era.** Un messaggio nuovo che strappa in basso
 *   mentre si rilegge una risposta di dieci minuti fa è il modo più veloce di rendere
 *   una chat sgradevole.
 *
 * La risposta di AIDA non è prosa: è **l'interpretazione in parti** costruita dal
 * Presentatore, dove ogni parte porta la propria origine (§3.3) e la regola che l'ha
 * prodotta (§10.2). Si disegna parte per parte proprio per questo — un testo unico
 * costringerebbe l'interfaccia a ri-analizzare ciò che il server sa già.
 */

import { Component, useEffect, useRef, onPatched, onMounted } from "@odoo/owl";

export class AidaThread extends Component {
    static template = "nli_web.AidaThread";
    static props = {
        store: Object,
        state: Object,
    };

    setup() {
        this.scroller = useRef("scroller");
        this._eraAlFondo = true;
        this._altezzaPrima = 0;

        onMounted(() => this.scrollToBottom());
        onPatched(() => this._afterPatch());

        // Quando cambia conversazione si riparte dal fondo, come aprire una chat.
        useEffect(
            () => {
                this._eraAlFondo = true;
                this.scrollToBottom();
            },
            () => [this.props.state.currentId]
        );
    }

    get turns() {
        return this.props.state.turns;
    }

    scrollToBottom() {
        const el = this.scroller.el;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }

    _afterPatch() {
        const el = this.scroller.el;
        if (!el) {
            return;
        }
        if (this._altezzaPrima) {
            // Sono arrivati turni vecchi in cima: si rimette la posizione dov'era,
            // altrimenti il testo che l'utente stava leggendo scivola via.
            el.scrollTop += el.scrollHeight - this._altezzaPrima;
            this._altezzaPrima = 0;
            return;
        }
        if (this._eraAlFondo) {
            this.scrollToBottom();
        }
    }

    onScroll(ev) {
        const el = ev.target;
        this._eraAlFondo = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
        if (el.scrollTop < 120 && this.props.state.hasMoreTurns && !this.props.state.loadingTurns) {
            this._altezzaPrima = el.scrollHeight;
            this.props.store.loadTurns();
        }
    }

    /** La chiave di `t-foreach`: stabile, così OWL rattoppa invece di ridisegnare. */
    turnKey(turn) {
        return turn.id;
    }

    partClass(part) {
        // §10.2 e D65: l'origine si vede, e non solo dal colore — chi non distingue i
        // colori deve poter distinguere lo stesso una condizione che ha chiesto lui da
        // una che ha dedotto il sistema.
        return part.origin === "inferred" ? "o_aida_part o_aida_part_inferred" : "o_aida_part";
    }
}
