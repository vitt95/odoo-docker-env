#!/usr/bin/env python3
"""
Generatore del corpus fondativo sintetico.

Principio: si genera prima lo **Stato di Interrogazione atteso**, poi lo si
verbalizza in italiano. L'interpretazione attesa e' quindi corretta per
costruzione e non richiede annotazione umana — che e' l'unico modo di produrre
un corpus senza clienti pilota (cfr. 11-corpus-fondativo.md §4.1).

Cio' che questo corpus NON e': linguaggio osservato. Non sostituisce il corpus
sigillato di D42 e non chiude il cancello di D49.

Uso:
    python3 genera_corpus.py --n 1200 --seme 42 --out corpus_fondativo.jsonl

## Revisione del 28/07/2026 — allineamento al contratto (D92)

Il generatore precedente emetteva un **dialetto proprio**, divergente dalla forma
normativa di `03-specifica-dsl.md`. Le quattro correzioni, con la ragione di
ciascuna:

1. **Forma normativa dello stato.** `target` come oggetto con `origin`, filtro ad
   albero con connettivo, `order_by`/`direction`, `limit.value`, `presentation`
   come oggetto, `origin` su ogni elemento, identificativo su ogni condizione.
   Prima serviva un adattatore per leggere il corpus, e un adattatore e' un
   secondo contratto da mantenere per dieci anni;
2. **Espressioni temporali simboliche.** Lo stato porta `current_month`, non
   *"questo mese"*: §9.2 lo impone, ed e' la condizione perche' un'interrogazione
   salvata a luglio mostri agosto in agosto. La frase italiana resta dove
   serve — nella verbalizzazione. Le espressioni che DSL 1.0 non sa esprimere non
   entrano piu' negli stati: quelle **ambigue** (*"a gennaio"* senza anno)
   diventano casi di chiarimento, che e' l'esito corretto (§11.4);
3. **Riferimenti semantici** al posto dei nomi tecnici Odoo (C2, §5.10), con il
   `binding_tecnico` conservato a parte perche' la parte 3 possa verificare la
   risoluzione. Tabella in `riferimenti.py`;
4. **Raffinamenti che raffinano.** Prima l'11,3% dei casi chiedeva
   *"raggruppa per venditore"* su uno stato gia' raggruppato per venditore: il
   contratto si comporta correttamente ma il caso non misura nulla, perche' un
   modello che emettesse qualunque operazione idempotente lo supererebbe.

## Perche' i raffinamenti portano anche lo stato atteso

Prima portavano solo stato di partenza e operazioni, e il criterio *"i casi
producono lo stato atteso"* non era verificabile su di essi. Ora l'atteso c'e', ed
e' calcolato **trasformando l'intento** — non applicando l'Applicatore del
prodotto. La distinzione e' l'intero valore del caso: due implementazioni
indipendenti della stessa semantica devono concordare. Usare l'Applicatore per
costruire la chiave renderebbe il confronto una tautologia.
"""

import argparse
import json
import random
import sys
import unicodedata
from pathlib import Path

from riferimenti import (
    binding,
    riferimento_attributo,
    riferimento_categoria,
    riferimento_entita,
)

# I campi che una categoria tocca non sono piu' dichiarati nel lessico: si
# derivano dalla condizione tipizzata (V-D87-1). Il generatore usa la stessa
# funzione del prodotto, cosi' non esistono due nozioni di "campi implicati".
_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from pure.bootstrap import install  # noqa: E402

install("nli_semantics")
from nli_semantics.dictionary import conditions as _condizioni  # noqa: E402


def campi_implicati(voce_categoria: dict) -> set[str]:
    condizione = voce_categoria.get("condizione_tipizzata")
    if not condizione:
        return set()
    return set(_condizioni.implied_fields(condizione))

QUI = Path(__file__).parent


# --- Espressioni temporali (§9.2) --------------------------------------------

#: Simbolo del contratto -> frasi italiane che lo esprimono. Il generatore
#: sceglie il **simbolo** e poi una frase: e' la direzione di D82 applicata anche
#: al tempo, e rende impossibile per costruzione uno stato con una frase dentro.
TEMPORALI: list[tuple[dict, list[str]]] = [
    ({"kind": "temporal", "expression": "today"}, ["oggi"]),
    ({"kind": "temporal", "expression": "yesterday"}, ["ieri"]),
    ({"kind": "temporal", "expression": "current_week"},
     ["questa settimana", "sta settimana"]),
    ({"kind": "temporal", "expression": "current_month"},
     ["questo mese", "sto mese"]),
    ({"kind": "temporal", "expression": "current_quarter"}, ["questo trimestre"]),
    ({"kind": "temporal", "expression": "current_year"}, ["quest'anno"]),
    ({"kind": "temporal", "expression": "previous_week"}, ["la settimana scorsa"]),
    ({"kind": "temporal", "expression": "previous_month"},
     ["il mese scorso", "lo scorso mese"]),
    ({"kind": "temporal", "expression": "previous_quarter"}, ["il trimestre scorso"]),
    ({"kind": "temporal", "expression": "previous_year"}, ["l'anno scorso"]),
    ({"kind": "temporal", "expression": "last_n_days", "n": 30},
     ["negli ultimi 30 giorni"]),
    ({"kind": "temporal", "expression": "last_n_months", "n": 3},
     ["negli ultimi tre mesi"]),
    ({"kind": "temporal", "expression": "last_n_months", "n": 12},
     ["nell'ultimo anno"]),
    ({"kind": "temporal", "expression": "absolute_range",
      "from": "2025-01-01", "to": "2025-12-31"}, ["nel 2025"]),
    ({"kind": "temporal", "expression": "absolute_range",
      "from": "2026-03-01", "to": "2026-03-31"}, ["a marzo 2026"]),
    # D91: l'anno parziale. Risolto contro l'inizio dell'esercizio fiscale, come
    # `current_year` (§9.2).
    ({"kind": "temporal", "expression": "year_to_date"}, ["da inizio anno"]),
]

