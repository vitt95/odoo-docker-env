"""Riferimenti semantici e loro binding tecnico.

Separato dal generatore perche' e' l'unico file del corpus che il **dizionario
semantico** dovra' riprodurre: entita', attributi e categorie con il nome che
l'organizzazione usa, e il legame verso il nome tecnico Odoo.

## Perche' esiste

Il generatore precedente scriveva nomi tecnici (`sale.order.amount_total`) dentro
lo stato atteso. Il criterio **C2** del contratto lo esclude — *semantico, mai
tecnico* — e §5.10 elenca i nomi di modelli e campi fra le cose che lo stato non
contiene. Finche' la validazione tratta un riferimento come stringa opaca la cosa
e' innocua; alla parte 3, quando il dizionario deve risolverli e la copertura di
**D34** va misurata, non lo e' piu'.

## Perche' e' una tabella e non una regola

Gli slug si potrebbero derivare dal primo termine del lessico con una
slugificazione. Sarebbe piu' corto e sbagliato: uno slug e' un **identificativo
stabile** che entra negli stati salvati, e D36 impone che le voci orfane siano
sospese, mai cancellate. Un identificativo generato da un'euristica cambia quando
cambia il lessico, e con esso il significato di ogni interrogazione salvata che lo
nomina. Qui si vede, si rivede in diff, e non cambia da solo.

Il `binding_tecnico` di ogni caso del corpus e' cio' che la parte 3 usera' per
verificare che il dizionario risolva verso il campo giusto.
"""

from __future__ import annotations

#: Entita': slug semantico -> nome tecnico del modello.
#: Le chiavi sono quelle di `lessico_l1.json`; gli slug sono il linguaggio
#: dell'organizzazione, non una traduzione del nome tecnico.
ENTITA: dict[str, str] = {
    "sale.order": "ordini_vendita",
    "sale.order.quotation": "preventivi",
    "account.move.out_invoice": "fatture_cliente",
    "account.move.in_invoice": "fatture_fornitore",
    "account.move.out_refund": "note_credito",
    "res.partner.customer": "clienti",
    "res.partner.supplier": "fornitori",
    "product.template": "prodotti",
    "crm.lead": "opportunita",
    "stock.picking": "documenti_trasporto",
    "purchase.order": "ordini_acquisto",
    "stock.quant": "giacenze",
    "hr.employee": "dipendenti",
}

#: Attributi: campo tecnico -> slug semantico. Ricavato dal primo termine
#: nominale del lessico, fissato qui perche' e' un identificativo.
ATTRIBUTI: dict[str, str] = {
    "partner_id": "cliente",
    "user_id": "venditore",
    "amount_total": "importo_totale",
    "amount_untaxed": "imponibile",
    "amount_tax": "iva",
    "date_order": "data_ordine",
    "invoice_date": "data_fattura",
    "invoice_date_due": "scadenza",
    "state": "stato",
    "commitment_date": "data_consegna",
    "city": "citta",
    "country_id": "paese",
    "phone": "telefono",
    "email": "email",
    "vat": "partita_iva",
    "payment_state": "stato_pagamento",
    "qty_available": "giacenza",
    "categ_id": "categoria",
    "team_id": "team",
    "expected_revenue": "valore_atteso",
    "stage_id": "fase",
}

#: Categorie (T5, condizione nominata): chiave del lessico -> slug semantico.
#: Lo slug non ripete l'entita': `fatture_cliente.scadute`, non
#: `fatture_cliente.fatture_scadute`.
CATEGORIE: dict[str, str] = {
    "fatture_scadute": "scadute",
    "partite_aperte": "partite_aperte",
    "da_fatturare": "da_fatturare",
    "da_consegnare": "da_consegnare",
    "sottoscorta": "sottoscorta",
    "confermati": "confermati",
    "in_bozza": "in_bozza",
    "attivi": "attivi",
    "clienti_importanti": "importanti",
    "fatturato": "fatturato",
}


#: Campi che portano una data, per entita' (D110, l'ancora del tempo dichiarata dal
#: catalogo: una sola data esposta e' l'appiglio implicito di un periodo senza campo;
#: due o piu' non hanno una principale, e l'appiglio giusto e' un chiarimento).
#: Il generatore e il verificatore del corpus leggono da qui, non da due copie: una
#: misura che contasse le date con una lista diversa da quella del generatore
#: misurerebbe un corpus che non e' quello prodotto.
TEMPORALI_PER_ENTITA: dict[str, tuple[str, ...]] = {
    "sale.order": ("date_order",),
    "account.move.out_invoice": ("invoice_date", "invoice_date_due"),
    "res.partner.customer": (),
    "product.template": (),
    "crm.lead": (),
    "stock.picking": (),
}


def riferimento_entita(modello: str) -> str:
    return ENTITA[modello]


def riferimento_attributo(modello: str, campo: str) -> str:
    return f"{ENTITA[modello]}.{ATTRIBUTI[campo]}"


def riferimento_categoria(modello: str, categoria: str) -> str:
    return f"{ENTITA[modello]}.{CATEGORIE[categoria]}"


def binding(modello: str, riferimenti: list[str]) -> dict[str, str]:
    """Semantico -> tecnico, per i soli riferimenti usati da un caso.

    E' il dato che la parte 3 confronta con la risoluzione del dizionario. Le
    categorie non hanno un campo: il loro binding e' la condizione che il
    dizionario definisce, e resta `None` qui perche' il corpus non la conosce.
    """
    inverso_attributi = {v: k for k, v in ATTRIBUTI.items()}
    categorie_slug = set(CATEGORIE.values())
    mappa: dict[str, str] = {}
    for riferimento in riferimenti:
        if "." not in riferimento:
            mappa[riferimento] = modello
            continue
        _, coda = riferimento.split(".", 1)
        if coda in categorie_slug:
            mappa[riferimento] = f"{modello}:categoria"
        elif coda in inverso_attributi:
            mappa[riferimento] = f"{modello}.{inverso_attributi[coda]}"
    return mappa
