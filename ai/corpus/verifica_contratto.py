#!/usr/bin/env python3
"""Esegue il corpus fondativo contro il contratto della parte 2.

    python3 ai/corpus/verifica_contratto.py            # rapporto sintetico
    python3 ai/corpus/verifica_contratto.py --dettagli # elenca i primi errori

Verifica i tre criteri di completamento della parte 2
(`ai/12-piano-implementazione.md`):

1. i casi `operations` producono lo stato atteso;
2. i casi incoerenti sono respinti;
3. la forma canonica e' stabile su permutazioni.

Niente modello linguistico, niente rete, niente ORM: solo la zona pura.

## Nessun adattatore

C'era, e ora non serve: dal 28/07/2026 il generatore emette la forma normativa
(**D92**). L'adattatore che traduceva il dialetto del corpus e' stato rimosso
anziche' mantenuto, perche' un adattatore fra corpus e contratto e' un secondo
contratto da tenere allineato per dieci anni — e il primo che divergerebbe in
silenzio.

## Che cosa questo confronto prova davvero

Lo `stato_atteso` dei raffinamenti e' calcolato dal generatore **trasformando il
proprio intento**, non applicando l'Applicatore del prodotto. Le due
implementazioni della semantica di applicazione sono indipendenti, e questo
strumento le mette una contro l'altra. Se lo stato atteso venisse dall'Applicatore
il confronto sarebbe una tautologia, e 504 casi darebbero l'impressione di
verificare qualcosa senza verificare nulla.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = Path(__file__).resolve().parent / "corpus_fondativo.jsonl"


sys.path.insert(0, str(REPO_ROOT / "tools"))
from pure.bootstrap import install  # noqa: E402

install("nli_core")

from nli_core.application import applicator  # noqa: E402
from nli_core.contract import canonical, state as state_module  # noqa: E402
from nli_core.validation import coherence, structural  # noqa: E402

#: Un riferimento semantico e' `entita` oppure `entita.attributo`, con al piu' due
#: salti di relazione (§7.3). Un nome tecnico Odoo (`sale.order.amount_total`,
#: `partner_id`) non ha questa forma, ed e' cio' che il controllo intercetta: C2 e
#: §5.10 escludono i nomi di modelli e campi dallo stato.
FORMA_RIFERIMENTO = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,3}$")
SOSPETTI_TECNICI = ("_id", "_ids")


class Esito:
    def __init__(self) -> None:
        self.verificati = 0
        self.errori: list[str] = []
        self.stati_validati = 0
        self.permutazioni = 0
        self.round_trip = 0
        self.raffinamenti = 0
        self.riferimenti_controllati = 0

    def errore(self, caso_id: str, messaggio: str) -> None:
        self.errori.append(f"{caso_id}: {messaggio}")


# --- Verifiche ---------------------------------------------------------------

def _valida(stato: dict, caso_id: str, dove: str, esito: Esito) -> bool:
    fallimenti = (
        structural.validate_state(stato)
        + coherence.validate_coherence(stato)
        + coherence.validate_cost(stato)
    )
    if fallimenti:
        esito.errore(caso_id, f"{dove}: " + "; ".join(str(f) for f in fallimenti[:3]))
        return False
    esito.stati_validati += 1
    return True


def _stabilita_canonica(stato: dict, caso_id: str, esito: Esito) -> None:
    """Criterio 3: la forma canonica non dipende dall'ordine delle condizioni."""
    riferimento = canonical.canonical_json(stato)
    for variante in canonical.permutations_of_conditions(stato):
        esito.permutazioni += 1
        if canonical.canonical_json(variante) != riferimento:
            esito.errore(caso_id, "forma canonica instabile su permutazione")
            return


