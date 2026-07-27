# Nota Tecnica — Esecuzione Asincrona dell'Interpretazione
## Soluzione alla saturazione dei worker Odoo

---

| Voce | Valore |
|---|---|
| **Titolo** | Esecuzione Asincrona dell'Interpretazione — soluzione alla saturazione dei worker |
| **Tipo** | Nota tecnica decisionale (ADR) |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Risolve** | `04-architettura.md` §10.3, rischio **RA3**, decisione **D20** |
| **Piattaforma verificata** | Odoo 18.0, sorgenti presenti in `core/` |
| **Ambito** | Meccanismo di esecuzione fuori dal ciclo di richiesta, controllo del carico, notifica dell'esito |
| **Fuori ambito** | Schema dei dati, interfaccia utente dell'attesa, strategia di prompting |

> **Perché una nota separata.** Il documento di architettura identifica RA3 come rischio critico e ne dichiara la direzione, ma la direzione non è una soluzione. RA3 è l'unico rischio del progetto il cui danno ricade **fuori** dal perimetro del prodotto: degrada Odoo per utenti che non stanno usando il livello conversazionale. Merita un progetto verificato sui sorgenti della piattaforma, non un rimando.

---

## 1. Il Problema, in Numeri

### 1.1 Il meccanismo del guasto

