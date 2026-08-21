"""The chain, assembled: catalogue -> interpreter -> validator -> applicator ->
resolver -> executor -> presenter (`05` §3.3).

This is the composition root, and it is the reason D94 exists: the chain needs the
module that builds the catalogue and the module that talks to the model, and §6.3
forbids either of them from depending on the other. Everything here is orchestration
— not one line of it decides anything the earlier parts had not already decided.

**It takes an environment and a queue row, and returns an outcome.** No threads, no
cursors, no cron: those are `worker.py`'s business. That split is what makes the
chain testable in an ordinary Odoo test, executed inline, with the same code path the
dispatcher runs. A pipeline reachable only through a thread pool is a pipeline nobody
tests at the boundaries.

**The identity is the caller's.** `env` arrives with the requesting user's uid and
the company context rebuilt from the turn (D40). Nothing here elevates, nothing here
reads a configuration the user could not read: §3.4 says *"the dispatcher never runs
with its own privileges"*, and the way to keep that true is for this file to have no
way of knowing it is on a cron process at all.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from odoo import fields as odoo_fields
from odoo.addons.nli_core.application import alternatives, applicator, completion
from odoo.addons.nli_core.contract import state as state_module
from odoo.addons.nli_core.contract import vocabulary
from odoo.addons.nli_core.contract.vocabulary import DSL_VERSION
from odoo.addons.nli_core.execution import executor
from odoo.addons.nli_core.presentation import presenter
from odoo.addons.nli_core.resolution import calendar as calendar_module
from odoo.addons.nli_core.resolution import resolver as resolver_module
from odoo.addons.nli_core.validation import coherence, contextual, structural
from odoo.addons.nli_semantics import scope_lexicon, temporal_lexicon
from odoo.addons.nli_semantics.dictionary import grounding
from odoo.addons.nli_engine import interpreter as interpreter_module

from .progress import report

#: Outcomes that end the turn without an execution. None of them is a failure of the
#: system: a clarification is the contract working (§4.4), and `out_of_scope` is the
#: product declining honestly rather than answering something adjacent.
TERMINAL_OUTCOMES = ("clarification", "out_of_scope", "not_understood")

#: `01` §11.2: sotto due opzioni non e' una domanda, e' una conferma travestita.
MIN_CLARIFICATION_OPTIONS = 2


def _anchor_clarification(env, failures, operations, catalogue) -> dict | None:
    """La domanda su quale data, con le opzioni costruite dall'ancora (**D135**).

    E' `_clarification_for` con una data al posto di una categoria, e la differenza
    sta tutta in che cosa si offre: li' la condizione rifiutata era inventata e la
    prima lettura e' *«senza quel filtro»*; qui la frase un periodo lo dice davvero, e
    D111 vieta di lasciarlo cadere. Quindi nessuna opzione lo toglie: le opzioni sono
    le date, una ciascuna, con dentro il periodo che il modello aveva gia' collocato
    bene.
    """
    anchor = getattr(catalogue, "time_anchor", None) or {}
    choices = list(anchor.get("choices") or ())
    if not choices:
        return None
    reference = failures[0].path

    # `label` e non `terms[0]`: i termini riconoscono, l'etichetta nomina (D108 e
    # `store._merge`). Un'opzione che dicesse «creazione» invece di `Data creazione`
    # chiederebbe all'utente di scegliere fra parole che non ha mai visto sullo schermo.
    labels = {attribute.ref: (attribute.label or (attribute.terms[0] if attribute.terms
                                                  else attribute.ref))
              for attribute in catalogue.attributes}
    readings = alternatives.for_unanchored(
        operations, reference=reference, choices=choices)
    if not readings:
        return None

    fragment = ""
    for operation in operations:
        if (operation.get("condition") or {}).get("ref") == reference:
            fragment = (operation.get("provenance") or {}).get("text") or ""
            break

    options = []
    for reading in readings:
        label = labels.get(reading.ref, reading.ref)
        # D121: l'opzione dev'essere applicabile com'e', perche' sceglierla la applica.
        # L'etichetta e' la data, ed e' cio' che l'utente avra' detto per sceglierla —
        # quindi al secondo giro il livello 3 di D135 la trova fondata e passa.
        options.append({"label": label,
                        "operations": alternatives.grounded_in(
                            reading.operations, reading.ref, label)})

    return {
        "dsl_version": DSL_VERSION,
        "outcome": "clarification",
        "clarification": {
            "question": (env._("Which date do you mean by “%s”?") % fragment if fragment
                         else env._("Which date do you mean?")),
            "options": options,
        },
    }


def _clarification_for(env, failures, operations, catalogue) -> dict | None:
    """The envelope of a question, when the refusal has a remedy the user can act on.

    **D106 and D135.** Two failures qualify — a named condition the fragment does not
    mention, and a period sitting on a date the fragment does not name — and only when
    one of them is the *whole* of what went wrong: a state that also fails on a type or
    a cost is not one reading away from being right, and offering a choice there would
    hide a defect behind a question. They are not mixed either: **one question at a
    time** (§4.4), and a question carrying both axes would need an option per pair.

    The options come from the catalogue, never from the model (P4): a model that has
    just invented a condition is the last thing to ask for its alternatives. The
    wording is built here, in the module that has the user's language, while the
    operations are built in the pure zone that has none.
    """
    unanchored = [failure for failure in failures
                  if failure.code == "unanchored_period"]
    if unanchored and len(unanchored) == len(failures):
        return _anchor_clarification(env, unanchored, operations, catalogue)

    ungrounded = [failure.path for failure in failures
                  if failure.code == "ungrounded_category"]
    if not ungrounded or len(ungrounded) != len(failures):
        return None

    labels = {category.ref: (category.terms[0] if category.terms else category.ref)
              for category in catalogue.categories}
    readings = alternatives.for_ungrounded(
        operations, ungrounded=ungrounded, candidates=list(labels))
    if not readings:
        return None

    fragment = ""
    for operation in operations:
        if (operation.get("condition") or {}).get("ref") == ungrounded[0]:
            fragment = (operation.get("provenance") or {}).get("text") or ""
            break

    options = []
    for reading in readings:
        if reading.kind == "without":
            label = (env._("without filtering by “%s”") % fragment if fragment
                     else env._("without that filter"))
            operations = reading.operations
        else:
            label = labels.get(reading.ref, reading.ref)
            # D121: the option has to be applicable as it stands, because picking it
            # applies it. The condition it proposes is founded in the label, which is
            # what the user will have said to pick it.
            operations = alternatives.grounded_in(
                reading.operations, reading.ref, label)
        options.append({"label": label, "operations": operations})

    return {
        "dsl_version": DSL_VERSION,
        "outcome": "clarification",
        "clarification": {
            "question": (env._("I am not sure I understood “%s” as a filter. Did you mean:")
                         % fragment if fragment
                         else env._("I am not sure which filter you meant. Did you mean:")),
            "options": options,
        },
    }


@dataclass
class Outcome:
    """What a turn produced, in the shape the notification and the turn both need."""

    outcome: str = "not_understood"
    state: dict | None = None
    interpretation: dict | None = None
    record_count: int = 0
    repairs: int = 0
    failures: list = field(default_factory=list)
    #: True when the provider itself was unreachable — the circuit breaker's input.
    provider_failed: bool = False
    #: La traccia di D123, presente solo quando la modalita' diagnostica e' accesa.
    debug: dict | None = None
    #: Il piano risolto di un turno eseguito (D124). **Sempre**, non solo in
    #: diagnostica: e' con questo che la chat disegna la tabella dei record.
    plan: dict | None = None

    @property
    def executed(self) -> bool:
        return self.outcome == "operations" and self.state is not None


def trace(collector: dict | None, key: str, value):
    """Annota un passaggio, se qualcuno sta guardando.

    Il `None` e' l'interruttore: quando la modalita' diagnostica e' spenta non si
    costruisce niente e non si paga niente. Nessun ramo `if debug` sparso per il
    pipeline — una funzione che non fa nulla e' piu' difficile da sbagliare di dieci
    condizioni che devono ricordarsi di essere tutte uguali.
    """
    if collector is not None:
        collector[key] = value


def run(env, item, *, adapter, scope, context_window: int,
        debug: bool = False, reporter=None) -> Outcome:
    """Un turno, dalla frase al risultato presentato.

    **La traccia si aggancia qui e non dentro** (D123). Il corpo ha una decina di
    punti d'uscita, e attaccare la traccia a ognuno vorrebbe dire che il primo
    dimenticato e' un esito che non si sa spiegare — cioe' proprio quello che si sta
    guardando quando la modalita' diagnostica serve.

    **L'avanzamento invece si aggancia dentro, e la differenza e' il verso.** La
    traccia racconta un turno finito, quindi la si puo' raccogliere in fondo;
    l'avanzamento racconta un turno in corso, e in fondo non racconterebbe piu'
    niente. I due passano da funzioni diverse (`trace` e `report`) con lo stesso
    interruttore a `None`, perche' spegnerli non deve costare condizioni sparse.
    """
    collector: dict | None = {} if debug else None
    outcome = _run(env, item, adapter=adapter, scope=scope,
                   context_window=context_window, collector=collector,
                   reporter=reporter)
    if collector is not None:
        collector["outcome"] = outcome.outcome
        collector["repairs"] = outcome.repairs
        collector["failures"] = list(outcome.failures)
        outcome.debug = collector
    return outcome


def _run(env, item, *, adapter, scope, context_window: int,
         collector: dict | None = None, reporter=None) -> Outcome:
    turn = item.turn_id
    interrogation = turn.interrogation_id
    state = _starting_state(interrogation)
    utterance = item.utterance()
    # D120: se il turno precedente si e' chiuso con una domanda, questa frase la
    # risponde. Una richiesta di chiarimento non scrive stato — non ha prodotto
    # operazioni — quindi senza questo il contesto della conversazione sparisce
    # esattamente nel punto in cui serve di piu'.
    precedente = _pending_turn(interrogation, turn)
    pending = _pending_question(precedente)

    semantics = env["nli.semantics"].semantics(scope)

    # D121: la frase che risponde a una domanda si confronta **prima** con le opzioni.
    # Le loro operazioni sono gia' nella busta — e' cio' che D106 ci ha messo — quindi
    # una risposta che ne sceglie una non ha niente da interpretare. Il modello si
    # chiama solo se la frase non corrisponde a nessuna opzione.
    trace(collector, "utterance", utterance)
    trace(collector, "state_before", state)
    trace(collector, "pending", pending)

    chosen = _chosen_operations(precedente, utterance, state)
    if chosen is not None:
        # La strada corta: nessuna chiamata al modello, quindi un passo solo. Dirne
        # sei su un turno che dura mezzo secondo sarebbe raccontare una fatica che
        # non c'e' — e chi guarda imparerebbe in fretta a non fidarsi dei passi.
        report(reporter, "reading", force=True)
        trace(collector, "path", "chosen_reading")
        trace(collector, "operations", chosen)
        riparte = _target_of({"operations": chosen})
        if riparte:
            # **D127 dove non arrivava.** L'opzione che si porta il proprio `set_target`
            # nasce da una frase che nominava il proprio soggetto, e quella frase
            # ricomincia. Lo stato di prima era gia' stato buttato via nel turno che ha
            # posto la domanda — ma un turno che chiede non scrive stato, quindi il
            # vecchio era ancora li' e l'opzione ci finiva sopra. Visto sul campo il
            # 3 agosto 2026 come un ordinamento di troppo; con una condizione al posto
            # dell'ordinamento sarebbe stata una risposta ristretta a una citta' che
            # nessuno aveva piu' nominato.
            #
            # Un'opzione **senza** `set_target` e' un raffinamento — e' cosi' che
            # `alternatives.chosen` la distingue gia', pretendendo che l'entita' sia
            # nota — e quella continua sullo stato che c'e'.
            state = {"dsl_version": interrogation.dsl_version}
            trace(collector, "state_restarted", riparte)
        return _apply_and_present(
            env, semantics, state, chosen,
            catalogue_of=lambda ref: _phase_c(env, semantics, ref, context_window),
            entity_ref=(state.get("target") or {}).get("ref"),
            utterance=utterance, collector=collector, reporter=reporter)

    trace(collector, "path", "model")
    entity_ref, outcome, riparte = _determine_entity(
        env, semantics, state, utterance, adapter=adapter,
        context_window=context_window, collector=collector, reporter=reporter)
    if entity_ref is None:
        return outcome
    if riparte:
        # D127: la frase si porta il proprio soggetto, quindi e' una domanda nuova e non
        # un raffinamento. Si riparte da vuoto — non da «vuoto tranne il bersaglio» —
        # perche' le operazioni del turno ricostruiscono tutto: il modello emette sempre
        # `set_target` per primo. E al modello si passa `state=None` poco sotto, che gli
        # toglie anche di dosso un contesto che non c'entra piu'.
        state = {"dsl_version": interrogation.dsl_version}
        trace(collector, "state_restarted", entity_ref)

    # **`da_stato`: questo turno sta rispondendo su un'entita' che la frase non ha
    # nominato** — la fase A non ha riconosciuto niente e ci si e' appoggiati allo
    # stato. E' un'assunzione, non un fatto, ed e' l'unico caso in cui vale la pena
    # ricredersi (D145). Si calcola qui, dove `known` e' ancora leggibile, e non dentro
    # `_determine_entity`: cambiare la forma di cio' che torna avrebbe toccato ogni suo
    # chiamante per un'informazione che serve a uno solo.
    da_stato = not riparte and entity_ref == (state.get("target") or {}).get("ref")

    # **E si dichiara** (D146). Il bersaglio ereditato arrivava allo schermo con
    # `origin: user`, cioe' come se l'utente lo avesse appena nominato: per il turno
    # prima era vero, per questo no. Marcarlo dedotto e' quello che fa disegnare
    # all'interfaccia il bordo tratteggiato di §10.2, e quindi l'unico rimedio che vale
    # anche per le parole che il dizionario non ha ancora — comprese quelle su cui il
    # modello riesce a rispondere lo stesso, che sono il caso pericoloso (§49.4).
    if da_stato:
        state = {**state,
                 "target": {**state["target"],
                            "origin": "inferred",
                            "rule": vocabulary.RULE_TARGET_CARRIED}}

    def _leggi(entity_ref, state, *, pending):
        """Fasi C e seguenti: prepara il catalogo, chiede al modello, applica.

        E' una funzione perche' si percorre **due volte** nel turno che si ricrede, e
        due copie diverterebbero: e' la stessa ragione per cui `_apply_and_present`
        non e' la coda di questa funzione.
        """
        report(reporter, "catalogue")
        started = time.monotonic()
        catalogue = _phase_c(env, semantics, entity_ref, context_window)
        budget = getattr(catalogue, "budget", None)
        trace(collector, "phase_c", {
            "entity": entity_ref,
            "seconds": round(time.monotonic() - started, 3),
            "attributes": len(getattr(catalogue, "attributes", ()) or ()),
            "categories": len(getattr(catalogue, "categories", ()) or ()),
            # **Quanti attributi il budget ha buttato via** (D79). Il contatore esisteva da
            # sempre — `refused_for_budget` — e non lo leggeva nessuno. Misurato il 3 agosto
            # 2026: con la finestra di 4096 dichiarata dal profilo in servizio il budget
            # vale **17** attributi contro il tetto di 60 di D31, quindi la fase C ne scarta
            # decine. Cio' toglie a **D32** la proprieta' con cui chiude **RC3** — *«in fase
            # C non c'e' selezione, la copertura e' esatta per costruzione»* — e nessuna
            # tabella diagnostica lo diceva, che e' esattamente il guasto per cui D79 esiste.
            # E' gia' un numero — `build.Catalogue.refused_for_budget` e' un `int`. Ci ho
            # messo un `len()` intorno e ogni turno moriva con un `TypeError` **prima di
            # arrivare al modello**, perche' un argomento si valuta anche quando la funzione
            # che lo riceve non ne fa niente: `trace` esce subito a diagnostica spenta, ma
            # il dizionario era gia' stato costruito.
            "refused_for_budget": getattr(catalogue, "refused_for_budget", 0),
            "budget": {"attributes": budget.attributes, "reason": budget.reason,
                       "detail": budget.detail} if budget else None,
        })
        # D112 (categories admitted narrowed to what the sentence names) and D105 (a
        # named condition not grounded in its own fragment is refused at level 3) read
        # the same recognizer: one keeps the ungrounded category from ever being
        # writable, the other refuses it if it arrives by another route. Building it
        # twice would mean building two term indexes in the request's path for the
        # same reply.
        mentions = grounding.mentions_of(semantics.dictionary)
        # L'attesa lunga comincia qui: e' la chiamata al modello, mediana 8,8 s e p95
        # 16,3 s sulle 414 misurate. L'avviso parte **prima** di entrarci, non dopo:
        # dire «ho interpretato» a cose fatte non toglie un secondo di attesa muta a
        # nessuno. Porta con se' il nome di casa dell'entita' — «fatture», «lead» —
        # perche' e' l'unico momento in cui il sistema puo' dire di che cosa ha capito
        # che si parla mentre lo sta ancora usando.
        report(reporter, "interpret", detail=_entity_label(catalogue))
        started = time.monotonic()
        interpretation = interpreter_module.interpret(
            adapter, utterance=utterance, catalogue=catalogue,
            state=state if state.get("target") else None,
            mentions=mentions,
            scope_justifies=scope_lexicon.justifies,
            names_period=temporal_lexicon.names_period,
            pending=pending,
        )
        trace(collector, "interpret", {
            "seconds": round(time.monotonic() - started, 3),
            "understood": interpretation.understood,
            "repairs": interpretation.repairs,
            # **Quanto ha letto davvero il fornitore, contro quanto il profilo dichiara.**
            #
            # Sono due numeri diversi e nessuno li confrontava. `context_window` e' cio' che
            # il profilo *dichiara* e con cui D79 dimensiona il catalogo; `prompt_tokens` e'
            # cio' che il server dice di aver letto. Se il secondo si avvicina al primo il
            # prompt e' sull'orlo, e oltre il primo **il server taglia in silenzio**: HTTP
            # 200, nessun errore, una risposta plausibile costruita su meta' catalogo.
            #
            # Misurato il 3 agosto 2026 su `ollama`: con la finestra a 4096, un prompt da
            # dodicimila gettoni tornava con `prompt_eval_count` a 2050 e il modello non
            # sapeva piu' cosa c'era all'inizio. L'adattatore **non manda** la finestra al
            # server (il protocollo OpenAI non ha un campo per dirla), quindi le due misure
            # possono divergere e l'unico modo di accorgersene e' guardarle vicine.
            "prompt_tokens": max((getattr(reply, "prompt_tokens", 0)
                                  for reply in interpretation.replies), default=0),
            "context_window": context_window,
            # La busta come il modello l'ha restituita: e' il DSL grezzo, prima che
            # l'applicatore la trasformi in stato. E' cio' che si guarda per capire se il
            # turno e' andato storto nel modello o dopo.
            "envelope": interpretation.envelope,
        })
        outcome = Outcome(outcome=interpretation.outcome, repairs=interpretation.repairs)
        if not interpretation.understood:
            return _provider_failure(outcome, interpretation)

        envelope = interpretation.envelope
        outcome.outcome = envelope.get("outcome", "not_understood")
        if outcome.outcome in TERMINAL_OUTCOMES:
            return _terminal_outcome(outcome, envelope, collector)

        return _apply_and_present(
            env, semantics, state, envelope.get("operations") or [],
            collector=collector,
            # The catalogue for this entity is already built — phase C built it to ask the
            # question. Handing it over as a callable is what lets the other caller, which
            # has no catalogue and usually needs none, avoid building one for nothing.
            catalogue_of=lambda ref: catalogue,
            entity_ref=entity_ref, outcome=outcome, mentions=mentions,
            utterance=utterance, reporter=reporter)

    esito = _leggi(entity_ref, state, pending=pending)

    # **D145 — un raffinamento che non si capisce si ricrede, una volta sola.**
    #
    # Se siamo arrivati qui su un'entita' che la frase non ha nominato (`da_stato`) e la
    # lettura e' finita in `not_understood`, l'assunzione ha un'alternativa che non
    # abbiamo ancora provato: chiedere al modello di che cosa parla la frase. E' la fase
    # B, esiste esattamente per il caso «il dizionario non conosce questa parola», ed era
    # irraggiungibile appena una conversazione aveva un bersaglio.
    #
    # Misurato il 20 agosto 2026 sul database vero: *«mostrami le vendite con totale
    # superiore a 2000»*, arrivata dopo una domanda sui lead, ha ricevuto il catalogo dei
    # lead — dove *Totale* non esiste — e ha risposto `not_understood` in 67,7 s. La
    # stessa frase, con la fase B raggiungibile, risolve `sale_order` in 7,2 s e torna
    # tre record.
    #
    # **Si paga solo dopo aver gia' fallito**: sul percorso buono questo blocco non
    # esiste. E si paga una volta: la seconda lettura non si ricrede a sua volta, perche'
    # riparte da uno stato pulito e quindi `da_stato` li' e' falso per costruzione.
    #
    # Il rifiuto resta quello di prima se la fase B non porta un'entita' **diversa**:
    # ripetere la stessa lettura per avere lo stesso esito costerebbe un minuto e non
    # cambierebbe una parola di cio' che l'utente legge.
    if da_stato and esito.outcome == "not_understood":
        rinuncia = esito
        entity_b, _fallito = _phase_b(
            env, semantics, utterance, adapter=adapter, context_window=context_window,
            collector=collector, reporter=reporter, trace_key="phase_b_retry")
        if entity_b is not None and entity_b != entity_ref:
            # Ricomincia: la frase porta il proprio soggetto, quindi e' una domanda
            # nuova e non un raffinamento (D127). Lo stato vecchio non si eredita —
            # portarselo dietro qui vorrebbe dire chiedere le vendite con il filtro
            # sull'anno dei lead, che e' il difetto di partenza con un'entita' in piu'.
            trace(collector, "reconsidered", {
                "from": entity_ref, "to": entity_b, "was": rinuncia.outcome})
            stato_nuovo = state_module.empty_state()
            esito = _leggi(entity_b, stato_nuovo, pending=None)
            if esito.outcome == "not_understood":
                # Neanche il secondo tentativo ha capito: si torna il primo rifiuto, che
                # e' quello costruito sull'entita' di cui l'utente stava parlando.
                esito = rinuncia
    return esito


def _entity_label(catalogue) -> str:
    """Il nome di casa dell'entita', quello con cui l'utente la chiama.

    `entity_names` porta gia' le coppie riferimento/termini che il catalogo espone al
    modello: il primo termine e' il nome piu' comune, ed e' quello che una persona
    riconosce. Se manca si torna vuoti — un passo senza dettaglio resta leggibile,
    un passo con un riferimento tecnico dentro no.
    """
    entita = getattr(catalogue, "entity", None)
    for riferimento, termini in getattr(catalogue, "entity_names", ()) or ():
        if riferimento == entita and termini:
            return termini[0]
    return ""


def _apply_and_present(env, semantics, state, operations, *, catalogue_of,
                       entity_ref=None, outcome=None, mentions=None, names=None,
                       utterance: str = "", collector=None, reporter=None) -> Outcome:
    """From operations to a presented result: applicator, levels 3-5, resolver,
    executor, presenter.

    **Why this is a function and not the tail of `run`.** There are two ways a turn
    produces operations — the model interprets a sentence, or the user picks a reading
    whose operations were already in the envelope (D121) — and there must be exactly
    one way of carrying them out. Two copies of this sequence would agree on the day
    they were written and drift on every day after: the second one would be the one
    that forgets a validation level, and it would forget it silently, because a query
    that skipped level 4 does not fail — it answers.
    """
    outcome = outcome or Outcome()
    # The recognizer is built once per turn and handed down: it indexes the whole term
    # list of the dictionary, and building a second one inside the request's path for
    # the same reply is the cost the caller already avoided once.
    mentions = mentions or grounding.mentions_of(semantics.dictionary)
    names = names or grounding.names_of(semantics.dictionary)

    # --- application: pure, and the same code the corpus runs ----------------
    # The types come first because the completion of D99 needs them: a direction the
    # user did not name is derived from the attribute's type here, not asked of the
    # model (P4) and not defaulted inside the Applicator (D88).
    types = {ref: binding.type for ref, binding in semantics.bindings.items()}
    operations = completion.fill_inferred_directions(operations, types)
    applied = applicator.apply(state, operations)
    new_state = applied.state
    trace(collector, "operations", operations)
    trace(collector, "state_after", new_state)

    # **D135**: l'ancora del tempo sta nel catalogo, e il catalogo si costruisce solo
    # se serve. Un turno che non porta nessun periodo non ha niente da ancorare, e la
    # fase C costa un quarto di secondo misurato (`00` §32.1) — niente accanto al
    # modello, tutto accanto a un turno che risponde senza chiamarlo (D121).
    asked = (new_state.get("target") or {}).get("ref") or entity_ref
    catalogue = (catalogue_of(asked)
                 if asked and contextual.carries_period(new_state) else None)

    # --- levels 3-5, with the dictionary this user actually has --------------
    report(reporter, "validate")
    failures = contextual.validate(
        new_state, known_refs=frozenset(semantics.bindings), types=types,
        # D105: the dictionary decides what counts as mentioning a term, because it
        # is the only component that knows the accents, the typos and the
        # abbreviations. `nli_core` receives the answer, never the vocabulary.
        mentions=mentions,
        # D135: la stessa domanda per le date. `names` riconosce i termini di un
        # attributo (T1), che `mentions` non vede perche' indicizza solo le condizioni
        # nominate (T5); l'ancora dice se questo utente aveva davvero una scelta.
        names=names,
        time_anchor=getattr(catalogue, "time_anchor", None),
        # D135, la frase intera: la parola che ancora il periodo sta quasi sempre fuori
        # dal frammento che il modello dichiara come provenienza — dice «i lead
        # **creati** negli ultimi 30 giorni» e dichiara «negli ultimi 30 giorni». La
        # regola la usa solo quando la frase nomina una data sola, e solo per
        # **accettare**: vedi `validate_anchoring`.
        utterance=utterance,
        # Le condizioni che c'erano **prima** che questo turno applicasse le sue
        # operazioni: sono gia' state giudicate nel turno che le ha introdotte, e i
        # loro frammenti non esistono piu' — `strip_provenance` li toglie quando lo
        # stato si salva. Senza questo, dopo un filtro sulle date ogni raffinamento
        # veniva rifiutato, e il rifiuto parlava di una condizione che l'utente non
        # aveva appena chiesto.
        already_judged=frozenset(state_module.condition_ids(state)),
        # V-D87-2: quanto costa ogni condizione nominata. Il parametro c'e' da sempre e
        # non lo passava nessuno, quindi valeva `{}` e il livello 5 sulle categorie non
        # poteva scattare — una regola scritta, provata e mai eseguita, come `coherence`
        # prima di §33.3. Stessa forma, stesso rimedio: un argomento in piu' nell'unico
        # punto in cui i livelli 3-5 girano.
        category_costs=getattr(semantics, "category_costs", None))
    trace(collector, "validation_failures", [str(failure) for failure in failures])
    if failures:
        # D106: an ungrounded named condition is the one failure with a remedy the
        # user can act on, and the remedy is derivable. Every other failure stays what
        # it was — a defect of ours, told as "we did not understand" (§12.7), with the
        # detail going to the register and never to the user.
        if catalogue is None and asked:
            catalogue = catalogue_of(asked)
        question = (_clarification_for(env, failures, operations, catalogue)
                    if catalogue is not None else None)
        if question is not None:
            outcome.outcome = "clarification"
            outcome.interpretation = question
            outcome.failures = [str(failure) for failure in failures]
            return outcome
        outcome.outcome = "not_understood"
        outcome.failures = [str(failure) for failure in failures]
        return outcome

    entity_ref = asked
    model_name = semantics.model_of(entity_ref)
    if model_name is None:
        outcome.outcome = "not_understood"
        outcome.failures = [f"the state names an entity that is not in scope: {entity_ref}"]
        return outcome

    # --- resolution: the one component aware of time (04 §4.6) --------------
    resolution = resolver_module.resolve(
        new_state,
        bindings=semantics.bindings,
        instant=_instant(env),
        model=model_name,
        # **L'utente arriva da qui e da nessun'altra parte** (D147). `env.uid` e'
        # l'identita' con cui il turno e' stato accettato: §3.4 dice che il dispatcher
        # non gira mai con privilegi propri, e D40 ricostruisce questo ambiente dal
        # turno. Il modello non la vede, non la scrive e non puo' sostituirla — al
        # massimo puo' nominare *un'altra persona*, che e' una domanda legittima e che
        # le regole di record di Odoo filtrano comunque.
        actor=env.uid,
    )
    if not resolution.resolved:
        trace(collector, "resolution_failures",
              [str(failure) for failure in resolution.failures])
        outcome.outcome = "not_understood"
        outcome.failures = [str(failure) for failure in resolution.failures]
        return outcome

    outcome.plan = _plan_as_dict(resolution.plan)
    trace(collector, "plan", outcome.plan)
    report(reporter, "execute")
    started = time.monotonic()
    # `run` e non `execute`: l'aggregazione era una seconda funzione dell'Esecutore che
    # questa riga non chiamava, quindi ogni misura dello stato arrivava fin qui e non
    # veniva calcolata da nessuno. Adesso l'Esecutore ha una porta sola e la scelta del
    # ramo la fa lui, guardando il piano.
    result = executor.run(env, resolution.plan)
    trace(collector, "execute", {"seconds": round(time.monotonic() - started, 3),
                                 "records": result.total,
                                 "groups": len(result.groups)})
    shown = presenter.present(state=new_state, plan=resolution.plan, result=result)

    outcome.outcome = "operations"
    outcome.state = new_state
    outcome.interpretation = shown.interpretation
    outcome.record_count = result.total
    return outcome


def _determine_entity(env, semantics, state, utterance, *, adapter, context_window,
                      collector=None, reporter=None):
    """Phases A, B and C — the strategy of D32 on a live dictionary.

    Restituisce `(entity_ref, None, riparte)` quando un'entita' e' stata determinata,
    oppure `(None, outcome, False)` quando il turno finisce senza.

    `riparte` dice se la frase si porta il **proprio** soggetto — cioe' se e' una
    domanda nuova invece di un raffinamento (D127).

    Phase A applies **only when the entity is not known** (§5.5, and registry §16.3,
    which records what applying it to refinements cost: 116 wrong determinations out
    of 1 200). A refinement already carries its target, so it goes straight to C.
    """
    from odoo.addons.nli_semantics.introspection import runtime

    known = (state.get("target") or {}).get("ref")

    # **La fase A gira sempre, anche quando lo stato ha gia' un bersaglio** (D127).
    # Prima si fermava qui, e con lei spariva il solo segnale che distingue una domanda
    # nuova da un raffinamento. Costa cinque centesimi di secondo ed e' il dizionario,
    # non il modello.
    # Il primo passo parte **subito** (`force`), perche' e' quello che sostituisce
    # l'attesa muta. Costa un quinto di secondo di strozzamento a tutti gli altri e
    # toglie il momento peggiore dell'interazione: quello in cui non si sa se il
    # sistema ha ricevuto la frase.
    report(reporter, "dictionary", force=True)
    started = time.monotonic()
    decision = runtime.determine_entity(semantics, utterance)
    trace(collector, "phase_a", {
        "seconds": round(time.monotonic() - started, 3),
        "resolved": decision.resolved,
        "entity": getattr(decision, "entity", None),
        "known": known,
    })
    if decision.resolved:
        # La frase nomina la propria entita': si ricomincia da li'. Vale anche quando
        # e' la stessa di prima — chi ridice il soggetto sta ridicendo la domanda — e
        # vale quando e' un'altra, caso che prima era **impossibile**: con un bersaglio
        # nello stato la fase A non girava, e «adesso mostrami le fatture» restava sui
        # lead senza che niente lo dicesse.
        return decision.entity, None, True

    if known:
        # Nessun soggetto **riconosciuto** nella frase: si continua su quello che c'e'
        # gia'. E' §17.1, ed e' cio' che fa funzionare «solo quelli confermati» al
        # secondo turno. **Nell'incertezza si continua**: la fase A che non riconosce e'
        # il caso frequente, e ripartire per prudenza romperebbe la conversazione ogni
        # volta.
        #
        # **Ma «non riconosciuto» non vuol dire «non nominato», ed e' li' che questa
        # riga costava** (D145). Chi dice *«mostrami le vendite con totale superiore a
        # 2000»* il soggetto lo ha nominato: e' il dizionario a non avere la parola. Il
        # turno continuava sui lead, in silenzio, e la fase B — che esiste apposta per
        # questo caso — non girava mai. Chi chiama guarda `da_stato` e, se la lettura
        # fallisce, la paga allora.
        return known, None, False

    entity, outcome = _phase_b(
        env, semantics, utterance, adapter=adapter, context_window=context_window,
        collector=collector, reporter=reporter)
    if entity is not None:
        # La fase B ha determinato il soggetto: e' una domanda nuova come quelle
        # che risolve la fase A, solo che e' costata un minuto invece di niente.
        return entity, outcome, True
    return None, outcome, False


def _phase_b(env, semantics, utterance, *, adapter, context_window,
             collector=None, reporter=None, trace_key: str = "phase_b"):
    """Phase B: the entity names alone, and one question — *which entity is this
    about?* Small, circumscribed, and the class of task models are most reliable at.
    The expensive path is also the narrow one, which is what closes RC3.

    Torna `(entita, None)` quando il modello ha nominato un'entita' del perimetro, e
    `(None, outcome)` quando non ce l'ha fatta — con l'esito gia' pronto da restituire.

    **Sta in una funzione sua perche' si paga da due punti** (D145): prima di leggere,
    quando il dizionario non ha riconosciuto niente e non c'e' nessuno stato su cui
    appoggiarsi; e dopo aver letto, quando un raffinamento e' finito in
    `not_understood`. Due copie della stessa sequenza andrebbero d'accordo il giorno in
    cui si scrivono e divergerebbero ogni giorno successivo — e' la stessa ragione per
    cui `_apply_and_present` e' una funzione e non la coda di `run`.
    """
    catalogue = env["nli.semantics"].entity_catalogue(
        semantics, context_window=context_window)
    # La strada costosa di D32: il dizionario non ha riconosciuto il soggetto e si
    # paga una chiamata al modello per saperlo. E' anche la piu' lenta delle due, ed
    # e' giusto che chi aspetta veda che sta succedendo qualcosa di diverso.
    report(reporter, "entity")
    started = time.monotonic()
    interpretation = interpreter_module.interpret(
        adapter, utterance=utterance, catalogue=catalogue, state=None)
    trace(collector, trace_key, {
        "seconds": round(time.monotonic() - started, 3),
        "understood": interpretation.understood,
        "envelope": interpretation.envelope,
    })
    outcome = Outcome(outcome=interpretation.outcome, repairs=interpretation.repairs)
    if not interpretation.understood:
        return None, _provider_failure(outcome, interpretation)

    envelope = interpretation.envelope
    entity = _target_of(envelope)
    if entity and entity in semantics.entity_refs:
        return entity, outcome

    outcome.outcome = envelope.get("outcome", "not_understood")
    if outcome.outcome in TERMINAL_OUTCOMES:
        _terminal_outcome(outcome, envelope, collector)
    else:
        # Operations without a target, or with one outside the catalogue it was just
        # given. D14: an unknown symbol is refused, never ignored — ignoring it here
        # would run the query against whichever entity happened to be around.
        outcome.outcome = "not_understood"
        outcome.failures = ["phase B produced no entity from the entity catalogue"]
    return None, outcome


def _target_of(envelope: dict) -> str | None:
    for operation in envelope.get("operations") or []:
        if operation.get("op") == "set_target":
            return operation.get("ref")
    return None


def _phase_c(env, semantics, entity_ref: str, context_window: int):
    return env["nli.semantics"].catalogue_for(
        semantics, entity_ref, context_window=context_window)


def _terminal_payload(envelope: dict) -> dict:
    """What travels to the user for a non-executing outcome.

    The clarification's own question and options, or the scope note. Never the
    envelope wholesale: it carries provenance fragments, which are the user's words,
    and D54 says those do not get written anywhere they would be retained.
    """
    if envelope.get("outcome") == "clarification":
        return {"clarification": envelope.get("clarification") or {}}
    if envelope.get("outcome") == "out_of_scope":
        return {"scope_note": envelope.get("scope_note")}
    return {}


def _instant(env) -> calendar_module.Instant:
    """The reference instant, read **here** and nowhere deeper.

    The Resolver is aware of time and never reads it (§4.6): this is the line where
    the clock enters the chain, in the user's own timezone, so that *"this month"*
    means their month. The fiscal year parameters ride along because `year_to_date`
    resolves against the fiscal year and not against January (V-D91-1) — in a company
    with a non-calendar year, January would give a wrong number that looks right.
    """
    now = odoo_fields.Datetime.context_timestamp(
        env["res.users"].browse(env.uid), odoo_fields.Datetime.now())
    last_month = int(getattr(env.company, "fiscalyear_last_month", 12) or 12)
    return calendar_module.Instant(
        now=now.replace(tzinfo=None),
        # Il **nome** del fuso, non l'ora gia' convertita. Serve al Risolutore per
        # riportare in UTC gli estremi di un periodo quando la colonna e' un `datetime`
        # — Odoo li conserva in UTC e il calendario ragiona nei giorni dell'utente. Il
        # contesto lo porta dal turno (D40), che e' l'unico posto dove esiste sul cron.
        timezone=(env.context.get("tz") or getattr(now.tzinfo, "key", "") or ""),
        # The year starts the month after the one it ends in, on the first day. That
        # covers every fiscal year that ends at a month boundary, which is all of
        # them in practice; an installation ending mid-month would need the day too,
        # and would deserve a test before being claimed to work.
        fiscal_year_start_month=last_month % 12 + 1,
        fiscal_year_start_day=1,
    )


def _terminal_outcome(outcome: "Outcome", envelope: dict, collector=None) -> "Outcome":
    """Un esito che chiude il turno senza eseguire, da qualunque fase arrivi (D128).

    **Una funzione sola, e stavolta e' il punto.** Un chiarimento puo' nascere in fase B
    — *«di quale entita' parli?»* — oppure in fase C, e le due strade impacchettavano la
    risposta **ognuna per conto suo**. La prima versione di questa validazione l'ho
    messa su una sola, e le prove hanno preso l'altra: e' il terzo caso in tre giorni
    dopo `worker._fail` e `_provider_failure`. Adesso ci passano tutte e due.
    """
    if outcome.outcome == "clarification":
        envelope = _usable_clarification(envelope, collector)
        outcome.outcome = envelope.get("outcome", "not_understood")
        if outcome.outcome != "clarification":
            outcome.failures = ["the model's clarification had no usable option"]
            return outcome
    outcome.interpretation = {"outcome": outcome.outcome,
                              **_terminal_payload(envelope)}
    return outcome


def _why_unusable(operations) -> list:
    """Perche' un'opzione non si puo' applicare, o lista vuota se si puo'.

    Due controlli, e servono tutti e due. Lo strutturale prende la busta malformata;
    la **coerenza** prende il caso vero visto sul campo — un `within` senza periodo e'
    strutturalmente una condizione a posto, ed e' il livello 4 a sapere che quel
    predicato un valore lo vuole. E' lo stesso `coherence` che fino a ieri non era
    nemmeno sul percorso (§33.3).

    Si applica a uno stato vuoto perche' un'opzione **e' una richiesta intera**: se non
    regge da sola, non regge.
    """
    if not operations:
        return ["an option with no operations proposes nothing"]
    failures = list(structural.validate_envelope({
        "dsl_version": DSL_VERSION, "outcome": "operations",
        "operations": list(operations),
    }))
    if failures:
        return failures
    try:
        applied = applicator.apply({"dsl_version": DSL_VERSION}, list(operations))
    except Exception as error:  # noqa: BLE001 — un'opzione che esplode e' inutilizzabile
        return [f"the option cannot be applied: {type(error).__name__}"]
    return list(coherence.validate_coherence(applied.state))


def _usable_clarification(envelope: dict, collector=None) -> dict:
    """Una domanda che facciamo deve avere risposte che funzionano (D128).

    **Il caso, visto sul campo il 3 agosto 2026.** Il modello ha chiesto per quale data
    filtrare e ha offerto quattro opzioni. Dietro *«Filtra per Data creazione»* c'era:

        {"op": "add_condition", "condition": {"ref": "crm_lead.create_date",
                                              "predicate": "within"}}
        {"op": "add_condition", "condition": {"ref": "crm_lead.date_closed",
                                              "predicate": "within"}}

    Un `within` **senza periodo**, e una condizione sulla data di chiusura dentro
    l'opzione della data di creazione. L'utente ha cliccato, D121 ha riconosciuto
    l'etichetta e ha applicato fedelmente qualcosa che non era applicabile: *«non ho
    capito»*, dopo un clic e due minuti.

    **Dove stava il buco.** D121 poggia su *«le operazioni di ogni opzione sono gia'
    nella busta»*. E' vero per le letture di **D106**, che costruiamo noi dal catalogo e
    sono valide per costruzione. Non e' vero per un chiarimento che scrive **il
    modello**: `_terminal_payload` lo memorizzava com'era, e le operazioni dentro le
    opzioni non passavano da nessuna validazione. Restavano li', invalide, finche'
    qualcuno non cliccava — e allora il difetto usciva dalla parte sbagliata della
    conversazione, come un fallimento dell'utente invece che del modello.

    **La regola.** Ogni opzione si valida con la stessa catena strutturale che valida
    una risposta, **nel momento in cui la domanda si memorizza**. Quelle che non passano
    non si mostrano. Se non ne restano almeno due, non e' un chiarimento — `01` §11.2
    dice che una sola opzione e' una conferma travestita — e il turno diventa un onesto
    *«non ho capito»* subito, mentre l'utente sta ancora leggendo la propria frase.

    Fin qui abbiamo controllato **quante** opzioni c'erano e mai **se funzionavano**.
    """
    body = envelope.get("clarification") or {}
    options = body.get("options") or []

    usable = []
    for option in options:
        operations = option.get("operations") or []
        failures = _why_unusable(operations)
        if failures:
            trace(collector, "clarification_option_refused",
                  {"label": option.get("label"), "why": [str(f) for f in failures][:2]})
            continue
        usable.append(option)

    if len(usable) < MIN_CLARIFICATION_OPTIONS:
        trace(collector, "clarification_dropped", len(usable))
        return {"dsl_version": DSL_VERSION, "outcome": "not_understood"}
    if len(usable) == len(options):
        return envelope
    return {**envelope, "clarification": {**body, "options": usable}}


def _plan_as_dict(plan) -> dict:
    """Il piano risolto, in una forma che si puo' scrivere e leggere.

    E' **la query**, non una sua descrizione: `domain`, `fields`, `order` e `limit` sono
    gli argomenti con cui l'Esecutore chiama Odoo. I periodi risolti ci sono per intero
    perche' D67 lo chiede — l'interpretazione dice *«1-31 luglio 2026»* e mai *«questo
    mese»*, e senza le date un anno fiscale non calendariale non si vedrebbe sbagliato.
    """
    return {
        "model": plan.model,
        "domain": [list(term) if isinstance(term, (list, tuple)) else term
                   for term in plan.domain],
        "fields": list(plan.fields),
        "group_by": list(plan.group_by),
        "order": plan.order,
        "limit": plan.limit,
        "view": plan.view,
        "measures": [list(measure) for measure in plan.measures],
        "resolved_periods": [list(period) for period in plan.resolved_periods],
    }


def _provider_failure(outcome: "Outcome", interpretation) -> "Outcome":
    """Il fornitore non ha risposto. E' un modo di fallire **dichiarato** (`04` §11).

    **Perche' l'esito diventa `unavailable` e non resta `not_understood`.** Sono due
    cose diverse e portano a due azioni diverse: «non ho capito» invita a riformulare, e
    riformulare non serve a niente se il modello non ha risposto — la frase era giusta e
    non l'ha letta nessuno. Il turno che scade in attesa del modello e' il caso di gran
    lunga piu' comune, ed era l'unico che arrivava all'utente con la frase sbagliata:
    `worker.execute` gia' diceva `unavailable` quando a mancare era il **profilo**, qui
    si diceva «non ho capito» quando a mancare era la **risposta**. Stessa condizione,
    due nomi, e quello sbagliato era sul percorso che si percorre sempre.

    L'interprete restituisce una busta `not_understood` perche' e' l'unica che il
    contratto gli permette di costruire senza modello: il vocabolario dell'esito del
    turno e' nostro, non del DSL, quindi puo' dire cio' che serve all'interfaccia senza
    allargare quello della busta.
    """
    outcome.outcome = "unavailable"
    outcome.provider_failed = True
    outcome.failures = list(interpretation.failures)
    return outcome


def _starting_state(interrogation) -> dict:
    """Lo stato da cui parte il turno, che dichiara sempre la propria versione.

    Una conversazione nuova ha `state_json` a `{}`, e uno stato senza `dsl_version`
    **non e' uno stato**: lo schema lo elenca fra le chiavi obbligatorie insieme a
    `target`, `limit` e `presentation`. Le altre tre le riempiono l'applicatore e la
    normalizzazione; la versione no, perche' non e' una cosa che si deduce dalle
    operazioni — e' una cosa che l'interrogazione dichiara, ed e' un suo campo.

    Senza questa riga il **primo turno che riusciva** di ogni conversazione moriva
    scrivendo lo stato, con un errore di validazione che parlava di una chiave mancante
    invece che di una risposta. Non lo vedeva nessun test perche' nessuna prova
    persisteva uno stato eseguito: si fermavano tutte all'esito.
    """
    state = interrogation.state
    if state and "dsl_version" not in state:
        state["dsl_version"] = interrogation.dsl_version
    elif not state:
        state = {"dsl_version": interrogation.dsl_version}
    return state


#: Esiti di un turno che il sistema ha buttato via senza eseguirlo. Non sono risposte:
#: la frase e' stata persa da noi, non e' che l'utente ha cambiato argomento.
SCARTATI = ("expired", "superseded", "failed")


def _pending_turn(interrogation, turn):
    """Il turno che ha lasciato una domanda in sospeso, se c'e'.

    Si guarda **solo il turno immediatamente precedente**: una domanda a cui l'utente
    non ha risposto subito non e' piu' in sospeso, ha cambiato argomento.

    **Ma un turno che abbiamo buttato via non conta come turno.** La regola serve a
    riconoscere che l'utente ha cambiato argomento; un turno scaduto in coda non dice
    niente sull'utente, dice che la sua frase e' andata persa. Contarlo faceva sparire
    la domanda in sospeso — ed e' cosi' che una risposta a un chiarimento tornava dal
    modello anche quando l'opzione corrispondeva parola per parola. Visto sul campo il
    2 agosto: il turno in mezzo era scaduto in coda, e con lui erano spariti sia D120
    sia D121.
    """
    precedenti = interrogation.turn_ids.filtered(
        lambda t: t.id < turn.id).sorted("id")
    for candidato in reversed(precedenti):
        if candidato.outcome in SCARTATI:
            continue
        return candidato if candidato.outcome == "clarification" else candidato.browse()
    return interrogation.turn_ids.browse()


def _clarification_of(precedente) -> dict:
    """Il corpo del chiarimento, comunque sia annidato nella busta."""
    if not precedente:
        return {}
    interpretazione = precedente.interpretation or {}
    return interpretazione.get("clarification") or interpretazione


def _pending_question(precedente) -> tuple[str, str] | None:
    """La frase di prima e la domanda che le e' stata posta (D120).

    Si portano due stringhe e non la conversazione intera, perche' un prompt che cresce
    con la durata della chat consuma la finestra che serve alla risposta.
    """
    domanda = _clarification_of(precedente).get("question")
    if not domanda or not precedente.utterance:
        return None
    return (precedente.utterance, domanda)


def _chosen_operations(precedente, utterance: str, state: dict) -> list | None:
    """Le operazioni dell'opzione che questa frase sceglie, se ne sceglie una (D121).

    Il confronto e' con le **etichette** e non con le operazioni, perche' l'etichetta e'
    l'unica cosa che l'utente ha visto. Il clic non ha una strada propria: scrive
    l'etichetta nella casella e la invia, quindi arriva qui esattamente come ci arriva
    chi la scrive a mano. Una sola strada, per costruzione — non perche' qualcuno si
    ricorda di tenerne allineate due.
    """
    opzioni = _clarification_of(precedente).get("options") or []
    if not opzioni:
        return None
    return alternatives.chosen(
        opzioni, utterance,
        # Le letture di D106 sono richieste intere. Un chiarimento scritto **dal
        # modello** e' completo quanto il modello l'ha fatto: un'opzione che porta la
        # sola operazione che disambigua, senza entita', non si applica a niente.
        entity_known=bool((state.get("target") or {}).get("ref")))
