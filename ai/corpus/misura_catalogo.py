#!/usr/bin/env python3
"""Misura dizionario e catalogo sul corpus fondativo — criteri della parte 3.

    python3 ai/corpus/misura_catalogo.py             # rapporto
    python3 ai/corpus/misura_catalogo.py --taratura  # griglia soglia/margine
    python3 ai/corpus/misura_catalogo.py --dettagli  # code di arricchimento

Verifica i tre criteri di completamento della parte 3
(`ai/12-piano-implementazione.md`):

1. **copertura misurabile sul corpus fondativo** — scomposta in entita' e attributi
   (D34, `06` §6.3);
2. **percorso rapido di Fase A funzionante** — quota risolta senza chiamare il
   modello, e determinazioni sbagliate (D33, `06` §5.5, §6.4);
3. **budget derivato dalla finestra di contesto** — D79.

Niente modello, niente rete, niente ORM: dizionario e catalogo sono zona pura, e la
piattaforma entra solo come descrittori di attributo, che qui vengono dal catalogo
del generatore anziche' dall'introspezione.

## Che cosa questa misura non e'

Non e' accuratezza. `07` §5.4 e RC3 insistono che le due si leggono insieme: un'87%
di accuratezza con il 92% di copertura descrive una situazione completamente diversa
da un 87% con il 99,5%, e nella prima il margine di miglioramento non e' nel modello.
Qui c'e' solo la copertura, perche' senza modello l'accuratezza non e' misurabile —
ed e' esattamente il punto della parte 2 e della parte 3: tutto cio' che si puo'
verificare senza il modello, verificato prima di introdurlo.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO_ROOT = QUI.parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(QUI))

from pure.bootstrap import install  # noqa: E402

install("nli_semantics")

from genera_corpus import CATALOGO  # noqa: E402
from nli_semantics.catalogue import build, coverage, exposure, phases  # noqa: E402
from nli_semantics.catalogue.exposure import Attribute  # noqa: E402
from nli_semantics.dictionary.store import Dictionary  # noqa: E402
from riferimenti import (  # noqa: E402
    ATTRIBUTI,
    CATEGORIE,
    ENTITA,
    riferimento_attributo,
    riferimento_categoria,
    riferimento_entita,
)

CORPUS = QUI / "corpus_fondativo.jsonl"
LESSICO = QUI / "lessico_l1.json"

#: Tolleranza sulle determinazioni sbagliate di Fase A. **Parametro dichiarato, non
#: costante**: e' l'indicatore piu' importante del percorso rapido, perche' quando
#: sbaglia non produce un errore — produce un'entita' diversa e plausibile.
#:
#: L'1% e' il valore iniziale, da ritarare. Le determinazioni sbagliate che restano
#: hanno tutte la stessa forma: la testa del sintagma e' danneggiata da un refuso
#: (*"fatuere"*, due edit da *fatture*) e resta a corrispondere un modificatore che
#: punta a un'altra entita' (*"per cliente"* -> `clienti`). L'esito corretto sarebbe
#: nessun candidato, quindi Fase B. Il rimedio e' un'analisi della testa del
#: sintagma, che e' lavoro vero: §3.9 dice di farlo quando i dati lo chiedono, e
#: questa misura e' il dato che lo chiedera'.
TOLLERANZA_DETERMINAZIONI_SBAGLIATE = 0.01

#: Le entita' che il corpus usa. Il dizionario ne conosce di piu' — l'indice dei
#: termini le contiene tutte — ma la copertura si misura su cio' che i casi nominano.
ENTITA_DEL_CORPUS = frozenset(riferimento_entita(m) for m in CATALOGO)


# --- Costruzione del dizionario dal lessico ----------------------------------

def costruisci_dizionario(lessico: dict) -> Dictionary:
    """Un dizionario a due livelli dal lessico del corpus.

    **L0** sono le denominazioni derivate dai sorgenti: qui gli slug semantici di
    `riferimenti.py`, che nella parte 3 completa arriveranno dall'introspezione dei
    metadati (D84). **L1** sono i sinonimi di dominio del lessico curato, ed e' il
    livello che fa la differenza in Fase A: *"insoluti"* per le fatture scadute non
    esiste in nessun sorgente Odoo.
    """
    voci: list[dict] = []

    # T1 — entita'. L0 porta lo slug, L1 il gergo e le abbreviazioni.
    abbreviazioni = (lessico.get("fenomeni_linguistici") or {}).get("abbreviazioni") or {}
    for modello, slug in ENTITA.items():
        voci.append({"type": "T1", "level": "L0", "ref": slug,
                     "terms": [slug.replace("_", " ")]})
        gergo = list((lessico["entita"].get(modello) or {}).get("termini") or [])
        # Le forme abbreviate sono **termini**, non un caso da gestire nel
        # confronto. La prima misura lo ha mostrato: la perturbazione abbrevia la
        # testa del sintagma — *"fatture cliente"* -> *"fatt. cliente"* — il termine
        # a due parole non corrisponde piu', e resta a corrispondere il solo
        # modificatore *cliente*, che punta a un'altra entita'. Sette
        # determinazioni sbagliate su 696, tutte di questa forma.
        #
        # La risposta di §7.3 e' arricchire il dizionario anziche' ampliare la
        # grammatica: un'abbreviazione che gli utenti usano e' un sinonimo, e un
        # sinonimo e' vocabolario L1 — additivo, per cliente, senza toccare il
        # confronto.
        abbreviati = []
        for termine in gergo:
            variante = termine
            for pieno, breve in abbreviazioni.items():
                if pieno in variante:
                    variante = variante.replace(pieno, breve)
            if variante != termine:
                abbreviati.append(variante)
        if gergo or abbreviati:
            voci.append({"type": "T1", "level": "L1", "ref": slug,
                         "terms": gergo + abbreviati})

    # T1 — attributi, per ogni entita' che li espone.
    for modello, spec in CATALOGO.items():
        for campo in spec["campi"] + spec["raggruppabili"] + spec["temporali"]:
            if campo not in ATTRIBUTI:
                continue
            ref = riferimento_attributo(modello, campo)
            termini = (lessico["attributi"].get(campo) or {}).get("nominali") or []
            voci.append({"type": "T1", "level": "L0", "ref": ref,
                         "terms": [ATTRIBUTI[campo].replace("_", " ")]})
            if termini:
                voci.append({"type": "T1", "level": "L1", "ref": ref,
                             "terms": list(termini)})

    # T5 — categorie, con la condizione tipizzata. I campi implicati si derivano
    # (V-D87-1), quindi non compaiono qui.
    for modello, spec in CATALOGO.items():
        for chiave in spec["categorie"]:
            voce = lessico["categorie"].get(chiave) or {}
            condizione = voce.get("condizione_tipizzata")
            if not condizione:
                continue
            termini = (list(voce.get("termini_inv") or [])
                       + list(voce.get("termini_m") or [])
                       + list(voce.get("termini_f") or []))
            voci.append({
                "type": "T5", "level": "L1", "version": "1",
                "ref": riferimento_categoria(modello, chiave),
                "entity": riferimento_entita(modello),
                "terms": termini, "condition": condizione,
            })

    # T3 — risolutori di vaghezza, tipizzati (D59).
    voci.append({"type": "T3", "level": "L1", "version": "1", "name": "approx_relative",
                 "rule": {"kind": "relative_percent", "percent": 10}})
    voci.append({"type": "T3", "level": "L1", "version": "1", "name": "recent_orders",
                 "rule": {"kind": "last_n_days", "days": 30}})

    return Dictionary.build(voci)


def descrittori(modello: str) -> list[Attribute]:
    """I descrittori di attributo dell'entita'.

    Nella parte 3 completa arrivano dall'introspezione; qui dal catalogo del
    generatore, che e' l'unica fonte disponibile senza un'installazione. Sono
    marcati come presenti nelle viste predefinite perche' e' cio' che sono: il
    generatore li ha scelti proprio perche' un utente li nominerebbe.
    """
    spec = CATALOGO[modello]
    nomi = dict.fromkeys(spec["campi"] + spec["raggruppabili"] + spec["temporali"])
    esposti = [
        Attribute(name=ATTRIBUTI[campo], label=ATTRIBUTI[campo].replace("_", " ").title(),
                  type=_tipo(campo), in_default_views=True)
        for campo in nomi if campo in ATTRIBUTI
    ]
    # Rumore che le regole di §5.3 devono togliere: se non lo togliessero, la
    # dimensione del catalogo crescerebbe e non lo sapremmo da questa misura.
    esposti += [
        Attribute("create_uid", "Creato da", "many2one", is_system=True),
        Attribute("write_date", "Ultima modifica", "datetime", is_system=True),
        Attribute("message_ids", "Messaggi", "one2many", is_technical_mixin=True),
        Attribute("activity_state", "Stato attivita", "selection",
                  is_technical_mixin=True),
        Attribute("margine_stimato", "Margine stimato", "float",
                  stored=False, searchable=False),
        Attribute("x_studio_char_1", "x_studio_char_1", "char"),
    ]
    return esposti


def _tipo(campo: str) -> str:
    if campo.endswith("_id"):
        return "many2one"
    if campo in ("state", "payment_state", "invoice_status", "delivery_status"):
        return "selection"
    if "date" in campo:
        return "date"
    if any(parte in campo for parte in ("amount", "revenue", "qty")):
        return "float"
    return "char"


# --- Misura ------------------------------------------------------------------

class Misura:
    def __init__(self) -> None:
        self.copertura = coverage.Report()
        self.fase_a = Counter()
        self.determinazioni_sbagliate: list[tuple[str, str, str]] = []
        self.dimensioni: list[int] = []
        self.rifiuti_budget = 0
        self.categorie_escluse: Counter = Counter()


def misura(
    casi: list[dict],
    dizionario: Dictionary,
    *,
    threshold: float,
    margin: float,
    context_window: int,
    readable: frozenset[str] | None = None,
) -> Misura:
    esito = Misura()
    indice = dizionario.term_index()

    for caso in casi:
        modello = (caso.get("etichette") or {}).get("entita")
        atteso = riferimento_entita(modello) if modello else None

        # Fase A si applica **solo quando l'entita' non e' nota**: primo turno o
        # dopo `reset` (§5.5). Un raffinamento ha gia' il proprio `target` nello
        # stato, e farlo passare per il percorso rapido non e' solo inutile: e'
        # sbagliato, e la prima misura lo ha mostrato. *"Ordina per cliente"* fa
        # corrispondere il verbo *ordina* al termine dell'entita' *ordini* —
        # entrambi hanno forma base `ordin` — e produceva 116 determinazioni
        # sbagliate su richieste che non chiedevano affatto un'entita'.
        if caso.get("stato_partenza") is None:
            risultato = phases.determine_entity(
                caso["testo"], indice, entity_refs=ENTITA_DEL_CORPUS,
                threshold=threshold, margin=margin,
            )
            esito.fase_a[risultato.outcome] += 1
            if risultato.resolved and atteso and risultato.entity != atteso:
                # L'indicatore che conta piu' della quota risolta: una
                # determinazione sbagliata in Fase A e' un fraintendimento che
                # nessun errore segnala.
                esito.determinazioni_sbagliate.append(
                    (caso["id"], atteso, risultato.entity or "?"))

        if not modello or caso["esito_atteso"] != "operations":
            continue

        permessi = readable if readable is not None else _tutto_leggibile(modello)
        catalogo = build.build(
            dizionario, entity=atteso, attributes=descrittori(modello),
            readable_refs=permessi, context_window=context_window,
            entity_refs=ENTITA_DEL_CORPUS,
        )
        esito.dimensioni.append(len(catalogo))
        esito.rifiuti_budget += catalogo.refused_for_budget
        for ref, motivo in catalogo.excluded_categories:
            esito.categorie_escluse[f"{ref}: {motivo}"] += 1

        necessari = frozenset(caso.get("riferimenti_necessari") or [])
        esito.copertura.add(coverage.case_coverage(necessari, catalogo.refs))

    return esito


def _tutto_leggibile(modello: str) -> frozenset[str]:
    """Un utente senza restrizioni: legge ogni campo dell'entita' e dei suoi vicini."""
    slug = riferimento_entita(modello)
    refs = {f"{slug}.{nome}" for nome in ATTRIBUTI.values()}
    refs |= {f"{slug}.{nome}" for nome in ATTRIBUTI}
    refs |= {f"{slug}.{campo}" for campo in
             ("state", "payment_state", "invoice_status", "delivery_status",
              "qty_available", "reordering_min", "active", "invoice_date_due")}
    refs |= {f"{altro}.{nome}" for altro in ENTITA.values() for nome in ATTRIBUTI.values()}
    refs |= {"create_uid", "write_date", "message_ids", "activity_state",
             "margine_stimato", "x_studio_char_1"}
    refs |= {f"{slug}.{nome}" for nome in
             ("create_uid", "write_date", "message_ids", "activity_state",
              "margine_stimato", "x_studio_char_1")}
    return frozenset(refs)


# --- Rapporto ----------------------------------------------------------------

def rapporto(esito: Misura, *, context_window: int, dettagli: bool) -> None:
    budget = exposure.attribute_budget(context_window)
    totale_a = sum(esito.fase_a.values())

    print("Dizionario e catalogo sul corpus fondativo — parte 3\n")
    print("  criterio 2 — percorso rapido di Fase A")
    print(f"    (solo aperture: {totale_a} casi su cui l'entita' non e' nota, §5.5)")
    for outcome in (phases.RESOLVED, phases.BELOW_MARGIN, phases.BELOW_THRESHOLD,
                    phases.NO_CANDIDATE):
        quanti = esito.fase_a.get(outcome, 0)
        print(f"    {outcome:<18} {quanti:5}  {quanti / totale_a:6.1%}")
    sbagliate = len(esito.determinazioni_sbagliate)
    quota_sbagliate = sbagliate / totale_a if totale_a else 0.0
    print(f"    determinazioni sbagliate {sbagliate:5}  {quota_sbagliate:6.2%}  "
          f"(tolleranza {TOLLERANZA_DETERMINAZIONI_SBAGLIATE:.0%})")
    print()

    print("  criterio 1 — copertura (D34, soglia >= 99% sulle due componenti)")
    print(f"    complessiva        {esito.copertura.overall:6.1%}")
    print(f"    entita             {esito.copertura.entity:6.1%}")
    print(f"    attributi          {esito.copertura.attributes:6.1%}")
    print(f"    casi misurati      {esito.copertura.cases:5}")
    print(f"    soglia D34 (99%)   {'raggiunta' if esito.copertura.meets() else 'NON raggiunta'}")
    print()

    medie = sum(esito.dimensioni) / len(esito.dimensioni) if esito.dimensioni else 0
    print("  criterio 3 — budget derivato dalla finestra di contesto (D79)")
    print(f"    finestra dichiarata {context_window}")
    print(f"    budget attributi    {budget.attributes}  ({budget.reason}: {budget.detail})")
    print(f"    dimensione media del catalogo {medie:.1f} voci")
    print(f"    rifiuti per budget  {esito.rifiuti_budget}")
    print()

    if esito.categorie_escluse:
        print("  categorie escluse dal filtro sui permessi (V-D87-1)")
        for motivo, quanti in esito.categorie_escluse.most_common(5):
            print(f"    {quanti:5}  {motivo}")
        print()

    if dettagli:
        if esito.copertura.missing:
            print("  coda di arricchimento — riferimenti mancanti per frequenza (§6.4)")
            for ref, quanti in esito.copertura.missing.most_common(15):
                print(f"    {quanti:5}  {ref}")
        for caso_id, atteso, ottenuto in esito.determinazioni_sbagliate[:10]:
            print(f"    {caso_id}: atteso {atteso}, Fase A ha detto {ottenuto}")


def taratura(casi: list[dict], dizionario: Dictionary, *, context_window: int) -> None:
    """Soglia e margine scelti su misura, non su intuizione (D33).

    §5.5 chiede una soglia e un margine e non fissa i valori. La griglia mostra il
    solo compromesso che conta: **quota risolta contro determinazioni sbagliate.**
    Una quota alta con determinazioni sbagliate non nulle e' peggio di una quota
    bassa, perche' il percorso rapido non produce un errore quando sbaglia — produce
    un'entita' diversa e plausibile.
    """
    print("\n  taratura di Fase A — quota risolta contro determinazioni sbagliate\n")
    print(f"    {'soglia':>7} {'margine':>8} {'risolti':>8} {'quota':>7} "
          f"{'sbagliate':>10} {'chiarimenti':>12}")
    for threshold in (0.70, 0.90, 1.00):
        for margin in (0.00, 0.15, 0.30):
            esito = misura(casi, dizionario, threshold=threshold, margin=margin,
                           context_window=context_window)
            totale = sum(esito.fase_a.values())
            risolti = esito.fase_a.get(phases.RESOLVED, 0)
            print(f"    {threshold:7.2f} {margin:8.2f} {risolti:8} "
                  f"{risolti / totale:6.1%} {len(esito.determinazioni_sbagliate):10} "
                  f"{esito.fase_a.get(phases.BELOW_MARGIN, 0):12}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dettagli", action="store_true")
    parser.add_argument("--taratura", action="store_true")
    parser.add_argument("--finestra", type=int, default=128_000,
                        help="finestra di contesto dichiarata dal profilo (D78)")
    parser.add_argument("--corpus", default=str(CORPUS))
    argomenti = parser.parse_args(argv)

    casi = [json.loads(riga) for riga in Path(argomenti.corpus).read_text(
        encoding="utf-8").splitlines() if riga.strip()]
    lessico = json.loads(LESSICO.read_text(encoding="utf-8"))
    dizionario = costruisci_dizionario(lessico)

    if dizionario.problems:
        print("voci di dizionario respinte:")
        for problema in dizionario.problems[:10]:
            print(f"  {problema}")
        print()

    esito = misura(casi, dizionario, threshold=phases.DEFAULT_THRESHOLD,
                   margin=phases.DEFAULT_MARGIN, context_window=argomenti.finestra)
    rapporto(esito, context_window=argomenti.finestra, dettagli=argomenti.dettagli)

    if argomenti.taratura:
        taratura(casi, dizionario, context_window=argomenti.finestra)

    totale_aperture = sum(esito.fase_a.values())
    quota_sbagliate = (len(esito.determinazioni_sbagliate) / totale_aperture
                       if totale_aperture else 0.0)
    fallito = (
        quota_sbagliate > TOLLERANZA_DETERMINAZIONI_SBAGLIATE
        or not esito.copertura.meets()
        or bool(dizionario.problems)
    )
    print("\n" + ("FALLITO" if fallito else "OK"))
    return 1 if fallito else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
