/** @odoo-module **/

/**
 * La tabella dei record di una risposta.
 *
 * ## Perché è la vista di Odoo e non una tabella nostra
 *
 * `15` chiede, per le tabelle: ricerca, ordinamento, filtri, selezione multipla,
 * gestione e ridimensionamento delle colonne, preferenze salvate, paginazione a
 * 10/25/50/100 con totali e navigazione. È l'elenco delle cose che la vista lista di
 * Odoo **fa già**, per ogni modello, con le preferenze dell'utente e i suoi diritti.
 *
 * Riscriverle voleva dire riscrivere anche i formattatori per valuta, data e
 * riferimento, il caricamento a blocchi, l'accessibilità della griglia e le
 * preferenze per utente — e ottenere qualcosa che *somiglia* a Odoo, che è il modo
 * più affidabile di sembrare un'estensione posticcia. `00` §23 ha deciso di
 * incorporarla, e questo componente è quella decisione in venti righe.
 *
 * ## Cosa passa, e cosa non passa
 *
 * Passa il **dominio**: la vista rilegge i record da sola, con i diritti di chi
 * guarda. Non passano i record. Un dominio che tornasse indietro da un utente a cui è
 * stato tolto un permesso non gli mostrerebbe niente di più di quanto vedrebbe
 * aprendo il menu — è la stessa regola di record, applicata dalla stessa vista.
 *
 * ## Niente barra sopra la tabella
 *
 * Il pannello di controllo della vista è **spento**: niente pulsante *Nuovo*, niente
 * barra di ricerca, niente titolo. La ragione non è estetica.
 *
 * *Nuovo* aprirebbe un modulo di creazione dentro una risposta a una domanda — e **D2**
 * (finché la Fase 2 non è misurata e superata, nessuna scrittura sui dati) dice che da
 * qui non si scrive. Un pulsante che non deve essere premuto è peggio di un pulsante
 * assente.
 *
 * La barra di ricerca sarebbe una **seconda strada per dire cosa si vuole**, accanto
 * alla domanda in italiano che è il prodotto. Due modi di filtrare la stessa tabella,
 * uno dei quali non passa dall'interpretazione e quindi non compare in ciò che AIDA
 * dichiara di aver capito: il numero mostrato smetterebbe di corrispondere alla
 * spiegazione sopra di esso. È lo stesso argomento di D121 — una strada sola — su un
 * altro pezzo.
 *
 * Restano le colonne ordinabili, la selezione, il ridimensionamento e la paginazione,
 * che sono lettura e non riformulazione della domanda.
 */

import { Component } from "@odoo/owl";
import { View } from "@web/views/view";
import { stringToOrderBy } from "@web/search/utils/order_by";

export class AidaRecords extends Component {
    static template = "nli_web.AidaRecords";
    static components = { View };
    static props = {
        query: Object,
    };

    /**
     * Le misure che la vista deve mostrare, dai nomi tecnici del piano.
     *
     * `count` non nomina un attributo (§8.5) e nelle viste di Odoo si chiama
     * `__count`; le altre nominano il campo su cui si calcolano.
     */
    get measureFields() {
        return (this.props.query.measures || [])
            .map((m) => m.field || "__count")
            .filter((name, index, all) => all.indexOf(name) === index);
    }

    get viewProps() {
        const q = this.props.query;
        const orderBy = stringToOrderBy(q.order || "");
        const groupBy = q.group_by || [];
        const measures = this.measureFields;
        return {
            type: q.view === "pivot" || q.view === "graph" ? q.view : "list",
            resModel: q.model,
            domain: q.domain,
            // **L'ordinamento e i raggruppamenti sono proprietà, non contesto.**
            //
            // Fino al 3 agosto 2026 questo componente riceveva `order` dal piano e non
            // lo usava: la vista rileggeva il solo dominio e ordinava come Odoo ordina
            // quel modello per conto suo. *«I 10 lead con il fatturato più alto»*
            // mostrava dieci righe plausibili, ordinate da tutt'altro, sotto
            // un'interpretazione che diceva «ordinati per fatturato, decrescente».
            // Nessun errore da nessuna parte — è la forma di **D2** (una risposta
            // sbagliata con l'aria di essere giusta) applicata alla tabella.
            orderBy,
            groupBy,
            // **Il limite è una proprietà, e la chiave di prima non esisteva.**
            //
            // Fino al 3 agosto 2026 il limite viaggiava come `list_view_limit` nel
            // contesto. Quella chiave **non esiste in Odoo 18** — zero occorrenze in
            // tutto `web/static/src` — quindi non la leggeva nessuno e la tabella
            // mostrava le sue 80 righe predefinite: *«i primi 5 lead»* ne mostrava
            // trentanove. Il piano era giusto, il server leggeva cinque record, e sullo
            // schermo ce n'erano tutti.
            //
            // Odoo 18 la prende da `props.limit` (`list_controller.js`:
            // `this.archInfo.limit || this.props.limit`), quindi è una proprietà come
            // l'ordinamento. È lo **stesso difetto di R2 due volte nello stesso
            // componente**: una chiave passata a chi non la legge, e nessuna prova del
            // lato client che se ne accorga.
            //
            // Resta il punto di partenza della paginazione e non un tetto: l'utente
            // può andare avanti, e il totale sopra la tabella dice quanti sono.
            ...(q.limit ? { limit: q.limit } : {}),
            // Nessun menu di ricerca: la domanda si fa in italiano, non con i filtri.
            searchMenuTypes: [],
            context: {
                // Le misure, per le viste che le sanno mostrare. Senza, il pivot e il
                // grafico ricadono sul conteggio: l'utente leggeva «media di fatturato»
                // sopra un grafico di quantità.
                ...(measures.length && q.view === "pivot"
                    ? { pivot_measures: measures, pivot_row_groupby: groupBy }
                    : {}),
                ...(measures.length && q.view === "graph"
                    ? { graph_measure: measures[0], graph_groupbys: groupBy }
                    : {}),
                // **Qui non c'erano cinque chiavi che vietavano di scrivere: c'erano
                // cinque parole che nessuno leggeva.** `create`, `edit`, `delete`,
                // `duplicate` e `import_enabled` nel contesto sono inerti in Odoo 18 —
                // verificato: `getActiveActions` le prende dagli **attributi dell'arch**
                // e il server le abbassa da solo secondo i diritti
                // (`ir_ui_view._postprocess_access_rights`), e nel client non c'e'
                // nessuna lettura di `context.create`. `import_enabled` non compare
                // nemmeno una volta in tutto il sorgente di Odoo.
                //
                // Toglierle non toglie nessuna garanzia, perche' non ne davano
                // nessuna. Cio' che tiene in piedi **D2** e' altrove, ed e' molto piu'
                // solido: il pannello di controllo e' spento (`display`), quindi i
                // pulsanti non esistono; `editable: false` spegne la modifica in riga,
                // ed e' una proprieta' vera; e soprattutto la catena non scrive mai —
                // e' architettura, non un suggerimento all'interfaccia.
            },
            // Il pannello di controllo è spento per intero: nessuna barra, nessun
            // titolo, nessun pulsante. Resta la tabella e la sua paginazione.
            display: { controlPanel: false },
            allowSelectors: false,
            editable: false,
        };
    }
}
