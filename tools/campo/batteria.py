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

import json
import os
import time
import urllib.error
import urllib.request

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


def _catalogo_riferimenti(catalogo):
    """I riferimenti che il modello vede per questa entita'."""
    riferimenti = {attributo.ref for attributo in catalogo.attributes}
    riferimenti.update(categoria.ref for categoria in catalogo.categories)
    return riferimenti


def _catalogo_termini(catalogo):
    """Tutte le parole che il modello vede per questa entita', in minuscolo.

    Non serve piu' a decidere chi salta — serve a **stampare** il catalogo in testa
    al giro, che e' l'unico modo per capire, leggendo un esito, cosa il modello aveva
    davanti.
    """
    parole = set()
    for attributo in catalogo.attributes:
        parole.update(termine.casefold() for termine in attributo.terms)
    for categoria in catalogo.categories:
        parole.update(termine.casefold() for termine in categoria.terms)
    return parole


def _manca(serve, riferimenti):
    """I riferimenti che la frase richiede e che il catalogo non espone.

    **Il confronto e' sui `ref`, non sulle etichette, e la ragione e' un difetto
    misurato.** Fino al 4 agosto 2026 qui si confrontavano per contenimento le
    stringhe che `frasi.py` dichiarava a mano contro le etichette Odoo vere, e le
    due non si incontravano quasi mai:

        la batteria cercava   l'etichetta vera    si incontravano?
        data di creazione     Data creazione      no, un «di» di troppo
        email                 E-mail              no, manca il trattino
        commerciale           Addetto vendite     no, sono parole diverse
        citta'                Citta'              no, l'apostrofo non e' l'accento

    Ventuno frasi su 54 — tutte le date — non sono mai state eseguite, in nessun
    giro, e il salto **nascondeva successi veri**: il modello legge `Addetto
    vendite` nel catalogo, sente «commerciale» e capisce da solo.

    Il `ref` invece e' cio' che il catalogo pubblica davvero, non una traduzione
    che qualcuno ha scritto a mano in un altro file. Chiedere «`crm_lead.user_id`
    e' nel catalogo?» ha una risposta sola, e la domanda che `serve` vuole fare e'
    esattamente questa: *l'attributo, il budget di D79 glielo ha mostrato oppure
    no?* Se il modello poi lo riconosca dalle parole e' cio' che la batteria
    misura, e non deve deciderlo il filtro d'ingresso.
    """
    return [riferimento for riferimento in serve if riferimento not in riferimenti]


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

    temporali = [(condizione.get("value") or {}) for condizione in condizioni
                 if (condizione.get("value") or {}).get("kind") == "temporal"]

    if attesa.get("periodo") and not temporali:
        differenze.append("nessuna condizione porta un periodo")

    # **Quale** periodo, non solo che ce ne sia uno (D141). E' la differenza fra una
    # misura che vede il difetto di `00` §46.1 e una che lo conta giusto: *«nel primo
    # trimestre»* portava un periodo — il terzo — e passava.
    if "espressione" in attesa:
        voluta, _, quale = attesa["espressione"].partition(":")
        trovate = [(valore.get("expression"), valore.get("n"), valore.get("year"))
                   for valore in temporali]
        atteso = (voluta, int(quale) if quale else None, attesa.get("anno"))
        if not any(nome == atteso[0]
                   and (atteso[1] is None or numero == atteso[1])
                   and (atteso[2] is None or anno == atteso[2])
                   for nome, numero, anno in trovate):
            descritte = ", ".join(
                f"{nome}({numero})" if numero is not None else str(nome)
                for nome, numero, _ in trovate) or "nessun periodo"
            atteso_scritto = attesa["espressione"] + (
                f" anno {attesa['anno']}" if "anno" in attesa else "")
            differenze.append(f"periodo {descritte} invece di {atteso_scritto}")

    return differenze