def _riferimenti_semantici(caso: dict, esito: Esito) -> None:
    """I riferimenti dello stato sono semantici, dichiarati e risolvibili.

    Tre proprieta' in una: la forma non e' un nome tecnico (C2), l'elenco
    `riferimenti_necessari` copre cio' che lo stato nomina — e' quello che la
    misura di copertura di **D34** usera' nella parte 3 — e ogni riferimento ha un
    binding tecnico da confrontare con la risoluzione del dizionario.
    """
    dichiarati = set(caso.get("riferimenti_necessari") or [])
    binding = caso.get("binding_tecnico") or {}
    usati: set[str] = set()
    for stato in (caso.get("stato_partenza"), caso.get("stato_atteso")):
        if stato:
            usati |= set(state_module.references(stato))

    for riferimento in sorted(usati):
        esito.riferimenti_controllati += 1
        if not FORMA_RIFERIMENTO.match(riferimento):
            esito.errore(caso["id"], f"riferimento non semantico: {riferimento!r}")
        if any(riferimento.endswith(coda) for coda in SOSPETTI_TECNICI):
            esito.errore(caso["id"], f"riferimento con forma tecnica: {riferimento!r}")

    mancanti = sorted(usati - dichiarati)
    if mancanti:
        esito.errore(caso["id"], f"riferimenti usati e non dichiarati: {mancanti}")
    senza_binding = sorted(usati - binding.keys())
    if senza_binding:
        esito.errore(caso["id"], f"riferimenti senza binding tecnico: {senza_binding}")


def _operazioni_valide(caso: dict, esito: Esito) -> bool:
    busta = {
        "dsl_version": "1.0", "outcome": "operations",
        "operations": caso["operazioni_attese"],
    }
    fallimenti = structural.validate_envelope(busta) + \
        coherence.validate_envelope_coherence(
            caso["operazioni_attese"], state=caso["stato_partenza"])
    if fallimenti:
        esito.errore(caso["id"], "busta: " + "; ".join(str(f) for f in fallimenti[:3]))
        return False
    return True


def sintetizza_operazioni(stato: dict) -> list[dict]:
    """Le operazioni che ricostruiscono `stato` dallo stato vuoto.

    Serve per le aperture, che portano lo stato atteso ma non le operazioni:
    senza di esse l'Applicatore non avrebbe nulla da applicare, e il criterio
    *"i casi producono lo stato atteso"* non sarebbe verificabile su di esse.
    """
    operazioni: list[dict] = [
        {"op": "set_target", "ref": stato["target"]["ref"],
         "provenance": {"text": "(corpus)"}}
    ]
    for condizione in state_module.conditions(stato.get("filter")):
        operazioni.append({
            "op": "add_condition", "combine": "all",
            "condition": {k: v for k, v in condizione.items()
                          if k not in ("id", "origin", "rule", "provenance")},
            "provenance": {"text": "(corpus)"},
        })
    if "fields" in stato:
        operazioni.append({
            "op": "set_fields", "refs": [v["ref"] for v in stato["fields"]],
            "provenance": {"text": "(corpus)"},
        })
    for voce in stato.get("group_by", []):
        operazioni.append({"op": "add_group", "ref": voce["ref"],
                           "provenance": {"text": "(corpus)"}})
    for posizione, voce in enumerate(stato.get("order_by", [])):
        operazioni.append({
            "op": "set_order" if posizione == 0 else "add_order",
            "ref": voce["ref"], "direction": voce["direction"],
            "origin": voce.get("origin", "user"),
            "provenance": {"text": "(corpus)"},
        })
    if stato["limit"]["origin"] == "user":
        operazioni.append({"op": "set_limit", "value": stato["limit"]["value"],
                           "provenance": {"text": "(corpus)"}})
    return operazioni


def _confronta(atteso: dict, prodotto: dict, caso_id: str, dove: str,
               esito: Esito) -> bool:
    if canonical.identical(prodotto, atteso):
        return True
    sezioni = canonical.section_comparison(atteso, prodotto)
    differenti = [nome for nome, uguale in sezioni.items() if not uguale]
    esito.errore(caso_id, f"{dove}: sezioni diverse {differenti}")
    return False


