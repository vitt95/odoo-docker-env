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

import { Component, useEffect, useRef, useState, onPatched, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { AidaRecords } from "./aida_records";
import { AidaSteps } from "./aida_steps";

export class AidaThread extends Component {
    static template = "nli_web.AidaThread";
    static components = { AidaRecords, AidaSteps };
    static props = {
        store: Object,
        state: Object,
    };

    setup() {
        this.scroller = useRef("scroller");
        this.action = useService("action");
        // Quale risposta ha appena risposto «copiato». Non reattivo per turno ma uno
        // solo: due conferme insieme non hanno senso, e tenerne una sola evita di
        // sporcare ogni turno con un campo che vive due secondi.
        this.ui = useState({ copiedId: null });
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

    // --- che cosa si può fare di una risposta -----------------------------

    /**
     * Aprire i risultati a tutta pagina.
     *
     * **Il pannello è largo quattrocentoquaranta pixel e una tabella no.** La vista
     * lista incorporata resta — è la funzione che c'è, e toglierla per fare spazio
     * all'estetica sarebbe un peggioramento travestito — ma dentro una colonna
     * stretta si consulta male, e per otto colonne di dati serve la pagina.
     *
     * Si passa **il dominio**, non i record: la vista li rilegge da sola con i
     * diritti di chi guarda, esattamente come fa quella incorporata. È la stessa
     * regola di record applicata dalla stessa vista, e non c'è nessuna seconda
     * strada verso quei dati da tenere allineata.
     *
     * Il pannello resta aperto: chi apre la tabella intera sta ancora ragionando
     * sulla conversazione, e chiudergliela sotto sarebbe togliergli il contesto
     * proprio mentre lo usa.
     */
    openFull(turn) {
        const query = turn.query;
        if (!query || !query.model) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: turn.utterance,
            res_model: query.model,
            domain: query.domain || [],
            views: [[false, query.view === "pivot" || query.view === "graph"
                ? query.view : "list"], [false, "form"]],
            target: "current",
        });
    }

    /**
     * Copiare la risposta come testo.
     *
     * Copia **quello che si legge**, non il JSON: l'interpretazione a parole e il
     * conteggio. Chi copia una risposta la incolla in un messaggio o in un ticket, e
     * lì una struttura tecnica non serve a niente.
     *
     * `navigator.clipboard` può non esserci (contesto non sicuro, browser vecchio) e
     * può essere negato dall'utente: in entrambi i casi non succede niente e non si
     * mostra nessun errore. È un comando accessorio, e un errore per un comando
     * accessorio pesa più del comando.
     */
    async copyAnswer(turn) {
        const righe = [turn.utterance, ""];
        if (turn.query) {
            righe.push(this.recordsLabel(turn));
        }
        for (const parte of (turn.interpretation && turn.interpretation.parts) || []) {
            righe.push(`— ${parte.text}`);
        }
        try {
            await navigator.clipboard.writeText(righe.join("\n"));
            this.ui.copiedId = turn.id;
            setTimeout(() => {
                if (this.ui.copiedId === turn.id) {
                    this.ui.copiedId = null;
                }
            }, 1800);
        } catch {
            // Niente da fare e niente da dire: vedi il commento sopra.
        }
    }

    /** Vero quando la risposta ha qualcosa su cui si può agire. */
    hasActions(turn) {
        return !turn.pending && Boolean(turn.query || (turn.interpretation || {}).parts);
    }
}
