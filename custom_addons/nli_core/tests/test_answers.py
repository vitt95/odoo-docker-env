"""Il banco delle risposte: da uno stato ai **numeri**, su dati noti.

## Perche' questo banco esiste

Il controllo di architettura del 3 agosto 2026 (`ai/17-esito-controllo-architettura.md`)
ha trovato undici pezzi di codice dichiarati, provati e non collegati, e **sette erano
lo stesso tratto di catena**: fra il piano risolto e lo schermo. Tutti provati un passo
a monte del punto in cui servivano.

La causa comune non era la disattenzione. Era che **nessuna prova partiva da uno stato e
arrivava a un numero**. Le prove del contratto guardano la forma della busta, le prove
pure guardano una funzione alla volta, le prove Odoo guardano l'esito — `operations`, e
quanti record. Nessuna guardava *quali* record, in *quale* ordine, con *quale* media.

Quindi:

* le aggregazioni non venivano calcolate da nessuno, e 1 549 prove verdi non se ne
  accorgevano;
* l'ordinamento non arrivava alla tabella, idem;
* il fuso orario mancava su ogni condizione temporale su un `datetime`, idem.

**Questo banco guarda il contenuto.** Ogni caso ha una risposta calcolabile a mente su
un insieme di dati che il caso stesso crea, e la asserisce per intero: i nomi in ordine,
la media col suo valore, il conteggio per gruppo. Se qualcuno scollega di nuovo uno di
quei tratti, qui diventa rosso.

## Perche' i dati se li crea

`ai/restart.md` avverte che `nli_test` contiene 50 004 partner del popolatore, e che
*«un test che passa solo su un database vuoto non e' un test»*. Ogni caso qui dentro
lavora dietro una condizione su una citta' che nessun popolatore produce, quindi il
perimetro e' esattamente quello che il caso ha creato — su un database vuoto e su uno
pieno allo stesso modo.
"""

from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged

from ..execution import executor
from ..presentation import presenter
from ..resolution import calendar as calendar_module
from ..resolution import resolver as resolver_module
from ..resolution.plan import Binding

#: Una citta' che nessun popolatore produce: e' il perimetro di ogni caso.
CITTA = "Bancorisposte"

#: I partner del banco, con il valore su cui si misura. Scelti perche' le risposte si
#: fanno a mente: la media e' 30, il massimo 50, i primi due per valore sono Delta e
#: Gamma, e la citta' spacca il gruppo in tre piu' due.
ANAGRAFICA = [
    ("Alfa banco", 10, CITTA),
    ("Beta banco", 20, CITTA),
    ("Gamma banco", 30, CITTA),
    ("Delta banco", 50, "Altrobanco"),
    ("Epsilon banco", 40, "Altrobanco"),
]

BINDINGS = {
    "partner": Binding(kind="attribute", field="", type="entity"),
    "partner.nome": Binding(kind="attribute", field="name", type="text"),
    "partner.valore": Binding(kind="attribute", field="color", type="number"),
    "partner.citta": Binding(kind="attribute", field="city", type="text"),
    "partner.creato": Binding(kind="attribute", field="create_date", type="datetime"),
}


