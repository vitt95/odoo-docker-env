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
import { AidaRecords } from "./aida_records";

export class AidaThread extends Component {
    static template = "nli_web.AidaThread";
    static components = { AidaRecords };
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

    /** Il corpo del chiarimento, comunque sia annidato nella busta. */
    clarificationOf(turn) {
        const i = turn.interpretation || {};
        return i.clarification || i;
    }

    /**
     * Scegliere una lettura (D121).
     *
     * Non manda operazioni al server: **scrive l'etichetta nella casella e la invia**,
     * cioè fa quello che farebbe l'utente scrivendola. È il motivo per cui il clic e lo
     * scritto non possono divergere — non ci sono due percorsi da tenere allineati, ce
     * n'è uno e il clic lo imbocca dall'inizio.
     *
     * Solo l'ultimo turno è cliccabile: una domanda di dieci messaggi fa non è più in
     * sospeso (il server guarda solo il turno immediatamente precedente), e un bottone
     * che finge di poter ancora rispondere manderebbe la frase a interpretare da capo.
     */
    isAnswerable(turn) {
        const turni = this.turns;
        return turni.length > 0 && turni[turni.length - 1].id === turn.id;
    }

    chooseOption(option) {
        this.props.store.setDraft(option.label);
        this.props.store.submitDraft();
    }

    /**
     * Quanti record ha trovato la domanda, e quanti se ne vedono.
     *
     * **La frase di D68, finalmente sullo schermo.** L'Esecutore conta prima di
     * recuperare proprio per poter dire *«i primi 80 di 1 243»*: la delibera si
     * giustifica così — *«ottanta record senza contesto si leggono come **tutti
     * quanti**»*. Il numero c'era, il totale pure, e la frase la costruiva
     * `Result.describe()` sul server: **nessuno la mostrava**. Sullo schermo restava
     * «39 record trovati» sopra una tabella di cinque righe.
     *
     * Visto sul campo il 3 agosto 2026, ed è la stessa famiglia della chiave del
     * limite che non esisteva: calcolato, portato fino al client, non collegato.
     *
     * Il taglio si riconosce senza chiedere niente al server: il totale è
     * `record_count`, quante righe si leggono è il limite del piano, e se il primo
     * supera il secondo la risposta è troncata. È lo stesso conto che fa
     * `Result.truncated`, fatto dove c'è la lingua per dirlo.
     *
     * Lo zero si scrive in lettere invece che come cifra perché *«0 record trovati»* si
     * legge come un errore di conto, e *«nessun record»* si legge come una risposta —
     * che è quello che è.
     */
    recordsLabel(turn) {
        const totale = turn.record_count || 0;
        if (totale === 0) {
            return "Nessun record trovato.";
        }
        const limite = turn.query && turn.query.limit;
        if (limite && totale > limite) {
            return `I primi ${limite} di ${totale} record.`;
        }
        return totale === 1 ? "1 record trovato." : `${totale} record trovati.`;
    }

    // --- modalità diagnostica (D123) -------------------------------------

    /**
     * Le fasi del turno con il loro tempo, nell'ordine in cui sono corse.
     *
     * Sta qui e non nel modello perché è una scelta di come mostrarlo, non un fatto
     * del turno: il server manda la traccia com'è, e cambiare l'ordine di lettura non
     * deve voler dire riscrivere quello che è stato scritto sul turno.
     */
    phasesOf(turn) {
        const d = turn.debug || {};
        const nomi = [
            ["phase_a", "fase A — dizionario"],
            ["phase_b", "fase B — modello: quale entità"],
            ["phase_c", "fase C — catalogo"],
            ["interpret", "modello: la busta"],
            ["execute", "esecuzione su Odoo"],
        ];
        return nomi
            .filter(([chiave]) => d[chiave])
            .map(([chiave, etichetta]) => ({
                key: chiave,
                label: etichetta,
                seconds: d[chiave].seconds,
                note: d[chiave].skipped || "",
            }));
    }

    /** Il DSL grezzo: la busta come il modello l'ha restituita. */
    envelopeOf(turn) {
        const d = turn.debug || {};
        const busta = (d.interpret && d.interpret.envelope) ||
            (d.phase_b && d.phase_b.envelope) || null;
        return busta ? JSON.stringify(busta, null, 2) : "";
    }

    /** La query: gli argomenti con cui Odoo è stato interrogato. */
    planOf(turn) {
        const piano = (turn.debug || {}).plan;
        return piano ? JSON.stringify(piano, null, 2) : "";
    }

    stateOf(turn) {
        const stato = (turn.debug || {}).state_after;
        return stato ? JSON.stringify(stato, null, 2) : "";
    }

    /** La riga di dominio da incollare in una vista Odoo, senza rileggere il JSON. */
    domainOf(turn) {
        const piano = (turn.debug || {}).plan;
        return piano ? JSON.stringify(piano.domain) : "";
    }

    partClass(part) {
        // §10.2 e D65: l'origine si vede, e non solo dal colore — chi non distingue i
        // colori deve poter distinguere lo stesso una condizione che ha chiesto lui da
        // una che ha dedotto il sistema.
        return part.origin === "inferred" ? "o_aida_part o_aida_part_inferred" : "o_aida_part";
    }
}
