"""La batteria sul campo: le frasi di `frasi.py` attraverso il prodotto vero.

Si esegue dentro la shell di Odoo, su un database vero e con il modello vero:

    ./manage.sh campo db                 # tutte le famiglie
    ./manage.sh campo db date            # una famiglia sola
    CAMPO_MAX=5 ./manage.sh campo db     # le prime cinque, per una prova rapida

**Costa tempo di modello.** Sul profilo misurato il 3 agosto 2026 un turno va dai 15
ai 145 secondi: la batteria intera e' un'ora abbondante. La famiglia sola, o `CAMPO_MAX`,
servono a questo.

## Che strada percorre

La stessa del prodotto, e non una copia: il perimetro, la finestra e l'adattatore
vengono dal **dispatcher**, cioe' dagli stessi metodi che il cron chiama. Poi ogni frase
entra in coda con `accept` — che e' l'unica porta d'ingresso — e viene eseguita da
`pipeline.run`. Non passa dal pool di thread, e non deve: il pool e' un fatto di
concorrenza, provato altrove (D27), e qui darebbe solo rumore.

**Una conversazione per frase.** Ogni caso si crea la propria interrogazione, altrimenti
il turno di prima farebbe da contesto a quello dopo — D120 e D127 sono regole giuste che
qui falserebbero la misura.

## Cosa non scrive

Niente, salvo che glielo si chieda con `CAMPO_SCRIVI=1`. Al termine la transazione viene
annullata: una misura non deve lasciare cinquanta turni in una banca dati di lavoro.
"""

import os
import time

from odoo.addons.nli_core.contract import state as state_module
from odoo.addons.nli_dispatch.runtime import pipeline as pipeline_module

# `FRASI` arriva da `frasi.py`, che `./manage.sh campo` incolla davanti a questo file
# prima di mandarlo alla shell di Odoo. Non e' un `import` perche' il contenitore
# monta `custom_addons` e non `tools`: due file sull'host, un flusso solo in ingresso.
FRASI = globals()["FRASI"]

VERDE = "\033[32m"
ROSSO = "\033[31m"
GIALLO = "\033[33m"
GRIGIO = "\033[90m"
FINE = "\033[0m"


def _catalogo_termini(catalogo):
    """Tutte le parole che il modello vede per questa entita', in minuscolo."""
    parole = set()
    for attributo in catalogo.attributes:
        parole.update(termine.casefold() for termine in attributo.terms)
    for categoria in catalogo.categories:
        parole.update(termine.casefold() for termine in categoria.terms)
    return parole


def _manca(serve, termini):
    """Le parole che la frase richiede e che il catalogo non ha.

    Il confronto e' per contenimento e non per uguaglianza: il catalogo dice
    *«Data di creazione»* e la frase chiede *«data di creazione»*, ma anche
    *«Ricavo atteso»* contro *«ricavo atteso»*. Una parola contenuta in un termine
    basta, perche' e' cosi' che il riconoscitore del dizionario lavora.
    """
    return [parola for parola in serve
            if not any(parola in termine for termine in termini)]


def _condizioni(stato):
    return list(state_module.conditions((stato or {}).get("filter")))


def _differenze(attesa, esito):
    """Le differenze fra cio' che la frase chiedeva e cio' che e' uscito."""
    atteso_esito = attesa.get("esito", "operations")
    if esito.outcome != atteso_esito:
        return [f"esito {esito.outcome} invece di {atteso_esito}"]
    if esito.outcome != "operations":
        return []

    stato = esito.state or {}
    differenze = []

    if "misure" in attesa:
        funzioni = {misura.get("function")
                    for misura in (stato.get("measures") or [])}
        if not attesa["misure"] <= funzioni:
            differenze.append(
                f"misure {sorted(funzioni) or 'nessuna'} invece di "
                f"{sorted(attesa['misure'])}")

    if "raggruppa" in attesa:
        quanti = len(stato.get("group_by") or [])
        if quanti != attesa["raggruppa"]:
            differenze.append(f"{quanti} raggruppamenti invece di {attesa['raggruppa']}")

    if "ordina" in attesa:
        quanti = len(stato.get("order_by") or [])
        if quanti != attesa["ordina"]:
            differenze.append(f"{quanti} ordinamenti invece di {attesa['ordina']}")

    if "limite" in attesa:
        limite = (stato.get("limit") or {})
        if limite.get("value") != attesa["limite"]:
            differenze.append(
                f"limite {limite.get('value')} invece di {attesa['limite']}")

    if "colonne" in attesa:
        quante = len(stato.get("fields") or [])
        if quante != attesa["colonne"]:
            differenze.append(f"{quante} colonne invece di {attesa['colonne']}")

    condizioni = _condizioni(stato)
    if "condizioni" in attesa and len(condizioni) != attesa["condizioni"]:
        differenze.append(
            f"{len(condizioni)} condizioni invece di {attesa['condizioni']}")

    if attesa.get("periodo"):
        temporali = [condizione for condizione in condizioni
                     if (condizione.get("value") or {}).get("kind") == "temporal"]
        if not temporali:
            differenze.append("nessuna condizione porta un periodo")

    return differenze


