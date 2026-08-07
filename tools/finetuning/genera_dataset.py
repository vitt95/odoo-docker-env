#!/usr/bin/env python3
"""Il dataset di addestramento: si sovra-genera e si sceglie (**D143**).

    python3 tools/finetuning/genera_dataset.py --genera 40000 --bersaglio 10000

## Perche' non «genera diecimila esempi»

`ai/18` §5 dice la cosa giusta — *«la cura conta piu' del volume»* — e si ferma alle
quote per famiglia. Le quote non bastano: garantiscono le **proporzioni**, non le
**forme**. Diecimila esempi possono rispettare ogni quota e insegnare dieci modelli di
frase.

Quindi: si generano quattro esempi per ognuno che serve, si filtrano, e i
sopravvissuti si scelgono **avidamente sulla copertura** — a ogni giro entra quello che
insegna la cosa piu' nuova. Generare costa CPU e niente altro; scegliere male costa una
corsa e un modello che sembra buono.

## Cosa insegna, e cosa no

**Nei pesi va un'operazione, non una nozione**: *«l'entita' e' quella in cima, gli
attributi sono quelli elencati, i riferimenti si copiano esattamente»*. Per questo il
catalogo **cambia a ogni esempio** — entita' diversa, budget diverso, sottoinsieme
diverso, e in una parte degli esempi termini che il modello non puo' conoscere. Su
quelli una risposta a memoria non esiste: l'unica strada e' leggere.

Non vanno nei pesi i nomi delle entita' di *questa* installazione. Quelli stanno nel
dizionario (**D108**, il registro delle voci approvate), dove si aggiornano senza
riaddestrare niente.

## Come si garantisce che un esempio sia giusto

Ogni esempio nasce **dall'intento e poi si verbalizza**, mai da un testo di cui si
indovina lo stato. E prima di entrare passa da tre controlli indipendenti:

1. il **validatore del contratto** sull'envelope (livelli 1-2);
2. **l'applicatore del prodotto**, che deve saperlo applicare;
3. il validatore sullo **stato risultante** — §4.2 mette la validazione sull'operazione
   *e* sullo stato, perche' un'operazione valida puo' produrre uno stato che non lo e'.

**Una differenza dichiarata rispetto a `ai/corpus/genera_corpus.py`.** Quello costruisce
lo stato atteso con un'implementazione *indipendente* dall'applicatore, ed e' cio' che
rende il confronto un test invece di una tautologia. Qui no: il bersaglio
dell'addestramento e' l'**envelope**, e lo stato serve solo a verificare che
l'envelope sia applicabile. Riscrivere l'applicatore per trecentotrentatre' entita'
sarebbe molto codice il cui unico compito e' non essere d'accordo con il prodotto.
Il prezzo, detto chiaro: un difetto dell'applicatore finirebbe nei pesi. Lo paghiamo
perche' il bersaglio e' cio' che il prodotto accetta, non cio' che un secondo autore
crede giusto.

## Il rapporto di copertura

Il dataset e' un artefatto grande e opaco. Accanto esce un file leggibile che dice
quante entita', quante applicazioni, quali simboli e con che frequenza, quanti esempi i
controlli hanno scartato, e **a che punto la copertura satura**. Se una riga dice zero,
il dataset non e' adottabile. E' lo stesso ruolo che `verifica_contratto.py` ha per il
corpus: un numero che si legge **prima** di spendere.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO_ROOT = QUI.parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from pure.bootstrap import install, install_odoo_alias  # noqa: E402

install("nli_core")
install("nli_semantics")
install("nli_engine")
install_odoo_alias()

from nli_core.application import applicator, completion  # noqa: E402
from nli_core.contract import state as state_module  # noqa: E402
from nli_core.contract import vocabulary  # noqa: E402
from nli_core.contract.state import strip_provenance  # noqa: E402
from nli_core.validation import coherence, structural  # noqa: E402
from nli_engine import prompt as prompt_module  # noqa: E402
from nli_semantics.catalogue import anchor as anchor_module  # noqa: E402

ATLANTE = QUI / "atlante.json"
ATLANTE_EN = QUI / "atlante_en.json"

#: Il tetto di **D31**: oltre sessanta attributi il catalogo affoga il modello. Il
#: minimo e' quello dell'atlante — sotto i quattro un'entita' non regge una domanda.
BUDGET_MIN, BUDGET_MAX = 6, 60

#: Caratteri per gettone, misurato sul nostro `prompt` con il tokenizzatore di Qwen:
#: 14 763 caratteri = 4 077 gettoni (`ai/19` §1). E' una stima, e basta a decidere se
#: un esempio sta nella finestra o no — la misura esatta la fara' `axolotl` con il
#: tokenizzatore vero.
CARATTERI_PER_TOKEN = 3.6

#: La finestra della ricetta (`ai/21` §6). Un esempio piu' lungo verrebbe **troncato**
#: durante l'addestramento, e un esempio troncato non insegna una risposta piu' corta:
#: insegna una risposta che finisce a meta'. Meglio scartarlo e contarlo.
LUNGHEZZA_MASSIMA = 6144

#: La versione del contratto, ripetuta qui perche' un dataset che non la dichiara e'
#: un dataset di cui nessuno sapra' mai per quale grammatica e' stato scritto.
DSL_VERSION = vocabulary.DSL_VERSION

#: Le due forme del `prompt` di **D142**.
#:
#: La lunga **non si riscrive qui**: e' quella che `prompt.system_message()` produce,
#: presa dal prodotto. Una copia scritta a mano sarebbe divergente alla prima delibera
#: che tocca il vocabolario, e addestrerebbe il modello a leggere un messaggio che
#: nessuno manda. `system_message` ignora la richiesta che riceve — le regole e i
#: vocabolari chiusi sono costanti — quindi `None` basta ed e' onesto.
SISTEMA_LUNGO = prompt_module.system_message(None)

#: La corta nomina il compito e **la versione del contratto**. La versione c'e' perche'
#: il giorno in cui il contratto cambia il `prompt` deve dirlo invece di lasciarlo
#: indovinare: la grammatica sta nei pesi, e i pesi non sanno di essere vecchi.
SISTEMA_CORTO = f"AIDA DSL {DSL_VERSION}. Answer one JSON envelope, nothing else."


# ---------------------------------------------------------------------------
# §1 — L'atlante
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Attributo:
    ref: str
    campo: str
    tipo: str
    termini_it: tuple[str, ...]
    termini_en: tuple[str, ...]
    valori: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class Entita:
    chiave: str
    modello: str
    termini_it: tuple[str, ...]
    termini_en: tuple[str, ...]
    applicazioni: tuple[str, ...]
    attributi: tuple[Attributo, ...]

    @property
    def applicazione(self) -> str:
        """L'applicazione che la porta: la prima in ordine, per stabilita'.

        Serve a dividere per **applicazione intera** (§4.6): un'entita' che finisse
        ora di qua e ora di la' renderebbe la divisione una bugia.
        """
        return self.applicazioni[0] if self.applicazioni else "base"


def carica_atlante(percorso_it: Path, percorso_en: Path) -> list[Entita]:
    """Le entita' presenti in **entrambe** le lingue, sull'intersezione dei riferimenti.

    L'intersezione e non l'unione: un attributo che esiste in una lingua sola non puo'
    comparire in un catalogo inglese, e tenerlo produrrebbe esempi che non si possono
    tradurre. Sono pochissimi — uno su 7 918 alla raccolta del 6 agosto 2026 — e non
    vale la pena di un caso speciale.
    """
    dati_it = json.loads(percorso_it.read_text())["entita"]
    dati_en = json.loads(percorso_en.read_text())["entita"]

    entita: list[Entita] = []
    for chiave in sorted(set(dati_it) & set(dati_en)):
        it, en = dati_it[chiave], dati_en[chiave]
        # I nostri stessi impianti fuori dal dataset. `nli.queue.item` e
        # `nli.interrogation` esistono in ogni installazione che ha AIDA, quindi
        # l'introspezione li vede — ma sono la macchina, non i dati dell'azienda, e
        # insegnare al modello a interrogare la propria coda e' rumore che occupa
        # posto in un budget di esempi che paghiamo.
        if it["modello"].startswith("nli."):
            continue
        per_ref_en = {a["ref"]: a for a in en["attributi"]}
        attributi = []
        for a in it["attributi"]:
            gemello = per_ref_en.get(a["ref"])
            if gemello is None:
                continue
            attributi.append(Attributo(
                ref=a["ref"], campo=a["campo"], tipo=a["tipo"],
                termini_it=tuple(a["termini"]),
                termini_en=tuple(gemello["termini"]),
                valori=tuple((v["valore"], tuple(v["termini"]))
                             for v in a.get("valori") or ()),
            ))
        if len(attributi) < 4:
            continue
        entita.append(Entita(
            chiave=chiave, modello=it["modello"],
            termini_it=tuple(it["termini"]), termini_en=tuple(en["termini"]),
            applicazioni=tuple(it.get("applicazioni") or ()),
            attributi=tuple(attributi),
        ))
    return entita


# ---------------------------------------------------------------------------
# §2 — Il catalogo di un esempio: variabile per costruzione
# ---------------------------------------------------------------------------

#: Le lingue di un catalogo, con le quote di `ai/18` §5bis.
LINGUE = ("it", "it", "it", "it", "it", "it", "it", "en", "inventata")

_SILLABE = ("va", "lor", "mek", "tis", "gon", "pru", "zan", "def", "mor", "quil")


def _parola_inventata(rng: random.Random) -> str:
    return "".join(rng.choice(_SILLABE)
                   for _ in range(rng.randint(2, 3))).capitalize()


@dataclass
class Catalogo:
    """Quello che il modello vede: la stessa forma di `prompt.catalogue_payload`."""
    entita: Entita
    lingua: str
    attributi: tuple[Attributo, ...]
    etichette: dict[str, tuple[str, ...]]
    etichetta_entita: tuple[str, ...]

    @property
    def refs(self) -> frozenset[str]:
        return frozenset({self.entita.chiave}
                         | {a.ref for a in self.attributi})

    @property
    def tipi(self) -> dict[str, str]:
        return {a.ref: a.tipo for a in self.attributi}

    def payload(self) -> dict:
        """La forma esatta che `prompt.catalogue_payload` manda.

        Esatta e non «simile»: un esempio di addestramento con una chiave diversa da
        quella di produzione insegnerebbe a leggere un catalogo che nessuno manda.
        """
        ancora = anchor_module.time_anchor(
            tuple(a.ref for a in self.attributi
                  if a.tipo in ("date", "datetime")))
        return {
            "entity": self.entita.chiave,
            "time_anchor": ancora,
            "attributes": [
                {"ref": a.ref, "terms": list(self.etichette[a.ref]), "type": a.tipo,
                 **({"values": [{"value": v, "terms": list(t)}
                                for v, t in a.valori]} if a.valori else {})}
                for a in self.attributi
            ],
            "categories": [],
            "entities": [{"ref": self.entita.chiave,
                          "terms": list(self.etichetta_entita)}],
        }

    @property
    def forma(self) -> str:
        """La fascia di grandezza, per la firma. Le fasce e non il numero esatto:
        un catalogo da 23 e uno da 24 attributi insegnano la stessa cosa."""
        n = len(self.attributi)
        return "4-9" if n < 10 else "10-19" if n < 20 else "20-39" if n < 40 else "40-60"


def costruisci_catalogo(entita: Entita, rng: random.Random) -> Catalogo:
    """Un catalogo diverso a ogni esempio.

    **E' il cuore del dataset, non un dettaglio di configurazione.** Se il catalogo
    fosse sempre lo stesso, la strada piu' breve verso una risposta giusta sarebbe
    ricordarselo, e il modello imparerebbe otto entita' invece di leggerne una.
    """
    lingua = rng.choice(LINGUE)
    disponibili = list(entita.attributi)
    rng.shuffle(disponibili)
    # Un'entita' con quattro attributi non ne regge sei: il minimo cede alla realta'
    # del catalogo, il tetto di D31 no.
    tetto = min(BUDGET_MAX, len(disponibili))
    budget = rng.randint(min(BUDGET_MIN, tetto), tetto)
    scelti = disponibili[:budget]

    # Almeno una data quando l'entita' ne ha: le espressioni di tempo sono il 15% del
    # dataset e un catalogo senza date le renderebbe irrealizzabili proprio dove
    # servono di piu'.
    if not any(a.tipo in ("date", "datetime") for a in scelti):
        date = [a for a in entita.attributi if a.tipo in ("date", "datetime")]
        if date:
            scelti[-1] = rng.choice(date)

    scelti.sort(key=lambda a: a.ref)

    if lingua == "inventata":
        etichette = {a.ref: (_parola_inventata(rng),) for a in scelti}
        etichetta_entita = (_parola_inventata(rng),)
    elif lingua == "en":
        etichette = {a.ref: a.termini_en for a in scelti}
        etichetta_entita = entita.termini_en
    else:
        etichette = {a.ref: a.termini_it for a in scelti}
        etichetta_entita = entita.termini_it

    return Catalogo(entita=entita, lingua=lingua, attributi=tuple(scelti),
                    etichette=etichette, etichetta_entita=etichetta_entita)


# ---------------------------------------------------------------------------
# §3 — L'intento, e l'envelope che ne esce
# ---------------------------------------------------------------------------

#: I predicati per tipo, presi dal contratto e non riscritti: `PREDICATES_BY_TYPE` e'
#: la fonte, e una seconda copia divergerebbe il giorno dopo.
PREDICATI = {t: tuple(sorted(p)) for t, p in vocabulary.PREDICATES_BY_TYPE.items()}

#: Le espressioni di tempo che non prendono parametri, con le parole per dirle.
TEMPO_SEMPLICE = {
    "current_year": ("quest'anno", "di quest'anno", "nell'anno in corso"),
    "current_month": ("questo mese", "di questo mese", "nel mese in corso"),
    "current_quarter": ("questo trimestre", "nel trimestre in corso"),
    "current_week": ("questa settimana", "nella settimana in corso"),
    "previous_year": ("l'anno scorso", "dell'anno scorso"),
    "previous_month": ("il mese scorso", "del mese scorso"),
    "previous_quarter": ("il trimestre scorso", "lo scorso trimestre"),
    "previous_week": ("la settimana scorsa", "la scorsa settimana"),
    "year_to_date": ("da inizio anno", "dall'inizio dell'anno"),
    "today": ("oggi", "di oggi"),
    "yesterday": ("ieri", "di ieri"),
    "tomorrow": ("domani", "di domani"),
}

#: Le parametriche, con la parola che porta il numero.
TEMPO_PARAMETRICO = {
    "last_n_days": "negli ultimi {n} giorni",
    "last_n_months": "negli ultimi {n} mesi",
    "last_n_weeks": "nelle ultime {n} settimane",
    "next_n_days": "nei prossimi {n} giorni",
}

#: I periodi che una frase **nomina** (**D141**), e le parole con cui si nominano.
#: Sono le stesse che il lessico di **D144** riconosce, ed e' voluto: un esempio di
#: addestramento che nominasse un periodo con parole che la rete non riconosce
#: passerebbe l'addestramento e verrebbe fermato in servizio.
MESI = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")
ORDINALI = ("primo", "secondo", "terzo", "quarto")

#: I periodi che **nessun simbolo sa dire**: qui diventano rifiuti, ed e' la meta'
#: della rete di D144 che vive nei pesi invece che nel codice.
PERIODI_INESPRIMIBILI = ("bimestre", "quadrimestre", "quinquennio", "decennio")

#: Le richieste fuori portata, per motivo. Le parole sono quelle di
#: `nli_semantics/scope_lexicon.py`: un rifiuto addestrato con parole che il lessico
#: di **D119** non riconosce sarebbe un rifiuto che il prodotto non lascia passare.
FUORI_PORTATA = {
    "creazione_record": ("genera un preventivo", "crea un'attivita' di richiamo",
                         "aggiungi un cliente nuovo"),
    "modifica_dati": ("modifica i prezzi", "aggiorna lo stato",
                      "cambia il venditore"),
    "cancellazione_record": ("cancella i vecchi", "elimina i duplicati"),
    "invio_esterno": ("invia una mail al commerciale", "esporta tutto in un foglio"),
    "previsione": ("prevedi quanto vendero' il mese prossimo",
                   "stima il fatturato del trimestre"),
}

FAMIGLIE = ("semplice", "aggregazione", "tempo", "presentazione", "rifiuto")


@dataclass
class Intento:
    """Cosa l'utente vuole, prima che esistano parole per dirlo."""
    famiglia: str
    catalogo: Catalogo
    condizioni: list[dict] = field(default_factory=list)
    gruppi: list[str] = field(default_factory=list)
    misure: list[dict] = field(default_factory=list)
    campi: list[str] = field(default_factory=list)
    ordine: list[str] = field(default_factory=list)
    limite: int | None = None
    esito: str = "operations"
    nota_portata: str | None = None
    frammento_portata: str = ""