def _finestra_servita(endpoint: str):
    """Quanti gettoni il server dice di servire davvero, o `None` se non sa dirlo.

    **Specifico di `ollama`, e sta qui e non nel prodotto proprio per questo**: `/api/ps`
    non e' nel contratto dell'adattatore (D78), e infilarcelo vorrebbe dire far dipendere
    la catena da un fornitore. Uno strumento di misura invece puo' — e deve — sapere
    contro che cosa sta misurando.
    """
    base = (endpoint or "").rstrip("/")
    if not base:
        return None
    if base.endswith("/v1"):
        base = base[:-3]
    try:
        with urllib.request.urlopen(f"{base}/api/ps", timeout=5) as risposta:
            caricati = json.loads(risposta.read()).get("models") or []
    except (urllib.error.URLError, ValueError, OSError):
        return None
    for modello in caricati:
        if modello.get("context_length"):
            return int(modello["context_length"])
    return None


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

    # **Il numero dichiarato non e' una prova.** Il 20 agosto 2026 il profilo diceva
    # 8192 e il server ne serviva 4096: i prompt arrivavano tagliati a meta' catalogo,
    # il prodotto rispondeva `not_understood` e la cosa somigliava a un limite del
    # modello. La firma sta in `pipeline.py:360` da tre settimane e nessun controllo la
    # leggeva. Una misura presa contro una finestra sbagliata non e' una misura
    # imprecisa: e' **carta straccia che sembra un risultato**, ed e' il secondo modo di
    # mentire di `ai/restart` §4.
    profilo = env["nli.profile"].search([("state", "=", "active")], limit=1)
    servita = _finestra_servita(profilo.endpoint if profilo else "")
    decisione = esito_della_finestra(finestra, servita)  # noqa: F821 — concatenato
    if decisione == NON_VERIFICABILE:  # noqa: F821 — concatenato
        print(f"  {GIALLO}servita     non verificabile{FINE} — il fornitore non dice "
              f"quanto serve, e la misura va letta sapendolo")
    elif decisione == FERMATI:  # noqa: F821 — concatenato
        print(f"\n  {ROSSO}Il server serve {servita} gettoni, il profilo ne dichiara "
              f"{finestra}{FINE}.\n  I prompt arriverebbero tagliati e i fallimenti "
              f"sembrerebbero del modello.\n  Si riparte il fornitore con la finestra "
              f"giusta e si rilancia — `ai/restart` §1 del 21 agosto.\n")
        return []
    else:
        print(f"  servita     {servita} verificati sul fornitore")
    print(f"  casi        {len(casi)}"
          f"{f' (famiglia {famiglia})' if famiglia else ''}\n")

    # Il catalogo dell'entita' su cui la batteria lavora, letto una volta: serve a
    # distinguere «il modello ha sbagliato» da «l'attributo non gliel'ha mostrato
    # nessuno», che con la finestra a 4096 e' la meta' dei casi (D79, D133).
    semantiche = semantica.semantics(scope)
    # **Le frasi parlano di lead, quindi senza lead non si misura niente.** Prima qui
    # c'era un ripiego — `scope[0]` se `crm_lead` mancava — e su una banca dati senza
    # CRM la batteria chiedeva «mostrami i lead» al catalogo dei contatti e chiamava
    # sbagliato il modello per averlo detto. Un ripiego silenzioso in uno strumento di
    # misura non e' robustezza: e' un terzo modo di mentire, dopo i due di `ai/restart`
    # §4. Meglio fermarsi e dirlo.
    entita = "crm_lead"
    if entita not in semantiche.bindings:
        print(f"\n  {ROSSO}Questa banca dati non espone `crm_lead`{FINE}: il perimetro "
              f"e' {', '.join(scope)}.\n  Le frasi di `frasi.py` parlano di lead, e "
              f"misurarle su un'altra entita' non direbbe niente\n  del prodotto. "
              f"Serve un database con il CRM installato e dentro il perimetro.\n")
        return []
    catalogo = semantica.catalogue_for(semantiche, entita, context_window=finestra)
    riferimenti = _catalogo_riferimenti(catalogo)
    termini = _catalogo_termini(catalogo)
    print(f"  catalogo di {entita}: {len(catalogo.attributes)} attributi tenuti, "
          f"{catalogo.refused_for_budget} rifiutati per budget")
    print(f"  {GRIGIO}{', '.join(sorted(termini))[:400]}{FINE}\n")

    esiti = {"ok": 0, "diverso": 0, "saltato": 0}
    per_famiglia = {}
    righe = []

    for indice, (nome_famiglia, frase, attesa, serve) in enumerate(casi, start=1):
        mancanti = _manca(serve, riferimenti)
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
            item.fail(type(errore).__name__)
            esiti["diverso"] += 1
            righe.append((nome_famiglia, frase, "errore", repr(errore), secondi, None))
            print(f"  {indice:3}/{len(casi)}  {ROSSO}errore {FINE}  {frase[:58]:<58} "
                  f"{secondi:5.1f}s  {errore!r}")
            continue
        secondi = time.monotonic() - partito
        # **Chiudere l'elemento di coda e' obbligatorio, non educazione.** `pipeline.run`
        # interpreta il turno e non tocca la coda: nel prodotto e' `worker._persist` a
        # chiamare `complete()`, e la batteria — che il worker non lo usa — non lo
        # chiamava nessuno. Cosi' ogni frase lasciava la sua riga in `pending`, e
        # `_queued` le contava tutte: al venticinquesimo caso si supera **L3** (la
        # profondita' della coda, pool 8 x 3 = 24) e `accept` rifiuta. Il giro moriva
        # li' con «ci sono molte richieste in corso», che era vero e voleva dire
        # soltanto che nessuno aveva sparecchiato.
        #
        # `complete()` scrive l'esito sul turno solo se il turno e' ancora vuoto,
        # quindi non sovrascrive cio' che la pipeline ha appena prodotto.
        item.complete()

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
