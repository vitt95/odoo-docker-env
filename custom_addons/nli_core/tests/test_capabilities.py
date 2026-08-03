"""Il banco delle capacita': ogni operazione di `ai/16`, dalla frase umana al numero.

## Cosa chiede questo banco, e perche' e' diverso dagli altri

`ai/16-controllo-architettura.md` elenca cosa il prodotto deve saper fare: gli intenti
(SELECT, COUNT, SUM, AVG, MIN, MAX, DISTINCT, GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET,
EXISTS, NOT EXISTS, FILTER, SEARCH, EXPORT, PAGINATION), gli operatori (`=`, `!=`, `>`,
`<`, `>=`, `<=`, LIKE, ILIKE, IN, NOT IN, BETWEEN, IS NULL, IS NOT NULL, CONTAINS,
STARTS WITH, ENDS WITH) e le date relative (oggi, ieri, domani, questa settimana, mese
scorso, ultimi 7/30/90 giorni, quest'anno, anno scorso, i trimestri, i mesi nominati).

`ai/17` §3 ha risposto **a tavolino** quali di queste ci sono e quali no. Questo banco
risponde **eseguendole**. I JOIN sono fuori di proposito: non esistono (reperto R5) e
sono una delibera da prendere, non una prova da scrivere.

Ogni caso porta nel proprio nome la frase italiana che rappresenta, perche' e' quello il
metro: non *«il contratto ammette il predicato `starts_with`»*, ma *«i partner che
iniziano per Del»* restituisce **Delta e nessun altro**.

## Cosa questo banco non fa, e va detto

**Non chiama il modello.** Parte dallo stato, non dalla frase, e percorre risolutore,
esecutore e presentatore veri. Che il modello traduca *«i primi 10 per fatturato»* in
quello stato e' un'altra domanda, e ha un altro strumento: la misura di accuratezza sul
corpus. Confondere le due cose renderebbe questo banco non deterministico — il modello
sbaglia a caso, e una prova che sbaglia a caso non e' una prova.

Quindi qui si legge: *dato che la frase e' stata capita, il prodotto sa rispondere?*

## Quello che non si puo' dire

L'ultima classe e' l'altra meta' del lavoro: le operazioni di `16` che **non sono
esprimibili**, ciascuna con la prova che lo dimostra sul contratto. Servono quanto le
altre. Un buco che nessuno misura torna a farsi credere una svista, e la prima volta che
qualcuno scrivera' `HAVING` in una specifica sara' comodo poter dire *«e' fuori portata
per costruzione, ecco la riga che lo dice»* invece di *«mi pare di no»*.

## Perche' i dati se li crea

Come per `test_answers.py`: `nli_test` porta 50 004 partner del popolatore, e ogni caso
qui dentro lavora dietro una condizione su una citta' che nessun popolatore produce. Su
un database vuoto e su uno pieno il perimetro e' lo stesso — quello che il caso ha
creato.
"""

from datetime import date, datetime

from odoo.tests import TransactionCase, tagged

from ..contract import vocabulary
from ..execution import executor
from ..presentation import presenter
from ..resolution import calendar as calendar_module
from ..resolution import resolver as resolver_module
from ..resolution.plan import Binding
from ..validation import structural

#: Le due citta' del banco: la prima e' il perimetro di quasi ogni caso, la seconda
#: serve ai raggruppamenti, che senza un secondo gruppo non provano niente.
CITTA = "Bancocapacita"
ALTRA = "Altracapacita"

#: I partner del banco. Le risposte si fanno a mente: nel perimetro i valori sono
#: 10, 20, 30, 40, 40 — somma 140, media 28, minimo 10, massimo 40, e **quattro**
#: valori distinti su cinque righe, che e' cio' che rende DISTINCT diverso da COUNT.
#:
#: Le date **non** stanno qui: `create_date` non e' scrivibile in Odoo 18, ne' in
#: `create` ne' in `write` — provato. Le date hanno il loro banco piu' sotto, su
#: un'entita' che una data scrivibile ce l'ha.
ANAGRAFICA = [
    # nome,             valore, citta,  posta,              commerciale, genere,    azienda
    ("Alfa capacita",    10, CITTA, "alfa@banco.test",  True,  "contact", True),
    ("Beta capacita",    20, CITTA, False,              False, "contact", True),
    ("Gamma capacita",   30, CITTA, "gamma@banco.test", False, "invoice", False),
    ("Delta capacita",   40, CITTA, "delta@banco.test", True,  "contact", False),
    ("Epsilon capacita", 40, CITTA, "eps@banco.test",   False, "contact", False),
    ("Zeta capacita",    90, ALTRA, "zeta@banco.test",  True,  "contact", False),
    ("Eta capacita",     70, ALTRA, "eta@banco.test",   False, "contact", False),
]

