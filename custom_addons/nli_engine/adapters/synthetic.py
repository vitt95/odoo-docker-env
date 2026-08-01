"""Un fornitore finto con latenza vera, per il solo banco di prova del carico (D97).

## Perche' esiste

La prova di D27 misura l'effetto del prodotto su **chi non lo sta usando**, e cio' che
produce quell'effetto non e' l'accuratezza dell'interpretazione: e' il fatto che ogni
turno tiene occupato un thread del pool e una connessione PostgreSQL per un tempo
dominato dall'attesa di rete. Senza un fornitore che risponda in quel tempo, la prova
misura una coda che si svuota istantaneamente — cioe' niente.

Il modello locale darebbe latenza vera, ma **D80 rifiuta l'attivazione di un profilo
non qualificato** e qwen2.5 e' al 15%. La regola e' giusta e non va aggirata: un
profilo lento dimezza la capacita' del dispatcher e la conseguenza cade sull'ERP.

Questo adattatore non e' quindi un profilo e **non passa dalla macchina a stati**:
non e' in `PROTOCOLS`, non e' costruibile da una riga di `nli.profile`, e D75 e D80
restano intatte. Vive dietro una variabile d'ambiente e nient'altro.

## Perche' non e' una porta di servizio

Tre proprieta', tutte verificabili leggendo questo file:

* **fallimento chiuso** — senza `NLI_LOAD_HARNESS` la funzione `enabled()` risponde
  falso e non esiste alcun modo di costruire l'adattatore. Come `NLI_ALLOWED_HOSTS`
  sotto D77: una protezione che degrada in silenzio non e' una protezione;
* **non amplia nulla** — la busta prodotta e' una costante di questo file, sempre la
  stessa, sempre valida secondo il contratto. Non legge dati, non chiama nessuno, non
  ha credenziali. Chi puo' impostare una variabile d'ambiente sul processo Odoo
  possiede gia' il processo, e questo adattatore non gli da' niente che non abbia;
* **non passa inosservato** — ogni ciclo che lo usa emette un `warning`, e ogni turno
  che ha prodotto lo dichiara nel proprio esito. Un banco di prova dimenticato acceso
  si riconosce dai log, non dal comportamento.

## La forma della variabile

    NLI_LOAD_HARNESS=1.5          -> risponde dopo 1,5 s
    NLI_LOAD_HARNESS=1.5:fail     -> attende 1,5 s e poi fallisce (prova §7.2)

La latenza e' un parametro perche' due delle sette prove di §7.2 la muovono: quella
sulla scadenza chiede *«fornitore rallentato a 10 s»* e quella sul guasto chiede un
fornitore irraggiungibile.
"""

from __future__ import annotations

import json
import os
import time

from .base import Adapter, AdapterError, Capabilities, Reply, Request

#: Il nome della variabile. Assente, questo modulo e' inerte.
VARIABLE = "NLI_LOAD_HARNESS"

PROTOCOL = "synthetic"

#: Latenza predefinita, dentro l'intervallo dichiarato da `04` §10.1 (0,6–2,5 s).
DEFAULT_LATENCY = 1.5

#: L'unica risposta che questo adattatore sa dare. Una costante, non una funzione dei
#: dati: cosi' non c'e' nulla che possa dipendere da cio' che l'utente ha scritto.
ENVELOPE = {
    "dsl_version": "1.0",
    "outcome": "operations",
    "confidence": 0.9,
    "operations": [
        {"op": "set_target", "ref": "res_partner",
         "provenance": {"text": "banco di prova"}},
    ],
}


def specification() -> tuple[float, bool] | None:
    """`(latenza, fallisce)` se il banco e' acceso, altrimenti `None`."""
    raw = os.environ.get(VARIABLE, "").strip()
    if not raw:
        return None
    latency, _, mode = raw.partition(":")
    try:
        seconds = float(latency) if latency else DEFAULT_LATENCY
    except ValueError:
        seconds = DEFAULT_LATENCY
    return max(0.0, seconds), mode.strip().lower() == "fail"


def enabled() -> bool:
    return specification() is not None


class SyntheticAdapter(Adapter):
    """Attende, poi risponde. E' tutto quello che la prova di carico richiede."""

    protocol = PROTOCOL

    def __init__(self, *, latency: float = DEFAULT_LATENCY, fail: bool = False,
                 capabilities: Capabilities | None = None):
        self.latency = latency
        self.fail = fail
        self._capabilities = capabilities or Capabilities(
            context_window=32_000, constrained_generation=False)

    @classmethod
    def from_environment(cls) -> "SyntheticAdapter":
        specified = specification()
        if specified is None:
            raise AdapterError(
                f"{VARIABLE} non e' impostata: il banco di prova non esiste "
                "se nessuno lo accende esplicitamente"
            )
        latency, fail = specified
        return cls(latency=latency, fail=fail)

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def complete(self, request: Request, *, schema: dict | None = None) -> Reply:
        # L'attesa e' il punto: e' cio' che tiene occupato il thread del pool e la
        # connessione, ed e' l'unica proprieta' del fornitore che la prova misura.
        time.sleep(self.latency)
        if self.fail:
            raise AdapterError("banco di prova: fornitore dichiarato irraggiungibile")
        return Reply(text=json.dumps(ENVELOPE))
