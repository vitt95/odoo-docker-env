/** @odoo-module **/

/**
 * Che cosa sta facendo AIDA, mentre lo fa.
 *
 * ## Le parole stanno qui, e le chiavi sul server
 *
 * Il dispatcher manda `dictionary`, `interpret`, `execute`. Le frasi che si leggono
 * sono scritte qui sotto, ed è deliberato: la lingua dell'interfaccia è una scelta
 * dell'interfaccia, e un giorno la stessa chiave dovrà poter diventare una riga
 * diversa senza che nessuno tocchi la coda.
 *
 * Le frasi dicono **cosa succede a chi guarda**, non come è fatto il prodotto
 * dentro. «Fase B» e «catalogo» sono i nomi giusti nei documenti e i nomi sbagliati
 * qui: chi aspetta una risposta non ha chiesto l'architettura. È la stessa regola per
 * cui l'attesa dice *«sto pensando»* e non *«sto interpretando la domanda»*.
 *
 * ## Perché se ne vedono tre
 *
 * Un elenco che cresce spinge in basso la conversazione a ogni passo, e chi stava
 * leggendo la risposta di prima se la vede scappare via. Tre righe stanno ferme:
 * l'ultimo arriva in fondo e il più vecchio esce dall'alto, quindi l'altezza del
 * blocco non cambia mai e niente si muove sotto gli occhi di nessuno.
 *
 * Tre e non uno perché un passo solo non racconta un percorso: si vede l'ultima cosa
 * e non si capisce se sta andando avanti o girando in tondo.
 *
 * ## Perché a fine turno si chiude invece di sparire
 *
 * Sparire cancellerebbe la sola spiegazione di quanto è durata l'attesa. Restare
 * aperto riempirebbe ogni risposta di sei righe che nessuno rilegge. Chiuso in una
 * riga: chi guarda vede la risposta, chi si chiede *perché ci ha messo venti
 * secondi* ha ancora tutto, a un clic. Sono due bisogni diversi e così non si
 * contendono lo stesso spazio.
 */

import { Component, useState } from "@odoo/owl";

/** Quanti passi restano visibili mentre il turno lavora. */
export const FINESTRA = 3;

/**
 * Da chiave a riga leggibile.
 *
 * `detail` è opzionale e arriva dal server solo quando c'è qualcosa di neutro da
 * dire — un nome di entità, mai la frase di chi ha scritto. La funzione lo riceve e
 * decide da sola se serve: un passo senza dettaglio deve restare una riga completa,
 * non una riga mutilata.
 */
export const PASSI = {
    dictionary: {
        icon: "fa-search",
        label: "Cerco di che cosa parli",
    },
    entity: {
        icon: "fa-question-circle-o",
        label: "Non l'ho riconosciuto: lo chiedo al modello",
    },
    catalogue: {
        icon: "fa-list-ul",
        label: "Preparo quello che posso leggere",
        detail: (nome) => (nome ? `Fra le ${nome}` : ""),
    },
    reading: {
        icon: "fa-check",
        label: "Applico la lettura che hai scelto",
    },
    interpret: {
        icon: "fa-magic",
        label: "Interpreto la domanda",
        detail: (nome) => (nome ? `Sto cercando fra le ${nome}` : ""),
    },
    validate: {
        icon: "fa-shield",
        label: "Controllo che la richiesta si possa fare",
    },
    execute: {
        icon: "fa-database",
        label: "Interrogo Odoo",
    },
};

/** Un passo che il client non conosce. Non deve poter diventare una riga vuota. */
const IGNOTO = { icon: "fa-circle-o", label: "Sto lavorando" };

export class AidaSteps extends Component {
    static template = "nli_web.AidaSteps";
    static props = {
        turn: Object,
    };

    setup() {
        this.ui = useState({ expanded: false });
    }

    get steps() {
        return this.props.turn.steps || [];
    }

    get collapsed() {
        return this.props.turn.stepsCollapsed && !this.ui.expanded;
    }

    /**
     * I passi da disegnare adesso.
     *
     * Durante il turno: gli ultimi tre. A turno finito e aperto: tutti, perché chi
     * l'ha aperto sta cercando proprio quello che la finestra nascondeva.
     */
    get visible() {
        if (this.props.turn.stepsCollapsed) {
            return this.ui.expanded ? this.steps : [];
        }
        return this.steps.slice(-FINESTRA);
    }

    /** Vero quando la finestra sta nascondendo qualcosa: lo dice invece di fingere. */
    get truncated() {
        return !this.props.turn.stepsCollapsed && this.steps.length > FINESTRA;
    }

    get summary() {
        const quanti = this.steps.length;
        return quanti === 1 ? "Completato 1 passo" : `Completati ${quanti} passi`;
    }

    definition(step) {
        return PASSI[step.step] || IGNOTO;
    }

    label(step) {
        return this.definition(step).label;
    }

    icon(step) {
        return `fa ${this.definition(step).icon}`;
    }

    /** La riga sotto il titolo, se questo passo ne ha una da dire. */
    detail(step) {
        const costruisci = this.definition(step).detail;
        return costruisci ? costruisci(step.detail) : "";
    }

    /**
     * La chiave di `t-key`: l'indice del server, che è stabile e unico per turno.
     *
     * Con la posizione nell'array, la finestra scorrevole farebbe credere a OWL che
     * ogni riga è cambiata a ogni passo — e ridisegnerebbe tre righe invece di
     * spostarne una.
     */
    key(step) {
        return step.index;
    }

    toggle() {
        this.ui.expanded = !this.ui.expanded;
    }
}