BINDINGS = {
    "partner": Binding(kind="attribute", field="", type="entity"),
    "partner.nome": Binding(kind="attribute", field="name", type="text"),
    "partner.valore": Binding(kind="attribute", field="color", type="number"),
    "partner.citta": Binding(kind="attribute", field="city", type="text"),
    "partner.posta": Binding(kind="attribute", field="email", type="text"),
    "partner.genere": Binding(kind="attribute", field="type", type="enum"),
    "partner.azienda": Binding(kind="attribute", field="is_company", type="boolean"),
    "partner.commerciale": Binding(kind="attribute", field="user_id", type="relation"),
}


class BancoCapacita(TransactionCase):
    """L'impalcatura: i dati, l'istante fisso, e la coda vera della conduttura."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        commerciale = cls.env.ref("base.user_admin")
        cls.partners = cls.env["res.partner"].create([
            {
                "name": nome, "color": valore, "city": citta,
                "email": posta, "type": genere, "is_company": azienda,
                "user_id": commerciale.id if ha_commerciale else False,
            }
            for nome, valore, citta, posta, ha_commerciale, genere, azienda
            in ANAGRAFICA
        ])
        # Un istante fisso: il banco non deve dipendere da quando gira, che e' la
        # stessa ragione per cui il Risolutore riceve l'istante invece di leggerlo
        # (§13.3). Il 3 agosto 2026 e' anche il giorno della batteria sul campo.
        cls.instant = calendar_module.Instant(
            now=datetime(2026, 8, 3, 9, 0), timezone="Europe/Rome")

    # -- l'impalcatura -----------------------------------------------------

    def perimetro(self, *citta):
        """La condizione che tiene fuori i 50 004 partner del popolatore."""
        return {"id": "c0", "ref": "partner.citta", "predicate": "is_one_of",
                "origin": "user",
                "value": {"kind": "enum", "items": list(citta or (CITTA,))}}

    def stato(self, condizione=None, **sezioni):
        """Uno stato completo, col perimetro e — se data — una condizione in `all`."""
        filtro = self.perimetro()
        if condizione is not None:
            filtro = {"connective": "all",
                      "conditions": [self.perimetro(), condizione]}
        stato = {
            "dsl_version": "1.0",
            "target": {"ref": "partner", "origin": "user"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred"},
            "filter": filtro,
        }
        stato.update(sezioni)
        return stato

    def rispondi(self, stato):
        risoluzione = resolver_module.resolve(
            stato, bindings=BINDINGS, instant=self.instant, model="res.partner")
        self.assertTrue(risoluzione.resolved,
                        f"il piano non si e' risolto: {risoluzione.failures}")
        risultato = executor.run(self.env, risoluzione.plan)
        mostrato = presenter.present(
            state=stato, plan=risoluzione.plan, result=risultato)
        return risoluzione.plan, risultato, mostrato

    def nomi(self, condizione=None, **sezioni):
        """I nomi trovati, in ordine alfabetico: quasi ogni caso si legge cosi'."""
        _, risultato, _ = self.rispondi(self.stato(condizione, **sezioni))
        return sorted(risultato.records.mapped("name"))

    def condizione(self, ref, predicate, value=None, identifier="c1"):
        condizione = {"id": identifier, "ref": ref, "predicate": predicate,
                      "origin": "user"}
        if value is not None:
            condizione["value"] = value
        return condizione

    def misura(self, gruppo, funzione, campo=""):
        return gruppo.measures[(funzione, campo)]