def _valore_per(attributo: Attributo, rng: random.Random) -> tuple[dict, str] | None:
    """Un valore plausibile per quel tipo, e le parole per dirlo.

    `None` quando quel tipo non regge una condizione che sappiamo verbalizzare: e'
    meglio un esempio in meno che un esempio che insegna una forma sbagliata.
    """
    tipo = attributo.tipo
    if tipo == "enum" and attributo.valori:
        valore, termini = rng.choice(attributo.valori)
        parola = rng.choice(termini) if termini else valore
        return {"kind": "enum", "items": [valore]}, parola
    if tipo == "number":
        if rng.random() < 0.15:
            basso = rng.choice((100, 500, 1000, 5000))
            alto = basso * rng.choice((2, 5, 10))
            return ({"kind": "range", "from": basso, "to": alto},
                    f"fra {basso} e {alto}")
        n = rng.choice((100, 500, 1000, 5000, 10000, 50000))
        return {"kind": "number", "value": n}, str(n)
    if tipo == "boolean":
        return {"kind": "boolean", "value": True}, ""
    if tipo == "text":
        parola = rng.choice(("Milano", "Roma", "Torino", "Alfa", "Beta", "SpA"))
        return {"kind": "text", "text": parola}, parola
    if tipo == "relation":
        # `reference` e' il nome che l'utente pronuncia, non un identificativo: e' il
        # risolutore a trovarlo, ed e' la ragione per cui il modello non deve
        # inventarne uno (§8.1).
        nome = rng.choice(("Rossi", "Bianchi", "Verdi", "Ferrari", "Conti"))
        return {"kind": "reference", "text": nome}, nome
    return None


