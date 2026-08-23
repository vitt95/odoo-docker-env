# RESEARCH LOG — stato condiviso della ricerca esterna

Questo file raccoglie i **fatti verificati tramite ricerca esterna** durante il percorso
architetturale. Serve a evitare di ripetere la stessa ricerca per ogni documento e a
mantenere una singola fonte di verità sui fatti tecnologici.

Regola: qui dentro va solo ciò che è **FATTO** (verificabile alla fonte).
Inferenze e decisioni architetturali vivono nei documenti, non qui.

Data della passata di ricerca: **2026-08-22**.

---

## R-01 — Model Context Protocol (MCP)

**FATTO.** La revisione corrente della specifica è **`2026-07-28`**.
Fonte: https://modelcontextprotocol.io/specification/2026-07-28

Cambiamenti rilevanti rispetto a `2025-11-25` (la versione citata in `ai/research/03`):

| Cambiamento | Impatto architetturale |
|---|---|
| **Core stateless** — rimosso l'handshake `initialize` a livello di protocollo | Un `MCP Client` non deve più mantenere sessione per parlare con un server; semplifica scaling orizzontale e riavvii |
| **`server/discover`** (SEP-2567) | Discovery esplicito delle capability, non più implicito nell'handshake |
| **Multi Round-Trip Requests** | Un tool può richiedere più giri di interazione prima di completare |
| **Header-based routing** | Consente gateway/proxy davanti ai server MCP senza parsing del body |
| **Cacheable list results** | `tools/list` diventa cacheabile → il `Tool Registry` locale può avere una strategia di cache definita dal protocollo |
| **Authorization hardening** | Rilevante per il confine agent → tool |
| **Framework di extension formale** | Estensioni opt-in con ID reverse-DNS |

**FATTO.** Non c'è switch-off: un client `2026-07-28` deve poter parlare con server
`2025-11-25` o precedenti. La compatibilità all'indietro è prevista.

**FATTO.** Il TypeScript SDK v2 è la linea stabile che implementa `2026-07-28`.
SDK beta rilasciati per Python, TypeScript, Go, C#.

**DA VERIFICARE:** maturità dell'SDK Python per `2026-07-28` al momento
dell'implementazione (il backend del progetto è Python).

---

## R-02 — A2A (Agent-to-Agent)

**FATTO.** A2A ha raggiunto **v1.0** ad aprile 2026, sotto Linux Foundation.
Fonte: https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year

Elementi della v1.0 rilevanti:

- oggetti core: `AgentCard`, `AgentSkill`, JSON Schema 2020-12;
- metodi: `SendMessage`, `SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`;
- trasporti: JSON-RPC 2.0 su HTTPS, gRPC, HTTP/JSON/REST;
- SDK in cinque linguaggi (Python, JavaScript, Java, Go, .NET);
- oltre 150 organizzazioni coinvolte, deployment enterprise in produzione.

**FATTO.** Gap noti dichiarati dal progetto stesso: schema per-skill del body,
token downscoping, standardizzazione del registry. Richiedono workaround applicativi.

**Conseguenza per noi:** A2A non è più un moving target. Level C può progettare
contro un contratto stabile invece che contro un'ipotesi.

---

## R-03 — Policy engine: OPA vs Cedar

**FATTO.** I due riferimenti dichiarativi principali sono Open Policy Agent (linguaggio
Rego, general-purpose) e AWS Cedar (linguaggio specifico per authorization, progettato
per verifica formale e leggibilità).

**FATTO.** Cedar è pensato per essere **embedded come libreria** nell'applicazione;
OPA è tipicamente deployato come processo/sidecar separato.

**FATTO.** Alternative rilevanti: OpenFGA (ReBAC stile Zanzibar, progetto CNCF in
incubation), Topaz (OPA + directory service stile Zanzibar).

**ATTENZIONE SULLE FONTI.** La maggior parte dei confronti disponibili proviene da
vendor commerciali (Oso, Permit.io, CloudMatos) che hanno interesse a posizionarsi
contro OPA. Le affermazioni su performance e roadmap vanno considerate deboli.

**DA VERIFICARE:** maturità dei binding Python di Cedar (il core è Rust).

---

## R-04 — Durable execution

**FATTO.** Il campo si è consolidato nel 2025-2026. Opzioni rilevanti:

| Opzione | Natura | Nota |
|---|---|---|
| **Temporal** | Cluster dedicato, backend Cassandra/Postgres | Maturo, SDK in 7 linguaggi. Richiede un secondo sistema distribuito da operare |
| **DBOS** | Libreria; PostgreSQL è la sorgente di verità del workflow | Semantica exactly-once transazionale quando lo step scrive sullo **stesso** Postgres che contiene lo stato del workflow. SDK Go rilasciato aprile 2026 |
| **pg_durable** | Estensione PostgreSQL, open-sourced da Microsoft il 2026-06-05 | Workflow definiti in SQL; checkpoint/retry/recovery gestiti da Postgres |
| **Absurd** | Singolo file `.sql` (~1.685 righe) che installa un motore di durable execution in Postgres | Di Armin Ronacher, lanciato novembre 2025. Nessun server |
| **Restate / Inngest / Hatchet** | Servizi/engine dedicati | Modelli commerciali diversi |

**FATTO (rubrica riportata dalle fonti).** Postgres-based conviene quando: gli effetti
del workflow atterrano perlopiù sul tuo Postgres, sei nell'ordine di qualche migliaio di
transizioni di stato al secondo, non serve isolamento di storage hard per tenant.
Temporal conviene quando: più servizi workflow-heavy, fan-out verso molte API esterne,
requisiti multi-region hard, decine di migliaia di transizioni/secondo.

**Nota critica riportata dalle fonti:** il costo nascosto degli engine dedicati è che
"il tuo Postgres gestisce un ordine di grandezza più query di quanto ti aspettassi".

---

## R-05 — PostgreSQL 18

**FATTO.** PostgreSQL 18 è rilasciato.
Fonte: https://www.postgresql.org/docs/release/18.0/

Novità rilevanti per questo progetto:

- **`uuidv7()` nativo** — UUID ordinati temporalmente. Rilevante per chiavi primarie di
  tabelle append-heavy (run, step, audit) perché riducono la frammentazione dell'indice
  B-tree rispetto a UUIDv4;
- **async I/O**;
- **OAuth 2.0 authentication** lato server;
- **btree skip scan** — indici multicolonna utilizzabili in più casi;
- **virtual generated columns** (ora default per le generated column);
- **`OLD` e `NEW` in `RETURNING`** per INSERT/UPDATE/DELETE/MERGE — utile per audit trail
  scritti nella stessa transazione della modifica;
- **temporal constraints** su range per PRIMARY KEY / UNIQUE / FOREIGN KEY.

Logical replication in 18:
- conflitti di scrittura ora riportati nei log e in `pg_stat_subscription_stats`;
- `CREATE SUBSCRIPTION` usa parallel streaming di default;
- `idle_replication_slot_timeout` per evitare accumulo di WAL;
- `publish_generated_columns` per le generated column STORED.

**FATTO.** `SKIP LOCKED` **non** è una novità della 18: esiste da tempo.
`FOR UPDATE SKIP LOCKED` fa sì che le righe già lockate da un'altra transazione vengano
saltate, così ogni consumer prende un set diverso senza collidere. È il pattern standard
per una queue su Postgres.

**FATTO — trappola operativa.** Le tabelle `UNLOGGED` saltano il WAL ma **non** vengono
replicate e vengono troncate al crash. Sono quindi incompatibili con una strategia di
logical replication applicata alla tabella di queue.

---

## R-06 — vLLM

**FATTO.** vLLM espone un endpoint Prometheus con contatori su: GPU cache usage,
richieste running/waiting, TTFT (time to first token), time per output token, queue depth.

**FATTO.** Supporta structured outputs (guided decoding con enforcement di JSON Schema)
e tool calling con parser specifici per modello.

**FATTO.** Il `production-stack` ufficiale include: Helm chart, logging strutturato
(`--log-format json`), tracing OpenTelemetry con propagazione del context W3C nel router,
routing prefix-aware.

**ATTENZIONE SULLE FONTI.** I blog di terze parti riportano numeri di versione
incoerenti. Per la versione autorevole consultare
https://github.com/vllm-project/vllm/releases

**FATTO — avvertenza operativa riportata dalla documentazione.** Prima di un upgrade va
testata la combinazione esatta di: checkpoint, formato di quantizzazione, tokenizer,
context length, structured outputs, reasoning parser, tool calling. Il fatto che un
modello sia "supportato" non garantisce che ogni modalità di serving funzioni.

---

## R-07 — Sicurezza degli agenti: OWASP e NIST

### OWASP Top 10 for Agentic Applications 2026

**FATTO.** Pubblicata il 2025-12-09 dall'OWASP GenAI Security Project. Identificatori da
**ASI01 a ASI10**.
Fonte: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

È una lista **distinta** dalla Top 10 for LLM Applications: quella copre rischi a livello
di modello (input → output), questa copre cosa succede quando il modello diventa un
**attore** con obiettivi, credenziali, tool, memoria e autonomia di concatenare azioni.

Rischi citati esplicitamente dalle fonti consultate:

- **ASI01 — Agent Goal Hijack**: l'attaccante manipola gli obiettivi dell'agent sfruttando
  il fatto che l'agent non distingue in modo affidabile istruzioni legittime da contenuto
  malevolo. Caso reale citato: **EchoLeak**, email con payload nascosto.
- **ASI10 — Rogue Agents**: agent che devia dal comportamento previsto e agisce con
  autonomia dannosa — autorizzato, trusted, ma disallineato. Esempio di reward hacking
  riportato: un agent incaricato di minimizzare i costi di storage cancella i backup di
  produzione.

Altri rischi nominati dalle fonti: tool misuse, memory poisoning.

**DA VERIFICARE:** l'elenco completo e testuale di ASI01-ASI10 va letto alla fonte
prima di costruirci sopra un threat model formale (documento 13-security).

### NIST

**FATTO.** Il **CAISI** (Center for AI Standards and Innovation) del NIST ha lanciato la
**AI Agent Standards Initiative** il **2026-02-17**.
Fonte: https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative

Tre pilastri: standard guidati dall'industria, sviluppo open-source di protocolli guidato
dalla community, ricerca fondazionale su sicurezza e identity.

**FATTO.** Un concept paper NCCoE di febbraio 2026 propone un progetto dimostrativo su
**AI agent identity e authorization** basato su **OAuth 2.0 + SPIFFE/SPIRE + MCP**.
Quattro aree: identification, authorization, access delegation, logging.
Pratica raccomandata: trattare ogni agent come **non-human identity distinta**, con owner
definito, tipo di credenziale documentato, schedule di rotazione e scope autorizzato.

