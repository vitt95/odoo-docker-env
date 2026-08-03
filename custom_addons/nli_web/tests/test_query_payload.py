"""Cio' che la chat riceve deve bastare a disegnare la risposta che l'ha prodotta.

**Perche' questa prova esiste.** `00` §38 raccoglie sette casi di codice dichiarato,
provato e non collegato; il controllo di architettura del 3 agosto ne ha trovati altri
undici, e **due erano proprio qui**. `_aida_query` calcolava `order` e `fields` e li
mandava al client; il componente `AidaRecords` non li usava, e la tabella rileggeva il
solo dominio. *«I 10 lead col fatturato piu' alto»* mostrava dieci righe ordinate da
tutt'altro. Le misure non partivano nemmeno.

La correzione ha due meta' su due lati di un confine — Python e JavaScript — ed e' la
forma che l'errore prende ogni volta: **la prova verde sta sempre da una parte sola**.
Questa prende la meta' Python. Il pezzo che manca al progetto e' un banco di componente
OWL per l'altra, ed e' il punto 2 degli aperti di `ai/restart.md`.
"""

import json

from odoo.tests.common import TransactionCase, tagged

#: Il piano come lo scrive il lavoratore: e' `pipeline._plan_as_dict`.
PIANO = {
    "model": "res.partner",
    "domain": [["city", "=", "Bancopayload"]],
    "fields": ["name", "city"],
    "group_by": ["city"],
    "order": "color desc, name asc",
    "limit": 10,
    "view": "graph",
    "measures": [["avg", "color"], ["count", ""]],
    "resolved_periods": [],
}


@tagged("post_install", "-at_install")
class TestQueryPayload(TransactionCase):
    def turno(self):
        interrogazione = self.env["nli.interrogation"].create({})
        return self.env["nli.turn"].create({
            "interrogation_id": interrogazione.id,
            "user_id": self.env.user.id,
            "company_ids": [(6, 0, self.env.companies.ids)],
            "lang": "it_IT",
            "outcome": "operations",
            "utterance": "quanti partner per citta'",
            "plan_json": json.dumps(PIANO),
        })

    def test_la_query_porta_l_ordinamento(self):
        """Senza, la tabella ordina come ordina Odoo e l'interpretazione mente."""
        query = self.turno()._aida_query()
        self.assertEqual(query["order"], "color desc, name asc")

    def test_la_query_porta_le_misure_con_funzione_e_campo(self):
        """La vista pivot e il grafico senza misure ricadono sul **conteggio**.

        E' il caso peggiore dei due, perche' un grafico di quantita' sotto la scritta
        «media di fatturato» e' una risposta sbagliata con l'aria di essere giusta —
        la forma che **D2** (il cancello che vieta qualunque scrittura sui dati finche'
        la Fase 2 non e' misurata e superata) porta come argomento centrale.
        """
        query = self.turno()._aida_query()
        self.assertEqual(query["measures"],
                         [{"function": "avg", "field": "color"},
                          {"function": "count", "field": ""}])

    def test_la_query_porta_raggruppamenti_e_vista(self):
        query = self.turno()._aida_query()
        self.assertEqual(query["group_by"], ["city"])
        self.assertEqual(query["view"], "graph")

    def test_un_turno_senza_piano_non_produce_una_query(self):
        """La prova gemella: un chiarimento non ha una tabella da disegnare."""
        turno = self.turno()
        turno.write({"outcome": "clarification", "plan_json": False})
        self.assertIsNone(turno._aida_query())

    def test_la_query_porta_il_limite(self):
        """Il limite serve alla tabella **e** alla frase sopra di essa.

        Alla tabella perche' e' con quello che la vista sa quante righe mostrare — e
        fino al 3 agosto 2026 viaggiava come `list_view_limit`, una chiave che in
        Odoo 18 non esiste, quindi *«i primi 5 lead»* ne mostrava trentanove (**D139**).

        Alla frase perche' **D68** (l'Esecutore conta prima di recuperare, per poter
        dire *«i primi 80 di 1 243»*) si giustifica cosi': *«ottanta record senza
        contesto si leggono come tutti quanti»*. Il client la costruisce confrontando il
        totale col limite, e se il limite non arriva non puo' dirla.
        """
        query = self.turno()._aida_query()
        self.assertEqual(query["limit"], 10)

    def test_il_turno_porta_il_totale_accanto_al_limite(self):
        """Le due meta' della frase di D68 devono viaggiare insieme.

        `record_count` e' quanti ne esistono, `query.limit` quanti se ne leggono. Con
        uno solo dei due la chat puo' dire *«39 record trovati»* sopra cinque righe, che
        e' cio' che faceva: vero, e fuorviante.
        """
        turno = self.turno()
        turno.write({"record_count": 39})
        payload = turno._aida_payload()
        self.assertEqual(payload["record_count"], 39)
        self.assertEqual(payload["query"]["limit"], 10)