def _condizione_confronto(catalogo: Catalogo, rng: random.Random) -> dict | None:
    candidati = [a for a in catalogo.attributi
                 if a.tipo in ("number", "enum", "boolean", "text", "relation")
                 and PREDICATI.get(a.tipo)]
    if not candidati:
        return None
    attributo = rng.choice(candidati)
    valore = _valore_per(attributo, rng)
    if valore is None:
        return None
    corpo, parola = valore
    ammessi = [p for p in PREDICATI[attributo.tipo]
               if corpo["kind"] in vocabulary.PREDICATE_VALUE_KINDS.get(p, frozenset())]
    if attributo.tipo == "boolean":
        # Un booleano non porta valore: il predicato **e'** la domanda. Il contratto
        # lo ammette come ridondante (§17.1), ma insegnarlo ridondante sarebbe
        # insegnare token che non dicono niente.
        ammessi = [p for p in PREDICATI["boolean"] if p in ("is_true", "is_false")]
        corpo = None
    if not ammessi:
        return None
    return {"tipo": "confronto", "attributo": attributo,
            "predicato": rng.choice(ammessi), "valore": corpo, "parola": parola}


def _condizione_tempo(catalogo: Catalogo, rng: random.Random,
                      *, nominato: bool = False,
                      inesprimibile: bool = False) -> dict | None:
    date = [a for a in catalogo.attributi if a.tipo in ("date", "datetime")]
    if not date:
        return None
    attributo = rng.choice(date)

    if inesprimibile:
        unita = rng.choice(PERIODI_INESPRIMIBILI)
        ordinale = rng.choice(ORDINALI[:2])
        return {"tipo": "tempo", "attributo": attributo, "inesprimibile": True,
                "parola": f"nel {ordinale} {unita}"}

    if nominato:
        # I quattro simboli di **D141**, con le parole che il lessico di **D144**
        # riconosce. L'accoppiamento e' voluto: un esempio che nominasse un periodo
        # con parole che la rete non riconosce passerebbe l'addestramento e verrebbe
        # fermato in servizio — cioe' insegnerebbe una cosa che il prodotto rifiuta.
        quale = rng.randint(0, 3)
        if quale == 0:
            n = rng.randint(1, 12)
            return {"tipo": "tempo", "attributo": attributo,
                    "valore": {"kind": "temporal", "expression": "month_of_year",
                               "n": n},
                    "parola": f"a {MESI[n - 1]}"}
        if quale == 1:
            n = rng.randint(1, 4)
            return {"tipo": "tempo", "attributo": attributo,
                    "valore": {"kind": "temporal", "expression": "quarter_of_year",
                               "n": n},
                    "parola": f"nel {ORDINALI[n - 1]} trimestre"}
        if quale == 2:
            n = rng.randint(1, 2)
            return {"tipo": "tempo", "attributo": attributo,
                    "valore": {"kind": "temporal", "expression": "half_of_year",
                               "n": n},
                    "parola": f"nel {ORDINALI[n - 1]} semestre"}
        n = rng.randint(2019, 2026)
        return {"tipo": "tempo", "attributo": attributo,
                "valore": {"kind": "temporal", "expression": "year_of", "n": n},
                "parola": f"nel {n}"}

    if rng.random() < 0.12:
        # Le date scritte per esteso. D144 le lascia fuori di proposito: portano un
        # valore che l'utente ha **scritto**, non un periodo che ha nominato.
        anno, mese, giorno = rng.randint(2023, 2026), rng.randint(1, 12), rng.randint(1, 28)
        if rng.random() < 0.5:
            return {"tipo": "tempo", "attributo": attributo, "predicato": "on",
                    "valore": {"kind": "temporal", "expression": "absolute",
                               "date": f"{anno}-{mese:02d}-{giorno:02d}"},
                    "parola": f"il {giorno} {MESI[mese - 1]} {anno}"}
        return {"tipo": "tempo", "attributo": attributo,
                "valore": {"kind": "temporal", "expression": "absolute_range",
                           "from": f"{anno}-01-01", "to": f"{anno}-06-30"},
                "parola": f"dal 1 gennaio {anno} al 30 giugno {anno}"}

    if rng.random() < 0.3:
        simbolo = rng.choice(list(TEMPO_PARAMETRICO))
        n = rng.choice((7, 30, 60, 90, 3, 6, 12))
        return {"tipo": "tempo", "attributo": attributo,
                "valore": {"kind": "temporal", "expression": simbolo, "n": n},
                "parola": TEMPO_PARAMETRICO[simbolo].format(n=n)}
    simbolo = rng.choice(list(TEMPO_SEMPLICE))
    return {"tipo": "tempo", "attributo": attributo,
            "valore": {"kind": "temporal", "expression": simbolo},
            "parola": rng.choice(TEMPO_SEMPLICE[simbolo])}


def genera_intento(entita: Entita, famiglia: str, rng: random.Random) -> Intento | None:
    catalogo = costruisci_catalogo(entita, rng)
    intento = Intento(famiglia=famiglia, catalogo=catalogo)

    if famiglia == "rifiuto":
        if rng.random() < 0.35:
            # Il periodo che nessun simbolo sa dire: la rete di D144 nei pesi.
            condizione = _condizione_tempo(catalogo, rng, inesprimibile=True)
            if condizione is None:
                return None
            intento.condizioni = [condizione]
            intento.esito = "clarification_periodo"
            return intento
        nota = rng.choice(list(FUORI_PORTATA))
        intento.esito = "out_of_scope"
        intento.nota_portata = nota
        intento.frammento_portata = rng.choice(FUORI_PORTATA[nota])
        return intento

    if famiglia == "tempo":
        condizione = _condizione_tempo(catalogo, rng, nominato=rng.random() < 0.45)
        if condizione is None:
            return None
        intento.condizioni = [condizione]
        if rng.random() < 0.3:
            altra = _condizione_confronto(catalogo, rng)
            if altra:
                intento.condizioni.append(altra)
        return intento

    if famiglia == "aggregazione":
        numerici = [a for a in catalogo.attributi if a.tipo == "number"]
        raggruppabili = [a for a in catalogo.attributi
                         if a.tipo in ("enum", "relation")]
        if not raggruppabili:
            return None
        intento.gruppi = [rng.choice(raggruppabili).ref]
        distinguibili = [a for a in catalogo.attributi
                         if a.tipo in ("relation", "enum", "text")]
        sorte = rng.random()
        if numerici and sorte < 0.6:
            intento.misure = [{"funzione": rng.choice(("sum", "avg", "max", "min")),
                               "ref": rng.choice(numerici).ref}]
        elif distinguibili and sorte < 0.8:
            # *«Quanti clienti diversi»*: conta i valori, non le righe. E' l'unica
            # aggregazione che chiede un attributo pur essendo un conteggio.
            intento.misure = [{"funzione": "count_distinct",
                               "ref": rng.choice(distinguibili).ref}]
        else:
            intento.misure = [{"funzione": "count", "ref": None}]
        return intento

    if famiglia == "presentazione":
        ordinabili = [a for a in catalogo.attributi
                      if a.tipo in ("number", "date", "datetime", "text")]
        if not ordinabili:
            return None
        if rng.random() < 0.6:
            intento.ordine = [rng.choice(ordinabili).ref]
        if rng.random() < 0.5:
            intento.limite = rng.choice((5, 10, 20))
        mostrabili = [a.ref for a in catalogo.attributi]
        if rng.random() < 0.5 and len(mostrabili) >= 2:
            intento.campi = rng.sample(mostrabili, 2)
        if not (intento.ordine or intento.limite or intento.campi):
            intento.limite = 10
        return intento

    # semplice
    quante = 1 if rng.random() < 0.6 else 2
    for _ in range(quante):
        condizione = _condizione_confronto(catalogo, rng)
        if condizione is not None:
            intento.condizioni.append(condizione)
    if not intento.condizioni:
        return None
    return intento