#: Espressioni assolute **senza anno**: risolverle richiede l'istante di
#: riferimento, che §5.10 esclude dallo stato, e ammettono piu' letture (l'anno in
#: corso o il precedente). L'esito corretto e' un chiarimento, non un'estensione
#: della grammatica — vedi D91.
TEMPORALI_AMBIGUE = ["a gennaio", "nel primo trimestre", "a settembre", "a giugno"]

#: Espressioni comprensibili e non esprimibili in DSL 1.0. *"Da inizio anno"* ne
#: e' uscita con **D91**, che ha aggiunto `year_to_date`. Resta *"l'altro ieri"*:
#: non e' `yesterday` e non e' un periodo, e nessun caso del lessico la usa — §3.9
#: dice di estendere quando i dati lo chiedono, e un solo termine non lo chiede.
TEMPORALI_NON_ESPRIMIBILI = ["l'altro ieri"]

VERSO_PREDICATO = {"sopra": "greater_than", "sotto": "less_than"}


# --- Verbalizzazione ---------------------------------------------------------

def _senza_accenti(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _elidi_di(sintagma: str) -> str:
    """'fammi un elenco' + 'ordini' -> 'degli ordini'. Articolo determinativo
    contratto con 'di', secondo la fonologia iniziale del sostantivo."""
    p = sintagma.split()[0].lower()
    if p[:1] in "aeiou":
        return f"degli {sintagma}" if p.endswith(("i", "e")) else f"dell'{sintagma}"
    if p.startswith(("gn", "ps", "x", "z")) or (p.startswith("s") and p[1:2] not in "aeiou"):
        return f"degli {sintagma}"
    if p.endswith("e") and not p.endswith("le"):
        return f"delle {sintagma}"
    if p.endswith("i"):
        return f"dei {sintagma}"
    return f"delle {sintagma}" if p.endswith("a") else f"dei {sintagma}"


class Verbalizzatore:
    """Trasforma un intento in una frase italiana plausibile."""

    def __init__(self, l1: dict, rng: random.Random):
        self.l1 = l1
        self.rng = rng

    def _termine_entita(self, chiave: str, ambiguo: bool = False) -> str:
        e = self.l1["entita"][chiave]
        if ambiguo and e.get("gergo_ambiguo"):
            return self.rng.choice(e["gergo_ambiguo"])
        return self.rng.choice(e["termini"])

    def _termine_attributo(self, campo: str) -> str:
        """Solo forme nominali: usabili dopo 'per' e 'con'."""
        voce = self.l1["attributi"].get(campo)
        if not voce:
            return campo
        return self.rng.choice(voce["nominali"] or [campo])

    def _termine_categoria(self, categoria: str, genere: str) -> str:
        """Accorda l'aggettivo al genere dell'entita; le locuzioni sono invarianti."""
        c = self.l1["categorie"][categoria]
        candidati = list(c["termini_inv"]) + list(c[f"termini_{genere}"])
        return self.rng.choice(candidati) if candidati else categoria

    def frase(self, intento: dict, ambiguo: bool = False) -> str:
        target = intento["target"]
        genere = self.l1["entita"][target]["genere"]
        usa_di = self.rng.random() < 0.15
        if usa_di:
            v = self.rng.choice(self.l1["verbi_richiesta"]["con_di"])
            entita = self._termine_entita(target, ambiguo)
            testa = f"{v} {_elidi_di(entita)}"
        else:
            v = self.rng.choice(
                self.l1["verbi_richiesta"]["colloquiale"]
                + self.l1["verbi_richiesta"]["neutro"]
            )
            testa = f"{v} {self._termine_entita(target, ambiguo)}"
        pezzi = [testa]

        for c in intento["condizioni"]:
            pezzi.append(self.frammento_condizione(c, genere))

        if intento["gruppi"]:
            pezzi.append(f"raggruppati per {self._termine_attributo(intento['gruppi'][0])}")
        if intento["ordine"]:
            pezzi.append(f"ordinati per {self._termine_attributo(intento['ordine'][0])}")
        if intento["campi"]:
            nomi = [self._termine_attributo(f) for f in intento["campi"]]
            pezzi.append("con " + ", ".join(nomi))
        if intento["limite"]["origin"] == "user":
            pezzi.insert(2, f"i primi {intento['limite']['valore']}")

        return " ".join(p for p in pezzi if p).strip()

    def frammento_condizione(self, c: dict, genere: str) -> str:
        """Il frammento di frase che produce una condizione.

        E' anche la provenienza (§10.3): il generatore la conosce perche' e' lui
        a costruire la frase, ed e' l'unico momento in cui la si puo' sapere con
        certezza anziche' stimarla.
        """
        if c["tipo"] == "categoria":
            return self._termine_categoria(c["categoria"], genere)
        if c["tipo"] == "temporale":
            return c["frase"]
        if c["tipo"] == "confronto":
            gruppo = ("confronto_sopra" if c["verso"] == "sopra"
                      else "confronto_sotto")
            op = self.rng.choice(self.l1["vaghezza"][gruppo])
            attr = self._termine_attributo(c["campo"])
            if "..." in op:                       # circonfisso: "da ... in su"
                prima, dopo = (p.strip() for p in op.split("..."))
                return f"con {attr} {prima} {c['valore']} {dopo}"
            return f"con {attr} {op} {c['valore']}"
        return ""

    def delta(self, scelta: dict, genere: str) -> str:
        """Verbalizza un solo turno di raffinamento."""
        op = scelta["op"]
        if op == "add_condition":
            t = self._termine_categoria(scelta["categoria"], genere)
            pron = "quelli" if genere == "m" else "quelle"
            return self.rng.choice(
                [f"solo {t}", f"solo {pron} {t}", f"e {t}", f"filtra {t}", t])
        if op == "add_order":
            a = self._termine_attributo(scelta["campo"])
            return self.rng.choice([f"ordina per {a}", f"per {a}", f"mettili in ordine di {a}"])
        if op == "add_field":
            a = self._termine_attributo(scelta["campo"])
            return self.rng.choice([f"mostrami anche {a}", f"aggiungi {a}", f"e anche {a}"])
        if op == "add_group":
            a = self._termine_attributo(scelta["campo"])
            return self.rng.choice([f"raggruppa per {a}", f"dividili per {a}"])
        if op == "set_limit":
            return f"solo i primi {scelta['valore']}"
        return "?"


# --- Perturbazione (metodo Spider-Syn / Spider-Realistic) --------------------

class Perturbatore:
    def __init__(self, l1: dict, rng: random.Random):
        self.f = l1["fenomeni_linguistici"]
        self.rng = rng

    def applica(self, testo: str) -> tuple[str, list[str]]:
        applicate = []
        if self.rng.random() < 0.18:
            for pieno, breve in self.f["abbreviazioni"].items():
                if pieno in testo:
                    testo = testo.replace(pieno, breve, 1)
                    applicate.append("abbreviazione")
                    break
        if self.rng.random() < 0.12:
            for giusto, sbagliato in self.f["refusi_frequenti"].items():
                if giusto in testo:
                    testo = testo.replace(giusto, sbagliato, 1)
                    applicate.append("refuso")
                    break
        if self.rng.random() < 0.10:
            for it, en in self.f["code_switching"].items():
                if it in testo:
                    testo = testo.replace(it, en, 1)
                    applicate.append("code_switching")
                    break
        if self.rng.random() < 0.15:
            testo = testo.lower()
            applicate.append("minuscole")
        if self.rng.random() < 0.08:
            testo = _senza_accenti(testo)
            applicate.append("senza_accenti")
        return testo, applicate


# --- Catalogo di generazione -------------------------------------------------

CATALOGO = {
    "sale.order": {
        "categorie": ["da_fatturare", "da_consegnare", "confermati", "in_bozza"],
        "campi": ["partner_id", "user_id", "amount_total", "date_order", "state"],
        "temporali": ["date_order"],
        "raggruppabili": ["user_id", "partner_id", "state"],
    },
    "account.move.out_invoice": {
        "categorie": ["fatture_scadute", "partite_aperte", "in_bozza"],
        "campi": ["partner_id", "amount_total", "invoice_date", "invoice_date_due", "payment_state"],
        "temporali": ["invoice_date", "invoice_date_due"],
        "raggruppabili": ["partner_id", "payment_state"],
    },
    "res.partner.customer": {
        "categorie": ["attivi"],
        "campi": ["city", "country_id", "phone", "email", "vat"],
        "temporali": [],
        "raggruppabili": ["city", "country_id"],
    },
    "product.template": {
        "categorie": ["sottoscorta", "attivi"],
        "campi": ["categ_id", "qty_available"],
        "temporali": [],
        "raggruppabili": ["categ_id"],
    },
    "crm.lead": {
        "categorie": ["confermati", "attivi"],
        "campi": ["partner_id", "user_id", "expected_revenue", "stage_id", "team_id"],
        "temporali": [],
        "raggruppabili": ["user_id", "stage_id", "team_id"],
    },
    "stock.picking": {
        "categorie": ["da_consegnare", "in_bozza"],
        "campi": ["partner_id", "state"],
        "temporali": [],
        "raggruppabili": ["state"],
    },
}


# --- Testi dei casi non interpretabili --------------------------------------

#: Categoria di `scope_note` -> modelli di frase. `{x}` e' l'oggetto.
#: Il vocabolario delle categorie e' chiuso (§11.4) e la loro distribuzione e'
#: l'evidenza quantitativa su cui si decide che cosa estendere: per questo ogni
#: modello dichiara la propria categoria anziche' lasciarla dedurre.
FUORI_AMBITO: dict[str, list[str]] = {
    "modifica_dati": [
        "cambia lo stato di {x} a confermato",
        "conferma {x}",
        "aggiorna il totale di {x}",
        "metti {x} in bozza",
        "modifica la data di {x}",
        "annulla {x}",
    ],
    "invio_esterno": [
        "mandami {x} per email",
        "invia {x} al cliente",
        "esporta {x} in excel",
        "stampa {x} in pdf",
        "condividi {x} con il team",
    ],
    "creazione_record": [
        "crea un nuovo cliente Mario Bianchi",
        "aggiungi un articolo nuovo al catalogo",
        "registra {x} per il cliente Rossi",
        "inserisci una riga in {x}",
        "duplica {x}",
    ],
    "cancellazione_record": [
        "elimina {x}",
        "cancella {x} dal sistema",
        "rimuovi {x}",
        "svuota {x}",
    ],
    "previsione": [
        "fammi una previsione di {x} del prossimo trimestre",
        "quanto venderemo il mese prossimo",
        "stima {x} per il prossimo anno",
        "prevedi l'andamento di {x}",
    ],
}

OGGETTI_FUORI_AMBITO = [
    "questo ordine", "questa fattura", "gli ordini in bozza",
    "le fatture scadute", "questo cliente", "questo articolo",
    "il documento di trasporto", "questa opportunita",
]

INCOMPRESO_SOCIALE = [
    "ciao", "ciao come stai", "buongiorno", "buonasera", "grazie mille",
    "grazie", "ok perfetto", "va bene grazie", "ci sei?", "sei un umano?",
    "come funzioni", "aiuto",
]

INCOMPRESO_MONOSILLABO = [
    "boh", "mah", "eh", "non lo so", "niente", "?", "asdf", "prova",
    "test", "ok",
]

INCOMPRESO_DEITTICO = [
    "quella cosa {x}",
    "fammi vedere quella roba {x}",
    "il coso {x}",
    "dov'e' finito quello {x}",
    "riprendi quello {x}",
]

DEITTICI = ["di ieri", "del tizio", "di prima", "dell'altra volta",
            "che ti ho detto", "di stamattina"]


# --- Dall'intento allo stato normativo ---------------------------------------

def condizione_normativa(intento_condizione: dict, target: str) -> dict:
    """Una condizione del contratto, senza identificativo ne' metadati."""
    c = intento_condizione
    if c["tipo"] == "categoria":
        # T5, condizione nominata (`06` §3.6). Predicato `is_category`: D87.
        return {"ref": riferimento_categoria(target, c["categoria"]),
                "predicate": "is_category"}
    if c["tipo"] == "temporale":
        return {"ref": riferimento_attributo(target, c["campo"]),
                "predicate": "within", "value": dict(c["simbolo"])}
    if c["tipo"] == "confronto":
        return {"ref": riferimento_attributo(target, c["campo"]),
                "predicate": VERSO_PREDICATO[c["verso"]],
                "value": {"kind": "number", "value": c["valore"]}}
    raise AssertionError(f"tipo di condizione non gestito: {c['tipo']!r}")


def stato_normativo(intento: dict) -> dict:
    """Rende un intento nella forma di `03` §5.

    Implementazione **indipendente** dall'Applicatore del prodotto: e' cio' che
    rende il confronto fra i due un test e non una tautologia.
    """
    target = intento["target"]
    stato: dict = {
        "dsl_version": "1.0",
        "target": {"ref": riferimento_entita(target), "origin": "user"},
        "limit": {"value": intento["limite"]["valore"],
                  "origin": intento["limite"]["origin"]},
    }

    condizioni = []
    for indice, c in enumerate(intento["condizioni"], start=1):
        voce = condizione_normativa(c, target)
        voce["id"] = f"c{indice}"
        voce["origin"] = "user"
        if c.get("frammento"):
            voce["provenance"] = {"text": c["frammento"]}
        condizioni.append(voce)
    if len(condizioni) == 1:
        stato["filter"] = condizioni[0]
    elif condizioni:
        stato["filter"] = {"connective": "all", "conditions": condizioni}

    if intento["campi"]:
        stato["fields"] = [
            {"ref": riferimento_attributo(target, campo), "origin": "user"}
            for campo in intento["campi"]
        ]
    if intento["gruppi"]:
        stato["group_by"] = [
            {"ref": riferimento_attributo(target, campo), "origin": "user"}
            for campo in intento["gruppi"]
        ]
    if intento["ordine"]:
        stato["order_by"] = [
            # La verbalizzazione non nomina la direzione ("ordinati per data"):
            # `desc` e' un'inferenza del sistema, e §10.2 impone di dichiararlo.
            {"ref": riferimento_attributo(target, campo), "direction": "desc",
             "origin": "inferred", "rule": "latest_implies_desc_by_date"}
            for campo in intento["ordine"]
        ]

    # §6.7: nessuna misura, quindi la vista e' `list`; la regola dipende dalla
    # presenza dei raggruppamenti. §14.3 regola 5: sempre presente col valore
    # effettivo, anche quando derivato.
    stato["presentation"] = {
        "view": "list", "origin": "inferred",
        "rule": ("grouping_without_measure_implies_list" if intento["gruppi"]
                 else "default_list"),
    }
    return stato


def riferimenti_di(intento: dict) -> list[str]:
    target = intento["target"]
    trovati = [riferimento_entita(target)]
    for c in intento["condizioni"]:
        if c["tipo"] == "categoria":
            trovati.append(riferimento_categoria(target, c["categoria"]))
        else:
            trovati.append(riferimento_attributo(target, c["campo"]))
    for campo in intento["campi"] + intento["gruppi"] + intento["ordine"]:
        trovati.append(riferimento_attributo(target, campo))
    return sorted(set(trovati))


# --- Generazione -------------------------------------------------------------

class Generatore:
    def __init__(self, l1: dict, rng: random.Random):
        self.l1, self.rng = l1, rng
        self.verb = Verbalizzatore(l1, rng)
        self.pert = Perturbatore(l1, rng)

    def _intento(self, target: str, n_cond: int) -> dict:
        spec = CATALOGO[target]
        intento = {"target": target, "condizioni": [], "campi": [], "gruppi": [],
                   "ordine": [], "limite": {"valore": 80, "origin": "default"}}
        # Una condizione per campo e una sola temporale: due vincoli sullo stesso
        # campo produrrebbero uno stato incoerente, respinto dalla validazione di
        # livello 4 — quindi un caso il cui atteso e' sbagliato.
        campi_usati: set[str] = set()
        numerici = [c for c in spec["campi"] if "amount" in c or "qty" in c
                    or "revenue" in c]
        scelte = []
        if spec["categorie"]:
            scelte.append("categoria")
        if spec["temporali"]:
            scelte.append("temporale")
        if numerici:
            scelte.append("confronto")

        for _ in range(n_cond):
            tipo = self.rng.choice(scelte)
            if tipo == "categoria":
                disponibili = [c for c in spec["categorie"]
                               if not (campi_implicati(self.l1["categorie"][c])
                                       & campi_usati)
                               and all(f.get("categoria") != c
                                       for f in intento["condizioni"])]
                if not disponibili:
                    continue
                c = self.rng.choice(disponibili)
                intento["condizioni"].append({"tipo": "categoria", "categoria": c})
                campi_usati |= campi_implicati(self.l1["categorie"][c])
            elif tipo == "temporale":
                if any(f["tipo"] == "temporale" for f in intento["condizioni"]):
                    continue
                campo = self.rng.choice(spec["temporali"])
                if campo in campi_usati:
                    continue
                simbolo, frasi = self.rng.choice(TEMPORALI)
                intento["condizioni"].append({
                    "tipo": "temporale", "campo": campo,
                    "simbolo": simbolo, "frase": self.rng.choice(frasi),
                })
                campi_usati.add(campo)
            else:
                liberi = [c for c in numerici if c not in campi_usati]
                if not liberi:
                    continue
                campo = self.rng.choice(liberi)
                intento["condizioni"].append({
                    "tipo": "confronto", "campo": campo,
                    "verso": self.rng.choice(["sopra", "sotto"]),
                    "valore": self.rng.choice([100, 500, 1000, 5000, 10000]),
                })
                campi_usati.add(campo)
        if self.rng.random() < 0.30 and spec["raggruppabili"]:
            intento["gruppi"] = [self.rng.choice(spec["raggruppabili"])]
        if self.rng.random() < 0.35:
            intento["ordine"] = [self.rng.choice(spec["campi"])]
        if self.rng.random() < 0.30:
            intento["campi"] = self.rng.sample(spec["campi"], min(3, len(spec["campi"])))
        if self.rng.random() < 0.18:
            intento["limite"] = {"valore": self.rng.choice([5, 10, 20]), "origin": "user"}
        return intento

    def _con_provenienza(self, intento: dict) -> None:
        """Registra su ogni condizione il frammento che la verbalizza (§10.3)."""
        genere = self.l1["entita"][intento["target"]]["genere"]
        for c in intento["condizioni"]:
            c["frammento"] = self.verb.frammento_condizione(c, genere)

    def caso_apertura(self, idx: int) -> dict:
        target = self.rng.choice(list(CATALOGO))
        intento = self._intento(target, self.rng.choice([0, 1, 1, 2, 2, 3]))
        testo = self.verb.frase(intento)
        testo, fen = self.pert.applica(testo)
        riferimenti = riferimenti_di(intento)
        return {
            "id": f"F{idx:05d}", "tipo": "apertura", "esito_atteso": "operations",
            "testo": testo, "stato_partenza": None,
            "stato_atteso": stato_normativo(intento),
            "riferimenti_necessari": riferimenti,
            "binding_tecnico": binding(target, riferimenti),
            "etichette": {"entita": target, "fenomeni": fen,
                          "difficolta": ["facile", "media", "difficile"][
                              min(2, len(intento["condizioni"]))]},
        }

    def _scelta_raffinamento(self, intento: dict) -> dict | None:
        """Un'operazione che **cambia** lo stato di partenza.

        Il controllo non e' pignoleria: un raffinamento idempotente produce un
        caso che qualunque modello supera emettendo qualunque cosa di idempotente,
        e un caso che non discrimina abbassa la misura senza dirlo.
        """
        spec = CATALOGO[intento["target"]]
        possibili = ["add_order", "add_group", "set_limit"]
        if spec["categorie"]:
            possibili.append("add_condition")
        if intento["campi"]:
            # `add_field` su uno stato senza `fields` significa "predefiniti piu'
            # questo" (§5.5), e i predefiniti sono voce del dizionario: un caso
            # cosi' non e' verificabile senza la parte 3.
            possibili.append("add_field")
        self.rng.shuffle(possibili)

        categorie_usate = {c.get("categoria") for c in intento["condizioni"]}
        for op in possibili:
            if op == "add_condition":
                libere = [c for c in spec["categorie"]
                          if c not in categorie_usate
                          and not (campi_implicati(self.l1["categorie"][c])
                                   & self._campi_vincolati(intento))]
                if libere:
                    return {"op": op, "categoria": self.rng.choice(libere)}
            elif op == "add_group":
                libere = [c for c in spec["raggruppabili"] if c not in intento["gruppi"]]
                if libere and len(intento["gruppi"]) < 3:
                    return {"op": op, "campo": self.rng.choice(libere)}
            elif op == "add_field":
                libere = [c for c in spec["campi"] if c not in intento["campi"]]
                if libere:
                    return {"op": op, "campo": self.rng.choice(libere)}
            elif op == "add_order":
                libere = [c for c in spec["campi"] if c not in intento["ordine"]]
                if libere:
                    return {"op": op, "campo": self.rng.choice(libere)}
            elif op == "set_limit":
                libere = [v for v in (5, 10, 20, 50) if v != intento["limite"]["valore"]]
                if libere:
                    return {"op": op, "valore": self.rng.choice(libere)}
        return None

    def _campi_vincolati(self, intento: dict) -> set[str]:
        vincolati: set[str] = set()
        for c in intento["condizioni"]:
            if c["tipo"] == "categoria":
                vincolati |= campi_implicati(
                    self.l1["categorie"][c["categoria"]])
            else:
                vincolati.add(c["campo"])
        return vincolati

    def _applica_scelta(self, intento: dict, scelta: dict, frammento: str) -> dict:
        """Trasforma l'intento secondo la scelta. Seconda implementazione della
        semantica di applicazione, indipendente da `application/applicator.py`."""
        dopo = {
            "target": intento["target"],
            "condizioni": [dict(c) for c in intento["condizioni"]],
            "campi": list(intento["campi"]),
            "gruppi": list(intento["gruppi"]),
            "ordine": list(intento["ordine"]),
            "limite": dict(intento["limite"]),
        }
        op = scelta["op"]
        if op == "add_condition":
            dopo["condizioni"].append({
                "tipo": "categoria", "categoria": scelta["categoria"],
                "frammento": frammento,
            })
        elif op == "add_group":
            dopo["gruppi"].append(scelta["campo"])
        elif op == "add_field":
            dopo["campi"].append(scelta["campo"])
        elif op == "add_order":
            dopo["ordine"] = [c for c in dopo["ordine"] if c != scelta["campo"]]
            dopo["ordine"].append(scelta["campo"])
        elif op == "set_limit":
            dopo["limite"] = {"valore": scelta["valore"], "origin": "user"}
        return dopo

    def _operazione_normativa(self, scelta: dict, target: str, frammento: str) -> dict:
        provenienza = {"text": frammento}
        op = scelta["op"]
        if op == "add_condition":
            return {"op": "add_condition", "combine": "all",
                    "condition": {"ref": riferimento_categoria(target, scelta["categoria"]),
                                  "predicate": "is_category"},
                    "provenance": provenienza}
        if op == "set_limit":
            return {"op": "set_limit", "value": scelta["valore"],
                    "provenance": provenienza}
        if op == "add_order":
            return {"op": "add_order",
                    "ref": riferimento_attributo(target, scelta["campo"]),
                    "direction": "desc", "origin": "inferred",
                    "provenance": provenienza}
        return {"op": op, "ref": riferimento_attributo(target, scelta["campo"]),
                "provenance": provenienza}

    def caso_raffinamento(self, idx: int) -> dict | None:
        target = self.rng.choice(list(CATALOGO))
        base = self._intento(target, self.rng.choice([1, 2]))
        self._con_provenienza(base)
        scelta = self._scelta_raffinamento(base)
        if scelta is None:
            return None

        genere = self.l1["entita"][target]["genere"]
        frammento = self.verb.delta(scelta, genere)
        testo, fen = self.pert.applica(frammento)
        dopo = self._applica_scelta(base, scelta, frammento)

        riferimenti = sorted(set(riferimenti_di(base)) | set(riferimenti_di(dopo)))
        return {
            "id": f"F{idx:05d}", "tipo": "raffinamento", "esito_atteso": "operations",
            "testo": testo,
            "stato_partenza": stato_normativo(base),
            "operazioni_attese": [
                self._operazione_normativa(scelta, target, frammento)
            ],
            "stato_atteso": stato_normativo(dopo),
            "riferimenti_necessari": riferimenti,
            "binding_tecnico": binding(target, riferimenti),
            "etichette": {"entita": target, "fenomeni": fen, "difficolta": "media"},
        }

    def caso_chiarimento(self, idx: int) -> dict:
        """Termini deliberatamente ambigui: l'esito corretto e' una domanda."""
        modo = self.rng.choice([
            "entita_ambigua", "definizione_mancante", "ruolo_ambiguo",
            "temporale_ambiguo",
        ])
        verbo = self.rng.choice(self.l1["verbi_richiesta"]["colloquiale"]
                                + self.l1["verbi_richiesta"]["neutro"])
        if modo == "entita_ambigua":
            gergo = self.rng.choice(["le pratiche aperte", "i lavori in corso",
                                     "le commesse aperte", "i documenti di ieri"])
            testo = f"{verbo} {gergo}"
            motivo = "termine di gergo non mappato: puo' indicare piu' entita"
        elif modo == "definizione_mancante":
            c = self.l1["categorie"]["clienti_importanti"]
            t = self.rng.choice(c["termini_m"] + c["termini_inv"])
            soggetto = self.rng.choice(["i clienti", "gli ordini", "gli articoli"])
            testo = f"{verbo} {soggetto} {t}"
            motivo = "vaghezza qualitativa priva di definizione L2"
        elif modo == "ruolo_ambiguo":
            cognome = self.rng.choice(["Rossi", "Bianchi", "Ferrari", "Conti"])
            testo = self.rng.choice([
                f"{verbo} gli ordini di {cognome}",
                f"{verbo} le fatture di {cognome}",
            ])
            motivo = f"'di {cognome}' ammette lettura come cliente o come venditore"
        else:
            espressione = self.rng.choice(TEMPORALI_AMBIGUE)
            soggetto = self.rng.choice(["gli ordini", "le fatture"])
            testo = f"{verbo} {soggetto} {espressione}"
            motivo = (f"'{espressione}' e' assoluta senza anno: ammette l'anno in "
                      "corso o il precedente, e §5.10 esclude dallo stato "
                      "l'istante di riferimento che la risolverebbe")
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "chiarimento", "esito_atteso": "clarification",
            "testo": testo, "stato_partenza": None, "motivo_atteso": motivo,
            "riferimenti_necessari": [], "binding_tecnico": {},
            "etichette": {"entita": None, "fenomeni": fen, "difficolta": "difficile"},
        }

    def caso_fuori_ambito(self, idx: int) -> dict:
        """Richiesta compresa e non esprimibile (§11.4).

        I testi si compongono da modello piu' oggetto anziche' essere una lista
        fissa. Una lista fissa di sei frasi per settantadue casi produce l'85% di
        duplicati, e la dimensione del corpus e' cio' su cui poggia la soglia di
        rumore di **D48**: settantadue casi che sono undici frasi non sono
        settantadue casi.
        """
        nota = self.rng.choice(list(FUORI_AMBITO))
        modello = self.rng.choice(FUORI_AMBITO[nota])
        oggetto = self.rng.choice(OGGETTI_FUORI_AMBITO)
        testo = modello.format(x=oggetto)
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "fuori_ambito", "esito_atteso": "out_of_scope",
            "testo": testo, "stato_partenza": None, "scope_note_atteso": nota,
            "riferimenti_necessari": [], "binding_tecnico": {},
            "etichette": {"entita": None, "fenomeni": fen, "difficolta": "facile"},
        }

    def caso_incompreso(self, idx: int) -> dict:
        forma = self.rng.choice(["sociale", "monosillabo", "deittico"])
        if forma == "sociale":
            testo = self.rng.choice(INCOMPRESO_SOCIALE)
        elif forma == "monosillabo":
            testo = self.rng.choice(INCOMPRESO_MONOSILLABO)
        else:
            testo = self.rng.choice(INCOMPRESO_DEITTICO).format(
                x=self.rng.choice(DEITTICI))
        return {
            "id": f"F{idx:05d}", "tipo": "incompreso", "esito_atteso": "not_understood",
            "testo": testo, "stato_partenza": None, "riferimenti_necessari": [],
            "binding_tecnico": {},
            "etichette": {"entita": None, "fenomeni": [], "difficolta": "facile"},
        }


