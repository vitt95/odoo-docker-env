/** @odoo-module **/

/**
 * Il pannello di AIDA: una colonna a destra, sopra qualunque vista di Odoo.
 *
 * ## Perché sta nei `main_components`
 *
 * Un'azione client vive dentro il gestore delle azioni: aprirla **sostituisce** ciò
 * che si stava guardando. AIDA serve mentre si guarda una board, una lista, un
 * modulo — chiedere «quali di questi sono scaduti?» ha senso solo se *questi* sono
 * ancora sullo schermo. Un componente montato alla radice del webclient è l'unico
 * che può stare accanto all'azione invece che al suo posto.
 *
 * È lo stesso schema della barra laterale Premium (`ui_premium_shell`), collaudato
 * qui dentro: componente radice, posizione fissa, e una classe sul `body` che dice
 * al foglio di stile di quanto restringere il contenuto.
 *
 * ## Perché il contenuto si restringe invece di finire sotto
 *
 * Un pannello che copre la vista costringe a chiuderlo per rileggere ciò di cui si
 * sta parlando, e chiuderlo perde il posto. Restringere costa un riflusso all'aper-
 * tura e alla chiusura — due volte in tutta la sessione — e in cambio la domanda e
 * la cosa di cui parla restano sullo schermo insieme.
 *
 * ## Il ridimensionamento, e la ragione per cui non passa dallo stato
 *
 * Trascinare la maniglia muove il puntatore decine di volte al secondo. Se ogni
 * movimento aggiornasse lo stato del componente, OWL ridisegnerebbe l'intera
 * conversazione a ogni fotogramma: con venti turni sullo schermo si sente, e si
 * sente proprio nel gesto che deve risultare immediato.
 *
 * Quindi durante il trascinamento **lo stato non si tocca**. Si scrive una sola
 * proprietà CSS sul `body`, dentro un `requestAnimationFrame`, e la stessa proprietà
 * è ciò che dà la larghezza al pannello *e* il rientro al contenuto: una scrittura
 * muove entrambi, e non c'è nessun calcolo di posizione in JavaScript da tenere
 * allineato. Lo stato si aggiorna una volta sola, quando il dito si alza.
 */