def envelope_di(intento: Intento, rng: random.Random) -> dict:
    """L'intento nella forma che il modello deve scrivere.

    La **provenienza** e' la parte che conta: §10.3 la definisce come *il frammento
    della frase che ha prodotto l'operazione*, ed e' cio' su cui D105, D119 e D144
    verificano. Un dataset con provenienze approssimative insegnerebbe al modello a
    citare a caso, e le tre reti lo fermerebbero in servizio.
    """
    catalogo = intento.catalogo
    entita_detta = rng.choice(catalogo.etichetta_entita)

    if intento.esito == "out_of_scope":
        return {"dsl_version": DSL_VERSION, "outcome": "out_of_scope",
                "confidence": round(rng.uniform(0.9, 0.99), 2),
                "scope_note": intento.nota_portata,
                "scope_provenance": {"text": intento.frammento_portata}}

    if intento.esito == "clarification_periodo":
        condizione = intento.condizioni[0]
        return {"dsl_version": DSL_VERSION, "outcome": "clarification",
                "confidence": round(rng.uniform(0.3, 0.6), 2),
                "clarification": {
                    "question": "Quale periodo intendi esattamente?",
                    "provenance": {"text": condizione["parola"]},
                    "options": [
                        {"label": "Quest'anno", "operations": [
                            {"op": "add_condition", "condition": {
                                "ref": condizione["attributo"].ref,
                                "predicate": "within",
                                "value": {"kind": "temporal",
                                          "expression": "current_year"}}}]},
                        {"label": "Il trimestre in corso", "operations": [
                            {"op": "add_condition", "condition": {
                                "ref": condizione["attributo"].ref,
                                "predicate": "within",
                                "value": {"kind": "temporal",
                                          "expression": "current_quarter"}}}]},
                    ]}}

    operations = [{"op": "set_target", "ref": catalogo.entita.chiave,
                   "provenance": {"text": entita_detta.lower()}}]

    for condizione in intento.condizioni:
        corpo = {"ref": condizione["attributo"].ref}
        if condizione["tipo"] == "tempo":
            corpo["predicate"] = condizione.get("predicato", "within")
            corpo["value"] = condizione["valore"]
        else:
            corpo["predicate"] = condizione["predicato"]
            if condizione["valore"] is not None:
                corpo["value"] = condizione["valore"]
        operations.append({"op": "add_condition", "combine": "all",
                           "condition": corpo,
                           "provenance": {"text": condizione["parola"]}})

    for ref in intento.gruppi:
        operations.append({"op": "add_group", "ref": ref,
                           "provenance": {"text": _detto(catalogo, ref, rng)}})
    for misura in intento.misure:
        corpo = {"op": "add_measure", "function": misura["funzione"]}
        if misura["ref"]:
            corpo["ref"] = misura["ref"]
        corpo["provenance"] = {"text": _parola_misura(misura["funzione"])}
        operations.append(corpo)
    if intento.campi:
        operations.append({"op": "set_fields", "refs": list(intento.campi),
                           "provenance": {"text": "mostrami anche " + " e ".join(
                               _detto(catalogo, r, rng) for r in intento.campi)}})
    for ref in intento.ordine:
        operations.append({"op": "add_order", "ref": ref,
                           "provenance": {"text": "ordinati per "
                                                  + _detto(catalogo, ref, rng)}})
    if intento.limite is not None:
        operations.append({"op": "set_limit", "value": intento.limite,
                           "provenance": {"text": f"i primi {intento.limite}"}})

    return {"dsl_version": DSL_VERSION, "outcome": "operations",
            "confidence": round(rng.uniform(0.82, 0.98), 2),
            "operations": operations}


def _detto(catalogo: Catalogo, ref: str, rng: random.Random) -> str:
    termini = catalogo.etichette.get(ref) or (ref,)
    return rng.choice(termini).lower()


#: Il verso di un confronto, detto a parole. Una sola tabella: il frammento **e'** la
#: provenienza, e D105, D119 e D144 ci verificano sopra. Un frammento che dicesse
#: *«importo 5000»* per `less_than` insegnerebbe a citare male, e le reti fermerebbero
#: in servizio proprio cio' che l'addestramento ha insegnato.
VERSO = {"greater_than": "sopra", "less_than": "sotto", "equals": "uguale a",
         "greater_or_equal": "da", "less_or_equal": "fino a",
         "is_one_of": "", "is_not_one_of": "diverso da", "contains": "che contiene",
         "starts_with": "che comincia per", "between": ""}


def _frammento_confronto(catalogo: Catalogo, condizione: dict,
                         rng: random.Random) -> str:
    """*«con importo sopra 5000»*: attributo, verso, valore."""
    nome = _detto(catalogo, condizione["attributo"].ref, rng)
    if condizione["valore"] is None:
        return nome
    verso = VERSO.get(condizione["predicato"], "")
    return " ".join(p for p in (nome, verso, condizione["parola"]) if p)


def _parola_misura(funzione: str) -> str:
    return {"sum": "il totale", "avg": "la media", "max": "il massimo",
            "min": "il minimo", "count": "quanti sono",
            "count_distinct": "quanti diversi"}.get(funzione, funzione)


# ---------------------------------------------------------------------------
# §4 — La frase
# ---------------------------------------------------------------------------

APERTURE = ("mostrami", "fammi vedere", "voglio vedere", "elenca", "dammi",
            "quali sono", "vorrei vedere")


def _elidi(sintagma: str) -> str:
    return sintagma


def verbalizza(intento: Intento, envelope: dict, rng: random.Random) -> str:
    """Dall'intento a una frase italiana plausibile.

    **Meno ricca di quella di `genera_corpus.py`, e per una ragione.** Quella si
    appoggia a un lessico L1 scritto a mano che conosce il *genere* di otto entita' e
    le forme nominali dei loro attributi, e ci costruisce sopra accordi grammaticali.
    Su trecentotrentatre' entita' quel lessico non esiste, e indovinare il genere
    dall'etichetta sbaglierebbe in silenzio.

    Quindi qui le forme sono quelle che **non chiedono accordo**: l'articolo resta
    fuori, gli attributi si nominano dopo *«con»*, *«per»*, *«a»*. Una frase un po'
    piu' piatta, mai una frase sbagliata. La ricchezza la portano le 918 frasi del
    corpus e — soprattutto — gli enunciati veri di **D85**, che nessun generatore
    sostituisce.
    """
    catalogo = intento.catalogo
    entita = rng.choice(catalogo.etichetta_entita).lower()

    if intento.esito == "out_of_scope":
        return f"{rng.choice(APERTURE)} {entita} e {intento.frammento_portata}"

    pezzi = [rng.choice(APERTURE), entita]

    for condizione in intento.condizioni:
        if condizione["tipo"] == "tempo":
            pezzi.append(condizione["parola"])
        elif condizione["valore"] is None:
            pezzi.append(f"con {_detto(catalogo, condizione['attributo'].ref, rng)}")
        elif condizione["valore"]["kind"] in ("number", "range"):
            pezzi.append("con " + _frammento_confronto(catalogo, condizione, rng))
        else:
            pezzi.append(f"{condizione['parola'].lower()}")

    for misura in intento.misure:
        if misura["funzione"] == "count":
            pezzi.insert(0, "quanti")
        else:
            pezzi.append(f"con {_parola_misura(misura['funzione'])} "
                         f"di {_detto(catalogo, misura['ref'], rng)}")
    for ref in intento.gruppi:
        pezzi.append(f"raggruppati per {_detto(catalogo, ref, rng)}")
    for ref in intento.ordine:
        pezzi.append(f"ordinati per {_detto(catalogo, ref, rng)}")
    if intento.campi:
        pezzi.append("con " + " e ".join(_detto(catalogo, r, rng)
                                         for r in intento.campi))
    if intento.limite is not None:
        pezzi.append(f"solo i primi {intento.limite}")

    return " ".join(p for p in pezzi if p)


# ---------------------------------------------------------------------------
# §4bis — Il secondo turno: i raffinamenti
# ---------------------------------------------------------------------------

def _condizioni_di(stato: dict) -> list[dict]:
    """Le condizioni di uno stato, comunque il filtro sia scritto.

    Con una sola condizione il filtro **e'** quella condizione; con piu' di una
    diventa un nodo con `connective` e `conditions`. Due forme, un solo significato:
    chi legge lo stato deve saperle entrambe o si accorgera' della seconda per via di
    un guasto.
    """
    filtro = stato.get("filter") or {}
    if not filtro:
        return []
    if filtro.get("conditions"):
        return [c for c in filtro["conditions"] if isinstance(c, dict)]
    return [filtro] if filtro.get("ref") else []


def _prima_voce(stato: dict, chiave: str) -> dict | None:
    voci = stato.get(chiave) or []
    return voci[0] if voci else None


