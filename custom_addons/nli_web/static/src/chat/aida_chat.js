/** @odoo-module **/

/**
 * La voce di menu, adesso che AIDA vive in un pannello.
 *
 * ## Perché questa azione esiste ancora
 *
 * Fino a oggi `nli_web.chat` **era** AIDA: un'azione a pagina intera che sostituiva
 * quello che si stava guardando. Non lo è più — AIDA è una colonna accanto alla
 * vista, perché chiedere «quali di questi sono scaduti?» ha senso solo se *questi*
 * sono ancora sullo schermo.
 *
 * L'azione resta perché la voce di menu la punta, e una voce di menu che porta a un
 * errore è il modo peggiore di annunciare un cambiamento. Chi arriva da qui trova il
 * pannello già aperto e una riga che dice dov'è andato: si legge una volta, e poi si
 * usa la scorciatoia.
 *
 * ## Perché non si richiude da sola
 *
 * Un'azione che si apre e si chiude da sé lascia nella cronologia del browser uno
 * stato che il tasto «indietro» non sa districare — e il tasto «indietro» è
 * esattamente quello che si preme quando non si capisce dove si è finiti. Meglio una
 * schermata che dice le cose che una navigazione che le nasconde.
 */

import { Component, onMounted } from "@odoo/owl";
import { isMacOS } from "@web/core/browser/feature_detection";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AidaChat extends Component {
    static template = "nli_web.AidaChat";
    static props = {
        "*": true,
    };

    setup() {
        this.aida = useService("aida");
        onMounted(() => this.aida.open());
    }

    /** La stessa scorciatoia del pulsante, scritta come la tastiera di chi legge.
     *  Su macOS il token `alt` di Odoo lo produce Ctrl: vedi `AidaLauncher`. */
    get shortcut() {
        return isMacOS() ? ["Ctrl", "Maiusc", "A"] : ["Alt", "Maiusc", "A"];
    }

    focusComposer() {
        this.aida.open();
        document.querySelector(".o_aida_panel .o_aida_input")?.focus();
    }
}

registry.category("actions").add("nli_web.chat", AidaChat);