@tagged("post_install", "-at_install")
class TestAnswers(TransactionCase):
    """Uno stato, la catena vera, e la risposta confrontata con quella giusta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partners = cls.env["res.partner"].create([
            {"name": name, "color": valore, "city": citta}
            for name, valore, citta in ANAGRAFICA
        ])
        # Un istante fisso: il banco non deve dipendere da quando gira. E' la stessa
        # ragione per cui il Risolutore riceve l'istante invece di leggerlo (§13.3).
        cls.instant = calendar_module.Instant(
            now=datetime(2026, 8, 3, 9, 0), timezone="Europe/Rome")

    # -- l'impalcatura -----------------------------------------------------

    def stato(self, **sezioni):
        stato = {
            "dsl_version": "1.0",
            "target": {"ref": "partner", "origin": "user"},
            "limit": {"value": 80, "origin": "default"},
            "presentation": {"view": "list", "origin": "inferred"},
            "filter": {"id": "c0", "ref": "partner.citta", "predicate": "equals",
                       "origin": "user",
                       "value": {"kind": "text", "text": CITTA}},
        }
        stato.update(sezioni)
        return stato

    def rispondi(self, stato):
        """La coda del pipeline: risolvi, esegui, presenta. Restituisce il risultato."""
        risoluzione = resolver_module.resolve(
            stato, bindings=BINDINGS, instant=self.instant, model="res.partner")
        self.assertTrue(risoluzione.resolved,
                        f"il piano non si e' risolto: {risoluzione.failures}")
        risultato = executor.run(self.env, risoluzione.plan)
        mostrato = presenter.present(
            state=stato, plan=risoluzione.plan, result=risultato)
        return risoluzione.plan, risultato, mostrato

    def nomi(self, risultato):
        return list(risultato.records.mapped("name"))

    def misura(self, gruppo, funzione, campo=""):
        return gruppo.measures[(funzione, campo)]

    # -- i casi ------------------------------------------------------------

    def test_i_primi_due_per_valore_sono_quelli_giusti_nell_ordine_giusto(self):
        """*«I 2 partner col valore piu' alto»* — ordinamento e limite insieme.

        Il caso che l'audit chiama R2: qui il server lo fa gia' bene, ed e' la tabella
        a perderlo. Sta qui lo stesso, perche' e' la meta' che deve restare vera mentre
        si sistema l'altra.
        """
        _, risultato, _ = self.rispondi(self.stato(
            filter={"id": "c0", "ref": "partner.citta", "predicate": "is_one_of",
                    "origin": "user",
                    "value": {"kind": "enum", "items": [CITTA, "Altrobanco"]}},
            order_by=[{"ref": "partner.valore", "direction": "desc",
                       "origin": "user"}],
            limit={"value": 2, "origin": "user"}))
        self.assertEqual(self.nomi(risultato), ["Delta banco", "Epsilon banco"])

    def test_il_piano_porta_l_ordinamento_e_le_misure(self):
        """R2 e R1 nella forma in cui viaggiano: il piano deve **contenerli**.

        Se sparissero da qui, nessuna correzione allo schermo potrebbe rimediare. Che
        poi arrivino davvero alla tabella lo prova `nli_web`, sull'altro lato del
        confine.
        """
        piano, _, _ = self.rispondi(self.stato(
            order_by=[{"ref": "partner.valore", "direction": "desc",
                       "origin": "user"}],
            measures=[{"function": "avg", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertEqual(piano.order, "color desc")
        self.assertEqual(piano.measures, (("avg", "color"),))

    def test_la_media_e_un_numero_e_non_un_elenco(self):
        """*«Qual e' il valore medio»* — una misura, nessun raggruppamento.

        **Prima del 3 agosto 2026 questo caso non aveva risposta.**
        `executor.aggregate` non era chiamata da nessuno: lo stato portava la misura,
        il piano la portava, l'interpretazione la elencava, e il numero non lo
        calcolava nessuno. L'utente riceveva l'elenco dei tre partner.

        Media di 10, 20 e 30 = 20. **D89** dice che una misura senza raggruppamento
        resta una lista, quindi le righe ci sono lo stesso: si controllano tutt'e due.
        """
        _, risultato, mostrato = self.rispondi(self.stato(
            measures=[{"function": "avg", "ref": "partner.valore",
                       "origin": "user"}]))
        self.assertEqual(len(risultato.groups), 1,
                         "una misura senza raggruppamento e' una riga sola")
        self.assertAlmostEqual(self.misura(risultato.groups[0], "avg", "color"), 20.0)
        self.assertEqual(self.misura(risultato.groups[0], "count"), 3)
        # E il numero deve **arrivare all'utente**, non restare nel risultato: era
        # esattamente il passo mancante di `in_words` in `00` §33.
        valori = mostrato.interpretation["results"][0]["measures"]
        self.assertIn({"function": "avg", "ref": "color", "value": 20.0}, valori)
        # Le righe restano, perche' D89 dice che questa e' una lista.
        self.assertEqual(len(risultato.records), 3)

    def test_il_conteggio_per_citta_da_i_gruppi_giusti(self):
        """*«Quanti partner per citta'»* — raggruppamento e conteggio.

        Tre in `Bancorisposte`, due in `Altrobanco`. Prima non veniva calcolato niente:
        il raggruppamento arrivava alla vista di Odoo, che lo faceva per conto suo, e
        il server non sapeva dire quanti fossero.
        """
        _, risultato, _ = self.rispondi(self.stato(
            filter={"id": "c0", "ref": "partner.citta", "predicate": "is_one_of",
                    "origin": "user",
                    "value": {"kind": "enum", "items": [CITTA, "Altrobanco"]}},
            group_by=[{"ref": "partner.citta", "origin": "user"}],
            measures=[{"function": "count", "origin": "user"}]))
        conteggi = {gruppo.keys[0]: self.misura(gruppo, "count")
                    for gruppo in risultato.groups}
        self.assertEqual(conteggi, {CITTA: 3, "Altrobanco": 2})

    def test_il_massimo_per_citta_e_il_massimo_di_quella_citta(self):
        """Due misure e un raggruppamento: massimo 30 di qua, 50 di la'."""
        _, risultato, _ = self.rispondi(self.stato(
            filter={"id": "c0", "ref": "partner.citta", "predicate": "is_one_of",
                    "origin": "user",
                    "value": {"kind": "enum", "items": [CITTA, "Altrobanco"]}},
            group_by=[{"ref": "partner.citta", "origin": "user"}],
            measures=[{"function": "max", "ref": "partner.valore",
                       "origin": "user"}]))
        massimi = {gruppo.keys[0]: self.misura(gruppo, "max", "color")
                   for gruppo in risultato.groups}
        self.assertEqual(massimi, {CITTA: 30, "Altrobanco": 50})

    def test_oggi_su_un_datetime_non_perde_le_ore_del_fuso(self):
        """*«Creati oggi»* su una colonna in UTC, con l'utente a Roma.

        **Il difetto che questo caso prende.** Odoo conserva i `datetime` in UTC; il
        calendario ragiona nei giorni dell'utente, perche' *«oggi»* deve voler dire il
        suo oggi. Prima nessuno convertiva: gli estremi uscivano come date nude e
        finivano confrontati con una colonna in un'altra unita' di misura.

        Su un'installazione italiana d'estate lo scarto e' di due ore: *«i lead creati
        oggi»* **escludeva** quelli inseriti fra mezzanotte e le due e **includeva**
        quelli di ieri sera dopo le 22, che e' il caso piu' comune che esista.

        **La prova e' sul dominio, e per una ragione che va scritta.** La prima
        versione di questo caso creava un partner *«dell'una di notte»* passando
        `create_date` alla creazione, e poi verificava di trovarlo. Non funzionava:
        **`create_date` non e' scrivibile in Odoo 18**, ne' in `create` ne' in `write`
        — provato il 3 agosto 2026 scrivendo il banco delle capacita'. Il partner
        prendeva l'ora in cui la prova girava, cioe' *adesso*, e *«creati oggi»* lo
        trovava sempre: **verde qualunque cosa facesse la conversione**. E dal giorno
        dopo sarebbe diventato rosso senza che nulla si rompesse, perche' l'istante del
        banco e' fisso al 3 agosto e *adesso* non lo e'.

        Una riga che non distingue niente e' peggio di una riga che manca: e' `00`
        §39.7 un giro piu' stretto — *un contatore si prova dove conta qualcosa*. Qui
        il posto dove la conversione conta e' **il dominio**, e non serve nessun record
        per guardarlo: se le due ore mancano, la prova cade. Le date su righe vere
        stanno in `test_capabilities.py`, su un'entita' che una data scrivibile ce
        l'ha.
        """
        piano, _, _ = self.rispondi(self.stato(
            filter={"connective": "all", "conditions": [
                {"id": "c0", "ref": "partner.citta", "predicate": "equals",
                 "origin": "user", "value": {"kind": "text", "text": CITTA}},
                {"id": "c1", "ref": "partner.creato", "predicate": "within",
                 "origin": "user",
                 "value": {"kind": "temporal", "expression": "today"}},
            ]}))

        self.assertIn(("create_date", ">=", "2026-08-02 22:00:00"), piano.domain,
                      "la mezzanotte di Roma e' le 22:00 UTC del giorno prima")
        self.assertIn(("create_date", "<", "2026-08-03 22:00:00"), piano.domain,
                      "e la mezzanotte di domani e' le 22:00 UTC di oggi")

    def test_una_data_pura_non_viene_convertita(self):
        """La prova gemella: su un campo `date` un giorno e' un giorno.

        Serve quanto l'altra. Convertire anche le date pure sposterebbe *«scaduto
        oggi»* di due ore su un campo che di ore non ne ha, che e' lo stesso difetto
        con il segno invertito.
        """
        bindings = {**BINDINGS,
                    "partner.scadenza": Binding(kind="attribute", field="date",
                                                type="date")}
        risoluzione = resolver_module.resolve(
            self.stato(filter={"id": "c1", "ref": "partner.scadenza",
                               "predicate": "within", "origin": "user",
                               "value": {"kind": "temporal",
                                         "expression": "today"}}),
            bindings=bindings, instant=self.instant, model="res.partner")
        self.assertTrue(risoluzione.resolved)
        self.assertIn(("date", ">=", "2026-08-03"), risoluzione.plan.domain)