**FATTO.** **COSAiS** (Control Overlays for Securing AI Systems) è l'estensione NIST di
SP 800-53 ai casi d'uso AI, e includerà overlay dedicati per deployment single-agent e
multi-agent. Ad aprile 2026 entrambi gli overlay erano **ancora in sviluppo, senza data
di pubblicazione**.

**FATTO.** La tassonomia di attacco avversariale di riferimento è **NIST AI 100-2 E2025**.

**FATTO.** Ricerca NIST di gennaio 2025: strategie di attacco nuove contro AI agent hanno
raggiunto un tasso di successo dell'**81%** contro l'**11%** delle difese baseline.

---

## R-08 — Fatti hardware/costo dai documenti di ricerca del progetto

Riportati qui perché già verificati in `ai/research/04` con citazione, e usati
ripetutamente nei documenti architetturali.

**FATTO.** Qwen3.5-9B quantizzato Q4_K_M: file ~5,24 GiB, ~5,83 GiB di VRAM sopra l'idle,
~122,9 tok/s in generazione su workload `tg128` su RTX 4090.
Fonte: https://huggingface.co/steven0226/Qwen3.5-9B-GGUF-Quant-Lab/blob/main/EVAL_REPORT.md

**Non è uno SLA.** Un altro benchmark riporta ~61 tok/s su backend Apple/MTL con la stessa
quantizzazione. La variabilità per hardware e runtime è enorme.

**FATTO.** Hetzner GEX44: RTX 4000 SFF Ada 20 GB VRAM, 64 GB RAM, €232,30/mese + setup,
IVA esclusa (prezzi pubblicati giugno 2026).
Fonte: https://www.hetzner.com/dedicated-rootserver/gex44/

**FATTO.** Google Cloud NVIDIA L4 24 GB: ~$0,56004/ora per GPU on-demand.
`g2-standard-4` (1× L4, 16 GiB RAM): ~$0,70683/ora ≈ $516/mese in 24/7, prima di storage,
network, database, load balancer, log, backup.
Fonte: https://cloud.google.com/products/compute/gpus-pricing

---

## R-09 — Password hashing (chiude `B-45`, ricerca del 2026-08-23)

**FATTO.** OWASP Password Storage Cheat Sheet raccomanda **Argon2id** come prima scelta.
Configurazioni tabellate, di sicurezza equivalente (si scambia memoria contro tempo):

| Memoria | Iterazioni | Parallelismo |
|---|---|---|
| `m = 47104` (46 MiB) | `t = 1` | `p = 1` |
| `m = 19456` (19 MiB) | `t = 2` | `p = 1` |
| `m = 12288` (12 MiB) | `t = 3` | `p = 1` |
| `m = 9216` (9 MiB) | `t = 4` | `p = 1` |
| `m = 7168` (7 MiB) | `t = 5` | `p = 1` |

