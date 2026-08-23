# RESTART — come riprendere il lavoro architetturale

> **Ultimo aggiornamento:** 2026-08-23
> **Motivo dell'interruzione:** —
> **Stato:** `A01`-`A14` completi, **`A17` e `A18` completi**.
> **⚠️ DEVIAZIONE DALL'ORDINE, decisa dal committente il 2026-08-23:**
> **`A15` (Deployment) e `A16` (CI/CD) sono gli unici documenti di Level A che mancano.**
> **Si riprendono SOLO su indicazione esplicita del committente.** Il gate di Level A
> **non può chiudersi** finché mancano: `A17` e `A18` gli hanno entrambi mandato lavoro.
> **`A15` e `A16` si riprendono SOLO quando il committente lo decide esplicitamente.**
> Non riprenderli di iniziativa: non sono dimenticati, sono rimandati per scelta.

---

## 1. Cosa leggere per ripartire, in quest'ordine

```text
1. questo file (RESTART.md)          → il metodo e lo stato
2. EXECUTION_LEDGER.md               → quale documento tocca adesso
3. ARCHITECTURE_STATE.md             → tutte le decisioni prese, vincolanti
4. research-log.md                   → i FATTI verificati + il backlog di ricerca
5. il prompt del documento TODO      → solo quello, letto a sezioni
```

**Non serve rileggere i documenti già prodotti.** `ARCHITECTURE_STATE.md` è la loro sintesi
vincolante ed è mantenuto aggiornato dopo ogni documento.

---

## 2. Cosa è stato chiesto

Eseguire, nell'ordine:

1. `ai/prompt/architecture-convetion.txt` — la convenzione di lavoro (lingua, stile, rigore);
2. `ai/prompt/research-context.txt` — come usare `/research` (contesto, non architettura);
3. `ai/prompt/master-architecture-entrypoint.txt` — il processo: Level A → B → C, gate,
   falsificazione, sintesi finale in `FINAL_ARCHITECTURE.md`.

Con un vincolo aggiunto dall'utente: **costruire in modo da non andare mai in API Error o
bloccarsi.**

---

## 3. Il metodo adottato, e perché

### 3.1 Il problema

35 prompt, da 32 a 85 KB ciascuno (~1,7 MB in totale). Ogni prompt chiede un documento con
40-50 sezioni. **Non entra in una singola finestra di contesto.**

### 3.2 Il primo tentativo, e perché è fallito

Il primo approccio — scrivere tutto nel thread principale — è andato in API Error. La causa
**non** era il context window: era il **budget di output per singola risposta**. Una `Write`
da ~20.000 caratteri (~7.000 token) più il thinking arrivava al tetto.

### 3.3 Il metodo attuale — modalità ibrida

Scelta dall'utente fra tre opzioni.

| Chi scrive | Quali documenti | Perché |
|---|---|---|
| **Thread principale** | `A01`, `A02`, `A03`, `A04`, `A13`, **tutti i gate di livello**, `FINAL_ARCHITECTURE.md` | prendono le decisioni **fondanti**: vanno scritti da chi ha in testa tutto lo stato |
| **Subagent isolato** | tutti gli altri (`A05`-`A12`, `A14`-`A18`, Level B, Level C) | **consumano** decisioni già prese. Il prompt (32-85 KB) non entra mai nel contesto principale |

### 3.4 Contromisure contro il blocco

Da applicare **sempre**, anche dopo il restart:

1. **Blocchi di scrittura da ~150-200 righe** per chiamata. Mai un documento intero in una
   `Write`. Tecnica: `Write` iniziale che termina con un marcatore `<!-- NEXT -->`, poi
   `Edit` successive che sostituiscono il marcatore con nuovo contenuto **più il marcatore**.
   L'ultima `Edit` lo rimuove.
2. **I prompt lunghi non si leggono interi.** Prima si mappa la struttura
   (`grep -n "^[0-9]\{1,2\}\. [A-Z]"`), poi si leggono solo le sezioni che dettano requisiti,
   con `offset`/`limit`.