def esegui(env, famiglia=None, massimo=None, scrivi=False):
    dispatcher = env["nli.dispatcher"]
    semantica = env["nli.semantics"]
    scope = semantica.entity_scope()
    finestra = dispatcher._context_window()
    adapter = dispatcher._adapter_factory()(env)

    casi = [caso for caso in FRASI if famiglia in (None, caso[0])]
    if massimo:
        casi = casi[:massimo]

    print(f"\n  perimetro   {len(scope)} entita'")
    print(f"  finestra    {finestra} gettoni dichiarati")
    print(f"  casi        {len(casi)}"
          f"{f' (famiglia {famiglia})' if famiglia else ''}\n")

    # Il catalogo dell'entita' su cui la batteria lavora, letto una volta: serve a
    # distinguere «il modello ha sbagliato» da «l'attributo non gliel'ha mostrato
    # nessuno», che con la finestra a 4096 e' la meta' dei casi (D79, D133).
    semantiche = semantica.semantics(scope)
    entita = "crm_lead" if "crm_lead" in semantiche.bindings else scope[0]
    catalogo = semantica.catalogue_for(semantiche, entita, context_window=finestra)
    termini = _catalogo_termini(catalogo)
    print(f"  catalogo di {entita}: {len(catalogo.attributes)} attributi tenuti, "
          f"{catalogo.refused_for_budget} rifiutati per budget")
    print(f"  {GRIGIO}{', '.join(sorted(termini))[:400]}{FINE}\n")

    esiti = {"ok": 0, "diverso": 0, "saltato": 0}
    per_famiglia = {}
    righe = []

    for indice, (nome_famiglia, frase, attesa, serve) in enumerate(casi, start=1):
        mancanti = _manca(serve, termini)
        if mancanti:
            esiti["saltato"] += 1
            righe.append((nome_famiglia, frase, "saltato",
                          f"il catalogo non espone: {', '.join(mancanti)}", 0, None))
            print(f"  {indice:3}/{len(casi)}  {GIALLO}saltato{FINE}  {frase[:58]:<58} "
                  f"{GRIGIO}{', '.join(mancanti)}{FINE}")
            continue

        interrogazione = env["nli.interrogation"].create({})
        item = env["nli.queue.item"].accept(interrogazione, frase)
        partito = time.monotonic()
        try:
            esito = pipeline_module.run(env, item, adapter=adapter, scope=scope,
                                        context_window=finestra, debug=True)
        except Exception as errore:  # noqa: BLE001
            secondi = time.monotonic() - partito
            esiti["diverso"] += 1
            righe.append((nome_famiglia, frase, "errore", repr(errore), secondi, None))
            print(f"  {indice:3}/{len(casi)}  {ROSSO}errore {FINE}  {frase[:58]:<58} "
                  f"{secondi:5.1f}s  {errore!r}")
            continue
        secondi = time.monotonic() - partito

        differenze = _differenze(attesa, esito)
        record = esito.record_count if esito.outcome == "operations" else ""
        if differenze:
            esiti["diverso"] += 1
            colore, etichetta = ROSSO, "diverso"
        else:
            esiti["ok"] += 1
            colore, etichetta = VERDE, "ok     "
        conteggi = per_famiglia.setdefault(nome_famiglia, {"ok": 0, "totale": 0})
        conteggi["totale"] += 1
        conteggi["ok"] += 0 if differenze else 1

        righe.append((nome_famiglia, frase, etichetta.strip(),
                      "; ".join(differenze), secondi, record))
        print(f"  {indice:3}/{len(casi)}  {colore}{etichetta}{FINE}  {frase[:58]:<58} "
              f"{secondi:5.1f}s  {str(record):>6}  "
              f"{GRIGIO}{'; '.join(differenze)[:70]}{FINE}")

    print(f"\n  {'-' * 76}")
    for nome_famiglia, conteggi in per_famiglia.items():
        quota = conteggi["ok"] / conteggi["totale"] if conteggi["totale"] else 0
        print(f"  {nome_famiglia:<12} {conteggi['ok']:3}/{conteggi['totale']:<3} "
              f"{quota:6.1%}")
    eseguiti = esiti["ok"] + esiti["diverso"]
    print(f"  {'-' * 76}")
    print(f"  eseguiti     {eseguiti}    come atteso {esiti['ok']}    "
          f"diversi {esiti['diverso']}    saltati {esiti['saltato']}")
    if esiti["saltato"]:
        print(f"  {GIALLO}I saltati non sono fallimenti del modello: sono attributi "
              f"che il budget di D79 non gli ha mostrato.{FINE}")
    print()

    if scrivi:
        env.cr.commit()
        print("  turni scritti (CAMPO_SCRIVI=1)\n")
    else:
        env.cr.rollback()
        print("  transazione annullata: nessun turno resta scritto\n")
    return righe


esegui(
    env,  # noqa: F821 — la shell di Odoo lo mette lei
    famiglia=os.environ.get("CAMPO_FAMIGLIA") or None,
    massimo=int(os.environ["CAMPO_MAX"]) if os.environ.get("CAMPO_MAX") else None,
    scrivi=os.environ.get("CAMPO_SCRIVI") == "1",
)