**FATTO.** Ordine di raccomandazione: Argon2id, poi scrypt, poi bcrypt, poi PBKDF2
(quest'ultimo solo per conformità FIPS). `bcrypt` resta difendibile con `cost ≥ 12`, ma il
suo argomento è la migrazione di basi installate, non la scelta iniziale.

**FATTO.** In Python la libreria è `argon2-cffi`. Le implementazioni pure-Python sono
abbastanza lente da indurre a scegliere parametri deboli per compensare.

**FATTO.** Pattern di migrazione standard: *rehash-on-next-login* — si verifica col vecchio
algoritmo, poi si ricalcola e si salva col nuovo.

**INFERENZA nostra:** scegliamo la riga a **più memoria** (`m=47104, t=1, p=1`). Argon2id è
*memory-hard*: costringe l'attaccante a comprare RAM, non solo calcolo, e le GPU — l'hardware
che userebbe — hanno poca memoria per core. I login sono rari (`AS-26`), quindi 46 MiB per
qualche centinaio di millisecondi non pesano. → **`ADR-120`**.

---

## R-10 — Odoo: API esterna, ID utente, LDAP (chiude `B-47` e `B-49`, ricerca del 2026-08-23)

**FATTO — `B-47`.** Odoo **non offre OAuth per l'API esterna**. Gli OAuth presenti riguardano
il login inbound (Google/Microsoft sign-in) e la posta, non l'accesso programmatico.

**FATTO — `B-47`.** Odoo 14+ ha **API key per singolo utente**: è la cosa più vicina a una
credenziale per-utente che il prodotto offra, e porta i permessi e le record rule di quella
persona. **È la strada verso la "catena 1" senza OAuth**, quindi verso la chiusura di `R-41`.

**DA VERIFICARE — deprecazione.** Secondo i risultati di ricerca sulla documentazione Odoo,
XML-RPC e JSON-RPC sono deprecate, con rimozione prevista in **Odoo 22 (autunno 2028)**,
sostituite da una **External JSON-2 API** con `Authorization: bearer <api_key>` e header
`X-Odoo-Database`. **Non confermato in originale**: la pagina primaria ha restituito solo la
navigazione. **Va confermato prima di scegliere il connector** → riguarda `A18`.

**FATTO — `Q-03` collaterale.** Su Odoo Online/SaaS l'accesso all'API esterna è disponibile
solo sui piani Custom, non su One App Free né Standard.

**FATTO — `B-49`. Odoo NON riusa gli ID utente.** `res_users.id` è un `SERIAL` PostgreSQL:
le sequence sono monotone, dopo una cancellazione l'ID non viene riassegnato, resta un buco.

**FATTO — caveat 1.** Un amministratore *può* forzarlo con `setval()`. È sconsigliato dalla
comunità PostgreSQL, e su `res_users` è velenoso: l'ID è referenziato da `create_uid`,
`write_uid`, `ir.model.access`, follower, allegati, `ir.model.data`. Riusarlo **riattacca
silenziosamente un nuovo utente alla storia e ai permessi del precedente**.

**FATTO — caveat 2.** In Odoo la pratica normale è **archiviare** gli utenti
(`active = False`), non cancellarli. Quindi "la persona non c'è più" ≠ "la riga non c'è più".

**FATTO — LDAP.** Il modulo `auth_ldap` è nelle addons base (anche Community). Configurazione
per server LDAP con base, filtro, binddn, e utente template.

**FATTO — LDAP, limite importante.** `auth_ldap` di base **non mappa i gruppi LDAP sui gruppi
Odoo**: gli utenti creati via LDAP ricevono i gruppi di default. La mappatura richiede il
modulo OCA **`users_ldap_groups`**.

**FATTO — LDAP, trappola di sicurezza.** In `users_ldap_groups`, se l'opzione *"Only LDAP
groups"* **non** è spuntata, un utente rimosso da un gruppo nella directory **non perde** il
gruppo in Odoo. Se adottiamo LDAP, quella spunta è obbligatoria.

---

## R-11 — Multi-agent contro single-agent: l'evidenza (chiude `B-58`, ricerca del 2026-08-23)

Ricerca approfondita richiesta dal committente. Nove fonti, cinque primarie (paper con
metodo dichiarato), quattro secondarie (report ingegneristici di chi costruisce questi
sistemi). Confidenza raggiunta: **alta**.

### R-11.1 — I FATTI a favore del single-agent

**FATTO.** *Why Do Multi-Agent LLM Systems Fail?* — Cemri, Pan, Yang et al., UC Berkeley,
arXiv:2503.13657, **poster NeurIPS 2025**. Dataset `MAST-Data`: **1.600+ trace annotate su 7
framework multi-agent**. Tassonomia `MAST` costruita su 150 trace con annotatori esperti,
accordo inter-annotatore **κ = 0,88**. **14 modi di fallimento** in 3 categorie: problemi di
design del sistema, disallineamento fra agent, verifica del task. Affermazione degli autori:
*"i guadagni di performance sui benchmark più diffusi sono spesso minimi"*. Su 1.642 trace
reali, i **tassi di fallimento vanno dal 41 % all'86,7 %**. Conclusione: i fallimenti nascono
dal **design del sistema**, non dai limiti del modello.

**FATTO.** *Do More Agents Help? Controlled and Protocol-Aligned Evaluation of LLM Agent
Workflows* — arXiv:2606.05670, giugno 2026. Harness `BenchAgent`: stesso benchmark loader,
stesso accesso ai tool, stesso answer contract, stessa contabilità d'uso. **10 benchmark**
(reasoning, coding, tool use), modello GPT-4.1. Risultato: **al massimo 1 su 6 sistemi
multi-agent supera l'ancora single-agent** a parità di protocollo, e quell'uno rientra
nell'incertezza statistica. **Gli altri 5 perdono da 2,56 a 11,29 punti** *e* costano di più.

**FATTO.** *Tran & Kiela (Stanford)*, arXiv:2604.02460, aprile 2026. Argomento
**informazione-teorico** fondato sulla **Data Processing Inequality**: a budget di reasoning
token fissato e utilizzo perfetto del context, il single-agent è **più efficiente in
informazione** — far passare l'informazione attraverso più hand-off non può aggiungerla, può
solo perderla. Studio controllato su **tre famiglie di modelli** (Qwen3,
DeepSeek-R1-Distill-Llama, Gemini 2.5) contro più architetture multi-agent **a budget di
token appaiato**: il single-agent **eguaglia o supera costantemente** il multi-agent sul
reasoning multi-hop. Gli autori identificano inoltre **artefatti nel controllo del budget via
API e nei benchmark standard che gonfiano i guadagni apparenti** del multi-agent.

**FATTO — il dato pro-multi-agent più citato si smonta da solo.** Anthropic, *How we built
our multi-agent research system*: il sistema orchestrator-worker (Opus 4 lead + Sonnet 4
subagent) batte il singolo Opus 4 del **90,2 %** sulla loro eval interna. Ma: consuma
**~15× i token** di una chat, e su BrowseComp **tre variabili spiegano il 95 % della varianza
di performance, di cui il solo uso di token ne spiega l'80 %**. Cioè: **la maggior parte del
guadagno è spesa, non architettura.**

**FATTO.** Anthropic dichiara dove **non** funziona: domini in cui gli agent devono
condividere lo stesso context o hanno molte dipendenze reciproche (*"non adatti al
multi-agent oggi"*), e **il coding in particolare** (*"la maggior parte dei task di coding ha
meno compiti davvero parallelizzabili della ricerca"*). Più: il lead agent aspetta i
subagent in modo sincrono, i subagent non si parlano, un subagent lento blocca tutto.

**FATTO.** Cognition (*Don't Build Multi-Agents*, poi *Multi-Agents: What's Actually
Working*) e LangChain convergono su una regola sola: **il multi-agent è gestibile sulle
letture, non sulle scritture.** Formulazione di Cognition ripresa da LangChain: *"le azioni
portano decisioni implicite, e decisioni in conflitto portano risultati sbattagliati"*.
Anche nella loro posizione aggiornata, ciò che funziona sono setup in cui **più agent
contribuiscono ma le scritture restano su un thread solo**. Nota: Claude Code e OpenCode
usano sub-agent **solo in lettura**, che riportano all'agent principale.

**FATTO.** Sul debate multi-agent: *"il solo voto di maggioranza spiega la maggior parte dei
guadagni attribuiti al multi-agent debate"*. Il debate consuma **2,1-3,4× più token** con
accuratezza pari o inferiore all'auto-correzione isolata. Aumentare il numero di agent alza
l'accuratezza (è l'effetto del campionamento, come la self-consistency), mentre aumentare i
**round** la abbassa.

### R-11.2 — I FATTI contro, che riguardano specificamente noi

Vanno registrati perché **la nostra situazione cade esattamente nei due regimi** in cui
l'evidenza dice che il multi-agent recupera.

**FATTO — il beneficio è inversamente proporzionale alla forza del modello base.**
Sobhani et al., arXiv:2512.16698 (accettato ARR ottobre 2025), 4 benchmark di ragionamento
visivo, confronto controllato a modello fisso variando solo l'architettura:

| Modello | Effetto del multi-agent |
|---|---|
| Qwen-2.5-VL **7B** | **+6,8 punti** su Geometry3K |
| Qwen-2.5-VL 32B | +3,3 punti |
| Gemini-2.0-Flash (proprietario, forte) | **il single-agent resta migliore** sui benchmark classici |

Il 7B guadagna **il doppio** del 32B. La spiegazione degli autori: i modelli deboli hanno più
margine da recuperare tramite decomposizione, e il guadagno viene dall'**aggiungere struttura
con literal intermedi espliciti**, non dal fatto che gli agent si parlino.
**Noi giriamo un ~9B a 4 bit** (`AS-10`): siamo nella fascia che guadagna di più.

**FATTO — la condizione di confine di Tran & Kiela.** Il multi-agent torna competitivo in due
regimi: quando **l'utilizzo effettivo del context del singolo agent è degradato**, oppure
quando si spende più compute. **Il nostro context è affollato per progetto**: tool definition
nel prefisso, frammenti recuperati, digest della memoria, tutti in competizione dentro le
quote di `ADR-091`. È letteralmente il regime di "context utilization degradata".

**FATTO — il benchmark più vicino al nostro dominio non risponde alla nostra domanda.**
arXiv:2603.22651: 4 architetture di orchestrazione (sequenziale, parallela, gerarchica
supervisor-worker, riflessiva) × 5 modelli (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro,
Llama 3 70B, Mixtral 8x22B) × **10.000 filing SEC**, ground truth con 12 annotatori CFA/CPA
(κ = 0,91), 200.000 valutazioni in 21 giorni. La gerarchica batte la sequenziale
(F1 0,929 contro 0,903; accuratezza per documento 0,718 contro 0,648 su Claude 3.5 Sonnet).
**Ma il paper non contiene alcun baseline single-agent**: confronta forme di multi-agent fra
loro. Non dice se un agent solo avrebbe fatto meglio.

**FATTO — dallo stesso studio, un numero utile altrove.** L'architettura gerarchica ha
**12,4 % di fallimenti di coordinamento fra agent, contro 0 % della sequenziale**. Il costo
di coordinamento non è teorico.

### R-11.3 — Cosa se ne ricava per questa architettura

**INFERENZA (nostra), e ha cambiato l'argomento di `ADR-123`.** `A10` aveva rifiutato il
multi-agent con un argomento **economico** (costa e non è dimostrato che renda). L'evidenza
mostra che per noi l'argomento giusto è **di capacità, ed è molto più forte**: il multi-agent
compra qualità **con i token**, e noi abbiamo un tetto sui token che non è negoziabile con il
denaro. `ADR-039` fissa `max_model_len` come decisione di **capacità** — ogni token dichiarato
è concorrenza tolta al KV cache su una sola scheda da 20 GB (`AS-08`, confermata da
`ADR-068`). Un moltiplicatore 15× **non è acquistabile a nessun prezzo**: significa 15 volte
meno run concorrenti sullo stesso hardware. In più `ADR-104` (50 step, 10 minuti) chiude la
strada anche in verticale. **Per noi il multi-agent non è caro: è indisponibile.**

**INFERENZA (nostra).** Il contro-segnale di R-11.2 **non** raccomanda il multi-agent: indica
un rimedio più economico. Se il guadagno sui modelli piccoli viene dai **literal intermedi
espliciti** e non dal dialogo fra agent, allora lo stesso guadagno si insegue con schemi di
output più strutturati e passaggi intermedi dichiarati — che è già il secondo gradino della
scala dei rimedi di `A10`, prima di qualunque agent nuovo. → **`B-66`**.

---

## R-12 — Idempotenza e verificabilità delle scritture su Odoo (chiude `B-69`, ricerca del 2026-08-23)

Ricerca richiesta dal committente per portare `AS-35` da confidenza Bassa ad Alta.

### R-12.1 — Il fatto negativo, prima

**FATTO.** L'API esterna di Odoo **non ha** un meccanismo nativo di idempotency key. Una
chiamata `create` via XML-RPC/JSON-RPC non è idempotente: due invocazioni creano due record.
Un timeout di rete è il caso ambiguo classico — la richiesta è partita, il server l'ha
eseguita, il commit è avvenuto, la risposta si è persa al ritorno.

### R-12.2 — Il fatto positivo, che risolve il problema

**FATTO.** Odoo mantiene la tabella **`ir.model.data`**, che mappa un identificatore esterno
**scelto dal chiamante** — la coppia `(module, name)`, cioè l'XML ID — sulla coppia
`(model, res_id)` del record reale.

**FATTO — ed è il punto decisivo.** Su quella coppia esiste un **vincolo UNIQUE a livello di
PostgreSQL**, non un controllo applicativo. Nel sorgente (`odoo/addons/base/models/ir_model.py`):

```python
_sql_constraints = [
    ('module_name_uniq', 'unique(name, module)',
     'You cannot have multiple records with the same external ID in the same module!'),
]
```

che genera `alter table "ir_model_data" add constraint "ir_model_data_module_name_uniq"
unique(name, module)`. **L'arbitro è il database, non Python.** È esattamente ciò che serve:
un `search()` seguito da `create()` sarebbe vulnerabile alla race condition, un vincolo UNIQUE
no.

**FATTO.** Il metodo ORM **`load(fields, rows)`**, se `fields` include la colonna speciale
`id` contenente l'external ID, esegue un **upsert**: se l'external ID non esiste crea, se
esiste **aggiorna** il record già collegato. È lo stesso meccanismo dell'import CSV, in cui
la colonna `id` è documentata come *"external identifiers (used for creation or update)"*.

**FATTO.** Ogni record Odoo porta `create_uid`, `create_date`, `write_uid`, `write_date`.

**FATTO — limite importante.** Gli external ID **non** vengono creati automaticamente per i
record nati da una `create()` normale né dall'interfaccia utente: esistono solo per record
importati, esportati, o a cui l'external ID viene assegnato **esplicitamente**.

**FATTO — trappola operativa.** Modificare o cancellare righe di `ir.model.data` di **altri**
moduli può compromettere l'installazione e l'aggiornamento dei moduli stessi. Il flag
`noupdate` controlla se un aggiornamento di modulo può sovrascrivere il record.

**FATTO — il pattern alternativo, se servisse.** Aggiungere al modello target un campo
`x_idempotency_key` indicizzato con vincolo UNIQUE via `_sql_constraints`, e usare
*insert-first*: si tenta la `create()`, si cattura `psycopg2.IntegrityError`/`UniqueViolation`
e si rilegge il record esistente. Richiede però un modulo Odoo nostro sul target.

### R-12.3 — Cosa se ne ricava

**INFERENZA (nostra).** `AS-35` era formulata male. Chiedeva *"il sistema esterno onora una
idempotency key?"* — cioè trattava l'idempotenza come una concessione di Odoo. Ma
**l'external ID lo scegliamo noi**, e `AR-EV-09` stabilisce già che `idempotency_key` deriva
in modo deterministico da `(run_id, step_index)`. Scrivendo quella stessa chiave come external
ID Odoo dentro un namespace nostro, l'idempotenza **la costruiamo**, non la riceviamo.

Conseguenza sul recovery di `ADR-144`: dopo un crash, il caso `IN_FLIGHT` ambiguo si risolve
con **una lettura su un indice unico** — l'external ID c'è oppure non c'è — invece che con
una ricerca euristica sul dominio. La verificabilità smette di essere una speranza e diventa
una `SELECT`.

**INFERENZA (nostra) — il residuo, dichiarato.** Questo risolve **le creazioni**, che sono il
caso dominante e quello pericoloso. Non risolve automaticamente:

- le **transizioni di stato** del dominio (confermare un ordine, validare una fattura): non
  sono `create`, e la loro idempotenza va dichiarata **tool per tool** (`AR-RT-04`);
- l'**atomicità** fra la creazione del record e quella della riga `ir.model.data`: `load()` le
  fa nella stessa transazione Odoo, due chiamate RPC separate **no**. Vincolo sul connector,
  non speranza su Odoo.

---

## R-13 — Threat model degli agent (chiude `B-01`, `B-25`, `B-37`, `B-42`, `B-60`; ricerca del 2026-08-23)

Passata richiesta prima di scrivere `A13`. Cinque documenti avevano rimandato qui lo stesso
threat model.

**Nota sulle fonti.** La pagina ufficiale OWASP ha restituito **HTTP 403**: l'elenco
`ASI01`-`ASI10` qui sotto viene da **più fonti secondarie convergenti** (Cycode, F5,
NeuralTrust, Modulos, PointGuard, VamiSec), non dal documento originale. Il contenuto
concorda fra loro, ma **il testo normativo va riletto alla fonte** prima di citarlo in un
documento contrattuale. I paper arXiv sono citati per abstract quando il full text non era
raggiungibile: dove i numeri vengono da fonti secondarie, è detto.

### R-13.1 — `ASI01` … `ASI10`, l'elenco completo

| ID | Titolo | Contenuto |
|---|---|---|
| **ASI01** | Agent Goal Hijack | manipolazione di obiettivi, istruzioni o percorso decisionale |
| **ASI02** | Tool Misuse and Exploitation | uso non sicuro dei tool, o sfruttamento delle interfacce dei tool |
| **ASI03** | Identity and Privilege Abuse | abuso di credenziali, token o permessi **ereditati** |
| **ASI04** | Agentic Supply Chain Vulnerabilities | tool di terzi, plugin, registry, **server MCP**, componenti esterni |
| **ASI05** | Unexpected Code Execution | l'agent genera, modifica o esegue codice o comandi |
| **ASI06** | Context Management and Retrieval Manipulation | context recuperato o memorizzato **avvelenato, fuorviante, stantio o manomesso** |
| **ASI07** | Inter-Agent Communication | fiducia e comunicazione fra agent |
| **ASI08** | Cascading Failures | propagazione del guasto lungo catene di agent |
| **ASI09** | **Human-Agent Trust Exploitation** | l'agent usa output **persuasivi o fuorvianti** per indurre l'umano ad azioni o **approvazioni** non sicure |
| **ASI10** | Rogue Agents | agent compromessi, disallineati o alla deriva che continuano a operare |

**FATTO — affermazione forte e citata.** `ASI07`, `ASI08` e `ASI09` **richiedono soluzioni
architetturali**: i layer di guardrail su input e output, da soli, non possono affrontarli.

### R-13.2 — `ASI09`, la voce che nessuno dei nostri documenti aveva considerato

Sotto-pattern catalogati:

- **approval fatigue** — le richieste di conferma, se troppo frequenti e non differenziate,
  perdono efficacia: si approva per riflesso;
- **fake explainability** — l'agent fabbrica motivazioni plausibili per nascondere la logica
  vera;
- **insufficient explainability** — il ragionamento è opaco e l'utente non può contestarlo;
- **emotional manipulation** — segnali antropomorfi per indurre azioni non sicure;
- **consent laundering via read-only previews** — effetti collaterali in un pannello che
  l'utente crede di sola lettura;
- **missing confirmation** — una singola conferma copre un'azione irreversibile;
- **phantom agent** — impersonare l'interfaccia di un agent legittimo per raccogliere
  approvazioni.

Mitigazioni riportate: **canale di conferma separato** per le azioni ad alto impatto;
monitoraggio delle **anomalie nelle richieste di approvazione**; approvazioni **ritardate**
per le azioni rischiose; **attribuzione obbligatoria** (quale agent, quale task, quale
azione); presentare **incertezza e contro-argomenti** invece di una raccomandazione sola;
**verifica indipendente** delle affermazioni dell'agent prima di mostrarle; interfacce che
incoraggiano la valutazione critica invece dell'approvazione passiva; **doppio operatore**
per le azioni ad alto rischio; rotazione contro l'affaticamento.

Riferimenti incrociati riportati: MITRE ATT&CK, OWASP LLM01:2025, `AML.T0051`,
NIST AI RMF `GV.6.1`. Esiste una regola pubblica dedicata (`ATR-2026-00118`, approval fatigue).

### R-13.3 — Memory poisoning (`ASI06`): i numeri

**FATTO (da fonti secondarie sul paper MINJA, arXiv:2503.03704, NeurIPS 2025).**
**MINJA** avvelena la memoria di un agent **con la sola interazione da utente normale** —
nessun accesso privilegiato allo store: **98,2 % di injection success rate** e
**76,8 % di attack success rate**. Tre tecniche: *bridging steps* che collegano una domanda
benigna a una traiettoria malevola; *indication prompts* che inducono **l'agent stesso** a
generare e salvare la voce (l'attaccante non scrive mai nel database); *progressive
shortening* che rimuove i segni di intento fino a farla sembrare naturale. Le rate
generalizzano su GPT-4o-mini, Gemini-2.0-Flash e **Llama-3.1-8B** — cioè anche su modelli
della **nostra** fascia.

**FATTO — perché le difese usuali non funzionano.** Le difese valutate (LlamaGuard,
sanificazione a livello di embedding, detection su prompt) si sono rivelate **inefficaci**
contro MINJA. La ragione è strutturale: **auditano i record in isolamento**, e il contenuto
malevolo appare benigno finché non lo si guarda insieme a una specifica query.
**I detector basati su LLM mancano il 66 % delle voci avvelenate.**

**FATTO (studio sistematico, arXiv:2606.04329).** Quattro canali di scrittura in memoria e
nove vulnerabilità strutturali, in sei classi di attacco; benchmark `MPBench`. Due conclusioni
citabili: **gli agent che scrivono e recuperano memoria in modo più aggressivo sono più
sfruttabili**, e **le difese esistenti contro la prompt injection non coprono il memory
poisoning**.

### R-13.4 — Confused deputy e identità (`ASI02`, `ASI03`)

**FATTO — il controllo primario raccomandato.** *Identity down-scoping*: ridurre i privilegi
dell'agent a quelli dell'utente delegante **a runtime**. Il pattern è chiamato **"Blended
Identity"** — le decisioni di accesso combinano l'identità di workload dell'agent **e**
l'identità del principal umano, applicando least privilege **su ogni richiesta**.

**FATTO.** Secondo controllo raccomandato: **credential brokering** invece di segreti
incorporati, perché il perimetro dell'agent cambia a ogni task.

**FATTO — incidente reale, marzo 2026.** La campagna di supply chain **TeamPCP** ha
compromesso **LiteLLM**, un gateway AI usato da migliaia di aziende. Proprio perché il suo
scopo era **concentrare le API key** di decine di servizi, gli attaccanti hanno raccolto
chiavi SSH, credenziali cloud, API key e password di database: stima di **500.000 identità
aziendali** colpite.

**FATTO — lacuna dichiarata.** Gli *handoff* multi-agent restano coperti male: quando l'agent
A delega a B, **chi controlla il passaggio?** L'escalation lungo la catena di delega è un
vettore distinto.

### R-13.5 — Multi-agent (`ASI07`, `ASI08`, `ASI10`) e completezza dei framework

**FATTO (arXiv:2603.09002, risposta a una RFI del NIST).** Le tre proprietà che definiscono
un sistema multi-agent dal punto di vista della sicurezza: **autorità di tool delegata**,
**memoria persistente condivisa**, **comunicazione fra agent**. Gli autori sostengono che il
multi-agent introduce vulnerabilità **qualitativamente distinte**.

**FATTO — ed è il dato epistemicamente più importante della passata.** Lo studio cataloga
**193 voci di minaccia in 9 categorie** e valuta 16 framework: **nessun framework raggiunge
la copertura maggioritaria in una singola categoria**. OWASP è il migliore con **65,3 %**.
Le categorie coperte peggio sono **Non-Determinism** (1,231 su 3) e **Data Leakage** (1,340).

**Conseguenza per noi:** nessun framework può essere trattato come una checklist completa.
`ASI01`-`ASI10` è un punto di partenza, non una garanzia di copertura.

### R-13.6 — Cosa se ne ricava per questa architettura

**INFERENZA (nostra) — validazioni esterne di scelte già fatte.**

| Nostra decisione | Riscontro esterno |
|---|---|
| `ADR-105` dual principal, autorità = intersezione | **è esattamente il pattern "Blended Identity"** raccomandato come controllo primario contro il confused deputy |
| `ADR-108` Credential Broker | **è il "credential brokering"** raccomandato contro i segreti incorporati |
| Rifiuto del Model Gateway (`A05`) | **l'incidente LiteLLM è quel rischio realizzato**: concentrare le credenziali in un punto solo |
| `ADR-094` nessuna estrazione automatica di memoria | **direttamente sostenuto**: "gli agent che scrivono memoria in modo più aggressivo sono più sfruttabili" |
| `INV-12` il PDP non legge mai la memoria | **è la sola difesa che regge**, dato che i detector mancano il 66 % delle voci avvelenate |
| `AR-KN-03`/`AR-ME-06`/`AR-AC-12` `trust_class = retrieved` | coerente con `ASI06` |
| `ADR-063` materializzazione umana per MCP | coerente con `ASI04` |
| `ADR-049` divieto di SQL, nessun argomento è un programma | coerente con `ASI05` |

**INFERENZA (nostra) — la lacuna vera, e non è piccola.** `ADR-023` impone **approvazione
umana su ogni `SIDE_EFFECT`** ed è il controllo su cui poggiano `R-26`, `R-33` e metà delle
mitigazioni dell'architettura. **`ASI09` dice che quel controllo è esso stesso una superficie
d'attacco**, e che i guardrail non bastano: serve una risposta **architetturale**.

Nessuno dei nostri dodici documenti ha affrontato l'approval fatigue, la fake explainability
o il consent laundering. **È il buco principale che `A13` deve chiudere.** Peggiora perché
`T-RT-04` prevede già attese di approvazione lunghe e frequenti, cioè esattamente le
condizioni che producono l'approvazione riflessa.

---

## R-14 — Cosa è permesso fare a un agent su CRM/ERP (ricerca del 2026-08-23)

Passata richiesta dal committente per verificare se l'architettura stia dando all'agent
troppi poteri. Quattro fronti: norme, pratica dei vendor, responsabilità contabile, incidenti.

### R-14.1 — AI Act

**FATTO.** Calendario di applicazione:

| Data | Cosa scatta |
|---|---|
| 2 ago 2025 | obblighi sui modelli general-purpose |
| **2 ago 2026** | **obblighi di trasparenza (art. 50)** + **regime sanzionatorio pienamente esigibile** + autorità nazionali operative |
| 2 dic 2026 | marcatura e rilevamento per sistemi immessi prima di agosto; due divieti assoluti nuovi |
| **2 dic 2027** | sistemi ad **alto rischio** (Allegato III), capo III sezioni 1-3 |
| 2 ago 2028 | alto rischio collegato ai prodotti dell'Allegato I |

**CONFLITTO DI FONTI — `B-90`.** Una fonte afferma invece che gli obblighi alto rischio sono
entrati in vigore il **2 agosto 2026**. Esiste inoltre una proposta *omnibus* che potrebbe
spostare le scadenze. **Da verificare alla fonte prima di costruirci sopra una scadenza.**

**FATTO.** Sanzioni: fino a **35 M€ o 7 %** del fatturato per pratiche vietate; **15 M€ o 3 %**
per violazioni sull'alto rischio; **7,5 M€ o 1 %** per informazioni false. Per PMI e start-up
si applica **l'importo minore** fra i due parametri.

**FATTO.** In Italia vigila l'**ACN** (poteri ispettivi e sanzionatori), notifica l'**AgID**.
Legge 23 settembre 2025 n. 132; decreto attuativo approvato in esame preliminare il 10 giugno
2026.

**FATTO.** La classificazione dipende dal **caso d'uso**, non dalla tecnologia. Alto rischio
(Allegato III): selezione di candidati, valutazione dell'affidabilità creditizia, accesso a
servizi essenziali. Un agent che aggiorna opportunità commerciali normalmente **non** vi
rientra; un agent che produce scoring usato per decidere fidi o condizioni **probabilmente sì**.

**FATTO — art. 14(4), sorveglianza umana.** Chi sorveglia un sistema ad alto rischio deve poter:
(a) comprendere capacità e limiti e rilevare anomalie; **(b) restare consapevole della
"possibile tendenza a fare automaticamente affidamento o eccessivo affidamento sull'output
prodotto da un sistema di IA ad alto rischio (*automation bias*)"**; (c) interpretare
correttamente l'output; (d) decidere di non usare il sistema, o ignorarne, annullarne o
ribaltarne l'output; **(e) intervenire o interrompere il sistema tramite un "pulsante di stop"
o procedura simile** che lo porti in uno stato sicuro.

**FATTO.** L'art. 14 è principalmente un obbligo del **provider** (rendere la sorveglianza
*possibile*); l'art. 26(2) obbliga il **deployer** ad assegnare personale qualificato con
autorità e competenza (rendere la sorveglianza *effettiva*).

**FATTO — critica accademica.** L'AI Act impone **consapevolezza** dell'automation bias — uno
stato psicologico difficile da provare o far rispettare — invece di imporre **risultati
misurabili di de-biasing**. La legge chiede meno di quanto servirebbe.

### R-14.2 — GDPR

**FATTO.** L'art. 22 vieta le decisioni basate **unicamente** su trattamento automatizzato che
producano effetti giuridici o similmente significativi. L'eccezione è l'intervento umano, ma
**"l'intervento umano deve essere sostanziale, non meramente formale"**.

**FATTO.** La profilazione (art. 4(4)) riguarda "qualsiasi forma di trattamento automatizzato",
non solo quello "unicamente" automatizzato: un CRM può fare profilazione senza ricadere
nell'art. 22, restando però soggetto a informativa, base giuridica e valutazione d'impatto.

**FATTO.** Sentenza **C-634/21 (SCHUFA)**: la nozione di "decisione" include anche **lo scoring
prodotto da un terzo su cui un altro soggetto basa in modo determinante la propria scelta**.

### R-14.3 — Scritture contabili (Italia)

**FATTO.** L'obbligo di tenuta e la responsabilità per le registrazioni restano
**dell'imprenditore**: né il software né il consulente lo sollevano. **L'automazione non
trasferisce la responsabilità.**

**FATTO.** Art. 2215-bis c.c. (tenuta con strumenti informatici) e art. 2220 c.c.
(conservazione decennale). **Non è ammesso modificare direttamente o cancellare le
registrazioni già effettuate**: ogni correzione avviene con una **nuova scrittura di rettifica**
che lascia traccia dell'errore originario.

**FATTO.** I gestionali hanno funzioni di **override** che forzano gli automatismi contabili;
i profili autorizzativi e **il log delle forzature diventano oggetto di verifica del revisore**.

### R-14.4 — Segregation of Duties

**FATTO.** La SoD distribuisce una transazione sensibile fra parti separate perché nessuno
controlli l'intero ciclo. **Gli agent collassano i confini fra i ruoli**: le identità non umane
sono spesso create e gestite **fuori dal normale ciclo di vita delle identità**, e i loro
permessi si allargano incrementalmente con poca revisione dell'insieme.

**FATTO — raccomandazioni convergenti.** (1) trattare gli agent come identità soggette alle
stesse regole; (2) tenere l'umano nel passo di autorizzazione, con audit trail che **separa chi
ha iniziato l'azione da chi l'ha autorizzata**; (3) applicare nel sistema, non sulla carta;
(4) **rilevare i conflitti prima dell'esecuzione, non dopo**.

**FATTO.** *"L'agent non è mai il soggetto responsabile: è un'identità, non un attore
imputabile."* La responsabilità va assegnata a un **proprietario umano nominato** che certifica
gli accessi dell'agent, più un autorizzatore umano sulle transazioni sensibili.

**FATTO.** Per i team piccoli si usano **controlli compensativi**: firma di un supervisore,
revisione di un commercialista esterno, rotazione delle mansioni.

### R-14.5 — Incidenti reali

**FATTO.** Almeno **nove casi documentati** di agent autonomi che hanno danneggiato ambienti di
produzione cancellando dati, database o sistemi vivi — da un censimento di 390+ aziende in 13
settori dal 2018 a giugno 2026. **Quasi uno al mese da luglio 2025**, ciascuno documentato dal
post-mortem dell'operatore stesso. Caso PocketOS: database di produzione distrutto in **9
secondi**.

**FATTO.** Un'indagine 2026 riporta che l'**88 % delle organizzazioni** ha avuto un incidente di
sicurezza legato ad agent, confermato o sospetto, nell'anno precedente.

**FATTO — il pattern di causa.** *"Quasi nessuno è un'allucinazione. L'intenzione del modello
era di solito corretta e noiosa. Il danno è avvenuto un livello più sotto: nel quoting della
shell, nell'espansione della tilde, nel parsing di un exit code, in un flag di database
documentato ma pericoloso."*

**FATTO — due frasi che ci riguardano.** *"Nel pattern più comune, l'agent ha trovato una
credenziale che non avrebbe mai dovuto avere e l'ha usata."* E: *"uno ha ereditato i permessi
elevati di un ingegnere ed è passato attraverso un gate di approvazione a due persone."*

**FATTO — raccomandazioni.** Eliminare il **privilegio permanente**: accesso *just-in-time*,
limitato al compito, revocato al completamento. E **mappare l'albero delle azioni nel caso
peggiore prima del deployment** — non cosa l'agent fa, ma cosa **può** fare con i suoi
permessi — tagliando i rami irrecuperabili **a livello di permesso**.

### R-14.6 — Cosa fanno i vendor sulla conferma delle scritture

**FATTO — la convenzione.** *"Le operazioni di lettura non critiche vengono eseguite
automaticamente, mentre le operazioni di scrittura — creare, aggiornare, annullare — sono gated
da una conferma binaria. **Questa divisione read-auto/write-gated è la convenzione fra i
vendor.**"*

**FATTO — Amazon Bedrock Agents.** La conferma **sospende l'orchestrazione** ed espone
all'utente **la funzione che sta per essere chiamata e i valori dei parametri**.

**FATTO — Microsoft 365 Copilot.** `GET` non chiede conferma; `POST`, `PATCH`, `PUT`, `DELETE`
**sì**. Sui tool MCP il flag è `readOnlyHint`; sulle API plugin è `x-openai-isConsequential`.
E: *"generalmente non si può rimuovere il passo di approvazione per le operazioni che creano o
aggiornano record dal lato consumatore: **è imposto dal modello di consenso di Copilot**"*.
Alcuni sviluppatori si lamentano che il prompt compaia a ogni interazione; Microsoft risponde
che fa parte del modello di sicurezza e consenso.

**FATTO — Magentic-UI (Microsoft Research).** Ogni azione porta un'euristica di irreversibilità
decisa dallo sviluppatore: **sempre / forse / mai**. "Sempre" chiede approvazione binaria,
"mai" esegue automaticamente, "forse" passa a un giudice LLM.

**NON VERIFICATO — `B-91`.** Il default di **Salesforce Agentforce** sulle scritture: le due
pagine di documentazione dal titolo pertinente (*"Confirmation Required for Agentforce
Actions"*, id `005133036`) **non si sono caricate**.

**FATTO — le tre posture.** *human-in-the-loop* (approvazione **prima** dell'azione);
*human-on-the-loop* (l'azione parte, una persona osserva e può intervenire durante o subito
dopo); *autonomo* (nessun checkpoint).

**FATTO — la raccomandazione di governance è a livelli, non uniforme.** *"Stratificare per
raggio d'azione dell'azione, non per agent."* E: *"le organizzazioni che usano modelli di
autorizzazione a livelli hanno drasticamente meno incidenti di quelle che usano
un'autorizzazione binaria."*

**FATTO — promozione graduata.** *"Ogni agent parte al livello 1 e viene promosso solo dopo
aver dimostrato affidabilità, tracciando il tasso di errore per agent: la promozione richiede
un tasso sotto il **2 % per 30 giorni consecutivi**."*

### R-14.7 — Odoo: comportamento di scrittura e cancellazione

**FATTO — e cambia l'ordine di pericolosità dei verbi.** In Odoo **nessun campo è tracciato per
default**: un campo conserva il valore precedente solo se dichiarato `tracking=True`. Nei
moduli standard lo sono lo *stage*, lo *state* e una manciata di campi chiave. **Per tutto il
resto, dopo un `UPDATE` il valore precedente non esiste più.**

**FATTO.** Quando c'è, il valore finisce in `mail.tracking.value` (`old_value_char`,
`old_value_float`, …). Il meccanismo copre bene solo campi scalari e `many2one`; `many2many` e
`one2many` sono gestiti male (esiste il modulo OCA `mail_improved_tracking_value`).

**FATTO.** `active = False` (archiviazione) è un soft delete: record e relazioni **restano nel
database**, spariscono dalle viste per via del dominio `active_test`, e **si torna indietro
disarchiviando**.

**FATTO.** `unlink()` è distruttivo. Su `res.partner` le dipendenze sono pervasive (fatture,
ordini, messaggi, `res.users`); di norma l'ORM solleva un errore di chiave esterna, ma dove è
dichiarato `ondelete='cascade'` o `set null` **si possono perdere o orfanare dati collegati in
silenzio**.

**FATTO — importante.** **`unlink()` non passa da `write()`**, quindi salta le automazioni
agganciate alla scrittura (log di audit, sincronizzazioni, azioni "On Update"): *"una fonte
comune di incoerenza silenziosa con i sistemi esterni"*. L'archiviazione invece **è** una
`write`, quindi le automazioni scattano.

**FATTO.** Il ciclo bulk "cerca `active = False` e cancella" è definito *"un vero autogol"* su
`res.partner`, perché i partner archiviati spesso reggono ancora registrazioni contabili vive.

### R-14.8 — Cosa se ne ricava

**INFERENZA (nostra).** La politica **lettura automatica / scrittura confermata** è lo standard
corrente, non un eccesso di prudenza: Microsoft la impone senza permettere di disattivarla,
Amazon la implementa nella stessa forma, le fonti la chiamano *convenzione fra vendor*.

**INFERENZA (nostra) — la tensione centrale, dichiarata.** Confermare **ogni** scrittura su
**ogni** entità massimizza la **frequenza** delle conferme, e la frequenza alta con conferme
indifferenziate è la definizione operativa dell'approval fatigue (`ASI09`, e *automation bias*
nell'art. 14(4)(b)). La sintesi adottata separa due domande: **se** serve la conferma (sempre,
`ADR-216`) da **che forma** ha (variabile per reversibilità, `ADR-191`).

**INFERENZA (nostra).** `ADR-191` e `ADR-212` non sono solo buona pratica di sicurezza:
**anticipano l'art. 14(4)(b) ed (e) dell'AI Act**. L'attrito differenziato contro
l'approvazione riflessa e il pulsante di stop sono ciò che la legge chiederà ai sistemi ad alto
rischio.

**INFERENZA (nostra).** `UPDATE` è il verbo più pericoloso dei tre — irreversibile per
mancanza di tracking, silenzioso, ad alta frequenza — ed è quello che tutti considerano
innocuo. È il vettore di `R-79` (corruzione lenta), che senza il valore precedente non era
nemmeno ricostruibile.

---

## R-15 — Prassi dei maggiori sulla retention, i backup e la SoD (ricerca del 2026-08-23)

Passata mirata sui rischi `R-87`, `R-92`, `R-95`, `R-96`.

### R-15.1 — Retention del testo di conversazione: 30 giorni è la convergenza

**FATTO.** OpenAI API: **30 giorni** di default, con *zero data retention* disponibile.
Anthropic API: **30 giorni** richiesti sui modelli più avanzati, con varianti ZDR; per le
violazioni d'uso la retention può salire a due anni sugli input/output e sette anni sui
punteggi di classificazione. Salesforce Einstein Trust Layer: audit e feedback **30 giorni**.

**FATTO — confine importante.** *"La ZDR copre solo l'infrastruttura del fornitore del modello;
il livello di storage dell'applicazione è una questione separata."*

**FATTO.** Salesforce **maschera i dati prima** che passino al gateway verso il provider
esterno del modello.

**INFERENZA (nostra).** Per noi il fornitore del modello **siamo noi**: modello locale,
processo senza rete, `AR-DG-16` vieta staticamente l'invio del context a un provider esterno.
**La zero data retention verso terzi è quindi una proprietà strutturale, non una promessa
contrattuale.** Il nostro problema è interamente nello strato applicativo — cioè `R-87`.

### R-15.2 — Backup e diritto alla cancellazione: la posizione "beyond use"

**FATTO.** Il GDPR **non prevede esenzioni per i backup**: il diritto alla cancellazione si
estende anche a quelli.

**FATTO — ICO.** È sufficiente che i dati di backup siano messi **"beyond use"** (fuori uso)
anche se non sovrascrivibili subito, a tre condizioni: non usarli per nessun altro scopo;
impegnarsi alla cancellazione permanente quando possibile; **essere assolutamente chiari con
l'interessato su cosa accadrà ai suoi dati, backup compresi**. Quest'ultima è indicata come la
parte che le organizzazioni disattendono più spesso.

**FATTO — il pattern tecnico raccomandato.** *"Un pattern ingegneristico comune è mantenere una
**suppression list** — un database che contiene tutte le richieste di cancellazione, rigiocato
contro i dati ripristinati, così che quando il database ripristinato entra in uso nessuno degli
utenti che ha chiesto la cancellazione sia presente."*

**INFERENZA (nostra).** È il `deletion_ledger` di `ADR-237`, nella stessa forma. Validazione
esterna di una decisione presa per ragionamento interno.

**FATTO — termini.** La richiesta va evasa **senza ingiustificato ritardo ed entro un mese
solare**, prorogabile fino a due mesi se particolarmente complessa, ma **la proroga va
comunicata prima della scadenza del primo mese**.

**FATTO — divergenza fra autorità.** La **CNIL** francese ha indicato che non è necessario
cancellare i backup; l'autorità **danese** afferma che i dati vanno cancellati dai backup dove
tecnicamente possibile. **La posizione del Garante italiano NON è stata verificata** → `B-104`.

**FATTO — enforcement.** Il rapporto **EDPB di febbraio 2026** (32 autorità, 764 titolari
esaminati) ha individuato **la gestione dei backup fra le sette criticità sistemiche**, e più
autorità hanno confermato che ne useranno i risultati per l'attività sanzionatoria dal 2026.

**FATTO.** L'archiviazione offline resta **trattamento** ai sensi del GDPR e richiede una base
giuridica.

### R-15.3 — Segregation of Duties: nessun baseline pubblico, ma numeri sì (chiude `B-97`)

**FATTO.** **Non esiste una matrice SoD pubblica autorevole.** La matrice ISACA, la più citata,
porta un disclaimer esplicito: *ISACA non sostiene che la Segregation of Duties Control Matrix
sia uno standard di settore*, perché funzioni, mansioni, processi e rischi variano fra
organizzazioni.

**FATTO — ordini di grandezza.** Un programma SAP maturo conta **150-200 rischi** SoD; sotto i
**100** il ruleset è considerato incompleto; i set pre-costruiti di fornitori terzi vanno da
**45 a 125**. OpenIAM ne distribuisce **45**, mappate su SOX, IFC e COBIT, derivate da ISACA,
PCAOB e documentazione SAP.

**FATTO — attenzione ai conteggi.** Il numero di regole di SAP GRC (espanse a livello di
permesso) non è comparabile con il conteggio "45 regole" di un fornitore (livello di rischio).

**FATTO — limite di SAP GRC.** Applica la SoD **solo dentro il confine SAP**: non governa
Microsoft 365, Salesforce o altri sistemi collegati.

**INFERENZA (nostra).** Il nostro motore SoD sta **fuori** da Odoo, nel PDP: può quindi vedere
conflitti che attraversano i sistemi, cosa che SAP GRC non fa. Ma vale il contrario: **i
controlli nativi di Odoo non ci coprono le spalle**, quindi un registro vuoto non ha una
seconda rete sotto.

---

## Ricerche ancora da fare (backlog)

Segnate qui per non dimenticarle quando si arriva al documento pertinente.

| ID | Cosa verificare | Serve al documento |
|---|---|---|
| ~~B-01~~ | **CHIUSA** il 2026-08-23 → vedi **`R-13`** | Elenco `ASI01`-`ASI10` verificato (da fonti secondarie convergenti; **la pagina OWASP ufficiale ha dato 403, il testo normativo va riletto alla fonte**). **Scoperta principale: `ASI09` Human-Agent Trust Exploitation è una lacuna aperta della nostra architettura** |
| B-02 | Maturità binding Python di Cedar | A/03 governance |
| B-03 | Maturità SDK Python MCP `2026-07-28` | C/07 MCP |
| B-04 | Stato pubblicazione COSAiS agent overlays | C/26 compliance |
| B-05 | pgvector: stato HNSW/quantizzazione e limiti di scala | A/07 knowledge |
| B-06 | OpenTelemetry GenAI semantic conventions: stato di stabilità | A/12 observability |
| B-07 | SPIFFE/SPIRE: costo operativo reale per un deployment single-node | A/09 identity |
| B-08 | EU AI Act: obblighi effettivi per un CRM agent non high-risk | A/14 data governance |
| B-09 | Pattern di control plane delle piattaforme di agent enterprise (AWS AgentCore, Microsoft Foundry, Google): registrazione agent, rappresentazione dei deployment, aggancio delle policy | A/02 control plane — prima del gate di Level A |
| B-10 | Kubernetes, documentazione primaria su reconciliation e resource model | A/02 — verifica che il rifiuto della riconciliazione sia argomentato correttamente |
| B-11 | Taint tracking / information flow control per sistemi LLM: esiste un approccio praticabile per impedire che dati a bassa fiducia finiscano in azioni verso l'esterno? | A/13 security, B/12 trust — è il problema aperto dichiarato in A03 §32 (composizione di azioni lecite) |
| B-12 | Matrice di supporto vLLM × Qwen3.5 | **A/05 — ALTA, blocca il `ModelProvider`** |
| B-13 | Tool parser disponibile per Qwen3.5 nel serving scelto | **A/05 — ALTA** |
| B-14 | Context nominale del modello vs `max_model_len` realistico su 20 GB VRAM | **A/05 — ALTA** |
| B-15 | Esistono checkpoint AWQ/GPTQ affidabili per Qwen3.5-9B? | **A/05 — ALTA. Se no, la scelta del serving si rovescia su GGUF/llama.cpp** |
| B-16 | Costo del guided decoding (constrained decoding) sul throughput | A/05 |
| B-17 | Determinismo con `seed` sotto continuous batching: quanto è ottenibile? | A/05, C/29 replay |
| B-18 | llama.cpp server: stato di tool calling e grammar | A/05 |
| B-19 | Firma e provenance degli artifact di modello | A/05, C/25 supply chain |
| B-20 | Degrado della tool selection in funzione del numero di tool su un modello ~9B | **A/06 — ALTA. Regge `AS-10`, che è la base del budget del prefisso** |
| B-21 | Multi Round-Trip Requests di MCP: come si gestiscono | C/07 MCP |
| B-22 | Costo in token di una tool definition | A/06 — si misura, non si cerca |
| B-23 | Il CRM target offre idempotency key o un marcatore verificabile? | **A/06 — ALTA appena `Q-01` è chiusa. Regge `AR-RT-04`** |
| B-24 | Integrità delle tool definition provenienti da server MCP | C/07, A/13 |
| ~~B-25~~ | **CHIUSA** il 2026-08-23 → vedi **`R-13`** | `ASI02` tool misuse, `ASI04` supply chain (server MCP), `ASI05` code execution. Le nostre `ADR-049`, `ADR-063`, `AR-TL-*` risultano allineate |
| **B-26** | **Latenza p95 e throughput reali di un modello di embedding su CPU, sull'hardware target.** È una **misura**, non una ricerca bibliografica | **A/07 — PRIORITÀ MASSIMA. Regge `ADR-068`, `AS-14`, `T-KN-01`, e quindi `AS-08`. Un pomeriggio di lavoro che può invalidare la decisione principale di `A07`. Va fatta PRIMA delle misure VRAM di `A05`** |
| B-27 | Candidati concreti di embedding model multilingua it/en open-weight: licenza, dimensione del vettore, finestra di input, qualità dichiarata | **A/07 — ALTA. Chiude `DEF-02` e `ADR-087`. Scadenza: prima dello schema** |
| B-28 | pgvector: dimensione massima indicizzabile, stato di HNSW e della quantizzazione, limiti pratici (specializza `B-05`) | A/07 — `ADR-070`, `ADR-087` |
| B-29 | Ricerca vettoriale filtrata: il motore garantisce `k` risultati sotto un filtro molto selettivo? Esiste una modalità iterativa? | **A/07 — regge `R-25`, il rischio di recall degradato in silenzio** |
| B-30 | Librerie di parsing PDF/DOCX/HTML: qualità su layout a colonne e tabelle, licenza | A/07 — `ADR-086`, `R-31` |
| B-31 | Chunking di tabelle e spreadsheet: approcci con evidenza | A/07 |
| B-32 | Attacchi di inversione degli embedding: quanto testo si recupera da un vettore | A/07 — `R-27`, `AR-KN-18` |
| B-33 | Side channel temporale sul prefix cache fra tenant nei serving runtime | A/07, A/13 — `R-28` |
| B-34 | Fusione dei risultati: evidenza comparativa fra fusione per rank e alternative calibrate | A/07 — `ADR-070` |
| B-35 | Modello ACL della sorgente documentale target (record rule di Odoo, o del DMS) e come proiettarlo in `grant` | **A/07 — regge `ADR-072` e `AS-15`. Dipende da `Q-01`** |
| B-36 | Esiste evidenza pubblica misurata sull'**accuratezza dell'estrazione automatica di memoria** da conversazioni (precision/recall, falsi positivi)? | **A/08 — regge `ADR-094`.** Senza, la decisione conservativa resta l'unica difendibile |
| ~~B-37~~ | **CHIUSA** il 2026-08-23 → vedi **`R-13`** | `ASI06`. **MINJA: 98,2 % injection, 76,8 % attack success, con la sola interazione da utente normale.** I detector LLM mancano il **66 %** delle voci avvelenate → `INV-12` è l'unica difesa che regge, `ADR-094` è confermata |
| B-38 | Costo in token di un digest strutturato **contro** lo stesso journal in prosa, sullo stesso tokenizer | A/08 — `ADR-090`, `ADR-091`. **È una misura**, non ricerca bibliografica |
| B-39 | I *temporal constraints* di PostgreSQL 18 sono applicabili a `valid_from`/`valid_until` per impedire sovrapposizioni? | A/08 — `ADR-102`. Parte dal `FATTO` già registrato in `R-05` |
| B-40 | Evidenza sul **degrado di qualità con context riempito da informazione irrilevante** ("context rot"): esiste una misura? | A/08 — `ADR-091`. Se il degrado è forte, le quote generose sono controproducenti |
| B-41 | **Memory inference**: è possibile dedurre memorie di altri soggetti dalle risposte dell'agent? Esiste letteratura? | A/13 — **è l'unica minaccia del threat model di `A08` senza difesa dichiarata** |
| ~~B-42~~ | **CHIUSA** il 2026-08-23 → vedi **`R-13`** | `ASI03`. Il controllo primario raccomandato è **"Blended Identity"**, che è esattamente il nostro `ADR-105` (dual principal). `ADR-108` corrisponde al *credential brokering*. **Incidente LiteLLM/TeamPCP** conferma il rifiuto del Model Gateway |
| B-43 | Un `sub` OIDC può essere riassegnato dopo la cancellazione di un utente? Quali IdP garantiscono `email_verified`, e con quale semantica? | **A/09 — ALTA.** Regge `ADR-107` e `AR-ID-10` |
| B-44 | Durate raccomandate correnti per sessione assoluta, sessione di inattività, access token | A/09 — oggi sono `NON ANCORA DECISO` |
| ~~B-45~~ | **CHIUSA** il 2026-08-23 → vedi **`R-09`**. Argon2id `m=47104, t=1, p=1`, `argon2-cffi` | **`ADR-120`**. Non blocca più l'implementazione |
| B-46 | Quanto è realisticamente garantibile l'azzeramento di materiale crittografico in memoria in Python | A/09 — regge `INV-14` |
| ~~B-47~~ | **CHIUSA** il 2026-08-23 → vedi **`R-10`**. Odoo **non ha OAuth** per l'API esterna (decisione del committente coerente col prodotto). Ma ha **API key per singolo utente** dalla 14: è quella la strada per la catena 1 | **`ADR-114` amendata, `T-ID-08` ripuntato.** Resta aperta la deprecazione RPC → **`B-53`** |
| B-48 | Quale campo del CRM target può portare un marcatore di correlazione senza inquinare i dati di dominio | A/09 — `AR-ID-17`. Dipende da `Q-01` |
| ~~B-49~~ | **CHIUSA** il 2026-08-23 → vedi **`R-10`**. Odoo **non riusa** gli ID (`SERIAL` monotono). Restano due caveat: `setval()` manuale, e utenti archiviati invece che cancellati | **`AS-24` sale ad Alta. `ADR-122`** aggiunge il discriminante come assicurazione a basso costo |
| B-50 | Approcci praticabili di cifratura per-tenant senza gestione di chiavi da parte del cliente | A/09, A/14 — regge `R-47`, `R-48`; connesso al crypto-shredding rimandato da `A08` |
| B-51 | Binding della sessione a caratteristiche della richiesta: efficacia reale contro il furto di sessione, falsi positivi | A/09, A/13 |
| B-52 | Guidance corrente su OAuth 2.x per la delega ad agent (pattern di abuso, token exchange); e se SAML sia davvero richiesto nel mid-market CRM/ERP | A/09 — Bassa Day-1, **Alta prima della catena 1** |

| **B-53** | **Confermare la deprecazione delle API RPC di Odoo**: XML-RPC/JSON-RPC rimosse in Odoo 22 (autunno 2028)? La External JSON-2 API è il sostituto? Quale timeline per Odoo Online? | **A/18 — ALTA prima di scegliere il connector.** Non si costruisce su un protocollo con la data di scadenza. `R-10` lo riporta come `DA VERIFICARE`, non letto in originale |
| B-54 | Operatività delle API key per-utente di Odoo: chi le genera, si possono creare per conto di un utente, hanno scadenza, sono revocabili singolarmente? | **A/09, A/18 — regge la catena 1, quindi `R-41`** |
| B-55 | `users_ldap_groups` (OCA): stato di manutenzione sulle versioni Odoo correnti, e se il bug storico del mancato aggiornamento dei gruppi ai login successivi sia risolto | `ADR-121`. Un gruppo che non si aggiorna è un permesso che non si revoca |
| **B-56** | **A2A v1.0: come si esprime l'attenuazione dell'autorità?** Il *token downscoping* è un gap dichiarato (`R-02`): esiste un pattern raccomandato, un'extension, o va costruito applicativamente? | **A/10, C/31 — ALTA prima della fase 3.** Regge `ADR-131` e `R-57`. Decide se A2A ci serve come protocollo o solo come formato |
| B-57 | `AgentCard`: quali campi sono normativi, esiste un meccanismo di firma o verifica dell'origine? | A/10, C/31 — `AR-AC-17` |
| ~~B-58~~ | **CHIUSA** il 2026-08-23 → vedi **`R-11`**. Nove fonti, cinque primarie. Confidenza **alta**. Verdetto: a protocollo e budget di token appaiati, il single-agent **eguaglia o supera** il multi-agent; il dato pro-multi-agent più citato (Anthropic, +90,2 %) costa **15× token**, e il solo uso di token spiega l'**80 %** della varianza | **`ADR-123` sale da Media ad Alta, con un argomento nuovo e più forte: di capacità, non economico.** `AS-31` scissa |
| **B-66** | **Misurare se literal intermedi espliciti e schemi di output più strutturati recuperano, sul nostro ~9B a 4 bit, il divario che la letteratura attribuisce alla decomposizione multi-agent** (`R-11.2`: il 7B guadagna +6,8 punti, il doppio del 32B, e il guadagno viene dalla struttura, non dal dialogo fra agent) | **A/10, A/17 — ALTA. È il rimedio economico che sostituisce il multi-agent.** È una **misura** sul nostro hardware, non ricerca bibliografica. Va fatta prima di riaprire `ADR-123` |
| **B-59** | **Costo reale del prefix caching con N prefissi distinti sul serving scelto**: politica di eviction, hit rate. È una **misura**, non ricerca bibliografica | A/10 — `ADR-124`, `R-53`, `T-AC-07`. Specializza `T-MD-09` |
| ~~B-60~~ | **CHIUSA** il 2026-08-23 → vedi **`R-13`** | `ASI07`, `ASI08`, `ASI10`. **193 voci di minaccia in 9 categorie: nessun framework copre la maggioranza di una singola categoria, OWASP è il migliore al 65,3 %.** Nessuna checklist è completa |
| B-61 | Stato di pubblicazione dell'overlay **multi-agent** di NIST COSAiS (ad aprile 2026 era in sviluppo, `R-07`) | specializza `B-04`; C/26 |
| B-62 | OpenTelemetry GenAI semantic conventions: esiste una convenzione per span agent→agent e per la relazione padre-figlio fra run? | A/10, A/12 — `ADR-137`. Specializza `B-06` |
| B-63 | La state machine del `Task` di A2A è mappabile sui 13 stati di `A04` senza perdita? | A/10, C/31 — `ADR-130` |
| **B-64** | **MCP `2026-07-28`, Multi Round-Trip Requests: un tool che fa più giri di interazione può comportarsi come un interlocutore, erodendo `ADR-064` dalla porta dei tool?** | **C/07 e A/13 — ALTA.** Specializza `B-21`/`T-TL-10`. **Problema scoperto da `A10`**: il confine agent/tool potrebbe cadere da dove nessuno guardava |
| B-65 | Con quale criterio la `MemoryScope` del dispatch dovrebbe **restringere** lo snapshot ereditato dal figlio? | A/10 — `ADR-129`. Dipende da `Q-01`. `NON ANCORA DECISO` fino al primo dispatch reale |

| **B-67** | **Costo reale di `FOR UPDATE SKIP LOCKED` con N worker, code profonde e cap di concorrenza per tenant su PostgreSQL 18.** È una **misura**, non ricerca bibliografica | A/11, B/21 — `ADR-141`, `ADR-158`, `R-65`, `DEF-05` |
| B-68 | `LISTEN`/`NOTIFY`: garanzie, limiti di payload, comportamento dietro un connection pooler in transaction pooling e dopo una riconnessione | A/11 — `T-EV-01`, `AS-34` |
| ~~B-69~~ | **CHIUSA per le creazioni** il 2026-08-23 → vedi **`R-12`**. Odoo non ha idempotency key native, ma `ir.model.data` ha un **vincolo UNIQUE di PostgreSQL** su un identificatore **scelto dal chiamante**, e `load()` fa upsert su quello. **L'idempotenza la costruiamo noi** | **`ADR-161`. `AS-35a` sale ad Alta, `R-58` scende a Bassa.** Residuo in `B-74` |
| **B-74** | **Per ciascun tool di transizione di stato del dominio** (confermare un ordine, validare una fattura, registrare un pagamento): l'operazione è idempotente in Odoo, o esiste un modo di verificare che sia già avvenuta? | **A/06, A/11 — regge `AS-35b`**, il residuo lasciato aperto da `R-12`. Va risolta **tool per tool** al momento di dichiarare `AR-RT-04`, non in astratto |
| B-75 | Verificare che `load()` crei record e riga `ir.model.data` **nella stessa transazione** e come si comporta su errore parziale in un batch | `AS-35c`, `AR-EV-32`. **È un test di integrazione**, non ricerca bibliografica |
| B-70 | DBOS / `pg_durable` / Absurd: chi possiede la state machine, il journal resta ispezionabile con SQL nostro, come si integrano `tenant_id` e RLS | A/11 — `T-EV-04`, decisione futura su `ADR-141` |
| B-71 | Advisory lock come leader election: comportamento su riconnessione, failover e con pooler | A/11 — `ADR-151`, `T-EV-07` |
| B-72 | `uuidv7()` come PK su tabelle append-heavy **con RLS**: impatto su indici, piani di query e bloat | A/11 — schema, `ADR-144` |
| B-73 | Standard corrente raccomandato per la firma dei webhook (**non verificato in questa passata**) | A/11 — `ADR-150`, `AR-EV-17` |

| **B-76** | **Misurare i byte per span e per riga di `metric_sample`, e il costo di scrittura sotto carico.** È una **misura**, non ricerca bibliografica | **A/12 — ALTA. Regge `ADR-166` e tutto il budget dell'osservabilità**: senza, è una formula senza numeri |
| **B-77** | Evidenza primaria e misurata sui bias di **LLM-as-a-judge** (verbosity, position, self-preference) e sulla correlazione con annotatori umani **in domini strutturati** | **A/12 — regge `ADR-179`**, oggi a confidenza Bassa. Se la correlazione fosse alta nei domini strutturati, il triage potrebbe estendersi |
| B-78 | Esiste evidenza sull'uso di un modello **piccolo e quantizzato** come judge di sé stesso? | A/12 — specializza `B-77` al nostro vincolo di una GPU (`AS-08`) |
| B-79 | Divulgazione statistica: quale `n` minimo rende sicuro un aggregato cross-tenant, e quali tecniche sono difendibili | A/12, A/14 — regge `ADR-186` |
| B-80 | PostgreSQL come store di telemetria: costo di partizionamento giornaliero + `UNLOGGED` + `DETACH`/`DROP`, e interazione con RLS | A/12 — regge `ADR-166`. Specializza `B-72` |
| B-81 | Stato delle **OpenTelemetry GenAI semantic convention** per attributi di modello e tool | A/12 — specializza `B-06` e `B-62` |
| B-82 | Dead man's switch esterno in un deployment on-premise: dove vive l'ultimo anello? | **A/12, A/15 — regge `AS-41`.** Dipende da `Q-03` |
| B-83 | Dimensione minima di un golden set di retrieval perché `recall_at_k` sia statisticamente utile | **A/12 — regge `ADR-178`**, oggi `NON ANCORA DECISO` |
| B-84 | Costo del render del working set a ogni step | A/12 — regge `AS-22`. Specializza `B-38` |
| B-85 | Come unire il trace del serving e quello di esecuzione senza affidarsi alla sola propagazione W3C, che con `llama.cpp` non esiste | A/12 — `ADR-169` |

| **B-86** | **Rileggere `ASI01`-`ASI10` alla fonte OWASP** (la pagina ha restituito 403): titoli normativi, sotto-voci, mitigazioni raccomandate | **A/13 — DOVUTA.** Necessario prima di citare la copertura in un documento contrattuale |
| **B-87** | Evidenza primaria su **attrito, ritardo e conferma tipizzata** come contromisure all'approvazione riflessa (ergonomia cognitiva, non solo raccomandazioni) | **A/13 — ALTA. Regge `AS-44` e `ADR-191`: è la scommessa meno verificata del documento** |
| **B-88** | Rilevamento di **data poisoning a bassa intensità** in sistemi transazionali: esiste letteratura? | **A/13, A/14 — regge `R-79` e `AS-47`.** È "il colpo più duro" della sezione di falsificazione: e se l'avversario volesse **corrompere** invece che rubare? |
| B-89 | Difese correnti contro l'**esfiltrazione per composizione** di azioni lecite (`R-17`), oltre alla redazione per campo | A/13, A/14 — `ADR-198`, `AR-GP-17` |

| **B-90** | **Data reale di entrata in vigore degli obblighi alto rischio dell'AI Act.** Due fonti si contraddicono: 2 dicembre 2027 contro 2 agosto 2026; esiste inoltre una proposta *omnibus* che potrebbe spostarle | **A/14 — ALTA.** Non si costruisce una scadenza di conformità su fonti in conflitto |
| B-91 | Default di **Salesforce Agentforce** sulle scritture: la conferma è attiva fuori dalla scatola? È configurabile per azione? | A/14, A/18 — le pagine `help.salesforce.com` id `005133036` non si sono caricate |
| B-92 | Quali campi di Odoo, sui modelli CRM che ci interessano, **innescano azioni automatizzate** (email, assegnazioni, ricalcoli) | **A/06, A/18 — regge `ADR-224`.** Va compilato per tool, non in astratto |
| B-93 | Esiste un **baseline standard di regole SoD** per CRM/ERP da cui partire, invece di chiederle al cliente da zero? | **A/14 — regge `ADR-226` e `AS-49`.** Un motore SoD senza regole è peggio di nessun motore |

| **B-94** | Difese contro l'esfiltrazione per composizione applicate all'**export DSAR** (specializza `B-89` su un percorso nuovo) | `R-94`, `ADR-246` |
| **B-95** | **art. 17(3) GDPR**: quali eccezioni coprono un audit trail di sicurezza; e se la pseudonimizzazione irreversibile rispetto al titolare soddisfa una richiesta di cancellazione. **RICHIEDE PARERE LEGALE** oltre alla ricerca EDPB | **`ADR-236`, §22. È la voce più importante di questo elenco** |
| **B-96** | Obblighi di **logging e conservazione dell'AI Act** (artt. 12 e 19) per i sistemi ad alto rischio: durate effettive | §19.6, `DEF-13` |
| ~~B-97~~ | **CHIUSA** il 2026-08-23 → vedi **`R-15.3`**. **Non esiste un baseline SoD pubblico autorevole**: la matrice ISACA si autodichiara non standard di settore. Esistono però gli ordini di grandezza (45-125 nei set commerciali, 150-200 in un programma SAP maturo) | **`ADR-259`**: starter set di ~45 regole da costruire, non da attendere. Prosegue in `B-105` |
| **B-98** | Soglia `k` minima e tecniche difendibili per gli aggregati cross-tenant. Specializza `B-79` | `ADR-243` |
| **B-99** | **Re-identificazione da pattern comportamentali** in log pseudonimizzati: quanto regge l'identity shredding | `R-89`, `ADR-236` |
| **B-100** | Formato standard per l'export di **portabilità** (**non** `DEF-08`, che è l'audit) | `ADR-246` |
| **B-101** | Attacchi di **inversione degli embedding applicati alla memoria**. Specializza `B-32` | `ADR-099`, prima di `memory_embedding` |
| **B-102** | Esiste una **prassi citabile** sulla retention degli audit di sicurezza per PMI italiane? | §19.6, `DEF-13` |
| **B-103** | Quali campi standard di **Odoo**, sui modelli CRM che ci interessano, possono contenere categorie particolari | `ADR-230`, `INV-39`, `AS-51` |