@tagged("post_install", "-at_install")
class TestGliIntenti(BancoCapacita):
    """La lista INTENT DETECTION di `16`, eseguita una voce alla volta."""

    def test_select_i_partner_di_bancocapacita(self):
        """*«Mostrami i partner di Bancocapacita»* — l'intento piu' semplice, ed e'
        quello su cui poggiano tutti gli altri: il perimetro e' esatto."""
        self.assertEqual(self.nomi(), [
            "Alfa capacita", "Beta capacita", "Delta capacita", "Epsilon capacita",
            "Gamma capacita",
        ])

    def test_select_con_le_colonne_che_la_frase_nomina(self):
        """*«Mostrami i partner con nome e valore»* — SELECT di colonne.

        Il piano le porta. Che arrivino **alla tabella** e' l'altra meta' (reperto R2
        dell'audit) e si prova in `nli_web`, oltre il confine.
        """
        piano, _, _ = self.rispondi(self.stato(fields=[
            {"ref": "partner.nome", "origin": "user"},
            {"ref": "partner.valore", "origin": "user"},
        ]))
        self.assertEqual(piano.fields, ("name", "color"))

    def test_search_i_partner_che_hanno_amma_nel_nome(self):
        """*«Cerca i partner con “amma” nel nome»* — SEARCH."""
        self.assertEqual(
            self.nomi(self.condizione("partner.nome", "contains",
                                      {"kind": "text", "text": "amma"})),
            ["Gamma capacita"])

    def test_filter_i_partner_che_valgono_piu_di_trenta(self):
        """*«Solo quelli sopra 30»* — FILTER."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "greater_than",
                                      {"kind": "number", "value": 30})),
            ["Delta capacita", "Epsilon capacita"])

    def test_count_quanti_partner_ci_sono(self):
        """*«Quanti partner ci sono a Bancocapacita»* — COUNT.

        Il conteggio arriva da due strade e devono dire la stessa cosa: il totale di
        **D68** (il conteggio prima del recupero, per poter dire *«i primi 80 di
        1 243»*) e la misura calcolata dall'aggregazione.
        """
        _, risultato, _ = self.rispondi(self.stato(
            measures=[{"function": "count", "origin": "user"}]))
        self.assertEqual(risultato.total, 5)
        self.assertEqual(self.misura(risultato.groups[0], "count"), 5)

    def test_sum_quanto_valgono_in_tutto(self):
        """*«Quanto valgono in tutto»* — SUM. 10+20+30+40+40 = 140."""
        _, risultato, _ = self.rispondi(self.stato(
            measures=[{"function": "sum", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertEqual(self.misura(risultato.groups[0], "sum", "color"), 140)

    def test_avg_qual_e_il_valore_medio(self):
        """*«Qual e' il valore medio»* — AVG. 140 su 5 = 28.

        **Prima del 3 agosto 2026 questo non aveva risposta**: `executor.aggregate`
        non era chiamata da nessuno e l'utente riceveva l'elenco. E il numero deve
        arrivare **all'utente**, non fermarsi nel risultato.
        """
        _, risultato, mostrato = self.rispondi(self.stato(
            measures=[{"function": "avg", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertAlmostEqual(self.misura(risultato.groups[0], "avg", "color"), 28.0)
        self.assertIn({"function": "avg", "ref": "color", "value": 28.0},
                      mostrato.interpretation["results"][0]["measures"])

    def test_min_e_max_il_piu_piccolo_e_il_piu_grande(self):
        """*«Il valore minimo e il massimo»* — MIN e MAX, insieme perche' e' cosi'
        che si chiedono."""
        _, risultato, _ = self.rispondi(self.stato(measures=[
            {"function": "min", "ref": "partner.valore", "origin": "user"},
            {"function": "max", "ref": "partner.valore", "origin": "user"},
        ]))
        gruppo = risultato.groups[0]
        self.assertEqual(self.misura(gruppo, "min", "color"), 10)
        self.assertEqual(self.misura(gruppo, "max", "color"), 40)

    def test_distinct_quanti_valori_diversi(self):
        """*«Quanti valori diversi»* — DISTINCT.

        Cinque righe, **quattro** valori: 40 c'e' due volte. Se DISTINCT non contasse
        davvero i distinti, qui direbbe cinque e la prova diventerebbe rossa — che e'
        l'unico modo di provare un DISTINCT.
        """
        _, risultato, _ = self.rispondi(self.stato(
            measures=[{"function": "count_distinct", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertEqual(
            self.misura(risultato.groups[0], "count_distinct", "color"), 4)

    def test_group_by_quanti_partner_per_citta(self):
        """*«Quanti partner per citta'»* — GROUP BY."""
        _, risultato, _ = self.rispondi(self.stato(
            filter=self.perimetro(CITTA, ALTRA),
            group_by=[{"ref": "partner.citta", "origin": "user"}],
            measures=[{"function": "count", "origin": "user"}]))
        self.assertEqual(
            {gruppo.keys[0]: self.misura(gruppo, "count")
             for gruppo in risultato.groups},
            {CITTA: 5, ALTRA: 2})

    def test_group_by_multiplo_per_citta_e_per_tipo(self):
        """*«Quanti partner per citta' e per azienda o persona»* — GROUP BY multipli.

        Quattro gruppi: a Bancocapacita due aziende e tre persone, ad Altracapacita
        due persone e nessuna azienda.
        """
        _, risultato, _ = self.rispondi(self.stato(
            filter=self.perimetro(CITTA, ALTRA),
            group_by=[{"ref": "partner.citta", "origin": "user"},
                      {"ref": "partner.azienda", "origin": "user"}],
            measures=[{"function": "count", "origin": "user"}]))
        self.assertEqual(
            {gruppo.keys: self.misura(gruppo, "count")
             for gruppo in risultato.groups},
            {(CITTA, True): 2, (CITTA, False): 3, (ALTRA, False): 2})

    def test_group_by_con_una_misura_da_il_numero_di_ogni_gruppo(self):
        """*«Il valore massimo per citta'»* — il caso che l'utente chiede davvero."""
        _, risultato, _ = self.rispondi(self.stato(
            filter=self.perimetro(CITTA, ALTRA),
            group_by=[{"ref": "partner.citta", "origin": "user"}],
            measures=[{"function": "max", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertEqual(
            {gruppo.keys[0]: self.misura(gruppo, "max", "color")
             for gruppo in risultato.groups},
            {CITTA: 40, ALTRA: 90})

    def test_order_by_dal_valore_piu_alto(self):
        """*«Ordinati dal valore piu' alto»* — ORDER BY."""
        _, risultato, _ = self.rispondi(self.stato(
            order_by=[{"ref": "partner.valore", "direction": "desc",
                       "origin": "user"}]))
        self.assertEqual(
            [record.color for record in risultato.records], [40, 40, 30, 20, 10])

    def test_order_by_multiplo_prima_il_valore_poi_il_nome(self):
        """*«Ordinati per valore decrescente e poi per nome»* — ORDER multipli.

        I due che valgono 40 sono Delta ed Epsilon, e il secondo criterio decide fra
        loro: se l'ordinamento portasse solo il primo, qui l'ordine sarebbe quello del
        modello e la prova cadrebbe.
        """
        piano, risultato, _ = self.rispondi(self.stato(order_by=[
            {"ref": "partner.valore", "direction": "desc", "origin": "user"},
            {"ref": "partner.nome", "direction": "asc", "origin": "user"},
        ]))
        self.assertEqual(piano.order, "color desc, name asc")
        self.assertEqual(list(risultato.records.mapped("name")), [
            "Delta capacita", "Epsilon capacita", "Gamma capacita",
            "Beta capacita", "Alfa capacita",
        ])

    def test_limit_i_primi_due(self):
        """*«I primi 2 per valore»* — LIMIT."""
        _, risultato, _ = self.rispondi(self.stato(
            order_by=[{"ref": "partner.valore", "direction": "desc",
                       "origin": "user"}],
            limit={"value": 2, "origin": "user"}))
        self.assertEqual(len(risultato.records), 2)
        self.assertEqual(sorted(risultato.records.mapped("name")),
                         ["Delta capacita", "Epsilon capacita"])

    def test_pagination_dice_quanti_sono_quelli_che_non_si_vedono(self):
        """PAGINATION nel senso di **D68**: *«i primi 2 di 5»*.

        Ottanta record senza contesto si leggono come *tutti quanti*. Il totale non e'
        decorazione: e' cio' che distingue una risposta completa da una troncata.
        """
        _, risultato, _ = self.rispondi(self.stato(
            limit={"value": 2, "origin": "user"}))
        self.assertEqual(risultato.total, 5)
        self.assertTrue(risultato.truncated)
        self.assertEqual(risultato.describe(), "i primi 2 di 5")

    def test_exists_i_partner_che_hanno_un_commerciale(self):
        """*«I partner che hanno un commerciale»* — EXISTS, nella forma semplice.

        `16` chiede EXISTS su una relazione. Quello che c'e' e' la relazione presa
        come un tutto: *«ce l'ha o non ce l'ha»*. Una condizione **sull'entita' in
        fondo alla relazione** — *«che hanno un commerciale di Roma»* — richiede i
        JOIN e non esiste (reperto R5).
        """
        self.assertEqual(
            self.nomi(self.condizione("partner.commerciale", "is_set")),
            ["Alfa capacita", "Delta capacita"])

    def test_not_exists_i_partner_senza_commerciale(self):
        """*«I partner senza commerciale»* — NOT EXISTS."""
        self.assertEqual(
            self.nomi(self.condizione("partner.commerciale", "is_not_set")),
            ["Beta capacita", "Epsilon capacita", "Gamma capacita"])


@tagged("post_install", "-at_install")
class TestGliOperatori(BancoCapacita):
    """La lista OPERATORI di `16`. Uno per prova, con la frase che lo dice."""

    def test_uguale(self):
        """`=` — *«quelli che valgono esattamente 30»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "equals",
                                      {"kind": "number", "value": 30})),
            ["Gamma capacita"])

    def test_maggiore(self):
        """`>` — *«sopra 30»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "greater_than",
                                      {"kind": "number", "value": 30})),
            ["Delta capacita", "Epsilon capacita"])

    def test_minore(self):
        """`<` — *«sotto 30»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "less_than",
                                      {"kind": "number", "value": 30})),
            ["Alfa capacita", "Beta capacita"])

    def test_maggiore_o_uguale(self):
        """`>=` — *«da 40 in su»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "greater_or_equal",
                                      {"kind": "number", "value": 40})),
            ["Delta capacita", "Epsilon capacita"])

    def test_minore_o_uguale(self):
        """`<=` — *«fino a 20»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "less_or_equal",
                                      {"kind": "number", "value": 20})),
            ["Alfa capacita", "Beta capacita"])

    def test_between_fra_venti_e_quaranta(self):
        """`BETWEEN` — *«fra 20 e 40»*, estremi **inclusi** tutti e due.

        Su una data `between` non esiste piu': **D113** l'ha tolto perche' era il
        doppione di `within` e il modello sceglieva a caso fra i due. Sui numeri resta,
        ed e' l'unico posto in cui vive.
        """
        self.assertEqual(
            self.nomi(self.condizione("partner.valore", "between",
                                      {"kind": "range", "from": 20, "to": 40})),
            ["Beta capacita", "Delta capacita", "Epsilon capacita",
             "Gamma capacita"])

    def test_contains_e_like(self):
        """`CONTAINS` / `LIKE` — *«che contengono “apacita”»*."""
        self.assertEqual(len(self.nomi(
            self.condizione("partner.nome", "contains",
                            {"kind": "text", "text": "apacita"}))), 5)

    def test_ilike_non_distingue_maiuscole_e_minuscole(self):
        """`ILIKE` — *«che contengono “GAMMA”»* trova *Gamma*.

        Non e' un dettaglio di comodo: chi scrive in una casella non guarda le
        maiuscole, e `contains` si traduce in `ilike` proprio per questo.
        """
        self.assertEqual(
            self.nomi(self.condizione("partner.nome", "contains",
                                      {"kind": "text", "text": "GAMMA"})),
            ["Gamma capacita"])

    def test_starts_with(self):
        """`STARTS WITH` — *«che iniziano per Del»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.nome", "starts_with",
                                      {"kind": "text", "text": "Del"})),
            ["Delta capacita"])

    def test_in_su_un_testo(self):
        """`IN` — *«di Bancocapacita o di Altracapacita»*."""
        _, risultato, _ = self.rispondi(self.stato(
            filter=self.perimetro(CITTA, ALTRA)))
        self.assertEqual(risultato.total, 7)

    def test_not_in_su_un_enumerato(self):
        """`NOT IN` — *«che non sono contatti»*.

        Vive **solo** sugli enumerati e sulle relazioni. Su un testo e su un numero non
        si puo' dire, ed e' scritto fra le cose che mancano, in fondo.
        """
        self.assertEqual(
            self.nomi(self.condizione("partner.genere", "is_not_one_of",
                                      {"kind": "enum", "items": ["contact"]})),
            ["Gamma capacita"])

    def test_is_null(self):
        """`IS NULL` — *«quelli senza posta elettronica»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.posta", "is_empty")),
            ["Beta capacita"])

    def test_is_not_null(self):
        """`IS NOT NULL` — *«quelli con la posta elettronica»*."""
        self.assertEqual(
            self.nomi(self.condizione("partner.posta", "is_not_empty")),
            ["Alfa capacita", "Delta capacita", "Epsilon capacita",
             "Gamma capacita"])

    def test_vero_e_falso(self):
        """*«Le aziende»* e *«le persone»* — un booleano ha due predicati, non uno."""
        self.assertEqual(
            self.nomi(self.condizione("partner.azienda", "is_true")),
            ["Alfa capacita", "Beta capacita"])
        self.assertEqual(
            self.nomi(self.condizione("partner.azienda", "is_false")),
            ["Delta capacita", "Epsilon capacita", "Gamma capacita"])

    def test_i_connettivi_e_e_o(self):
        """*«Sopra 30 **e** senza commerciale»*, e poi *«sopra 30 **o** senza posta»*.

        Gli operatori senza i connettivi rispondono a meta' delle domande vere.
        """
        _, risultato, _ = self.rispondi(self.stato(filter={
            "connective": "all", "conditions": [
                self.perimetro(),
                self.condizione("partner.valore", "greater_than",
                                {"kind": "number", "value": 30}),
                self.condizione("partner.commerciale", "is_not_set", identifier="c2"),
            ]}))
        self.assertEqual(list(risultato.records.mapped("name")),
                         ["Epsilon capacita"])

        _, risultato, _ = self.rispondi(self.stato(filter={
            "connective": "all", "conditions": [
                self.perimetro(),
                {"connective": "any", "conditions": [
                    self.condizione("partner.valore", "greater_than",
                                    {"kind": "number", "value": 30}),
                    self.condizione("partner.posta", "is_empty", identifier="c2"),
                ]},
            ]}))
        self.assertEqual(sorted(risultato.records.mapped("name")),
                         ["Beta capacita", "Delta capacita", "Epsilon capacita"])


@tagged("post_install", "-at_install")
class TestLeDate(TransactionCase):
    """La lista DATE RESOLUTION di `16`, ciascuna contro le righe che deve prendere.

    **Perche' questa classe ha un'entita' tutta sua.** Le date del banco devono essere
    scelte dal banco, e su `res.partner` non ce n'e' una che si possa scegliere:
    `create_date` **non e' scrivibile** in Odoo 18 — non in `create`, non in `write`,
    provato — e nessun altro campo data risulta scrivibile e memorizzato.

    Un banco che ci provasse lo stesso non fallirebbe: prenderebbe l'ora in cui gira, e
    *«creati oggi»* troverebbe tutto perche' tutto e' stato creato adesso. **Una prova
    che passa perche' non distingue niente e' peggio di una prova che manca**, ed e'
    la lezione di `00` §39.7 un giro piu' stretto.

    Quindi le date si provano dove una data si puo' scrivere: i **cambi di valuta**,
    che hanno il giorno come campo proprio (`res.currency.rate.name`) e su una valuta
    inventata dal banco non danno fastidio a nessuno. E' un `date` puro, senza ore,
    quindi il fuso non c'entra: quello vive su un `datetime` e ha il suo banco in
    `test_answers.py`.
    """

    #: I giorni del banco, e cosa ciascuno serve a distinguere. L'istante e' il
    #: 3 agosto 2026: quindi 3 = oggi, 2 = ieri, 4 = domani.
    GIORNI = {
        "oggi": date(2026, 8, 3),
        "ieri": date(2026, 8, 2),
        "domani": date(2026, 8, 4),
        "mese scorso": date(2026, 7, 15),
        "trimestre scorso": date(2026, 5, 20),
        "quest'anno": date(2026, 1, 10),
        "anno scorso": date(2025, 11, 20),
    }

    BINDINGS = {
        "cambio": Binding(kind="attribute", field="", type="entity"),
        "cambio.giorno": Binding(kind="attribute", field="name", type="date"),
        "cambio.valuta": Binding(kind="attribute", field="currency_id",
                                 type="relation"),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.valuta = cls.env["res.currency"].create({
            "name": "ZZB", "symbol": "Z", "rounding": 0.01,
        })
        cls.env["res.currency.rate"].create([
            {"name": giorno, "rate": 1 + indice / 100,
             "currency_id": cls.valuta.id, "company_id": False}
            for indice, giorno in enumerate(cls.GIORNI.values())
        ])
        cls.instant = calendar_module.Instant(
            now=datetime(2026, 8, 3, 9, 0), timezone="Europe/Rome")

    def perimetro(self):
        """Solo i cambi della valuta inventata qui: le altre valute hanno le loro
        quotazioni e non sono affari di questo banco."""
        return {"id": "c0", "ref": "cambio.valuta", "predicate": "is_one_of",
                "origin": "user",
                "value": {"kind": "enum", "items": [self.valuta.id]}}

    def giorni(self, espressione, **extra):
        """I giorni che l'espressione seleziona, in ordine."""
        stato = {
            "dsl_version": "1.0",
            "target": {"ref": "cambio", "origin": "user"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred"},
            "filter": {"connective": "all", "conditions": [
                self.perimetro(),
                {"id": "c1", "ref": "cambio.giorno", "predicate": "within",
                 "origin": "user",
                 "value": {"kind": "temporal", "expression": espressione, **extra}},
            ]},
        }
        risoluzione = resolver_module.resolve(
            stato, bindings=self.BINDINGS, instant=self.instant,
            model="res.currency.rate")
        self.assertTrue(risoluzione.resolved,
                        f"il piano non si e' risolto: {risoluzione.failures}")
        risultato = executor.run(self.env, risoluzione.plan)
        return sorted(risultato.records.mapped("name"))

    def il(self, *etichette):
        return sorted(self.GIORNI[etichetta] for etichetta in etichette)

    # -- le date relative --------------------------------------------------

    def test_oggi(self):
        """*«Di oggi»*."""
        self.assertEqual(self.giorni("today"), self.il("oggi"))

    def test_ieri(self):
        """*«Di ieri»*."""
        self.assertEqual(self.giorni("yesterday"), self.il("ieri"))

    def test_domani(self):
        """*«Di domani»* — una data futura e' una condizione come le altre."""
        self.assertEqual(self.giorni("tomorrow"), self.il("domani"))

    def test_questa_settimana_contiene_oggi(self):
        """*«Di questa settimana»*.

        Si asserisce che **oggi ci sia dentro**, non quali giorni siano: il primo
        giorno della settimana e' un dato dell'installazione, e una prova che lo
        fissasse proverebbe la propria copia della regola invece di quella vera.
        """
        self.assertIn(self.GIORNI["oggi"], self.giorni("current_week"))

    def test_la_settimana_scorsa_non_contiene_oggi(self):
        """*«Della settimana scorsa»* — la meta' gemella, e senza di lei la prima
        passerebbe anche se le due finestre fossero la stessa."""
        self.assertNotIn(self.GIORNI["oggi"], self.giorni("previous_week"))

    def test_questo_mese(self):
        """*«Di questo mese»* — agosto: ieri, oggi e domani."""
        self.assertEqual(self.giorni("current_month"),
                         self.il("ieri", "oggi", "domani"))

    def test_il_mese_scorso(self):
        """*«Del mese scorso»* — luglio."""
        self.assertEqual(self.giorni("previous_month"), self.il("mese scorso"))

    def test_ultimi_sette_giorni(self):
        """*«Degli ultimi 7 giorni»* — oggi conta, domani no."""
        self.assertEqual(self.giorni("last_n_days", n=7), self.il("ieri", "oggi"))

    def test_ultimi_trenta_giorni(self):
        """*«Degli ultimi 30 giorni»* — entra anche il 15 luglio."""
        self.assertEqual(self.giorni("last_n_days", n=30),
                         self.il("mese scorso", "ieri", "oggi"))

    def test_ultimi_novanta_giorni(self):
        """*«Degli ultimi 90 giorni»* — entra anche il 20 maggio, e **non** il 10
        gennaio: e' la differenza che rende la prova capace di fallire."""
        self.assertEqual(self.giorni("last_n_days", n=90),
                         self.il("trimestre scorso", "mese scorso", "ieri", "oggi"))

    def test_quest_anno(self):
        """*«Di quest'anno»* — tutti tranne quello del 2025.

        **E' la frase della batteria del 3 agosto 2026**, quella che ha portato a D135
        (la domanda su quale data la costruiamo noi) e poi a D136 (l'interpretazione
        mostra l'insieme interrogato, non la finestra dell'espressione).
        """
        self.assertEqual(
            self.giorni("current_year"),
            self.il("quest'anno", "trimestre scorso", "mese scorso", "ieri", "oggi",
                    "domani"))

    def test_l_anno_scorso(self):
        """*«Dell'anno scorso»* — il solo del 2025."""
        self.assertEqual(self.giorni("previous_year"), self.il("anno scorso"))

    def test_questo_trimestre(self):
        """*«Di questo trimestre»* — luglio-settembre."""
        self.assertEqual(self.giorni("current_quarter"),
                         self.il("mese scorso", "ieri", "oggi", "domani"))

    def test_il_trimestre_scorso(self):
        """*«Del trimestre scorso»* — aprile-giugno.

        I trimestri **nominati** — *«nel primo trimestre»*, `Q1` — sono un'altra cosa
        e non ci sono: e' provato in fondo, fra le cose che non si possono dire.
        """
        self.assertEqual(self.giorni("previous_quarter"), self.il("trimestre scorso"))

    def test_dall_inizio_dell_anno_a_oggi(self):
        """*«Da inizio anno»* — **D91**: si ferma a oggi, quindi domani resta fuori.
        E' la differenza con *«quest'anno»*, ed e' il motivo per cui sono due
        espressioni e non una."""
        self.assertEqual(
            self.giorni("year_to_date"),
            self.il("quest'anno", "trimestre scorso", "mese scorso", "ieri", "oggi"))

    def test_una_data_precisa(self):
        """*«Del 2 agosto 2026»* — una data che l'utente ha detto per esteso."""
        self.assertEqual(self.giorni("absolute", date="2026-08-02"), self.il("ieri"))

    def test_un_intervallo_preciso(self):
        """*«Fra il 1 e il 31 gennaio 2026»* — l'unico modo di dire *«gennaio»*.

        Funziona, ed e' proprio qui che si vede il buco: il prompt vieta al modello di
        risolvere una data (*«never resolve a date»*), quindi un mese nominato non
        arriva mai fin qui. La contraddizione e' registrata, non risolta.
        """
        self.assertEqual(
            self.giorni("absolute_range", **{"from": "2026-01-01", "to": "2026-01-31"}),
            self.il("quest'anno"))

    def test_prima_e_dopo_prendono_un_lato_solo(self):
        """*«Prima di questo mese»* e *«dopo questo mese»* — **D136**.

        `before` prende il lato sinistro della finestra e `after` il destro, e
        l'interpretazione lo dice. Il caso sul campo era questo con `after
        current_year`: il dominio diceva *dopo la fine del 2026*, zero record, e
        l'interpretazione mostrava l'anno intero.
        """
        stato = {
            "dsl_version": "1.0",
            "target": {"ref": "cambio", "origin": "user"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred"},
            "filter": {"connective": "all", "conditions": [
                self.perimetro(),
                {"id": "c1", "ref": "cambio.giorno", "predicate": "before",
                 "origin": "user",
                 "value": {"kind": "temporal", "expression": "current_month"}},
            ]},
        }
        risoluzione = resolver_module.resolve(
            stato, bindings=self.BINDINGS, instant=self.instant,
            model="res.currency.rate")
        risultato = executor.run(self.env, risoluzione.plan)
        mostrato = presenter.present(
            state=stato, plan=risoluzione.plan, result=risultato)
        self.assertEqual(
            sorted(risultato.records.mapped("name")),
            self.il("anno scorso", "quest'anno", "trimestre scorso", "mese scorso"))
        self.assertEqual(mostrato.interpretation["periods"],
                         [{"ref": "cambio.giorno", "resolved": "< 2026-08-01"}])


@tagged("post_install", "-at_install")
class TestQuelloCheNonSiPuoDire(BancoCapacita):
    """Le voci di `16` che il contratto **non** ammette, ciascuna con la sua prova.

    Non sono difetti da sistemare di corsa: sono la distanza fra l'obiettivo dichiarato
    e il contratto di oggi, e vanno sapute con precisione. Ognuna e' provata sul
    vocabolario, che e' l'unico posto dove una cosa che non esiste si puo' asserire.
    """

    def test_having_una_condizione_su_un_aggregato_non_e_esprimibile(self):
        """*«Le citta' con piu' di 10 partner»* — HAVING.

        Una condizione porta un valore, e i tipi di valore ammessi sono sette: testo,
        numero, intervallo, enumerato, booleano, temporale, riferimento. **Nessuno di
        loro e' un aggregato**, quindi non c'e' modo di scrivere *«il conteggio > 10»*.

        E' una scelta dichiarata (V-D87-2), non una svista: un `HAVING` costa una
        seconda passata sui dati e il livello 5 esiste per rendere il costo calcolabile
        prima di eseguire. Quelle domande sono **fuori portata per costruzione**.
        """
        self.assertNotIn("aggregate", vocabulary.VALUE_KINDS)
        for kinds in vocabulary.PREDICATE_VALUE_KINDS.values():
            self.assertNotIn("aggregate", kinds)

    def test_offset_non_esiste(self):
        """*«I secondi 20»* — OFFSET.

        Non c'e' un'operazione che lo scriva. La paginazione e' quella della vista
        incorporata (`00` §33.4), che e' una risposta ragionevole e **diversa** da
        quella che `16` immagina.
        """
        self.assertNotIn("set_offset", vocabulary.OPERATIONS)
        self.assertFalse([operazione for operazione in vocabulary.OPERATIONS
                          if "offset" in operazione])

    def test_export_non_esiste(self):
        """*«Esportamelo in Excel»* — EXPORT. Nessuna operazione lo nomina."""
        self.assertFalse([operazione for operazione in vocabulary.OPERATIONS
                          if "export" in operazione])

    def test_diverso_da_non_esiste_su_testi_e_numeri(self):
        """*«Diverso da»* — `!=`, il reperto M8 dell'audit.

        `is_not_one_of` c'e', ma solo sugli enumerati e sulle relazioni. Su un testo e
        su un numero non si puo' dire *«che non e' Roma»*, ed e' una delle prime cose
        che una persona dice.
        """
        self.assertNotIn("not_equals", vocabulary.PREDICATES)
        self.assertNotIn("is_not_one_of", vocabulary.PREDICATES_BY_TYPE["text"])
        self.assertNotIn("is_not_one_of", vocabulary.PREDICATES_BY_TYPE["number"])

    def test_finisce_per_non_esiste(self):
        """*«Che finisce per SRL»* — ENDS WITH, sempre M8. `starts_with` c'e', la sua
        gemella no."""
        self.assertIn("starts_with", vocabulary.PREDICATES_BY_TYPE["text"])
        self.assertNotIn("ends_with", vocabulary.PREDICATES)

    def test_la_negazione_non_e_producibile(self):
        """*«I partner che non sono di Roma»* — il reperto M7.

        Lo stato ammette il connettivo `not` e il risolutore lo traduce, ma **nessuna
        operazione lo puo' creare**: `add_condition` accetta `combine` solo fra `all` e
        `any`. Un simbolo dichiarato e irraggiungibile, e stavolta nel contratto.
        """
        self.assertIn("not", vocabulary.CONNECTIVES)
        self.assertEqual(set(structural.COMBINE_VALUES), {"all", "any"})

    def test_i_trimestri_nominati_e_i_mesi_nominati_non_esistono(self):
        """*«Nel primo trimestre»*, *«a gennaio»*.

        Ci sono `current_quarter` e `previous_quarter`, che sono un'altra cosa: dicono
        *«questo»* e *«scorso»*, non *«il primo»*. Un mese nominato si puo' dire con
        `absolute_range` — provato sopra — ma solo se qualcuno ne calcola gli estremi,
        e il prompt lo vieta proprio al modello. **E' una contraddizione fra il prompt
        e il vocabolario**, ed e' da deliberare.
        """
        for nominato in ("q1", "q2", "q3", "q4", "january", "gennaio", "named_month"):
            self.assertNotIn(nominato, vocabulary.TEMPORAL_EXPRESSIONS)

    def test_le_aggregazioni_annidate_non_esistono(self):
        """*«La media dei totali per cliente»* — aggregazioni annidate.

        Una misura si applica a un **attributo**, e i tipi che ogni aggregazione
        ammette sono tipi di attributo: nessuno di loro e' una misura. Quindi non c'e'
        modo di aggregare un aggregato.
        """
        for tipi in vocabulary.AGGREGATION_TYPES.values():
            self.assertNotIn("aggregate", tipi)
            self.assertNotIn("measure", tipi)

    def test_i_join_non_esistono_e_qui_si_dichiara(self):
        """*«I partner di Roma dei commerciali di Milano»* — il reperto R5.

        Fuori dal mandato di questo banco per scelta dell'Architect, ma **dichiarato**:
        un riferimento del catalogo non attraversa mai una relazione, quindi non
        esistono percorsi puntati come `partner_id.city`. La relazione si puo' prendere
        solo come un tutto (`is_set`, `is_not_set`), ed e' provato sopra.
        """
        self.assertFalse([ref for ref in BINDINGS if ref.count(".") > 1],
                         "un percorso a due punti sarebbe un join, e non e' producibile")