def raffinamento_di(stato: dict, catalogo: Catalogo, rng: random.Random
                    ) -> tuple[list[dict], str] | None:
    """Le operazioni del secondo turno e la frase ellittica che le chiede.

    **Ogni raffinamento deve avere davvero su cosa agire.** Le possibilita' si
    costruiscono da quello che lo stato contiene, non da un elenco fisso: un
    *«togli il filtro»* generato su uno stato senza filtri sarebbe un esempio che
    insegna un'operazione che il prodotto rifiuta.
    """
    condizioni = _condizioni_di(stato)
    possibili: list[str] = ["aggiungi_condizione", "limite", "vista", "ricomincia",
                            "annulla", "apri"]
    if condizioni:
        possibili += ["togli_condizione", "sostituisci_condizione", "svuota_filtro"]
    if stato.get("fields"):
        # `add_field` **aggiunge a una selezione che esiste**. Su uno stato senza
        # colonne scelte l'applicatore lo rifiuta, e ha ragione: le colonne di
        # partenza non sono una selezione, sono l'assenza di una selezione. Chi
        # sceglie da zero dice `set_fields`.
        possibili += ["togli_campo", "svuota_campi", "aggiungi_campo"]
    else:
        possibili += ["imposta_campi"]
    if stato.get("group_by"):
        possibili += ["togli_gruppo", "svuota_gruppi"]
    else:
        possibili += ["aggiungi_gruppo"]
    if stato.get("measures"):
        possibili += ["togli_misura"]
    if stato.get("order_by"):
        possibili += ["svuota_ordine", "cambia_ordine"]
    else:
        possibili += ["aggiungi_ordine"]

    # **Non uniforme, e per una ragione misurata.** Sei raffinamenti sono sempre
    # possibili — un limite, una vista, un annulla si chiedono su qualunque stato —
    # mentre *«togli il raggruppamento»* richiede uno stato che un raggruppamento ce
    # l'abbia, e capita in un quarto dei casi. Scegliendo a caso fra le possibilita',
    # i condizionati escono tre volte meno e restano sotto il minimo di cinquanta
    # esempi che D143 pretende per ogni simbolo. Il peso ripara lo squilibrio alla
    # sorgente, invece di generare il triplo di esempi per pescarne abbastanza.
    sempre = {"aggiungi_condizione", "limite", "vista", "ricomincia", "annulla",
              "apri"}
    pesi = [1 if q in sempre else 3 for q in possibili]
    quale = rng.choices(possibili, pesi)[0]

    if quale == "aggiungi_condizione":
        condizione = _condizione_confronto(catalogo, rng)
        if condizione is None:
            return None
        corpo = {"ref": condizione["attributo"].ref,
                 "predicate": condizione["predicato"]}
        if condizione["valore"] is not None:
            corpo["value"] = condizione["valore"]
        parola = ("e solo quelli con "
                  + _frammento_confronto(catalogo, condizione, rng))
        return ([{"op": "add_condition", "combine": "all", "condition": corpo,
                  "provenance": {"text": parola}}], parola)

    if quale == "togli_condizione":
        bersaglio = rng.choice(condizioni)
        # Le due vie di indirizzamento di §6.3, una per volta: l'identificativo che
        # lo stato mostra, o il riferimento. Mai tutt'e due — sarebbe ambiguo, e il
        # livello 1 lo rifiuta.
        if rng.random() < 0.5 and bersaglio.get("id"):
            indirizzo = {"id": bersaglio["id"]}
        else:
            indirizzo = {"ref": bersaglio["ref"]}
        parola = f"togli il filtro su {_detto(catalogo, bersaglio['ref'], rng)}"
        return ([{"op": "remove_condition", **indirizzo,
                  "provenance": {"text": parola}}], parola)

    if quale == "sostituisci_condizione":
        bersaglio = rng.choice(condizioni)
        if not bersaglio.get("id"):
            return None
        nuova = _condizione_confronto(catalogo, rng)
        if nuova is None:
            return None
        corpo = {"ref": nuova["attributo"].ref, "predicate": nuova["predicato"]}
        if nuova["valore"] is not None:
            corpo["value"] = nuova["valore"]
        parola = "anzi, " + _frammento_confronto(catalogo, nuova, rng)
        return ([{"op": "replace_condition", "id": bersaglio["id"],
                  "condition": corpo, "provenance": {"text": parola}}], parola)

    if quale == "svuota_filtro":
        parola = rng.choice(("togli tutti i filtri", "senza filtri",
                             "leva ogni filtro"))
        return ([{"op": "clear_filter", "provenance": {"text": parola}}], parola)

    if quale == "aggiungi_campo":
        gia_scelti = {v["ref"] for v in stato.get("fields") or []}
        candidati = [a.ref for a in catalogo.attributi if a.ref not in gia_scelti]
        if not candidati:
            return None
        ref = rng.choice(candidati)
        parola = f"mostrami anche {_detto(catalogo, ref, rng)}"
        return ([{"op": "add_field", "ref": ref,
                  "provenance": {"text": parola}}], parola)

    if quale == "imposta_campi":
        candidati = [a.ref for a in catalogo.attributi]
        if len(candidati) < 2:
            return None
        refs = rng.sample(candidati, 2)
        parola = ("fammi vedere solo "
                  + " e ".join(_detto(catalogo, r, rng) for r in refs))
        return ([{"op": "set_fields", "refs": refs,
                  "provenance": {"text": parola}}], parola)

    if quale == "apri":
        # Solo per posizione: *«apri il terzo»*. La selezione per attributo esiste nel
        # contratto, ma su un catalogo qualunque non sappiamo quale valore ci sia
        # davvero fra i risultati, e un esempio che apre un record inesistente
        # insegnerebbe a inventare (§6.6 vieta anche di scegliere per identificativo,
        # per la stessa ragione).
        posizione = rng.randint(1, 5)
        parola = rng.choice((f"apri il {posizione}",
                             f"aprimi il numero {posizione}",
                             f"fammi vedere il {posizione}"))
        return ([{"op": "open_record",
                  "selector": {"by": "position", "value": posizione},
                  "provenance": {"text": parola}}], parola)

    if quale == "togli_campo":
        voce = _prima_voce(stato, "fields")
        if not voce:
            return None
        parola = f"togli {_detto(catalogo, voce['ref'], rng)}"
        return ([{"op": "remove_field", "ref": voce["ref"],
                  "provenance": {"text": parola}}], parola)

    if quale == "svuota_campi":
        parola = rng.choice(("torna alle colonne di prima", "togli le colonne"))
        return ([{"op": "clear_fields", "provenance": {"text": parola}}], parola)

    if quale == "aggiungi_gruppo":
        candidati = [a.ref for a in catalogo.attributi
                     if a.tipo in ("enum", "relation")]
        if not candidati:
            return None
        ref = rng.choice(candidati)
        parola = f"raggruppa per {_detto(catalogo, ref, rng)}"
        return ([{"op": "add_group", "ref": ref,
                  "provenance": {"text": parola}}], parola)

    if quale == "togli_gruppo":
        voce = _prima_voce(stato, "group_by")
        if not voce:
            return None
        parola = f"non raggruppare per {_detto(catalogo, voce['ref'], rng)}"
        return ([{"op": "remove_group", "ref": voce["ref"],
                  "provenance": {"text": parola}}], parola)

    if quale == "togli_misura":
        voce = _prima_voce(stato, "measures")
        if not voce:
            return None
        # Le due vie di §6.3 anche qui: `count` non ha attributo, quindi una misura
        # si indirizza per funzione quando il riferimento non c'e'.
        if voce.get("ref") and rng.random() < 0.5:
            indirizzo = {"ref": voce["ref"]}
            parola = f"togli {_detto(catalogo, voce['ref'], rng)}"
        else:
            indirizzo = {"function": voce["function"]}
            parola = f"togli {_parola_misura(voce['function'])}"
        return ([{"op": "remove_measure", **indirizzo,
                  "provenance": {"text": parola}}], parola)

    if quale == "svuota_gruppi":
        parola = rng.choice(("senza raggruppamenti", "togli i raggruppamenti"))
        return ([{"op": "clear_groups", "provenance": {"text": parola}}], parola)

    if quale == "aggiungi_ordine":
        candidati = [a.ref for a in catalogo.attributi
                     if a.tipo in ("number", "date", "datetime", "text")]
        if not candidati:
            return None
        ref = rng.choice(candidati)
        parola = f"ordina per {_detto(catalogo, ref, rng)}"
        return ([{"op": "add_order", "ref": ref,
                  "provenance": {"text": parola}}], parola)

    if quale == "cambia_ordine":
        voce = _prima_voce(stato, "order_by")
        if not voce:
            return None
        verso = "asc" if voce.get("direction") == "desc" else "desc"
        parola = ("dal piu' grande al piu' piccolo" if verso == "desc"
                  else "dal piu' piccolo al piu' grande")
        return ([{"op": "set_order", "ref": voce["ref"], "direction": verso,
                  "provenance": {"text": parola}}], parola)

    if quale == "svuota_ordine":
        parola = rng.choice(("non ordinarli", "togli l'ordinamento"))
        return ([{"op": "clear_order", "provenance": {"text": parola}}], parola)

    if quale == "vista":
        vista = rng.choice(sorted(vocabulary.VIEWS))
        parola = {"list": "mettilo in elenco", "chart": "fammi un grafico",
                  "pivot": "mettilo in tabella incrociata",
                  "kanban": "mettilo a schede"}.get(vista, f"vista {vista}")
        return ([{"op": "set_view", "view": vista,
                  "provenance": {"text": parola}}], parola)

    if quale == "limite":
        n = rng.choice((5, 10, 20, 50))
        parola = f"solo i primi {n}"
        return ([{"op": "set_limit", "value": n,
                  "provenance": {"text": parola}}], parola)

    if quale == "ricomincia":
        # **`reset` non viaggia da solo.** Da solo lascia uno stato senza bersaglio,
        # che il validatore rifiuta — giustamente: non e' un'interrogazione. Il
        # vocabolario lo dice gia' (§4.5): *«una sola intenzione produce `reset`
        # seguito da `set_target`»*, ed e' anche la frase che una persona dice davvero.
        entita_detta = rng.choice(catalogo.etichetta_entita).lower()
        parola = rng.choice(("ricominciamo", "azzera tutto", "riparti da capo"))
        frase = f"{parola}, mostrami {entita_detta}"
        return ([{"op": "reset", "provenance": {"text": parola}},
                 {"op": "set_target", "ref": catalogo.entita.chiave,
                  "provenance": {"text": entita_detta}}], frase)

    if quale == "annulla":
        parola = rng.choice(("annulla l'ultima cosa", "torna indietro",
                             "no, disfa quello che ho appena detto"))
        return ([{"op": "revert_last", "provenance": {"text": parola}}], parola)

    return None


