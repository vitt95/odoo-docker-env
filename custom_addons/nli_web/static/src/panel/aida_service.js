/** @odoo-module **/

/**
 * Il servizio di AIDA: chi tiene lo stato quando nessuno lo sta guardando.
 *
 * ## Perché è un servizio e non lo stato di un componente
 *
 * Il pannello e il pulsante che lo apre sono **due componenti diversi**, montati in
 * due punti diversi dell'albero: il primo fra i `main_components`, il secondo nel
 * systray della barra in alto. Non hanno un antenato comune sotto la radice del
 * webclient, quindi non c'è nessuna proprietà che possa scendere dall'uno all'altro.
 *
 * Un servizio è il punto che entrambi possono leggere senza conoscersi. È anche il
 * solo posto dove la conversazione può sopravvivere alla chiusura del pannello: chi
 * chiude e riapre deve ritrovare la conversazione dov'era, non una schermata vuota.
 *
 * ## Perché non parte da solo
 *
 * `store.start()` carica le conversazioni e apre il canale del bus. Farlo al
 * caricamento della pagina vorrebbe dire che **ogni utente di Odoo paga una chiamata
 * al server e una sottoscrizione al bus**, compresi tutti quelli che AIDA non la
 * aprono mai. Su un'installazione con cinquecento utenti sono cinquecento richieste
 * al minuto di apertura per una funzione che ne usano dodici.
 *
 * Quindi parte alla **prima apertura**, e da lì in poi resta acceso: un turno che si
 * conclude a pannello chiuso deve comunque arrivare, altrimenti chiudere il pannello
 * mentre AIDA pensa vorrebbe dire perdere la risposta.
 *
 * ## Perché la larghezza sta qui
 *
 * È una preferenza della persona, non della sessione: chi allarga il pannello lo fa
 * una volta e si aspetta di ritrovarlo largo domani. Vive in `localStorage`, che è
 * dove vivono le preferenze che non vale la pena mandare al server — e non vale la
 * pena, perché sbagliarla costa un trascinamento.
 */

import { reactive } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { AidaStore } from "../chat/aida_store";

/** La chiave della larghezza. Prefissata come tutto ciò che questo modulo scrive. */
const CHIAVE_LARGHEZZA = "aida_panel_width";

/**
 * La larghezza di partenza, in pixel.
 *
 * Misurata sul riferimento: 439 px al primo aperto, ricavata dal fotogramma con
 * un'analisi dei bordi verticali. Quattrocentoquaranta è quel numero arrotondato, e
 * non è arbitrario nemmeno di suo: sotto i quattrocento una riga di testo scende a
 * meno di cinquanta caratteri e si legge a scatti.
 */
export const LARGHEZZA_PREDEFINITA = 440;

/** Sotto questa il testo non si legge più, si scansiona. */
export const LARGHEZZA_MINIMA = 360;

/**
 * Quanto può prendersi al massimo: metà della finestra.
 *
 * Non è una misura di gusto. Il pannello **restringe** la vista di Odoo invece di
 * coprirla, e una vista lista sotto la metà della finestra smette di essere
 * consultabile: a quel punto conviene la pagina intera, che è un'altra cosa e si
 * raggiunge in un altro modo.
 */
export const frazioneMassima = () => Math.round(browser.innerWidth * 0.5);

function larghezzaSalvata() {
    const grezza = Number.parseInt(browser.localStorage.getItem(CHIAVE_LARGHEZZA), 10);
    if (!Number.isFinite(grezza)) {
        return LARGHEZZA_PREDEFINITA;
    }
    return limita(grezza);
}

/** Dentro i confini, sempre. Una larghezza salvata su uno schermo grande e riletta
 *  su un portatile va rimessa in riga, non applicata com'era. */
export function limita(valore) {
    return Math.max(LARGHEZZA_MINIMA, Math.min(valore, frazioneMassima()));
}

export const aidaService = {
    dependencies: ["orm", "bus_service"],

    start(env, { orm, bus_service }) {
        const store = new AidaStore(orm, bus_service);

        // Lo stato del contenitore, separato da quello della conversazione. Sono due
        // cose con due vite diverse: aprire e chiudere il pannello non tocca la
        // conversazione, e una risposta che arriva non deve poter aprire il pannello.
        const ui = reactive({
            open: false,
            width: larghezzaSalvata(),
            /** Vero da quando lo store ha caricato la prima volta. Non torna falso. */
            started: false,
            /** La cronologia, che entra da sinistra sopra la conversazione. */
            historyOpen: false,
        });

        async function apri() {
            ui.open = true;
            if (!ui.started) {
                ui.started = true;
                await store.start();
            }
        }

        function chiudi() {
            ui.open = false;
            ui.historyOpen = false;
        }

        return {
            store,
            ui,
            open: apri,
            close: chiudi,
            toggle: () => (ui.open ? chiudi() : apri()),
            // I confini si espongono perché il trascinamento li applica **durante**
            // il gesto, senza passare dallo stato. Se il pannello si fermasse solo al
            // rilascio, il puntatore andrebbe avanti e il bordo starebbe fermo: si
            // legge come un'interfaccia che ha smesso di rispondere.
            clamp: limita,
            setWidth(pixel) {
                ui.width = limita(pixel);
                browser.localStorage.setItem(CHIAVE_LARGHEZZA, String(ui.width));
            },
        };
    },
};

registry.category("services").add("aida", aidaService);