def verifica_apertura(caso: dict, esito: Esito) -> None:
    atteso = caso["stato_atteso"]
    if not _valida(atteso, caso["id"], "stato_atteso", esito):
        return
    _stabilita_canonica(atteso, caso["id"], esito)
    _riferimenti_semantici(caso, esito)

    prodotto = applicator.apply(
        state_module.empty_state(), sintetizza_operazioni(atteso)).state
    if not _confronta(atteso, prodotto, caso["id"], "round-trip", esito):
        return
    esito.round_trip += 1
    esito.verificati += 1


def verifica_raffinamento(caso: dict, esito: Esito) -> None:
    partenza, atteso = caso["stato_partenza"], caso["stato_atteso"]
    if not _valida(partenza, caso["id"], "stato_partenza", esito):
        return
    if not _valida(atteso, caso["id"], "stato_atteso", esito):
        return
    _riferimenti_semantici(caso, esito)
    if not _operazioni_valide(caso, esito):
        return

    prodotto = applicator.apply(partenza, caso["operazioni_attese"]).state
    _stabilita_canonica(prodotto, caso["id"], esito)

    # Criterio 1, in forma diretta: l'Applicatore del prodotto contro la
    # trasformazione dell'intento del generatore.
    if not _confronta(atteso, prodotto, caso["id"], "applicazione", esito):
        return
    if canonical.identical(prodotto, partenza):
        esito.errore(caso["id"], "il raffinamento non ha cambiato nulla (D92)")
        return
    esito.raffinamenti += 1
    esito.verificati += 1


# --- Criterio 2: i casi incoerenti sono respinti ----------------------------

def verifica_incoerenze(base: dict) -> list[str]:
    """Muta uno stato valido del corpus e pretende che la validazione lo respinga.

    Il corpus non contiene casi incoerenti: il generatore li evita per
    costruzione. Il criterio si verifica quindi iniettando l'incoerenza, che e'
    anche il solo modo di sapere che il rifiuto funziona.
    """
    problemi: list[str] = []

    def pretendi(nome: str, fallimenti: list) -> None:
        if not fallimenti:
            problemi.append(f"non respinto: {nome}")

    foglia = {"id": "c9", "ref": "x.y", "predicate": "is_true", "origin": "user"}
    profondo = copy.deepcopy(base)
    profondo["filter"] = {"connective": "all", "conditions": [
        {"connective": "any", "conditions": [
            {"connective": "not", "conditions": [foglia]},
        ]},
    ]}
    pretendi("albero dei filtri a 4 livelli", coherence.validate_coherence(profondo))

    gruppi = copy.deepcopy(base)
    gruppi["group_by"] = [{"ref": f"x.g{i}", "origin": "user"} for i in range(4)]
    pretendi("quattro raggruppamenti", coherence.validate_coherence(gruppi))

    misure = copy.deepcopy(base)
    misure["measures"] = [{"function": "sum", "ref": "x.importo", "origin": "user"}]
    misure["group_by"] = [{"ref": "x.venditore", "origin": "user"}]
    misure["presentation"] = {"view": "list", "origin": "user"}
    pretendi("misure con vista lista e raggruppamento",
             coherence.validate_coherence(misure))

    costoso = copy.deepcopy(base)
    costoso["limit"] = {"value": 5000, "origin": "user"}
    pretendi("limite oltre il massimo assoluto", coherence.validate_cost(costoso))

    salti = copy.deepcopy(base)
    salti["fields"] = [{"ref": "x.a.b.c.d", "origin": "user"}]
    pretendi("riferimento con 3 salti di relazione", coherence.validate_cost(salti))

    pretendi("due set_limit in conflitto", coherence.validate_envelope_coherence([
        {"op": "set_limit", "value": 5}, {"op": "set_limit", "value": 10},
    ]))
    pretendi("revert_last composto", coherence.validate_envelope_coherence([
        {"op": "revert_last"}, {"op": "set_limit", "value": 5},
    ]))
    pretendi("simbolo inventato", structural.validate_envelope({
        "dsl_version": "1.0", "outcome": "operations",
        "operations": [{"op": "set_raw_domain", "ref": "x"}],
    }))
    pretendi("busta con operazioni vuote", structural.validate_envelope({
        "dsl_version": "1.0", "outcome": "operations", "operations": [],
    }))
    pretendi("stato con sezione vuota esplicita", structural.validate_state(
        {**copy.deepcopy(base), "fields": []}))
    pretendi("predicato e valore incompatibili",
             coherence.validate_envelope_coherence([{
                 "op": "add_condition", "condition": {
                     "ref": "x.importo", "predicate": "contains",
                     "value": {"kind": "number", "value": 10}},
             }]))

    return problemi