def genera_raffinamento(entita: Entita, rng: random.Random,
                        scarti: Counter) -> "Esempio | None":
    """Un esempio di secondo turno: stato di partenza, frase ellittica, operazioni.

    **La trappola specifica di questa famiglia**, e la ragione per cui non e' stata
    scritta di fretta: lo stato che il prodotto manda al modello **non ha i
    frammenti** — `strip_provenance` li toglie quando lo stato si salva, finche'
    **D54** non li pseudonimizza. Un esempio con le provenienze dentro insegnerebbe al
    modello a lavorare con un'informazione che in servizio non arriva mai, e il difetto
    si vedrebbe solo dal secondo turno in poi — cioe' dove nessuna delle nostre misure
    guarda (`00` §46, la lezione del 5 agosto).
    """
    # Anche le aggregazioni: senza uno stato che porti raggruppamenti e misure,
    # `remove_group`, `clear_groups` e `remove_measure` non avrebbero mai su cosa
    # agire, e sarebbero simboli che il dataset non insegna mai.
    famiglia_base = rng.choice(("semplice", "tempo", "presentazione",
                                "aggregazione"))
    intento = genera_intento(entita, famiglia_base, rng)
    if intento is None:
        return None
    primo = envelope_di(intento, rng)
    motivo, stato = valida(primo, intento.catalogo)
    if motivo or stato is None:
        scarti["raffinamento_primo_turno"] += 1
        return None

    # Esattamente cio' che la conduttura manda: lo stato salvato, senza frammenti.
    stato_mostrato = strip_provenance(stato)

    proposta = raffinamento_di(stato, intento.catalogo, rng)
    if proposta is None:
        scarti["raffinamento_non_costruibile"] += 1
        return None
    operazioni, frase = proposta

    envelope = {"dsl_version": DSL_VERSION, "outcome": "operations",
                "confidence": round(rng.uniform(0.85, 0.98), 2),
                "operations": operazioni}
    motivo, _ = valida(envelope, intento.catalogo, stato)
    if motivo:
        scarti[motivo.split(":")[0]] += 1
        return None

    lunghezza = _lunghezza_stimata(intento.catalogo.payload(), frase, envelope,
                                   stato=stato_mostrato)
    if lunghezza > LUNGHEZZA_MASSIMA:
        scarti["troppo_lungo"] += 1
        return None

    celle = set(firma(intento, envelope))
    celle.add(("turno", "raffinamento"))
    celle.discard(("famiglia", famiglia_base))
    celle.add(("famiglia", "raffinamento"))

    return Esempio(
        entita=entita.chiave,
        applicazione=entita.applicazione,
        famiglia="raffinamento",
        lingua=intento.catalogo.lingua,
        frase=frase,
        catalogo=intento.catalogo.payload(),
        envelope=envelope,
        celle=tuple(sorted(celle)),
        modello_frase=f"raffinamento:{operazioni[0]['op']}",
        stato=stato_mostrato,
    )


# ---------------------------------------------------------------------------
# §5 — La firma: l'unita' di diversita' (D143)
# ---------------------------------------------------------------------------

def firma(intento: Intento, envelope: dict) -> tuple[tuple[str, str], ...]:
    """Cio' che questo esempio **insegna**, come insieme di celle.

    Due esempi con la stessa firma insegnano la stessa cosa, per quanto le parole
    siano diverse. E' su queste celle che la selezione di D143 massimizza.
    """
    catalogo = intento.catalogo
    celle: set[tuple[str, str]] = {
        ("entita", catalogo.entita.chiave),
        ("applicazione", catalogo.entita.applicazione),
        ("forma_catalogo", catalogo.forma),
        ("lingua", catalogo.lingua),
        ("famiglia", intento.famiglia),
        ("esito", envelope["outcome"]),
    }
    if envelope["outcome"] == "out_of_scope":
        celle.add(("nota_portata", envelope["scope_note"]))
    for operazione in envelope.get("operations") or ():
        celle.add(("op", operazione["op"]))
        condizione = operazione.get("condition") or {}
        if condizione.get("predicate"):
            celle.add(("predicato", condizione["predicate"]))
        valore = condizione.get("value") or {}
        if valore.get("kind"):
            celle.add(("kind", valore["kind"]))
        if valore.get("expression"):
            celle.add(("tempo", valore["expression"]))
        if operazione.get("function"):
            celle.add(("aggregazione", operazione["function"]))

    # **Le coppie, e sono la parte che rende il numero onesto.** Con le sole celle
    # singole la copertura satura appena ogni entita' e ogni simbolo si sono visti una
    # volta — cioe' intorno al numero delle entita', qualunque cosa il dataset
    # contenga. Ma il compito non e' «vedere `add_group`» e «vedere un catalogo
    # inglese»: e' vedere `add_group` **su** un catalogo inglese. Quel che si vuole
    # imparare sta nelle combinazioni, e una copertura che non le conta dichiara
    # «satura» un dataset che non ha ancora visto niente di interessante.
    famiglia = dict(celle).get("famiglia", "?")
    lingua = catalogo.lingua
    coppie = {("famiglia_x_lingua", f"{famiglia}|{lingua}"),
              ("famiglia_x_forma", f"{famiglia}|{catalogo.forma}")}
    for chiave, valore in list(celle):
        if chiave in ("op", "predicato", "kind", "tempo", "aggregazione"):
            coppie.add((f"{chiave}_x_lingua", f"{valore}|{lingua}"))
            coppie.add((f"{chiave}_x_famiglia", f"{valore}|{famiglia}"))
    return tuple(sorted(celle | coppie))


# ---------------------------------------------------------------------------
# §6 — I controlli: tre, indipendenti
# ---------------------------------------------------------------------------

@dataclass
class Esempio:
    entita: str
    applicazione: str
    famiglia: str
    lingua: str
    frase: str
    catalogo: dict
    envelope: dict
    celle: tuple[tuple[str, str], ...]
    modello_frase: str
    #: Lo stato del turno precedente, gia' senza frammenti. `None` per un'apertura.
    stato: dict | None = None


def valida(envelope: dict, catalogo: Catalogo,
           stato_iniziale: dict | None = None) -> tuple[str | None, dict | None]:
    """`(None, stato)` se l'esempio e' buono, `(motivo, None)` se va scartato.

    Quattro controlli indipendenti, gli stessi che l'interprete e la conduttura fanno
    su una risposta vera. Il quarto — la **coerenza rispetto allo stato** — esiste solo
    per i secondi turni: un'operazione puo' essere valida da sola e non avere senso su
    quello stato, per esempio togliere una condizione che non c'e'.
    """
    fallimenti = structural.validate_envelope(envelope)
    if fallimenti:
        return f"envelope:{fallimenti[0].code}", None

    if envelope["outcome"] != "operations":
        return None, None

    fuori = [op.get("ref") for op in envelope["operations"]
             if op.get("ref") and op["ref"] not in catalogo.refs]
    if fuori:
        return f"ref_fuori_catalogo:{fuori[0]}", None

    fallimenti = coherence.validate_envelope_coherence(
        envelope["operations"], state=stato_iniziale)
    if fallimenti:
        codice = getattr(fallimenti[0], "code", "incoerente")
        return f"coerenza:{codice}", None

    try:
        operazioni = completion.fill_inferred_directions(
            envelope["operations"], catalogo.tipi)
        partenza = stato_iniziale or state_module.empty_state()
        esito = applicator.apply(partenza, operazioni)
    except applicator.ApplicationError as errore:
        return f"applicatore:{str(errore)[:40]}", None

    fallimenti = structural.validate_state(esito.state)
    if fallimenti:
        return f"stato:{fallimenti[0].code}", None
    return None, esito.state


# ---------------------------------------------------------------------------
# §7 — Il forno, i filtri e la selezione
# ---------------------------------------------------------------------------

def _normalizza(testo: str) -> str:
    piatto = unicodedata.normalize("NFKD", testo)
    return "".join(c for c in piatto if not unicodedata.combining(c)).lower()


def _cinque_grammi(testo: str) -> set[str]:
    parole = re.findall(r"\w+", _normalizza(testo))
    return {" ".join(parole[i:i + 5]) for i in range(max(1, len(parole) - 4))}


def _lunghezza_stimata(catalogo: dict, frase: str, envelope: dict,
                       stato: dict | None) -> int:
    """I gettoni dell'esempio intero, nella sua forma piu' lunga."""
    caratteri = len(SISTEMA_LUNGO) + len(frase) + len(
        json.dumps(catalogo, ensure_ascii=False, separators=(",", ":")))
    if stato:
        caratteri += len(json.dumps(stato, ensure_ascii=False,
                                    separators=(",", ":")))
    caratteri += len(json.dumps(envelope, ensure_ascii=False,
                                separators=(",", ":")))
    return int(caratteri / CARATTERI_PER_TOKEN)