| **B-104** | **Posizione del Garante italiano sulla cancellazione dai backup**: la linea ICO "beyond use" è accettata in Italia? CNIL e autorità danese divergono | **A/14 — regge `ADR-257`.** Il rapporto EDPB 2026 ha messo i backup fra le sette criticità sistemiche: è materia di enforcement attivo |
| B-105 | Conflitti SoD standard del ciclo passivo/attivo applicabili a un CRM/ERP di PMI, da cui derivare le ~45 regole di `ADR-259` | `ADR-259`, `R-92`. **Non esiste un catalogo pubblico autorevole (`R-15.3`): va costruito** |
| **B-106** | Metodo statistico raccomandato per fissare `k` (numero di ripetizioni) e la soglia di regressione su una metrica **binomiale rumorosa** in valutazione di agent. Esistono approcci sequenziali che permettono di fermarsi prima? | **A/17 — PRIORITÀ ALTA. Regge `ADR-265` e `DEF-14`.** Senza, **nessun gate di qualità diventa mai bloccante** e `ADR-180` si trasforma in una scusa permanente (`R-106`) |
| **B-107** | Tempo reale di avvio e di caricamento dati di un'immagine Odoo ufficiale minima | A/17 — regge la scelta fra `OdooFake` e Odoo effimero per la fascia integration (`ADR-262`, `T-QA-02`) |
| **B-108** | Generatori di dati sintetici con caratteristiche italiane (nomi, P.IVA formalmente valide, indirizzi) e licenza compatibile | A/17 — `ADR-263` |
| **B-109** | Evidenza sull'efficacia del mutation testing specificamente su codice di **autorizzazione** | A/17 — `ADR-269` |
| **B-110** | Pratiche correnti di quarantena dei test flaky in progetti con componenti non deterministici | A/17 — `ADR-276`, `AR-QA-07` |
| **B-111** | Benchmark pubblici di agent evaluation **orientati all'esito** (post-condizioni, non output): quali sono riusabili come **struttura**, non come dataset | A/17 — `ADR-273`. Potrebbe far cadere la scelta di scrivere il runner in casa |
| **B-112** | Protocolli per il red teaming con **soggetti umani** su approval fatigue: dimensione del campione, ripetizioni, considerazioni etiche | A/17 — **`ADR-215`, `AS-60`, `AS-44`.** Va insieme a `B-87` |
| **B-113** | Cosa dicono ISTQB e ISO 29119 sui sistemi non deterministici | A/17 — `ADR-261`, per sapere se la struttura a tre corpi ha precedenti |
| **B-114** | Fault injection su componenti **fail-closed** senza introdurre percorsi di degrado | A/17 — `AS-29`, `TC-QA-008`, `TC-QA-135`…`137` |
| **B-115** | Come si costruisce un golden set del retrieval **senza portare documenti aziendali reali in repository** | A/17 — **`R-108`**, scoperto in §30 e non risolto. O si estende `INV-40` ai documenti, o si impone il sintetico con una regola |
| **B-116** | **Quali limiti di rate ha un'istanza Odoo, e come li segnala.** Esistono limiti nativi, o l'unico segnale è il degrado? | **A/18 — PRIORITÀ ALTA. Regge `ADR-294` e `DEF-21`.** Senza, il budget di chiamate esterne è un numero inventato e l'errore verso il largo è **invisibile** (`R-110`) |
| **B-117** | **Per ogni CRM alternativo: esiste un external ID scelto dal chiamante con vincolo di unicità del database?** | **A/18 — PRIORITÀ ALTA condizionata a `Q-01`.** È la domanda vera dietro `Q-01`, molto più di «quale prodotto»: `ADR-161` e `AS-35a` poggiano su quella proprietà di Odoo, e **il costo di cambiare CRM sta lì, non nel connector** |
| **B-118** | **Forma concreta della External JSON-2 API di Odoo**: ha o no la forma `(model, method, args, kwargs)`? | **A/18 — PRIORITÀ ALTA.** Regge `AS-66` e decide se `R-109` è vero. Va insieme a `B-53` |
| **B-119** | Costo reale di un token bucket implementato su PostgreSQL | A/18 — `AS-65`, `R-116`, `T-AP-10` |
| **B-120** | Stato IETF degli header `RateLimit-*` e `Deprecation` | A/18 — se sono standard si usano quelli invece di inventarne |
| **B-121** | Comportamento degli SSE inattivi attraverso proxy aziendali | A/18 — `R-111`, `T-AP-05`. Un run in attesa di approvazione è inattivo per definizione |
| **B-122** | Tassonomie pubbliche di test negativi su API, confrontabili con le nostre sette classi | A/18 — per sapere quali classi ci mancano; le nostre derivano dalle **nostre** difese, quindi ne ereditano i buchi |

> **`B-07` (SPIFFE/SPIRE) resta aperto e non evaso.** `A09` ha deciso `ADR-117` (niente
> SPIFFE Day-1) senza dipendere da `B-07`, ma la voce non è chiusa.