Nel modello di esecuzione di Odoo in modalità multiprocesso, una richiesta HTTP occupa un worker per l'intera durata. L'interpretazione dura fra 0,6 e 2,5 secondi (§10.1 dell'architettura): è tempo di attesa di rete, ma il worker resta occupato ugualmente.

Con una configurazione ordinaria — `--workers=4`, quindi 4 richieste servibili contemporaneamente:

| Utenti che scrivono nello stesso momento | Effetto |
|---|---|
| 1–3 | Nessuno |
| 4 | Tutti i worker occupati; **ogni altra richiesta a Odoo si accoda** |
| 8 | Attesa raddoppiata; l'ERP appare bloccato a tutti |
| 12+ | Timeout a cascata; richieste legittime uccise da `--limit-time-real` |

**Quattro utenti che scrivono una frase contemporaneamente sono sufficienti a fermare l'ERP per tutti gli altri.** Non è uno scenario di carico estremo: è un lunedì mattina.

### 1.2 Perché non si risolve aumentando i worker

Tre ragioni, tutte dirimenti.

**Il rapporto è sfavorevole.** Un worker Odoo consuma memoria in modo significativo. Dimensionare i worker sull'attesa di rete significa pagare memoria per processi che non fanno nulla se non attendere una risposta HTTP.

**Non elimina la condivisione.** Anche con 16 worker, l'interpretazione e le operazioni ERP continuano a contendersi la stessa risorsa. Un picco conversazionale degrada comunque il lavoro di chi sta emettendo fatture. L'isolamento non è una questione di quantità.

**Il carico è impredicibile.** Dipende dalla latenza di un servizio esterno che non controlliamo. Un rallentamento del fornitore triplica il tempo di occupazione dei worker senza alcun preavviso. Dimensionare per il caso peggiore di un sistema esterno non è dimensionare.

> **Conclusione.** Il problema non è la capacità: è che **il livello conversazionale e l'ERP condividono un pool di risorse che non deve essere condiviso.** La soluzione deve separarli, non ampliarli.

---

## 2. Vincoli di Piattaforma — Verificati sui Sorgenti

Le decisioni che seguono poggiano su comportamenti verificati nei sorgenti Odoo 18 presenti in `core/`, non su assunzioni. Sono riportati con il riferimento esatto perché ciascuno vincola il progetto.

### 2.1 I fatti utilizzabili

**F1 — `ir.cron._trigger()` produce una sveglia immediata, non un'attesa di un minuto.**

```
ir_cron.py:711   cr.execute(SQL("SELECT %s('cron_trigger', %s)", …))   → pg_notify
server.py:499    cr.execute("LISTEN cron_trigger")
server.py:1234   select.select([self.wakeup_fd_r, self.dbcursor._cnx], [], [], interval)
```

Il worker cron è in attesa su `select()` sulla connessione PostgreSQL con `LISTEN cron_trigger` attivo. Un `_trigger()` invia `pg_notify` in post-commit e **risveglia il worker cron nell'ordine dei millisecondi**.

È il fatto che rende praticabile una coda basata su cron per un'interazione conversazionale. La convinzione diffusa che il cron di Odoo abbia una granularità di un minuto riguarda il campo `interval`, non i trigger.

**F2 — Il worker cron è un processo distinto dai worker HTTP.**

`server.py:1215` definisce `WorkerCron` come classe di worker autonoma. In modalità prefork, i processi cron sono separati da quelli HTTP: **il lavoro svolto su un cron non sottrae capacità alle richieste web.** È esattamente l'isolamento richiesto da §1.2.

**F3 — Il bus è servito dal worker gevent, non dai worker HTTP.**

```
bus.py:106       def _sendone(self, target, notification_type, message)
server.py:683    self.port = config['gevent_port']
```

Le notifiche websocket sono servite da un processo dedicato. **Un client in attesa del risultato non occupa alcun worker HTTP**, a differenza di qualunque soluzione basata su interrogazione periodica.

### 2.2 I vincoli da rispettare

**V-A — Un record `ir.cron` ammette una sola esecuzione concorrente nell'intero cluster.**

```
ir_cron.py:140   job = cls._acquire_one_job(cron_cr, job_id)
ir_cron.py:145   "another worker is processing job %s, skip"
```

L'acquisizione è protetta da un blocco per riga. Due worker cron non eseguono mai lo stesso job. **Un solo `ir.cron` dà concorrenza 1**: è il vincolo che determina la forma della soluzione (§3.3).

**V-B — I processi cron sono pochi, e condivisi.**

```
config.py:321    --max-cron-threads   my_default=2
```

Due processi cron predefiniti, condivisi con tutti i cron di business dell'installazione. Occuparne uno stabilmente significa dimezzare la capacità di esecuzione delle attività pianificate del cliente.

**V-C — Il tempo di esecuzione di un cron è limitato.**

```
config.py:364    --limit-time-real-cron   my_default=-1     (-1 → eredita --limit-time-real)
config.py:361    --limit-time-real        my_default=120
server.py:461    if config['limit_time_real_cron'] and config['limit_time_real_cron'] > 0
```

Con la configurazione predefinita un ciclo di cron viene interrotto dopo **120 secondi**. Un dispatcher che lavori a lotti deve restare ampiamente al di sotto di questa soglia e cedere il controllo regolarmente.

**V-D — I worker HTTP vengono riciclati.**

```
config.py:368    --limit-request   my_default=65536
```

Un worker HTTP viene terminato e sostituito dopo un numero prefissato di richieste. **Qualunque elaborazione affidata a un thread interno a un worker HTTP può essere interrotta a metà**, senza garanzie. È la ragione tecnica per cui la soluzione più immediata — un thread in background nel worker che ha ricevuto la richiesta — è inaccettabile e non compare fra le alternative valutate.

### 2.3 Sintesi dei vincoli

| | Vincolo | Conseguenza progettuale |
|---|---|---|
| F1 | Trigger → sveglia immediata | Una coda su cron è compatibile con l'interattività |
| F2 | Cron su processi separati | L'isolamento richiesto è ottenibile senza servizi nuovi |
| F3 | Bus su processo gevent | L'attesa del client non costa worker HTTP |
| V-A | 1 cron = 1 esecuzione concorrente | La concorrenza va ottenuta **dentro** il job, non moltiplicando i job |
| V-B | 2 processi cron, condivisi | Il job deve cedere il controllo a intervalli brevi |
| V-C | 120 s di limite | Cicli a lotti brevi, con ri-trigger |
| V-D | Worker HTTP riciclati | Nessuna elaborazione in thread dentro un worker HTTP |

---

## 3. La Soluzione

### 3.1 Struttura in tre livelli

```
┌─ LIVELLO 1 ── ACCETTAZIONE ─────────────── worker HTTP, ~10 ms ─┐
│  crea il turno in stato "pending"                                │
│  applica il controllo di carico  (§4)                            │
│  chiama cron._trigger()                                          │
│  risponde con l'identificativo del turno → WORKER LIBERATO       │
└──────────────────────────────────────────────────────────────────┘
                    │ pg_notify('cron_trigger')  [post-commit]
                    ▼
┌─ LIVELLO 2 ── ESECUZIONE ──────── processo cron, fuori dagli HTTP ┐
│  Dispatcher: acquisisce un lotto di turni                         │
│  li elabora in concorrenza con un pool di thread                  │
│  ogni thread: Interprete → Validatore → … → Esecutore             │
│  persiste l'esito, poi commit                                     │
└───────────────────────────────────────────────────────────────────┘
                    │ bus._sendone(...)
                    ▼
┌─ LIVELLO 3 ── NOTIFICA ─────────── processo gevent, non HTTP ─────┐
│  websocket → il client aggiorna l'interfaccia                     │
│  nessun worker HTTP occupato durante l'attesa                     │
└───────────────────────────────────────────────────────────────────┘
```

**Proprietà risultante:** in tutto il ciclo di vita di un turno, i worker HTTP sono occupati per circa 10 millisecondi in accettazione e per nulla durante l'attesa. Il tempo dell'interpretazione — la quota dominante — è interamente speso su processi che non servono richieste web.

### 3.2 Livello 1 — Accettazione

Il worker HTTP compie tre operazioni e si libera:

1. verifica i limiti di carico (§4) e, se superati, **rifiuta subito** con un messaggio esplicito;
2. crea il record del turno in stato `pending`;
3. invoca `_trigger()` sul cron del dispatcher.

**La correttezza dipende da una proprietà verificata:** `_trigger()` registra la notifica in post-commit (`ir_cron.py:701`). La sveglia del worker cron arriva quindi **dopo** che il turno `pending` è visibile in banca dati. Senza questa garanzia si aprirebbe una corsa critica in cui il dispatcher si sveglia e non trova nulla, e il turno resterebbe fermo fino al risveglio successivo — fino a un minuto dopo.

### 3.3 Livello 2 — Il Dispatcher

Il vincolo **V-A** determina la forma della soluzione: un record `ir.cron` ammette **una sola esecuzione concorrente**. Da qui la scelta centrale:

> **Un solo cron, che funge da dispatcher, e la concorrenza si ottiene con un pool di thread al suo interno.**

**Perché i thread sono adeguati qui — e non lo sarebbero altrove.** Il lavoro è quasi interamente attesa di rete: il thread che attende la risposta del fornitore non consuma CPU e non contende il *global interpreter lock*. Un pool di 8 thread che attendono 8 risposte HTTP costa quanto un thread che ne attende una. È il caso d'uso per cui i thread sono lo strumento corretto.

```
DISPATCHER (un solo ir.cron)

  inizio_ciclo = adesso
  finché  adesso − inizio_ciclo < CICLO_MAX  e  esistono turni pending:

      lotto = acquisisci fino a POOL turni pending
              SELECT … FOR UPDATE SKIP LOCKED
              stato → "running"
              commit                          ← il lotto è prenotato

      esegui il lotto in parallelo con un pool di POOL thread
          ogni thread:
              cursore proprio        odoo.registry(db).cursor()
              ambiente con l'identità dell'UTENTE RICHIEDENTE
              catalogo → interprete → validatore → applicatore
                       → risolutore → esecutore
              persiste stato ed esito, poi commit
              bus._sendone(canale utente, esito)
              in caso di eccezione: turno → "failed", commit, notifica

      attendi il completamento del lotto

  se restano turni pending:
      cron._trigger()        ← cede il processo cron e riprende subito
```

### 3.4 Le quattro proprietà del ciclo

**Cede il controllo regolarmente.** `CICLO_MAX` è fissato a **15 secondi**, molto al di sotto del limite di 120 (**V-C**), e a ogni scadenza il dispatcher si ri-triggera. Ne discende che un processo cron non resta occupato in modo continuativo e i cron di business dell'installazione non subiscono starvation (**V-B**).

**Prenota prima di elaborare.** L'acquisizione del lotto con passaggio a `running` viene confermata **prima** dell'elaborazione. Un'interruzione del processo lascia turni in `running` senza esecutore, che il recupero (§5.3) rimette in coda: è preferibile a turni in `pending` presi due volte.

**Ogni thread ha il proprio cursore e la propria transazione.** Il fallimento di un turno non annulla gli altri del lotto. È la ragione per cui non si può riusare il cursore del cron.

**Ogni thread opera con l'identità dell'utente richiedente.** Il vincolo V2 vale anche qui, e va detto perché il contesto asincrono è precisamente il luogo in cui la tentazione di eseguire con privilegi elevati diventa concreta: il codice non è più dentro una richiesta autenticata, e l'utente va ricostruito dal turno. **Il dispatcher non esegue mai con privilegi propri.**

### 3.5 Livello 3 — Notifica

A esito prodotto, il thread invia la notifica sul bus verso il canale dell'utente. Il websocket è servito dal processo gevent (**F3**): il client resta in attesa **senza occupare alcun worker HTTP**.

Questo è ciò che distingue la soluzione da un'architettura a interrogazione periodica: con un'interrogazione ogni secondo, dieci utenti in attesa produrrebbero dieci richieste HTTP al secondo — reintroducendo su scala minore il problema che si voleva risolvere.

**Ricaduta sull'esperienza.** Il canale di notifica consente anche di comunicare l'avanzamento — *accettata*, *in interpretazione*, *in esecuzione* — soddisfacendo il requisito di attesa leggibile (§10.5 del documento di visione) senza alcun meccanismo aggiuntivo.

**Percorso di ripiego.** Se il websocket non è disponibile (rete d'impresa restrittiva, canale non interattivo), il client interroga lo stato del turno con frequenza decrescente. È un ripiego, non il funzionamento normale, e va misurato: una quota elevata di sessioni in ripiego riporta il carico sui worker HTTP.

---

## 4. Controllo del Carico

### 4.1 Perché la coda, da sola, non risolve nulla

Una coda senza limiti non elimina la saturazione: **la sposta e la rende invisibile.**

Il sistema smette di rallentare l'ERP — che è l'obiettivo — ma inizia ad accumulare turni che nessuno elaborerà in tempo utile. L'utente attende quaranta secondi una risposta che ha smesso di aspettare dopo dieci, il fornitore viene interrogato per richieste ormai prive di destinatario, e il costo variabile viene speso su lavoro inutile.

**Il controllo del carico non è un complemento del disegno: ne è la metà.** Una coda senza limiti è un guasto rinviato.

### 4.2 I cinque limiti

| | Limite | Valore proposto | Comportamento al superamento |
|---|---|---|---|
| **L1** | Interpretazioni in volo per sessione | **1** | La nuova richiesta sostituisce quella in attesa, oppure viene rifiutata |
| **L2** | Concorrenza globale | **= dimensione del pool** | Applicato per costruzione: il pool è il limite |
| **L3** | Profondità della coda | **3 × pool** | **Rifiuto immediato** in accettazione, con messaggio esplicito |
| **L4** | Età massima del turno | **30 secondi** | Turno scartato senza essere interpretato |
| **L5** | Richieste per utente al minuto | **20** | Rifiuto con indicazione della natura temporanea |

**L1 merita una nota.** Una persona non pone due domande contemporaneamente: se ne scrive una seconda mentre la prima è in corso, ha cambiato idea. Consentire l'accodamento produrrebbe due interpretazioni di cui la prima è già priva di interesse — costo sprecato e, peggio, un risultato che compare e viene subito sostituito. Il comportamento corretto è annullare la precedente.

**L4 è il limite più trascurato e il più utile.** Un turno accodato da più di trenta secondi ha perso il proprio destinatario: l'utente ha rinunciato, riformulato o cambiato pagina. Interpretarlo costa denaro e occupa il pool a scapito di richieste vive. **Scartare i turni scaduti è ciò che consente alla coda di recuperare da un picco anziché accumulare ritardo in modo permanente.**

**L3 realizza il rifiuto esplicito.** Sotto un picco imprevisto, il sistema deve dire *"in questo momento c'è troppo lavoro, riprova fra qualche secondo"* anziché accettare e deludere. Un rifiuto immediato e comprensibile è un'esperienza migliore di un'attesa che non finisce, ed è anche l'unico comportamento che protegge chi è già in coda.

### 4.3 Separazione dei carichi

Non tutte le interpretazioni sono interattive. Il ricalcolo del corpus di valutazione (§13.4 dell'architettura) può richiedere migliaia di interpretazioni.

> **Regola: il carico differito non usa mai il pool interattivo.**

Il ricalcolo del corpus gira su un dispatcher separato, con il proprio cron, il proprio pool ridotto e nessun requisito di latenza — idealmente fuori dagli orari di lavoro. Un corpus in esecuzione non deve poter rallentare un utente che sta scrivendo, e senza questa separazione lo farebbe sistematicamente, perché è il carico più massiccio che il sistema genera.

### 4.4 Protezione dal fornitore non disponibile

Un circuito di protezione sull'Adattatore di Fornitore (§8.2 dell'architettura): superata una soglia di fallimenti consecutivi, il dispatcher smette di tentare, rifiuta immediatamente i nuovi turni con un messaggio esplicito e riprende gradualmente.

Senza questo meccanismo, un guasto del fornitore riempie la coda di turni destinati a fallire dopo il tempo massimo di attesa, saturando il pool per minuti dopo che il problema è già stato risolto.

---

## 5. Esecutore Dedicato e Resilienza

### 5.1 Quando il dispatcher su cron non basta

La soluzione di §3 non introduce alcun servizio nuovo, coerentemente con §14.5 dell'architettura. Ha però un limite dichiarato: occupa uno dei due processi cron predefiniti (**V-B**), e la sua capacità è quella di un solo pool.

Tre situazioni la rendono insufficiente:

- **volume elevato**: decine di utenti conversazionali contemporanei in modo continuativo;
- **cron di business intensi**: l'installazione usa i processi cron per elaborazioni proprie e non può cederne uno;
- **isolamento richiesto**: il cliente esige che il carico di interpretazione non tocchi in alcun modo l'istanza applicativa.

### 5.2 L'esecutore dedicato

**Stesso codice, entrypoint diverso.** Un'istanza Odoo dedicata, sulla stessa banca dati, configurata per non servire richieste web ed eseguire soltanto processi cron:

```
odoo --no-http --max-cron-threads=N       (config.py:145, config.py:321)
```

In `docker-compose` è un servizio aggiuntivo che riusa l'immagine già costruita: nessun nuovo artefatto, nessun nuovo protocollo, nessuna nuova modalità di guasto significativa.

L'istanza dedicata riceve la stessa notifica `pg_notify` — il canale `cron_trigger` è per banca dati, non per processo — ed esegue lo stesso dispatcher. **La commutazione fra le due configurazioni non richiede modifiche al codice.**

| | Dispatcher su cron condiviso | Esecutore dedicato |
|---|---|---|
| Servizi aggiuntivi | Nessuno | Uno |
| Isolamento dall'ERP | Buono (processo cron separato) | Completo |
| Capacità | Un pool | Scalabile per **record dispatcher** (vedi nota) |
| Impatto sui cron di business | Occupa un processo su due | Nessuno |
| Configurazione consigliata per | Prima release, installazioni piccole e medie | Volumi elevati, clienti con isolamento contrattuale |

**Raccomandazione:** avviare con il dispatcher su cron condiviso, elevando `--max-cron-threads` da 2 a **4** per lasciare margine ai cron di business. Passare all'esecutore dedicato sulla base dei dati — profondità della coda, tempo di attesa, contesa con i cron di business — non per preferenza.

> **Nota sulla capacità — come si scala davvero.** Aggiungere istanze **non** aggiunge capacità: per **V-A** un record `ir.cron` ammette una sola esecuzione concorrente nell'intero cluster, quindi due istanze competono per lo stesso record e una salta. La capacità si aggiunge con **N record dispatcher distinti**, ciascuno con il proprio pool, collocabili su una o più istanze. È già compatibile con §3.3 senza modifiche: l'acquisizione del lotto usa `FOR UPDATE SKIP LOCKED`, che rende sicura l'estrazione concorrente da parte di dispatcher diversi.
>
> Capacità ≈ `N_dispatcher × POOL`, entro il tetto di connessioni: `(worker_http) + (max_cron_threads) + (N_dispatcher × POOL) ≤ 0,8 × db_maxconn`.
>
> *(Delibera del 27 luglio 2026 — `00-registro-decisioni.md` §5.1 e §6.4.)*

### 5.3 Recupero dei turni orfani

Un processo cron interrotto — riavvio, aggiornamento, guasto — lascia turni in stato `running` senza esecutore.

Un cron di manutenzione a bassa frequenza rimette in `pending` i turni in `running` da più del tempo massimo plausibile, con un contatore di tentativi: al secondo fallimento il turno passa a `failed` e l'utente riceve un messaggio.

**Il contatore è indispensabile.** Senza di esso, un turno che provoca sistematicamente il fallimento del processo verrebbe ripreso all'infinito, riproducendo il guasto a ogni ciclo. È la modalità di guasto più fastidiosa delle code costruite senza limite di tentativi.

### 5.4 Idempotenza

Un turno può essere elaborato due volte in condizioni eccezionali: la doppia elaborazione deve produrre lo stesso risultato, non due.

Le proprietà necessarie esistono già nel disegno: gli **stati sono immutabili** e ogni applicazione ne produce uno nuovo (§9.2 dell'architettura); l'applicazione delle operazioni è **serializzata sulla sessione** e una busta calcolata su uno stato non più corrente viene respinta (§9.6). Il turno registra lo stato prodotto: se è già presente, la seconda elaborazione non riparte.

Vale la pena notare che nessuna di queste proprietà è stata introdotta per l'esecuzione asincrona: erano già lì per ragioni di correttezza. L'idempotenza è un beneficio che si ottiene senza costo aggiuntivo — segnale che l'impianto è coerente.

---

## 6. Parametri

| Parametro | Valore proposto | Note |
|---|---|---|
| Dimensione del pool | **8** | Attesa di rete: i thread costano poco. Da tarare sui dati |
| `CICLO_MAX` | **15 s** | Molto sotto i 120 s di **V-C**; cede il processo cron regolarmente |
| Dimensione del lotto | = pool | Nessun beneficio nell'acquisire più di quanto si possa eseguire |
| `--max-cron-threads` | **4** | Da 2 predefiniti; lascia margine ai cron di business (**V-B**) |
| L1 in volo per sessione | 1 | §4.2 |
| L3 profondità coda | 3 × pool = 24 | Rifiuto in accettazione oltre questa soglia |
| L4 età massima | 30 s | Turni più vecchi scartati senza interpretazione |
| L5 richieste al minuto per utente | 20 | Protezione da automatismi e da usi anomali |
| Tentativi di recupero | 2 | Poi `failed` (§5.3) |
| Soglia del circuito di protezione | 5 fallimenti consecutivi | Riapertura graduale |

**Nessuno di questi valori è una costante di progetto.** Sono punti di partenza ragionevoli formulati prima di disporre di dati reali, e vanno rivisti dopo le prime prove di carico (§7) e dopo il primo periodo di uso reale. Mantenerli quando i dati li smentiscono sarebbe peggio che non averli fissati.

---

## 7. Collaudo

### 7.1 La prova che conta

Il rischio RA3 riguarda l'ERP, non il livello conversazionale. La prova decisiva misura quindi **l'impatto sugli utenti che non stanno usando il prodotto**:

> Con N utenti conversazionali attivi in modo continuativo, il tempo di risposta di Odoo per un utente ordinario — che apre una fattura, salva un ordine, cerca un cliente — **non deve peggiorare in modo misurabile**.

È il criterio di accettazione. Un livello conversazionale rapido su un ERP rallentato è un fallimento.

### 7.2 Prove richieste

| Prova | Condizione | Criterio |
|---|---|---|
| **Isolamento** | 20 utenti conversazionali continui + traffico ERP ordinario | Latenza ERP invariata entro il margine di misura |
| **Occupazione dei worker** | Sotto carico conversazionale | Nessun worker HTTP occupato oltre l'accettazione |
| **Picco e recupero** | 100 richieste in 5 secondi | Rifiuti espliciti oltre L3; coda smaltita; nessun accumulo permanente |
| **Scadenza** | Fornitore rallentato a 10 s | I turni oltre L4 scartati; il sistema non accumula ritardo |
| **Guasto del fornitore** | Fornitore non raggiungibile | Circuito aperto entro la soglia; messaggi espliciti; Odoo intatto |
| **Interruzione del processo** | Processo cron terminato durante un lotto | Turni orfani recuperati; nessuno perso in silenzio |
| **Cron di business** | Attività pianificate del cliente attive | Nessuna starvation: eseguite entro i tempi attesi |

**La prova sui cron di business è quella che verrà dimenticata**, ed è l'unica che verifica il vincolo V-B. Un dispatcher che monopolizza i processi cron non fa fallire il prodotto: fa fallire le fatture elettroniche del cliente, e la causa non sarà evidente.

### 7.3 Indicatori da sorvegliare in esercizio

Profondità della coda (istantanea e al 95° percentile), tempo di attesa prima dell'interpretazione, turni scartati per scadenza, rifiuti per soglia, tentativi di recupero, aperture del circuito di protezione, quota di sessioni in ripiego sull'interrogazione periodica.

Il primo indicatore è quello che anticipa tutti gli altri: **una coda che non torna a zero fra un picco e l'altro è un sistema sottodimensionato**, e va rilevato prima che se ne accorgano gli utenti.

---

## 8. Alternative Valutate e Scartate

| Alternativa | Perché scartata |
|---|---|
| **Aumentare i worker HTTP** | Non elimina la condivisione delle risorse; costo in memoria; impossibile dimensionare sulla latenza di un servizio esterno (§1.2) |
| **Thread in background nel worker HTTP** | **V-D**: il riciclo del worker (`--limit-request`) può interromperlo a metà, senza garanzie. Inaccettabile a prescindere dal resto |
| **Più record `ir.cron` per ottenere concorrenza** | **V-A** dà concorrenza 1 per record, ma **V-B** limita a 2 i processi cron: la concorrenza resterebbe 2 e i cron di business ne sarebbero privati |
| **Coda esterna** (Redis, RabbitMQ, Celery) | Un servizio in più da gestire, aggiornare e mettere in sicurezza per dieci anni, in cambio di ciò che `pg_notify` + `ir.cron` già forniscono (**F1**, **F2**) |
| **`queue_job` OCA** | Soluzione matura, ma introduce una dipendenza esterna significativa e un modello concettuale proprio per un caso d'uso ristretto e ben definito. Da riconsiderare se il progetto adottasse comunque il pacchetto OCA per altre ragioni |
| **Interrogazione periodica dal client** | Reintroduce carico sui worker HTTP proprio durante l'attesa: dieci utenti in attesa producono dieci richieste al secondo (§3.5) |
| **Interpretazione sincrona con timeout breve** | Non risolve nulla: il worker resta occupato per tutto il timeout, e le richieste vengono perse |
| **Esecutore dedicato fin dalla prima release** | Corretto ma prematuro: introduce un servizio quando il dispatcher su cron è sufficiente per le installazioni iniziali. Rinviato con percorso di adozione già pronto (§5.2) |

**Sull'ultima riga.** La differenza fra "rinviato" e "escluso" è sostanziale: l'esecutore dedicato non richiede modifiche al codice ma solo una configurazione diversa. È un rinvio senza debito.

---

## 9. Rischi Residui

### RE1 — Il dispatcher affama i cron di business
**Impatto.** Alto e **fuori dal perimetro del prodotto**: le attività pianificate del cliente ritardano, con cause non evidenti.
**Mitigazione.** `CICLO_MAX` a 15 s con ri-trigger; `--max-cron-threads` portato a 4; prova dedicata in §7.2.
**Segnale.** Ritardi nell'esecuzione dei cron di business correlati ai picchi conversazionali.

### RE2 — I limiti di carico vengono allentati sotto pressione
**Impatto.** Alto: un rifiuto esplicito viene percepito come un difetto, e la reazione istintiva è alzare le soglie. Così la coda torna a crescere senza limiti e il guasto si sposta più avanti, dove è meno diagnosticabile.
**Mitigazione.** I limiti sono parametri sorvegliati, non costanti nascoste; la profondità della coda è monitorata; ogni modifica delle soglie è motivata dai dati.
**Segnale.** Soglie alzate senza una prova di carico a sostegno.

### RE3 — Il ripiego sull'interrogazione periodica diventa la norma
**Impatto.** Medio-alto: se il websocket non è utilizzabile presso una quota rilevante di clienti, il carico rientra dalla porta di servizio.
**Mitigazione.** Misurare la quota di sessioni in ripiego; frequenza di interrogazione decrescente; considerarla una condizione da correggere, non una configurazione accettabile.
**Segnale.** Quota di sessioni in ripiego superiore a pochi punti percentuali.

### RE4 — Il pool viene dimensionato come se il lavoro fosse di calcolo
**Impatto.** Medio: un pool di 2 thread "per prudenza" limiterebbe artificiosamente il sistema; un pool di 100 esaurirebbe le connessioni alla banca dati.
**Nota.** Il limite reale non è la CPU ma il **numero di connessioni PostgreSQL**: ogni thread ne usa una. Il pool va dimensionato tenendo conto di `db_maxconn` e del consumo degli altri processi.
**Mitigazione.** Taratura sui dati; sorveglianza dell'uso delle connessioni.

### RE5 — Il carico differito rientra nel pool interattivo
**Impatto.** Alto quando accade: il ricalcolo del corpus è il carico più massiccio che il sistema genera.
**Mitigazione.** Dispatcher separato con cron proprio (§4.3); verifica automatica che il ricalcolo non usi il pool interattivo.
**Segnale.** Picchi di latenza interattiva coincidenti con le esecuzioni del corpus.

---

## 10. Decisioni Richieste

Numerazione in continuità con i documenti precedenti (D1–D26). Sostituiscono e specificano **D20**.

| # | Decisione | Raccomandazione |
|---|---|---|
| **D20a** | Accettazione immediata + `ir.cron._trigger()` + notifica su bus (§3) | **Adottare** — risolve RA3 senza servizi aggiuntivi |
| **D20b** | Un solo cron dispatcher con pool di thread interno, `CICLO_MAX` 15 s (§3.3) | **Adottare** — imposto da **V-A** e **V-B** |
| **D20c** | I cinque limiti di carico di §4.2, con rifiuto esplicito e scadenza dei turni | **Adottare** — senza questi, la coda rinvia il guasto anziché risolverlo |
| **D20d** | Carico differito su dispatcher separato (§4.3) | **Adottare** |
| **D20e** | `--max-cron-threads` da 2 a 4 (§6) | **Adottare** — protegge i cron di business |
| **D20f** | Esecutore dedicato come opzione di configurazione, non nella prima release (§5.2) | **Adottare** — rinvio senza debito |
| **D27** | Prova di isolamento (§7.1) come criterio di accettazione della prima release | **Adottare** — è la sola prova che verifica RA3 |

**D20c è la decisione che verrà messa in discussione per prima**, perché produce rifiuti visibili all'utente. Vale la pena fissarne ora la ragione: senza limiti, il sistema smette di rallentare l'ERP e comincia ad accumulare lavoro che nessuno riceverà. Il guasto non scompare — diventa più difficile da diagnosticare.

---

## 11. Effetti sui Documenti Esistenti

| Documento | Modifica |
|---|---|
| `04-architettura.md` §10.3 | Sostituito dal rimando a questa nota; la direzione era corretta, il meccanismo è qui |
| `04-architettura.md` §16 RA3 | Mitigazione aggiornata con il riferimento a questa nota |
| `04-architettura.md` §17 D20 | Articolata in D20a–D20f |
| `04-architettura.md` §14.5 | Confermato: nessun servizio nuovo nella prima release; l'esecutore dedicato resta un'opzione di configurazione |

---

## Chiusura

Il rischio RA3 non si risolve con più capacità: si risolve **separando due carichi che non devono condividere risorse.**

La piattaforma fornisce già tutto il necessario, e i sorgenti lo confermano: `pg_notify` risveglia il worker cron in millisecondi (**F1**), i processi cron sono distinti da quelli HTTP (**F2**), il bus è servito dal processo gevent (**F3**). Non serve un'infrastruttura aggiuntiva: serve usare correttamente quella esistente.

La parte che decide l'esito non è però il meccanismo di coda — è il **controllo del carico**. Una coda senza limiti sposta la saturazione dai worker alla coda stessa, dove è meno visibile e più difficile da diagnosticare. I cinque limiti di §4.2, e in particolare la scadenza dei turni, sono ciò che permette al sistema di **recuperare** da un picco anziché accumulare ritardo in modo permanente.

Il criterio di verifica finale resta quello di §7.1, e riflette la natura del rischio: un utente che sta emettendo una fattura non deve accorgersi che qualcun altro sta conversando con l'ERP.

---

*Fine del documento.*