def genera(entita: list[Entita], quanti: int, seme: int,
           scarti: Counter) -> list[Esempio]:
    rng = random.Random(seme)
    esempi: list[Esempio] = []
    # Le quote di `ai/18` §5. I raffinamenti sono il 10%, e sono la famiglia che
    # nessuna misura vede: la batteria apre una conversazione nuova per ogni frase.
    pesi = {"semplice": 0.30, "tempo": 0.15, "aggregazione": 0.13,
            "presentazione": 0.17, "raffinamento": 0.10, "rifiuto": 0.15}
    famiglie = list(pesi)
    probabilita = [pesi[f] for f in famiglie]

    tentativi = 0
    while len(esempi) < quanti and tentativi < quanti * 6:
        tentativi += 1
        entita_scelta = rng.choice(entita)
        famiglia = rng.choices(famiglie, probabilita)[0]

        if famiglia == "raffinamento":
            esempio = genera_raffinamento(entita_scelta, rng, scarti)
            if esempio is not None:
                esempi.append(esempio)
            continue

        intento = genera_intento(entita_scelta, famiglia, rng)
        if intento is None:
            scarti["intento_non_costruibile"] += 1
            continue
        envelope = envelope_di(intento, rng)
        motivo, _ = valida(envelope, intento.catalogo)
        if motivo:
            scarti[motivo.split(":")[0]] += 1
            continue
        frase = verbalizza(intento, envelope, rng)

        # La forma lunga del `prompt` e' il caso peggiore: se ci sta quella, ci sta
        # anche la corta. Si misura sul peggiore perche' la quota delle due forme si
        # sorteggia al momento di scrivere, e un esempio non puo' stare nella
        # finestra solo a volte.
        lunghezza = _lunghezza_stimata(intento.catalogo.payload(), frase, envelope,
                                       stato=None)
        if lunghezza > LUNGHEZZA_MASSIMA:
            scarti["troppo_lungo"] += 1
            continue

        esempi.append(Esempio(
            entita=entita_scelta.chiave,
            applicazione=entita_scelta.applicazione,
            famiglia=famiglia,
            lingua=intento.catalogo.lingua,
            frase=frase,
            catalogo=intento.catalogo.payload(),
            envelope=envelope,
            celle=firma(intento, envelope),
            modello_frase=f"{famiglia}:{len(intento.condizioni)}:"
                          f"{bool(intento.gruppi)}:{bool(intento.ordine)}",
        ))
    return esempi


def filtra(esempi: list[Esempio], scarti: Counter, *, tetto: int) -> list[Esempio]:
    """Doppioni esatti, doppioni vicini dentro la stessa firma, tetto per modello."""
    visti_esatti: set[tuple[str, str]] = set()
    grammi_per_firma: dict[tuple, list[set[str]]] = defaultdict(list)
    per_modello: Counter = Counter()
    tenuti: list[Esempio] = []

    for esempio in esempi:
        chiave = (esempio.frase, json.dumps(esempio.catalogo, sort_keys=True))
        if chiave in visti_esatti:
            scarti["doppione_esatto"] += 1
            continue
        visti_esatti.add(chiave)

        grammi = _cinque_grammi(esempio.frase)
        vicino = False
        for altro in grammi_per_firma[esempio.celle]:
            unione = grammi | altro
            if unione and len(grammi & altro) / len(unione) > 0.9:
                vicino = True
                break
        if vicino:
            scarti["doppione_vicino"] += 1
            continue
        grammi_per_firma[esempio.celle].append(grammi)

        modello = (esempio.modello_frase, esempio.entita)
        if per_modello[modello] >= tetto:
            scarti["tetto_modello_frase"] += 1
            continue
        per_modello[modello] += 1
        tenuti.append(esempio)

    return tenuti


#: Le classi di simbolo su cui **D143** pretende almeno cinquanta esempi. Un simbolo
#: visto tre volte e' un simbolo non imparato, e sara' quello che il modello sbagliera'
#: in servizio.
CLASSI_CON_MINIMO = ("op", "tempo", "kind", "aggregazione", "nota_portata",
                     "predicato")

MINIMO_PER_SIMBOLO = 50


def _ripiana(scelti: list[Esempio], rimasti: list[Esempio], coperte_conta: Counter,
             per_entita: Counter, *, bersaglio: int, massimo_per_entita: int,
             minimo: int) -> None:
    """Porta al minimo i simboli che la selezione avida ha lasciato sotto.

    **Il minimo di D143 e' una garanzia, non una misura.** Prima questo codice non
    esisteva e il rapporto si limitava a dire *«sotto 50: add_field, clear_fields,
    …»* — cioe' a constatare che la regola non era rispettata, giro dopo giro. Una
    regola che il codice dichiara e non fa rispettare e' una regola che si legge nei
    documenti e non esiste nel prodotto (§38, ancora).

    Il motivo per cui l'avidita' da sola non basta: la copertura si accontenta della
    **prima** volta che vede un simbolo, e da li' in poi quel simbolo non guadagna
    piu' niente. Coprire e imparare sono due cose diverse.
    """
    indice: dict[tuple[str, str], list[Esempio]] = defaultdict(list)
    for esempio in rimasti:
        for cella in esempio.celle:
            if cella[0] in CLASSI_CON_MINIMO:
                indice[cella].append(esempio)

    presi: set[int] = set()
    # Dal piu' scoperto: se il bersaglio finisce, che finisca sui simboli che ne
    # hanno meno bisogno.
    da_ripianare = sorted(
        (cella for cella in indice if coperte_conta[cella] < minimo),
        key=lambda cella: coperte_conta[cella])

    for cella in da_ripianare:
        for esempio in indice[cella]:
            if coperte_conta[cella] >= minimo or len(scelti) >= bersaglio:
                break
            if id(esempio) in presi:
                continue
            if per_entita[esempio.entita] >= massimo_per_entita:
                continue
            presi.add(id(esempio))
            per_entita[esempio.entita] += 1
            scelti.append(esempio)
            for altra in esempio.celle:
                coperte_conta[altra] += 1

    rimasti[:] = [e for e in rimasti if id(e) not in presi]


def seleziona(esempi: list[Esempio], bersaglio: int,
              *, tetto_entita: float = 0.015,
              minimo: int = MINIMO_PER_SIMBOLO) -> tuple[list[Esempio], int]:
    """La selezione avida di **D143**, e il punto in cui la copertura satura.

    A ogni giro entra l'esempio che copre il maggior numero di celle **ancora
    scoperte**. Quando non ce ne sono piu', il resto si riempie rispettando le quote —
    e quel momento e' un'informazione: se la copertura satura a quattromila esempi,
    gli altri seimila sono volume e non cura, e la corsa puo' essere piu' corta.
    """
    massimo_per_entita = max(1, int(bersaglio * tetto_entita))
    coperte: set[tuple[str, str]] = set()
    per_entita: Counter = Counter()
    scelti: list[Esempio] = []
    rimasti = list(esempi)
    saturazione = -1

    while len(scelti) < bersaglio and rimasti:
        migliore = None
        migliore_guadagno = -1
        for indice, esempio in enumerate(rimasti):
            if per_entita[esempio.entita] >= massimo_per_entita:
                continue
            guadagno = len(set(esempio.celle) - coperte)
            if guadagno > migliore_guadagno:
                migliore, migliore_guadagno = indice, guadagno
                if guadagno == len(esempio.celle):
                    break
        if migliore is None or migliore_guadagno == 0:
            # **Saturata: da qui l'avidita' non serve piu' e costa.** Cercare il
            # massimo fra trentamila esempi che valgono tutti zero e' una scansione
            # completa per ogni scelta — ore, per prendere lo stesso esempio che
            # prenderebbe il primo che passa. Il resto si riempie in ordine,
            # rispettando il tetto per entita', che e' cio' che la decisione dice.
            if saturazione < 0:
                saturazione = len(scelti)
            # Prima il minimo di D143, poi il riempimento: se il bersaglio si
            # esaurisce, deve esaurirsi sul volume e non sulla garanzia.
            conta: Counter = Counter()
            for gia in scelti:
                for cella in gia.celle:
                    conta[cella] += 1
            _ripiana(scelti, rimasti, conta, per_entita, bersaglio=bersaglio,
                     massimo_per_entita=massimo_per_entita, minimo=minimo)
            for esempio in rimasti:
                if len(scelti) >= bersaglio:
                    break
                if per_entita[esempio.entita] >= massimo_per_entita:
                    continue
                per_entita[esempio.entita] += 1
                scelti.append(esempio)
            break
        esempio = rimasti.pop(migliore)
        coperte |= set(esempio.celle)
        per_entita[esempio.entita] += 1
        scelti.append(esempio)

    return scelti, (saturazione if saturazione >= 0 else len(scelti))


# ---------------------------------------------------------------------------
# §8 — Le divisioni e il rapporto
# ---------------------------------------------------------------------------

def dividi(esempi: list[Esempio], tenute_fuori: set[str]
           ) -> tuple[list[Esempio], list[Esempio]]:
    """Per **applicazione intera**, mai a caso.

    Dividere a caso — l'80/20 che fa chiunque — produce un numero alto e falso: ogni
    entita' di prova avrebbe decine di fratelli in addestramento, e la domanda vera
    (*«risponde su un'applicazione installata domani?»*) resterebbe senza risposta.
    """
    dentro = [e for e in esempi if e.applicazione not in tenute_fuori]
    fuori = [e for e in esempi if e.applicazione in tenute_fuori]
    return dentro, fuori