3. **Non si rileggono mai i documenti prodotti.** Vale `ARCHITECTURE_STATE.md`.
4. **Un documento alla volta**, come impone il Master Entrypoint §4. Mai subagent in
   parallelo.
5. **Lo stato si aggiorna con `Edit` puntuali**, mai riscrivendo i file interi.

---

## 4. Stato di avanzamento

### Fatti

| Doc | File | Chi | Decisione centrale |
|---|---|---|---|
| `A01` | `level-a/01_ARCHITECTURE_PRINCIPLES.md` | thread | un artefatto, tre ruoli di processo. Separare ciò che è **caro da cambiare** (forma dei dati) da ciò che è economico (motori, librerie) |
| `A02` | `level-a/02_CONTROL_PLANE.md` | thread | il **Config Snapshot**: la configurazione si risolve una volta all'avvio del run e si congela. Il Control Plane smette di essere dipendenza critica |
| `A03` | `level-a/03_GOVERNANCE_POLICY.md` | thread | autorità = **intersezione di 5 insiemi**; PDP come **funzione pura**; decisione = effetto **+ obbligazioni** |
| `A04` | `level-a/04_AGENT_RUNTIME.md` | thread | loop agentico su passi deterministici; **si scrive prima di agire**; `UNCERTAIN` invece di indovinare |
| `A05` | `level-a/05_MODEL_INFERENCE.md` | subagent | due serving profile un contratto; riproducibilità dell'**evidenza**, non dell'output |
| `A06` | `level-a/06_TOOL_ARCHITECTURE.md` | subagent | un tool = **una decisione di autorizzazione**; nessun argomento di tool può essere un programma |
| `A07` | `level-a/07_KNOWLEDGE_DATA.md` | subagent | due percorsi (dato live via tool, documenti indicizzati); **embedding su CPU** → `AS-08` confermata e `ADR-039` salvo; autorizzazione del retrieval **dentro la query** |
| `A08` | `level-a/08_MEMORY.md` | subagent | il riassunto del journal è **generato da codice, mai dal modello**; la memoria **non contiene fatti di dominio**; il PDP non legge mai la memoria (`INV-12`) |
| `A09` | `level-a/09_IDENTITY_AUTHZ.md` | subagent | **dual principal**: chi agisce è la coppia `(agent, per conto di chi)` e l'autorità è l'**intersezione**; si congela il tetto, si rilegge l'autorità viva a ogni step |
| `A10` | `level-a/10_AGENT_COMMUNICATION.md` | subagent | **niente comunicazione agent→agent Day-1**, ma le 4 colonne di lineage si scrivono subito perché dopo è impossibile aggiungerle. `DEF-07` chiusa |
| `A11` | `level-a/11_EVENTING_WORKFLOW.md` | subagent | **nessun engine di durable execution**: il motore è il loop su PostgreSQL. Il tempo attivo è un **contatore**, non un intervallo; il ledger lo consuma un **trigger di database** |
| `A12` | `level-a/12_OBSERVABILITY_EVAL.md` | subagent | 63 metriche mandate dai documenti precedenti, **63 coperte**. Il prompt **non si conserva: si ricostruisce**. Tre piani separati: telemetria, audit, evaluation |
| `A13` | `level-a/13_SECURITY.md` | **thread** | la sicurezza **è l'invariante**, non il filtro. Chiude `ASI09` (l'approvazione umana come superficie d'attacco): si approva un `ActionBinding` **tipizzato**, mai una narrazione |
| `A14` | `level-a/14_DATA_GOVERNANCE.md` | subagent | `FieldScope`, il terzo ambito che mancava. La cancellazione non tocca l'audit: **distrugge la chiave che lo rende leggibile**. Nessuna retention inventata |

### In sospeso