# --- Esecuzione --------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dettagli", action="store_true")
    parser.add_argument("--corpus", default=str(CORPUS))
    argomenti = parser.parse_args(argv)

    casi = [json.loads(riga) for riga in Path(argomenti.corpus).read_text(
        encoding="utf-8").splitlines() if riga.strip()]

    esito = Esito()
    per_tipo: Counter = Counter()
    primo_stato: dict | None = None

    for caso in casi:
        per_tipo[caso["tipo"]] += 1
        if caso["esito_atteso"] != "operations":
            # Chiarimento, fuori ambito e incompreso non hanno stato atteso: la
            # loro verifica appartiene all'Interprete (parte 5), non al contratto.
            continue
        if caso["tipo"] == "apertura":
            verifica_apertura(caso, esito)
            if primo_stato is None:
                primo_stato = caso["stato_atteso"]
        else:
            verifica_raffinamento(caso, esito)

    if primo_stato is None:
        print("nessun caso di apertura nel corpus")
        return 1
    problemi_incoerenza = verifica_incoerenze(primo_stato)

    # §6 di `11-corpus-fondativo.md`: soglia < 2%. Un duplicato esatto gonfia il
    # corpus senza aggiungere segnale, e la dimensione e' cio' su cui poggia la
    # soglia di rumore di D48: contarli e' l'unico modo di sapere che i 1 200 casi
    # sono 1 200 casi.
    frasi = Counter(caso["testo"] for caso in casi)
    duplicati = sum(quanti - 1 for quanti in frasi.values() if quanti > 1)
    quota_duplicati = duplicati / len(casi)

    totale = sum(1 for caso in casi if caso["esito_atteso"] == "operations")

    print("Corpus fondativo contro il contratto — parte 2\n")
    print(f"  casi nel corpus                {len(casi)}")
    for tipo, quanti in per_tipo.most_common():
        print(f"    {tipo:<26} {quanti}")
    print()
    print(f"  casi con esito 'operations'    {totale}")
    print(f"    verificati                   {esito.verificati}")
    print(f"    errori                       {len(esito.errori)}")
    print()
    print(f"  stati validati (livelli 1,2,4,5)     {esito.stati_validati}")
    print(f"  aperture: round-trip stato->op->stato {esito.round_trip}")
    print(f"  raffinamenti: applicatore vs intento  {esito.raffinamenti}")
    print(f"  permutazioni confrontate              {esito.permutazioni}")
    print(f"  riferimenti semantici controllati     {esito.riferimenti_controllati}")
    print()
    print("  criterio 2 — incoerenze respinte: "
          f"{'tutte' if not problemi_incoerenza else problemi_incoerenza}")
    print(f"  frasi duplicate                {duplicati} ({quota_duplicati:.1%}, "
          f"soglia < 2%)")

    if argomenti.dettagli:
        for riga in esito.errori[:25]:
            print(f"    {riga}")

    fallito = bool(esito.errori) or bool(problemi_incoerenza) or quota_duplicati >= 0.02
    print("\n" + ("FALLITO" if fallito else "OK"))
    return 1 if fallito else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
