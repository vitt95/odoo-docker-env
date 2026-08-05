/** @odoo-module **/

/**
 * La schermata di quando non c'è ancora niente.
 *
 * ## Perché i suggerimenti riempiono la casella invece di partire
 *
 * Nel riferimento cliccare un suggerimento manda subito la domanda. Lì può
 * permetterselo: i suggerimenti li calcola il server guardando i dati veri di quel
 * progetto, quindi sono domande che funzionano di sicuro.
 *
 * Qui no. AIDA gira su installazioni diverse, e quali entità esistono dipende da
 * quali moduli sono installati e da cosa quella persona può leggere: un suggerimento
 * che nomina le fatture su un'installazione senza contabilità è una domanda che
 * fallisce al primo clic. **Un esempio che non funziona insegna a non fidarsi dei
 * suggerimenti**, e lo insegna al primo tentativo.
 *
 * Quindi il clic scrive nella casella e mette il cursore in fondo: l'esempio mostra
 * *la forma* di una domanda che AIDA capisce — un soggetto, un filtro, un periodo,
 * un raggruppamento — e chi legge la adatta a ciò che ha davvero. È il contrario di
 * D121 (dove il clic deve inviare) e per la ragione opposta: lì l'opzione viene dal
 * catalogo ed è vera per costruzione, qui è un esempio scritto da noi.
 *
 * ## Perché ne cambiano tre alla volta
 *
 * Un elenco fisso si smette di leggere dopo due giorni. Tre estratti a sorte da un
 * elenco più lungo restano una cosa da guardare, e ognuno insegna una forma diversa
 * di domanda.
 */

import { Component } from "@odoo/owl";

/**
 * Le forme di domanda che AIDA sa leggere.
 *
 * Non sono frasi a caso: ognuna esercita un pezzo diverso del DSL — un filtro
 * testuale, un periodo, un confronto numerico, un raggruppamento, un ordinamento con
 * limite. Chi le legge tutte e tre ha capito cosa può chiedere senza leggere niente.
 */
export const ESEMPI = [
    "i clienti di Milano",
    "le fatture di questo mese sopra 500 euro",
    "gli ordini dell'anno scorso raggruppati per cliente",
    "i 10 contatti creati più di recente",
    "quante opportunità ci sono per ogni fase",
    "i prodotti senza prezzo di listino",
    "le attività in ritardo assegnate a me",
    "il fatturato per mese di quest'anno",
];

/** Quanti se ne mostrano. Tre stanno in una colonna stretta senza affollarla. */
const QUANTI = 3;

export class AidaWelcome extends Component {
    static template = "nli_web.AidaWelcome";
    static props = {
        store: Object,
        state: Object,
    };

    setup() {
        // Estratti una volta al montaggio e non a ogni ridisegno: dei suggerimenti
        // che cambiano mentre si scrive sono una superficie che si muove da sola, ed
        // è il genere di cosa che fa sbagliare bersaglio a un clic già partito.
        this.suggerimenti = this.constructor.pescane(QUANTI);
    }

    /** Estrazione senza ripetizioni: mescola una copia e prende i primi. */
    static pescane(quanti) {
        const copia = [...ESEMPI];
        for (let i = copia.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [copia[i], copia[j]] = [copia[j], copia[i]];
        }
        return copia.slice(0, quanti);
    }

    use(esempio) {
        this.props.store.setDraft(esempio);
        // Il fuoco nella casella, con il cursore in fondo: l'esempio è un punto di
        // partenza da modificare, e chi deve modificarlo non deve prima cliccarci.
        const casella = document.querySelector(".o_aida_panel .o_aida_input");
        if (casella) {
            casella.focus();
            casella.setSelectionRange(esempio.length, esempio.length);
        }
    }
}