def rapporto(scelti: list[Esempio], fuori: list[Esempio], entita: list[Entita],
             scarti: Counter, saturazione: int, generati: int,
             quota_corta: float, minimo: int) -> str:
    #: Quanti gettoni risparmia la forma corta: tutto il messaggio di sistema meno la
    #: riga che lo sostituisce.
    risparmio_corto = int((len(SISTEMA_LUNGO) - len(SISTEMA_CORTO))
                          / CARATTERI_PER_TOKEN)
    celle: Counter = Counter()
    for esempio in scelti:
        for chiave, valore in esempio.celle:
            celle[(chiave, valore)] += 1

    def elenco(chiave: str, attesi: set[str], *, esclusi: set[str] = frozenset()
               ) -> str:
        """Una riga del rapporto.

        `esclusi` sono i simboli che **non insegniamo apposta**, e sono nominati
        invece che tolti in silenzio: una riga che dicesse MANCANTI per una scelta
        deliberata insegnerebbe a chi legge a ignorare quella riga, e la riga serve
        proprio a non essere ignorata.
        """
        attesi = attesi - esclusi
        presenti = {v: celle[(chiave, v)] for (k, v) in celle if k == chiave}
        mancanti = sorted(attesi - set(presenti))
        sotto = sorted(v for v, n in presenti.items() if n < minimo)
        riga = f"    {chiave:16} {len(presenti)}/{len(attesi)}"
        if esclusi:
            riga += f"   esclusi apposta: {', '.join(sorted(esclusi))}"
        if mancanti:
            riga += f"   MANCANTI: {', '.join(mancanti)}"
        if sotto:
            riga += f"   sotto {minimo}: {', '.join(sotto)}"
        return riga

    righe = [
        "Copertura del dataset di addestramento (D143)",
        "",
        f"  generati                  {generati}",
        f"  scelti                    {len(scelti)}  (addestramento + validazione)",
        f"  tenuti fuori              {len(fuori)}  (applicazioni mai viste)",
        f"  copertura satura a        {saturazione} esempi",
        "",
        "  Cosa vuol dire, e cosa NON vuol dire.",
        "  E' il punto oltre il quale nessun esempio porta una FORMA nuova — una",
        "  combinazione di entita', simbolo, lingua e famiglia mai vista. E' un",
        "  pavimento: sotto quel numero il dataset ha buchi di forma, ed e' un",
        "  difetto. NON e' un tetto: la firma non guarda quale attributo, quante",
        "  condizioni, con che parole. Gli esempi oltre la saturazione comprano",
        "  varieta' di SUPERFICIE, che e' cio' di cui un modello di lingua vive e",
        "  che questo numero non misura apposta.",
        "",
        "  scarti",
    ]
    for motivo, quanti in scarti.most_common():
        righe.append(f"    {motivo:28} {quanti}")
    righe += [
        "",
        f"  simboli del vocabolario chiuso (minimo {minimo} per simbolo)",
        elenco("op", set(vocabulary.OPERATIONS)),
        elenco("tempo", set(vocabulary.TEMPORAL_EXPRESSIONS)),
        # `boolean` non compare fra i valori e non e' una dimenticanza: su un booleano
        # il predicato **e'** la domanda (`is_true`), e il contratto ammette il valore
        # come ridondante (§17.1). Insegnarlo ridondante sarebbe insegnare token che
        # non dicono niente, a ogni risposta, per sempre.
        elenco("kind", set(vocabulary.VALUE_KINDS), esclusi={"boolean"}),
        elenco("aggregazione", set(vocabulary.AGGREGATIONS)),
        elenco("nota_portata", set(vocabulary.SCOPE_NOTES)),
        "",
        "  ampiezza",
        f"    entita               {len({e.entita for e in scelti})} su {len(entita)}",
        f"    applicazioni         {len({e.applicazione for e in scelti})}"
        f"   tenute fuori: {len({e.applicazione for e in fuori})}",
    ]
    # **La distribuzione delle lunghezze, e non solo la media.** `ai/18` §8 fa il conto
    # dei costi su «10 000 esempi da ~4 200 gettoni»: se la lunghezza vera e' un'altra,
    # il preventivo e' un altro, e il `sequence_len` della ricetta pure.
    lunghezze = sorted(_lunghezza_stimata(e.catalogo, e.frase, e.envelope, e.stato)
                       for e in scelti) or [0]

    def percentile(quanto: float) -> int:
        return lunghezze[min(len(lunghezze) - 1, int(len(lunghezze) * quanto))]

    righe += [
        "",
        "  lunghezza dell'esempio in gettoni (stima, forma lunga del prompt)",
        f"    mediana {percentile(0.5)}   90° {percentile(0.9)}   "
        f"99° {percentile(0.99)}   massimo {lunghezze[-1]}",
        f"    il sequence_len della ricetta e' {LUNGHEZZA_MASSIMA}: "
        f"gli esempi oltre sono scartati, non troncati",
        f"    gettoni totali per passata, tutti con il prompt lungo  "
        f"{sum(lunghezze):,}",
        # Il numero su cui si fa il preventivo: il prompt corto di D142 toglie i
        # gettoni del messaggio di sistema a tre esempi su quattro, e sono la meta'
        # dell'esempio. Un costo calcolato sul caso peggiore e' un costo sbagliato di
        # un fattore due.
        f"    gettoni totali per passata, con la quota corta di D142  "
        f"{sum(lunghezze) - int(quota_corta * len(lunghezze) * risparmio_corto):,}",
    ]

    lingue = Counter(e.lingua for e in scelti)
    totale = max(1, len(scelti))
    righe.append("    lingua del catalogo  " + "  ".join(
        f"{k} {100 * v / totale:.0f}%" for k, v in sorted(lingue.items())))
    famiglie = Counter(e.famiglia for e in scelti)
    righe.append("    famiglie             " + "  ".join(
        f"{k} {100 * v / totale:.0f}%" for k, v in sorted(famiglie.items())))
    return "\n".join(righe)


def scrivi(esempi: list[Esempio], percorso: Path, *, quota_corta: float,
           seme: int) -> None:
    """Il file che Axolotl legge, con le due forme del `prompt` di **D142**."""
    rng = random.Random(seme)
    with percorso.open("w") as uscita:
        for esempio in esempi:
            corta = rng.random() < quota_corta
            sistema = SISTEMA_CORTO if corta else SISTEMA_LUNGO
            # La stessa forma, nello stesso ordine, di `prompt.user_message()`: il
            # catalogo, poi lo stato quando c'e'. Un esempio con le chiavi in un
            # ordine diverso da quello di produzione insegnerebbe a leggere un
            # messaggio che nessuno manda.
            parti = ["Catalogue:\n" + json.dumps(
                esempio.catalogo, ensure_ascii=False, separators=(",", ":"))]
            if esempio.stato:
                parti.append("Current state:\n" + json.dumps(
                    esempio.stato, ensure_ascii=False, separators=(",", ":")))
            parti.append(f"User: {esempio.frase}")
            utente = "\n".join(parti)
            # Forma canonica, byte per byte: il modello scrive come gli si insegna, e
            # ogni spazio in piu' e' un token in piu' a ogni risposta (ai/21 §3.1).
            risposta = json.dumps(esempio.envelope, ensure_ascii=False,
                                  separators=(",", ":"))
            uscita.write(json.dumps({"messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": utente},
                {"role": "assistant", "content": risposta},
            ]}, ensure_ascii=False) + "\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlante", type=Path, default=ATLANTE)
    parser.add_argument("--atlante-en", type=Path, default=ATLANTE_EN)
    parser.add_argument("--genera", type=int, default=40_000)
    parser.add_argument("--bersaglio", type=int, default=10_000)
    parser.add_argument("--tetto-modello", type=int, default=6,
                        help="quante volte lo stesso modello di frase per entita'")
    parser.add_argument("--quota-corta", type=float, default=0.75,
                        help="quota di esempi con il prompt corto (D142)")
    parser.add_argument("--tieni-fuori", default="maintenance,event,pos_restaurant,"
                                                 "website_slides,hr_recruitment,repair,"
                                                 "lunch")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data")
    parser.add_argument("--minimo", type=int, default=MINIMO_PER_SIMBOLO,
                        help="quante volte ogni simbolo deve comparire (D143). "
                             "Si abbassa solo per la prova di fumo, dove il "
                             "bersaglio e' troppo piccolo per contenerlo")
    parser.add_argument("--seme", type=int, default=20260806)
    argomenti = parser.parse_args(argv)

    entita = carica_atlante(argomenti.atlante, argomenti.atlante_en)
    print(f"atlante: {len(entita)} entita' utilizzabili", file=sys.stderr)

    scarti: Counter = Counter()
    grezzi = genera(entita, argomenti.genera, argomenti.seme, scarti)
    print(f"generati: {len(grezzi)}", file=sys.stderr)

    filtrati = filtra(grezzi, scarti, tetto=argomenti.tetto_modello)
    print(f"dopo i filtri: {len(filtrati)}", file=sys.stderr)

    tenute_fuori = {a.strip() for a in argomenti.tieni_fuori.split(",") if a.strip()}
    dentro, fuori = dividi(filtrati, tenute_fuori)

    scelti, saturazione = seleziona(dentro, argomenti.bersaglio,
                                    minimo=argomenti.minimo)
    print(f"scelti: {len(scelti)}  (satura a {saturazione})", file=sys.stderr)

    argomenti.out.mkdir(parents=True, exist_ok=True)
    taglio = max(1, int(len(scelti) * 0.95))
    scrivi(scelti[:taglio], argomenti.out / "aida_train.jsonl",
           quota_corta=argomenti.quota_corta, seme=argomenti.seme)
    scrivi(scelti[taglio:], argomenti.out / "aida_val.jsonl",
           quota_corta=argomenti.quota_corta, seme=argomenti.seme + 1)
    scrivi(fuori, argomenti.out / "aida_test_mai_viste.jsonl",
           quota_corta=argomenti.quota_corta, seme=argomenti.seme + 2)

    testo = rapporto(scelti, fuori, entita, scarti, saturazione, len(grezzi),
                     argomenti.quota_corta, argomenti.minimo)
    (argomenti.out / "copertura.txt").write_text(testo + "\n")
    print("\n" + testo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