| Doc | Stato |
|---|---|
| **`A15` Deployment** | **RIMANDATO per decisione del committente** (2026-08-23). Da riprendere **solo su sua indicazione esplicita** |
| **`A16` CI/CD** | **RIMANDATO per decisione del committente** (2026-08-23). Da riprendere **solo su sua indicazione esplicita** |
| `A17` Testing / QA | **FATTO** (3.781 righe, subagent). 145 mandati inventariati, 9 gate, 6 bloccanti |
| `A18` API / Integration | **FATTO** (3.635 righe, subagent). Due superfici separate, tutto asincrono, `B-53` isolata |
| Gate Level A | TODO |
| Level B (8 doc) + gate | TODO |
| Level C (9 doc) + gate | TODO |
| `FINAL_ARCHITECTURE.md` | TODO |

**Numeri in corso:** ADR fino a `ADR-297`. Prossimo libero: **`ADR-298`**.
Ricerca fino a `B-122`. Prossimo libero: **`B-123`**.
Rischi fino a `R-117`. Assunzioni fino a `AS-67`. Invarianti fino a `INV-47`.
Decisioni rimandate fino a `DEF-22`.
Registro dei test: `TC-QA-001`…`TC-QA-145` (`A17`); gate `G-QA-01`…`09` e `G-AP-01`…`03`.
Metriche: registro `M-OB-01`…`M-OB-86` (`A12`).

---

## 5. Il prossimo passo: **serve una decisione del committente**

**Non c'è un documento successivo da eseguire d'iniziativa.** `A01`-`A14`, `A17` e `A18` sono
fatti. `A15` (Deployment) e `A16` (CI/CD) sono **rimandati per decisione del committente del
2026-08-23**, e la stessa decisione dice che **si riprendono solo su sua indicazione esplicita**.
Non vanno ripresi perché "mancano".

Le tre strade possibili, da proporre e **non** da scegliere al posto suo:

| Strada | Cosa comporta |
|---|---|
| **Riprendere `A15` e `A16`** | è l'unica che sblocca il **gate di Level A**. Entrambi hanno già lavoro in attesa: `A17` manda ad `A16` i nove gate da eseguire in pipeline più `DEF-19`; `A18` manda ad `A15` il reverse proxy, la parità di ambiente, e la **scadenza di `T-AP-01`** (verificare `B-53` prima che `A15` fissi la versione di Odoo) |
| **Chiudere una delle domande aperte** | `Q-01` (quale CRM), `Q-02`, `Q-03`, più le tre decisioni di §8. `Q-01` in particolare: `A18` ha scoperto che **il costo vero di cambiare CRM non è il connector, è `ADR-161`/`AS-35a`** — l'idempotenza poggia su una proprietà specifica di Odoo. Ricerca `B-117` |
| **Andare a Level B** | possibile tecnicamente, ma **viola l'ordine del Master Entrypoint** (LEVEL A → gate → LEVEL B). Il gate di Level A non può chiudersi senza `A15` e `A16` |

### Il debito che `A17` e `A18` hanno lasciato ai due documenti rimandati

- **`A16` eredita**: l'esecuzione dei nove gate `G-QA-01`…`09` nella pipeline, i tre gate
  `G-AP-01/02/03`, il registro `tests.yaml` di `ADR-266`, e **`DEF-19`** (se il tempo basta solo
  per metà delle 145 voci del registro, quale metà — omissione dichiarata da `A17`).
