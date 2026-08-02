#!/usr/bin/env python3
"""Accuratezza dell'interpretazione sul corpus fondativo — criterio della parte 5.

    python3 ai/corpus/misura_accuratezza.py --casi 40
    python3 ai/corpus/misura_accuratezza.py --casi 40 --profilo qwen2.5:latest

**La prima volta che il sistema vede un modello.** Tutto quello che viene prima —
contratto, applicatore, forma canonica, dizionario, catalogo — e' stato costruito e
misurato senza; questo strumento chiude il cerchio misurando cio' che senza modello
non e' misurabile.

## Che cosa misura, e con quale disciplina

L'accuratezza e' **scomposta per sezione** (§14.5, **D44**), non complessiva. La
ragione e' quantitativa: con la sola soglia complessiva, entita' al 99% e
raggruppamenti al 62% superano il cancello, e chi usa i raggruppamenti sta facendo
analisi — e' l'utente che ha piu' bisogno del prodotto.

Si legge **insieme alla copertura** (`07` §5.4, RC3): un 87% di accuratezza con il 92%
di copertura descrive una situazione diversa da un 87% con il 99,5%, e nella prima il
margine di miglioramento non e' nel modello. La copertura la misura
`misura_catalogo.py`; questo strumento la richiama nel rapporto perche' riportarne una
senza l'altra invita al lavoro sbagliato.

## Che cosa **non** e'

Non e' il cancello di Fase 2. **D86**: il corpus fondativo e' sintetico, quindi non e'
sigillabile — chi ha scritto il generatore ne conosce la distribuzione — e **D42** e
**D49** restano insoddisfatte. Questo numero dice se il sistema funziona, non se e'
pronto a scrivere sui dati.

L'istante di riferimento e' **fissato** (§9.2): senza, l'atteso di un caso che contiene
`current_month` cambierebbe col calendario e i confronti fra rilasci non
significherebbero nulla.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO_ROOT = QUI.parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(QUI))

from pure.bootstrap import install, install_odoo_alias  # noqa: E402

install("nli_core")
install("nli_semantics")
install("nli_engine")
install_odoo_alias()

from misura_catalogo import (  # noqa: E402
    ENTITA_DEL_CORPUS, costruisci_dizionario, descrittori, _tutto_leggibile,
)
from nli_core.application import applicator, completion  # noqa: E402
from nli_core.contract import canonical, state as state_module  # noqa: E402
from nli_core.validation import contextual  # noqa: E402
from nli_engine.adapters.base import Capabilities  # noqa: E402
from nli_engine.adapters.openai_compatible import OpenAICompatibleAdapter  # noqa: E402
from nli_engine.interpreter import interpret  # noqa: E402
from nli_semantics.catalogue import build as build_module  # noqa: E402
from nli_semantics.dictionary import grounding  # noqa: E402
from nli_semantics.platform_types import (  # noqa: E402
    CONTRACT_TYPE_BY_ODOO_TYPE,
)
from riferimenti import ENTITA, riferimento_entita  # noqa: E402

CORPUS = QUI / "corpus_fondativo.jsonl"
LESSICO = QUI / "lessico_l1.json"

#: Istante di riferimento fissato (§9.2). Lo stesso di `pure_tests`.
ISTANTE = datetime(2026, 7, 15, 10, 30)

#: Sezioni confrontate separatamente (§14.5). `target` per prima perche' e' la sola
#: che, sbagliata, rende tutto il resto privo di significato.
SEZIONI = ("target", "filter", "fields", "group_by", "measures", "order_by",
           "limit", "presentation")


class Accuratezza:
    def __init__(self) -> None:
        self.casi = 0
        self.esatti = 0
        self.per_sezione: Counter = Counter()
        self.esiti: Counter = Counter()
        self.esiti_attesi: Counter = Counter()
        self.riparazioni = 0
        #: Rifiuti del livello 3 per condizione nominata infondata — D105, "la
        #: condizione nominata dev'essere fondata" (registro §19.1). Con D112, "le
        #: categorie ammesse dalla generazione vincolata sono quelle nominate dalla
        #: frase, non tutte quelle del catalogo" (ai/14-ancoraggio-del-tempo.md §6,
        #: non ancora nel registro) in vigore dovrebbero restare a zero: se non lo
        #: sono, il riconoscitore che restringe e quello che verifica non danno la
        #: stessa risposta.
        self.infondate: int = 0
        self.token_prompt = 0
        self.token_risposta = 0
        self.millisecondi = 0
        self.errori: list[str] = []
        self.sbagliati: list[tuple[str, str, list[str]]] = []


def _catalogo(dizionario, modello: str):
    return build_module.build(
        dizionario, entity=riferimento_entita(modello),
        attributes=descrittori(modello),
        readable_refs=_tutto_leggibile(modello),
        context_window=32_000, entity_refs=ENTITA_DEL_CORPUS,
        # `17.5` del registro l'aveva rilevato e nessuno l'aveva applicato qui: senza
        # la traduzione, il catalogo del corpus porta i tipi di Odoo (`many2one`,
        # `selection`) invece di quelli di §8.1, e la misura eserciterebbe un catalogo
        # che l'installazione vera non produce. Con **D103** la differenza smette di
        # essere cosmetica: i predicati ammessi si derivano dal tipo.
        type_map=CONTRACT_TYPE_BY_ODOO_TYPE,
    )


def _campione(casi: list[dict], quanti: int) -> list[dict]:
    """Un campione deterministico: uno ogni N, non a caso.

    Deterministico perche' due esecuzioni devono confrontarsi fra loro: con un
    campione casuale la variazione fra due misure conterrebbe anche il campione, e
    D48 chiede di distinguere il rumore dal risultato.
    """
    utili = [c for c in casi if c["esito_atteso"] == "operations"
             and c["tipo"] == "apertura"]
    if quanti >= len(utili):
        return utili
    passo = len(utili) / quanti
    return [utili[int(indice * passo)] for indice in range(quanti)]


def misura(casi: list[dict], dizionario, adapter, *, verboso: bool) -> Accuratezza:
    esito = Accuratezza()

    for caso in casi:
        modello = caso["etichette"]["entita"]
        atteso = caso["stato_atteso"]
        catalogo = _catalogo(dizionario, modello)

        partito = time.monotonic()
        interpretazione = interpret(adapter, utterance=caso["testo"],
                                    catalogue=catalogo, state=None)
        esito.millisecondi += int((time.monotonic() - partito) * 1000)
        esito.casi += 1
        esito.riparazioni += interpretazione.repairs
        for risposta in interpretazione.replies:
            esito.token_prompt += risposta.prompt_tokens
            esito.token_risposta += risposta.completion_tokens

        esito.esiti[interpretazione.outcome] += 1
        esito.esiti_attesi[caso["esito_atteso"]] += 1

        if interpretazione.outcome != "operations":
            esito.sbagliati.append(
                (caso["id"], caso["testo"][:60], [f"esito {interpretazione.outcome}"]))
            continue

        try:
            # D99: la direzione che l'utente non ha nominato la deriva il sistema dal
            # tipo dell'attributo, non il modello (P4). Senza questo passo la misura
            # confronterebbe uno stato *prima* del completamento con un atteso che lo
            # ha gia' subito, e penalizzerebbe il modello per una nostra omissione.
            operazioni = completion.fill_inferred_directions(
                interpretazione.envelope["operations"],
                {attributo.ref: attributo.type for attributo in catalogo.attributes})
            prodotto = applicator.apply(
                state_module.empty_state(), operazioni).state
        except applicator.ApplicationError as errore:
            esito.errori.append(f"{caso['id']}: {errore}")
            continue

        # Livello 3 (D105): interpret() e l'applicatore fermano ai livelli 1-2 e alla
        # coerenza, quindi senza questa chiamata il metro non aveva mai visto il
        # controllo di fondatezza — e il punteggio non aveva mai visto i suoi
        # fallimenti. Si conta solo `ungrounded_category`: gli altri codici sono
        # livelli diversi, e mescolarli in un numero solo confonderebbe cose diverse.
        fallimenti = contextual.validate(
            prodotto, known_refs=catalogo.refs,
            types={attributo.ref: attributo.type for attributo in catalogo.attributes},
            mentions=grounding.mentions_of(dizionario))
        if any(fallimento.code == "ungrounded_category" for fallimento in fallimenti):
            esito.infondate += 1

        confronto = canonical.section_comparison(atteso, prodotto)
        for sezione in SEZIONI:
            if confronto.get(sezione, True):
                esito.per_sezione[sezione] += 1
        if canonical.identical(atteso, prodotto):
            esito.esatti += 1
        else:
            diverse = [s for s in SEZIONI if not confronto.get(s, True)]
            esito.sbagliati.append((caso["id"], caso["testo"][:60], diverse))
            if verboso:
                print(f"  {caso['id']} {caso['testo'][:60]!r} -> sezioni {diverse}")

    return esito


def rapporto(esito: Accuratezza, *, modello: str) -> None:
    print(f"\nAccuratezza dell'interpretazione — parte 5\n")
    print(f"  modello                {modello}")
    print(f"  casi                   {esito.casi}")
    if not esito.casi:
        return
    print(f"  accuratezza complessiva {esito.esatti / esito.casi:6.1%}  "
          f"({esito.esatti}/{esito.casi})")
    print()
    print("  per sezione (D44: soglia >= 85% su ciascuna)")
    for sezione in SEZIONI:
        quota = esito.per_sezione[sezione] / esito.casi
        marca = " " if quota >= 0.85 else " <-- sotto soglia"
        print(f"    {sezione:<14} {quota:6.1%}{marca}")
    print()
    print("  esiti prodotti")
    for nome, quanti in esito.esiti.most_common():
        print(f"    {nome:<16} {quanti:5}  {quanti / esito.casi:6.1%}")
    print()
    print(f"  riparazioni (D15)      {esito.riparazioni}  "
          f"{esito.riparazioni / esito.casi:.1%} dei casi")
    print(f"  condizioni infondate    {esito.infondate}  "
          f"{esito.infondate / esito.casi:.1%} dei casi  (D105, atteso 0 con D112)")
    print(f"  token prompt/risposta  {esito.token_prompt} / {esito.token_risposta}")
    print(f"  latenza media          {esito.millisecondi // esito.casi} ms")
    if esito.errori:
        print(f"\n  errori di applicazione: {len(esito.errori)}")
        for riga in esito.errori[:5]:
            print(f"    {riga}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casi", type=int, default=40)
    parser.add_argument("--profilo", default="qwen2.5:latest")
    parser.add_argument("--endpoint", default="http://localhost:11434/v1")
    parser.add_argument("--finestra", type=int, default=32_000)
    parser.add_argument("--vincolata", action="store_true",
                        help="il profilo dichiara la generazione vincolata (D78)")
    parser.add_argument("--ragionamento", default=None,
                        choices=("none", "minimal", "low", "medium", "high"),
                        help="sforzo di ragionamento dichiarato (D98). Assente, la "
                             "chiave non viaggia: un fornitore che non la conosce "
                             "risponde 400")
    parser.add_argument("--attesa", type=int, default=60,
                        help="secondi concessi a una risposta. Il valore d'esercizio "
                             "e' 60 (D5); su un portatile un modello locale lo supera "
                             "e la misura vuole dirlo, non fallire")
    parser.add_argument("--verboso", action="store_true")
    argomenti = parser.parse_args(argv)

    casi = [json.loads(riga) for riga in CORPUS.read_text(encoding="utf-8").splitlines()
            if riga.strip()]
    dizionario = costruisci_dizionario(json.loads(LESSICO.read_text(encoding="utf-8")))
    campione = _campione(casi, argomenti.casi)

    adapter = OpenAICompatibleAdapter(
        endpoint=argomenti.endpoint, model=argomenti.profilo,
        capabilities=Capabilities(context_window=argomenti.finestra,
                                  constrained_generation=argomenti.vincolata,
                                  reasoning_effort=argomenti.ragionamento),
        timeout=argomenti.attesa,
    )

    print(f"interrogo {argomenti.profilo} su {len(campione)} casi di apertura...")
    esito = misura(campione, dizionario, adapter, verboso=argomenti.verboso)
    rapporto(esito, modello=argomenti.profilo)

    print("\n  Da leggere con la copertura (07 §5.4): "
          "python3 ai/corpus/misura_catalogo.py")
    print("  Non e' il cancello di Fase 2: il corpus e' sintetico e non sigillabile "
          "(D86), quindi D42 e D49 restano insoddisfatte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