# --- Composizione secondo il bilanciamento di D46 ---------------------------

QUOTE = [
    ("raffinamento", 0.42),   # D46: >= 40%
    ("chiarimento", 0.11),    # D46: >= 10%
    ("fuori_ambito", 0.06),   # D46: >= 5%
    ("incompreso", 0.04),     # D46: >= 3%
    ("apertura", 0.37),
]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=1200)
    p.add_argument("--seme", type=int, default=42)
    p.add_argument("--l1", default=str(QUI / "lessico_l1.json"))
    p.add_argument("--out", default=str(QUI / "corpus_fondativo.jsonl"))
    args = p.parse_args()

    rng = random.Random(args.seme)
    l1 = json.loads(Path(args.l1).read_text(encoding="utf-8"))
    g = Generatore(l1, rng)

    piano = []
    for tipo, quota in QUOTE:
        piano += [tipo] * round(args.n * quota)
    rng.shuffle(piano)

    metodo = {
        "apertura": g.caso_apertura, "raffinamento": g.caso_raffinamento,
        "chiarimento": g.caso_chiarimento, "fuori_ambito": g.caso_fuori_ambito,
        "incompreso": g.caso_incompreso,
    }
    casi = []
    scartati = 0
    duplicati_accettati = 0
    visti: set[str] = set()
    #: Quanti tentativi prima di accettare una frase gia' vista. Il tetto esiste
    #: perche' lo spazio delle frasi di un tipo e' finito: senza, un tipo saturo
    #: farebbe girare a vuoto il generatore anziche' dichiarare la saturazione.
    TENTATIVI = 25
    for tipo in piano:
        caso = None
        for tentativo in range(TENTATIVI):
            candidato = metodo[tipo](len(casi) + 1)
            if candidato is None:
                continue
            caso = candidato
            if candidato["testo"] not in visti:
                break
        if caso is None:
            # Nessun raffinamento non degenere disponibile per quell'entita': si
            # scarta il caso anziche' emetterne uno che non misura nulla.
            scartati += 1
            continue
        if caso["testo"] in visti:
            # Spazio delle frasi saturo per quel tipo. Si accetta e si conta: la
            # quota di duplicati e' un indicatore della dimensione **effettiva**
            # del corpus, e la soglia di rumore di D48 poggia su quella, non sul
            # numero di righe del file.
            duplicati_accettati += 1
        visti.add(caso["testo"])
        casi.append(caso)

    with Path(args.out).open("w", encoding="utf-8") as f:
        for c in casi:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    conteggi: dict = {}
    entita: dict = {}
    fenomeni: dict = {}
    temporali: dict = {}
    for c in casi:
        conteggi[c["tipo"]] = conteggi.get(c["tipo"], 0) + 1
        e = c["etichette"]["entita"]
        if e:
            entita[e] = entita.get(e, 0) + 1
        for ph in c["etichette"]["fenomeni"]:
            fenomeni[ph] = fenomeni.get(ph, 0) + 1
        for stato in (c.get("stato_atteso"), c.get("stato_partenza")):
            if not stato:
                continue
            nodo = stato.get("filter")
            voci = ([nodo] if nodo and "connective" not in nodo
                    else (nodo or {}).get("conditions", []))
            for voce in voci:
                valore = voce.get("value") or {}
                if valore.get("kind") == "temporal":
                    temporali[valore["expression"]] = temporali.get(
                        valore["expression"], 0) + 1

    distinte = len({c["testo"] for c in casi})
    print(f"casi generati: {len(casi)}  seme: {args.seme}  scartati: {scartati}")
    print(f"frasi distinte: {distinte}  duplicate: {len(casi) - distinte} "
          f"({(len(casi) - distinte) / len(casi):.1%}, soglia < 2%)\n")
    print("per tipo")
    for k, v in sorted(conteggi.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:5}  {v / len(casi):6.1%}")
    print("\nper entita")
    for k, v in sorted(entita.items(), key=lambda x: -x[1]):
        print(f"  {k:30} {v:5}  {v / len(casi):6.1%}")
    print("\nespressioni temporali negli stati (simboliche, §9.2)")
    for k, v in sorted(temporali.items(), key=lambda x: -x[1]):
        print(f"  {k:20} {v:5}")
    print("\nfenomeni linguistici applicati")
    for k, v in sorted(fenomeni.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:5}")
    print(f"\nScritto in {args.out}")


if __name__ == "__main__":
    main()
