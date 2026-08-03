"""One turn, on its own cursor, with the identity of whoever asked for it.

Three properties of `05` §3.4 are realised here, and each one is a decision:

**Its own cursor and its own transaction.** The failure of one turn must not roll back
the others in the batch, which is why the cron's cursor cannot be reused.

**The identity of the requesting user.** V2 holds on the cron process too, and this is
exactly where the temptation to elevate becomes concrete: the code is no longer inside
an authenticated request, so the user has to be rebuilt. The environment is therefore
constructed with the uid **read from the queue row** and the company context
**rebuilt from the turn** (D40) — never with a constant, never with `sudo`. An
execution that restored the user but not their active companies would return the same
orders plus those of a company they had deselected: no error, no warning, a different
number.

**Nothing here decides.** The thread opens a cursor, builds an environment, calls the
pipeline, writes the outcome and notifies. Every judgement — what the limits are, what
the catalogue is, what the model said — belongs to code that can be tested without a
thread.

The pool is threads and not processes because the work is almost entirely network
wait: eight threads waiting on eight HTTP responses cost about what one costs, and
they do not contend for the interpreter lock. That is the case threads are the right
tool for, and `pool.py` is where the size stops being a matter of taste.
"""

from __future__ import annotations

import logging
import traceback

import odoo
from odoo import api, fields

from odoo.addons.nli_engine.adapters.base import AdapterError

from . import pipeline

_logger = logging.getLogger(__name__)


def execute(dbname, item_id: int, uid: int, context: dict, *, adapter_factory,
            scope, context_window: int, debug: bool = False):
    """Run one queue row to completion. Never raises: it records and notifies.

    A thread that dies with an exception leaves a row in `running` and a user in
    front of a spinner. Every failure is therefore turned into a final state and a
    message, and the recovery cron of §5.3 is left to handle only what this function
    could not reach — a process that was killed.
    """
    registry = odoo.registry(dbname)
    with registry.cursor() as cr:
        env = api.Environment(cr, uid, context)
        item = env["nli.queue.item"].browse(item_id)
        try:
            adapter = adapter_factory(env)
        except AdapterError as error:
            # §11 di `04`: il fornitore irraggiungibile e' un modo di fallire
            # **dichiarato**, non un guasto nostro. Deve arrivare all'utente come tale
            # — e al circuito, che su questo apre — invece di finire nel gestore
            # generico e diventare «qualcosa e' andato storto».
            cr.rollback()
            # `unavailable` e non `not_understood`: sono due cose diverse e portano a
            # due azioni diverse. «Non ho capito» invita a riformulare, e riformulare
            # non serve a niente se il modello non c'e'. Il campo `outcome` del turno
            # e' nostro, non del contratto, quindi puo' dire cio' che serve
            # all'interfaccia senza allargare il vocabolario del DSL.
            outcome = pipeline.Outcome(
                outcome="unavailable", provider_failed=True,
                failures=[str(error)])
            _persist(env, item, outcome)
            cr.commit()
            item.notify({"outcome": outcome.outcome})
            return outcome

        # **La scrittura sta dentro il `try` quanto l'interpretazione**, e per la
        # ragione che il docstring dichiara: *«non solleva mai»*. Prima il `try`
        # copriva `pipeline.run` e basta, quindi un guasto in `_persist` usciva dal
        # thread — e la riga restava in `running` con l'utente davanti all'attesa fino
        # al cron di recupero, cinque minuti dopo.
        #
        # Non e' un'ipotesi: `write_state` ha gia' fallito una volta, per la
        # `dsl_version` mancante di `00` §30.1, e il primo turno che riusciva di ogni
        # conversazione moriva li'. Allora il guasto fu corretto; il fatto che potesse
        # uccidere il thread, no.
        try:
            outcome = pipeline.run(
                env, item, adapter=adapter, scope=scope,
                context_window=context_window, debug=debug)
            _persist(env, item, outcome)
        except Exception as error:  # noqa: BLE001 — see the docstring
            cr.rollback()
            return _fail(env, item_id, error)

        cr.commit()
        # D124: l'avviso dice **che** il turno e' finito, non cosa dice. Cio' che si
        # disegna lo costruisce `_aida_payload`, in `nli_web`, e una sola volta: quando
        # l'avviso portava anche l'interpretazione erano due strade verso lo stesso
        # schermo, ed erano divergute in silenzio.
        item.notify({"outcome": outcome.outcome})
        return outcome


