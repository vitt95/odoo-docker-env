/** @odoo-module **/

/**
 * Il pulsante che apre AIDA, nella barra in alto.
 *
 * ## Perché nel systray e non in un menu
 *
 * Una voce di menu si raggiunge in due clic e va cercata. AIDA si apre e si chiude
 * decine di volte in una giornata di lavoro — è la sua natura: si chiede una cosa, si
 * guarda la risposta, si torna a lavorare — quindi il costo di aprirla si paga ogni
 * volta. Il systray è la sola parte della barra che resta ferma mentre le viste
 * cambiano, ed è dove Odoo mette le cose che devono essere sempre a un clic.
 *
 * ## Perché il pulsante conosce lo stato del pannello
 *
 * Perché è lo stesso comando in tutti e due i versi. Un pulsante che apre e un altro
 * che chiude sono due strade per la stessa cosa, e prima o poi una delle due si
 * dimentica qualcosa — qui, per esempio, chiudere la cronologia. `aria-pressed` dice
 * a chi usa un lettore di schermo in che stato si trova, che è l'informazione che
 * l'icona dà a tutti gli altri.
 */

import { Component, useState } from "@odoo/owl";
import { isMacOS } from "@web/core/browser/feature_detection";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AidaLauncher extends Component {
    static template = "nli_web.AidaLauncher";
    static props = {};

    setup() {
        this.aida = useService("aida");
        this.ui = useState(this.aida.ui);
        this.state = useState(this.aida.store.state);
    }

    /**
     * Vero quando AIDA sta lavorando e il pannello è chiuso.
     *
     * È l'unico caso in cui il pulsante deve dire qualcosa da solo: a pannello aperto
     * l'attesa si vede già, e senza turni in corso non c'è niente da annunciare. Un
     * puntino che sta acceso sempre smette di voler dire qualcosa in due giorni.
     */
    get working() {
        return !this.ui.open && this.state.pendingCount > 0;
    }

    /**
     * Come si scrive la scorciatoia su **questa** tastiera.
     *
     * Odoo registra le scorciatoie con il token `alt`, ma su macOS quel token lo
     * produce **Ctrl**, non Alt (`hotkey_service.js`: `isMacOS() ? ev.ctrlKey :
     * ev.altKey`). È una convenzione della piattaforma e va bene così — quello che
     * non va bene è scriverne una sola nel suggerimento.
     *
     * Trovato provando: su un Mac la scritta diceva «Alt+Maiusc+A» e quella
     * combinazione non apriva niente. Un suggerimento che insegna un gesto che non
     * funziona è peggio di nessun suggerimento: chi lo prova una volta smette di
     * fidarsi anche degli altri.
     */
    get shortcut() {
        return isMacOS() ? "Ctrl+Maiusc+A" : "Alt+Maiusc+A";
    }
}

registry.category("systray").add(
    "nli_web.AidaLauncher", { Component: AidaLauncher }, { sequence: 12 });