- **`A15` eredita**: il test di drain, la parità di ambiente, `ADR-270` (staging = quale Odoo
  tocchi, non quale macchina), il reverse proxy con timeout maggiore del `wait` massimo,
  `AS-41`/`B-82` (rete in uscita per il dead man's switch), e la **scadenza di `T-AP-01`**.

### Vincoli di dominio permanenti (valgono per ogni documento successivo)

- **`B-53` va chiusa prima di scegliere il connector**: le API RPC di Odoo risulterebbero
  deprecate con rimozione in **Odoo 22 (autunno 2028)**, sostituite dalla *External JSON-2 API*
  con `Authorization: bearer <api_key>` — ma **il dato non è confermato in originale** (`R-10`).
  Non si costruisce su un protocollo con la data di scadenza.
- **`R-10` e `R-12`** contengono i FATTI su Odoo già verificati: API key per singolo utente
  (dalla v14), `ir.model.data` con vincolo UNIQUE di PostgreSQL, `load()` che fa upsert,
  nessun campo tracciato per default, `unlink()` che non passa da `write()`, `auth_ldap`.
- **`AR-SE-11`**: nessun tool accetta un URL senza allowlist di host **dichiarata nello schema**.
- **`ADR-217`/`ADR-219`/`ADR-220`/`ADR-221`/`ADR-223`**: capability floor, tool per campo,
  cardinalità 1 di default, lettura prima della scrittura, campi amministrativi fuori.
- **`ADR-161`**: l'idempotenza verso Odoo la costruiamo noi con l'external ID nel namespace
  `__agent__`, record e riga `ir.model.data` **nella stessa transazione** (`AR-EV-32`).
- **`B-54`** (operatività delle API key per-utente) è la via d'uscita da **`R-41`**.
- `Q-01` (Odoo o CRM generico?) pesa su `A18` più che su ogni altro documento.

### `AS-29` è stata confermata (2026-08-23)

*Se il PDP si guasta, il sistema **si ferma**.* Decisione esplicita del committente. Il
fail-closed di `A13` §22 e `AR-SE-16` non poggiano più su un'ipotesi. **Nessun percorso di
degrado va introdotto**: ogni percorso di degrado è un percorso che un attaccante innesca.

### Debito aperto che riguarda tutti

- **`B-26`** resta la ricerca più urgente: misurare l'embedding su CPU. Un pomeriggio.
- **`B-86` è dovuta**: l'elenco `ASI01`-`ASI10` non è stato letto alla fonte (403).
- **`B-53`** (deprecazione delle API RPC di Odoo) prima di scegliere il connector.
- **`B-66`**, **`B-74`**, **`B-76`**, **`B-87`** restano aperte.
- `Q-01`, `Q-02`, `Q-03`, `Q-04` restano aperte.

### Da portare al gate di Level A

**Pattern scoperto da `A13`:** due trigger progettati per **allentare** una difesa (`T-GP-02`,
`T-ME-04`) non distinguevano fra *"la difesa non serve più"* e *"la difesa ha smesso di
funzionare"*. Al gate vanno riletti **tutti** i trigger di allentamento con la domanda: *cosa
lo farebbe scattare se il controllo fosse stato aggirato invece che reso superfluo?*

### Vincoli di dominio dichiarati dal committente (2026-08-23)

Non derivabili dal codice né dai prompt. Vanno rispettati da tutti i documenti successivi.

- **`AS-29` confermata**: se il PDP (chi decide se un'azione è permessa) si guasta, il sistema
  **si ferma**, non degrada. Vale per tutti i documenti successivi: niente percorsi di degrado.
- **`ADR-216` — conferma umana su OGNI `Insert`, `Update` e `Archive`, su OGNI entità, senza
  eccezioni.** È lo standard corrente dei vendor (`R-14.6`), non un eccesso di prudenza.
  L'uscita esiste **solo** via `T-GP-02` riformulato, mai per configurazione.
- **`ADR-217` — capability floor: Day-1 l'agent è in sola lettura sull'ERP** e scrive solo su
  una superficie CRM dichiarata. Contabilità e campi amministrativi del contatto fuori.
- **`ADR-218` — non esiste alcun tool di cancellazione: solo `archive`.** `unlink()` in Odoo
  **non passa da `write()`**, quindi aggira le automazioni invece di attraversarle.
- **`ADR-220` — cardinalità dichiarata, default 1.** La differenza fra un errore e un disastro
  non è la gravità dell'azione: è quanti record tocca.
- **`ADR-221` — lettura prima della scrittura.** In Odoo **nessun campo è tracciato per
  default**: se non conserviamo noi il valore precedente, dopo un `UPDATE` è perduto.
- **`ADR-104`**: nessun task CRM supera **50 step** o **10 minuti di tempo attivo**. La
  sospensione in attesa di approvazione umana **non conta** nel tempo attivo. Questo ha
  chiuso `AS-20` e ha disinnescato la debolezza di scala di `AR-ME-13`.
- **~90 % dei casi d'uso è una singola chiamata a tool** (3-5 step), seguita da codice
  applicativo deterministico. **Attenzione al lessico:** il modello emette un payload
  **tipizzato e validato contro uno JSON Schema**, non un DSL. Un DSL si interpreta e la sua
  potenza espressiva non è limitabile da uno schema: è precisamente ciò che `A06` ha vietato
  (nessun argomento di tool può essere un programma, `ADR-049`, rifiuto di `execute_kw`).
- **Credenziali aziendali, nessun OAuth, al massimo LDAP** (`ADR-121`). Vale sia per
  l'autenticazione delle persone verso la piattaforma, sia verso il CRM. Coerente col
  prodotto: Odoo **non ha** OAuth per l'API esterna. La delega per singolo utente, quando
  servirà, passerà dalle **API key per-utente** di Odoo, non da OAuth.

---

## 6. Il template del prompt per i subagent

Riusabile per ogni documento delegato. Sostituire le parti fra `<>`.

```text
Sei un Principal Architect. Produci un documento architetturale per una piattaforma AI
agent enterprise per CRM/ERP.

## Cosa devi fare

1. Leggi in quest'ordine (obbligatorio):
   - ai/prompt/architecture-convetion.txt          → convenzione. VINCOLANTE.
   - ai/state/ARCHITECTURE_STATE.md                → stato canonico. VINCOLANTE.
   - ai/state/research-log.md                      → i FATTI. Non rifare ricerca.
   - <percorso del prompt>                         → leggilo a sezioni con offset/limit,
                                                     ma copri TUTTE le sue richieste.
2. Produci <percorso del documento di output>

## Regole di stile NON negoziabili

- Prosa in italiano. Terminologia tecnica in inglese (niente traduzioni artificiali).
- Ogni sigla glossata alla prima occorrenza.
- Spiegare come a un principiante: analogie concrete, frasi corte, senza perdere precisione.
- Diagrammi Mermaid dove servono, ciascuno seguito da "Come leggerlo".
- Distingui FATTO / INFERENZA / DECISIONE ARCHITETTURALE.
- Quando non sai: DA VERIFICARE, NON ANCORA DECISO, ASSUNZIONE, RICHIEDE RICERCA.
  Mai inventare, in particolare numeri di scala o performance.
- "Responsabilità" e "Non responsabilità" esplicite.
- Ogni decisione: alternative reali, trade-off, perché le altre perdono, cosa la invertirebbe.
- Autocritica onesta con le debolezze reali + un contro-argomento forte all'architettura
  scelta, con la tua risposta.

## Vincoli ereditati (consuma, non ridiscutere)
<elenco puntuale degli ADR e delle regole AR-* che il documento deve rispettare>

## Mandati espliciti dai documenti precedenti
<cosa i documenti già scritti hanno imposto a questo>

## Cosa devi decidere in modo indipendente
<elenco delle questioni aperte specifiche del documento>

## Formato di ritorno

Il tuo testo finale NON è un messaggio per un umano: è il checkpoint che verrà integrato
nello stato. Restituisci SOLO questo, compatto, in italiano:

DOCUMENT / PURPOSE / KEY DECISIONS / REJECTED ALTERNATIVES / NEW INTERFACES /
NEW CONSTRAINTS (nuove regole AR-<sigla>-*) / NEW RISKS / NEW ASSUMPTIONS /
DECISIONS THAT MAY NEED REVISION / IMPACT ON PREVIOUS ARCHITECTURE /
IMPACT ON FUTURE ARCHITECTURE / DAY-1 REQUIREMENTS / FUTURE REQUIREMENTS /
NEW ADR (da ADR-<prossimo libero>) / NEW TRIGGERS (T-<sigla>-*) /
NEW RESEARCH BACKLOG (da B-<prossimo libero>) / CONFIDENCE (con il motivo).

Non incollare il documento nel messaggio di ritorno.
```

### Dopo ogni subagent

1. Aggiornare `EXECUTION_LEDGER.md` → `FATTO`.
2. Integrare il checkpoint in `ARCHITECTURE_STATE.md`: ADR, regole, rischi, assunzioni,
   trigger, la scheda del documento in §9d.
3. Aggiungere le nuove voci al backlog di `research-log.md`.
4. Riferire all'utente **solo ciò che conta**: le decisioni che cambiano qualcosa, i
   problemi aperti, le cose su cui deve decidere lui.

---

## 7. Le sigle in uso

| Prefisso | Significato | Assegnato in |
|---|---|---|
| `AR-001…036` | regole architetturali generali | `A01` |
| `AR-CP-*` | Control Plane | `A02` |
| `AR-GP-*` | governance e policy | `A03` |
| `AR-RT-*` | runtime | `A04` |
| `AR-MD-*` | model e inference | `A05` |
| `AR-TL-*` | tool | `A06` |
| `AR-KN-*` | knowledge e retrieval | `A07` |
| `AR-ME-*` | memory e context budget | `A08` |
| `AR-ID-*` | identity, autenticazione, delega | `A09` |
| `AR-AC-*` | comunicazione fra agent, multi-agent | `A10` |
| `AR-EV-*` | eventing, esecuzione durevole, recovery | `A11` |
| `AR-OB-*` | observability, evaluation, affidabilità | `A12` |
| `AR-SE-*` | sicurezza | `A13` |
| `AR-DG-*` | data governance, privacy, retention | `A14` |
| `AR-QA-*` | testing, qualità, validazione | `A17` |
| `AR-AP-*` | API, integration, superfici esterne | `A18` |
| `ADR-*` | decisioni formali, numerazione unica e progressiva | tutti |
| `T-*` | trigger di revisione architetturale | tutti |
| `AS-*` | assunzioni | tutti |
| `R-*` | rischi | tutti |
| `D-*` | debito architetturale | `A01` |
| `DEF-*` | decisioni esplicitamente rimandate | tutti |
| `B-*` | backlog di ricerca esterna | `research-log.md` |
| `Q-*` | domande aperte per il committente | tutti |
| `INV-*` | invarianti: regole con verifica automatica, violarle rompe la build | tutti |
| `TC-QA-*` | voci del registro dei test (`tests.yaml`), 145 | `A17` |
| `G-QA-*`, `G-AP-*` | gate di rilascio (9 + 3), con classe bloccante / advisory / manuale | `A17`, `A18` |
| `TS-1…10`, `TC-EV-*` | gate di sicurezza e test di recovery, battezzati prima di `A17` | `A13`, `A11` |
| `NEG-1…3` | i test negativi sull'API che non possono mai migrare nightly (`AR-AP-30`) | `A18` |
| `ASI01`-`ASI10` | i dieci rischi OWASP per agent, usati come threat model | `A13` |

---

## 8. Le cose che l'utente deve decidere

Bloccano o limitano documenti già in coda.

| ID | Domanda | Cosa blocca | Nota |
|---|---|---|---|
| **`Q-01`** | **quale CRM?** | `A06`, `A18` (entrambi già scritti su Odoo concreto) | `A06` raccomandava: **se la risposta tarda, cominciare da Odoo**. Fatto. **`A18` ha però cambiato la forma della domanda**: il costo di un CRM diverso **non è il connector** — `transport.py` è un file solo — **è `ADR-161`/`AS-35a`**, cioè l'idempotenza, che poggia su una proprietà specifica di Odoo (external ID scelto dal chiamante con vincolo UNIQUE **del database**). La domanda utile sugli alternativi è *«ce l'hanno?»*, ed è la ricerca **`B-117`**. Nessuna astrazione è stata costruita: `AR-020` la vieta senza due implementazioni reali (`ADR-293`, `AS-67`, `T-AP-06`) |
| `Q-02` | esistono SLA, RPO, RTO dichiarati? | `A13`, `C24` | in assenza: `NON ANCORA DECISO`, nessun numero inventato |
| `Q-03` | SaaS, on-premises, o entrambi? | `A15`, `B19` | in assenza si assume "entrambi", che è il vincolo più stretto |
| `Q-04` | volume dei documenti della knowledge base? | **`A07`**, `B23` | serve al dimensionamento di pgvector |
| `Q-05` | utenti concorrenti attesi nel pilot? | `B21` | capacity planning |
| `Q-06` | esiste già un identity provider aziendale? | `A09` | in assenza: OIDC generico |
| `Q-07` | chi opererà il sistema in produzione? | `A15`, `A12` | in assenza si assume il team di sviluppo |

### Decisioni aperte dopo `A17` e `A18` (2026-08-23)

Non sono `Q-*` perché non sono domande di scoperta: sono **scelte** che nessun documento può
fare al posto del committente.

| Cosa | Perché serve lui | Se non risponde |
|---|---|---|
| **`R-108` — documenti reali nel golden set** | `INV-40` vieta il **testo libero prodotto in produzione**, non i **documenti aziendali caricati**. Un golden set del retrieval costruito sui contratti veri non viola niente, e git non dimentica | resta possibile per omissione. **È la più economica da decidere adesso e la più costosa da correggere dopo.** Ricerca `B-115` |
| **`AS-60` — red teaming con soggetti umani** | `ADR-215` lo esige su `ASI09` (approval fatigue), e i soggetti **non** possono essere chi ha costruito l'interfaccia. È una risorsa organizzativa, non tecnica | `ADR-215` resta un requisito non soddisfatto e **`AS-44` («l'attrito della conferma funziona») resta non verificata**: la difesa principale non è mai stata provata. Ricerca `B-112` |
| **`AS-64` — accettare che tutto sia asincrono** | `ADR-285`: nessuna operazione risponde "fatto" nella stessa richiesta HTTP. È **derivato** da `ADR-104` + `ADR-216`, ma cambia l'esperienza d'uso | si costruisce l'API su un'assunzione non confermata, e cambiarla dopo significa cambiare la forma dell'intera superficie |
| **`DEF-21` / `DEF-14` — i numeri** | rate limit, quote, timeout, budget verso Odoo (`DEF-21`); `k` e soglie di regressione (`DEF-14`). **I criteri sono scritti, i numeri no, e nessuno è stato inventato** | `DEF-21` scade prima del primo tenant reale; `DEF-14` prima del terzo rilascio, altrimenti `R-106` (nessun gate di qualità diventa mai bloccante). Ricerche `B-106`, `B-116`, `B-119` |
| **`T-AP-01` — verificare `B-53`** | le API RPC di Odoo risulterebbero deprecate (rimozione Odoo 22, autunno 2028), **ma il dato non è confermato in originale**. Va verificato sulla fonte primaria | **scadenza ancorata a un documento, non a una data: prima che `A15` fissi la versione di Odoo.** Se la sostituta ha forma diversa da `(model, method, args, kwargs)`, non basta riscrivere un file: `R-109`. Ricerca `B-118` |

---

## 9. I problemi aperti, dichiarati e non risolti

Da non perdere di vista: sono le cose su cui l'architettura **non** ha una risposta
strutturale.

| # | Problema | Stato |
|---|---|---|
| 1 | **Composizione di azioni lecite.** `export_report` + `send_email`, entrambe autorizzate, fanno un'esfiltrazione. Nessuna policy per-azione lo intercetta | **compensato** dall'approvazione umana obbligatoria sui side effect, **non risolto**. Ricerca `B-11`. La sede naturale di una soluzione è lo **step journal** |
| 2 | **Il codice di recovery** è il rischio più concreto dell'architettura, perché produce danni **silenziosi** | mitigato da test che uccidono il worker in CI. Trigger volutamente severo `T-RT-06`: più di due correzioni nel primo trimestre → riaprire `ADR-002` (la scelta di non usare Temporal) |
| 3 | **Il threat model non è completo** | **Aggiornato il 2026-08-23.** `A13` è stato scritto e ha chiuso `ASI09` (approval fatigue), il buco che nessun documento aveva visto. Ma la copertura resta **dichiarata incompleta (65,3 %, `R-13.5`)**, e `A17` l'ha confermata invece di chiuderla. `A18` aggiunge una superficie nuova con le stesse riserve. Va al gate di Level A e a `C26` |
| 4 | **Nessuna ricerca esterna nuova è stata fatta** in queste sessioni | ci si è appoggiati al `research-log` del 2026-08-22. Ogni documento lo dichiara. Le decisioni **costose** non dipendono da fonti esterne, per costruzione. **Il prezzo è cumulativo e ora è visibile**: `A17` ha aperto 10 voci di backlog, `A18` altre 7. Tre sono a priorità **Alta** e bloccano cose concrete — `B-106` (nessun gate di qualità diventa bloccante), `B-116` (il budget verso Odoo è un numero inventato), `B-118` (se `B-53` è vera, quanto costa) |
| 5 | **`AS-10`: un modello da 9B a 4 bit regge decine di tool** — confidenza **bassa, non verificata** | regge il budget del prefisso di `A06`. Ricerca `B-20` |
| 6 | **Copertura della verifica automatica sulle regole `AR-*`** | **Aggiornato il 2026-08-23.** Il dato «~20 su 36» era riferito alle sole `AR-001…036` di `A01`. Oggi i prefissi sono 16 e le regole alcune centinaia. I due ultimi documenti dichiarano il proprio rapporto: `A17` **14 su 20** sulle `AR-ME-*` ereditate, `A18` **26 su 32**. Al gate di Level A ogni `AR-` va marcata `ENFORCED` o `REVIEWED`; **le `REVIEWED` sono debito, e il conto non è mai stato fatto sull'insieme** |
| 7 | **`R-115` — l'`OdooFake` non può rilevare divergenze di protocollo** | scoperto da `A18` il 2026-08-23. Il fake implementa la **firma** di `call()`, non il filo: per costruzione non vede una divergenza di protocollo. **`A18` peggiora `R-98` e lo dichiara invece di nasconderlo.** L'unico luogo dove la divergenza può emergere è il contract test notturno contro Odoo reale (`ADR-262`) |
| 8 | **La disciplina di test è il rischio più probabile del progetto** | `R-97` (i gate migrano fuori dal percorso che bloccano) e `R-112` (i 192 test negativi di `A18` migrano nightly) sono entrambi **Alta**. La mitigazione di `AR-AP-30` copre solo `NEG-1/2/3` ed è **dichiarata parziale**. Vale il pattern generale: *i rischi ad alta probabilità di questo progetto non sono tecnici, sono di disciplina* |
| 9 | **`A17` misura l'inutilità molto meglio di quanto misuri la dannosità** | autocritica di `A17` §31.3, riportata senza attenuanti: l'architettura protegge bene dal sistema **dannoso** ma le sue *misure* riguardano quasi solo il sistema **inutile**. Sproporzione deliberata — l'inutilità ha un canale di rilevamento naturale, la dannosità no — ma `ADR-283` chiude solo una delle tre falle che l'obiezione nomina |

---

## 10. Il comando per ripartire

> Leggi `ai/state/RESTART.md`, poi `ai/state/EXECUTION_LEDGER.md`, poi
> `ai/state/ARCHITECTURE_STATE.md` e `ai/state/research-log.md`. Riprendi dal primo
> documento `TODO` rispettando il metodo ibrido e le contromisure descritte.

> **⚠️ Dal 2026-08-23 questo comando non basta più.** L'unico `TODO` rimasto in Level A è il
> **gate**, che è bloccato, e i due documenti che lo sbloccherebbero (`A15`, `A16`) sono
> **rimandati per decisione del committente**. Vedi §5: non si riprende d'iniziativa, si chiede.