def _persist(env, item, outcome):
    """Write what the turn produced, then close the queue row.

    The order matters: the turn's state is what the user will see, and the queue row
    reaching a final state is what erases the utterance (D96). Erasing first would
    leave a window in which a crash loses the sentence and the answer both.
    """
    turn = item.turn_id
    values = {"executed_at": fields.Datetime.now(), "outcome": outcome.outcome}
    if outcome.executed:
        values["state_json"] = _dumped(outcome.state)
        values["record_count"] = outcome.record_count
        turn.interrogation_id.write_state(outcome.state)
    # La risposta impaginata si conserva qui, non si riderivera'. Vale per ogni esito,
    # non solo per quelli eseguiti: un chiarimento e un fuori-portata sono risposte che
    # la cronologia deve poter rimostrare (§12.7 li registra come turni completati).
    if outcome.interpretation is not None:
        values["interpretation_json"] = _dumped(outcome.interpretation)
    # D123: la traccia c'e' solo se qualcuno l'ha chiesta accendendo la modalita'
    # diagnostica. Un'installazione ordinaria non ne scrive nessuna, che e' il motivo
    # per cui puo' contenere la busta per intero senza essere un archivio di frasi.
    if outcome.debug is not None:
        values["debug_json"] = _dumped(outcome.debug)
    # D124: il piano non e' diagnostica, e' la query con cui si disegna la
    # tabella. Si scrive per ogni turno eseguito.
    if outcome.plan is not None:
        values["plan_json"] = _dumped(outcome.plan)
    turn.write(values)

    if outcome.outcome == "operations":
        item.complete()
    elif outcome.provider_failed:
        item.fail("provider_unavailable")
    else:
        # A clarification or an out-of-scope answer is a completed turn, not a
        # failure: the system understood and answered. Recording them as failures
        # would make the failure rate measure the contract working (§12.7).
        item.complete()


def _fail(env, item_id: int, error: Exception):
    """Record an unexpected failure without ever writing what caused it verbatim.

    D60 forbids utterances and catalogues in diagnostic logs, and an exception
    message can carry either — a validation error quotes the value it refused. So il
    **messaggio** non si scrive, mai.

    **La pila delle chiamate invece si scrive, e prima non succedeva.** Il docstring
    diceva che il dettaglio *«resta nell'eccezione, che la piattaforma registra con la
    traccia»*: non e' vero, perche' l'eccezione la catturiamo noi e non la rilanciamo.
    Il risultato era una riga sola — `AIDA turn 80 failed: TypeError` — e nessun modo di
    sapere dove. Trovato il 3 agosto 2026 debuggando un difetto mio: il file e la riga
    erano l'unica cosa che serviva, ed erano l'unica che mancava.

    `format_tb` scrive **solo i fotogrammi** — file, riga, sorgente — e non il messaggio
    dell'eccezione, che e' il pezzo che potrebbe citare una frase dell'utente. La
    distinzione e' la ragione per cui questo si puo' fare senza toccare D60.
    """
    item = env["nli.queue.item"].browse(item_id)
    _logger.warning("AIDA turn %s failed: %s\n%s", item_id, type(error).__name__,
                    "".join(traceback.format_tb(error.__traceback__)))
    # Chiudere la riga di coda non basta: il **turno** e' cio' che la cronologia
    # rilegge, e un turno senza esito e' un turno «in corso» per sempre. Prima di
    # questa riga, una conversazione riaperta mostrava l'animazione dell'attesa su una
    # domanda a cui nessuno avrebbe piu' risposto — e non lo vedeva nessun test,
    # perche' si vede solo riaprendo.
    item.turn_id.write({
        "outcome": "failed",
        "executed_at": fields.Datetime.now(),
    })
    item.fail(type(error).__name__)
    item.notify({"outcome": "failed"})
    env.cr.commit()
    return None


def _dumped(state) -> str:
    import json

    return json.dumps(state, ensure_ascii=False)