import { Component, onMounted, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { useService } from "@web/core/utils/hooks";
import { AidaComposer } from "../chat/aida_composer";
import { AidaHistory } from "../chat/aida_history";
import { AidaThread } from "../chat/aida_thread";
import { AidaWelcome } from "../chat/aida_welcome";

/** La proprietà che porta la larghezza. Una sola, letta da due regole. */
const VARIABILE_LARGHEZZA = "--aida-panel-width";

/** Dove comincia il pannello: sotto la barra in alto, misurata e non indovinata. */
const VARIABILE_ALTO = "--aida-top";

/** La barra di Odoo, che il pannello non deve mai coprire né restringere. */
const SELETTORE_BARRA = ".o_navbar";

/** La classe che dice al foglio di stile di fare spazio. */
const CLASSE_APERTO = "o_aida_has_panel";

/** Mentre si trascina: spegne le transizioni e blocca la selezione del testo. */
const CLASSE_TRASCINO = "o_aida_resizing";

export class AidaPanel extends Component {
    static template = "nli_web.AidaPanel";
    static components = { AidaComposer, AidaHistory, AidaThread, AidaWelcome };
    static props = {};

    setup() {
        this.aida = useService("aida");
        this.ui = useState(this.aida.ui);
        this.state = useState(this.aida.store.state);
        this.panel = useRef("panel");

        // Lo stato del trascinamento non è reattivo di proposito: nessuno di questi
        // valori deve poter far ridisegnare qualcosa.
        this._trascino = { attivo: false, larghezza: 0, frame: 0, pointerId: null };

        // La barra può cambiare altezza quando la finestra si restringe (in Odoo si
        // accorcia sotto una certa larghezza). Si rimisura, invece di fidarsi del
        // valore preso all'apertura.
        this._onResize = () => this._misuraBarra();

        onMounted(() => {
            this._applica(this.ui.width);
            this._misuraBarra();
            window.addEventListener("resize", this._onResize);
        });
        onWillUnmount(() => {
            window.removeEventListener("resize", this._onResize);
            document.body.classList.remove(CLASSE_APERTO, CLASSE_TRASCINO);
            this._annullaFrame();
        });

        // L'apertura e la larghezza sono due effetti separati: cambiare larghezza a
        // pannello aperto non deve rifare il lavoro dell'apertura, e viceversa.
        useEffect(
            (open) => {
                document.body.classList.toggle(CLASSE_APERTO, open);
                if (open) {
                    // La barra può essersi accorciata dopo il montaggio: si rimisura
                    // qui, che è l'unico istante in cui la misura serve davvero.
                    this._misuraBarra();
                    // Il fuoco va nella casella: chi apre il pannello vuole scrivere.
                    // In un fotogramma, perché prima il pannello non è ancora nel DOM.
                    requestAnimationFrame(() => this._focusComposer());
                }
            },
            () => [this.ui.open]
        );
        useEffect(
            (width) => this._applica(width),
            () => [this.ui.width]
        );

        // **`bypassEditableProtection` perché il fuoco è quasi sempre nella casella.**
        //
        // Il servizio delle scorciatoie, di norma, ignora i tasti quando si sta
        // scrivendo — regola giusta, che qui rendeva la scorciatoia inutilizzabile
        // proprio nel caso normale: aprendo il pannello il fuoco va nella casella, e
        // da lì la combinazione non chiudeva più niente. Trovato provandola.
        //
        // Aprire e chiudere AIDA deve funzionare **sempre**, anche a metà di una
        // frase: è la via d'uscita, e una via d'uscita che si chiude quando serve non
        // è una via d'uscita. Vale solo per questa combinazione, che è nostra e non
        // collide con niente che si scriva.
        useHotkey("alt+shift+a", () => this.aida.toggle(),
                  { global: true, bypassEditableProtection: true });
        // `Escape` chiude, **anche mentre si scrive**, e va bene così.
        //
        // Il commento qui sopra diceva il contrario e sbagliava due volte: il
        // servizio registra `escape` per conto suo saltando la protezione dei campi
        // modificabili, quindi la chiusura avviene comunque; e soprattutto non c'è
        // niente da proteggere. La bozza vive nello store, non nella casella (D121 —
        // ci scrive anche il clic su una lettura), quindi chiudere non la perde:
        // provato chiudendo con `Escape` a metà di «le fatture di marzo» e
        // riaprendo — la frase è ancora lì, con il cursore dov'era.
        //
        // Che `Escape` chiuda un pannello è quello che si aspettano tutti. Sarebbe
        // stato un problema solo se avesse buttato via qualcosa, e non lo fa.
        useHotkey("escape", () => this.aida.close());
    }

    get conversation() {
        return this.state.conversations.find((c) => c.id === this.state.currentId);
    }

    get isEmpty() {
        return !this.state.currentId || this.state.turns.length === 0;
    }

    /** Vero finché AIDA sta lavorando su un turno: la casella lo dice, non lo nasconde. */
    get isBusy() {
        return this.state.pendingCount > 0;
    }

    // --- la larghezza --------------------------------------------------------

    /**
     * Scrive la larghezza dove la leggono entrambi.
     *
     * Sul `body` e non sul pannello: il rientro del contenuto è una regola che parla
     * del `body`, e una proprietà scritta sul figlio non risale. Un solo posto in cui
     * la larghezza esiste, quindi nessun modo di farli divergere.
     */
    _applica(pixel) {
        document.body.style.setProperty(VARIABILE_LARGHEZZA, `${pixel}px`);
    }

    /**
     * Dove finisce la barra in alto, che è dove comincia il pannello.
     *
     * **Misurata e non scritta.** Vale 46 pixel con la skin Classic e 48 con Premium,
     * e domani sarà un altro numero: un valore cablato è giusto finché qualcuno non
     * cambia la barra, e quel giorno il pannello la coprirebbe di due pixel — abbastanza
     * per tagliare il bordo inferiore e non abbastanza perché qualcuno capisca perché.
     *
     * Una lettura all'apertura e una a ogni ridimensionamento della finestra. Non è
     * nel percorso del disegno e non è nel trascinamento: succede quando la finestra
     * cambia, cioè raramente e mai a sessanta volte al secondo.
     */
    _misuraBarra() {
        const barra = document.querySelector(SELETTORE_BARRA);
        if (!barra) {
            return;
        }
        const altezza = Math.round(barra.getBoundingClientRect().height);
        document.body.style.setProperty(VARIABILE_ALTO, `${altezza}px`);
    }

    _annullaFrame() {
        if (this._trascino.frame) {
            cancelAnimationFrame(this._trascino.frame);
            this._trascino.frame = 0;
        }
    }

    onResizeStart(ev) {
        // Solo il tasto principale: un menu contestuale sulla maniglia non deve
        // lasciare il pannello agganciato al puntatore.
        if (ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        this._trascino.attivo = true;
        this._trascino.larghezza = this.ui.width;
        this._trascino.pointerId = ev.pointerId;
        // La cattura del puntatore è ciò che rende il gesto affidabile: senza, un
        // trascinamento veloce che esce dalla maniglia perde gli eventi e la
        // larghezza si blocca dove il mouse è uscito.
        ev.currentTarget.setPointerCapture(ev.pointerId);
        document.body.classList.add(CLASSE_TRASCINO);
    }

    onResizeMove(ev) {
        if (!this._trascino.attivo) {
            return;
        }
        // La larghezza è la distanza dal bordo destro: il pannello è ancorato lì, e
        // calcolarla così la rende indipendente da dove sta la maniglia.
        this._trascino.larghezza = window.innerWidth - ev.clientX;
        if (this._trascino.frame) {
            return; // Un fotogramma è già prenotato: l'ultimo valore vince.
        }
        this._trascino.frame = requestAnimationFrame(() => {
            this._trascino.frame = 0;
            // Si passa dal servizio per i confini, non per lo stato: `limita` è la
            // stessa funzione che userà il rilascio, quindi il pannello si ferma
            // durante il gesto esattamente dove si fermerà alla fine.
            this._applica(this.aida.clamp(this._trascino.larghezza));
        });
    }

    onResizeEnd(ev) {
        if (!this._trascino.attivo) {
            return;
        }
        this._trascino.attivo = false;
        this._annullaFrame();
        ev.currentTarget.releasePointerCapture?.(this._trascino.pointerId);
        document.body.classList.remove(CLASSE_TRASCINO);
        // **Adesso** lo stato, una volta sola: da qui parte il salvataggio.
        this.aida.setWidth(this._trascino.larghezza);
    }

    /**
     * La maniglia si muove anche da tastiera.
     *
     * Un ridimensionamento che esiste solo per chi usa il mouse è una funzione che
     * non esiste per una parte delle persone. Venti pixel per pressione: abbastanza
     * da arrivare da un capo all'altro in poche battute, abbastanza poco da poter
     * scegliere.
     */
    onResizeKeydown(ev) {
        const passo = ev.key === "ArrowLeft" ? 20 : ev.key === "ArrowRight" ? -20 : 0;
        if (!passo) {
            return;
        }
        ev.preventDefault();
        this.aida.setWidth(this.ui.width + passo);
    }

    // --- comandi dell'intestazione -------------------------------------------

    toggleHistory() {
        this.ui.historyOpen = !this.ui.historyOpen;
    }

    async newConversation() {
        await this.aida.store.newConversation();
        this.ui.historyOpen = false;
        this._focusComposer();
    }

    openConversation(id) {
        this.ui.historyOpen = false;
        return this.aida.store.open(id);
    }

    _focusComposer() {
        this.panel.el?.querySelector(".o_aida_input")?.focus();
    }
}

registry.category("main_components").add("nli_web.AidaPanel", { Component: AidaPanel });
