# ARCHITECTURE STATE — stato canonico dell'architettura

Questo file è la **singola fonte di verità** durante il processo di sintesi.

I documenti nei `level-*/` sono **moduli architetturali**. Questo file è lo **stato
consolidato** che li tiene insieme. Quando un documento successivo cambia una decisione
presa prima, la modifica va registrata **qui**, non solo nel documento nuovo.

Ultimo aggiornamento: dopo `A14`, più la passata `R-15` del 2026-08-23 sulle prassi dei maggiori (`ADR-256`…`ADR-260`). Include la passata `R-14` del 2026-08-23 sui poteri dell'agent su CRM/ERP (`ADR-216`…`ADR-227`). Include l'analisi del 2026-08-23 su `AS-35` (chiusa, `R-12`/`ADR-161`) e `R-63` (mitigata, `ADR-162`/`ADR-163`/`INV-24`). Include le passate di ricerca del 2026-08-23 che hanno chiuso `B-45`, `B-47`, `B-49` (`ADR-120`, `ADR-121`, `ADR-122`) e `B-58` (`R-11`: `ADR-123` confermata, confidenza Alta).

---

## 0. Scostamenti dal Master Entrypoint

Il Master Entrypoint elenca voci che non corrispondono uno a uno ai file presenti.
Li registro esplicitamente invece di risolverli in silenzio.

| Voce nel Master Entrypoint | Situazione reale | Risoluzione |
|---|---|---|
| Level B: `28 Human-in-the-loop` | il file esiste solo in `level-c/prompt/` | eseguito in Level C, **ma** le decisioni Day-1 su approval sono anticipate in `A03` (governance) e `A04` (runtime), perché l'approval è un requisito Day-1 e non può aspettare Level C |
| Level B: `29 Replay` | il file esiste solo in `level-c/prompt/` | eseguito in Level C, **ma** il contratto di step journal che rende possibile il replay è deciso Day-1 in `A11` |
| Level B: `33 ADR` | nessun file | l'ADR system è definito dentro `A01` (§ ADR Candidates) e mantenuto nel registro ADR di questo file |
| Level B: `34 Quality Model` | nessun file | il quality model è definito dentro `A01` (§ Architectural Quality Contract) e `A17` (testing) |
| Level C: `18 Advanced Deployment` | `18` esiste solo in `level-a/prompt/` come *API/Integration* | `A18` copre API/Integration; gli aspetti "advanced deployment" sono coperti da `A15` + `C24` |
| Level C: `32 Admin Console` | nessun file | trattato come superficie del Control Plane in `A02` e come requisito di governance in `A03` |
| Level A: numerazione `01..18` del Master | non coincide con i nomi dei file | si segue la numerazione **dei file**, che riflette le dipendenze reali |

---

## 1. Registro delle decisioni architetturali (ADR)

| ADR | Titolo | Decisione | Reversibilità | Stato | Fonte |
|---|---|---|---|---|---|
| ADR-001 | Struttura di deployment | Single artifact, multi-role process (`api`, `worker`, `scheduler`) + inference server separato | Moderata | Accettata | A01 |
| ADR-002 | Durable execution | Step journal su PostgreSQL + queue `FOR UPDATE SKIP LOCKED`. No Temporal Day-1 | Costosa da invertire (schema) | Accettata | A01 |
| ADR-003 | Sistema di record | PostgreSQL unico system of record Day-1, incluso vector search via pgvector | Costosa da invertire | Accettata | A01 |
| ADR-004 | Policy come dato | Le Policy sono righe versionate nel Control Plane, non codice. L'evaluator è sostituibile | Facile (evaluator) / Costosa (modello dati) | Accettata | A01 |
| ADR-005 | Model access | Contratto `ModelProvider` su API OpenAI-compatible. Nessun Model Router come componente Day-1 | Facile | Accettata | A01 |
| ADR-006 | Tool contract | Tool Registry con JSON Schema (forma MCP-compatibile). MCP come adapter, non come transport interno Day-1 | Facile | Accettata | A01 |
| ADR-007 | Trust class del context | Ogni frammento di context ha una `trust_class` (7 classi). Solo `system` può definire le capability | Costosa se tardiva | Accettata | A01 |
| ADR-008 | Capability binding | L'insieme di capability di un run è **congelato all'avvio** e può solo restringersi | Facile allentare | Accettata | A01 |
| ADR-009 | `tenant_id` Day-1 | `tenant_id` su ogni riga applicativa dal primo commit, con test | Irreversibile in senso inverso | Accettata | A01 |
| ADR-010 | Audit separato dallo stato | Prove immutabili e stato mutabile non condividono tabella né regole | Costosa | Accettata | A01 |

| ADR-011 | Control Plane embedded | Modulo, non servizio. Superficie API da servizio, forma dati dichiarativa | Moderata | Accettata | A02 |
| ADR-012 | Config Snapshot | Il runtime risolve la configurazione **una volta all'avvio del run**, la congela in uno snapshot immutabile e hashato | Costosa | Accettata | A02 |
| ADR-013 | Nessuna riconciliazione Day-1 | `spec`/`status` sì, controller no: non c'è stato che diverge | Facile | Accettata | A02 |
| ADR-014 | Modello a 12 risorse | 12 risorse, non 18. Test: lifecycle proprio + owner proprio + riferita da qualcosa | Costosa | Accettata | A02 |
| ADR-015 | Versioni immutabili + binding | `X` / `XVersion` / `Binding`. Rollback = un `UPDATE` su un puntatore | Costosa | Accettata | A02 |
| ADR-016 | Tenant di sistema | Risorse globali con `tenant_id` del tenant di sistema, mai `NULL` | Costosa | Accettata | A02 |
| ADR-017 | Niente registrazione dei worker | I worker prendono lavoro, non lo ricevono: registrarli riporta la riconciliazione | Facile | Accettata | A02 |
| ADR-018 | Concorrenza ottimistica | `revision` + `ETag`/`If-Match`; `409` obbligatorio sul binding | Facile | Accettata | A02 |

| ADR-019 | Autorità come intersezione | `capability(agent) ∩ permissions(utente) ∩ policy(tenant) ∩ policy(risorsa) ∩ contesto`. Mai unione, mai eredità | Costosa | Accettata | A03 |
| ADR-020 | PDP come funzione pura | Nessun I/O, nessun orologio, nessuna casualità. Gli attributi li pre-carica il PIP | Costosa | Accettata | A03 |
| ADR-021 | Decisione con obbligazioni | `effect + obligations + reasons`, non booleana. Approval/redaction/budget/rate sono obbligazioni | Costosa | Accettata | A03 |
| ADR-022 | `INDETERMINATE` ≠ `DENY` terminale | Guasto del PDP → azione negata ma run **retryable**, categoria di audit distinta | Facile | Accettata | A03 |
| ADR-023 | Approvazione su ogni `SIDE_EFFECT` Day-1 | Restrittivo per default; si allenta solo con accuratezza misurata (`T-GP-02`) | Facile | Accettata | A03 |
| ADR-024 | Cache di policy per versione | Invalidata sulla `bundle_version`, **mai** per TTL: un TTL applica regole revocate | Facile | Accettata | A03 |
| ADR-025 | Precedenza a imbuto | Piattaforma → tenant → agent → risorsa: ogni livello può solo **restringere** | Costosa | Accettata | A03 |
| ADR-026 | Isolamento tenant come invariante | Prima regola valutata, non sovrascrivibile da nessuna policy | Costosa | Accettata | A03 |

> **Scadenza comune a ADR-002, 003, 004, 009, 010, 012, 014, 015, 016:** vanno chiusi
> **prima dello schema del database**, che è il primo lavoro tecnico del progetto.
| ADR-027 | Loop agentico su passi deterministici | `OBSERVE → DECIDE → AUTHORIZE → EXECUTE → RECORD`. Non plan-execute-verify | Costosa | Accettata | A04 |
| ADR-028 | Tre modi, un runtime | `AGENTIC` / `WORKFLOW` / `HYBRID`: cambia solo chi risponde a "qual è il prossimo passo". Day-1 solo `AGENTIC` | Facile | Accettata | A04 |
| ADR-029 | Scrivi prima di agire | Lo step si scrive `PENDING` **prima** dell'effetto. Un effetto senza traccia non è rilevabile | Costosa | Accettata | A04 |
| ADR-030 | Nessun componente Planner | La pianificazione è una chiamata al modello dentro `DECIDE` | Facile | Accettata | A04 |
| ADR-031 | Verifica strutturale ≠ semantica | La semantica (fatta dal modello) è **advisory**, mai decisiva | Facile | Accettata | A04 |
| ADR-032 | `UNCERTAIN` come stato reale | Quando non si sa se un side effect è avvenuto, si ammette e si escala | Costosa | Accettata | A04 |
| ADR-033 | Parallelismo solo in lettura | `READ` in parallelo; `WRITE`/`SIDE_EFFECT` sempre seriali | Facile | Accettata | A04 |
| ADR-034 | Cancellazione cooperativa | Flag ai confini di passo, mai a metà passo | Facile | Accettata | A04 |
| ADR-035 | Irreversibili in fondo | Le azioni non compensabili vanno il più tardi possibile nella sequenza | Facile | Accettata | A04 |

> **ADR-019, 020, 021, 026** vanno chiusi **prima del PDP/PEP**.
| ADR-036 | Serving runtime a due profili | vLLM (produzione) + llama.cpp (sviluppo). Due implementazioni reali → `AR-020` soddisfatta dal primo giorno | Facile | Accettata | A05 |
| ADR-037 | Quantizzazione 4 bit + gate agentico | 4 bit è requisito di ammissione (F16 non ci sta); si adotta solo dopo un gate su tool selection e schema compliance | Moderata | Accettata | A05 |
| ADR-038 | Serving boundary a processo separato | Container sulla stessa macchina, API OpenAI-compatible su loopback. In-process respinto: ogni worker vorrebbe la sua copia dei pesi | Moderata | Accettata | A05 |
| ADR-039 | `max_model_len` come decisione di capacità | Ogni token dichiarato è concorrenza tolta al KV cache. Si sceglie per misura, si congela nello snapshot | Moderata | Accettata | A05 |
| ADR-040 | Structured output a doppio anello | Constrained decoding nel serving **+** validazione JSON Schema nel runtime. Il secondo anello non è rimovibile | Facile | Accettata | A05 |
| ADR-041 | Il prompt è tre sorgenti versionate | Istruzione (`AgentVersion`) + scaffolding del loop (codice) + chat template (`ModelVersion`). È la chiave del lock-in | Costosa | Accettata | A05 |
| ADR-042 | Riproducibilità dell'**evidenza**, non dell'output | Il continuous batching rende il determinismo non ottenibile: si promette di sapere *come* è stata prodotta la risposta | Costosa | Accettata | A05 |
| ADR-043 | Nessun Model Gateway | — | Facile | Accettata | A05 |
| ADR-044 | Nessun fallback automatico | Il fallback è una decisione di **policy**, non un automatismo (→ `C27`) | Facile | Accettata | A05 |
| ADR-045 | Multi-GPU come worker indipendenti | Non tensor parallelism: il modello sta su una GPU. **Condiziona l'acquisto hardware** | Moderata | Accettata | A05 |
| ADR-046 | Artifact allowlist per digest | Nessuna rete dal container di serving; i pesi si verificano per digest | Facile | Accettata | A05 |
| ADR-047 | Priorità come limite di concorrenza a monte | Risolta nella query di prelievo della coda, non con uno scheduler | Facile | Accettata | A05 |
| ADR-048 | Granularità: un tool = **una decisione di autorizzazione** | Verificata da 5 test. Niente mega-tool | Costosa | Accettata | A06 |
| ADR-049 | Nessun `execute_sql` né linguaggio di query | Sostituito da ricerca strutturata + catalogo di query salvate + metrica `missing_capability_rate` | Costosa | Accettata (sotto osservazione `T-TL-06`) | A06 |
| ADR-050 | Tool Runtime modulare **in-process** | Contratto già pronto per l'ibrido | Moderata | Accettata | A06 |
| ADR-051 | Definizione immutabile, implementazione no | Il gap è **registrato** con `build_id` e verificato all'avvio del worker | Moderata | Accettata | A06 |
| ADR-052 | `definition_tokens` dichiarato per tool | Le tool definition occupano il prefisso: vanno misurate | Facile | Accettata | A06 |
| ADR-053 | Le business rule stanno fuori dal tool | Niente duplicazione delle regole del CRM | Costosa | Accettata | A06 |
| ADR-054 | **Set di tool costante per la durata del run** | La restrizione avviene ad `AUTHORIZE`, non a presentazione: altrimenti muore il prefix caching | Moderata | Accettata | A06 |
| ADR-055 | Budget del prefisso che fa **fallire `resolve()`** | Soglia numerica `NON ANCORA DECISO` (dipende da `B-14`) | Moderata | Parziale | A06 |
| ADR-056 | Il tool riceve un **client già autenticato**, mai un segreto | — | Costosa | Accettata | A06 |
| ADR-057 | La delega è un **tipo di credenziale** | — | Moderata | Accettata | A06 |
| ADR-058 | Nessun `http_request(url)` generico | — | Facile | Accettata | A06 |
| ADR-059 | `side_effects` esplicito a 8 tipi | Incluso `TRIGGERS_WORKFLOW` | Moderata | Accettata | A06 |
| ADR-060 | L'errore esterno lo classifica il **connector** | Default `UNKNOWN`, non ritentabile | Facile | Accettata | A06 |
| ADR-061 | `compat` COMPATIBLE/BREAKING verificato in CI | Niente semver | Facile | Accettata | A06 |
| ADR-062 | Salute per telemetria **passiva** + circuit breaker | Niente health check attivi | Facile | Accettata | A06 |
| ADR-063 | MCP adapter bidirezionale con **materializzazione umana obbligatoria** | Nessun import automatico di tool di terzi | Moderata | Accettata | A06 |
| ADR-064 | A2A **accanto** ai tool, mai dentro | — | Moderata | Accettata | A06 |
| ADR-065 | Composizione ammessa solo nei `READ` | — | Facile | Accettata | A06 |
| ADR-066 | `x-sensitivity` per campo nello schema | Alimenta la redazione del PEP | Moderata | Accettata | A06 |
| ADR-067 | Due percorsi di conoscenza | Dato strutturato dal vivo via `Tool` (mai copiato) + documenti indicizzati. La piattaforma non è mai system of record di dato aziendale esterno | Costosa | Accettata | A07 |
| **ADR-068** | **Embedding model su CPU** | Processo separato, contratto `EmbeddingProvider`, **zero VRAM sottratta al modello di generazione**. **Chiude `AS-08` confermandola** | Facile | Accettata (confidenza **bassa** finché `B-26` non misura) | A07 |
| ADR-069 | Nessun reranker Day-1 | Prima la fusione ibrida; il reranker si valuta su una misura di precision | Facile | Accettata | A07 |
| ADR-070 | Retrieval ibrido, fusione per rank | Lessicale + vettoriale, fusi per **posizione** non per punteggio. Due implementazioni reali di `Retriever` → `AR-020` soddisfatta | Moderata | Accettata | A07 |
| ADR-071 | Autorizzazione del retrieval a tre strati | Pre-filtro **in query** (autoritativo) + RLS + post-verifica. Gli strati 2 e 3 possono solo togliere | Costosa | Accettata | A07 |
| ADR-072 | ACL per riferimento, non per copia | `acl_subject` + `grant` con `synced_at`; **fail closed** sulla staleness | Costosa | Accettata | A07 |
| ADR-073 | Blob fuori dal database | Content-addressed, filesystem Day-1, interfaccia `BlobStore`. **Precisazione di perimetro di `ADR-003`, non riapertura** | Moderata | Accettata | A07 |
| ADR-074 | Cinque entità di documento | `document` / `document_version` / `parsed_content` / `chunk` / `embedding`: cinque cause di invalidazione, cinque entità | Costosa | Accettata | A07 |
| ADR-075 | Chunking structure-aware con fallback registrato | Struttura → paragrafo → frase → dimensione, con `boundary_quality` | Moderata | Accettata | A07 |
| ADR-076 | Tutto il derivato è ricostruibile | Solo blob, identità e audit sono irreplaceable. **Test di ricostruzione in CI** | Facile | Accettata | A07 |
| ADR-077 | Frammenti in coda al prompt, retrieval per-run append-only | `AR-MD-15` rispettata e sfruttata; budget dichiarato | Moderata | Accettata | A07 |
| ADR-078 | Nessuna cache dei risultati di retrieval | Una cache di retrieval è una cache di permessi | Facile | Accettata | A07 |
| ADR-079 | Nessun knowledge graph | Le relazioni sono autoritative nel CRM; `entity_link` basta; CTE ricorsive prima di qualunque grafo | Facile | Accettata | A07 |
| ADR-080 | Nessun semantic layer, nessun MDM | Con una sorgente sola non c'è niente da normalizzare (`AR-020`) | Facile | Accettata (dipende da `Q-01`) | A07 |
| ADR-081 | Polling incrementale + reconciliation sweep | Niente CDC (vietato da `INV-07`), niente webhook Day-1 | Facile | Accettata | A07 |
| ADR-082 | Classi di freschezza + `freshness_requirement` per run | Il retrieval esclude o marca; non esiste "ignoralo" | Moderata | Accettata | A07 |
| ADR-083 | Audit del retrieval per identificatori e hash, mai testo | Riconcilia `INV-05` (audit append-only) con la cancellazione | Costosa | Accettata | A07 |
| ADR-084 | Tombstone immediato, purge asincrona | "Non visibile" è istantaneo, "non presente" può prendersi tempo | Moderata | Accettata | A07 |
| ADR-085 | Email fuori dalla knowledge base Day-1 | Superficie d'attacco (`ASI01`/EchoLeak) + ACL per utente | Facile | Accettata (**dipende da conferma del committente**) | A07 |
| ADR-086 | Parsing Day-1 solo di formati con testo estraibile | Niente OCR. Il fallimento è uno **stato visibile**, mai un documento vuoto | Facile | Accettata | A07 |
| ADR-087 | Embedding model: slot deciso, checkpoint aperto | Vincoli di ammissione + criterio di selezione + scadenza. **Chiude `DEF-02` per la forma, la lascia aperta sul checkpoint** | Costosa (il checkpoint) | **Parziale** | A07 |
| ADR-088 | Tre orizzonti di memoria | Working Set, Conversation Trail, Long-Term Memory. Non nove categorie cognitive | Moderata | Accettata | A08 |
| **ADR-089** | **La memoria non contiene fatti di dominio** | Il confine knowledge/memory passa per il `system of record`. Test a tre domande (`AR-ME-01`). È un vincolo di **schema**, non una linea guida | Costosa in pratica | Accettata | A08 |
| **ADR-090** | **Compattazione deterministica a tre zone** | `render_working_set()` in codice: identifier ledger + zona A verbatim + zona B compressa. **Mai il modello**. Salda il debito di `AR-RT-14` | Facile | Accettata | A08 |
| ADR-091 | Budget del context in quote dichiarate | 10/25/8/22/15-20/5 % + ≥15 % di riserva di output, su `max_model_len`. Sforare fa fallire il run con `CONTEXT_BUDGET_EXCEEDED`, non troncare | Facile | **Parziale** (il valore assoluto dipende da `B-14`) | A08 |
| **ADR-092** | **`MemorySnapshot` congelato all'avvio** | Come il `ConfigSnapshot` di `A02`. Sta nella zona cacheabile del prompt | Moderata | Accettata | A08 |
| ADR-093 | Lettura come canale, scrittura come tool | Asimmetria voluta: la lettura non è negoziabile dal modello, la scrittura è autorizzata e auditata | Moderata | Accettata | A08 |
| ADR-094 | Nessuna estrazione automatica attiva Day-1 | Solo `EXPLICIT`, `OBSERVED`, `ADMIN` entrano nel context. Le proposte del modello restano `PROPOSED` e si **misurano** | Facile ad allentare (voluto) | Accettata | A08 |
| **ADR-095** | **Schema minimo: `memory` + `memory_audit`** (+ `run_summary`, `conversation`) | **Chiude `DEF-04`.** Test `AR-CP-02` applicato a 8 entità candidate, 5 bocciate | Costosa | Accettata | A08 |
| ADR-096 | Autorizzazione della memoria a tre strati | Pre-filtro **in query** + RLS + post-verifica: riuso di `ADR-071`. **Niente `ADR-072`**: l'ownership è nativo, non c'è ACL esterna da proiettare | Costosa | Accettata | A08 |
| ADR-097 | `trust_class = retrieved` per ogni memoria | `trust_class` governa il **potere**, `authority` la **fiducia epistemica**: due assi ortogonali. Non si aggiungono classi | Costosa | Accettata | A08 |
| ADR-098 | Cancellazione: tombstone + purge, audit per identificatori | Riuso di `ADR-083`/`ADR-084`, **con una differenza: la memoria non è ricostruibile** | Irreversibile sui dati | Accettata | A08 |
| ADR-099 | Nessun vector search sulla memoria Day-1 | Sotto il cap non c'è selezione da fare. Quando servirà: filtro strutturale → lessicale → embedding, **riusando `A07`** | Facile | Accettata | A08 |
| ADR-100 | Nessuna memoria condivisa Day-1 | Niente `scope = TENANT` in scrittura, niente organizational memory | Facile ad allentare | Accettata | A08 |
| ADR-101 | `run_summary` deterministico | Stessa funzione del Working Set, budget più stretto. Mai generato dal modello | Facile | Accettata | A08 |
| ADR-102 | Supersessione, mai sovrascrittura; bi-temporale a 5 timestamp | 5 stati terminali distinti; `CURRENT`/`HISTORICAL`/`UNKNOWN` **derivati**, non memorizzati | Costosa (schema) | Accettata | A08 |
| ADR-103 | Nessun memory service separato | Modulo in-process in `api` e `worker`, coerente con `ADR-001` e `AR-002` | Facile | Accettata | A08 |
| **ADR-104** | **Tetto di step e di durata attiva per ogni run** | `max_steps = 50` e `max_active_duration = 10 minuti`. La durata è **tempo attivo**: la sospensione in attesa di approvazione umana (`ADR-023`) **non conta**, altrimenti ogni run che aspetta un umano fallirebbe (`T-RT-04` prevede attese lunghe). Entrambi vivono nel `ConfigSnapshot`, congelati all'avvio. Superarli è uno **stato visibile**: errore tipizzato + metrica, mai troncamento silenzioso | Facile (sono numeri nello snapshot) | Accettata | thread — **vincolo di dominio dichiarato dal committente**, 2026-08-23 |
| **ADR-105** | **Dual principal** | Il `principal` è la coppia `(actor = AgentRun, on_behalf_of = HumanSubject \| ServicePrincipal)`. L'autorità è l'**intersezione** delle due, mai l'unione; `on_behalf_of` non è mai vuoto | **Costosa** (sta nel tipo di ogni riga di audit) | Accettata | A09 |
| **ADR-106** | **Tetto congelato, autorità viva** | Si congelano capability, tool set, `MemorySnapshot`, `bundle_version`, `scope` della delega. Si **rileggono a ogni `AUTHORIZE`** stato del subject, sessione, delega, ruoli, tenant, freschezza dei grant. Una revoca ferma le **azioni** subito | Moderata | Accettata | A09 |
| **ADR-107** | **`subject_id` opaco, immutabile, mai riassegnato** | UUIDv4 generato da noi. Tutto ciò che muta sta in righe collegate; la fusione di account produce un **alias** (`merged_into`) risolto in lettura, mai una riscrittura dell'audit | **Effettivamente irreversibile** | Accettata | A09 |
| **ADR-108** | **`Credential Broker` + contratto `SecretStore`** | Interfaccia a 5 metodi, chiamabile **solo** dal Broker, che ne ricava un `AuthenticatedClient` valido per **un solo `EXECUTE`**. Day-1: tabella PostgreSQL cifrata con chiave **fuori** dal database. **Salda il debito che `A06` aveva assegnato ad `A09`** | Moderata (broker) / Facile (store) | Accettata | A09 |
| ADR-109 | Nessun IdP esterno Day-1 | Autenticazione locale password + MFA, ma con superficie interna già IdP-shaped | Facile | Accettata | A09 |
| ADR-110 | La sessione è una riga, non un token | Revocabile immediatamente: è la precondizione di `ADR-106` | Facile | Accettata | A09 |
| ADR-111 | RBAC come sorgente di attributi, ABAC come motore | I ruoli espandono in permessi nel PIP; il PDP non conosce i ruoli. Il perimetro sui dati resta della sorgente esterna | Moderata | Accettata | A09 |
| ADR-112 | `AR-GP-04` si riferisce alla **sessione**, non all'access token | `delegation.not_after = min(session.expires_at, run.started_at + max_active_duration + approval_window)`. **Risolve il conflitto con `ADR-104`** | Facile | Accettata | A09 |
| ADR-113 | La delega non è un token | Riga nel database + struttura in memoria. Nessuna firma, nessuna chiave, finché non deve attraversare una rete | Moderata | Accettata | A09 |
| **ADR-114** | **Catena 3 Day-1: credenziale di servizio per tenant** | Il perimetro sui dati lo applichiamo noi. La catena 1 (delega per singolo utente) è l'obiettivo, non l'implementazione Day-1. **È la decisione che genera `R-41` e che il documento dichiara contestabile**. **AMENDATA il 2026-08-23:** la catena 1 **non** passerà da OAuth — Odoo non ce l'ha per l'API esterna e il committente l'ha escluso. Passerà dalle **API key per singolo utente** (Odoo 14+), che portano i permessi e le record rule di quella persona. `R-41` resta quindi **risolvibile**, con un costo operativo (una chiave per utente invece di una per tenant) invece che con un blocco tecnico | Facile da estendere, **impossibile da togliere** | Accettata | A09 + thread |
| ADR-115 | `EXTERNAL_IDENTITY_LINK` | Mappatura esplicita `subject_id → acl_subject` con `link_method`, `synced_at`, `verified_at`, unicità bidirezionale. **Nessun match per email** | Moderata | Accettata | A09 |
| ADR-116 | Service identity via ruoli PostgreSQL | Il least privilege dei processi lo applica il database, non il codice. Generalizza `AR-CP-05` | Moderata | Accettata | A09 |
| ADR-117 | Nessun SPIFFE/SPIRE Day-1 | Conferma `D-04`: il problema che risolve non esiste su una macchina sola | Facile | Accettata | A09 |
| ADR-118 | Il `PlatformOperator` non legge i dati dei tenant | Tipo di principal separato, stesse policy RLS. Difesa **procedurale e di rilevabilità**, non crittografica | Moderata | Accettata | A09 |
| ADR-119 | Nessun break-glass: **elevazione dichiarata** | `RoleAssignment` temporaneo con `reason`, `valid_until`, notifica e audit. Passa dal PDP come tutto il resto | Facile | Accettata | A09 |
| **ADR-120** | **Argon2id per le password, `m=47104` (46 MiB), `t=1`, `p=1`** | Prima raccomandazione OWASP (`R-09`). Libreria `argon2-cffi`; **mai** implementazioni pure-Python, che inducono parametri deboli. Scelta la riga a più memoria perché Argon2id è *memory-hard*: costringe l'attaccante a comprare RAM, e le GPU — l'hardware dell'attacco — ne hanno poca per core. I login sono rari (`AS-26`), 46 MiB per qualche centinaio di ms non pesano. Rehash-on-next-login se i parametri cambiano | Facile (i parametri stanno nella configurazione) | Accettata | thread — **chiude `B-45`**, 2026-08-23 |
| **ADR-121** | **LDAP come sorgente di identità condivisa; nessun OAuth verso il CRM** | Vincolo del committente: realtà aziendale, credenziali corporate, **niente OAuth**, al massimo LDAP. Odoo ha `auth_ldap` nelle addons base. **Conseguenza forte:** se piattaforma e Odoo autenticano contro la **stessa** directory, `link_method = DIRECTORY_SYNC` diventa affidabile e **il buco di `ADR-115` si chiude alla radice** invece di essere presidiato. Due cautele obbligatorie: `auth_ldap` da solo **non mappa i gruppi** (serve OCA `users_ldap_groups`), e in quel modulo l'opzione *"Only LDAP groups"* **deve** essere attiva, altrimenti chi esce da un gruppo nella directory non perde il gruppo in Odoo | Moderata | Accettata | thread — 2026-08-23 |
| **ADR-122** | **`acl_subject` con discriminante, e archiviazione = revoca** | `acl_subject` non è `odoo:res.users:42` ma `odoo:res.users:42@<create_date>`. Odoo **non riusa** gli ID (`SERIAL` monotono, `R-10`), ma un `setval()` manuale può forzarlo, e riattaccherebbe **in silenzio** un nuovo utente alla storia e ai permessi del precedente. Il discriminante trasforma un errore invisibile in una mappatura **rotta**. In più: utente Odoo con `active = False` → link `STALE` → `AR-ID-19` nega | Facile (una colonna) | Accettata | thread — **chiude il buco dichiarato di `ADR-115`**, 2026-08-23 |
| **ADR-123** | **Nessuna comunicazione agent→agent Day-1** | Un compito = un run. Nessuna superficie per invocare un altro agent. **Chiude `DEF-07`** (metà negativa). **RAFFORZATA il 2026-08-23 da `B-58`/`R-11`:** l'argomento non è economico ma **di capacità**. Il multi-agent compra qualità **con i token** (Anthropic: +90,2 % a **15× token**, e il solo uso di token spiega l'**80 %** della varianza). Ma `ADR-039` fissa `max_model_len` come decisione di capacità su **una sola scheda** (`AS-08`): 15× token = 15× meno run concorrenti. **Non è acquistabile a nessun prezzo.** In più: a protocollo appaiato **al massimo 1 su 6 sistemi multi-agent batte l'ancora single-agent** (arXiv:2606.05670), e a budget di token appaiato il single-agent **eguaglia o supera** il multi-agent (Stanford, arXiv:2604.02460) | Facile *se* `ADR-125` esiste | Accettata, **confidenza Alta** (era Media) | A10 + `R-11` |
| ADR-124 | La specializzazione è una **risorsa, non un processo** | Agent specializzato = `Agent` + `AgentVersion` + `Binding`, già disponibili da `A02`. La scelta la fa il **codice applicativo**. **Chiude `DEF-07`** (metà positiva) | Facile | Accettata | A10 |
| **ADR-125** | **Colonne di lineage Day-1, degeneri** | `root_run_id`, `parent_run_id`, `parent_step_index`, `depth` dal primo commit, su `run` e sull'audit. Costano nulla adesso, sono impossibili da aggiungere dopo | **Effettivamente irreversibile** dopo il primo run | Accettata | A10 |
| ADR-126 | L'invocazione futura è un **child run** | Mai "agent come tool": ogni azione del figlio passa dal proprio `AUTHORIZE` | Moderata | Accettata (fase 2) | A10 |
| **ADR-127** | **Attenuazione dell'autorità, `on_behalf_of` invariante** | `ceiling(child) = ceiling(parent congelato) ∩ capability(B)`; `on_behalf_of` **copiato** dalla radice; niente delega a catena, quindi `AR-ID-04` resta intatta | **Costosa** | Accettata | A10 |
| **ADR-128** | **I tetti di `ADR-104` sono dell'albero, non del run** | Un ledger di step per albero, consumato **atomicamente**; deadline **assoluta** copiata; orologio fermo solo se **tutti** i run non terminati sono sospesi | Facile (numeri nello snapshot) | Accettata | A10 |
| ADR-129 | Memoria ereditata **per riferimento**; ownership = `on_behalf_of` | Il figlio non risolve uno snapshot proprio; una memoria scritta durante l'albero non è leggibile dall'albero. **Chiude `T-ME-07` in anticipo** | Moderata / Costosa (colonne di `memory_audit`, che sono **Day-1**) | Accettata | A10 |
| ADR-130 | Task model = `AgentTask` asincrono persistito | `task_id`, stato, risultato, cancellazione. **Trasporto = database** (`AR-002`), nessun broker. Nessuno streaming fra agent | Moderata | Accettata (fase 2) | A10 |
| ADR-131 | **A2A come adapter di confine, mai transport interno** | Conferma `ADR-064`; materializzazione umana obbligatoria come `ADR-063`. Fase 3 | Facile | Accettata | A10 |
| ADR-132 | Nessun Agent Registry nuovo | Il registro è il Control Plane; il "trust level" resta policy, non attributo | Facile | Accettata | A10 |
| ADR-133 | Discovery **statica**, nessuna negoziazione | Il set di agent invocabili sta nel `ConfigSnapshot`, congelato — altrimenti cade `INV-13` | Facile ad allentare, impossibile a stringere | Accettata | A10 |
| ADR-134 | L'approvazione la chiede **chi esegue** | Il PEP del run che esegue; attribuita alla radice e a `on_behalf_of`. **Nessun agent può approvare** | Moderata | Accettata (fase 2) | A10 |
| ADR-135 | Loop prevention a **quattro barriere deterministiche** | Profondità, ciclo su `ancestor_agent_ids`, ledger, ripetizione. **Nessuna affidata al modello** | Facile | **Parziale** (i valori sono `NON ANCORA DECISO`) | A10 |
| ADR-136 | Nessun sandboxing fra agent nostri | Il confine è il processo `worker`. Al primo agent non nostro → `T-AC-08` | Facile | Accettata | A10 |
| ADR-137 | Tracing standard, nessun modello proprietario | W3C Trace Context + OTel. `root_run_id` è **stato**, il `trace_id` è **correlazione** e non entra in decisioni (`AR-ID-02`) | Facile | Accettata | A10 |
| ADR-138 | **Nessun event bus, nessuna coda nuova** | Gli agent non reagiscono a eventi. Se un pattern richiedesse orchestrazione durevole → **mandato ad `A11`**, non un broker | Facile | Accettata | A10 |
| ADR-139 | **Isolamento cross-tenant hard** | `child.tenant_id = parent.tenant_id`, applicato dal database. Nessuna federazione cross-tenant in nessuna fase | **Effettivamente irreversibile** in senso inverso | Accettata | A10 |
| ADR-140 | Artifact **per riferimento** via `BlobStore` | Nessuna entità `Artifact` nuova: il test `AR-CP-02` dà due mancanti su tre | Facile | Accettata | A10 |
| **ADR-141** | **Nessun engine di durable execution: il motore è il loop su PostgreSQL** | Conferma `ADR-002` con un argomento **nuovo e più forte di quello economico**: dai FATTI di `R-04`, la garanzia exactly-once di DBOS vale **solo se lo step scrive sullo stesso PostgreSQL del workflow**. I nostri effetti atterrano su Odoo (`INV-07`), quindi compreremmo un secondo system of record dello stato **per una garanzia che sul confine che conta non ci verrebbe data**. In più: due state machine per la stessa cosa violano il Single Owner. Temporal respinto; **DBOS/`pg_durable` sono i candidati n.1 al futuro, non Temporal** | Moderata | Accettata | A11 |
| ADR-142 | Il `job` è un'entità **distinta** dal `run`; un pool solo | 8 tipi di job di background (purge dei tombstone, polling, sweep, proiezione dei grant…). **Un job non chiama mai il modello, non esegue tool con effetti, non avvia run.** Salda i debiti di lavoro in background lasciati da `A07` e `A08` | Facile | Accettata | A11 |
| ADR-143 | Lease con **fencing token** (`lease_epoch`) e heartbeat | Rende `AR-RT-08` strutturale invece che sperata (`INV-22`) | Facile | Accettata | A11 |
| **ADR-144** | **Protocollo a tre scritture: `PENDING → IN_FLIGHT → esito`** | `IN_FLIGHT` è committato **nell'istante prima del primo byte**. Recovery a quattro esiti: `PENDING` → riesegui · `IN_FLIGHT` + idempotente → riesegui con la **stessa** chiave · `IN_FLIGHT` + verificabile → **probe** (che è uno step e paga dal ledger) · altrimenti → `UNCERTAIN` → `ESCALATED`, **mai** riesecuzione | **Costosa** | Accettata | A11 |
| **ADR-145** | **Il tempo attivo è un contatore, non un intervallo** | `run_tree.active_ms_consumed`, incrementato **solo da chi tiene un lease**, a ogni heartbeat. Quando tutti i run sono sospesi nessuno tiene un lease, quindi nessuno paga: l'orologio non "si ferma", **non esiste**. Precisa `ADR-128`: la deadline assoluta diventa derivata sopra il contatore | Facile | Accettata | A11 |
| **ADR-146** | **Il consumo del ledger d'albero lo fa un trigger di database** | Il campo budget **non esiste** su `run`: solo una FK verso `run_tree`. Inaggirabile da qualunque percorso applicativo. **È la difesa strutturale contro `R-50`** | Moderata | Accettata | A11 |
| ADR-147 | Nessun event sourcing | Stato corrente + journal + audit append-only. Lo stato **si scrive**, non si deriva per fold di un log | Moderata | Accettata | A11 |
| ADR-148 | Nessun event bus; **nessun evento avvia un run** | Conferma `ADR-138` | Facile ad allentare, impossibile a stringere | Accettata | A11 |
| ADR-149 | Outbox minimale a una tabella, **solo riferimenti**, drenato dal pool | Mai contenuto di dominio, mai segreti | Facile | Accettata | A11 |
| ADR-150 | Nessun inbox Day-1; contratto del callback definito | Un callback esterno **si autentica prima** di essere correlato: la correlazione non è autenticazione | Facile | Accettata | A11 |
| ADR-151 | Scheduler come **ruolo di processo** con advisory lock; `catchup_policy = SKIP` | Nessun processo nuovo | Facile | Accettata | A11 |
| ADR-152 | I timer durevoli sono **righe** (`wakeup_at`), non attese in memoria | Nessun worker attende in RAM | Facile | Accettata | A11 |
| ADR-153 | Retry guidato da policy: backoff + jitter, tetto per classe | **Il retry consuma tempo ma non step.** La classe di errore la dichiara il connector, mai il modello | Facile | Accettata | A11 |
| ADR-154 | Nessuna compensazione automatica; `compensation_hint` registrata | Coerente con `AR-RT-13` | Facile | Accettata | A11 |
| **ADR-155** | **`DELEGATION_EXPIRED`, `AUTHORIZATION_LOOP` e gli altri sono ragioni terminali, non stati** | La macchina resta a **13 stati**. `CHECK` di database a garantire la visibilità. **Conflitto con `A09` dichiarato invece che risolto in silenzio**: `A09` chiedeva due stati nuovi | Facile | Accettata | A11 |
| ADR-156 | Ripresa del padre per **risveglio idempotente su riga** | Padre morto → risultato leggibile e nessun effetto. **Non esiste un comando `ResumeRun`** | Facile | Accettata (fase 2) | A11 |
| ADR-157 | Cancellazione durevole **per albero** + `tree_reaper` | Chiude `R-54` (figli orfani). Nessun figlio sopravvive alla radice (`AR-AC-18`) | Facile | Accettata | A11 |
| ADR-158 | Priorità, riserva interattiva e cap per tenant **nella query di prelievo** | Estende `ADR-047` | Facile | Accettata | A11 |
| ADR-159 | Drain ai confini di passo; migrazioni expand/contract | **Nessuna sostituzione silenziosa di versione**: una versione pinnata mancante fa fallire il run in modo visibile | Facile | Accettata | A11 |
| ADR-160 | **Nessun ordinamento globale degli eventi** | Ordine totale solo dentro un run | Moderata | Accettata | A11 |
| **ADR-161** | **L'idempotenza verso Odoo la costruiamo noi, con l'external ID** | La `idempotency_key` deterministica di `AR-EV-09` — derivata da `(run_id, step_index)` — viene scritta come **external ID Odoo** in un namespace nostro (`__agent__`), sfruttando il vincolo **UNIQUE a livello PostgreSQL** su `ir_model_data(name, module)` (`R-12`). Record e riga `ir.model.data` vanno creati **nella stessa transazione Odoo** (via `load()`), mai con due chiamate RPC separate. **Il ramo `IN_FLIGHT` ambiguo di `ADR-144` si risolve con una lettura su indice unico**, non con una ricerca euristica. Vietato toccare gli external ID di altri moduli | Moderata (è nel connector) | Accettata | thread — **chiude `B-69` per le creazioni**, 2026-08-23 |
| **ADR-162** | **La conferma di dispatch è precondizione dell'attesa** | Un run **non entra** in attesa di approvazione per il fatto di aver *scritto* una riga di outbox: entra solo quando quella riga raggiunge `DISPATCH_CONFIRMED` (handoff al trasporto accettato). Se la conferma non arriva entro una finestra dichiarata, il run **termina** con ragione `APPROVAL_UNDELIVERABLE`. **Disinnesca `R-63`**: converte uno stallo silenzioso in un fallimento rumoroso, notato da **chi ha avviato il run** e non solo da un operatore davanti a un cruscotto. Confine onesto: confermiamo la consegna al trasporto, **non** che un umano abbia letto | Moderata | Accettata | thread — 2026-08-23 |
| **ADR-163** | **Ogni tipo di `job` dichiara una staleness massima; l'assenza di progresso è un evento** | Generalizza `R-63` alla sua classe: **ogni consumatore di background il cui guasto non produce errori è un guasto silenzioso**. Vale per purge dei tombstone (`ADR-084`/`098`), polling (`ADR-081`), sweep, proiezione dei grant (`ADR-072`), `tree_reaper` (`ADR-157`). Tre strati: (1) ogni `job_type` dichiara `max_staleness` e scrive una riga di liveness che conta le **consegne riuscite**, non i giri di loop; (2) il controllo vive nello **`scheduler`**, la cui morte è di per sé visibile perché non schedulerebbe più nulla; (3) un **canary** sintetico verso un sink nullo garantisce che ci sia sempre qualcosa da consegnare, così "zero consegne riuscite" è inequivocabile e non confondibile con una coda vuota | Facile | Accettata | thread — 2026-08-23 |
| **ADR-164** | **Tre piani di segnale separati** | Telemetria operativa, audit legale, evaluation di giudizio: **tre sistemi, tre garanzie**, correlati solo per identificatore. Mai fusi | Costosa | Accettata | A12 |
| ADR-165 | OpenTelemetry come **contratto**, non come stack | SDK e semantic convention sì; Collector e backend dedicato **no** Day-1 | Facile | Accettata | A12 |
| ADR-166 | Telemetria su PostgreSQL Day-1 | `telemetry_span` + `metric_sample`. Niente Prometheus/Jaeger/ClickHouse | Moderata | Accettata (**Media** finché `B-76`/`B-80` aperte) | A12 |
| ADR-167 | Gerarchia a 5 livelli; **`PDP`, memoria e render non sono span** | `RUN_TREE → RUN → STEP → operazione esterna → chiamata di rete`. Alla ripresa si apre un **nuovo trace** con `link` | Moderata | Accettata | A12 |
| ADR-168 | **Nessun identificatore nuovo** | `trace_id`/`span_id` per correlazione; gli identificatori di stato esistono già. Rifiutati `session_id`, `execution_id`, `task_id`, `tool_call_id`, `model_invocation_id`, `retrieval_id`, `memory_access_id` | Facile | Accettata | A12 |
| ADR-169 | Il trace HTTP e il trace di esecuzione sono **separati** | Legati da uno span link e da `initiating_trace_id`, mai da parentela. Conseguenza di `AR-002` | Facile | Accettata | A12 |
| **ADR-170** | **Difesa strutturale, non filtrante** | Il contenuto **non entra** (`INV-26`). La redaction è seconda linea, deterministica, per campo, **mai da LLM** | Costosa | Accettata | A12 |
| **ADR-171** | **Il prompt non si conserva, si ricostruisce** | `Reproduction Bundle`: modulo in-process che ri-renderizza il prompt dagli artefatti già versionati e hashati (`ADR-041`, `ADR-012`, `ADR-092`, `ADR-090` è una funzione pura), sotto RLS e con audit. **Non rigenera l'output** (`ADR-042`) | Moderata | Accettata | A12 |
| ADR-172 | `DebugCapture` come **unica porta al contenuto** | Opt-in del tenant, a tempo, con perimetro, autorizzata dal PDP, auditata, retention propria, **visibile mentre è attiva**. Off by default | Moderata | Accettata | A12 |
| ADR-173 | Sampling misto guidato **dall'esito** dello step | Head-based sui `READ` nominali, tail-based su tutto il resto. **Otto classi mai campionate** | Facile | Accettata | A12 |
| ADR-174 | Budget di cardinalità; **`run_id` e `tenant_id` non sono label** | Le viste per tenant si calcolano per query | Moderata | Accettata | A12 |
| ADR-175 | Schema di log **chiuso**, nessun campo di testo libero | `event` è un enum; niente `message` | Facile | Accettata | A12 |
| **ADR-176** | **Il registro `M-OB-*` è un artefatto verificato in CI** | Tre verifiche: ogni trigger ha una metrica (**rende `AR-035` eseguibile**), ogni metrica è registrata, nessuna label vietata | Facile | Accettata | A12 |
| **ADR-177** | **Evaluation orientata all'esito**: post-condizioni e vincoli | Mai output attesi, mai trajectory matching. Coerente con `R-11` | Costosa (i dataset) | Accettata | A12 |
| ADR-178 | Golden set del retrieval come **artefatto Day-1** con owner e scadenza | Precede l'attivazione del retrieval in produzione. **Disinnesca `R-30`** | **Effettivamente irreversibile** (è conoscenza) | Accettata | A12 |
| ADR-179 | LLM-as-a-judge **solo triage, mai gate** | Offline, `advisory` **nel tipo**, con quota casuale della coda e concordanza umana misurata | Facile | Accettata (**Bassa** finché `B-77` aperta) | A12 |
| ADR-180 | Gate bloccanti **deterministici**, gate di qualità **advisory** | Le soglie di qualità si fissano **relative alla baseline**, dopo tre rilasci misurati | Facile | Accettata | A12 |
| ADR-181 | **`task_success_rate` non è un SLO** | Al suo posto: `technical_completion_rate` (SLO), `eval_task_success_rate` (gate), segnali online (indicatori) | Facile | Accettata | A12 |
| ADR-182 | Canary sintetico + dead man's switch a **tre livelli** | Canary come `job_type` nel tenant di sistema, senza `SIDE_EFFECT`. **L'ultimo anello è esterno al sistema** | Facile | Accettata | A12 |
| ADR-183 | Nessun esperimento in produzione su percorsi **con effetti** | Solo offline, shadow di sola lettura, o opt-in del tenant | Facile | Accettata | A12 |
| ADR-184 | Retention differenziata per piano di segnale | Rollup delle metriche **≥ 2 trimestri**, altrimenti `T-MD-08` è morto | Facile | Accettata (valori `NON ANCORA DECISO`) | A12 |
| ADR-185 | **Ogni incidente produce un `EvaluationCase`** | La chiusura dell'incidente **richiede** che il caso esista | Facile (di processo) | Accettata | A12 |
| ADR-186 | Due cruscotti: piattaforma e tenant | Quello di piattaforma non porta dimensioni derivate dall'attività di un tenant | Moderata | Accettata | A12 |
| ADR-187 | **Una sola tassonomia di errori, non nuova** | `A12` adotta quella di `A04`/`A06`/`A11` come unico enum `error_class`. Più: **`T-GP-01` va rifissata al netto dell'inference** | Facile | Accettata | A12 |
| ADR-188 | Il rilevamento di prompt injection è un **sensore, non un controllo**: non blocca mai da solo | Un filtro che blocca ha falsi positivi che qualcuno vorrà abbassare, e il modo di abbassarli è disattivarlo. Un sensore che misura non ha quel destino | Facile | Accettata | A13 |
| **ADR-189** | **Si approva un `ActionBinding` tipizzato, non una narrazione** | L'oggetto dell'approvazione è la struttura: tool, argomenti validati, identificatori. La giustificazione del modello è mostrata ma marcata `advisory` **nel tipo**. **Rende inefficace la *fake explainability* per costruzione** | **Costosa** | Accettata | A13 |
| **ADR-190** | **Le etichette leggibili vengono da una lettura autoritativa**, mai dal modello | Altrimenti basterebbe far scrivere al modello un nome diverso da quello del record che sta per modificare. Costa una `READ` per approvazione | Moderata | Accettata | A13 |
| **ADR-191** | **Interfaccia di approvazione strutturalmente diversa per classe di reversibilità** | Tre classi da `side_effects` e `compensability`, **mai scelte dal modello**. Sull'irreversibile: digitazione dell'identificatore + **ritardo minimo** — non si può cliccare più in fretta di quanto si legge | Moderata | Accettata | A13 |
| ADR-192 | **Nessuna anteprima ha effetti** | Contromisura al *consent laundering*: un'anteprima si calcola solo da tool `READ`. Verificabile staticamente | Facile | Accettata | A13 |
| ADR-193 | Attribuzione obbligatoria e completa su ogni richiesta di approvazione | Quale agent, quale run, per conto di chi, quale tool. Contromisura al *phantom agent*. Il dato esiste già (`INV-15`) | Facile | Accettata | A13 |
| ADR-194 | **Tetto di approvazioni per soggetto e finestra** | Superato, si degrada a **revisione differita**, **mai** ad auto-approvazione. È un limite di sicurezza, non di throughput | Facile | Accettata (valore `NON ANCORA DECISO`) | A13 |
| ADR-195 | Doppio operatore per la classe irreversibile ad alta sensibilità | Due `subject_id` distinti, vincolo di database. Lista che parte vuota | Facile | Accettata | A13 |
| **ADR-196** | **`T-GP-02` riformulato come congiunzione di tre condizioni** | Un tasso di approvazione vicino al 100 % ha due spiegazioni indistinguibili: l'agent è affidabile, **oppure le persone hanno smesso di leggere**. Servono anche `approval_decision_time_p50` e `approval_modification_rate`. **Senza, `T-GP-02` va considerato disattivato** | Facile | Accettata | A13 |
| ADR-197 | Quarantena dei documenti con segnali anomali | Indicizzati ma **non recuperabili** finché una persona non rilascia. Coda con `max_staleness`, quindi l'abbandono è un evento di errore | Facile | Accettata | A13 |
| ADR-198 | Guardia sugli identificatori | Un id in un `SIDE_EFFECT` non osservato in un `READ` precedente dello stesso run è **stato visibile**. Sensore, non controllo: rende `R-17` ricostruibile, non impedita | Facile | Accettata | A13 |
| ADR-199 | `T-ME-04` richiede valutazione **adversariale**, non solo precisione | Un attacco MINJA riuscito produce voci che **sembrano precise**. Non può scattare finché `AS-42` resta a confidenza bassa | Facile | Accettata | A13 |
| ADR-200 | **Nessun componente concentra credenziali verso sistemi eterogenei** | Generalizza il rifiuto del Model Gateway. Il `Credential Broker` è l'eccezione dichiarata: un solo perimetro, monouso, non esposto | Moderata | Accettata | A13 |
| ADR-201 | Il pre-filtro autorizzativo verso il CRM è una **guardia di invariante** | Nessun error budget, violazione = evento di sicurezza, copertura di test bloccante. Se è l'unica cosa fra noi e la fuga di dati, va trattato come tale | Moderata | Accettata | A13 |
| ADR-202 | Test adversariale di isolamento fra tenant come **gate bloccante** | Dichiara di provare l'assenza di **accesso diretto**, non l'assenza di canali laterali | Facile | Accettata | A13 |
| ADR-203 | **Allowlist di egress a livello di rete del container**, Day-1 | Chiude in un colpo SSRF, esfiltrazione da tool malconfigurato, connessioni inattese | Facile | Accettata | A13 |
| ADR-204 | Un tool che accetti un URL richiede allowlist **nello schema** | Mai validazione a runtime: si aggira con redirect, DNS rebinding, notazioni alternative. **L'insieme degli host è dichiarato prima, non controllato dopo** | Facile | Accettata | A13 |
| ADR-205 | Tetto di dimensione e insieme chiuso di tipi **prima** di qualunque parsing | Il parsing è la parte più attaccabile di ogni sistema | Facile | Accettata | A13 |
| **ADR-206** | **Il parsing dei documenti in un processo separato, senza rete e senza credenziali** | Unico sandboxing Day-1, giustificato: il parser mangia byte ostili per mestiere | Moderata | Accettata | A13 |
| ADR-207 | Rate limiting **sull'avvio di run**, non sulle richieste HTTP | Le richieste HTTP sono economiche, i run no. Limitare la superficie sbagliata dà l'illusione della protezione | Facile | Accettata (valore `NON ANCORA DECISO`) | A13 |
| ADR-208 | Il modello è una **dipendenza di supply chain** | Hash verificato al caricamento, nessun caricamento remoto a runtime. Un modello sostituito silenziosamente non lascia traccia in nessun log applicativo | Facile | Accettata | A13 |
| ADR-209 | L'attivazione di `DebugCapture` è un **evento di sicurezza** | Notificata al tenant; per il `PlatformOperator` passa da `ADR-119` (elevazione dichiarata), non da una configurazione | Facile | Accettata | A13 |
| **ADR-210** | **Ogni componente dichiara il comportamento in caso di guasto; default fail-closed con stato visibile** | Promuove a regola l'idioma che dodici documenti avevano adottato indipendentemente | Facile | Accettata | A13 |
| ADR-211 | Profilo comportamentale per `agent_version` come **segnale**, mai blocco | Primo uso di un metodo statistico nell'architettura, e solo per guardare | Facile | Accettata | A13 |
| **ADR-212** | **`KillSwitch` a tre livelli** (`HALT_SUBJECT`, `HALT_AGENT`, `HALT_TENANT`), Day-1 | Passa dal PDP, reversibile, auditato. In un incidente, comporre sei operazioni sotto pressione produce errori: un comando solo è la differenza fra contenere in un minuto e in venti | Facile | Accettata | A13 |
| ADR-213 | Ogni incidente di sicurezza produce un **test di regressione** | Oltre all'`EvaluationCase` di `ADR-185`. Senza, ogni incidente si può ripetere | Facile (di processo) | Accettata | A13 |
| ADR-214 | 10 gate **deterministici e bloccanti**, red teaming obbligatorio ma **non** bloccante | Coerente con `ADR-180`: il blocco è riservato al deterministico | Facile | Accettata | A13 |
| ADR-215 | Il red teaming su `ASI09` **richiede soggetti umani** | Non automatizzabile. Se le persone approvano azioni che non corrispondono alla descrizione, il problema è l'interfaccia | Facile | Accettata | A13 |
| **ADR-216** | **Conferma umana su OGNI `Insert`, `Update` e `Archive`, su OGNI entità, senza eccezioni** | Decisione del committente, 2026-08-23. Rafforza `ADR-023` e lo estende esplicitamente a tutte le entità. **È lo standard corrente, non un eccesso**: Microsoft 365 Copilot lo impone senza permettere di disattivarlo, Amazon Bedrock lo implementa nella stessa forma, le fonti lo chiamano *convenzione fra vendor* (`R-14.6`). Si separano due domande: **se** serve la conferma (sempre, qui) da **che forma** ha (variabile, `ADR-191`). **L'uscita dalla conferma esiste solo via `T-GP-02` riformulato (`ADR-196`), mai per configurazione** | Costosa | Accettata | thread |
| **ADR-217** | **Capability floor: Day-1 sola lettura sull'ERP** | L'agent legge tutto ciò che gli è permesso, ma **scrive solo su una superficie CRM dichiarata e ristretta**. Zero scritture su contabilità e amministrazione. Motivi: gli incidenti reali sono quasi tutti scritture distruttive (`R-14.5`); le scritture contabili hanno un regime giuridico non modellato (`R-14.3`); guadagna i mesi che mancano alla scadenza alto rischio | Facile ad allargare, **difficile a stringere** | Accettata | thread |
| **ADR-218** | **Nessun tool di cancellazione. Solo `archive`** | `unlink()` **non passa da `write()`**, quindi salta le automazioni agganciate alla scrittura: è l'unico verbo che **aggira i controlli invece di attraversarli**. Su `res.partner` può orfanare dati in silenzio. `active = False` è reversibile e non distrugge nulla. La cancellazione fisica resta amministrativa; **il diritto all'oblio ha un percorso umano proprio**, mai l'agent | Facile | Accettata | thread |
| ADR-219 | I tool di scrittura sono **per campo, non per record** | `aggiorna_stage_opportunita`, non `aggiorna_opportunita`. Segue `ADR-048`; rende leggibile l'approvazione, perché chi conferma vede **quale** campo cambia | Moderata | Accettata | thread |
| **ADR-220** | **Cardinalità dichiarata, default = 1** | Un tool di scrittura tocca **un record per chiamata**, salvo dichiarare nello schema una cardinalità massima; se massiva, **il numero di record va mostrato nell'approvazione**. È il simmetrico di `AR-TL-15` sulle scritture, e mancava. **La differenza fra un errore e un disastro non è la gravità dell'azione: è quanti record tocca** | Facile | Accettata | thread |
| **ADR-221** | **Lettura prima della scrittura; il valore precedente va nel journal** | **FATTO (`R-14.7`): in Odoo nessun campo è tracciato per default**, quindi dopo un `UPDATE` il valore precedente non esiste più. Lo conserviamo noi. Tre benefici: rende l'`UPDATE` **reversibile**, alimenta il `compensation_hint` di `ADR-154`, e **dà a `R-79` (corruzione lenta) la prima difesa reale**. Costa una `READ` per scrittura | Moderata | Accettata | thread |
| **ADR-222** | **Classe `IMMUTABLE_RECORD`: rettifica, mai modifica** | Sui record soggetti a inalterabilità legale (registrazioni contabili, art. 2215-bis c.c.) l'`update` è **vietato nel tipo**: esiste solo la scrittura di rettifica che lascia traccia dell'errore originario | Costosa | Accettata | thread |
| ADR-223 | I campi amministrativi del contatto stanno con l'**ERP**, non col CRM | P.IVA, codice fiscale, sede legale, coordinate bancarie: fuori dal perimetro dell'agent Day-1. `res.partner` è il punto di giunzione fra CRM e contabilità, non una tabella normale — e i dati bancari sono il primo bersaglio di ogni frode aziendale | Facile | Accettata | thread |
| ADR-224 | I campi che innescano automazioni vanno **dichiarati nello schema** | Scrivere un campo in Odoo può far partire azioni automatizzate, email, ricalcoli. L'agent non vede questi effetti di secondo ordine: l'approvazione deve dirlo (*"questa modifica invierà una notifica al cliente"*) | Facile | Accettata | thread |
| **ADR-225** | **Albero delle azioni nel caso peggiore, obbligatorio prima del rilascio di ogni `agent_version`** | Non cosa l'agent **fa**, ma cosa **può** fare con i suoi permessi; i rami irrecuperabili si tagliano **a livello di permesso**, non di prompt. Raccomandazione diretta dall'analisi degli incidenti reali (`R-14.5`) | Facile (di processo) | Accettata | thread |
| **ADR-226** | **Conflitti di Segregation of Duties valutati dal PDP** | Il PDP oggi risponde a *"questo principal può fare questa azione?"*, non a *"questa azione, insieme a ciò che ha già fatto, viola una separazione di funzioni?"*. Coppie di funzioni incompatibili dichiarate e verificate **prima** dell'esecuzione (`R-14.4`). **In un ERP è il controllo fondativo, ed è ciò che i revisori guardano** | Costosa | Accettata | thread |
| ADR-227 | Ceiling **per compito**, non per `agent_version` | Oggi il tool set è costante nel run per non invalidare il prefix caching: **è privilegio permanente a granularità di run**, contro la raccomandazione *just-in-time, limitato al compito, revocato al completamento*. Il run dichiara il proprio perimetro all'avvio e non può superarlo | Moderata | **Parziale**: il costo sul prefix caching va **misurato** (`B-59`) prima di fissarla | thread |
| **ADR-228** | **`FieldScope`: projection al confine, redazione come seconda linea** | Il PDP produce un terzo ambito accanto a `RetrievalScope` e `MemoryScope`. Il PEP restringe i campi **prima** della chiamata al connector, e verifica il risultato dopo. **Chiude `R-32` sul percorso strutturato** | Moderata | Accettata | A14 |
| **ADR-229** | **Sul percorso documentale la granularità resta il documento** | Non è un rinvio: è una limitazione strutturale del mezzo. `sensitivity_max` per sorgente; sovra-restrizione misurata da `R-86`; `T-DG-06` riapre verso la **separazione a monte**, mai verso la redazione | Moderata | Accettata, **dichiarata definitiva** | A14 |
| **ADR-230** | **Le categorie particolari si dichiarano, non si rilevano** | Nessun classificatore. Esclusione per campo dichiarato (strutturato) e per sorgente dichiarata (documentale). Sul testo libero: non risolvibile, `R-87` | Costosa da invertire (è una posizione) | Accettata | A14 |
| **ADR-231** | **Il `purpose` può solo restringere** | Enum chiuso. Nessun `ALLOW` dipende dal `purpose`. Risolve `R-45` mettendolo dove è onesto | Facile | Accettata | A14 |
| **ADR-232** | **Classificazione a due assi, dichiarata** | `confidentiality_class` × `personal_data_class`. Mai inferita. Il derivato eredita (`INV-36`) | Moderata | Accettata | A14 |
| **ADR-233** | **Il registro `data_asset` è un artefatto di codice verificato in CI** | `data_assets.yaml`. Nessun data catalog. Stessa forma di `ADR-176` | Facile | Accettata | A14 |
| **ADR-234** | **La retention è una riga di policy, eseguita da un `job_type`** | `RetentionPolicy` nel Control Plane; nessun processo nuovo; `period = NULL` → inazione | Facile | Accettata | A14 |
| **ADR-235** | **Gli stati di cancellazione stanno sulla richiesta, non sulle righe** | `ErasureRequest` + `ErasureTask`; `PARTIAL` è uno stato visibile | Moderata | Accettata | A14 |
| **ADR-236** | **Identity shredding**: la cancellazione del soggetto distrugge la chiave di risoluzione, non l'audit | Attributi, credenziali, **chiusura degli alias**, `EXTERNAL_IDENTITY_LINK` → hard delete. La riga `subject` resta in stato `ERASED`. **Non è anonimizzazione** (`R-89`) | **Effettivamente irreversibile** | Accettata, con `B-95` aperta | A14 |
| **ADR-237** | **`deletion_ledger` rigiocato dopo ogni restore** | Append-only, solo identificatori e hash, conservato **fuori dal ciclo di backup**, rigiocato **prima** che il sistema accetti traffico | Facile, ma **va prima dei backup** | Accettata | A14 |
| **ADR-238** | **`audit_redaction`: la rimozione fisica da un audit si confessa** | Break-glass, due operatori, passa dal PDP, scrive **prima** di rimuovere, in un registro append-only non raggiungibile dallo stesso percorso | Facile come tabella; **irreversibile a ogni uso** | Accettata | A14 |
| **ADR-239** | **Colonna `key_ref` degenere Day-1** | Su ogni tabella con `tenant_id` e contenuto personale in testo libero. Day-1 non fa niente. Sblocca cifratura per tenant, CMK e crypto-shredding. **Risposta a `B-50`: non il meccanismo, il contratto** | **Facile adesso, costoso dopo** | Accettata | A14 |
| **ADR-240** | **Nessun testo libero di produzione nei dataset di evaluation** | `derivation ∈ {SYNTHETIC, PRODUCTION_STRUCTURED, HUMAN_REWRITTEN}`; `PRODUCTION_FREETEXT` non esiste nel tipo; `INV-40` in CI. **Chiude `AR-OB-24` con un meccanismo** | **Effettivamente irreversibile in senso inverso** | Accettata | A14 |
| **ADR-241** | **Il valore precedente di `ADR-221` è un'eccezione dichiarata a `INV-07`** | Perimetro stretto: solo i campi scritti, classe ereditata dal campo, **mai leggibile dal modello**, retention più corta del journal e non fissabile prima di `B-88` | Moderata | Accettata | A14 |
| **ADR-242** | **Registro `ExternalTransfer`: i destinatari si dichiarano, non si scoprono** | Si aggancia a `ADR-203` (allowlist di rete) e `AR-SE-11`. Day-1 l'unico destinatario è Odoo | Facile | Accettata | A14 |
| **ADR-243** | **Aggregati cross-tenant solo da vista dichiarata con soglia minima di gruppo** | Il valore di `k` è `NON ANCORA DECISO` (`B-79`, `B-98`). Day-1 la protezione è **non avere la vista** | Facile | **Parziale** (manca `k`) | A14 |
| **ADR-244** | **Nessun accesso permanente ai dati dei tenant per il personale** | Solo elevazione dichiarata (`ADR-119`): autorizzazione, `purpose`, tempo, audit, **luogo di trattamento** | Moderata | Accettata | A14 |
| **ADR-245** | **Legal hold non Day-1, ma il predicato esiste ed è costante falso** | Il gancio costa una riga; reinserirlo dopo in ogni percorso di cancellazione è il modo di dimenticarne uno | Facile | Accettata | A14 |
| **ADR-246** | **Export DSAR: solo dai nostri store, sotto RLS, con manifesto degli esclusi** | Non è `DEF-08` (export di audit), che resta di `A16`/`C26`. Rischio nuovo `R-94` | Moderata | Accettata | A14 |
| **ADR-247** | **Regione singola; sovereignty e luogo di trattamento tracciati separatamente** | Nessuna architettura regionale Day-1. La residency si dichiara, il luogo di trattamento si registra | Facile (non c'è niente da invertire) | Accettata | A14 |
| **ADR-248** | **La qualificazione titolare/responsabile è bloccata su `Q-03` e non la prendo** | La piattaforma fornisce le capacità tecniche di **entrambi** i ruoli. `RICHIEDE PARERE LEGALE` | — | Accettata come non-decisione dichiarata | A14 |
| **ADR-249** | **SoD: la forma è definita, il contenuto è `INTERPRETAZIONE NOSTRA`** | `SoDConflict` come riga; valutato su `on_behalf_of`, **mai** sull'`actor`; baseline minimo a 6 coppie, di cui 2 attive Day-1. `B-97` per un baseline citabile | Moderata | **Parziale** | A14 |
| **ADR-250** | **Nessuna scadenza di conformità costruita su fonti in conflitto (`B-90`)** | Invece: verificare che le capacità dell'art. 14(4) ci siano **già**. Sono `ADR-191`, `ADR-196`, `ADR-189`, `ADR-190`, `ADR-216`, `ADR-212`. La data diventa irrilevante per l'architettura, non per il contratto | Facile | Accettata | A14 |
| **ADR-251** | **`modified_fields[]` e `approval_decision_time` sono evidenza di conformità** | Prova dell'intervento umano **sostanziale** (art. 22, SCHUFA C-634/21). Conseguenza: **seguono la retention dell'audit** (`AR-DG-25`) | Facile | Accettata | A14 |
| **ADR-252** | **La retention della telemetria è strettamente più corta di quella dell'audit** | Completa `ADR-184` di `A12` fissando **l'ordinamento** invece dei valori. `INV-35` | Facile | Accettata | A14 |
| **ADR-253** | **Retention dei soggetti `DEPARTED`** | Non leggibili **e** tombstone immediati; purge dopo una finestra di grazia `NON ANCORA DECISO`. L'identità **resta**; muore solo con una `erasure_request`. Completa `AR-ID-09` | Irreversibile negli effetti | **Parziale** (manca il valore) | A14 |
| **ADR-254** | **Nessun oggetto `Consent` Day-1** | Il consenso non è la base giuridica di default. L'unico luogo plausibile è la memoria, dove il controllo utente esiste già in forma più forte (`ADR-094`, `AR-ME-09`, 8 endpoint) | Facile | Accettata | A14 |
| **ADR-255** | **`Erasure Coordinator` come modulo in-process** | Unico componente nuovo del documento. Zero servizi, zero datastore nuovi. Passa il test di `AR-CP-02` tre su tre | Moderata | Accettata | A14 |
| **ADR-256** | **Retention del testo libero di conversazione: 30 giorni** | Allineata alla convergenza dei maggiori (`R-15.1`): OpenAI 30 giorni, Anthropic 30 sui modelli avanzati, Salesforce Einstein Trust Layer 30 su audit e feedback. **Abbastanza per indagare un abuso o un difetto, troppo poco per costituire un archivio.** Chiude la voce di `DEF-13` con più leva su `R-87`, che era il maggior serbatoio di dato personale che deteniamo | Facile (è una riga di `RetentionPolicy`) | Accettata | thread |
| **ADR-257** | **Postura "beyond use" sui backup, dichiarata e comunicata** | Il GDPR **non esenta i backup**. Si adotta la linea ICO (`R-15.2`): i dati di backup si mettono **fuori uso** invece di essere estirpati, a tre condizioni — non usarli per altro scopo, impegnarsi alla cancellazione quando possibile, e **dirlo all'interessato**. Quest'ultima è *"la parte che le organizzazioni disattendono più spesso"*: la conferma di cancellazione **deve** indicare l'orizzonte di backup. Termine: **un mese solare**, prorogabile a due se complessa, ma **la proroga va comunicata prima della scadenza del primo mese** | Moderata (è processo + testo) | Accettata | thread |
| **ADR-258** | **Il `deletion_ledger` è una *suppression list* nel senso ICO** | Validazione esterna di `ADR-237`: *"un database che contiene tutte le richieste di cancellazione, rigiocato contro i dati ripristinati"* è il pattern raccomandato, e ci eravamo arrivati per ragionamento. Conseguenza operativa: il rigioco **non è un passo descritto, è un passo provato** della procedura di restore (lezione di `R-78`) | Facile | Accettata | thread |
| **ADR-259** | **Starter set SoD di ~45 regole, obbligatorio prima di `T-SE-10`** | `B-97` chiusa con un no: **non esiste un baseline pubblico autorevole**, la matrice ISACA si autodichiara non standard. Ma gli ordini di grandezza esistono: 45-125 nei set commerciali, 150-200 in un programma SAP maturo, **sotto 100 = ruleset incompleto**. Le 6 coppie di `ADR-249` vanno bene finché il capability floor tiene chiusa la superficie; **il giorno che si allarga, 6 non sono un motore, sono un placeholder**. Il set va **costruito**, non atteso (`B-105`) | Moderata | Accettata | thread |
| **ADR-260** | **Zero data retention verso terzi come proprietà strutturale dichiarabile** | Per noi il fornitore del modello **siamo noi**: modello locale, processo senza rete, `AR-DG-16` vieta staticamente l'invio del context a un provider esterno. **Non è una promessa contrattuale: è una proprietà dell'architettura**, e come tale è verificabile e opponibile. Rimetterla in discussione richiede di attraversare `T-DG-09`, mai una configurazione | **Costosa** (è una promessa commerciale che diventa vincolo) | Accettata | thread |
| **ADR-261** | **Tre corpi di test, non una piramide** | Il corpo **deterministico** (blocca sempre), il **probabilistico** (blocca solo dopo tre baseline, `ADR-180`), l'**umano** (dichiarato, quasi mai bloccante). La piramide classica presuppone che l'unità di test sia riproducibile: qui il componente centrale non lo è, quindi si separa per **natura dell'esito** invece che per ampiezza | Moderata | Accettata | A17 |
| **ADR-262** | **`OdooFake` a fedeltà verificata** | In CI Odoo è sostituito da un doppio che riproduce **otto comportamenti** noti (`ir.model.data` UNIQUE, `load()` upsert, nessun campo tracciato, `unlink()` che non passa da `write()`, …). La fedeltà non è dichiarata: è verificata da un **contract test bidirezionale notturno** contro Odoo reale | Moderata | Accettata | A17 |
| **ADR-263** | **Generatore `crm_seed` a tre livelli, incluso `hostile`** | `tiny` / `realistic` / `hostile`. Il livello `hostile` esiste perché **i difetti reali stanno nello sporco**: omonimi, campi vuoti, accenti, partner archiviati con fatture vive (`R-14.7`). Nessun dump di produzione: `INV-40`, `INV-43`, `R-73` | Facile | Accettata | A17 |
| **ADR-264** | **Due barriere per `AR-TL-16`** | Allowlist di rete (`INV-41`) **più** `OdooEndpoint` non costruibile con `environment = PRODUCTION` sotto test. Due, perché su una macchina sola una barriera non basta: `R-14.5` conta nove distruzioni di ambienti di produzione | Moderata | Accettata | A17 |
| **ADR-265** | **Contratto di flakiness: `k` e soglie si calcolano, non si scelgono** | Procedura in §9.2 del documento. **Mai retry**, sempre quarantena con owner e scadenza. I numeri sono `DEF-14`: il metodo statistico è `B-106`, ricerca ad **ALTA** priorità | Facile (sono parametri) | Accettata, **parametri aperti** | A17 |
| **ADR-266** | **Il registro dei test è un artefatto di CI** (`tests.yaml`) | Stessa forma di `ADR-176` (registro `M-OB-*`) e `ADR-233` (`data_asset`). Tre controlli: ogni voce risolve a un test, ogni **mandato** dei documenti è coperto, ogni voce bloccante ha un `negative_case`. L'errore **nomina la decisione architetturale che resta incontrollata** | Facile | Accettata | A17 |
| **ADR-267** | **I tre contenimenti + il dead man's switch sono un solo gate bloccante** (`G-QA-05`) | `KillSwitch` (`ADR-212`) con il **quarto test che nessuno scrive: la reversibilità**; rigioco del `deletion_ledger` come **precondizione strutturale del rientro in servizio** (`AR-DG-31`); drain ai confini di passo. Applica `R-78`: *un contenimento non provato non esiste* | Moderata | Accettata | A17 |
| **ADR-268** | **Tre classi di gate: bloccante / advisory / manuale** | Promozione advisory→bloccante a **quattro condizioni**, la quarta è il caso negativo provato (`INV-42`). Nove gate `G-QA-01`…`09`, sei bloccanti | Facile | Accettata | A17 |
| **ADR-269** | **Mutation testing su quattro superfici soltanto** | PDP, redazione, isolamento fra tenant, recovery. Non come metrica generale: la copertura di riga non è un gate (`ADR-280`) | Facile | Accettata | A17 |
| **ADR-270** | **Staging = quale Odoo tocchi, non quale macchina** | `AS-08` (embedding su CPU, hardware singolo) rende la parità di macchina impossibile. Lo staging diventa un valore di `Environment`, non un cluster | Moderata | Accettata | A17 |
| **ADR-271** | **Tre doppi del modello, nominati e distinti** | `DeterministicModel`, `ScriptedModel`, `MisbehavingModel`. Il terzo ha scopo **opposto** agli altri due: fa fallire il test apposta, per verificare il secondo anello di `ADR-040` | Facile | Accettata | A17 |
| **ADR-272** | **I tre compiti umani hanno cadenza e artefatto dichiarati** | Red teaming `ASI09` (`ADR-215`), revisione campionaria, classificazione dei difetti. Senza cadenza e artefatto restano buone intenzioni: è la difesa contro `R-101` e `R-70`, **dichiarata debole** | Facile | Accettata | A17 |
| **ADR-273** | **Nessun framework di eval di terzi** | La famiglia similarità/rubric contraddice `ADR-177`; le piattaforme con tracing gestito sono vietate staticamente da `AR-DG-16`; promptfoo è output matching. Runner in casa, in-process. `B-111` può far cadere la scelta | Facile | Accettata | A17 |
| **ADR-274** | **Stack di test deliberatamente noioso** | property-based dove serve, PostgreSQL reale, nessuno strumento nuovo in produzione. Zero servizi aggiunti Day-1 | Facile | Accettata | A17 |
| **ADR-275** | **L'holdout si esegue solo al rilascio** | `AR-OB-21`: il failure corpus si divide train/holdout alla creazione. Guardarlo di continuo lo brucia (`R-105`). Non impedibile tecnicamente: il numero di esecuzioni fra due rilasci è il segnale | Facile | Accettata | A17 |
| **ADR-276** | **Nessuna disattivazione di test o registro senza riga di quarantena** | Owner e scadenza obbligatori. È la difesa contro `R-69`, `R-91`, `R-103`: disattivare deve costare quanto scrivere | Facile | Accettata | A17 |
| **ADR-277** | **Chaos engineering su due guasti Day-1, non sei** | Gli altri quattro presuppongono un deployment multi-nodo che Day-1 non esiste. Si riaprono al primo deployment multi-nodo | Facile | Accettata | A17 |
| **ADR-278** | **Punti di interruzione dichiarati** (`CrashInjector`) | È ciò che rende i test di recovery **deterministici**, quindi bloccanti. *Il modo in cui si scrive il test decide se il gate può bloccare.* Trade-off: si testa il crash dove abbiamo pensato di metterci un punto (`R-104`) | Moderata | Accettata | A17 |
| **ADR-279** | **Matrice di autorizzazione a generazione parziale** | Righe positive scritte a mano (sono la specifica), negative generate dal complemento, un `ALLOW` inatteso fa fallire il test. Forma falsificabile di `AR-ID-20` | Facile | Accettata | A17 |
| **ADR-280** | **Si misura la copertura dei mandati, non la copertura di riga** | La copertura di riga come gate premia i test che eseguono codice senza asserire. `INV-44` rende «il conto è pagato» una query | Facile | Accettata | A17 |
| **ADR-281** | **Il capability probe è un gate bloccante e deterministico**, distinto dal gate di qualità che è advisory | Il probe risponde a domande **binarie** (tool calling, structured output, enum). Nessun cambio di `ModelVersion` passa senza probe | Facile | Accettata | A17 |
| **ADR-282** | **I test adversarial sono bloccanti anche col modello dentro** | L'esito atteso è **strutturale** (`DENY`), non statistico: la stocasticità non lo cambia. **È la proprietà più preziosa che l'architettura a invarianti di `A13` regala ai test.** Obbligo: ogni test adversariale asserisce anche che **il tentativo sia avvenuto** | Facile | Accettata | A17 |
| **ADR-283** | **Il golden set del retrieval è il gate di *attivazione* del retrieval, non di ogni rilascio** | Rende `ADR-178` un gate invece che una frase, e disinnesca `R-30`. Bloccare ogni rilascio produrrebbe un dataset etichettato in fretta | Facile | Accettata | A17 |
| **ADR-284** | **REST + OpenAPI 3.1, contract-first** | Il contratto dev'essere **enumerabile**: senza una lista chiusa di endpoint, `AR-QA-02` non ha dominio su cui applicarsi e la lista «cosa non esponiamo» non è verificabile. GraphQL respinto per due incompatibilità **strutturali**, non estetiche | Moderata | Accettata | A18 |
| **ADR-285** | **Una sola forma: ogni run è asincrono** | Nessun endpoint sincrono. La sincronia sarebbe una promessa che dipende da cosa il modello decide di fare. **Derivata**, non scelta: `ADR-104` (50 step / 10 min) + `ADR-216` (conferma umana su ogni scrittura) rendono l'attesa la norma. `?wait=` collassa i round-trip senza promettere niente | **Difficile** (è la forma dell'API) | Accettata | A18 |
| **ADR-286** | **Il polling è il contratto; SSE e feed pull sono ottimizzazioni della latenza di scoperta** | Se il canale spinto cade, il client degrada al polling senza perdere niente. SSE e non WebSocket: motivo primario l'**autenticazione**, riusa quella dell'API invece di inventarne una seconda | Facile | Accettata | A18 |
| **ADR-287** | **Nessun token streaming sulla superficie di approvazione** | Estensione operativa di `INV-29` e di `ASI09`: vedere il testo formarsi predispone ad accettarlo. Poggia su `AS-44`, che è a confidenza Bassa → `R-114` | Facile | Accettata | A18 |
| **ADR-288** | **Evento = riferimento, non consegna** | Envelope a **9 campi**, nessun payload di dominio. Chi riceve l'evento va a leggere la risorsa sotto la propria autorità: l'evento non può diventare un canale di esfiltrazione | Moderata | Accettata | A18 |
| **ADR-289** | **`api` e `worker` non si parlano: il trasporto interno è PostgreSQL** | Nessun HTTP interno, nessun broker, nessun gRPC. Day-1 girano sulla stessa macchina (`AS-63`). Si rivede a `T-AP-09` (multi-nodo) | Moderata | Accettata | A18 |
| **ADR-290** | **`Idempotency-Key` obbligatoria, non opzionale** | Su `POST /v1/runs` e sulle conferme. Opzionale significa che qualcuno la ometterà proprio quando serve. **Distinta** dall'idempotenza verso Odoo di `ADR-161`: le due non si sostituiscono | Moderata | Accettata | A18 |
| **ADR-291** | **Reverse proxy, non API gateway** | Il proxy può solo **rifiutare**, mai permettere (`AR-AP-26`). Un gateway che autorizza sarebbe un secondo punto di decisione, e `AR-ID-20` dice che ne esiste uno solo | Facile | Accettata | A18 |
| **ADR-292** | **Nessun webhook Day-1** | `AR-SE-11` (allowlist di host dichiarata nello schema) li rende incompatibili con la regola: un webhook è un URL scelto dal cliente. Il contratto è già scritto, si attiva a `T-AP-03` | Facile | Accettata | A18 |
| **ADR-293** | **`connectors/odoo/` concreto, con `transport.py` unico file che conosce il protocollo** | Firma `call(model, method, args, kwargs, ctx)`. **Nessun `CRM Adapter Interface`**: `AR-020` vieta un'astrazione generica senza due implementazioni reali. `B-53` (RPC deprecate in Odoo 22) resta **non risolta**: la si isola invece di indovinarla | Moderata (per costruzione) | Accettata, **`B-53` aperta** | A18 |
| **ADR-294** | **Budget di chiamate esterne per albero di run** | Consumato da un trigger di database, stessa forma di `ADR-146`. Un agent che itera può saturare un'istanza Odoo di produzione: **è un modo di far danno che non richiede nessun permesso di scrittura**. I valori sono `DEF-21`, il metodo per ricavarli è `B-116` | Facile nei valori | Accettata, **valori aperti** | A18 |
| **ADR-295** | **Venti cose che l'API non deve permettere**, verificate in CI contro la specifica | La lista di ciò che non si espone vale quanto quella di ciò che si espone, ma solo se è controllata da una macchina | Facile | Accettata | A18 |
| **ADR-296** | **Versioning nel path (`/v1/`), non per header** | L'header rende invisibile nella URL quale contratto si sta usando, e i log e le metriche perdono l'informazione. Si rivede a `T-AP-09` | Moderata | Accettata | A18 |
| **ADR-297** | **Probe di schema all'avvio: un campo dichiarato e mancante nel CRM impedisce l'avvio** | `AR-AP-24`. È fail-closed applicato alla configurazione: meglio non partire che partire e scoprirlo alla prima scrittura | Facile | Accettata | A18 |

> **ADR-029, 032** vanno chiusi **prima dello schema** (`run`, `run_step`).

> **Scadenza "prima dello schema" anche per: `ADR-067`, `072`, `073`, `074`, `083`, `084`, `087`.**

> **Scadenza "prima dello schema" anche per: `ADR-089`, `095`, `096`, `097`, `102`.**

> **`ADR-104` è l'unico ADR non prodotto da un documento**: nasce da un vincolo di dominio
> dichiarato dal committente in sessione. **Mandato per `A11`** (eventing e durable
> execution, che possiede il ciclo di vita del run): implementare i due tetti, distinguere il
> tempo attivo dal tempo sospeso, e definire il codice di errore. **Mandato per `A12`**:
> misurare `run_steps_p95` e `run_active_duration_p95` — se il p95 sfiorasse il tetto, il
> vincolo di dominio sarebbe sbagliato, non il tetto.

> **`ADR-068` ha la scadenza più urgente di tutte: prima delle misure VRAM di `A05`.**
> Se `A05` misurasse il bilancio prima che `B-26` confermi l'embedding su CPU, misurerebbe
> su un'ipotesi.

---

## 1b. Regole architetturali attive (`AR-001` … `AR-036`)

Definite per esteso in `level-a/01_ARCHITECTURE_PRINCIPLES.md` §37. Qui solo le più
vincolanti per i documenti successivi.

| ID | Regola in breve |
|---|---|
| AR-002 | `api` e `worker` comunicano solo tramite il database |
| AR-003 | Il ruolo `api` non chiama mai il modello |
| AR-004 | Un piano è una responsabilità, non un processo |
| AR-005 | Le dipendenze fra moduli sono verificate in CI |
| AR-006 / AR-008 | Il runtime legge il Control Plane, non lo scrive mai |
| AR-007 | Solo il Tool Runtime parla con sistemi esterni |
| AR-009 | L'output del modello è input non fidato |
| AR-011 | Solo `trust_class = system` può definire capability |
| AR-012 | Capability set congelato all'avvio, può solo restringersi |
| AR-013 | Nessun tool si esegue senza decisione del PDP registrata |
| AR-014 | Il token dell'utente non lascia mai la piattaforma |
| AR-015 | Se il PDP non risponde, l'azione è negata (fail closed) |
| AR-017 / AR-018 | `tenant_id` su ogni riga, preso dal token |
| AR-019 | Nessun datastore nuovo senza una misura del limite attuale |
| AR-020 | Nessuna interfaccia con una sola implementazione non identificata |
| AR-024 / AR-025 | I passi sono funzioni pure; nessun effetto fuori da un passo |
| AR-026 | Ogni side effect ha `idempotency_key` da `(run_id, step_index)` |
| AR-027 | Side effect di esito ignoto → stato `UNCERTAIN` + escalation |
| AR-028 | Ogni run ha budget espliciti (step, model call, token, tempo) |
| AR-030 | Ogni run porta una `priority` |
| AR-031 / AR-032 | Ogni decisione di autorizzazione è auditata; se l'audit fallisce, il side effect non procede |
| AR-035 | Ogni trigger di revisione ha una metrica che lo misura |

**Debito noto (autocritica A01 §46):** solo ~20 regole su 36 hanno una verifica automatica.
Al gate di Level A ogni `AR-` va marcata `ENFORCED` o `REVIEWED`; le `REVIEWED` contano
come debito.

### Regole del Control Plane (`A02`)

| ID | Regola |
|---|---|
| AR-CP-01 | Il runtime accede al Control Plane **solo** tramite `resolve()`, **solo** all'avvio del run |
| AR-CP-02 | Una risorsa si giustifica solo se ha lifecycle proprio + owner proprio + è riferita da qualcosa. Due mancanti su tre → è un campo |
| AR-CP-03 | `resolve()` non produce mai snapshot parziali: se un riferimento non si risolve, fallisce interamente |
| AR-CP-04 | Il rollout/rollback del binding richiede concorrenza ottimistica; un aggiornamento perso è vietato |
| AR-CP-05 | La separazione dei permessi Control Plane / Execution Plane è applicata **a livello di database**, non solo nel codice |

### Regole di governance (`A03`)

| ID | Regola |
|---|---|
| AR-GP-01 | Il PDP è una funzione pura: nessun I/O, nessun orologio, nessuna casualità |
| AR-GP-02 | Il token dell'utente non lascia il ruolo `api`; oltre passa solo un contesto di delega |
| AR-GP-03 | Il Tool usa la propria credenziale verso i sistemi esterni |
| AR-GP-04 | Il contesto di delega scade non dopo il token originale |
| AR-GP-05 | L'audit riporta sempre **entrambe** le identità: agent *per conto di* utente |
| AR-GP-06 | Un run senza utente usa un **service principal dichiarato**, mai un insieme vuoto trattato come illimitato |
| AR-GP-07 | Ogni condizione all'esecuzione è un'obbligazione, non un meccanismo separato |
| AR-GP-08 | Obbligazione non riconosciuta dal PEP → `DENY`, mai `ALLOW` ignorandola |
| AR-GP-09 | Ogni livello di policy può solo **restringere** quello superiore |
| AR-GP-10 | `INDETERMINATE` non è mai `ALLOW` né un `DENY` terminale |
| AR-GP-11 | Il livello di rischio si calcola a ogni decisione, non si memorizza sul run |
| AR-GP-12 | Chi approva ≠ chi ha avviato, quando la policy lo richiede |
| AR-GP-13 | L'approvazione è per **azione**, mai per run |
| AR-GP-14 | L'approvazione scade; oltre, il run va in `EXPIRED` |
| AR-GP-15 | L'approvazione è ri-verificata dal PDP al momento dell'esecuzione |
| AR-GP-16 | Consumo del budget e registrazione dello step sono **atomici** |
| AR-GP-17 | La redazione dei campi è applicata dal PEP, mai dal Tool |
| AR-GP-18 | La verifica del tenant è la **prima** regola e non è sovrascrivibile |
| AR-GP-19 | La cache di policy si invalida sulla versione del bundle, mai per TTL |
| AR-GP-20 | Ogni decisione produce una spiegazione completa, senza flag di debug |
| AR-GP-21 | L'audit distingue `policy_denied` da `policy_unavailable` |
| AR-GP-22 | Il kill switch di emergenza **non passa dal database** |
| AR-GP-23 | Non esiste accesso di emergenza che salti il PDP |

### Regole del runtime (`A04`)

| ID | Regola |
|---|---|
| AR-RT-01 | Fra `DECIDE` e `EXECUTE` c'è sempre `AUTHORIZE`: applicato dai **tipi** (`StepProposal` → `AuthorizedStep`) |
| AR-RT-02 | La verifica semantica non è mai l'unica base di una decisione con conseguenze |
| AR-RT-03 | Si scrive lo step `PENDING` **prima** di produrre l'effetto |
| AR-RT-04 | Ogni tool con side effect dichiara **idempotenza o verificabilità** → requisito per `A06` |
| AR-RT-05 | Un retry riusa lo stesso `step_index`, quindi la stessa `idempotency_key`; cambia solo `attempt` |
| AR-RT-06 | La cancellazione è cooperativa, ai confini di passo |
| AR-RT-07 | `BUDGET_EXCEEDED` produce un messaggio comprensibile che include cosa è già stato fatto |
| AR-RT-08 | Un run è eseguito da **un solo worker** per volta |
| AR-RT-09 | Parallelismo solo per i tool `READ` |
| AR-RT-10 | Nessun run in attesa occupa un worker |
| AR-RT-11 | Ogni tool dichiara la compensabilità: `COMPENSABLE` / `PARTIAL` / `IRREVERSIBLE` |
| AR-RT-12 | Le azioni irreversibili vanno il più tardi possibile nella sequenza |
| AR-RT-13 | La compensazione non è automatica sui `SIDE_EFFECT` |
| AR-RT-14 | Il context riceve un **riassunto** del journal, mai il journal intero |
| AR-RT-15 | Gli errori `BUSINESS` tornano al modello come osservazioni, non fanno fallire il run |
| AR-RT-16 | Un contesto di delega scaduto non si rinnova automaticamente alla ripresa |
| AR-RT-17 | Ogni run ha un tetto di step e di **durata attiva** (`ADR-104`); superarlo è uno stato visibile, mai un troncamento silenzioso. Il tempo in attesa di approvazione umana è escluso dal conteggio |

### Regole identity (`A09`) — `AR-ID-01` … `AR-ID-33`

| ID | Regola |
|---|---|
| AR-ID-01 | Un `subject_id` non è mai riassegnato, riscritto, né derivato da un dato mutabile |
| AR-ID-02 | Un identificatore di correlazione (`trace_id`, `span_id`) non entra mai in una decisione di autorizzazione |
| AR-ID-03 | `approval_window ≥ approval_ttl` di `A03` |
| AR-ID-04 | Day-1 `parent_delegation IS NULL` (nessuna delega a catena) |
| AR-ID-05 | Ogni autenticazione produce un `AuthenticationResult` con `issuer`, `subject_ref`, `auth_time`, `auth_strength`, `claims` |
| AR-ID-06 | Nessun claim di un issuer esterno diventa direttamente un input di autorizzazione |
| AR-ID-07 | `subject_id` non deriva mai dal `sub` dell'issuer |
| AR-ID-08 | La lettura della memoria risolve gli alias di `merged_into` |
| AR-ID-09 | La transizione a `DEPARTED` rende le memorie `USER` non leggibili |
| AR-ID-10 | L'auto-link di identità **per email** è vietato di default |
| AR-ID-11 | Un ID token non è mai usato come credenziale di accesso a un'API |
| AR-ID-12 | La risposta all'utente non distingue "utente inesistente" da "credenziale sbagliata" |
| AR-ID-13 | Nessuna credenziale è valida su più di un `audience` |
| AR-ID-14 | L'interruzione di un run per revoca produce un messaggio comprensibile che include **cosa è già stato fatto** |
| AR-ID-15 | La rotazione non è mai avviata da un run né da un tool |
| AR-ID-16 | Fallimento di credenziale **dopo** l'invio → `UNCERTAIN`; **prima** → `FAILED` |
| AR-ID-17 | Ogni chiamata esterna porta un marcatore `run_id`/`agent_id`/`subject_id` dove il protocollo lo consente |
| AR-ID-18 | Il marcatore di correlazione non è una credenziale né un'asserzione di identità |
| AR-ID-19 | Mappatura di identità esterna stantia o non `ACTIVE` → **DENY** |
| AR-ID-20 | Esiste **un solo** punto che può concedere: il PDP. Tutti gli altri possono solo togliere |
| AR-ID-21 | La `RetrievalScope` non è mai costruita da un identificatore fornito dal modello |
| AR-ID-22 | Nessun controllo è saltato perché il chiamante è locale |
| AR-ID-23 | Un `subject_id` appartiene a un solo tenant |
| AR-ID-24 | Un'approvazione è legata a un `action_binding`; se cambia, non vale più |
| AR-ID-25 | Un'approvazione si consuma **una sola volta**, atomicamente con lo step |
| AR-ID-26 | Nessun `AgentRun` modifica permessi, ruoli, policy o credenziali |
| AR-ID-27 | Ogni revoca produce un evento di audit e alimenta `revocation_effective_latency` |
| AR-ID-28 | Nessun evento di audit contiene segreti, token, password, contenuto di documenti, `value_text`, campi di dominio |
| AR-ID-29 | Chi legge l'audit vede **entrambi** gli identificatori: quello registrato e quello corrente |
| AR-ID-30 | Una ragione di negazione che rivelerebbe l'esistenza di una risorsa non arriva mai al modello |
| AR-ID-31 | N `DENY` consecutivi sulla stessa `(action, resource)` → `AUTHORIZATION_LOOP`, stato visibile |
| AR-ID-32 | Un tenant può avere più `issuer` attivi contemporaneamente |
| AR-ID-33 | Solo il modulo di autenticazione e il `Credential Broker` importano tipi con materiale crittografico |
| AR-ID-34 | `acl_subject` porta sempre un **discriminante** oltre all'identificatore (`odoo:res.users:42@<create_date>`). Un identificatore nudo non è mai sufficiente a risolvere una persona (`ADR-122`) |
| AR-ID-35 | Un utente **archiviato** nella sorgente esterna (`active = False`) rende il link `STALE`: `AR-ID-19` nega. "Archiviato" vale quanto "cancellato" ai fini dell'autorizzazione (`ADR-122`) |
| AR-ID-36 | Le password sono hashate con Argon2id ai parametri di `ADR-120`; nessun altro algoritmo è ammesso per nuove password |

### Regole agent communication (`A10`) — `AR-AC-00` … `AR-AC-25`

| ID | Regola |
|---|---|
| AR-AC-00 | Un agent nuovo si giustifica solo se **tutte e quattro** le domande del test di `A10` hanno risposta affermativa |
| AR-AC-01 | Day-1 nessun run ne avvia un altro: `parent_run_id IS NULL AND depth = 0 AND root_run_id = run_id` |
| AR-AC-02 | Nessuna `ToolVersion` può avere come implementazione l'avvio di un run. **Un agent non è mai un tool** |
| AR-AC-03 | `on_behalf_of` si **copia** dal padre, mai si ricalcola, mai è un `AgentRun` |
| AR-AC-04 | Il ceiling del figlio contiene **esplicitamente** il ceiling congelato del padre come fattore dell'intersezione |
| AR-AC-05 | Nessun campo di un `AgentTask`/`AgentResult` è input di una decisione di autorizzazione |
| AR-AC-06 | Il figlio **non risolve** un `MemorySnapshot` proprio: eredita per riferimento, eventualmente ristretto |
| AR-AC-07 | Nessun run figlio usa un `model_id` diverso da quello della radice (**blinda `AS-08`**) |
| AR-AC-08 | Step e durata attiva si consumano da un **ledger unico dell'albero**, atomicamente con la scrittura dello step |
| AR-AC-09 | La deadline è **assoluta** e si copia; non esistono timeout per run |
| AR-AC-10 | La profondità massima è nel `ConfigSnapshot`; superarla è uno **stato visibile** |
| AR-AC-11 | Un `agent_id` già presente in `ancestor_agent_ids` non è dispatchabile |
| AR-AC-12 | Un `AgentResult` ha `trust_class = retrieved`: dato, mai istruzione |
| AR-AC-13 | Ogni riga di audit porta `root_run_id`, `parent_run_id`, `parent_step_index`, `depth` **oltre** alle due identità di `INV-15` |
| AR-AC-14 | L'approvazione la chiede il PEP che esegue; **nessun `AgentRun` è mai un approver** |
| AR-AC-15 | Il dispatch è **uno step**, scritto `PENDING` prima, e consuma dal ledger |
| AR-AC-16 | `child.tenant_id = parent.tenant_id` |
| AR-AC-17 | Nessuna capability dichiarata da un `AgentCard` entra nel Control Plane senza **materializzazione umana** |
| AR-AC-18 | La cancellazione della radice si propaga ai discendenti ai confini di passo; **nessun figlio sopravvive alla radice** |
| AR-AC-19 | Un artifact passa per `content_hash`, mai incorporato nel messaggio |
| AR-AC-20 | Nessun `SecretMaterial`, credenziale o client autenticato attraversa un `AgentTask` |
| AR-AC-21 | Chi propone la comunicazione agent→agent deve **dimostrare** che i rimedi più economici sono stati provati e misurati |
| AR-AC-22 | **Il multi-agent non si apre prima che `R-41` sia chiusa** (catena 1 via API key per-utente) |
| AR-AC-23 | Il fan-out parallelo di run figli è ammesso solo se **tutti** i figli hanno ceiling di sola lettura |
| AR-AC-24 | Un tool MCP che richiede più di un round-trip non è materializzabile finché `B-64` è aperta |
| AR-AC-25 | Il figlio **eredita** la `priority` della radice; non può dichiararne una propria |

**Debito noto: 19 su 26 con verifica automatica.** Le sette `REVIEWED` (`AR-AC-00`, `-17`,
`-18`, `-21`, `-22`, `-24`, in parte `-12`) contano al gate di Level A.

### Regole eventing ed esecuzione (`A11`) — `AR-EV-01` … `AR-EV-31`

| ID | Regola |
|---|---|
| AR-EV-01 | Il trasporto è il database. Nessun broker, nessun bus, nessuna coda in memoria |
| AR-EV-02 | Nessuna tabella di lavoro, journal, audit o outbox è `UNLOGGED` |
| AR-EV-03 | Ogni riga di lavoro porta `tenant_id` ed è sotto RLS |
| AR-EV-04 | Nessun worker attende in memoria: ogni attesa è **una riga con un istante di risveglio** |
| AR-EV-05 | Un `INSERT` in `run_step` è valido solo se **consuma il ledger dell'albero nella stessa transazione** |
| AR-EV-06 | Il tempo attivo è un **contatore** incrementato da chi tiene il lease, mai una differenza fra timestamp |
| AR-EV-07 | Ogni scrittura di un worker su un run porta il proprio `lease_epoch` |
| AR-EV-08 | Il recovery **non riesegue mai** uno step `IN_FLIGHT` non idempotente e non verificabile |
| AR-EV-09 | `idempotency_key` deriva da `(run_id, step_index)` e non cambia fra i tentativi |
| AR-EV-10 | Un retry non cambia mai `step_index`; cambia `attempt` |
| AR-EV-11 | La classe di errore la dichiara il connector; **il modello non decide mai se ritentare** |
| AR-EV-12 | Nessun `job` chiama il modello, esegue un tool con `side_effects ≠ READ`, o avvia un run |
| AR-EV-13 | Nessun percorso di codice avvia un run in conseguenza della scrittura di un evento |
| AR-EV-14 | La cancellazione è una riga sull'albero, osservata ai confini di passo |
| AR-EV-15 | Nessun figlio sopravvive alla radice: il `tree_reaper` chiude i discendenti non presidiati |
| AR-EV-16 | L'outbox contiene **solo riferimenti**: mai contenuto di dominio, mai segreti |
| AR-EV-17 | Un callback esterno **si autentica prima** di essere correlato; la correlazione non è autenticazione |
| AR-EV-18 | Nessuno stato di esecuzione è derivato per fold di un log: lo stato **si scrive** |
| AR-EV-19 | Un run che riprende **non guadagna mai** autorità, budget o deadline |
| AR-EV-20 | Il drain di un deployment rilascia il lease solo a un **confine di passo** |
| AR-EV-21 | Nessun run in attesa occupa un lease |
| AR-EV-22 | Ogni transizione durevole avviene in **una** transazione insieme all'audit |
| AR-EV-23 | Ogni stato terminale porta un `termination_reason` non nullo |
| AR-EV-24 | Nello stato di esecuzione entra solo un **riferimento**, mai un contenuto |
| AR-EV-25 | Nessuna credenziale è persistita nello stato di esecuzione |
| AR-EV-26 | Le deadline si restringono verso il basso, **mai** si allargano |
| AR-EV-27 | `timeout esterno < heartbeat_interval < lease_ttl` |
| AR-EV-28 | Nessun componente dipende da un ordine globale degli eventi |
| AR-EV-29 | Un cambiamento incompatibile di un evento richiede un `event_type` **nuovo**, non un `event_version` |
| AR-EV-30 | Una versione pinnata mancante fa fallire il run in modo visibile; **nessuna sostituzione silenziosa** |
| AR-EV-31 | Un replay **non riproduce mai** un side effect |

| AR-EV-32 | Ogni scrittura con effetti verso Odoo porta un **external ID deterministico** nel namespace `__agent__`, creato **nella stessa transazione** del record (`ADR-161`) |
| AR-EV-33 | Nessun percorso di codice legge, modifica o cancella righe di `ir.model.data` **fuori** dal namespace `__agent__` |
| AR-EV-34 | Un run entra in attesa di approvazione **solo dopo** `DISPATCH_CONFIRMED`; se la conferma non arriva entro la finestra, termina con `APPROVAL_UNDELIVERABLE` (`ADR-162`) |
| AR-EV-35 | Ogni `job_type` dichiara `max_staleness`; superarla **è un evento di errore**, non una metrica mancante. La riga di liveness conta le **consegne riuscite**, non i giri di loop (`ADR-163`) |

**Debito noto: 28 su 35 con verifica automatica.** Le sette `REVIEWED` (`AR-EV-04`, `-17`,
`-18`, `-20`, `-28`, in parte `-05` e `-15`) contano al gate di Level A.

### Regole observability (`A12`) — `AR-OB-01` … `AR-OB-24`

| ID | Regola |
|---|---|
| AR-OB-01 | Emette telemetria chi **possiede** il dato. Nessun osservatore esterno legge lo stato altrui |
| AR-OB-02 | Nessuna richiesta di conformità o contestazione si soddisfa con una query sulla **telemetria** |
| AR-OB-03 | Nessuna scrittura di telemetria avviene **dentro la transazione** di uno step durevole |
| AR-OB-04 | Label vietate su ogni metrica: `run_id`, `tenant_id`, `subject_id`, `trace_id`, `span_id`, qualunque campo di dominio |
| AR-OB-05 | Un'approvazione registra i **nomi** dei campi modificati, mai i valori |
| AR-OB-06 | Gli attributi di span vengono da una **allowlist chiusa**. Ammessi i nomi di campo, mai i valori |
| AR-OB-07 | Ogni span `STEP` corrisponde a una riga `run_step`. Uno span senza journal è un **errore**, non un dato |
| AR-OB-08 | Nessun campo di log è testo libero. `event` è un enum |
| AR-OB-09 | `DEBUG` è spento in produzione, attivabile per `(component, tenant, durata)` con **spegnimento automatico**, e non può mai contenere contenuto |
| AR-OB-10 | Nessuna metrica è emessa se non esiste nel registro con le label dichiarate |
| AR-OB-11 | Nessun identificatore di correlazione nuovo oltre a `trace_id`/`span_id` |
| AR-OB-12 | Nessun allarme dipende da una metrica disponibile in **un solo** profilo di serving |
| AR-OB-13 | La `max_staleness` di un consumatore è sempre **più corta** della soglia oltre cui il ritardo ha conseguenze per l'utente |
| AR-OB-14 | La violazione di una guardia di invariante è un **evento di errore**, non un alert su soglia |
| AR-OB-15 | La telemetria può essere scartata, **mai in silenzio**: ogni scarto incrementa un contatore |
| AR-OB-16 | Nessuna configurazione di sampling può portare sotto il 100 % le **otto classi critiche**. Applicato nel codice, non in configurazione |
| AR-OB-17 | `telemetry_span` e `metric_sample` hanno `tenant_id` non nullo e RLS attiva |
| AR-OB-18 | Il `Reproduction Bundle` non bypassa mai la RLS e scrive la propria riga di audit **prima** di restituire |
| AR-OB-19 | Un esito prodotto da un LLM judge è marcato `advisory` **nel tipo** e non entra in nessun gate |
| AR-OB-20 | I dataset di evaluation sono file versionati in repository; la modifica passa da una review |
| AR-OB-21 | Il failure corpus si divide in *train* e *holdout* alla creazione; l'holdout **non entra mai** in un fine-tuning |
| AR-OB-22 | Nessun error budget su isolamento fra tenant, decisioni di autorizzazione, `SIDE_EFFECT` non autorizzati, contenuto in archivi operativi |
| AR-OB-23 | Un allarme esiste solo se corrisponde a un **sintomo**, ha una procedura e ha un tasso atteso basso |
| AR-OB-24 | Nessun dato di produzione entra in un dataset di evaluation senza **anonimizzazione dichiarata** |

**Debito noto: 17 su 24 con verifica automatica.** Le sette `REVIEWED` contano al gate.

### Regole security (`A13`) — `AR-SE-01` … `AR-SE-18`

| ID | Regola |
|---|---|
| AR-SE-01 | Nessun rilevamento euristico blocca un run da solo |
| AR-SE-02 | L'oggetto di un'approvazione è un `ActionBinding` tipizzato; la giustificazione del modello è `advisory` **nel tipo** |
| AR-SE-03 | Le etichette mostrate in approvazione provengono da una **lettura autoritativa**, mai dal modello |
| AR-SE-04 | **Un'anteprima non può invocare un tool con `side_effects ≠ READ`** |
| AR-SE-05 | La classe di reversibilità viene dalla dichiarazione del tool, **mai dal modello** |
| AR-SE-06 | Nessuna configurazione può portare un'azione irreversibile alla conferma singola |
| AR-SE-07 | Superare il tetto di approvazioni degrada a revisione differita, **mai** ad auto-approvazione |
| AR-SE-08 | Nessun componente concentra credenziali verso sistemi eterogenei; il `Credential Broker` è l'eccezione dichiarata |
| AR-SE-09 | Il pre-filtro autorizzativo verso il CRM è una guardia: nessun error budget lo copre |
| AR-SE-10 | Ogni uscita di rete passa per l'allowlist del container |
| AR-SE-11 | Nessun tool accetta un URL senza allowlist di host **dichiarata nello schema** |
| AR-SE-12 | Il parsing di contenuto esterno avviene in un processo senza rete e senza credenziali |
| AR-SE-13 | Nessun caricamento di pesi del modello da fonte remota a runtime; hash verificato |
| AR-SE-14 | L'attivazione di `DebugCapture` produce un evento di sicurezza e una notifica al tenant |
| AR-SE-15 | **Lo scatto di `T-TL-03` richiede una revisione di sicurezza formale prima dell'integrazione** |
| AR-SE-16 | Ogni componente nuovo dichiara il comportamento in caso di guasto; default **fail-closed con stato visibile** |
| AR-SE-17 | Ogni incidente di sicurezza produce un test di regressione prima della chiusura |
| AR-SE-18 | Il `KillSwitch` passa dal PDP; **non esiste alcun percorso di contenimento che bypassi l'autorizzazione** |

| AR-SE-19 | **Nessuna configurazione può portare a zero il requisito di conferma su una scrittura.** L'uscita esiste solo via `T-GP-02` riformulato | statica |
| AR-SE-20 | Nessun percorso di codice invoca una cancellazione fisica su un sistema esterno; esiste solo `archive` | statica |
| AR-SE-21 | Un tool di scrittura dichiara la cardinalità massima; il default è **1**, e se >1 il conteggio è mostrato nell'approvazione | statica + test |
| AR-SE-22 | Nessuna scrittura su un campo esistente avviene senza che il valore precedente sia stato registrato nel journal | statica + test |
| AR-SE-23 | Su un record `IMMUTABLE_RECORD` non esiste alcun tool di `update`: solo rettifica | statica (il tipo lo impone) |
| AR-SE-24 | I campi amministrativi di `res.partner` (P.IVA, C.F., sede, coordinate bancarie) non sono raggiungibili da alcun tool di scrittura Day-1 | statica |
| AR-SE-25 | Ogni campo che innesca un'automazione nel sistema esterno è marcato nello schema del tool | `REVIEWED` |
| AR-SE-26 | Nessuna `agent_version` è rilasciata senza l'albero delle azioni nel caso peggiore, approvato | `REVIEWED` (gate di rilascio) |
| AR-SE-27 | Le coppie di funzioni in conflitto SoD sono dichiarate e valutate **prima** dell'esecuzione | statica + test |
| AR-SE-28 | Nessun tool di scrittura è raggiungibile su un'entità fuori dalla superficie CRM dichiarata Day-1 | statica |

**Debito noto: 22 su 28 con verifica automatica.** Le sei `REVIEWED` contano al gate.

### Regole data governance (`A14`) — `AR-DG-01` … `AR-DG-28`

| ID | Regola |
|---|---|
| **AR-DG-01** | Ogni dato persistito appartiene a un `data_asset` dichiarato nel registro; nessuna tabella senza voce |
| **AR-DG-02** | Ogni `data_asset` dichiara `confidentiality_class` e `personal_data_class`. Nessuna classificazione inferita a runtime |
| **AR-DG-03** | `writable_fields ⊆ allowed_fields`: un campo che non si può leggere non si può scrivere. Nessun tool scrive su un campo `SPECIAL_CATEGORY` |
| **AR-DG-04** | La projection dei campi è decisa dal PDP e applicata **prima** della chiamata al connector; la redazione è seconda linea, mai unica. Nessun tool espone un campo che un altro nega alla stessa `FieldScope` |
| **AR-DG-05** | Nessun campo di dominio del CRM è persistito, **con l'unica eccezione dichiarata di `ADR-241`** |
| **AR-DG-06** | Il `purpose` può solo restringere; nessun `ALLOW` dipende da esso |
| **AR-DG-07** | Ogni categoria di dato ha una retention dichiarata come **riga di policy**, mai come costante nel codice |
| **AR-DG-08** | Nessun job di retention cancella righe di audit; la lista delle tabelle su cui opera è chiusa |
| **AR-DG-09** | Una richiesta di cancellazione per soggetto risolve l'intera **chiusura degli alias** `merged_into` |
| **AR-DG-10** | La cancellazione di un documento propaga a `parsed_content`, `chunk`, `embedding`, `entity_link` e blob non referenziati |
| **AR-DG-11** | Nessun testo libero di produzione entra in un dataset di evaluation. **Non esiste il percorso di codice** |
| **AR-DG-12** | La retention della telemetria è **strettamente più corta** di quella dell'audit |
| **AR-DG-13** | Nessun accesso permanente ai dati dei tenant per il personale di piattaforma; solo elevazione dichiarata a tempo |
| **AR-DG-14** | Ogni elevazione registra `purpose`, durata e **luogo di trattamento** |
| **AR-DG-15** | Nessun trasferimento esterno esiste se non è nel registro `ExternalTransfer` **e** nell'allowlist di rete |
| **AR-DG-16** | Nessun percorso di codice invia il context a un model provider esterno |
| **AR-DG-17** | Ogni tabella con `tenant_id` e contenuto personale in testo libero porta `key_ref` |
| **AR-DG-18** | Ogni cancellazione produce una riga nel `deletion_ledger`; il ledger è **rigiocato** dopo un restore prima di accettare traffico |
| **AR-DG-19** | La rimozione fisica di una riga di audit passa **solo** dal registro `audit_redaction` |
| **AR-DG-20** | Un aggregato cross-tenant è servito solo da una vista dichiarata con soglia minima di gruppo |
| **AR-DG-21** | Nessun dato di produzione diventa dato di addestramento: non esiste il percorso di codice |
| **AR-DG-22** | La classificazione di un dato derivato è **almeno** quella della sua sorgente |
| **AR-DG-23** | Un `EvaluationCase` dichiara `derivation`; `PRODUCTION_FREETEXT` non è un valore ammesso dal tipo |
| **AR-DG-24** | Ogni conflitto SoD è valutato su `on_behalf_of`, **mai** sull'`actor` agent |
| **AR-DG-25** | `modified_fields[]` e `approval_decision_time` seguono la retention dell'**audit**, non della telemetria |
| **AR-DG-26** | Un documento entra nell'indice solo se la sua sorgente **e** la sua `sensitivity_max` sono dichiarate |
| **AR-DG-27** | Il registro `data_asset` è verificato in CI contro lo schema: una tabella nuova senza voce **fa fallire la build, nominando la decisione bloccata** |
| **AR-DG-28** | Nessun export attraversa il confine di tenant; l'export si costruisce sotto RLS con l'identità del **richiedente** |

| **AR-DG-29** | La conferma di una cancellazione **dichiara l'orizzonte di backup** entro cui il dato sparirà anche da lì | `REVIEWED` (è testo) |
| **AR-DG-30** | Nessun backup viene ripristinato **selettivamente** per recuperare un dato cancellato: violerebbe la postura *beyond use* | statica + procedura |
| **AR-DG-31** | Il rigioco del `deletion_ledger` è un **passo eseguito e verificato** della procedura di restore, non un passo documentato | **test di restore** |
| **AR-DG-32** | Nessun percorso di codice invia prompt, context o output a un fornitore di modello esterno. **La ZDR verso terzi è una proprietà, non una promessa** | statica |

**Debito noto: 28 su 32 con verifica automatica.** Le quattro `REVIEWED` (`AR-DG-02`, `-14`, `-26`, `-29`) contano al gate.


**Debito noto: 28 su 33 con verifica automatica** — il rapporto migliore fra i documenti,
perché quasi tutte le regole di identità sono esprimibili come vincoli di tipo o di database.
Le cinque `REVIEWED` (`AR-ID-09`, `-14`, `-17`, `-18`, `-29`) contano al gate di Level A.

### Regole model/inference (`A05`) — `AR-MD-01` … `AR-MD-15`

| ID | Regola (le più vincolanti) |
|---|---|
| AR-MD-02 | Una risposta del modello senza identità di produzione completa è un **errore**, non una risposta |
| AR-MD-03 | Il runtime valida **sempre** lo schema, anche con constrained decoding attivo |
| AR-MD-04 | Un tool allucinato è un'**osservazione** per il modello, non un guasto |
| AR-MD-05 | Nessun prompt letterale nel codice |
| AR-MD-06 | Si ritenta la **chiamata**, mai il passo (coerente con `AR-RT-05`) |
| AR-MD-07 | Nessun troncamento automatico del context lato serving |
| AR-MD-08 | Pesi verificati per digest, allowlist, nessuna rete dal container di serving |
| AR-MD-09 | Nessun egress verso provider esterni senza passare dal PDP |
| AR-MD-11 | Specializzazione di `AR-019` per l'inference |
| AR-MD-13 | Lo streaming è cosmetico: non produce effetti |
| AR-MD-15 | Le parti variabili del prompt vanno **in coda**, per non invalidare il prefix caching |

### Regole tool (`A06`) — `AR-TL-01` … `AR-TL-16`

| ID | Regola |
|---|---|
| AR-TL-01 | Solo `connectors/` fa rete |
| AR-TL-02 | La `risk_class` deriva dal **comportamento reale**, non dall'intenzione |
| AR-TL-03 | Niente SQL né linguaggi di query come argomento |
| AR-TL-04 | Una capability mancante è un'**osservazione misurata**, non un errore da nascondere |
| AR-TL-05 | **Nessun argomento di tool può essere un programma** (principio-spina del documento) |
| AR-TL-06 | Gli identificatori si **osservano**, non si inventano |
| AR-TL-07 | Il modello nomina la **chiave**, mai la versione |
| AR-TL-08 | `tool_definitions_hash` resta stabile per tutta la durata del run |
| AR-TL-09 | La fase pre-send è **sempre** ritentabile |
| AR-TL-10 | Il Tool Runtime **non ritenta mai** (è l'executor a farlo) |
| AR-TL-11 | Niente import automatico di tool di terzi |
| AR-TL-12 | Niente `READ` verso terzi trattato come innocuo |
| AR-TL-13 | Nessun segreto arriva al codice del tool |
| AR-TL-14 | `tenant`, `principal`, `now`, `idempotency_key` sono **iniettati**, mai forniti dal modello |
| AR-TL-15 | `limit` obbligatorio su ogni tool che restituisce liste |
| AR-TL-16 | Mai un `SIDE_EFFECT` eseguito contro il sistema di produzione durante i test |

### Regole knowledge (`A07`) — `AR-KN-01` … `AR-KN-22`

| ID | Regola |
|---|---|
| AR-KN-01 | Nessun frammento entra nel context senza `tenant_id` verificato **nella query** e RLS attiva sulla tabella |
| AR-KN-02 | Il filtro di autorizzazione è **nella query**, mai solo dopo. Ciò che viene dopo può solo togliere |
| AR-KN-03 | Un frammento recuperato non è mai un'istruzione: `trust_class = retrieved` è una costante del tipo |
| AR-KN-04 | Un frammento senza provenance completa (11 campi) non entra nel context |
| AR-KN-05 | La piattaforma non è mai system of record di un dato aziendale esterno |
| AR-KN-06 | Nessun campo di dominio del CRM viene copiato nell'indice: solo identificatori |
| AR-KN-07 | Ogni artefatto derivato è ricostruibile da blob + versioni di trasformazione (**test in CI**) |
| AR-KN-08 | Le ACL si referenziano, non si copiano |
| AR-KN-09 | Proiezione dei grant più vecchia della soglia → retrieval **fail closed** su quella sorgente |
| AR-KN-10 | I frammenti stanno **in coda** al prompt, dopo le tool definition e prima del riassunto del journal |
| AR-KN-11 | Il taglio per budget avviene per frammenti interi, mai a metà frammento |
| AR-KN-12 | L'audit del retrieval registra identificatori e hash, mai il testo |
| AR-KN-13 | Nessuna cache dei risultati di retrieval |
| AR-KN-14 | Ogni embedding è attribuibile a source, source_version, modello, versione, chunking, preprocessing |
| AR-KN-15 | Un documento non parsabile è uno **stato visibile**, mai un documento vuoto |
| AR-KN-16 | Nessun processo di ingestion usa la GPU riservata al modello di generazione |
| AR-KN-17 | Ogni run dichiara un `freshness_requirement` e il Retrieval Layer lo applica |
| AR-KN-18 | Nessun embedding esce da un'API |
| AR-KN-19 | Ogni ingestion ha una `ingestion_key` deterministica da tenant, sorgente, id, `content_hash` |
| AR-KN-20 | Nessuna misura di recall senza golden set; **senza golden set `T-03` non può scattare** |
| AR-KN-21 | Il retrieval è un canale di `OBSERVE`, non un tool Day-1 |
| AR-KN-22 | Il `Blob Store` non conosce tenant né permessi; un hash si ottiene solo da una riga protetta da RLS |

**Debito noto:** ~15 delle 22 hanno verifica automatica realistica. `AR-KN-05`, `-06`, `-08`,
`-13`, `-18`, `-22` si verificano a revisione → contano come debito al gate di Level A.

### Regole memory (`A08`) — `AR-ME-01` … `AR-ME-20`

| ID | Regola |
|---|---|
| AR-ME-01 | La classificazione knowledge/memory segue il test a tre domande. In dubbio → knowledge o dato live, **mai** memory |
| AR-ME-02 | Nessuna memoria è autoritativa su un fatto di dominio; il dato di dominio si legge sempre dal `Tool` |
| AR-ME-03 | `tenant_id`, `scope_type`, `scope_id`, `subject_id`, `run_id` sono **iniettati** dal runtime, mai forniti dal modello |
| AR-ME-04 | Il set di memoria di un run è congelato all'avvio e può solo restringersi |
| AR-ME-05 | Il filtro di autorizzazione della memoria sta **nella query**; gli strati successivi possono solo togliere |
| AR-ME-06 | Una memoria entra nel context con `trust_class = retrieved`; nessuna memoria definisce capability |
| AR-ME-07 | Nessuna decisione del PDP legge la tabella `memory` |
| AR-ME-08 | Solo `EXPLICIT`, `OBSERVED`, `ADMIN` in stato `ACTIVE` entrano nel `MemorySnapshot` |
| AR-ME-09 | Una memoria `EXPLICIT` conserva la formulazione dell'utente; il modello non la riscrive |
| AR-ME-10 | `value_text ≤ max_memory_chars` (280 Day-1) |
| AR-ME-11 | Il riassunto del journal è **generato da codice**, mai dal modello |
| AR-ME-12 | Il digest non perde mai un identificatore osservato in un `ToolResult` |
| AR-ME-13 | Step `SIDE_EFFECT`, step `UNCERTAIN`, identifier ledger e `run.input` **non sono comprimibili** |
| AR-ME-14 | Sotto pressione di budget cedono, in quest'ordine: frammenti → zona B → memorie meno importanti → `N` di zona A. **Mai** il blocco incomprimibile |
| AR-ME-15 | Ordine del prompt: istruzione → tool definition → `MemorySnapshot` → frammenti → `WorkingSetBlock` → turno |
| AR-ME-16 | L'audit della memoria registra identificatori e hash, **mai** `value_text` |
| AR-ME-17 | La cancellazione è tombstone immediato + purge asincrona, ed è **irreversibile** |
| AR-ME-18 | Nessuna memoria con `scope_type = USER` è leggibile in un run il cui principal non è quel soggetto |
| AR-ME-19 | Superare il cap di memorie attive è uno **stato visibile**: rifiuto + metrica, mai cancellazione silenziosa |
| AR-ME-20 | Se il PDP non produce una `MemoryScope`, il run parte **senza memoria** e lo dichiara nel context |

**Debito noto:** 14 delle 20 hanno verifica automatica. `AR-ME-01`, `-02` (in parte),
`-09`, `-15` (in parte) restano `REVIEWED` → debito al gate di Level A.

### Regole testing / QA (`A17`) — `AR-QA-01` … `AR-QA-19`

| ID | Regola | Verifica |
|---|---|---|
| AR-QA-01 | Nessun test del corpo deterministico dipende da un'inferenza su GPU | ambiente di CI senza serving |
| AR-QA-02 | Per ogni endpoint pubblico e per ogni tool esiste un test per ciascuna delle **sette classi negative**, più la classe «valido e ostile» | registro |
| AR-QA-03 | Ogni test possiede il proprio schema di database | harness |
| AR-QA-04 | Nessun `EvaluationCase` è generato dal modello che sarà valutato | statica |
| AR-QA-05 | Un `EvaluationResult` senza version matrix completa è un **errore**, non un risultato | tipo |
| AR-QA-06 | Dipendenza reale quando il suo comportamento è ciò che si testa; doppio quando è un prerequisito | `REVIEWED` |
| AR-QA-07 | Un test deterministico instabile **non si ritenta**: quarantena con owner e scadenza | statica (nessun retry nel runner) |
| AR-QA-08 | Ogni test che esercita un percorso con conseguenze asserisce anche sulla riga di audit | `REVIEWED` |
| AR-QA-09 | Il test di isolamento fra tenant copre le **nove superfici**, lista chiusa nel registro. Una superficie di persistenza nuova non registrata **fa fallire la build** | statica |
| AR-QA-10 | Nessun test di performance produce un gate finché non esiste una baseline misurata su hardware reale | registro |
| AR-QA-11 | Il golden set è dichiarato nel registro; se manca o è scaduto il report **nomina la decisione architetturale che resta incontrollata** | registro |
| AR-QA-12 | Un test bloccante non ha owner diverso da chi possiede il codice che verifica. **Unica eccezione: la famiglia di sicurezza** | registro |
| AR-QA-13 | Un `EvaluationCase` nato da un incidente ha **una sola** post-condizione o **un solo** vincolo | `REVIEWED` |
| AR-QA-14 | Una voce del registro `BLOCCANTE` senza `negative_case` **fa fallire la build** | statica (`ADR-266`) |
| AR-QA-15 | Il fallimento di un test del gate di sicurezza è un **evento di sicurezza**, non un difetto di build | processo + `ADR-213` |
| AR-QA-16 | Nessun percorso di codice raggiungibile in produzione può armare un punto di interruzione | statica |
| AR-QA-17 | Se la eval suite non esegue tutti i casi, il campionamento è **dichiarato** e la copertura è nel report | runner |
| AR-QA-18 | Nessuno dei tre registri (`M-OB-*`, `data_asset`, `TC-QA-*`) si disattiva senza riga di quarantena | statica |
| AR-QA-19 | Il test harness può interrogare direttamente il database dell'Odoo **di test**. **Eccezione dichiarata a `INV-07`**, valida solo sotto test e solo verso `environment = TEST` | statica (`ADR-264`) |

### Regole API / integration (`A18`) — `AR-AP-01` … `AR-AP-32`

| ID | Regola | Verifica |
|---|---|---|
| AR-AP-01 | Nessuna primitiva di composizione di run. Comporre run è del codice applicativo del client | statica (assenza di endpoint) |
| AR-AP-02 | La chiusura di una connessione HTTP non produce mai un effetto sul dominio | test |
| AR-AP-03 | In saturazione, le letture di stato non sono mai rifiutate prima delle scritture | test |
| AR-AP-04 | Nessun payload di webhook contiene dato di dominio o testo libero | statica (allowlist di campi) |
| AR-AP-05 | Nessun endpoint di webhook è registrabile senza allowlist per tenant approvata | statica + test |
| AR-AP-06 | `retention(idempotency_record) ≥ retention(run)` | statica sulla policy |
| AR-AP-07 | L'`api` non ritenta mai verso il `worker`; l'unico retry esterno è quello del client | statica |
| AR-AP-08 | Il `detail` di un errore è una **costante per `code`** | statica (enum) |
| AR-AP-09 | `AUTHORIZATION_DENIED` e `AUTHORIZATION_UNAVAILABLE` sono distinti; nessun percorso converte l'uno nell'altro | statica + `G-AP-02` |
| AR-AP-10 | Ogni terminazione non riuscita con almeno uno step `SIDE_EFFECT` espone gli effetti già prodotti | test |
| AR-AP-11 | **Nessun parametro di richiesta allarga l'autorità del chiamante** | statica (lista vietata su OpenAPI) |
| AR-AP-12 | Un endpoint funziona durante un guasto del PDP solo se il PDP non era sul suo percorso | statica |
| AR-AP-13 | Il `tenant_id` è risolto **solo dall'identità**; se presente nella richiesta è `400`, non un override | statica + `NEG-3` |
| AR-AP-14 | Una richiesta HTTP produce **uno** span; i due trace si correlano per `run_id` | `REVIEWED` |
| AR-AP-15 | Un cambiamento al capability set di un agent è classificato e comunicato come **breaking change** | `REVIEWED` (gate `AR-SE-26`) |
| AR-AP-16 | Il tetto primario è la **concorrenza di run per tenant**; l'ammissione precede la creazione della riga | test |
| AR-AP-17 | Nessun endpoint produce una chiamata al CRM fuori dall'esecuzione di un `run` | statica (`G-AP-03`) |
| AR-AP-18 | Nessun modulo fuori da `connectors/odoo/` nomina Odoo, i suoi modelli, i suoi campi o le sue librerie | statica (`G-AP-03`) |
| AR-AP-19 | In `connectors/odoo/tools/*`, `model` e `method` di `call()` sono **letterali**. *È la traduzione di `ADR-049` al confine Odoo: senza, il Tool Layer sarebbe una facciata su `execute_kw`* | statica su AST (`G-AP-03`) |
| AR-AP-20 | L'`OdooFake` implementa la firma di `call()`, non il protocollo sul filo | statica |
| AR-AP-21 | Un circuit breaker aperto verso il CRM produce un errore visibile, **mai** un percorso alternativo o una cache | statica + test |
| AR-AP-22 | Violazione di unicità sull'external ID `__agent__` → **`ALREADY_APPLIED`**, mai fallimento. *L'errore che è un successo* | test (con caso negativo) |
| AR-AP-23 | `AUTHORIZATION_DENIED` e `EXTERNAL_ACCESS_DENIED` sono distinti; nessun percorso li unifica | statica |
| AR-AP-24 | All'avvio ogni campo dichiarato negli schemi dei tool è verificato contro il CRM; un campo mancante **impedisce l'avvio** | test di avvio |
| AR-AP-25 | Un campo `triggers_automation` compare nell'`ActionBinding` con quella marcatura | statica + `REVIEWED` |
| AR-AP-26 | Il reverse proxy non prende **nessuna** decisione di autorizzazione | `REVIEWED` (configurazione) |
| AR-AP-27 | Nessun tool `side_effects ≠ READ` è esponibile dove l'approvazione è raccolta da un sistema che non controlliamo. *MCP inbound spezza la catena di custodia dell'approvazione* | statica (quando MCP inbound esisterà) |
| AR-AP-28 | Ogni parametro di filtro corrisponde a una colonna indicizzata | statica (`G-AP-01`) |
| AR-AP-29 | La route in uno span o in una metrica è sempre **templata** | statica |
| AR-AP-30 | I test `NEG-1`, `NEG-2`, `NEG-3` **non migrano mai** fuori dal percorso che blocca una PR | registro (`ADR-266`) |
| AR-AP-31 | Ogni schema di richiesta/risposta è mappato a una voce del registro `data_asset` | statica (`G-AP-01`) |
| AR-AP-32 | Un campo negato dal `FieldScope` **non compare come chiave**, né come `null` né mascherato | statica + test |

**Debito noto: 26 su 32 con verifica automatica.** Le sei `REVIEWED` (`AR-AP-14`, `-15`, `-25`,
`-26`, e le parti manuali) sono debito al gate di Level A.

---

## 2. Registro dei componenti

| Componente | Piano | Responsabilità | Day-1 | Owner del dato |
|---|---|---|---|---|
| Control Plane API | Control | CRUD versionato di tenant, agent, tool, model, policy, prompt, workflow | Sì | registries |
| Agent Runtime | Execution | esegue i `run`, avanza la state machine, chiama model e tool | Sì | `run`, `step` |
| Policy Enforcement Point (PEP) | Execution | blocca/consente ogni chiamata tool prima dell'esecuzione | Sì | — |
| Policy Decision Point (PDP) | Execution | valuta le policy del Control Plane e restituisce una decisione | Sì | — |
| Tool Runtime | Resource | esegue i Tool, applica validazione schema e idempotenza | Sì | — |
| Model Provider | Resource | astrazione sull'inference server | Sì | — |
| Knowledge / Retrieval | Resource | RAG su pgvector, restituisce frammenti con provenance | Sì | `document`, `chunk` |
| Evidence Store | Evidence | audit append-only, step journal, telemetria | Sì | `audit_event` |
| Retrieval Layer | Resource | canale di `OBSERVE` (**non un tool**, `AR-KN-21`): pre-filtro autoritativo, ricerca ibrida, fusione per rank, provenance | Sì | `document`, `document_version`, `parsed_content`, `chunk`, `embedding`, `entity_link`, `acl_subject`, `grant` |
| Ingestion Pipeline | Resource | polling incrementale + sweep, parsing, chunking, embedding. **Mai sulla GPU** (`AR-KN-16`) | Sì | — |
| Embedding Provider | Resource | `embed()` **su CPU**, processo separato (`ADR-068`) | Sì | — |
| Blob Store | Resource | contenuto content-addressed su filesystem, fuori dal database (`ADR-073`). Non conosce tenant né permessi | Sì | — |
| Memory Module | Execution | modulo **in-process** (`ADR-103`) in `api` e `worker`: risoluzione del `MemorySnapshot`, scrittura autorizzata, supersessione, cancellazione | Sì | `memory`, `memory_audit`, `run_summary`, `conversation` |
| Context Assembler | Execution | monta il prompt nell'ordine di `AR-ME-15` e applica l'ordine di cessione di `AR-ME-14` quando il budget si stringe | Sì | — |
| Working Set Renderer | Execution | `render_working_set()`: **funzione pura, in codice, mai il modello** (`ADR-090`, `AR-ME-11`) | Sì | — |

> **Risorsa aggiunta da `A06`: `ToolBinding`** — completa il pattern `X`/`XVersion`/`Binding`
> di `ADR-015`, che `A02` aveva istanziato per gli agent ma non per i tool. Serve per
> environment e tenant. Il modello risorse passa da 12 a 13.

---

## 3. Registro delle interfacce

| Interfaccia | Provider | Consumer | Protocollo | Auth | Stato |
|---|---|---|---|---|---|
| `POST /v1/runs` | Agent Runtime | Application / CRM | REST + OpenAPI 3.1 | OIDC | Day-1 |
| `GET /v1/runs/{id}` | Agent Runtime | Application | REST | OIDC | Day-1 |
| `ModelProvider.complete()` | Model Provider | Agent Runtime | in-process → HTTP OpenAI-compatible | secret interno | Day-1 |
| `ToolRuntime.invoke()` | Tool Runtime | Agent Runtime (via PEP) | in-process | contesto del run | Day-1 |
| `PDP.decide()` | PDP | PEP | in-process | — | Day-1 |
| `RetrievalLayer.retrieve(RetrievalQuery, RetrievalScope) → RetrievalResult` | Retrieval Layer | Agent Runtime (in `OBSERVE`) | in-process | `RetrievalScope` prodotta dal PDP | Day-1 |
| `Retriever.search()` | pgvector / ricerca lessicale | Retrieval Layer | in-process | — | Day-1 (**due implementazioni reali → `AR-020`**) |
| `EmbeddingProvider.embed()` | Embedding Provider | Ingestion + Retrieval Layer | in-process → HTTP su loopback, **CPU** | secret interno | Day-1 |
| `BlobStore.put/get(content_hash)` | Blob Store | Ingestion, Retrieval Layer | in-process | — | Day-1 |
| `DocumentSource.list_changes/fetch` | connector documentale | Ingestion Pipeline | in-process | credenziale del connector | Day-1 |
| `MemoryScope` | PDP | Memory Module | in-process | prodotta dal PDP, come `RetrievalScope` | Day-1 |
| `MemorySnapshot` | Memory Module | Agent Runtime | in-process | **congelato all'avvio del run** (`ADR-092`), sta nella zona cacheabile del prompt | Day-1 |
| `render_working_set() → WorkingSetBlock` | Working Set Renderer | Context Assembler | in-process (**funzione pura**) | — | Day-1 |
| tool `memory_write` (`MemoryCandidate → CommittedMemory`) | Memory Module | modello, via Tool Runtime | in-process | args di scope **iniettati** (`AR-ME-03`) | Day-1 |
| 8 endpoint REST di memoria (ispezione, correzione, cancellazione, explanation) | Control Plane API | UI / admin | HTTP | — | Day-1 |
| annotazione `x-entity-ref` nello schema dei tool | registro dei tool | Working Set Renderer | — | marca gli identificatori che il ledger deve conservare (`INV-10`) | Day-1 |
| Control Plane CRUD | Control Plane | Admin Console / CLI | REST | OIDC + ruolo admin | Day-1 |

---

## 4. Invarianti architetturali

Regole che devono restare vere finché non vengono esplicitamente cambiate.

| ID | Invariante |
|---|---|
| INV-01 | Nessun `Tool` con side effect viene eseguito senza una decisione del PDP registrata nello step journal |
| INV-02 | Ogni riga di ogni tabella applicativa ha un `tenant_id`; nessuna query applicativa lo omette |
| INV-03 | Il modello non è un enforcement point: la sua uscita è input non fidato |
| INV-04 | L'insieme di capability di un run non cresce dopo l'avvio del run |
| INV-05 | L'audit è append-only e non condivide tabella con lo stato mutabile |
| INV-06 | Ogni operazione con side effect ha un `idempotency_key` derivato deterministicamente da `(run_id, step_index)` |
| INV-07 | Nessun componente accede al database CRM se non attraverso un `Tool` con schema dichiarato. **Esteso da `A07`:** non solo "nessun accesso", ma **nessuna copia** — l'indice contiene identificatori, mai campi di dominio (`AR-KN-06`). Vieta anche il CDC |
| INV-08 | Un frammento recuperato, **una memoria o un `AgentResult`** è dato, mai istruzione: `trust_class = retrieved` (`AR-KN-03`, `AR-ME-06`, `AR-AC-12`). *Esteso da `A08` e `A10`* |
| INV-09 | Il filtro di autorizzazione del retrieval sta **nella query**; gli strati successivi possono solo togliere (`ADR-071`) |
| **INV-10** | Per ogni run e ogni step, gli identificatori nel `WorkingSetBlock` sono un **soprainsieme** degli identificatori marcati `x-entity-ref` in tutti i `ToolResult` registrati fino a quel punto. **Non dipende dal budget.** È ciò che tiene in piedi `AR-TL-06` sotto compattazione |
| **INV-11** | L'insieme delle memorie leggibili in un run è determinato prima della prima chiamata al modello e **non cresce** durante il run. *Esteso da `A10`*: vale per **qualunque run di un albero**, determinato prima della prima chiamata al modello della **radice** |
| **INV-12** | Nessuna funzione del PDP, del PIP o del PEP legge la tabella `memory`. Verificato staticamente. È la difesa **strutturale** contro il memory poisoning: una memoria avvelenata non può cambiare i permessi |
| **INV-13** | Per ogni run e ogni istante successivo all'avvio, l'insieme delle azioni autorizzabili è un **sottoinsieme** di quello all'avvio. Nessun evento può **aggiungere** un'azione autorizzabile a un run già avviato. *Generalizza `INV-04` e `INV-11` a tutta l'autorità* |
| **INV-14** | Nessun `SecretMaterial` esiste fuori dal modulo di autenticazione e dal `Credential Broker`. Nessun tool, connector, riga di audit o log ne contiene uno. *Rende `AR-TL-13` verificabile staticamente* |
| **INV-15** | Ogni decisione di autorizzazione registrata contiene **entrambe** le identità (`actor` e `on_behalf_of`). *Rende `AR-GP-05` strutturale invece che procedurale* |
| **INV-16** | Per ogni **albero** di run, l'**unione** delle azioni autorizzabili di tutti i run dell'albero, in ogni istante, è un **sottoinsieme** delle azioni autorizzabili della radice al suo avvio. *Generalizza `INV-13` dall'esecuzione all'albero* |
| **INV-17** | `on_behalf_of` è **invariante** lungo tutto l'albero: ogni discendente porta lo stesso `on_behalf_of` della radice. **Nessun run ha come `on_behalf_of` un `AgentRun`** |
| **INV-18** | Il tetto di step e la deadline di `ADR-104` sono proprietà dell'**albero**. Nessun run figlio possiede un budget o una deadline propri: li referenzia |
| **INV-19** | Nessuna funzione del PDP, del PIP o del PEP legge campi provenienti da un `AgentTask` o da un `AgentResult`. Verificato staticamente. *Difesa strutturale contro l'escalation via messaggio, nella stessa forma di `INV-12`* |
| **INV-20** | Per ogni albero, `run_tree.steps_consumed` è **esattamente** il numero di righe `run_step` dei run dell'albero. Nessuno step senza consumo, nessun consumo senza step. *È la forma falsificabile di `INV-18` e la difesa misurabile contro `R-50`* |
| **INV-21** | Per ogni step con `side_effects ≠ READ`, **prima che un solo byte parta** verso un sistema esterno, esiste una riga committata con `state ∈ {PENDING, IN_FLIGHT}` che porta la sua `idempotency_key` e il `decision_id`. *Rende `ADR-029` sufficiente al recovery, non solo alla rilevabilità* |
| **INV-22** | In ogni istante, al più un worker possiede un lease valido su una unità di lavoro; `lease_epoch` è monotono crescente, e ogni scrittura di un worker è condizionata al proprio epoch. *Rende `AR-RT-08` strutturale invece che sperata* |
| **INV-23** | Ogni run in stato non terminale ha, in ogni istante, almeno una fra: un lease valido, un `wakeup_at`, un'attesa esplicita registrata. **Nessun run può essere perso** |
| **INV-24** | Per ogni consumatore di background, l'assenza di progresso oltre la `max_staleness` dichiarata produce un **evento di errore**. Nessun componente può fallire senza che qualcuno se ne accorga entro una finestra dichiarata. *È la forma generale della difesa contro i guasti silenziosi, di cui `R-63` era un'istanza* |
| **INV-25** | Nessuna funzione del PDP, del PIP o del PEP legge `trace_id`, `span_id`, `traceparent`, `tracestate` o qualunque campo di telemetria. *Rende `AR-ID-02` strutturale, nella forma di `INV-12` e `INV-19`* |
| **INV-26** | Nessun record di telemetria contiene testo di dominio, prompt, risposta del modello, `value_text`, contenuto di documento, argomento di tool, valore di campo del CRM o materiale crittografico. **Solo identificatori, hash, enum, numeri, timestamp e nomi di campo.** Verificato da allowlist in CI |
| **INV-27** | Nessun controllo di sistema — autorizzazione, budget, retry, recovery, cancellazione, rilevamento di loop — dipende da una lettura di telemetria. **È il confine audit/telemetria reso strutturale** |
| **INV-28** | Ogni lettura di telemetria avviene sotto un `tenant_id` risolto dall'identità autenticata; unica eccezione il `PlatformOperator`, su una vista **senza dimensioni di dominio** e auditato |
| **INV-29** | L'oggetto di ogni approvazione registrata è un `ActionBinding` tipizzato. **Nessun testo generato dal modello è mai l'oggetto di un'approvazione.** Verificato dal tipo |
| **INV-30** | Nessun percorso di calcolo di un'anteprima può raggiungere un tool con `side_effects ≠ READ`. Verificato staticamente |
| **INV-31** | Nessun percorso di contenimento (`KillSwitch`, revoca, cancellazione) bypassa il PDP. **Non esistono percorsi privilegiati di emergenza** |
| **INV-32** | Nessuna scrittura verso un sistema esterno avviene senza un'approvazione umana registrata su un `ActionBinding` confermato. **Vale per ogni entità e per ogni verbo di modifica**, senza eccezioni configurabili |
| **INV-33** | Non esiste alcun percorso di codice che invochi una **cancellazione fisica** su un sistema esterno. L'unica forma di rimozione disponibile all'agent è l'archiviazione |
| **INV-34** | Per ogni scrittura su un campo esistente, il **valore precedente** è registrato nel journal **prima** della scrittura. *È ciò che rende `R-79` ricostruibile e l'`UPDATE` reversibile, dato che Odoo non conserva i valori precedenti* |
| **INV-35** | Per ogni fatto registrato in entrambi i piani, il record di telemetria **non sopravvive** al record di audit corrispondente. `retention(telemetry) < retention(audit)`, per ogni classe. *È il confine audit/telemetria di `INV-27` esteso alla dimensione temporale* |
| **INV-36** | Per ogni arco `sorgente → derivato` del registro `data_asset`, **entrambe** le classi del derivato sono ≥ di quelle della sorgente. *Rende strutturale "il derivato non sfugge alla governance della sorgente"* |
| **INV-37** | Nessuna riga di audit è rimossa fisicamente se non attraverso `audit_redaction`; per ogni rimozione esiste **esattamente una** riga firmata in quel registro. *Non conserva l'integrità: conserva la conoscenza della sua perdita* |
| **INV-38** | Dopo il completamento di una `erasure_request`, **nessuna riga della piattaforma** permette di risolvere quel `subject_id` in un identificatore diretto della persona. *È la forma falsificabile di `ADR-236`* |
| **INV-39** | Nessun campo dichiarato `SPECIAL_CATEGORY` compare in un `ToolInvocation`, in un `ToolResult`, nel context, nel journal o nell'audit. *Rende `ADR-230` verificabile* |
| **INV-40** | Nessun testo libero prodotto in produzione compare in un file di dataset di evaluation. *Rende `AR-OB-24` un meccanismo invece che un'intenzione* |
| **INV-41** | Nessun percorso di codice eseguito sotto test può aprire una connessione verso un endpoint non dichiarato nell'allowlist di test. *Rende `AR-TL-16` strutturale invece che scritta* — verifica: rete + tipo (`ADR-264`) |
| **INV-42** | Per ogni voce del registro marcata `BLOCCANTE` esiste un **caso negativo provato**: un test che dimostra che il gate fallisce quando il controllo che dovrebbe proteggere viene rimosso. *È la difesa contro il gate verde per costruzione* — verifica: `ADR-266` n. 3 |
| **INV-43** | Nessun file di fixture o di dataset contiene un identificatore di record appartenente a un tenant reale. *Estende `INV-40` dal testo libero agli identificatori, e dai dataset di evaluation alle fixture* — verifica: statica + review |
| **INV-44** | Ogni mandato di test estratto dai documenti architetturali risolve a una voce del registro, e ogni voce del registro risolve a un test eseguibile. *Rende «il conto è pagato» una query invece che un'affermazione* — verifica: `ADR-266` n. 1 e n. 2 |
| **INV-45** | Nessun esito positivo di autorizzazione esiste senza una decisione del PDP registrata: **nessun `default allow`, nessuna cache usata a PDP guasto, nessun flag di bypass, nessuna modalità manutenzione**. *Rende `AS-29` (fail-closed) strutturale sulla superficie esterna* — verifica: statica + `G-AP-02` |
| **INV-46** | Il contatore `external_calls_consumed` è **esattamente** uguale al numero di chiamate uscite da `connectors/`. *Forma di `INV-20` applicata al budget verso il CRM: un budget che si può aggirare non è un budget* — verifica: statica + test |
| **INV-47** | Nessun testo di errore proveniente da un sistema esterno viene persistito, loggato o restituito. *Forma di `INV-26`: i messaggi di errore di Odoo contengono nomi di campo, valori e talvolta dato di dominio* — verifica: statica |

---

## 5. Registro dei conflitti

| ID | Componente A | Componente B | Conflitto | Stato |
|---|---|---|---|---|
| — | — | — | nessun conflitto registrato finora | — |

---

## 6. Registro delle assunzioni

| ID | Assunzione | Fonte | Confidenza | Impatto se falsa | Validazione |
|---|---|---|---|---|---|
| AS-01 | Il carico Day-1 è nell'ordine di decine di run concorrenti, non migliaia | inferenza da vincoli hardware (1 GPU) | Media | se falsa, la queue su Postgres va sostituita prima del previsto | benchmark di concurrency all'MVP |
| AS-02 | Qwen3.5-9B Q4 sta in 20-24 GB VRAM con context ragionevole e concurrency utile | `research/04`, `research-log` R-08 | Alta | se falsa, serve GPU più grande o modello più piccolo | misura su hardware reale |
| AS-03 | pgvector regge il volume di knowledge Day-1 senza vector DB dedicato | `research/02`, `research/04` | Media | se falsa, serve un vector store separato | backlog ricerca B-05 + benchmark |
| AS-04 | Il team è piccolo (1-3 persone) e non ha SRE dedicato | prompt A01 §2 | Alta | se falsa, si potevano permettere Temporal/K8s Day-1 | conferma dal committente |
| AS-05 | I tenant Day-1 sono pochi e fidati (pilot), quindi isolamento logico basta | inferenza dal contesto pilot | Media | se falsa, serve isolamento fisico prima | decisione commerciale |
| AS-06 | L'inference gira sulla stessa macchina fidata → un secret condiviso basta | A05 | Alta | se falsa, serve mTLS | `A09` |
| AS-07 | Il carico è prefill-bound | A05 | Media | cambia il dimensionamento | misura `M2` |
| **AS-08** | **Un solo modello sulla GPU** | A05 | **CONFERMATA da `A07`** (`ADR-068`: embedding su CPU, nessun reranker Day-1 per `ADR-069`) | il bilancio VRAM di `A05` resta valido; `ADR-039` **non cambia nel numero**, cambia la sua ripartizione interna, dichiarata come vincolo verificato al `resolve()` | resta subordinata a `B-26`: se l'embedding su CPU non regge la latenza, `ADR-068` cade e `AS-08` si riapre |
| AS-13 | La maggior parte delle domande utili si serve con documenti + dato live, non con conoscenza aggregata sul corpus | A07 | Media | servirebbe qualcosa tipo GraphRAG | osservare i run reali |
| **AS-14** | **Un modello di embedding piccolo su CPU regge il carico di query Day-1** | A07 | **Bassa** | **`ADR-068` cade, e con esso `AS-08`** | **`B-26`: una misura, prima di tutto il resto** |
| AS-15 | Le ACL delle sorgenti documentali sono proiettabili in una tabella di `grant` | A07 | Media | `ADR-072` non è implementabile per quella sorgente → la sorgente resta fuori | `B-35`, dipende da `Q-01` |
| **AS-16** | **Il volume Day-1 sta nell'ordine ~10⁴–10⁵ chunk** | A07 | **Bassa** | cambia il dimensionamento dell'intero percorso documentale | **chiudere `Q-04`** |
| AS-17 | Le sorgenti documentali espongono un modo di elencare le modifiche dopo un cursore | A07 | Media | serve un full sweep a ogni giro per quella sorgente | verifica per connector |
| **AS-18** | **Le memorie utili per soggetto sono nell'ordine delle decine**, non delle migliaia | A08 | **Bassa** | il cap di 32 è sbagliato, `ADR-099` cade, serve retrieval sulla memoria | `memory_active_count`, primo trimestre |
| AS-19 | Una preferenza di interazione utile sta in **280 caratteri** | A08 | Media | `AR-ME-10` va allentata, il budget della memoria va rifatto | tasso di `memory_write` rifiutati per lunghezza |
| ~~AS-20~~ | ~~Il journal di un run tipico è nell'ordine delle decine di step~~ → **NON È PIÙ UN'ASSUNZIONE**: `ADR-104` la trasforma in un **limite imposto** (`max_steps = 50`). Il committente ha dichiarato che nessun task CRM supera i 50 step o i 10 minuti attivi, e che ~90 % dei casi è una singola chiamata a tool (3-5 step) | A08 → thread | **risolta** | — | il tetto la rende vera per costruzione |
| **AS-21** | **Gli utenti dichiarano le preferenze esplicitamente, se il sistema glielo permette** | A08 | **Bassa** — condizione di prodotto, non tecnica | la memoria resta vuota: `ADR-094` va riaperto **o la funzione va tolta** | `memory_confirmation_rate` |
| AS-22 | Il tempo di `render_working_set()` è trascurabile rispetto alla latenza di una chiamata al modello | A08 | Media | gira a ogni step: diventerebbe un costo fisso significativo | misura `M-ME-2` |
| AS-23 | Gli utenti Day-1 sono interni e pochi: l'autenticazione locale basta | A09 | Media → **precisata**: il committente ha escluso OAuth e indicato **LDAP** come massimo (`ADR-121`). Non serve OIDC, serve un bind LDAP | `ADR-109` regge Day-1, ma la superficie deve accogliere LDAP prima di OIDC | conferma del committente, 2026-08-23 |
| AS-24 | Il CRM target offre un identificatore utente stabile e non riusato su cui costruire `acl_subject` | A09 | **Alta** (era Bassa) — **`B-49` chiusa**: `res_users.id` è un `SERIAL` PostgreSQL, le sequence sono monotone, gli ID non tornano indietro (`R-10`) | resta un residuo: `setval()` manuale, e utenti **archiviati** invece che cancellati | **verificata**. `ADR-122` copre il residuo col discriminante |
| AS-25 | La finestra di approvazione umana sta dentro una sessione di lavoro | A09 | Media | `ADR-112` non regge: i run che aspettano approvazioni lunghe falliscono sempre | `T-ID-03`, tasso di `DELEGATION_EXPIRED` |
| AS-26 | Le persone per tenant sono nell'ordine delle decine Day-1 | A09 | Media | SCIM serve prima; la gestione manuale non regge | conteggio reale |
| AS-27 | Gli attributi di identità sono caricabili a ogni step senza sfondare il budget di latenza | A09 | Media | `ADR-106` va rivista: si tornerebbe verso il congelamento con finestra breve | **`T-GP-01`**, misura di `A12` |
| **AS-28** | **`AS-12` (tutti i tool sono nostri) regge abbastanza a lungo** da non dover isolare i segreti in un processo separato Day-1 | A09 | **Bassa** | il `Credential Broker` in-process espone i segreti a codice di terzi | `T-TL-03` — *il primo tool non nostro* |
| ~~AS-29~~ | ~~Il committente accetta che in un guasto del PDP il sistema si fermi~~ → **NON È PIÙ UN'ASSUNZIONE: CONFERMATA dal committente il 2026-08-23.** *Se il PDP si guasta, il sistema si ferma.* | A09 → thread | **risolta** | — | il fail-closed di `A13` §22 e `AR-SE-16` poggiano ora su una decisione dichiarata, non su un'ipotesi |
| AS-30 | Nessun caso d'uso CRM Day-1 richiede **due contesti di ragionamento indipendenti e simultanei** | A10 | Media | `ADR-123` cade e serve concorrenza vera → **riapre `AS-08`** | osservare i run reali; `T-AC-05` |
| AS-31a | **Il multi-agent non offre un guadagno di qualità che il single-agent non possa ottenere a parità di token** | A10 → **verificata da `R-11`** | **Alta** | — | **`B-58` chiusa**: evidenza convergente da 5 fonti primarie, inclusi due studi controllati a budget appaiato |
| **AS-31b** | **La struttura che manca al nostro ~9B si recupera con literal intermedi e schemi migliori, senza decomporre in agent** | A10 + `R-11.2` | **Media** (era Bassa e indistinta) | resta solo la scala dei rimedi; ma il rimedio giusto è **più struttura**, non più agent | **`B-66`: una misura sul nostro hardware** |
| **AS-31c** | **Il nostro context non è così affollato da degradare l'utilizzo effettivo** al punto in cui la letteratura dice che il multi-agent torna competitivo | `R-11.2` (condizione di confine di Tran & Kiela) | **Bassa — è il contro-segnale più serio** | il regime in cui il multi-agent recupera è **esattamente** il nostro: `ADR-091` mette tool definition, frammenti e digest in competizione | `context_utilization` e `fragment_eviction_rate` (`A12`); `T-ME-02` |
| **AS-32** | **Il committente non ha requisiti di interoperabilità con agent di altre organizzazioni** prima della fase 3 | A10 | **Bassa** — condizione di prodotto, non tecnica | l'A2A adapter diventa Day-1, con tutte le domande aperte ancora tali | **conferma esplicita del committente** |
| AS-33 | Se il multi-agent arriverà, arriverà **in-process sulla stessa macchina** prima che remoto | A10 | Media | l'attenuazione dovrebbe attraversare una rete subito: `ADR-113` andrebbe riaperta (`T-ID-02`) | `Q-03` |
| AS-34 | L'intervallo di polling che ci possiamo permettere è compatibile con l'esperienza interattiva attesa | A11 | Media | serve `LISTEN`/`NOTIFY` o una coda vera prima del previsto | `T-EV-01`, `B-68` |
| **AS-35a** | **Le scritture di creazione verso Odoo sono rese idempotenti e verificabili dall'external ID con vincolo UNIQUE di PostgreSQL** | A11 → **verificata da `R-12`** | **Alta** (era Bassa e indistinta) | — | **`B-69` chiusa per le creazioni.** L'idempotenza non è una concessione di Odoo: **la costruiamo noi** (`ADR-161`). Il caso ambiguo di `ADR-144` diventa una `SELECT` su indice unico |
| **AS-35b** | **L'idempotenza delle transizioni di stato del dominio (confermare un ordine, validare una fattura) è dichiarabile tool per tool** | A11 + `R-12.3` | **Media** | i soli step di transizione di stato producono `UNCERTAIN` dopo un crash; le creazioni no | `AR-RT-04` la impone come dichiarazione per tool; `T-EV-03` la misura. **Residuo dichiarato, molto più stretto di prima** |
| AS-35c | Il connector crea record e riga `ir.model.data` **nella stessa transazione Odoo** (via `load()`), mai con due chiamate RPC separate | `R-12.3` | **Alta** — è un **vincolo sul nostro codice** (`AR-EV-32`), non un'ipotesi su Odoo | l'atomicità salta e il caso ambiguo torna | test di integrazione sul connector |
| AS-36 | Un crash del worker è raro (giorni/settimane), quindi la finestra di tempo attivo non contabilizzato è irrilevante | A11 | Media | `R-60` diventa reale: i tetti temporali non tengono | misura |
| AS-37 | Il volume di job di background Day-1 sta in una coda condivisa con i run senza affamarli | A11 | Media | servono code o pool separati prima del previsto | metrica per `worker_class` |
| AS-38 | Il volume di telemetria Day-1 sta in PostgreSQL senza degradare il percorso di esecuzione | A12 | Media | `ADR-166` cade, serve un backend dedicato prima del previsto | **`B-76`, `B-80`** |
| **AS-39** | **Utenti e committente segnalano i difetti di esito abbastanza spesso da alimentare il failure corpus** | A12 | **Bassa** | il ciclo di miglioramento gira a vuoto: i difetti esistono e non arrivano | tasso di segnalazioni nel primo trimestre |
| AS-40 | Le post-condizioni deterministiche coprono la **maggior parte** dei compiti CRM | A12 | Media | `ADR-177` non basta: servirebbe giudizio umano su molti più casi di quanti un team di 1-3 persone possa gestire | i primi 20 `EvaluationCase`: quanti hanno post-condizioni verificabili? |
| **AS-41** | **Esiste una rete in uscita per il dead man's switch esterno** | A12 | **Bassa** — dipende da `Q-03` | l'ultimo anello si perde, e il regresso "chi guarda il guardiano" resta aperto | **`B-82`**; conferma sul modello di deployment |
| **AS-42** | **Il team ha la disciplina di scrivere un `EvaluationCase` per ogni incidente** | A12 | **Bassa** — condizione sociale, non tecnica | `ADR-185` diventa una regola che nessuno applica → **`R-70`** | osservazione dopo il primo trimestre |
| AS-43 | `render_working_set()` cambia raramente, e le versioni precedenti restano eseguibili | A12 | Media | la ricostruzione retrospettiva si degrada; `HASH_MISMATCH` diventa il caso normale | conteggio dei cambi al renderer nel primo trimestre |
| **AS-44** | **L'attrito differenziato riduce davvero l'approvazione riflessa** | A13 | **Bassa** — raccomandato dalla letteratura, non verificato su studio primario | `ADR-191` è teatro di sicurezza: costo senza beneficio | **`B-87`** + red teaming con persone (`ADR-215`) |
| AS-45 | Il volume di approvazioni Day-1 sta sotto la soglia oltre cui l'attrito è insostenibile | A13 | Media | `ADR-023` viene rimosso per pressione operativa, e con esso metà delle mitigazioni | `M-OB-01` e il tetto di `ADR-194` nel primo trimestre |
| AS-46 | La quarantena ha un tasso di falsi positivi gestibile da una persona | A13 | Bassa | `ADR-197` diventa collo di bottiglia o viene disattivata | misura nel primo trimestre |
| **AS-47** | **L'avversario vuole rubare dati o compiere azioni, non corrompere lentamente il dato** | A13 | **Bassa** | ~~non abbiamo alcuna difesa~~ → **attenuato il 2026-08-23 da `ADR-221`**: il valore precedente nel journal rende la corruzione **ricostruibile** | **`B-88`** |
| AS-48 | La superficie CRM scrivibile Day-1 (`ADR-217`) copre i casi d'uso utili | thread | Media | il capability floor viene allargato subito, e `R-81` si realizza | osservare `missing_capability_rate` nel primo trimestre |
| AS-49 | Il cliente sa dichiarare le proprie coppie di funzioni in conflitto SoD | thread | **Bassa** — è conoscenza di processo, non tecnica | `ADR-226` resta un motore vuoto (`R-84`) | partire da un baseline standard, `B-93` |
| **AS-50** | A14 | Il deployment Day-1 è in UE e la macchina è sotto il controllo del committente | **Bassa** — dipende da `Q-03` | residency e sovereignty vanno riprogettate, §37 | **`Q-03`** |
| **AS-51** | A14 | Nessun tenant Day-1 tratta categorie particolari nei campi che i nostri tool leggono | **Bassa** | `INV-39` non basta e serve una base giuridica ex art. 9(2) | **`B-103`** + revisione degli schemi |
| **AS-52** | A14 | Le richieste di data subject Day-1 sono poche unità l'anno: un processo semi-manuale basta | Media | serve automazione completa e verifica dell'identità del richiedente | conteggio nel primo anno; `T-DG-02` |
| **AS-53** | A14 | I documenti indicizzati Day-1 vengono da sorgenti aziendali dichiarate, non da caselle di posta personali | Media | `AR-DG-26` non basta; `ADR-085` va difeso | verifica per connector |
| **AS-54** | A14 | Il committente accetta che la cancellazione dai backup avvenga per scadenza, non su richiesta | **Bassa** — è contrattuale, non tecnica | serve il crypto-shredding, quindi `ADR-239` reale, quindi `T-DG-01` anticipato | **conferma esplicita del committente** |
| **AS-55** | A14 | Nessun caso d'uso Day-1 rientra nell'Allegato III dell'AI Act | Media (il `FATTO` di `R-14.1` la supporta) | classificazione ad alto rischio, obblighi del capo III | `T-DG-03` + `Q-01` |
| **AS-56** | A17 | L'`OdooFake` riproduce fedelmente gli otto comportamenti di `ADR-262`, e quegli otto sono quelli che contano | **Media** | `R-98` si realizza: i test passano su una finzione | il contract test notturno, `T-QA-02` |
| **AS-57** | A17 | La variabilità del modello su un `EvaluationCase` è stabile abbastanza da calibrare `k` una volta e riusarlo per un trimestre | **Bassa** | `k` va ricalibrato di continuo e la eval suite diventa impraticabile | la misura del passo 2 di §9.2 (`A17`) |
| **AS-58** | A17 | Il team tiene la CI sotto la soglia ergonomica senza spostare gate fuori dal percorso che bloccano | **Media** — è una condizione **sociale** | `R-97`: i gate migrano nightly e smettono di bloccare le PR | `T-QA-01` |
| **AS-59** | A17 | Un dataset CRM sintetico basta per i gate deterministici | **Media** | `R-100`: i difetti che stanno nello sporco non vengono trovati | il livello `hostile` di `ADR-263` |
| **AS-60** | A17 | Il red teaming con soggetti umani (`ADR-215`) è organizzabile con le risorse del committente, e i soggetti **non** sono chi ha costruito l'interfaccia | **Bassa** — condizione **organizzativa** | `ADR-215` resta un requisito non soddisfatto e `AS-44` (l'attrito funziona) resta non verificata | conferma esplicita del committente |
| **AS-61** | A17 | Le post-condizioni si esprimono come query sull'Odoo di test e sul nostro PostgreSQL, senza bisogno di giudizio | **Alta** per i casi `D`, **subordinata ad `AS-40`** | vedi il protocollo `AS-40` | il protocollo di §8.2 (`A17`) |
| **AS-62** | A17 | I moduli soggetti a invarianti statici sono scrivibili senza accesso dinamico agli attributi, quindi l'analisi statica è completa su di loro | **Media** | gli invarianti statici hanno buchi silenziosi, **e sono il 55 % della copertura** | verifica alla prima implementazione del PDP |
| **AS-63** | A18 | L'unico consumatore dell'API Day-1 è l'interfaccia utente, che gira sulla stessa macchina | **Media** | `ADR-289` (PostgreSQL come trasporto interno) e `ADR-291` vanno rivisti | `T-AP-09` |
| **AS-64** | A18 | Il committente accetta che **tutto** sia asincrono, cioè che nessuna operazione risponda "fatto" nella stessa richiesta HTTP | **Media** | `ADR-285` va rinegoziato, e con esso la forma dell'intera API | conferma esplicita del committente |
| **AS-65** | A18 | Il costo del rate limiting implementato su PostgreSQL è trascurabile alle nostre scale | **Bassa — non misurata** | `R-116`: il meccanismo che protegge diventa il collo di bottiglia | `T-AP-10`, ricerca `B-119` |
| **AS-66** | A18 | La firma `call(model, method, args, kwargs, ctx)` sopravvive a qualunque successore delle API RPC di Odoo | **Bassa — è un'ipotesi su una specifica non vista** | `R-109`: non basta riscrivere `transport.py`, cambia la forma di tutti i tool | `T-AP-01`, ricerca `B-118` |
| **AS-67** | A18 | Nessun secondo connector viene richiesto prima che `Q-01` risponda | **Media** | `AR-020` costringerebbe a costruire l'astrazione senza averne pagato il prezzo di conoscenza | `T-AP-06` |

---

## 7. Registro dei rischi

| ID | Rischio | Classe | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|---|
| R-01 | Prompt injection via dati CRM/email che porta a side effect non autorizzati | Security | Alta | Alto | `trust_class` + capability binding + approval sui side effect |
| R-02 | Un task pesante satura la GPU e blocca le interazioni umane | Reliability | Alta | Medio | separazione priority interactive/background già Day-1 (logica) |
| R-03 | Il modello 9B sbaglia tool o argomenti troppo spesso | Quality | Media | Alto | structured output + validazione schema + dataset di errori → QLoRA |
| R-04 | PostgreSQL usato per tutto (state + queue + vector + audit) diventa il collo di bottiglia | Scalability | Media | Medio | metriche di saturazione definite Day-1, percorso di split già identificato |
| R-05 | Lock-in accidentale su Qwen tramite prompt e formati specifici | Vendor | Media | Medio | `ModelProvider` + eval suite indipendente dal modello |
| R-06b | **Il codice di recovery è il rischio più concreto dell'architettura**: produce danni silenziosi | Reliability | Media | Alto | test che uccidono il worker a metà run, in CI; trigger severo `T-RT-06` |
| R-12 | Non-determinismo dell'inference sotto continuous batching | Reliability | Alta | Medio | `ADR-042`: si promette l'evidenza, non l'output. **`C29` (replay) va ridefinito** |
| R-13 | Un upgrade del serving rompe tool calling o structured output in modo **silenzioso** | Reliability | Media | Alto | FATTO dalla doc vLLM: va testata la combinazione esatta checkpoint × quantizzazione × tokenizer × parser → gate in `A16` |
| R-14 | GPU singolo punto di guasto non ridondato | Reliability | Media | Alto | accettato Day-1 (`D-05`); degrado a sola lettura |
| R-15 | La quantizzazione degrada il **tool calling** più della qualità percepita del testo | Quality | Media | Alto | gate agentico di `ADR-037`: si misura la selezione dei tool, non la fluidità |
| R-16 | Il lock-in si accumula per iterazione di prompt engineering, **invisibile nel codice** | Vendor | Alta | Medio | metrica `portability_delta` (`A12`), trigger `T-MD-08` |
| R-17 | Composizione di azioni lecite (`export` + `send` = esfiltrazione) | Security | Media | **Alto** | **non risolto**: compensato dall'approvazione umana. Ricerca `B-11`; sede naturale della soluzione = lo step journal |
| R-18 | Il costo di scrivere un tool produce **scorciatoie** (tool troppo generici, per fare prima) | Maintainability | **Alta** | Alto | scaffolding di un tool Day-1: senza, il rischio si realizza |
| R-19 | Tool definition di terzi finiscono nel prefisso con fiducia `tool_spec` | Security | Media | Alto | `AR-TL-11`: materializzazione umana obbligatoria (`ADR-063`) |
| R-20 | Gli schemi sono progettati su inferenze non validate su un 9B reale | Quality | **Alta** | Medio | `schema_failure_rate` **per campo**; schema usability test in `A17` |
| R-21 | Gap fra definizione (immutabile) e implementazione (no) | Correctness | Media | Alto | `build_id` registrato + verifica all'avvio del worker (`ADR-051`) |
| R-22 | L'isolamento in-process viene superato senza una decisione esplicita | Security | Media | Alto | `T-TL-03`: il primo tool non nostro è il trigger |
| R-23 | La granularità fine si rivela troppo rigida per il lavoro reale | Usability | Media | Medio | `missing_capability_rate` + `T-TL-06`, progettati apposta per falsificare `ADR-048`/`ADR-049` |
| R-24 | Proiezione ACL obsoleta → accesso non autorizzato attraverso l'indice | Security | Media | **Alto** | `ADR-072` + fail closed (`AR-KN-09`) + allarme prima della soglia |
| R-25 | Il pre-filtro selettivo degrada il recall dell'indice ANN **in silenzio** | Quality | **Alta** | Medio | `underfill_rate` + over-fetch + ripiego su scansione esatta; ricerca `B-29` |
| R-26 | Documento avvelenato → goal hijack (`ASI01`) | Security | Media | **Alto** | **non risolto strutturalmente**: quarantena + capability congelate + `ADR-023`. Eredita i punti ciechi di `B-01` |
| R-27 | L'embedding è dato sensibile (attacchi di inversione) | Security | Bassa | Medio | `AR-KN-18`; ricerca `B-32` |
| R-28 | Side channel temporale sul prefix cache fra tenant | Security | Bassa | Basso | disposizione del prompt di `A07` §17.2; ricerca `B-33` |
| R-29 | L'ingestion su CPU non sta dietro al volume → knowledge base cronicamente in ritardo | Scalability | Media | Alto | `ingestion_lag` + `T-KN-02`; dipende da `Q-04` |
| R-30 | **Il golden set non viene mai costruito** → `T-03` non scatta mai e `ADR-003` non è falsificabile | Process | **Alta** | Medio | `AR-KN-20` + requisito Day-1 esplicito |
| R-31 | Parsing silenziosamente povero (PDF a colonne, tabelle) → frammenti **plausibili e inutili** | Quality | **Alta** | Medio | `boundary_quality`, `parse_state = PARTIAL`, `forced_boundary_rate`; ricerca `B-30` |
| R-32 | La granularità di autorizzazione è il documento, non il campo: `AR-GP-17` è coperta solo in parte sul percorso documentale | Security | Media | Medio | dichiarata, rinviata ad `A14`; ricerca `B-32` |
| **R-33** | **Memory poisoning persistente**: un'iniezione che sopravvive al run e si ripresenta a ogni run successivo. Peggioramento di `R-26` | Security | Media | **Alto** | `ADR-094` (`GENERATED` non entra) + `ADR-097` (`trust_class` bassa) + **`INV-12`** (nessuna autorità). Difesa di configurazione **+** difesa strutturale |
| R-34 | Fuga cross-user o cross-tenant per una memoria scritta con lo scope sbagliato | Security | Bassa | **Alto** | `AR-ME-03` (args iniettati) + 4 strati in lettura + test adversariale Day-1. **Residuo: un bug nell'iniezione degli argomenti** |
| **R-35** | **La memoria diventa una copia strisciante del CRM**, un fatto alla volta, violando `INV-07` per accumulo | Correctness | **Alta** | Alto | `ADR-089` come vincolo di **schema**, non linea guida: violarlo richiede una migration |
| R-36 | Il digest deterministico perde il "perché": il modello ripete tentativi già falliti su run lunghi | Quality | Media | Medio | `repeated_failed_call_rate` + `T-ME-03`; rimedio già progettato (digest ibrido) |
| R-37 | Il cap di memorie attive si riempie e la personalizzazione si congela | Usability | Media | Basso | `AR-ME-19` lo rende visibile + `T-ME-01` |
| R-38 | Un bug nella purge distrugge dati **non ricostruibili** (a differenza della knowledge) | Reliability | Bassa | **Alto** | finestra di grazia + purge solo su righe già `DELETED` + backup (`DEF-06` aperta) |
| R-39 | La competizione di budget rende il retrieval di `A07` progressivamente decorativo nei run lunghi | Quality | Media | Medio | `fragment_eviction_rate` + `T-ME-02`. **Rimedio corretto: alzare `max_model_len`, non cambiare l'ordine di cessione** |
| **R-40** | **La memoria non viene usata affatto**: gli utenti non confermano, le memorie attive restano zero, l'infrastruttura è costo puro | Product | **Alta** | Basso | `memory_confirmation_rate`. **Falsifica `AS-21`** |
| **R-41** | **Confused deputy**: la credenziale di servizio verso il CRM ha più autorità di chi comanda l'agent; la difesa è software **nostro**, non del CRM | Security | **Alta** | **Alto** | 4 strati applicativi + percorso verso la catena 1 (`T-ID-08`). **Non risolto strutturalmente Day-1**, ma **la via d'uscita ora esiste ed è verificata**: API key per-utente di Odoo (`R-10`, `ADR-114` amendata). Il blocco è operativo, non tecnico |
| R-42 | Dipendenza dalla sorgente esterna per il perimetro sui dati: se il CRM è lento o giù, l'autorizzazione è lenta o nega | Reliability | Media | Medio | classi di freschezza (`ADR-082`), allarme prima della soglia, degrado dichiarato |
| R-43 | Il `MemorySnapshot` congelato conserva memorie **revocate** fino a fine run | Security | Media | Basso | `ADR-104` limita la finestra a 10 min attivi; la memoria non produce effetti da sola. Trigger `T-ME-08`/`T-ME-10` |
| R-44 | Dati letti prima di una revoca restano nel context del run | Security | Media | Basso | come `R-43`; `ADR-106` ferma le **azioni** immediatamente |
| R-45 | `purpose` è dichiarato dal chiamante e non verificato: una policy che ci si basa è aggirabile | Security | Media | Medio | `purpose` marcato come non verificato **nel tipo**; mai unica base di un `ALLOW` |
| R-46 | Nessun fallback quando l'IdP è giù: nessuno lavora | Availability | Bassa Day-1 (nessun IdP), **Media** dopo | Alto | categoria di audit distinta; **accettato**: sicurezza sopra disponibilità |
| **R-47** | **Chi ha `root` sulla macchina ha database e chiave master**: la cifratura protegge solo dal furto del solo database | Security | Media | **Alto** | dichiarato; `B-50` (cifratura per-tenant). Vault sposta il problema, non lo elimina |
| R-48 | Il `PlatformOperator` è tecnicamente in grado di leggere i dati dei tenant via database diretto | Security | Media | **Alto** | `ADR-118` rende l'accesso applicativo auditato e quello diretto **rilevabile come anomalia**. Difesa vera solo con `B-50` |
| R-49 | Le colonne di lineage restano inutilizzate e qualcuno le toglie in una pulizia | Process | Media | **Alto** (renderebbe `ADR-123` irreversibile) | il test CI di `AR-AC-01` verifica che **esistano**, non solo che siano degeneri |
| **R-50** | **Il tetto di `ADR-104` viene implementato per run invece che per albero** → una catena di agent diventa il modo di **comprare budget** | Correctness | **Alta** se non presidiato | **Alto** | `INV-18` + `AR-AC-08`; test che crea un albero e verifica che il 51° step fallisca **ovunque si trovi** |
| R-51 | Prompt injection agent→agent: `R-17` diventa meno visibile perché si distribuisce su journal diversi | Security | Media | **Alto** | `AR-AC-12` + ceiling attenuato **contengono**, non impediscono. Mandato ad `A13`, `T-AC-09` |
| R-52 | Confused deputy verso il CRM **aggravato** dall'albero: il CRM vede un utente tecnico al posto di una persona **e di una catena** | Security | Media | Alto | `AR-AC-22`: chiudere `R-41` prima (catena 1, `T-ID-08`, `B-54`) |
| **R-53** | **Il prefix caching si frammenta con N `AgentVersion`**, e `T-MD-09` contava su quella leva | Performance | Media | Medio | `prefix_cache_hit_rate` **per `agent_version`** + `T-AC-07`; misura `B-59` |
| R-54 | Run figli orfani continuano a consumare GPU dopo la morte della radice | Reliability | Media | Medio | `AR-AC-18` + mandato ad `A11`; test che uccide il worker della radice |
| R-55 | Un risultato **parziale** viene presentato al modello come completo | Correctness | Media | Alto | `aggregation` dichiarata **prima** del dispatch, default `ALL_REQUIRED` (fail closed) |
| R-56 | N `AgentVersion` = N volte il debito di lock-in di `R-16`, invisibile nel codice | Vendor | Media | Medio | `portability_delta` misurata **per agent**, non in aggregato |
| **R-57** | **Si assume che A2A dia l'attenuazione dell'autorità**, mentre il *token downscoping* è un **gap dichiarato** della v1.0 (`R-02`) | Security | Media | **Alto** | `ADR-131` lo dichiara; `B-56` cerca il pattern raccomandato |
| **R-58** | **Il recovery classifica male uno step `IN_FLIGHT` e riesegue un side effect non idempotente** → duplicato in produzione | Correctness | **Bassa** (era Media) | **Alto** | `ADR-144` + `AR-EV-08` + 4 test; `RecoveryClassifier` come **funzione pura testabile**. **Ridotta il 2026-08-23 da `ADR-161`**: per le creazioni la classificazione non è più un giudizio ma una lettura su indice unico. Resta sulle transizioni di stato (`AS-35b`) |
| R-59 | Il ledger d'albero è **una riga sola**: hot row sotto fan-out, e allunga la transazione dello step | Scalability | Bassa Day-1, Media dopo | Medio | `AR-AC-23` limita il fan-out ai figli di sola lettura; rimedio (quote) noto e non applicato senza misura |
| **R-60** | **Un crash loop consuma tempo reale senza consumare tempo attivo**: il tetto di 10 minuti diventa ottimista | Correctness | Media | Medio | tetto di step (pessimista) + tetto di `attempt`. **Non risolto per il solo tetto temporale**, dichiarato |
| R-61 | Il `job` diventa la **porta di servizio**: qualcuno ci mette un tool con effetti, ottenendo un agent senza mandante | Security | Media | **Alto** | `AR-EV-12` con test statico; `ADR-142` separa le entità |
| R-62 | Il polling a intervallo fisso brucia I/O quando il sistema è scarico, o aggiunge latenza quando è carico | Performance | Media | Basso | `T-EV-01`, `B-68` |
| ~~R-63~~ | ~~L'outbox senza consumatore vivo accumula in silenzio~~ → **MITIGATO STRUTTURALMENTE** il 2026-08-23 | Reliability | Media | **Alto → Basso** | **`ADR-162`**: la conferma di dispatch è **precondizione dell'attesa** — niente conferma, niente attesa, il run termina con `APPROVAL_UNDELIVERABLE` e lo vede **chi l'ha avviato**. **`ADR-163` + `INV-24`**: generalizzato a tutti i job di background, con dead man's switch nello `scheduler` e canary sintetico. Restano `outbox_lag` e `T-EV-08` come rilevazione, non più come unica difesa |
| R-64 | Il fencing token viene dimenticato in un percorso di scrittura → due worker sullo stesso run | Correctness | Media | Alto | `AR-EV-07` + test; helper unico di scrittura |
| R-65 | Il costo della fairness per tenant nella query di prelievo cresce col numero di run attivi | Performance | Media | Basso | rimedio (contatore denormalizzato) noto e non applicato senza misura |
| R-66 | Una migrazione di schema o la rimozione di una versione rende inutilizzabili i run vivi | Reliability | Media | Medio | `AR-EV-30` + query di guardia + expand/contract |
| **R-67** | **La ricostruzione del prompt non copre i dati letti dal vivo dal CRM**: sappiamo quale chiamata è stata fatta, non cosa ha risposto | Correctness | **Alta** | Medio | `result_hash` + identifier ledger coprono "identificatore sbagliato", non "valore sbagliato". **Non risolvibile senza violare `INV-07`.** Dichiarato |
| R-68 | Il sampling viene abbassato in emergenza e **non rialzato**: il sistema resta cieco senza che nessuno lo decida | Process | Media | Medio | `effective_sampling_rate` monitorata; `AR-OB-16` impedisce di scendere sulle otto classi critiche |
| R-69 | Il registro delle metriche diverge dal codice e il test di CI viene disattivato: `AR-035` torna inapplicata | Process | Media | **Alto** | il test deve fallire nominando **la decisione architetturale bloccata**, non con "registry mismatch" |
| **R-70** | **L'anello di feedback muore al passo umano**: nessuno analizza i difetti, nessun `EvaluationCase` nasce, il set invecchia | Process | **Alta** | Alto | `ADR-185` + caso minimo piccolo. **Mitigazione dichiarata debole** |
| R-71 | La revisione umana campionaria che sostituisce la metrica non automatizzabile non viene fatta, e `ADR-094` resta chiuso per inerzia invece che per evidenza | Process | Media | Basso | è **il comportamento corretto** (chiuso è la posizione conservativa). Il rischio è di non saperlo mai |
| R-72 | **Iniezione di telemetria**: un chiamante inietta `traceparent` o valori che alterano aggregati | Security | Bassa | Basso | `AR-EV-17` (autenticare prima di correlare), `AR-OB-08`, enum ovunque |
| R-73 | **Fuga del dataset di evaluation**: casi derivati da incidenti reali portano dati reali in repository | Security | Media | **Alto** | `AR-OB-24`; fixture sintetici; tenant di test. **Attrito costante**: il caso reale è il più prezioso |
| R-74 | Un identificatore di correlazione o una metrica entrano in una decisione | Security | Bassa | **Alto** | `INV-25` e `INV-27`, verificati staticamente |
| **R-75** | **L'attrito introdotto contro `ASI09` viene disattivato perché gli utenti si lamentano**: sono numeri in una configurazione | Process | **Alta** | **Alto** | `AR-SE-06` impedisce staticamente il caso peggiore; il resto è documentazione della ragione. **Mitigazione debole, dichiarata** |
| R-76 | La coda di quarantena non viene mai svuotata: i documenti legittimi restano invisibili | Process | Media | Medio | `max_staleness` sulla coda (`INV-24`): l'abbandono è un evento di errore |
| R-77 | La lettura autoritativa di `ADR-190` viene tolta per prestazioni | Process | Media | Alto | è il costo più giustificato del documento; va scritto nel codice, non solo in architettura |
| **R-78** | **Il `KillSwitch` non viene mai provato e non funziona quando serve** | Process | **Alta** | **Alto** | test di contenimento fra i gate. **Un contenimento non provato non esiste** |
| **R-79** | **Corruzione lenta del dato**: alterazioni piccole e plausibili passano l'approvazione, e l'audit le registra come legittime | Correctness | Media | **Alto → Medio** | `ADR-190` mostra il valore vero in approvazione. **Attenuato il 2026-08-23 da `ADR-221`**: il valore precedente finisce nel journal, quindi la corruzione diventa **ricostruibile** — non impedita, ma non più invisibile. Rilevamento ancora aperto → `B-88` |
| R-80 | Il profilo comportamentale produce falsi allarmi e viene ignorato | Process | Media | Basso | è un segnale, non un blocco |
| **R-81** | **Il capability floor viene allargato per pressione commerciale, senza l'albero delle azioni** | Process | **Alta** | **Alto** | `AR-SE-26` rende l'albero un gate di rilascio. `ADR-217` è *facile ad allargare e difficile a stringere*: va difeso in revisione |
| R-82 | La cardinalità 1 viene aggirata con N chiamate ripetute nello stesso run | Correctness | Media | Medio | `ADR-104` (50 step) mette un tetto per costruzione; il profilo comportamentale (`ADR-211`) lo vede come anomalia |
| R-83 | La lettura prima della scrittura **non è atomica**: fra la lettura e la scrittura un altro attore può cambiare il valore | Correctness | Media | Basso | registriamo **ciò che abbiamo visto**, non ciò che c'era: è sufficiente per la ricostruzione, non per il locking. Dichiarato |
| R-84 | Le regole SoD non vengono mai dichiarate dal cliente e `ADR-226` resta un motore vuoto | Process | **Alta** | Medio | il set parte da un baseline standard; `B-93`. Un motore SoD senza regole è peggio di nessun motore, perché dà l'illusione del controllo |
| R-85 | La conferma su **ogni** scrittura produce approval fatigue, cioè `ASI09` per costruzione | Security | **Alta** | **Alto** | `ADR-191` differenzia la **forma**; `ADR-194` mette un tetto; `ADR-196` impedisce di uscirne per il motivo sbagliato. **È la tensione centrale dell'architettura, dichiarata e non risolta** |
| **R-86** | **Sovra-restrizione documentale**: documenti utili resi irraggiungibili perché contengono un passaggio sensibile; il retrieval si impoverisce **in silenzio** | Quality/Privacy | Media | Medio | `over_restriction_rate` + `T-DG-06` → separazione a monte, **mai** redazione |
| **R-87** | **Il testo libero dell'utente è il maggior serbatoio di dato personale da noi**, non classificabile né minimizzabile; ci possono finire categorie particolari | Privacy | **Alta** | **Alto → Medio** | **Attenuato il 2026-08-23 da `ADR-256`: retention a 30 giorni**, allineata alla convergenza di OpenAI, Anthropic e Salesforce (`R-15.1`). Più `INV-40` (mai nei dataset) e `ADR-260` (nessun invio a terzi, strutturale). **Resta il fatto che non possiamo impedirne l'ingresso**: la difesa è su durata e diffusione |
| **R-88** | **Il valore precedente di `ADR-221` è dato di dominio nel nostro journal**: erode `INV-07` per accumulo, come `R-35` per la memoria | Compliance | Media | **Alto** | `ADR-241`: perimetro stretto, retention più corta, mai leggibile dal modello, `AR-DG-05` |
| **R-89** | **L'identity shredding non è anonimizzazione**: `acl_subject` risolve in Odoo e i pattern comportamentali re-identificano | Privacy | Media | **Alto** | dichiarato. `B-95`, `B-99`. Mitigazione parziale: hash di `acl_subject` nell'audit, al costo della leggibilità |
| **R-90** | **Il `deletion_ledger` non viene rigiocato dopo un restore** e dati cancellati tornano vivi in silenzio | Compliance | Media | **Alto** | il rigioco è **un passo obbligatorio** della procedura di restore, e la procedura va **provata** (lezione di `R-78`) |
| **R-91** | **Il registro `data_asset` diverge dallo schema e il test di CI viene disattivato** (stessa forma di `R-69`) | Process | Media | **Alto** | il test fallisce **nominando la decisione bloccata**, non con "registry mismatch" |
| **R-92** | **Il motore SoD resta vuoto Day-1 senza che nessuno se ne accorga**, perché `ADR-217` ha già tolto la superficie; quando la superficie si allarga, il motore è ancora vuoto | Process | **Alta** | **Alto** | **`T-DG-11`**: allargamento con registro vuoto = **blocco di rilascio**. **Rafforzato il 2026-08-23 da `ADR-259`**: il target non è più indefinito ma **~45 regole**, l'ordine di grandezza dei set commerciali. `B-97` chiusa con un no — **non esiste un catalogo pubblico da attendere**, va costruito (`B-105`). Nota: i controlli nativi di Odoo **non ci coprono le spalle**, un registro vuoto non ha una seconda rete |
| **R-93** | **La classificazione ad alto rischio dell'AI Act cambia per un caso d'uso nuovo** e nessuno rivaluta | Compliance | Media | **Alto** | `T-DG-03`, agganciato al gate di `AR-SE-26` |
| **R-94** | **L'export DSAR diventa un canale di esfiltrazione**: in un file ciò che le policy davano a pezzi. È `R-17` travestita da diritto | Security | Media | **Alto** | autenticazione forte, notifica all'amministratore, rate limiting, contenuto limitato al richiedente. `B-94` |
| **R-95** | **La retention non viene mai fissata**: tutto resta `NON ANCORA DECISO` e il sistema accumula per sempre | Process | **Alta** | Medio | **`DEF-13` con scadenza "prima dello schema"** e owner nominato. Senza owner, si realizza |
| **R-96** | **I backup diventano l'archivio vero**: retention di backup più lunga di quella del dato, quindi la cancellazione è nominale | Compliance | **Alta** | **Alto → Medio** | **Attenuato il 2026-08-23**: `ADR-257` adotta la postura ICO *beyond use* con obbligo di comunicazione all'interessato; `ADR-258` dichiara il `deletion_ledger` come *suppression list* e ne rende il rigioco un **test**, non una procedura scritta. Resta aperto il posizionamento del Garante italiano → **`B-104`**. **Fonte di urgenza: il rapporto EDPB 2026 mette i backup fra le sette criticità sistemiche, ed è materia di enforcement attivo** |
| **R-97** | **I gate bloccanti migrano fuori dal percorso che bloccano**: la CI diventa lenta, si sposta lavoro nightly, e i primi spostati sono proprio i test che bloccano | Process | **Alta** | **Alto** | `T-QA-01` impone che lo spostamento avvenga in un **ordine dichiarato**, con i gate deterministici **ultimi** |
| **R-98** | **L'`OdooFake` diverge da Odoo reale** e i test passano su una finzione | Correctness | **Alta** | **Alto** | contract test bidirezionale notturno (`TC-QA-023`), `T-QA-02` → Odoo effimero |
| **R-99** | **Un gate probabilistico si fa diventare verde alzando la soglia** | Process | **Alta** | **Alto** | `ADR-268`: la soglia vive nel registro sotto review, non nel codice del test |
| **R-100** | **Il dataset sintetico è troppo pulito**: nessun omonimo, nessun campo vuoto, nessun accento, nessun partner archiviato con fatture vive. **I difetti reali stanno nello sporco** | Quality | **Alta** | Medio | il livello `hostile` di `ADR-263`, alimentato dai `FATTO` di `R-14.7` e dagli incidenti |
| **R-101** | **I tre compiti umani non vengono eseguiti** (red teaming `ASI09`, revisione campionaria, classificazione dei difetti) | Process | **Alta** | **Alto** | `ADR-272` (cadenza e artefatto dichiarati), `G-QA-09` marcato `INCOMPLETO`. **Mitigazione dichiarata debole** |
| **R-102** | **La suite contende la GPU allo sviluppo**: la eval suite gira e nessuno può lavorare col modello | Performance | Media | Medio | eval suite notturna e seriale, due sole eccezioni in PR (`T-QA-05`) |
| **R-103** | **Il registro diventa la lista dei test che abbiamo, non di quelli che servono** | Process | Media | **Alto** | il controllo n. 2 estrae i mandati **dai documenti**, non dal codice: rilassarlo richiede di modificare l'estrattore, che è una modifica visibile |
| **R-104** | **Il crash è sempre negli stessi punti dichiarati**, e un difetto di recovery in un punto non dichiarato resta invisibile | Correctness | Media | Alto | ogni difetto di recovery sfuggito diventa un nuovo punto dichiarato (`ADR-278`) |
| **R-105** | **L'holdout viene guardato** e si brucia | Quality | Media | Alto | `ADR-275`: esecuzione solo al rilascio. Non impedibile tecnicamente — il numero di esecuzioni fra due rilasci è il segnale |
| **R-106** | **`k` non viene mai calibrato** e `ADR-180` («bloccanti solo se deterministici») diventa una scusa permanente per non far bloccare nulla di qualità | Process | **Alta** | **Alto** | `T-QA-03`, `DEF-14` con scadenza al terzo rilascio, `B-106` a priorità **ALTA** |
| **R-107** | **Il `negative_case` di `INV-42` viene scritto per far passare il controllo**, non per provare il gate | Quality | Media | Medio | il `negative_case` dichiara **quale controllo rimuove**, e il runner verifica che il test principale fallisca **col messaggio atteso**, non con un errore qualsiasi |
| **R-108** | **`INV-40` copre il testo libero prodotto in produzione, non i documenti aziendali reali**: un golden set del retrieval costruito su documenti reali del committente non viola nessuna regola attuale, ma porta contenuto aziendale in repository | Privacy | Media | **Alto** | **scoperto in `A17` §30, NON risolto.** Va portato ad `A14` o al committente: o si estende `INV-40` ai documenti, o si dichiara che il golden set usa solo documenti sintetici (posizione di `ADR-263`, oggi non imposta da nessuna regola). Ricerca `B-115` |
| **R-109** | **`B-53` viene confermata E la JSON-2 API non ha la forma `(model, method, args, kwargs)`**: allora non basta riscrivere `transport.py`, cambia la forma di tutti i tool | Correctness | Media | **Alto** | **non mitigabile oltre l'isolamento già fatto** (`ADR-293`). `T-AP-01` + `B-118` |
| **R-110** | **Il budget di `ADR-294` è tarato sul nulla**, e un errore verso il largo è **invisibile**: nessuno si accorge di un budget troppo generoso finché non satura Odoo | Performance | **Alta** | Medio | `B-116` (priorità Alta), `DEF-21` |
| **R-111** | **Gli SSE si chiudono mentre il run è in attesa di approvazione**: proxy e reti aziendali chiudono le connessioni inattive, e un run in attesa umana è inattivo per definizione | Correctness | **Alta** | Medio | `ADR-286`: il polling è il contratto, SSE è ottimizzazione. `T-AP-05`, `B-121` |
| **R-112** | **I 192 test negativi migrano nightly** appena la CI diventa lenta | Process | **Alta** | **Alto** | `AR-AP-30` blocca solo `NEG-1/2/3`. **Mitigazione parziale e dichiarata tale.** È `R-97` applicato ad `A18` |
| **R-113** | **Un endpoint viene aggiunto fuori dalla specifica OpenAPI** e sfugge a tutte le regole che poggiano sulla specifica | Process | Media | Alto | `ADR-284` contract-first + `G-AP-01` |
| **R-114** | **`ADR-287` (niente streaming in approvazione) è teatro se `AS-44` è falsa**: se l'attrito della conferma non funziona, togliere lo streaming non aggiunge nulla | Security | Media | Medio | dipende da `AS-44` e da `B-87`. Non risolvibile dentro `A18` |
| **R-115** | **L'`OdooFake` non può rilevare divergenze di protocollo**, perché implementa la firma di `call()`, non il filo. **`A18` peggiora `R-98` e lo dichiara** | Correctness | **Alta** | **Alto** | **non risolto.** Il contract test notturno di `ADR-262` gira contro Odoo reale ed è l'unico luogo dove la divergenza può emergere |
| **R-116** | **Il rate limiting su PostgreSQL diventa il collo di bottiglia**: il meccanismo che protegge è quello che cede | Performance | Media | Medio | `AS-65` non misurata, `T-AP-10`, `B-119` |
| **R-117** | **Il PDP e i permessi di Odoo divergono in silenzio.** Il caso peggiore **non** è che il PDP neghi e Odoo permetta: è il **contrario**, perché allora il nostro `ALLOW` è scritto nell'audit come se fosse valido | Security | Media | **Alto** | `T-AP-04` su `external_authz_divergence_rate` |

---

## 8. Registro dei Trust Boundary

| # | Confine | Controllo applicato |
|---|---|---|
| TB-1 | Utente → Piattaforma | OIDC, sessione, tenant resolution |
| TB-2 | Piattaforma → Agent Runtime | identità dell'agent distinta, capability set congelato |
| TB-3 | Agent Runtime → Model | il prompt è dato; l'output è **untrusted** |
| TB-4 | Agent Runtime → Tool | PEP: policy + schema validation + idempotenza |
| TB-5 | Tool → Sistema esterno (CRM/ERP/email) | credenziale del tool, mai il token dell'utente |
| TB-6 | Knowledge/RAG → Context | i frammenti recuperati sono `trust_class = retrieved`, mai istruzioni |
| TB-7 | Tenant → Tenant | `tenant_id` obbligatorio + row-level enforcement |

---

## 9. Registro del debito architetturale

| ID | Debito | Tipo | Trigger di risoluzione |
|---|---|---|---|
| D-01 | Queue su PostgreSQL invece di broker dedicato | Intenzionale | throughput sostenuto > qualche migliaio di transizioni/s |
| D-02 | Policy evaluator scritto in casa invece di OPA/Cedar | Intenzionale | serve authoring di policy da parte di non-sviluppatori, o verifica formale |
| D-03 | Nessun isolamento fisico per tenant | Intenzionale | primo cliente con requisito contrattuale di isolamento |
| D-04 | Nessun SPIFFE/SPIRE per identità di servizio | Intenzionale | deployment multi-nodo con più servizi che si autenticano fra loro |

---

## 9b. Trigger di revisione architetturale

Condizioni **osservabili** che riaprono una decisione. Ogni trigger deve avere una metrica
(`AR-035`); `A12` è responsabile di garantirlo.

| ID | Condizione osservabile | Riapre | Verso |
|---|---|---|---|
| T-01 | p95 enqueue > 100 ms per contesa su PostgreSQL | persistenza | broker / Redis per la queue |
| T-02 | > 2.000 transizioni di step/s sostenute | durable execution | Temporal / partizionamento |
| T-03 | recall del retrieval sotto soglia con pgvector | persistenza | vector store dedicato |
| T-04 | team > 8 persone con ownership separate | decomposizione | estrazione di servizi |
| T-05 | cliente con isolamento fisico contrattuale | multi-tenancy | deployment per tenant |
| T-06 | policy scritte da non-sviluppatori | autorità | OPA / Cedar |
| T-07 | il Tool Runtime deve eseguire codice non fidato | decomposizione | sandbox / isolamento di processo |
| T-08 | serve consumare server MCP di terzi in produzione | tool | adapter MCP outbound |
| T-09 | GPU > 80% con p95 fuori SLA | risorse | seconda replica di inference |
| T-10 | tasso di errore su tool selection alto dopo prompt engineering | modello | QLoRA sul dataset di errori |

| T-CP-01 | `resolve()` p95 > 50 ms, o cache hit snapshot < 50% | Control Plane | cache in-process invalidata su `revision` |
| T-CP-02 | l'API amministrativa diventa raggiungibile da rete non fidata | Control Plane | Opzione D: gestione in processo separato |
| T-CP-03 | più installazioni da gestire centralmente, o runtime con config in memoria | Control Plane | riconciliazione limitata alla propagazione |
| T-CP-04 | > ~5 amministratori concorrenti, o conflitti `409` frequenti | Control Plane | console + approval workflow |

| T-GP-01 | le query del PIP superano il 30% della latenza di uno step | governance | pre-caricamento in blocco o attributi denormalizzati |
| T-GP-02 | una classe di azioni viene approvata quasi sempre **senza modifiche** | governance | allentare `ADR-023` su quella classe |
| T-GP-03 | le policy diventano troppe o troppo intrecciate per essere lette | governance | Cedar/OPA con verifica formale |
| T-GP-04 | requisiti di condivisione gerarchica profonda | governance | OpenFGA come **fonte di attributi** |

| T-RT-01 | tasso di `UNCERTAIN` sopra soglia (da definire dopo il primo mese) | runtime | indagine sulla stabilità prima di allentare l'approvazione |
| T-RT-02 | un tipo di compito ha traiettoria stabile su N esecuzioni | runtime | promozione a `HYBRID` / `WORKFLOW` |
| T-RT-03 | rilevamenti di loop sopra soglia | runtime/modello | workflow deterministico o modello diverso |
| T-RT-04 | tempo in attesa di approvazione > tempo di lavoro | governance | allentare `ADR-023` |
| T-RT-05 | serve backtracking vero su azioni con effetti | runtime | **rottura seria**: ripensare il modello di esecuzione |
| T-RT-06 | > 2 correzioni al codice di recovery nel primo trimestre | durable execution | **riaprire `ADR-002`** invece di rattoppare |
| T-MD-01 | TTFT fuori soglia con GPU scarica | inference | il collo non è la GPU: indagare altrove |
| T-MD-02 | KV cache > 90% o preemption | inference | **ridurre `max_model_len`**, non comprare GPU |
| T-MD-03 | `malformed_rate` alto dopo l'anello 1 | inference | rivedere constrained decoding o prompt |
| T-MD-04 | serve un secondo modello reale | inference | routing statico per capability |
| T-MD-05 | un tenant vieta o richiede il cloud | policy | il fallback diventa decisione di policy (`C27`) |
| T-MD-06 | i due profili di serving arrivano in produzione | — | `AR-020` verificata sul campo |
| T-MD-07 | restart ripetuti del serving | reliability | indagine sulla stabilità |
| T-MD-08 | `portability_delta` in crescita per due trimestri | vendor | il lock-in sta maturando: intervenire |
| T-MD-09 | prefix caching molto redditizio | inference | valutare SGLang (candidato n.1 alla sostituzione) |

| T-TL-01 | `schema_failure_rate` alta su un tool | tool | ridisegnare lo schema di quel tool |
| T-TL-02 | troppi tool dopo uno split | tool | rivedere la granularità |
| T-TL-03 | **il primo tool non nostro** | isolamento | specializzazione di `T-07`: sandbox o processo separato |
| T-TL-04 | requisito di data residency sull'egress | networking | proxy di egress |
| T-TL-05 | serve esporre i nostri tool via MCP | integrazione | adapter MCP inbound |
| T-TL-06 | `missing_capability_rate` alto | tool | **riapre `ADR-049`** (il divieto di SQL) |
| T-TL-07 | `uncertain_rate` concentrato su pochi tool | tool | quei tool non dichiarano bene idempotenza/verificabilità |
| T-TL-08 | le credenziali superano la rotazione manuale | identity | secret store con rotazione |
| T-TL-09 | budget di prefisso in warning stabile | inference | ridurre i tool esposti o le definition |
| T-TL-10 | serve gestire i Multi Round-Trip di MCP | integrazione | `NON ANCORA DECISO` (`B-21`) |

| T-KN-01 | `query_embed_latency_p95` oltre la quota assegnata del budget di latenza | **riapre `ADR-068` e `AS-08`** | embedding su GPU o servizio dedicato |
| T-KN-02 | `ingestion_lag_p95` fuori dalla classe di freschezza, o backfill impraticabile | `ADR-068` (solo per il backfill) | batch su GPU in finestre dedicate |
| T-KN-03 | `recall_at_k` accettabile ma `precision_at_k` bassa | `ADR-069` | reranker, partendo dalla CPU |
| T-KN-04 | `recall_at_k` sotto soglia sul golden set | **`T-03`**, quindi `ADR-003` | prima tuning e over-fetch, poi vector store |
| T-KN-05 | `retrieval_miss_rate` alto con l'informazione presente nell'indice | `AR-KN-21` | tool `knowledge_search` **accanto** al canale |
| T-KN-06 | query di traversamento multi-hop frequenti e non esprimibili | `ADR-079` | prima CTE ricorsive, poi grafo |
| T-KN-07 | latenza di propagazione oltre la classe di freschezza di una sorgente | `ADR-081` | webhook per quella sorgente, polling come rete |
| T-KN-08 | i blob superano il disco locale, o serve durabilità superiore | `ADR-073` | object storage S3-compatible |
| T-KN-09 | tempo di propagazione di una revoca oltre la soglia | `ADR-072` | proiezione dei grant event-driven |
| T-KN-10 | serve una lingua o un dominio non coperti dal modello di embedding | `ADR-087` | secondo modello in coesistenza |
| T-KN-11 | `index_build_time` oltre la finestra di manutenzione, o isolamento dell'indice richiesto | `ADR-070` / `D-03` | indice partizionato per tenant o collezione |

| T-ME-01 | `memory_cap_reached_rate` significativo, o `memory_active_count` al cap per una quota di soggetti | `ADR-099`, `AS-18` | consolidamento, poi retrieval strutturale → lessicale → embedding, **in quest'ordine** |
| T-ME-02 | `context_budget_exceeded_rate` sopra soglia, o `fragment_eviction_rate` alto e stabile | **`ADR-039`** prima di `ADR-091` | più context, non un ordine di cessione diverso |
| T-ME-03 | `refetch_rate` o `repeated_failed_call_rate` alti | `ADR-090` | zona A più lunga, poi eventualmente digest ibrido |
| T-ME-04 | `proposed_memory_precision` alta e stabile su campione etichettato | **`ADR-094`** | attivare l'estrazione automatica per un sottoinsieme di tipi |
| T-ME-05 | Requisito reale di memoria condivisa da un cliente | `ADR-100` | `scope = TENANT` in scrittura, con approvazione |
| T-ME-06 | `memory_correction_rate` o `memory_deletion_rate` alti | `ADR-094`, l'assegnazione di `authority` | la scrittura è troppo facile, o `OBSERVED` è mal definita |
| T-ME-07 | Primo run multi-agent (`C31`/A2A) | l'ownership della memoria | modello di delega e di lettura condivisa |
| T-ME-08 | Un tenant richiede propagazione **immediata** delle revoche ai run in corso | **`ADR-092`** | scongelamento dello snapshot, col costo sul prefix caching |
| T-ME-09 | `wrong_entity_rate` sopra soglia | il design dell'identifier ledger | ledger con relazioni `(entity, relation, entity)` |
| T-ME-10 | Un requisito di cancellazione impone propagazione ai run in corso | `ADR-092` | come `T-ME-08` |
| T-ME-11 | Reclami di continuità fra run della stessa conversazione | `ADR-101` | trail più lunga, o summary ibrido |

| T-ID-01 | Richieste ricorrenti di azioni che l'agent deve poter fare e l'utente no | **`ADR-105`** (l'intersezione) | dare il permesso all'utente in modo condizionato, **mai** un'eccezione all'intersezione |
| T-ID-02 | La delega deve attraversare una rete (tool remoto, processo separato) | `ADR-113` | token firmato, stesso contratto |
| T-ID-03 | Tasso di run terminati in `DELEGATION_EXPIRED` sopra soglia | `ADR-112`, `AS-25` | rivedere sessione contro finestra di approvazione |
| **T-ID-04** | **Primo tenant con un proprio IdP**, o requisito di MFA che non vogliamo implementare | **`ADR-109`** | **prima LDAP** (`ADR-121`: è ciò che il committente si aspetta in una realtà aziendale), OIDC/Keycloak solo dopo |
| T-ID-05 | La lettura della sessione diventa una quota visibile della latenza | `ADR-110` | token a vita brevissima + riga consultata al rinnovo |
| T-ID-06 | Requisito di isolamento della memoria dei segreti, **o primo tool non nostro** | `ADR-108` (specializza `T-TL-03`) | `Credential Broker` in processo separato |
| T-ID-07 | Un cliente chiede separazione fra le proprie divisioni | il modello di tenant piatto | `org_id` come colonna aggiuntiva |
| **T-ID-08** | **Un tenant chiede che le azioni compaiano nei suoi log con l'identità della persona**, o una conformità vieta l'utente tecnico condiviso | **`ADR-114`** — è il trigger che risolve **`R-41`** | catena 1 via **API key per singolo utente di Odoo**, non OAuth (`ADR-114` amendata, `B-54`) |
| T-ID-09 | L'inference server non è più sulla stessa macchina, o la macchina ospita processi non nostri | `AS-06` | mTLS fra i processi |
| T-ID-10 | Un tenant supera ~200 persone, o serve disattivazione automatica alla cessazione | la gestione manuale dei soggetti | SCIM |

| **T-AC-01** | `tool_selection_error_rate` cresce in modo misurabile col numero di tool esposti (`B-20`) | **`ADR-123`**, ma **passando dalla scala dei rimedi** | prima `ToolBinding` più stretti, poi **literal intermedi e schemi migliori (`B-66`, è il rimedio che `R-11.2` indica per i modelli piccoli)**, poi QLoRA, poi un secondo agent avviato dal codice, **infine** multi-agent |
| T-AC-02 | `missing_capability_rate` alto **e** i casi richiedono ragionamento su due domini disgiunti | `ADR-123` | agent specializzati con tool set disgiunti, prima di tutto il resto |
| **T-AC-03** | **Primo requisito reale di interoperabilità con un agent di un'altra organizzazione** | `ADR-131` | A2A adapter di confine (fase 3) |
| T-AC-04 | `run_steps_p95` sfiora 50 o `run_active_duration_p95` sfiora 10 minuti | **`ADR-104`**, non `ADR-123` | rinegoziare il vincolo di dominio col committente. **Il multi-agent non produce tempo** |
| T-AC-05 | Un compito richiede due contesti di ragionamento **davvero simultanei** | **`AS-08`**, `ADR-039`, `ADR-045` | è una decisione di `A05`: seconda GPU o secondo profilo di serving |
| T-AC-06 | Primo run con `parent_run_id IS NOT NULL` | `T-ME-07` (già presidiato), `R-41`, il threat model di `A13` | revisione congiunta memoria + identity + security |
| T-AC-07 | `prefix_cache_hit_rate` cala sotto soglia dopo l'aggiunta di una `AgentVersion` | `ADR-124` | consolidare i prompt, ridurre le `AgentVersion` attive |
| T-AC-08 | Primo agent **non nostro** eseguito nel nostro processo | `ADR-136`, `AS-12`/`AS-28` | isolamento a processo; specializza `T-TL-03` e `T-ID-06` |
| T-AC-09 | `A13` conclude che la separazione dei privilegi **dentro** un compito è un requisito | **`ADR-123`** | prima due run in sequenza dal codice applicativo, poi eventualmente `child run` |

| T-EV-01 | `queue_wait_p95` alto **con worker scarichi** | il meccanismo di sveglia | `LISTEN`/`NOTIFY` (dopo `B-68`), poi coda dedicata |
| T-EV-02 | contesa misurata sul ledger, o `step_transitions_per_second` verso la soglia di `T-02` | `ADR-146`, `ADR-141` | ledger a quote, poi partizionamento, poi engine dedicato |
| **T-EV-03** | **`uncertain_after_crash_rate` sopra soglia** | **`AS-35b`** (le transizioni di stato; le creazioni sono chiuse da `ADR-161`) e la dichiarazione di idempotenza dei tool (`AR-RT-04`) | intervento su `A06`: `SIDE_EFFECT` a due fasi per le transizioni di stato. Specializza `T-TL-07` |
| **T-EV-04** | **Più di 2 correzioni al codice di recovery nel primo trimestre** (= `T-RT-06`) | **`ADR-141`/`ADR-002`** | **DBOS o `pg_durable`, non Temporal** (`B-70`) |
| T-EV-05 | primo requisito reale di run avviato o ripreso da un evento esterno | `ADR-150` | inbox + verifica di firma (`B-73`) |
| T-EV-06 | primo requisito di esecuzione **automatica** di un agent (non di un job) | **`ADR-148`** | `ServicePrincipal` con ceiling dichiarato e materializzato da un umano |
| T-EV-07 | serve più di un processo `scheduler` (multi-nodo) | `ADR-151` | leader election esplicita invece dell'advisory lock (`B-71`) |
| T-EV-08 | `outbox_lag`, `outbox_undelivered_age`, o **`approval_undeliverable_rate` non nullo** | `ADR-149`, `ADR-162` | consumatore dedicato, allarme prima della soglia. **Non è più l'unica difesa**: `ADR-162` fa fallire il run in modo visibile |
| T-EV-09 | `T-RT-02` scatta (traiettorie stabili) | `ADR-028` | `WorkflowDefinition` come risorsa del Control Plane, modo `WORKFLOW` |
| T-EV-10 | `delegation_expired_rate` sopra soglia (= `T-ID-03`) | **`ADR-112`, `AS-25`** | rivedere durata di sessione contro finestra di approvazione |

| T-OB-01 | l'exporter scritto in casa diventa fonte di difetti, **o** esiste una piattaforma progettata su riferimenti invece che su contenuto | `ADR-165` | OpenTelemetry Collector |
| T-OB-02 | più di una macchina, **o** cercare nei log non è più praticabile | il backend dei log | Loki o simile |
| **T-OB-03** | la telemetria è una quota significativa delle scritture su PostgreSQL | **`ADR-166`** | backend di trace e metriche dedicato |
| T-OB-04 | le query per tenant sui cruscotti diventano troppo lente | `ADR-174` | rollup per tenant, poi backend dedicato |
| T-OB-05 | il volume di run rende statisticamente significativa una frazione di traffico | `ADR-183` (in parte) | canary di versione |
| T-OB-06 | il volume rende impraticabile guardare i grafici **e** le soglie fisse fanno rumore | la scelta di non fare anomaly detection | rilevamento statistico |
| T-OB-07 | esistono **tre** baseline consecutive misurate per una metrica di qualità | `ADR-180` | i gate advisory diventano bloccanti in forma **relativa** |
| T-OB-08 | `eval_dataset_age` oltre soglia, **o** i casi passano mentre la produzione peggiora | i dataset di evaluation | rinfresco da campioni di produzione |
| T-OB-09 | requisito contrattuale di integrità dell'audit | il modello di audit | tamper evidence |
| T-OB-10 | un guasto specifico di un tenant sfugge al canary di sistema | `ADR-182` | canary per tenant, con costo e consenso dichiarati |

| T-SE-01 | tasso di rilevamento euristico di injection sopra soglia | il modello di minaccia sui documenti | **stringere i ceiling**, non aggiungere filtro |
| T-SE-02 | `approval_decision_time_p50` sotto la soglia di leggibilità | **`ADR-191`, `AS-44`** | l'attrito non funziona: rivedere l'interfaccia, **non rimuoverla** |
| T-SE-03 | tetto di `ADR-194` raggiunto regolarmente da utenti legittimi | `ADR-023`, `AS-45` | rivedere **quali** azioni richiedono approvazione, per classe, non toglierla in blocco |
| T-SE-04 | coda di quarantena oltre `max_staleness` | `ADR-197` | soglie del sensore, o persona dedicata |
| **T-SE-05** | **primo componente non nostro nel processo** (= `T-TL-03`) | **`ADR-136`, `AS-12`** | isolamento a processo. **Il trigger di sicurezza più importante**: `AS-12` regge tre difese |
| T-SE-06 | identificatori in `SIDE_EFFECT` non osservati, sopra soglia | `ADR-198`, `AR-GP-17` | redazione per campo, cioè il residuo di `R-32` |
| T-SE-07 | requisito di conformità che impone rilevamento centralizzato | la scelta di non avere un SIEM | SIEM, dopo il secondo nodo |
| **T-SE-08** | una classe di azioni supera le **tre** condizioni di `ADR-196` per un periodo dichiarato | **`ADR-216`** | quella classe passa da *human-in-the-loop* a *human-on-the-loop*: l'azione parte e una persona può intervenire dopo. **Mai direttamente ad autonoma** |
| T-SE-09 | la cardinalità 1 rende impraticabile un caso d'uso reale e ricorrente | `ADR-220` | cardinalità dichiarata per quel tool, col conteggio in evidenza nell'approvazione |
| T-SE-10 | primo requisito reale di **scrittura sull'ERP** o sulla contabilità | **`ADR-217`, `ADR-222`, `ADR-223`** | classe per classe, con albero delle azioni e regole SoD dichiarate. **Mai in blocco** |
| T-SE-11 | `missing_capability_rate` alto sulla superficie CRM scrivibile | `AS-48` | allargare la superficie **per entità dichiarata**, dopo `AR-SE-26` |

| **T-DG-01** | primo tenant con requisito **contrattuale** di CMK, o primo deployment multi-tenant con co-tenant non fidati | `ADR-239`, `B-50` | cifratura per tenant → CMK → crypto-shredding → backup per tenant |
| **T-DG-02** | prima richiesta reale di un data subject | il processo semi-manuale, `AS-52` | `Erasure Coordinator` completo + verifica dell'identità del richiedente |
| **T-DG-03** | primo caso d'uso che produce **scoring** usato per decidere fidi, condizioni o accesso a servizi | `AS-55`, la classificazione AI Act, l'art. 22 | rivalutazione **prima** del rilascio, dentro il gate di `AR-SE-26` |
| **T-DG-04** | primo tenant con requisito di residency diverso dalla macchina | `ADR-247` | **installazione per regione**, mai replica cross-regione. Coincide con `T-05` |
| **T-DG-05** | primo requisito reale di legal hold | `ADR-245` | il predicato da costante falso a sistema |
| **T-DG-06** | `over_restriction_rate` sopra soglia sul percorso documentale | **`ADR-229`** | granularità di chunk **per separazione a monte**, mai per redazione |
| **T-DG-07** | prima richiesta di un'autorità di rimuovere fisicamente un dato dall'audit | **`INV-05`**, `ADR-238` | `ADR-238` esce dal cassetto e `INV-05` va rinegoziata col committente |
| **T-DG-08** | il numero di `data_asset` supera ciò che una persona legge in un pomeriggio (~50) | `ADR-233` | valutare un catalogo vero |
| **T-DG-09** | primo model provider esterno richiesto da un tenant | `ADR-242`, §8.3, §33.2 | DPA, valutazione del trasferimento, `AR-DG-16` da rinegoziare |
| **T-DG-10** | la retention dei backup supera quella dichiarata di una categoria di dato | `R-96` si è realizzato | o si accorcia il backup, o `ADR-237` deve coprire la differenza in modo provato |
| **T-DG-11** | **`T-SE-10` scatta (allargamento della superficie di scrittura sull'ERP) mentre il registro SoD è vuoto per le entità coinvolte** | `ADR-226`, `ADR-249`, `R-92` | **blocco di rilascio**, dentro il gate di `AR-SE-26` |
| **T-QA-01** | il tempo di CI per commit supera la soglia ergonomica | la matrice di esecuzione | spostamento nightly **in un ordine dichiarato**, coi gate deterministici **ultimi** |
| **T-QA-02** | il contract test `OdooFake` ↔ Odoo reale fallisce ripetutamente in un trimestre. **Previsto come il primo trigger a scattare** | `ADR-262` | Odoo effimero per la fascia integration |
| **T-QA-03** | esistono **tre baseline consecutive** per una metrica di qualità **e** `k` è calibrato | `ADR-180`, `G-QA-07` (= `T-OB-07`) | il gate advisory diventa bloccante in forma **relativa** |
| **T-QA-04** | `flake_rate` sopra soglia su una classe di test | l'isolamento dei test | revisione di `AR-QA-03` e della concorrenza, **mai** retry automatico |
| **T-QA-05** | la GPU è contesa fra eval suite e sviluppo | `AS-08`, `ADR-045` | finestra dedicata, poi seconda scheda (decisione di `A05`) |
| **T-QA-06** | primo tenant reale in produzione | il synthetic monitoring | canary per tenant (= `T-OB-10`) |
| **T-QA-07** | il numero di `EvaluationCase` supera ciò che si esegue in una notte | la eval suite | **campionamento stratificato dichiarato** (`AR-QA-17`), mai riduzione silenziosa |
| **T-QA-08** | **primo tool non nostro** (= `T-TL-03`) | la superficie di test | suite di tool poisoning |
| **T-QA-09** | un gate viene disattivato più di una volta | `ADR-276` | la quarantena diventa escalation, non rinnovo |
| **T-QA-10** | `escaped_defect_rate` in crescita | l'intera piramide a tre corpi | il corpo che non sta trovando i difetti va rivisto |
| **T-QA-11** | **`T-SE-10` scatta** (allargamento della superficie di scrittura sull'ERP) | **`AS-40`** | il protocollo di §8.2 **va rieseguito sulla superficie ERP**: le post-condizioni deterministiche del CRM non si estendono per assunzione all'ERP |
| **T-AP-01** | **verifica di `B-53` sulla fonte primaria di Odoo.** **Scadenza: prima che `A15` fissi la versione di Odoo** | `ADR-293`, `AS-66` | se confermata con forma diversa, `R-109` si realizza e la forma dei tool cambia |
| **T-AP-02** | si apre la finestra di rimozione delle API RPC | `ADR-293` | riscrittura di `transport.py`, o dell'intero connector se `R-109` |
| **T-AP-03** | primo consumatore esterno che chiede notifiche push | `ADR-292` | i webhook si attivano; il contratto è già scritto |
| **T-AP-04** | `external_authz_divergence_rate` sopra soglia | `R-117` | il PDP e i permessi Odoo divergono: **il caso grave è il nostro `ALLOW` scritto nell'audit come valido** |
| **T-AP-05** | gli SSE si chiudono durante l'attesa di approvazione. **Previsto come il primo a scattare, per natura del sistema, non per carico** | `ADR-286` | keep-alive, o si accetta il polling come unico canale |
| **T-AP-06** | viene richiesto un **secondo connector** | `ADR-293`, `AS-67` | **è il momento in cui `AR-020` è soddisfatta davvero** e l'astrazione si può costruire |
| **T-AP-07** | `Q-01` risponde con un CRM diverso da Odoo | tutta la §23 di `A18` | **il costo vero non è il connector: è `ADR-161`/`AS-35a`**, cioè l'idempotenza costruita sull'external ID |
| **T-AP-08** | latenza misurata sulla superficie esterna | `ADR-285` | rivalutazione di `?wait=` |
| **T-AP-09** | primo deployment multi-nodo | `ADR-289`, `ADR-296` | PostgreSQL come trasporto interno non basta più |
| **T-AP-10** | il rate limiting su PostgreSQL mostra contesa | `AS-65`, `R-116` | meccanismo diverso; ricerca `B-119` |

> ~~**Previsione (`A05`):** il primo trigger di inference a scattare sarà `T-MD-04`, e non per
> carico ma **per roadmap** — l'embedding model di `A07` arriva fra due documenti.~~
> **SMENTITA da `A07`:** l'embedding model non è "un secondo modello reale" sull'inference
> server, perché `ADR-068` lo mette su CPU in un processo separato. `T-MD-04` non scatta.
> Al suo posto `A07` prevede **`T-KN-01`** come primo trigger di knowledge — non per volume,
> ma al primo uso interattivo serio, quando la latenza di embedding della query si vede.

> **Previsione (`A02` §32):** il primo trigger a scattare sarà `T-CP-02`, e non per carico
> ma per **esposizione**, alla prima installazione presso un cliente.
>
> **`T-GP-02` richiede una metrica che `A12` deve fornire:** *tasso di approvazione concessa
> senza modifiche, per classe di azione*. Senza quella metrica, `ADR-023` resta bloccato sul
> livello restrittivo per sempre.

---

## 9c. Decisioni esplicitamente rimandate

Stato `NON ANCORA DECISO`. Nessuna va trasformata in decisione implicita.

| ID | Decisione | A chi tocca |
|---|---|---|
| DEF-01 | quale policy evaluator concreto | `A03` (dipende da `B-02`) |
| DEF-02 | chunking e modello di embedding | **chiusa in parte da `A07`**: il chunking è deciso (`ADR-075`), la **forma** del modello di embedding è decisa (`ADR-087`: su CPU, multilingua it/en, open-weight, con criterio di ammissione e selezione scritto). Resta `NON ANCORA DECISO` **il checkpoint concreto**, che dipende da `B-27`. **Scadenza: prima dello schema del database** |
| DEF-03 | quali tool CRM esistono | `A06`, `A18` (dipende da `Q-01`) |
| DEF-04 | schema della memoria a lungo termine | **CHIUSA da `A08`** (`ADR-095`): due tabelle applicative — `memory` (record versionati per supersessione) + `memory_audit` (append-only, identificatori e hash, mai testo) — più `run_summary` e `conversation`. Bocciate `MemoryVersion`, `MemoryScope` come tabella, `MemorySource`, `MemoryEvent`, `MemoryEmbedding` |
| DEF-05 | soglie di capacità e piano di scaling | `B21` |
| DEF-06 | RPO / RTO | `C24` (dipende da `Q-02`) |
| DEF-07 | se e quando introdurre multi-agent | **CHIUSA da `A10`, in due metà.** *Specializzazione*: disponibile **Day-1** via `Agent`/`AgentVersion`/`Binding`, scelta dal codice applicativo (`ADR-124`). *Comunicazione agent→agent*: **NO Day-1** (`ADR-123`). Riapertura solo per `T-AC-01` (degrado misurato della tool selection, dopo i rimedi più economici) o `T-AC-09` (`A13` richiede separazione dei privilegi), **e in entrambi i casi solo dopo la chiusura di `R-41`** (`AR-AC-22`) |
| DEF-08 | formato dell'export di audit | `A16`, `C26` |
| DEF-09 | se fare fine-tuning e su cosa | fuori da Level A |
| DEF-10 | modello di deployment commerciale | `A15`, `B19` (dipende da `Q-03`) |
| **DEF-13** | **PARZIALMENTE CHIUSA il 2026-08-23**: il **testo libero di conversazione è a 30 giorni** (`ADR-256`), allineato alla convergenza dei maggiori. Restano aperti gli altri valori concreti di retention per categoria. Il criterio è scritto per ciascuna; **mancano i numeri**. Nessun periodo è fissabile citando una norma: l'unico obbligo citabile (art. 2220 c.c., decennale) riguarda le scritture contabili, che Day-1 **non deteniamo** (`ADR-217` + `ADR-223`) | **il committente**, con parere legale. Input tecnici da `B-95`, `B-96`, `B-102`, `B-88`. **Scadenza: prima dello schema del database** — determinano il partizionamento |
| DEF-11 | promozione **automatica** di traiettorie a workflow | futuro — richiede dati che non abbiamo |
| DEF-12 | forma delle proposte di lavoro in blocco ("sto per mandare 4.000 email, confermi?") | dipende da `Q-01` |
| **DEF-14** | il valore di `k` (ripetizioni) e le soglie di regressione per i gate probabilistici | `A17`, dopo la calibrazione di §9.2. **Scadenza: prima del terzo rilascio**, altrimenti `R-106` |
| **DEF-15** | la dimensione minima del golden set del retrieval e del failure corpus | dipende da `B-83` e `B-106`. **Scadenza: prima dell'attivazione del retrieval** (`ADR-283`) |
| **DEF-16** | quale strumento di load testing | rimandata: non serve Day-1, e `DEF-05` (soglie di capacità) è aperta |
| **DEF-17** | se il judge di `ADR-179` gira sullo stesso modello o su uno diverso | dipende da `B-77`, `B-78`, `AS-08` |
| **DEF-18** | **condizionale**: se il protocollo `AS-40` classificasse molti casi come `P`/`N`, quale meccanismo per i compiti di giudizio, sapendo che `ADR-179` vieta al judge di essere un gate | si apre **solo** se il protocollo di §8.2 (`A17`) dà quell'esito |
| **DEF-19** | la **sequenza di costruzione** delle 145 voci del registro se il tempo basta solo per metà: quale metà | `A16`. *Dichiarata in `A17` §31.2 come omissione riconosciuta* |
| **DEF-20** | token streaming su una superficie conversazionale **read-only** (dove `ADR-287` non si applica, perché non c'è niente da approvare) | `A18`, dopo il primo consumatore reale |
| **DEF-21** | **tutti i valori numerici della superficie**: rate limit, quote, `wait` massimo, timeout, budget di chiamate esterne, finestra di deprecazione | `A18`. **I criteri sono scritti, i numeri mancano, e nessuno è stato inventato.** Scadenza: prima del primo tenant reale. Dipende da `B-116`, `B-119` |
| **DEF-22** | la soglia oltre la quale un `ToolResult` diventa un riferimento invece di un valore | `A18` / `A06`, alla prima misura reale |

---

## 9d. Checkpoint per documento

### A01 — Architecture Principles

| Campo | Contenuto |
|---|---|
| **PURPOSE** | costituzione architetturale: decomposizione, autorità, persistenza, sostituibilità |
| **KEY DECISIONS** | ADR-001…ADR-010; regole AR-001…AR-036; 4 piani; PEP inline |
| **REJECTED** | microservizi · Temporal · OPA/Cedar Day-1 · Redis · vector DB dedicato · MCP come transport · Model Router come componente · LangChain nel core |
| **NEW INTERFACES** | `ModelProvider.complete()` · `ToolRuntime.invoke()` · `PDP.decide()` · repository per aggregato · evento di audit |
| **NEW CONSTRAINTS** | `tenant_id` ovunque · `trust_class` · capability congelato · budget per run · fail closed |
| **NEW RISKS** | R-01…R-11 (§7 di questo file) |
| **NEW ASSUMPTIONS** | AS-01…AS-05 |
| **MAY NEED REVISION** | il Tool Layer generico (dipende da `Q-01`); `ADR-003` dipende dal benchmark pgvector (`B-05`) |
| **IMPACT ON FUTURE** | vincola tutti i documenti successivi; `A02`-`A04` ne implementano i piani |
| **DAY-1** | 3 ruoli · PostgreSQL · step journal · PEP/PDP · Tool Registry · OTel · audit |
| **FUTURE** | HA · multi-tenant fisico · MCP · A2A · fallback cloud · DR |
| **ADR CANDIDATES** | tutti e 10 formalizzati |
| **CONFIDENCE** | **Alta** su decomposizione, autorità e riproducibilità. **Media** su `ADR-003` (pgvector non verificato) e sul Tool Layer (requisiti CRM ignoti) |

### A02 — Control Plane

| Campo | Contenuto |
|---|---|
| **PURPOSE** | dove vive la configurazione: modello risorse, versioning, come il runtime la ottiene |
| **KEY DECISIONS** | Control Plane embedded · **Config Snapshot** (il meccanismo centrale) · niente riconciliazione · 12 risorse · versioni immutabili + binding · tenant di sistema · niente registrazione worker · concorrenza ottimistica |
| **REJECTED** | servizio dedicato Day-1 · riconciliazione Kubernetes-style · controller/watch/finalizer · Workflow/Prompt/Environment/Worker/Evaluation Registry · risorsa `Deployment` · `tenant_id NULL` · semver · segreti nel Control Plane |
| **NEW INTERFACES** | `resolve(tenant, agent, environment) → ConfigSnapshot` — **unico** punto di contatto CP↔EP · `/v1/admin/*` con `ETag`/`If-Match` · `/v1/admin/resolve/preview` |
| **NEW CONSTRAINTS** | il runtime non scrive mai nel Control Plane (applicato dal DB) · nessuno snapshot parziale · `reason` obbligatorio su rollout/rollback/kill switch · niente configurazione senza tipo |
| **NEW RISKS** | l'API amministrativa condivide il processo con quella di runtime: una RCE sull'`api` espone l'amministrazione (→ `T-CP-02`) |
| **NEW ASSUMPTIONS** | le modifiche di configurazione sono rare rispetto al volume di esecuzione (base della concorrenza ottimistica e dell'audit completo) |
| **MAY NEED REVISION** | `Model`/`ModelVersion` forse sovradimensionato con un modello solo · nessuna validazione **semantica** della configurazione (mitigata solo da anteprima e rollback finché non esiste `A17`) |
| **IMPACT ON PREVIOUS** | rafforza `A01` §25 (riproducibilità): lo snapshot è il meccanismo concreto. Risolve la tensione apparente snapshot vs revoche con l'**intersezione** (`A02` §12.3) |
| **IMPACT ON FUTURE** | `A03` eredita il Policy Registry e la doppia frequenza di lettura · `A04` eredita il ConfigSnapshot come input del run · `A05`/`A06` ereditano Model/Tool Registry · `A15` eredita il modello di deployment come binding |
| **DAY-1** | 12 tabelle · resolver · CRUD · audit delle modifiche · nessuna console |
| **FUTURE** | Opzione D (gestione separata) · cache · canary · console · fleet management |
| **ADR CANDIDATES** | `ADR-011` … `ADR-018` |
| **CONFIDENCE** | **Alta** su Config Snapshot, versioning e tenancy. **Media** sul numero esatto di risorse (`B-09` non verificato) e sul rifiuto della riconciliazione (`B-10` non verificato — ma l'argomento non dipende da fonti esterne) |

### A03 — Governance e Policy

| Campo | Contenuto |
|---|---|
| **PURPOSE** | dove vive l'autorità, come si decide, come si impedisce il bypass |
| **KEY DECISIONS** | autorità = **intersezione di 5 insiemi** · PDP **funzione pura** · decisione = **effetto + obbligazioni** · precedenza a imbuto · tenant come invariante del motore · approvazione su ogni `SIDE_EFFECT` Day-1 · cache per versione |
| **REJECTED** | Governance Plane separato · PDP che legge dati · decisione booleana · eredità dell'autorità dell'utente · ReBAC/OpenFGA come motore · TTL sulla cache · break glass che salta il PDP · fail-terminal sui guasti |
| **NEW INTERFACES** | `PDP.decide(request, bundle) → Decision` (puro) · `POST /v1/admin/policies/simulate` · `POST /v1/admin/policies/explain` · `GET /v1/runs/{id}/decisions` · `POST /v1/approvals/{id}` |
| **NEW CONSTRAINTS** | 23 regole `AR-GP-*` · 8 policy di piattaforma Day-1 · `INDETERMINATE` retryable · consumo budget atomico con lo step |
| **NEW RISKS** | **composizione di azioni lecite** (`export` + `send` = esfiltrazione): non risolto strutturalmente, compensato dall'approvazione umana · troppa approvazione può rendere l'agent inutile (`T-GP-02`) |
| **NEW ASSUMPTIONS** | il numero di policy resta leggibile da una persona (decine, non centinaia) · gli attributi necessari alla decisione sono pre-caricabili |
| **MAY NEED REVISION** | l'assegnazione dei tool alle `risk_class` va rifatta quando `A06` avrà l'elenco reale (dipende da `Q-01`) · le difese sono costruite su 2 rischi OWASP su 10 (`B-01` aperto) |
| **IMPACT ON PREVIOUS** | conferma e raffina `A01` §24 (il principio di sicurezza) · usa `ADR-012` (Config Snapshot) come fonte del capability set |
| **IMPACT ON FUTURE** | `A04` deve implementare gli stati `WAITING_FOR_APPROVAL`, `RETRYABLE`, `EXPIRED` · `A06` eredita `risk_class` e permessi sui tool · `A12` deve fornire la metrica di `T-GP-02` · `A13` deve chiudere `B-01` **prima** e affrontare il problema della composizione · `C28` estende l'approvazione |
| **DAY-1** | PDP puro testato a tabella · PEP unico · PIP · 8 policy · 4 esecutori di obbligazioni · audit con spiegazioni |
| **FUTURE** | simulazione su storico · modalità shadow · Cedar/OPA · taint tracking |
| **ADR CANDIDATES** | `ADR-019` … `ADR-026` |
| **CONFIDENCE** | **Alta** su PDP puro, obbligazioni e intersezione. **Media** su `ADR-023` (giusto ora, va allentato con i dati). **Bassa** sulla copertura del threat model finché `B-01` è aperto |

### A04 — Agent Runtime

| Campo | Contenuto |
|---|---|
| **PURPOSE** | il motore che porta avanti un run: chi decide il prossimo passo, cosa si registra, come si riprende |
| **KEY DECISIONS** | loop `OBSERVE→DECIDE→AUTHORIZE→EXECUTE→RECORD` · **6 moduli su 21 nomi candidati** · tre modi di esecuzione · **scrivi prima di agire** · `UNCERTAIN` come stato reale · verifica strutturale ≠ semantica · parallelismo solo in lettura · irreversibili in fondo |
| **REJECTED** | plan-execute-verify · componente Planner · Verifier unico · Model Router · Tool Router · State/Retry/Timeout/Cancellation/Budget/Approval Manager come componenti · backtracking · parallelismo in scrittura · cancellazione forzata · compensazione automatica dei side effect |
| **NEW INTERFACES** | `next_step(run, snapshot, journal) → StepProposal` · `StepProposal → AuthorizedStep` (solo via PEP) · dichiarazioni sul tool: idempotenza/verificabilità/compensabilità |
| **NEW CONSTRAINTS** | 16 regole `AR-RT-*` · state machine a 13 stati · un worker per run · transazione unica per esito+audit+budget |
| **NEW RISKS** | **il codice di recovery è il rischio più concreto dell'architettura** (`R-06` di `A01`, confermato e alzato di priorità) · `WORKFLOW`/`HYBRID` potrebbero non servire mai se i compiti non si stabilizzano · composizione di azioni lecite resta aperta anche qui |
| **NEW ASSUMPTIONS** | i compiti CRM si stabilizzano in pattern ricorrenti (base di `ADR-028`, **non verificata**, dipende da `Q-01`) · `UNCERTAIN` è raro |
| **MAY NEED REVISION** | `ADR-028` se i compiti non si stabilizzano (violerebbe `AR-020`) · `ADR-002` se il recovery si rivela fragile (`T-RT-06`) |
| **IMPACT ON PREVIOUS** | conferma `ADR-002` ma ne alza il rischio · `AR-RT-05` precisa `AR-026` (il retry non cambia lo `step_index`) · scopre un **quinto uso** dello step journal: la promozione a workflow |
| **IMPACT ON FUTURE** | **`A06` deve** far dichiarare a ogni tool idempotenza/verificabilità/compensabilità · **`A08` deve** definire la compattazione del journal per il context · **`A11` eredita** i tre modi e `AR-RT-12` · **`A12` deve** fornire metriche di `UNCERTAIN`, attesa di approvazione, traiettorie · `C29` usa il journal per il replay · `C31` (A2A): gli stati sono compatibili |
| **DAY-1** | solo modo `AGENTIC` · 6 moduli · state machine · journal · recovery con test che uccidono il worker · 3 rilevatori di loop |
| **FUTURE** | `HYBRID`/`WORKFLOW` a `T-RT-02` · promozione automatica (`DEF-11`) · taint tracking nel journal |
| **ADR CANDIDATES** | `ADR-027` … `ADR-035` |
| **CONFIDENCE** | **Alta** su loop, journal, state machine e modello degli errori. **Media** su `ADR-028` (dipende da `Q-01`). **Bassa** sulla correttezza del recovery finché non è testato uccidendo processi |

### A05 — Model e Inference

| Campo | Contenuto |
|---|---|
| **PURPOSE** | dove passa il confine fra runtime e inference, cosa lo attraversa, cosa succede quando si rompe |
| **KEY DECISIONS** | **due serving profile, un contratto** (vLLM + llama.cpp → `AR-020` soddisfatta davvero) · serving come processo separato · `max_model_len` come decisione di **capacità** · 4 bit con **gate agentico** · structured output a **doppio anello** · il prompt è **tre sorgenti versionate** · riproducibilità dell'**evidenza** · niente gateway/router/fallback · multi-GPU = worker indipendenti |
| **REJECTED** | Ollama (nasconde i parametri che l'audit richiede) · Triton · Transformers diretto · TGI · SGLang (rinviato, **candidato n.1 alla sostituzione**) · in-process · Model Gateway · fallback automatico · `Prompt Registry` · troncamento automatico · F16 · Q3 |
| **NEW INTERFACES** | `ModelProvider.complete()` / `.stream()` · `ModelRequest` **senza** `model_id` (viene dallo snapshot, mai dal chiamante) · `ModelResponse` con `decoding_params_effective` (ciò che è stato applicato, non ciò che è stato chiesto) · `ModelCapabilities` **verificate da un probe**, non dichiarate · 8 codici di errore tipizzati |
| **NEW CONSTRAINTS** | `AR-MD-01` … `AR-MD-15` |
| **NEW RISKS** | `R-12` … `R-16` |
| **NEW ASSUMPTIONS** | `AS-06`, `AS-07`, **`AS-08` (un solo modello sulla GPU) — la più urgente** |
| **MAY NEED REVISION** | la scelta del serving runtime è la decisione **meno solida** (`B-12`/`B-15` aperti), mitigata dal fatto che è la più facilmente reversibile · quasi ogni numero è `ASSUNZIONE` finché non si misura |
| **IMPACT ON PREVIOUS** | chiude l'autocritica di `A02` (`Model`/`ModelVersion` **non** collassa: l'argomento è il rollout N-a-1 sulle `AgentVersion`, che `A02` non aveva visto) · il prompt versionato **non** richiede il `Prompt Registry` respinto da `A02` · `ADR-042` ridefinisce la promessa di `A01` §25 in ciò che quella sezione elencava davvero |
| **IMPACT ON FUTURE** | **`A06`**: le tool definition occupano il prefisso → budget e prefix caching · **`A07`**: deve chiudere **`AS-08` prima delle misure** · **`A08`**: riassunti sotto una **soglia numerica**, non "brevi" · **`A12`**: `portability_delta`, `malformed_rate`, `hallucinated_tool_rate`, `refusal_rate`, correlazione con `run_id` · **`A15`**: container senza rete, volume read-only · **`A16`**: capability probe + eval suite come gate di rilascio · **`A17`**: eval suite agentica, **mai** confronti di output esatti · **`C27`** parte da `ADR-044` · **`C29`**: replay sul **journal**, non sulla rigenerazione |
| **ADR CANDIDATES** | `ADR-036` … `ADR-047` |
| **CONFIDENCE** | **Alta** su confine, contratto, doppio anello, tre sorgenti del prompt, failure mode. **Media** su bilancio VRAM e quantizzazione. **Bassa** sulla scelta del serving runtime finché `B-12`/`B-15` sono aperti — vLLM parte avvantaggiato perché è l'unico su cui la ricerca è stata fatta, non perché sia dimostrato superiore |

### A06 — Tool Architecture

| Campo | Contenuto |
|---|---|
| **PURPOSE** | dove l'agent tocca il mondo. Principio-spina: **nessun argomento di tool può essere un programma** |
| **KEY DECISIONS** | un tool = **una decisione di autorizzazione** · niente SQL, sostituito da ricerca strutturata + query salvate + `missing_capability_rate` · Tool Runtime in-process · definizione immutabile / implementazione no, con gap **registrato** · 13 regole di schema design per un 9B · **set di tool costante nel run** (per non uccidere il prefix caching) · budget del prefisso che fa fallire `resolve()` · il tool riceve un **client già autenticato** · `side_effects` a 8 tipi · l'errore lo classifica il connector · MCP con **materializzazione umana obbligatoria** |
| **REJECTED** | mega-tool `crm(action,data)` · `execute_sql` (anche read-only su replica) · `http_request(url)` generico · Tool Gateway Day-1 · MCP-first · progressive disclosure sui tool · agent-come-tool · health check attivi · semver · modello dati canonico multi-CRM · cache dei risultati |
| **NEW INTERFACES** | `ToolVersion` esteso · `ToolInvocation` con `args_model`/`args_injected` **separati** · `ToolResult` con provenance e `trust_class` · `ToolContext` con client pre-autenticato · `CredentialResolver` · **`ToolBinding`** (risorsa nuova) |
| **NEW CONSTRAINTS** | `AR-TL-01` … `AR-TL-16` |
| **NEW RISKS** | `R-18` … `R-23` |
| **NEW ASSUMPTIONS** | `AS-09` decine di azioni nominabili (Media) · **`AS-10` un 9B a 4 bit regge decine di tool (Bassa, non verificata)** · `AS-11` i CRM offrono idempotency key o marcatore (dipende da `Q-01`) · `AS-12` Day-1 tutti i tool sono nostri (**condizione sociale, non tecnica**) |
| **MAY NEED REVISION** | `ADR-054` se `denied_after_selection` costasse molto · la soglia di `ADR-055` è `NON ANCORA DECISO` · **tutta la §14 (schema design) è INFERENZA da validare** · `ADR-049` sotto osservazione di `T-TL-06` |
| **IMPACT ON PREVIOUS** | soddisfa i mandati che `A04` aveva rimandato (`AR-RT-04`, `AR-RT-11`) · rende **operativo** `ADR-035` (senza `compensability` il runtime non poteva ordinare le irreversibili) · aggiunge `ToolBinding` al pattern di `ADR-015` · due tensioni dichiarate e risolte a monte, **nessun ADR precedente rivisto** |
| **IMPACT ON FUTURE** | **`A07`: retrieval come canale separato, non come tool** · **`A08`**: il riassunto del journal deve preservare gli identificatori osservati, altrimenti `AR-TL-06` cade · `A09`: contratto del secret store · `A11`: eredita `ADR-065` e usa `compensability` · **`A12`**: 6 metriche nuove, `schema_failure_rate` **per campo** · **`A13`**: rivedere il threat model dopo `B-01`+`B-25`, affrontare `R-17` e `R-19` · `A15`: allowlist anche a livello di rete del container · `A16`: contract test come gate di rilascio · `A17`: schema usability test + live smoke test · `C07` parte da `ADR-063` · `C31` da `ADR-064` |
| **ADR CANDIDATES** | `ADR-048` … `ADR-066` |
| **`Q-01`** | non cambia nulla di strutturale; cambiano **10 cose concrete** se "Odoo e solo Odoo". La principale: **l'API di Odoo è nativamente il mega-tool che abbiamo respinto** (`execute_kw`), quindi il valore del layer diventa **restringere** invece di astrarre. `AR-RT-04` si soddisferebbe via **verificabilità**, non idempotenza. **Raccomandazione: se `Q-01` tarda, cominciare da Odoo** — l'astrazione generica senza due implementazioni reali violerebbe `AR-020` |
| **CONFIDENCE** | **Alta** su confine Registry/Runtime, contratto, credenziali, tassonomia errori, confine MCP/A2A. **Media** su granularità e `ADR-049` (poggiano su `AS-09` non verificata, ma `T-TL-06` è progettato per falsificarli). **Bassa** su tutta la §14 e sul numero di tool sostenibile (`B-20` aperto). **Bassa** sul threat model finché `B-01`/`B-25` sono aperti |

### A07 — Knowledge e Data

| Campo | Contenuto |
|---|---|
| **PURPOSE** | da dove viene l'informazione su cui l'agent ragiona: chi possiede il dato, cosa si indicizza, come si recupera, chi ha diritto di vederlo |
| **KEY DECISIONS** | **due percorsi** (dato strutturato dal vivo via `Tool`, documenti indicizzati) · **embedding su CPU, zero VRAM** (chiude `AS-08`) · autorizzazione a **tre strati** con pre-filtro autoritativo **in query** · ACL **per riferimento** con fail closed sulla staleness · **cinque entità** di documento · retrieval ibrido con **fusione per rank** · frammenti **in coda al prompt**, append-only per run · audit per identificatori e hash, **mai testo** · tutto il derivato **ricostruibile** · **golden set Day-1** |
| **REJECTED** | vector DB dedicato · motore di ricerca separato · knowledge graph · semantic layer / MDM · data lake · persistenza poliglotta · reranker Day-1 · cache dei risultati · copia sincronizzata del CRM · CDC · webhook Day-1 · OCR · email nella KB · embedding su GPU / via API esterna / col modello di generazione · query rewriting automatico · trust score calcolati · blob in `bytea` |
| **NEW INTERFACES** | `RetrievalLayer.retrieve(RetrievalQuery, RetrievalScope) → RetrievalResult` · `Retriever.search()` (**due implementazioni Day-1 → `AR-020` soddisfatta davvero**) · `EmbeddingProvider.embed()` · `BlobStore.put/get(content_hash)` · `DocumentSource.list_changes/fetch` · **`RetrievalScope` prodotta dal PDP** · `Fragment` con provenance a 11 campi obbligatori |
| **NEW CONSTRAINTS** | `AR-KN-01` … `AR-KN-22`. Le più vincolanti: `AR-KN-02` (filtro in query), `AR-KN-04` (niente provenance → niente context), `AR-KN-07` (tutto ricostruibile, test in CI), `AR-KN-09` (fail closed su ACL obsolete), `AR-KN-10` (frammenti in coda), `AR-KN-16` (ingestion mai sulla GPU), `AR-KN-20` (niente recall senza golden set) |
| **NEW RISKS** | `R-24` … `R-32` |
| **NEW ASSUMPTIONS** | `AS-13` (Media) · **`AS-14` embedding su CPU sufficiente (Bassa)** · `AS-15` ACL proiettabili (Media, dipende da `Q-01`) · **`AS-16` volume ~10⁴–10⁵ chunk (Bassa)** · `AS-17` cursore di modifiche (Media) |
| **MAY NEED REVISION** | `ADR-068` se `B-26` va male · **`ADR-073` (blob fuori dal DB) è la più contestabile**: `AR-019` non ha una misura · `ADR-085` (email fuori) se il committente la vuole · `ADR-087` parziale finché `B-27` è aperto · copertura solo parziale di `AR-GP-17` · `DataSource` come risorsa toccherebbe `ADR-014` |
| **IMPACT ON PREVIOUS** | **`A05`: `AS-08` confermata, `ADR-039` invariato nel numero** (cambia la ripartizione interna, dichiarata come vincolo verificato al `resolve()`), **la previsione su `T-MD-04` non si avvera** · `A01`: `ADR-003` confermato con perimetro precisato (`ADR-073`); **`INV-07` esteso da "nessun accesso" a "nessuna copia"** · `A03`: il PDP acquisisce `RetrievalScope`, il PIP attributi nuovi, `T-GP-01` più probabile, `AR-GP-17` coperta a metà · `A02`: 5 voci nuove nel `ConfigSnapshot` · `A04`: `OBSERVE` acquisisce un passo, il run un `freshness_requirement` · `A06`: mandato del canale rispettato, `ADR-049` rafforzato |
| **IMPACT ON FUTURE** | **`A08`**: il budget del riassunto compete col retrieval; va tracciato il confine knowledge/memory · **`A12`**: 18 metriche correlate a `run_id`, senza le quali `T-03` e `T-KN-05` non scattano mai · **`A13`**: `R-26` insieme a `R-17` · **`A14`**: `R-32`, retention, cancellazione per soggetto · **`A15`**: container senza GPU + volume · `A16`/`A17`: test di ricostruzione, golden set, ANN vs scansione esatta · `C24`, `C29` |
| **DAY-1** | 8 tabelle di knowledge + `grant`/`acl_subject`/`entity_link` · RLS · `Blob Store` su filesystem · pipeline a stati persistiti · polling + sweep · `EmbeddingProvider` su CPU · retrieval ibrido con pre-filtro · provenance completa · `retrieval_audit` append-only · **golden set etichettato** · test di ricostruzione in CI |
| **FUTURE** | reranker · embedding su GPU per il backfill · object storage · webhook · vector store o indice partizionato · tool `knowledge_search` accanto al canale · OCR/multimodale · CTE ricorsive poi eventuale grafo · redazione per campo · cancellazione per soggetto |
| **ADR CANDIDATES** | `ADR-067` … `ADR-087` (21). I portanti: `ADR-067`, **`ADR-068`**, `ADR-071`, `ADR-077` |
| **`Q-04`** | resta **aperta**. Risultato controintuitivo dichiarato: **a rompersi per prima non è pgvector, è l'embedding su CPU** (~10⁶ chunk) |
| **CONFIDENCE** | **Alta** su `ADR-067`/`071`/`072`/`074`/`077` e sulla ricostruibilità — poggiano su argomenti interni e invarianti già stabiliti, non su fatti esterni non verificati. **Media** su `ADR-070` (fusione non calibrata), `ADR-075` (parametri), `ADR-081`, `ADR-073` (l'argomento su `AR-019` è di definizione). **Bassa** su **`ADR-068`** finché `B-26` non è misurato, su `ADR-087` finché `B-27` è aperto, su tutto il dimensionamento finché `Q-04` è aperta, e sulla completezza del threat model finché `B-01`/`B-25` sono aperti |

### A08 — Memory

| Campo | Contenuto |
|---|---|
| **PURPOSE** | cosa la piattaforma si ricorda, per quanto, chi può rileggerlo, chi paga i token |
| **IL DEBITO DI `AR-RT-14`, SALDATO** | il context riceve un **digest deterministico generato da codice** (mai dal modello), a tre zone — identifier ledger incomprimibile + finestra recente verbatim + storico compresso a una riga per step — sotto il **15 % di `max_model_len`** in esercizio normale e il **20 %** come limite hard, oltre il quale il run **fallisce** con `CONTEXT_BUDGET_EXCEEDED` invece di troncare |
| **CONFINE KNOWLEDGE/MEMORY** | la knowledge ha una sorgente esterna autoritativa ed è **ricostruibile**; la memoria no, e la piattaforma ne è il `system of record`. Conseguenza dura: **la memoria non contiene mai un fatto di dominio** (`ADR-089`). In sovrapposizione vince sempre la knowledge come autorità |
| **KEY DECISIONS** | tre orizzonti (Working Set / Conversation Trail / Long-Term Memory) · digest deterministico a tre zone · niente fatti di dominio · `MemorySnapshot` **congelato all'avvio** nella zona cacheabile · **lettura come canale, scrittura come tool** · nessuna estrazione automatica attiva (le proposte si registrano e si misurano) · quote di budget + ordine di cessione dichiarato · `trust_class = retrieved` per ogni memoria, `authority` come asse **ortogonale** · supersessione + bi-temporale · tombstone + purge irreversibile |
| **REJECTED** | riassunto generato dal modello · finestra scorrevole pura · memory service separato · vector store · pgvector sulla memoria · grafo · event sourcing · memoria condivisa · consolidamento · `run_summary` generato · campo `importance` · scoring pesato · tool `search_memory` · ACL proiettate stile `ADR-072` |
| **NEW INTERFACES** | `MemoryScope` · `MemorySnapshot` · `WorkingSetBlock` · `MemoryCandidate → CommittedMemory` · `render_working_set()` (**funzione pura**) · tool `memory_write` · 8 endpoint REST · annotazione `x-entity-ref` |
| **NEW CONSTRAINTS** | `AR-ME-01` … `AR-ME-20` (14/20 con verifica automatica, 6 `REVIEWED`) |
| **NEW INVARIANTS** | **`INV-10`** (il digest non perde identificatori, **a prescindere dal budget**) · **`INV-11`** (il set di memoria non cresce durante il run) · **`INV-12`** (il PDP non legge mai `memory`) · `INV-08` esteso alle memorie |
| **NEW RISKS** | `R-33` … `R-40` |
| **NEW ASSUMPTIONS** | `AS-18` (Bassa) · `AS-19` (Media) · `AS-20` (Media) · **`AS-21` gli utenti dichiarano preferenze (Bassa)** · `AS-22` costo del render trascurabile (Media, **gira a ogni step**) |
| **MAY NEED REVISION** | `ADR-091` **Parziale** (dipende da `B-14`) · `ADR-094` è progettata per allentarsi · la classificazione di `memory_write` come **non**-`SIDE_EFFECT` è ribaltabile da `A13` · ~~`AR-ME-13` è giusta per la sicurezza e sbagliata per la scala~~ → **RISOLTA da `ADR-104`**: con `max_steps = 50` il ledger incomprimibile ha una dimensione massima calcolabile, quindi non è più un rischio di scala · il vocabolario delle `key` è senza criterio |
| **IMPACT ON PREVIOUS** | `A04`: **`AR-RT-14` diventa implementabile** · `A06`: **`AR-TL-06` dimostrata valida sotto compattazione** (via `INV-10`), più la richiesta di rivedere i `limit` dei tool di lista · `A07`: **conflitto di budget risolto — i frammenti cedono per primi** (`AR-ME-14`), `AR-KN-10` precisata come ordine relativo, `ADR-068`/`083`/`084` **riusati senza modifiche** · `A03`: `INV-12` blinda il PDP contro il poisoning · `A02`: 6 voci nel `ConfigSnapshot`, `ADR-014` intatto |
| **IMPACT ON FUTURE** | **`A12`**: 18 metriche (una non automatizzabile) · **`A13`**: `R-33`/`R-34` + `B-37`/`B-41` · **`A14`**: le categorie particolari di dati non sono rilevate Day-1 · **`C24`**: la memoria è **irreplaceable** e vincola l'`RPO` · `C29`: replay facilitato · `C31`: `T-ME-07` |
| **DAY-1** | 4 tabelle con RLS · 3 moduli in-process · 1 tool (`memory_write`) · ispezione, correzione, cancellazione, explanation · 3 test su `INV-10` + test di isolamento adversariale + test di iniezione + verifica che gli step `SIDE_EFFECT` restino nel digest |
| **FUTURE** | retention per tipo · `scope = TENANT` · `memory_embedding` **additiva riusando `ADR-068`** · consolidamento · estrazione automatica · digest ibrido · export · crypto-shredding |
| **ADR CANDIDATES** | `ADR-088` … `ADR-103` (16). I portanti: `ADR-089`, `ADR-090`, `ADR-092`, `ADR-095` |
| **CONFIDENCE** | **Alta** su separazione memoria/knowledge/audit/config, `INV-12`, schema minimo, cancellazione, e sulla dimostrazione di `INV-10`. **Media** sulle quote di `ADR-091`, sull'ordine di cessione, sul cap di 32. **Bassa** su `AS-21` (potrebbe portare a **togliere** il terzo orizzonte), su `AS-22`, sulla tenuta del ledger incomprimibile a scala (**il punto più debole**), e sul threat model finché `B-01`/`B-36`/`B-37`/`B-41` sono aperti. **Nessuna ricerca esterna fatta, per vincolo: `B-36`…`B-41` sono il debito che ne consegue** |

### A09 — Identity, Authentication, Authorization

| Campo | Contenuto |
|---|---|
| **PURPOSE** | chi è il soggetto che si presenta alla decisione del PDP, e come si dimostra che è davvero lui |
| **CHI È IL `principal`** | la coppia `(actor = AgentRun, on_behalf_of = HumanSubject \| ServicePrincipal)`. L'autorità è l'**intersezione** delle due, mai l'unione. `on_behalf_of` non è mai vuoto: nessuna azione è orfana |
| **CONTRATTO DEL SECRET STORE** (chiesto da `A06`) | interfaccia a 5 metodi (`get_secret`/`describe_secret`/`put_secret`/`rotate_secret`/`revoke_secret`), chiamabile **solo** dal `Credential Broker`, che ne ricava un `AuthenticatedClient` valido per **un solo `EXECUTE`**. Day-1: tabella PostgreSQL cifrata con chiave **fuori** dal database; l'audit registra il solo `credential_ref` |
| **I PERMESSI SI CONGELANO?** | **No, per metà.** Si congela il **tetto** (capability, tool set, `MemorySnapshot`, `bundle_version`, `scope` della delega); si rilegge a ogni `AUTHORIZE` l'**autorità viva** (stato subject, sessione, delega, ruoli, tenant, freschezza grant). **Costo:** due letture per step → `T-GP-01` più probabile, e `R-43` (una memoria revocata resta nel prompt fino a fine run — finestra ≤ 10 min grazie a `ADR-104`) |
| **COSA È UN `subject_id`** | UUIDv4 opaco, immutabile, generato da noi, globalmente unico, **mai riassegnato**. Tutto ciò che muta (nome, email, ruolo, stato) sta in righe collegate. La fusione di account produce un alias `merged_into` risolto **in lettura**, mai una riscrittura dell'audit |
| **KEY DECISIONS** | dual principal · tetto congelato / autorità viva · `subject_id` opaco · Credential Broker + SecretStore · nessun IdP Day-1 · la sessione è una riga · RBAC per gli attributi, ABAC come motore · `AR-GP-04` riferita alla **sessione** · la delega non è un token · catena 3 Day-1 · `EXTERNAL_IDENTITY_LINK` · service identity via ruoli PostgreSQL · niente SPIFFE · il platform operator non legge i dati · **elevazione dichiarata** invece di break-glass |
| **REJECTED** | agent-come-utente · agent-solo · run-come-contesto · IdP esterno Day-1 · policy engine Day-1 · ReBAC/Zanzibar · JWT di delega · break-glass come bypass · match per email · Organization/Workspace · token universali · cache di decisioni · SAML/SCIM Day-1 · service account unico · inoltro del token utente |
| **NEW CONSTRAINTS** | `AR-ID-01` … `AR-ID-33`. **28 su 33 con verifica automatica** — il rapporto migliore fra i documenti |
| **NEW INVARIANTS** | **`INV-13`** (l'autorità di un run non cresce mai) · **`INV-14`** (nessun `SecretMaterial` fuori da 2 moduli) · **`INV-15`** (ogni decisione auditata porta entrambe le identità) |
| **NEW RISKS** | `R-41` … `R-48`. **`R-41` (confused deputy) è Alta/Alto e NON risolto Day-1** |
| **NEW ASSUMPTIONS** | `AS-23` … `AS-29`. Le più fragili: **`AS-24`** (il CRM non riusa gli ID utente) e **`AS-28`** (`AS-12` regge) |
| **MAY NEED REVISION** | **`ADR-114` è la decisione che il documento stesso confessa contestabile**: la catena 3 è facile da estendere e impossibile da togliere · `AS-24` finché `B-49` è aperto · le durate di sessione e token sono `NON ANCORA DECISO` (`B-44`) |
| **IMPACT ON PREVIOUS** | precisa `AR-018`: il `tenant_id` viene dall'identità **risolta**, mai da un claim · **risolve il conflitto `AR-GP-04` × `ADR-104`** (via `ADR-112`) · dà forma alla delega che `AR-RT-16` presupponeva senza definirla · **rende `AR-ME-18` applicabile**, con un requisito nuovo per `A08`: la lettura della memoria deve risolvere gli alias di fusione (`AR-ID-08`) · **salda il debito del secret store che `A06` aveva assegnato** · conferma `ADR-092`, `T-ME-08`/`T-ME-10`, `D-04`, `T-TL-08` senza duplicarli · **lascia `DEF-01` ad `A03`**, come richiesto |
| **IMPACT ON FUTURE** | **`A11`**: stati `DELEGATION_EXPIRED` e `AUTHORIZATION_LOOP` · **`A12`**: `revocation_effective_latency` e il costo del PIP a ogni step · **`A13`**: `B-42` da chiudere con `B-01` · **`A14`**: retention dei soggetti `DEPARTED` · **`A15`**/`Q-03` |
| **ADR CANDIDATES** | `ADR-105` … `ADR-119` (15) |
| **PREVISIONE** | il primo trigger a scattare sarà **`T-ID-04`** (primo tenant con IdP proprio), **per contratto, non per carico** |
| **CONFIDENCE** | **Alta** su modello di identità, dual principal, `subject_id` e contratto del secret store — poggiano su invarianti interni già stabiliti. **Media** sulle durate e sul costo di `ADR-106` (non misurato). **Bassa** su **`ADR-114`** (dichiarata contestabile dall'autore), su `AS-24` finché `B-49` è aperto, e sul threat model finché `B-01`/`B-42` sono aperti. **Nessuna ricerca esterna, per vincolo: 11 voci di backlog nuove sono il prezzo, e `B-45` blocca l'implementazione** |

### A10 — Agent Communication e Multi-Agent

| Campo | Contenuto |
|---|---|
| **PURPOSE** | se, quando e come un agent debba parlare con un altro; cosa succede a identità, autorità, budget e memoria quando lo fa |
| **`DEF-07` CHIUSA, IN DUE METÀ** | *specializzazione* → **sì, Day-1**, ma come **risorsa** (`Agent`/`AgentVersion`/`Binding` già esistenti), scelta dal codice applicativo. *Comunicazione agent→agent* → **no Day-1**. Riapertura solo su `T-AC-01` o `T-AC-09`, e **mai prima che `R-41` sia chiusa** |
| **IDENTITÀ E AUTORITÀ QUANDO A CHIAMA B** | `actor` = il run figlio; `on_behalf_of` = **la stessa persona della radice, copiata** (`INV-17`); `ceiling(B) = ceiling(A congelato all'avvio) ∩ capability(B) ∩ policy(dispatch)`. Quindi `ceiling(B) ⊆ ceiling(A)` **per costruzione**: l'unione dell'albero resta sottoinsieme della radice all'avvio (`INV-16`). **`INV-13` non solo regge, si rafforza** |
| **I 50 STEP E I 10 MINUTI** | **ledger unico per albero**, di proprietà della radice, decrementato **atomicamente** da qualunque run. Il dispatch costa uno step. Deadline **assoluta** copiata, mai 10 minuti freschi. L'orologio si ferma **solo se tutti** i run non terminati sono sospesi (`ADR-128`, `INV-18`) |
| **KEY DECISIONS** | niente comunicazione agent→agent Day-1 · specializzazione come risorsa · **4 colonne di lineage Day-1, degeneri** · child run e non agent-come-tool · attenuazione con `on_behalf_of` invariante · tetti d'albero · memoria ereditata per riferimento · task asincrono persistito, **trasporto = database** · A2A come adapter di confine · nessun registry nuovo · discovery **statica** · approvazione chiesta da chi esegue · 4 barriere anti-loop **deterministiche** · niente sandboxing fra agent nostri · tracing standard · niente event bus · cross-tenant vietato · artifact per riferimento |
| **REJECTED** | supervisor/worker Day-1 · gerarchia · **peer-to-peer** ed **event-driven** (in cui `INV-13` è *inesprimibile*, non solo rischioso) · A2A come transport interno · A2A come meccanismo di delega · agent-come-tool · Agent Registry separato · discovery dinamica · negoziazione di schema · streaming fra agent · entità `Artifact` · marketplace · federazione · budget per run · timeout relativi · `on_behalf_of` = agent chiamante · snapshot memoria risolto dal figlio · broker |
| **NEW INTERFACES** | `AgentTask` (tipizzato, **un solo campo libero** per il modello) · `AgentResult` (`trust_class = retrieved`) · `AgentDispatcher.dispatch()` · `TreeLedger` · A2A Adapter. **Day-1: nessuna** |
| **NEW CONSTRAINTS** | `AR-AC-00` … `AR-AC-25` (26; **19 `ENFORCED`**, 7 `REVIEWED`) |
| **NEW INVARIANTS** | `INV-16` · `INV-17` · `INV-18` · `INV-19`. Più `INV-11` esteso all'albero e `INV-08` esteso agli `AgentResult` |
| **NEW RISKS** | `R-49` … `R-57`. Critici: **`R-50`** (tetto per run invece che per albero → la catena compra budget), **`R-57`** (assumere che A2A dia l'attenuazione), `R-53` (frammentazione del prefix cache) |
| **NEW ASSUMPTIONS** | `AS-30` (Media) · **`AS-31` Bassa — è ciò su cui poggia il rifiuto** · **`AS-32` Bassa** · `AS-33` (Media) |
| **MAY NEED REVISION** | ~~`ADR-123` se `B-20`/`B-58` mostrassero…~~ → **`B-58` chiusa il 2026-08-23 (`R-11`): `ADR-123` è confermata e la sua confidenza sale ad Alta**, con un argomento nuovo e più forte (capacità, non economia). Resta aperto `B-20` e nasce `B-66` · i valori di `ADR-135` sono `NON ANCORA DECISO` · la `MemoryScope` del dispatch (`B-65`) · l'attenuazione attraverso rete (`C31`) · `ADR-136` cade al primo agent non nostro |
| **IMPACT ON PREVIOUS** | **nessun ADR precedente rivisto o contraddetto.** `ADR-064` confermato con un argomento nuovo · `INV-13` generalizzato · `ADR-105` esteso senza modifiche · **`AR-ID-04` intatta** (una catena di run non è una catena di deleghe: `DelegationContext` unica per albero) · `ADR-104` precisato in `ADR-128` · **`T-ME-07` chiuso in anticipo** da `ADR-129` · `AS-08` blindata da `AR-AC-07`. **Problema nuovo scoperto:** le Multi Round-Trip di MCP potrebbero erodere `ADR-064` **dalla porta dei tool** → `B-64`, `AR-AC-24` |
| **IMPACT ON FUTURE** | **`A11`**: ripresa del padre, cancellazione, ledger, 4 codici d'errore — *mandato dichiarato, durable execution non invasa* · **`A12`**: 8 metriche, 2 delle quali bloccanti (senza, `ADR-123` non è falsificabile) · **`A13`**: `R-51`, `R-52`, `B-60`, `T-AC-09` · `A16`/`A17`: 2 test CI · **`A18`**: "due run in sequenza" è il sostituto del multi-agent · `C07` (`B-64`), `C31`, `C28` |
| **DAY-1** | 4 colonne su `run` + audit, `root_run_id` in `memory_audit`, 3 test CI, `agent_id` esplicito su `POST /v1/runs`. **Zero componenti, zero protocolli, zero servizi** |
| **FUTURE** | `AgentDispatcher` in-process · ledger d'albero · 4 barriere · ripresa e cancellazione durevoli · A2A adapter · isolamento a processo |
| **ADR CANDIDATES** | `ADR-123` … `ADR-140` (18) |
| **PREVISIONE** | il primo trigger a scattare sarà **`T-AC-03`** (interoperabilità con un agent esterno), **per contratto, non per carico** — stessa logica di `T-ID-04` |
| **CONFIDENCE** | **Alta** su `INV-16`/`17`/`19`, attenuazione, tetti d'albero, `ADR-125`, `ADR-139` — poggiano su invarianti interni già stabiliti. **Alta anche su `ADR-123`** dopo la chiusura di `B-58` (`R-11`, 2026-08-23): cinque fonti primarie convergenti, di cui due studi controllati a protocollo e budget appaiati. **Contro-segnale registrato onestamente in `AS-31b`/`AS-31c`**: i due regimi in cui la letteratura dice che il multi-agent recupera — modello piccolo e context degradato — sono **entrambi i nostri**. **Media** su `ADR-129`/`ADR-134` (corretti rispetto agli invarianti, non provati sull'uso). **Bassa** su tutta la fase 3 (A2A), sul recovery di un albero (deliberatamente mandato ad `A11`) e sul threat model finché `B-01`/`B-25`/`B-42`/`B-60` sono aperti |

### A11 — Eventing, Workflow, Durable Execution

| Campo | Contenuto |
|---|---|
| **PURPOSE** | cosa succede al run quando il processo muore a metà. È il documento che possiede il **ciclo di vita** |
| **QUALE MOTORE DI DURABLE EXECUTION** | **nessuno** (`ADR-141`). Argomento nuovo e più forte di quello economico: dai FATTI di `R-04`, l'exactly-once di DBOS vale **solo se lo step scrive sullo stesso PostgreSQL del workflow**. I nostri effetti atterrano su Odoo (`INV-07`) → compreremmo un secondo system of record **per una garanzia che sul confine che conta non ci verrebbe data**. Temporal respinto. **DBOS/`pg_durable` sono i candidati n.1 al futuro** via `T-EV-04` |
| **COME SI MISURA IL TEMPO ATTIVO** | **è un contatore, non un intervallo** (`ADR-145`): `run_tree.active_ms_consumed`, incrementato **solo da chi tiene un lease**, a ogni heartbeat. Quando tutti i run sono sospesi nessuno tiene un lease, quindi nessuno paga: l'orologio **non "si ferma", non esiste** |
| **COME SI DISINNESCA `R-50`** | tre strati: (1) il campo budget **non esiste** su `run`, solo una FK verso `run_tree`; (2) il consumo lo fa un **trigger di database** (`ADR-146`), inaggirabile da qualunque percorso applicativo; (3) **`INV-20`** rende il tutto una query verificabile → test su albero di profondità 3, il 51° step fallisce **ovunque si trovi** |
| **STEP `SIDE_EFFECT` INTERROTTO** | `ADR-144`, tre scritture `PENDING → IN_FLIGHT → esito`, con `IN_FLIGHT` committato **nell'istante prima del primo byte**. Quattro esiti al recovery: `PENDING` → riesegui · `IN_FLIGHT` + idempotente → riesegui con la **stessa** chiave · `IN_FLIGHT` + verificabile → **probe** (che è uno step e paga dal ledger) · altrimenti → `UNCERTAIN` → `ESCALATED`, **mai** riesecuzione |
| **DELEGA SCADUTA ALLA RIPRESA** | `EXPIRED` con ragione `DELEGATION_EXPIRED`, nessun altro passo, messaggio che include **cosa è già stato fatto**. Rimedio: **run nuovo, mai una ripresa** — e infatti **non esiste il comando `ResumeRun`** |
| **KEY DECISIONS** | nessun engine · `job` distinto dal `run`, un pool solo · lease con fencing token · protocollo a tre scritture · tempo attivo come contatore · ledger consumato da trigger · niente event sourcing · niente event bus · outbox minimale a riferimenti · niente inbox Day-1 · scheduler come ruolo con advisory lock · timer come righe · retry a policy (consuma tempo, non step) · niente compensazione automatica · ragioni terminali invece di stati nuovi · ripresa per risveglio idempotente · cancellazione per albero + `tree_reaper` · priorità e cap per tenant nella query di prelievo · drain ai confini di passo · nessun ordine globale degli eventi |
| **REJECTED** | Temporal · engine dedicati Day-1 · event sourcing · event bus / broker / coda in memoria · inbox Day-1 · attese in memoria · compensazione automatica · stati nuovi nella macchina · comando `ResumeRun` · ordinamento globale · sostituzione silenziosa di versione |
| **NEW CONSTRAINTS** | `AR-EV-01` … `AR-EV-31` (**24 su 31 automatiche** — il rapporto più alto insieme ad `A09`) |
| **NEW INVARIANTS** | **`INV-20`** (il ledger è verificabile con una query) · **`INV-21`** (nessun byte parte senza una riga committata) · **`INV-22`** (un solo lease per unità di lavoro) · **`INV-23`** (nessun run può essere perso) |
| **NEW RISKS** | `R-58` … `R-66`. **Aggiornati il 2026-08-23:** `R-58` scesa a probabilità Bassa (`ADR-161`), **`R-63` mitigata strutturalmente** (`ADR-162`, `ADR-163`, `INV-24`). Resta `R-60` (crash loop che consuma tempo reale ma non attivo), non risolto per il solo tetto temporale |
| **NEW ASSUMPTIONS** | `AS-34` (Media) · ~~`AS-35` Bassa~~ → **scissa e risolta il 2026-08-23**: `AS-35a` **Alta** (creazioni, `R-12`), `AS-35b` Media (transizioni di stato), `AS-35c` Alta (vincolo sul nostro connector) · `AS-36` (Media) · `AS-37` (Media) |
| **MAY NEED REVISION** | `ADR-141` se `T-EV-04` scatta (più di 2 correzioni al recovery nel primo trimestre) · `ADR-155` è un **conflitto con `A09` dichiarato invece che risolto in silenzio**: `A09` chiedeva due *stati* nuovi, `A11` li implementa come *ragioni terminali* · `R-60` non è risolto per il solo tetto temporale |
| **IMPACT ON PREVIOUS** | **salda i tre mandati ereditati**: `A04` (che succede al crash), `ADR-104`/`AR-RT-17` (i due tetti, resi eseguibili), `A10` (ripresa del padre, cancellazione d'albero, ledger, codici d'errore) · **chiude `R-54`** (figli orfani) col `tree_reaper` · **salda i debiti di lavoro in background di `A07` e `A08`** (purge dei tombstone, polling, sweep, proiezione dei grant) con 8 tipi di `job` · rende `ADR-029` sufficiente al recovery (`INV-21`) e `AR-RT-08` strutturale (`INV-22`) · conferma `ADR-002` e `ADR-138` con argomenti nuovi |
| **IMPACT ON FUTURE** | `A12` (metriche di coda, lag dell'outbox, `uncertain_after_crash_rate`) · `A13` (`R-61`: il `job` come porta di servizio) · `A15` (drain, deployment, migrazioni expand/contract) · `A16`/`A17` (i test di recovery sono il gate) · `B21` (`DEF-05`, non chiusa qui) · `C24` (`DEF-06`/`RPO`: la memoria è **irreplaceable**) · `C29` (replay che non riproduce effetti) |
| **DAY-1** | `run_tree` con ledger e trigger · lease con `lease_epoch` e heartbeat · protocollo a tre scritture · `job` a 8 tipi · outbox a una tabella · scheduler come ruolo · `wakeup_at` · `tree_reaper` · `termination_reason` non nullo |
| **FUTURE** | `LISTEN`/`NOTIFY` · inbox con verifica di firma · leader election esplicita · ledger a quote · `WorkflowDefinition` come risorsa · eventualmente DBOS/`pg_durable` |
| **ADR CANDIDATES** | `ADR-141` … `ADR-160` (20) |
| **PREVISIONE** | il primo trigger a scattare sarà **`T-EV-03`** (`uncertain_after_crash_rate`), **per natura del sistema target e non per carico** |
| **CONFIDENCE** | **Alta** su lease e fencing, protocollo a tre scritture, contatore del tempo attivo, `INV-20`…`INV-23`, e sul rifiuto dell'engine (poggia su un FATTO di `R-04`, non su un'opinione). **Media** sulla scelta del polling (`AS-34`, `B-67` è una misura non fatta) e sul costo del ledger a riga singola. ~~**Bassa** su `AS-35`~~ → **risolta il 2026-08-23 da `R-12`**: Odoo non ha idempotency key native, ma ha `ir.model.data` con **vincolo UNIQUE di PostgreSQL** su un identificatore **scelto da noi**. L'idempotenza si costruisce, non si riceve (`ADR-161`). Confidenza **Alta** sulle creazioni, **Media** sulle transizioni di stato (`AS-35b`) |

### A12 — Observability, Evaluation, AI Reliability

| Campo | Contenuto |
|---|---|
| **PURPOSE** | rendere osservabili le decisioni dichiarate sbagliabili, **senza che l'osservabilità diventi la porta da cui esce ciò che l'audit tiene fuori** |
| **IL DEBITO SALDATO** | **63 metriche mandate da `A03`…`A11`: tutte e 63 coperte.** 1 confermata **non automatizzabile** (`proposed_memory_precision`, sostituita da revisione umana campionaria), 4 automatiche nell'esecuzione ma dipendenti da un **golden set umano**. In più **4 misure richieste dal prompt sono state rifiutate** con sostituto dichiarato: `task_success_rate` come SLO, `citation_correctness`, `unnecessary_action_rate`, "cosa ha capito l'agent". Registro totale: **86 voci `M-OB-01`…`M-OB-86`** |
| **CONFINE AUDIT / TELEMETRIA** | l'**audit** registra le decisioni che vincolano qualcuno: completo, mai campionato, la sua perdita è un difetto **legale**. La **telemetria** registra il comportamento: campionabile e scartabile, la sua perdita è un difetto **operativo**. **`INV-27` lo rende strutturale** vietando a qualunque controllo di sistema di leggere la telemetria |
| **DEBUGGING SENZA CONTENUTO** | **il prompt non si conserva, si ricostruisce** (`ADR-171`) dagli artefatti già versionati e hashati (`ADR-041`, `ADR-012`, `ADR-092`, e `ADR-090` che è una funzione pura). Unica porta al contenuto: `DebugCapture` (`ADR-172`) — opt-in del tenant, a tempo, autorizzato, auditato, **off by default** |
| **IL COSTO** | tetto **derivato**, non stimato: da `ADR-104` seguono **≤ 252 span per albero di run, sempre**. Tagliati: `run_id`/`tenant_id` come label di metrica, span per `PDP.decide()`/memoria/render, trace completo dei run nominali `READ`. **Mai campionate 8 classi**: autorizzazioni, `SIDE_EFFECT`, `UNCERTAIN`, errori, span `RUN`, eventi di sicurezza, guardie, canary |
| **KEY DECISIONS** | tre piani separati · OTel come contratto non stack · PostgreSQL Day-1 · gerarchia a 5 livelli · trace HTTP separato da trace di esecuzione · nessun ID nuovo · difesa **strutturale** non filtrante · sampling guidato dall'esito · budget di cardinalità · registro metriche verificato in CI · eval orientata all'esito · golden set con owner e scadenza · judge solo triage · `task_success_rate` non è SLO · canary + dead man's switch a 3 livelli con **l'ultimo anello esterno** · due cruscotti separati |
| **REJECTED** | piattaforma di AI observability commerciale · Prometheus/Grafana/Jaeger/Loki/ClickHouse Day-1 · identificatori nuovi · uno span per ogni operazione · redaction come difesa **primaria** · judge come gate · A/B in produzione su percorsi con effetti · canary di versione Day-1 · anomaly detection · error budget sulla sicurezza · tassonomia di errori nuova |
| **NEW INTERFACES** | `TelemetryExporter` · `ServingScraper` · **`Reproduction Bundle`** · `ExecutionSpan` / `MetricSample` / `EvaluationCase` / `EvaluationResult` / `QualitySignal` |
| **NEW CONSTRAINTS** | `AR-OB-01` … `AR-OB-24` (17/24 automatiche) |
| **NEW INVARIANTS** | **`INV-25`** (nessun campo di telemetria in una decisione) · **`INV-26`** (nessun contenuto in telemetria) · **`INV-27`** (nessun controllo dipende dalla telemetria) · **`INV-28`** (lettura sotto `tenant_id` risolto) |
| **NEW RISKS** | `R-67` … `R-74`. Critici: **`R-67`** (la ricostruzione non copre i dati letti dal vivo — Alta, **non risolvibile senza violare `INV-07`**) e **`R-70`** (l'anello di feedback muore al passo umano — Alta, mitigazione dichiarata debole) |
| **NEW ASSUMPTIONS** | `AS-38` … `AS-43`. Fragili: **`AS-42`** (disciplina del failure corpus), **`AS-41`** (rete in uscita, dipende da `Q-03`), **`AS-39`** |
| **MAY NEED REVISION** | `ADR-166` finché `B-76`/`B-80` sono aperte · `ADR-179` finché `B-77` è aperta · l'uso di `UNLOGGED` sugli span · il rifiuto del canary di versione · `ADR-186` se servissero aggregati cross-tenant |
| **IMPACT ON PREVIOUS** | **`AR-035` diventa eseguibile** (`ADR-176`: un test di CI verifica che ogni trigger abbia la sua metrica) · **conflitto dichiarato con `T-GP-01`**: il denominatore va preso **al netto dell'inference**, altrimenti non scatta mai e `AS-27` resta infalsificabile · **requisito nuovo per `A03`**: l'endpoint di approvazione deve registrare `modified_fields[]`, altrimenti la metrica che sblocca `ADR-023` **non esiste** · `ADR-104` acquista un beneficio non previsto: limita il volume di trace **per costruzione** · **nessun ADR precedente rivisto** |
| **IMPACT ON FUTURE** | `A13` (adversarial, `R-72`/`R-73`) · `A14` (retention dell'audit, anonimizzazione dei dataset) · `A15` (job nuovi, dead man's switch) · `A16`/`A17` (**i gate sono il contratto di rilascio**) · `B21`/`C24`/`C26` ricevono strumenti ma **`DEF-05`, `DEF-06`, `DEF-08` restano aperte** |
| **DAY-1** | 5 tabelle · 2 librerie in-process · 6 `job_type` · registro con test CI · 8 allarmi · **golden set etichettato** · 4 test di recovery · dead man's switch esterno. **Zero servizi nuovi** |
| **FUTURE** | backend dedicato · rollup per tenant · gate relativi · canary di versione · anomaly detection · tamper evidence · Collector |
| **ADR CANDIDATES** | `ADR-164` … `ADR-187` (24) |
| **PREVISIONE** | il primo trigger a scattare sarà **`T-OB-03`**, e non per traffico: `metric_sample` scrive a ogni finestra **indipendentemente dal traffico**, quindi **il costo fisso arriva prima di quello variabile** |
| **CONFIDENCE** | **Alta** su confine audit/telemetria, `INV-25`…`INV-28`, ricostruzione del prompt, eval orientata all'esito (poggiano su invarianti interni e su `R-11`), e sul tetto di trace — che è **derivato** da `ADR-104`, non stimato. **Media** su `ADR-166` e sul sampling. **Bassa** su `ADR-179` (nessuna ricerca sui bias dei judge), sulla tenuta del ciclo di feedback umano, e su tutte le soglie numeriche lasciate `NON ANCORA DECISO` **per scelta** |

### A13 — Security

| Campo | Contenuto |
|---|---|
| **PURPOSE** | verificare che le difese già costruite reggano contro un avversario reale, e chiudere ciò che manca |
| **LA TESI** | l'architettura di sicurezza **non è il filtro né il perimetro: è l'invariante**. `INV-12`, `INV-19`, `INV-25`, `INV-27` hanno tutti la stessa forma — **tolgono il potere invece di giudicare il contenuto**. È la sola difesa che regge contro un avversario che scrive testo meglio di quanto noi lo filtriamo: i detector LLM mancano il **66 %** delle voci di memoria avvelenate (`R-13`) |
| **IL BUCO CHIUSO** | **`ASI09` — Human-Agent Trust Exploitation**, non affrontata da nessuno dei 12 documenti precedenti. `ADR-023` (approvazione umana) è il pilastro su cui poggiano `R-26`, `R-33`, `R-51`; `ASI09` dice che **quel pilastro è esso stesso una superficie d'attacco**, e OWASP dichiara che i guardrail non bastano. Sette decisioni (`ADR-189`…`195`), di cui la portante: **si approva un `ActionBinding` tipizzato, non una narrazione** |
| **IL DIFETTO TROVATO IN `A03`** | **`T-GP-02` scatterebbe esattamente quando le approvazioni perdono valore.** Un tasso di approvazione vicino al 100 % ha due spiegazioni indistinguibili: l'agent è affidabile, **oppure le persone hanno smesso di leggere**. `ADR-196` lo riformula come congiunzione di **tre** condizioni; senza le due metriche nuove va considerato **disattivato**, non "non ancora scattato" |
| **KEY DECISIONS** | invariante come architettura · 7 decisioni su `ASI09` · `T-GP-02` riformulato · `KillSwitch` a tre livelli · allowlist di egress a livello di container · parser in processo separato · quarantena documenti · guardia sugli identificatori · fail-closed promosso a regola esplicita · il rilevamento di injection è un **sensore, non un controllo** |
| **REJECTED** | WAF · SIEM Day-1 · secret manager esterno · sandbox per i nostri agent · classificatore bloccante di injection · agent di sorveglianza · break-glass · cifratura per campo · autovalutazione della rischiosità da parte del modello |
| **NEW CONSTRAINTS** | `AR-SE-01` … `AR-SE-18` (13/18 automatiche) |
| **NEW INVARIANTS** | `INV-29` (nessun testo del modello è oggetto di approvazione) · `INV-30` (le anteprime non hanno effetti) · `INV-31` (nessun contenimento bypassa il PDP) |
| **NEW RISKS** | `R-75` … `R-80`. Critici: **`R-75`** (l'attrito viene disattivato per lamentele — Alta/Alto), **`R-78`** (il `KillSwitch` mai provato), **`R-79`** (corruzione lenta del dato, **nessuna difesa reale**) |
| **NEW ASSUMPTIONS** | `AS-44` … `AS-47`. **`AS-44`** (l'attrito funziona davvero) e **`AS-47`** (l'avversario vuole rubare, non corrompere) sono entrambe **Bassa** |
| **MAY NEED REVISION** | `ADR-191` se `B-87` va male · `ADR-195` probabilmente sovraprogettato · `ADR-211` rischia di essere un cruscotto ignorato · **tutto il documento se `AS-29` fosse falsa** |
| **IMPACT ON PREVIOUS** | **`A03`: `T-GP-02` difettoso, riformulato** (`ADR-196`); l'endpoint di approvazione acquista `approval_decision_time` oltre a `modified_fields[]` già chiesto da `A12` · **`A08`: `T-ME-04` alza la soglia** (`ADR-199`) — un MINJA riuscito produce voci apparentemente precise · `A06`/`A02`: vincoli su anteprima e interfaccia di approvazione · `A05`: il rifiuto del Model Gateway **confermato da un incidente reale** (LiteLLM/TeamPCP, ~500.000 identità) · **nessun ADR precedente rivisto**, due riformulati |
| **IMPACT ON FUTURE** | **`A14`**: `AR-GP-17`/`R-32` (redazione per campo), retention, `B-50` · **`A15`**: allowlist di rete, processo del parser, `AS-41` · **`A16`/`A17`**: i 10 gate sono contratto di rilascio, `ADR-213` lega incidente e test · `A18`: `AR-SE-11` sugli URL · `C24`/`C26`: runbook e conformità |
| **DAY-1** | 7 ADR sull'approvazione · allowlist di egress · parser isolato · quarantena · `KillSwitch` · sensore di injection · guardia sugli identificatori · 10 gate di test · **1 sessione di red teaming con persone vere** |
| **FUTURE** | isolamento a processo (`T-TL-03`) · catena 1 (`T-ID-08`, chiude `R-41`) · cifratura per-tenant (`B-50`) · SIEM · tamper evidence |
| **ADR CANDIDATES** | `ADR-188` … `ADR-215` (28) |
| **VALIDAZIONI ESTERNE RICEVUTE** | `ADR-105` (dual principal) **è il pattern "Blended Identity"** raccomandato come controllo primario contro il confused deputy · `ADR-108` è il *credential brokering* raccomandato · `ADR-094` (nessuna estrazione automatica di memoria) **spezza il meccanismo stesso di MINJA** · il rifiuto del Model Gateway è confermato da un incidente reale |
| **CONFIDENCE** | **Alta** sull'inventario delle difese, sui confini, su `ASI03` (validato esternamente), sul fail-closed e sul contenimento. **Media** sulle 7 decisioni di `ASI09`: il ragionamento è solido e `ADR-189` è strutturale, ma `AS-44` non è verificata. **Bassa** sul rilevamento (**l'architettura è brava a impedire e mediocre ad accorgersi**), su `AS-47`, e sulla completezza — **nessun framework copre più del 65,3 % di una singola categoria (`R-13`): questo documento non può essere completo e non pretende di esserlo** |

> **Pattern scoperto da `A13`, da portare al gate di Level A.** Due trigger progettati per
> **allentare** una difesa (`T-GP-02`, `T-ME-04`) non distinguevano fra *"la difesa non serve
> più"* e *"la difesa ha smesso di funzionare"*. **Ogni trigger di allentamento va riletto**
> con la domanda: *cosa lo farebbe scattare se il controllo fosse stato aggirato invece che
> reso superfluo?*

### A14 — Data Governance, Privacy, Compliance

| Campo | Contenuto |
|---|---|
| **PURPOSE** | quali dati personali restano davvero da noi, chi risponde di cosa, quanto si conservano, e cosa succede quando qualcuno chiede di cancellarli |
| **`R-32` CHIUSO A METÀ, E LA METÀ È DICHIARATA** | **chiuso sul percorso strutturato** con `ADR-228`: non con la redazione ma con la **projection**. Il PDP produce un **`FieldScope`** — il terzo ambito che mancava, accanto a `RetrievalScope` e `MemoryScope` — e il PEP restringe i campi **prima** che la chiamata parta verso Odoo, con verifica sul risultato come seconda linea. **Dichiarato definitivamente aperto** sul percorso documentale (`ADR-229`): un documento non ha campi, e redigere dentro un testo richiederebbe un classificatore che `ADR-188` ha già respinto. Non è un rinvio: è **una limitazione strutturale del mezzo** |
| **QUALI DATI PERSONALI RESTANO DA NOI** | sei famiglie: identità dei nostri utenti · **il testo che le persone ci scrivono** (il serbatoio più grande e meno controllabile → `R-87`, Alta/Alto) · memoria (**irreplaceable**) · documenti indicizzati e derivati · identificatori di record del CRM · **il valore precedente dei campi scritti**. Quest'ultima è una **scoperta**: `ADR-221` è una copia di dato di dominio nel nostro journal, cioè **un'erosione di `INV-07` che nessuno aveva registrato** → `R-88`, perimetrata da `ADR-241` |
| **CANCELLAZIONE DENTRO UN AUDIT APPEND-ONLY** | **non si cancella l'audit: si distrugge la chiave che lo rende leggibile.** *Identity shredding* (`ADR-236`), che poggia su `ADR-107` (`subject_id` opaco mai riassegnato). **Non è anonimizzazione, e il documento lo dice** (`R-89`). Se un'autorità pretendesse la rimozione fisica: `ADR-238`, break-glass a due operatori che **scrive la propria confessione in `audit_redaction` prima** di rimuovere → `INV-37`. *Non conserviamo l'integrità: conserviamo la conoscenza della sua perdita* |
| **RETENTION** | **nessun periodo fissabile citando una norma.** L'unico obbligo citabile in `R-14` (art. 2220 c.c., decennale) riguarda le scritture contabili, che **Day-1 non deteniamo** (`ADR-217` + `ADR-223`). Tutti i valori restano `NON ANCORA DECISO` → **`DEF-13`**, scadenza *prima dello schema*. È stato però fissato **l'ordinamento senza numeri** che mancava ad `ADR-184`: **`INV-35`, la telemetria non sopravvive mai all'audit** |
| **KEY DECISIONS** | `FieldScope` al confine · granularità documentale dichiarata definitiva · **le categorie particolari si dichiarano, non si rilevano** · il `purpose` può solo restringere · classificazione a due assi mai inferita · registro `data_asset` come artefatto di **CI** · retention come **riga di policy** · identity shredding · `deletion_ledger` **rigiocato dopo ogni restore** · `audit_redaction` che si confessa · **colonna `key_ref` degenere Day-1** · nessun testo libero di produzione nei dataset di evaluation · legal hold come predicato costante falso · nessun oggetto `Consent` Day-1 |
| **REJECTED** | classificatori di dato personale · data catalog · redazione dentro il testo dei documenti · anonimizzazione presentata come tale · retention nel codice · architettura regionale Day-1 · oggetto `Consent` · qualificazione titolare/responsabile (bloccata su `Q-03`, **non-decisione dichiarata**) |
| **NEW INTERFACES** | **`FieldScope`** · `RetentionPolicy` · `ErasureRequest` / `ErasureTask` · `deletion_ledger` · `audit_redaction` · registro `ExternalTransfer` · `SoDConflict` · **`Erasure Coordinator`** (unico componente nuovo, in-process) |
| **NEW CONSTRAINTS** | `AR-DG-01` … `AR-DG-28` (25/28 automatiche) |
| **NEW INVARIANTS** | `INV-35` (la telemetria non sopravvive all'audit) · `INV-36` (il derivato eredita la classe della sorgente) · `INV-37` (nessuna rimozione dall'audit fuori da `audit_redaction`) · `INV-38` (dopo la cancellazione nessuna riga risolve il soggetto) · `INV-39` (nessuna categoria particolare in un `ToolInvocation`) · `INV-40` (nessun testo libero di produzione nei dataset) |
| **NEW RISKS** | `R-86` … `R-96`. Critici: **`R-87`** (il testo libero è il maggior serbatoio di dato personale, mitigazione dichiarata debole), **`R-92`** (il motore SoD resta vuoto e nessuno se ne accorge), **`R-95`** (la retention non viene mai fissata), **`R-96`** (i backup diventano l'archivio vero e la cancellazione è nominale) |
| **NEW ASSUMPTIONS** | `AS-50` … `AS-55`. Fragili: **`AS-50`** (deployment UE, dipende da `Q-03`), **`AS-51`** (nessun tenant tratta categorie particolari), **`AS-54`** (il committente accetta che la cancellazione dai backup avvenga per scadenza — **è contrattuale, non tecnica**) |
| **MAY NEED REVISION** | `ADR-243` e `ADR-249` sono **Parziali** (manca `k`, manca il baseline SoD citabile) · `ADR-253` Parziale (manca la finestra di grazia) · `ADR-236` dipende da `B-95`, che **richiede parere legale** · `ADR-248` è una **non-decisione dichiarata** bloccata su `Q-03` |
| **IMPACT ON PREVIOUS** | **`A03`/`A06`: nasce `FieldScope`**, il terzo ambito prodotto dal PDP · **`A07`: `R-32` chiuso sul percorso strutturato, dichiarato definitivo su quello documentale** · **`A13`: `ADR-221` viene perimetrata** perché era un'erosione non registrata di `INV-07` · `A12`: `ADR-184` acquista un ordinamento (`INV-35`) e `AR-OB-24` diventa un meccanismo (`ADR-240`, `INV-40`) · `A09`: `AR-ID-09` completata da `ADR-253` · `A05`: `AR-DG-16` vieta staticamente di mandare il context a un provider esterno |
| **IMPACT ON FUTURE** | **`A15`**: `key_ref`, luogo di trattamento, regione singola · **`A16`**: `DEF-08` resta aperta; il registro `data_asset` è un gate di CI · **`A17`**: il rigioco del `deletion_ledger` va **provato**, non descritto (lezione di `R-78`) · **`C24`**: `R-96` — o il backup dura meno del dato, o il ledger copre la differenza · `C26`: conformità |
| **DAY-1** | registro `data_asset` in CI · `FieldScope` · classificazione a due assi · `RetentionPolicy` con valori nulli · `deletion_ledger` · colonna `key_ref` degenere · `ExternalTransfer` · nessun accesso permanente per il personale · `Erasure Coordinator` minimo. **Zero servizi, zero datastore nuovi** |
| **FUTURE** | cifratura per tenant → CMK → crypto-shredding · legal hold · aggregati cross-tenant con soglia · automazione DSAR · catalogo vero se i `data_asset` superano ~50 |
| **ADR CANDIDATES** | `ADR-228` … `ADR-255` (28) |
| **CONFIDENCE** | **Alta** su `FieldScope`, sulla classificazione dichiarata, sul registro in CI, su `INV-35`…`INV-40` e sulla scelta di non costruire scadenze su fonti in conflitto. **Media** su identity shredding (dipende da `B-95`, che richiede parere legale) e su SoD (forma definita, contenuto `INTERPRETAZIONE NOSTRA`). **Bassa** su tutto ciò che dipende da `Q-03`, su `R-87` (il testo libero non è minimizzabile), e su ogni valore di retention — **che per scelta non è stato inventato** |

> **Nota di metodo.** `A14` dichiara esplicitamente di non essere un parere legale e distingue
> **OBBLIGO CITABILE** (con fonte in `R-14`) da **INTERPRETAZIONE NOSTRA**. Dove serve un
> avvocato, lo scrive: `B-95` (art. 17(3) GDPR) e `ADR-248` (qualificazione
> titolare/responsabile) sono marcati `RICHIEDE PARERE LEGALE`.

### A17 — Testing, Quality Assurance, Validation

| Campo | Contenuto |
|---|---|
| **PURPOSE** | **raccogliere il conto.** Tredici documenti hanno dichiarato gate di rilascio senza costruirli: `A17` ne fa l'inventario e per ogni voce dice **come si esegue, cosa blocca quando fallisce, quanto costa**. Poi progetta ciò che mancava: piramide, ambiente di test, contratto di flakiness, classificazione dei gate, budget, ownership |
| **L'INVENTARIO È IL DOCUMENTO** | §4 elenca **145 voci** mandate da `A02`…`A14`, di cui 18 già battezzate (`TC-EV-01`…`08`, `TS-1`…`TS-10`) e 127 registrate qui col prefisso **`TC-QA-*`**. **~55 % sono verificabili staticamente**: è il dividendo dell'architettura a invarianti di `A13` — le regole scritte come invarianti si testano senza far girare niente |
| **TRE CORPI, NON UNA PIRAMIDE** | `ADR-261`. Deterministico (**blocca sempre**), probabilistico (**blocca solo dopo tre baseline**, `ADR-180`), umano (**dichiarato, quasi mai bloccante**). La piramide classica presuppone che l'unità di test sia riproducibile: qui il componente centrale non lo è, quindi si separa per **natura dell'esito** invece che per ampiezza |
| **LA SCOPERTA PIÙ UTILE** | `ADR-282`: **i test adversarial sono bloccanti anche col modello dentro**, perché l'esito atteso è **strutturale** (`DENY`), non statistico. La stocasticità non lo cambia. Obbligo che ne consegue: ogni test adversariale asserisce anche che **il tentativo sia avvenuto** — un test in cui il `DENY` non compare nel journal non ha misurato niente |
| **I TRE CONTENIMENTI SONO UN GATE SOLO** | `ADR-267`, `G-QA-05` bloccante: `KillSwitch` (`ADR-212`) col **quarto test che nessuno scrive, la reversibilità** · rigioco del `deletion_ledger` come **precondizione strutturale del rientro in servizio** (`AR-DG-31`) · drain ai confini di passo. Applica `R-78`: *un contenimento non provato non esiste* |
| **AMBIENTE DI TEST** | `OdooFake` a fedeltà **verificata** da contract test notturno (`ADR-262`) · generatore `crm_seed` a tre livelli, incluso **`hostile`** (`ADR-263`) · **due barriere** per `AR-TL-16` (`ADR-264` + `INV-41`), perché su una macchina sola una non basta · staging = **quale Odoo tocchi, non quale macchina** (`ADR-270`, conseguenza di `AS-08`) |
| **GATE** | nove, `G-QA-01`…`09`, tre classi (`ADR-268`), **sei bloccanti**. Promozione advisory→bloccante a **quattro condizioni**, la quarta è il **caso negativo provato** (`INV-42`). Registro `tests.yaml` verificato in CI (`ADR-266`), stessa forma di `ADR-176` e `ADR-233`: l'errore **nomina la decisione architetturale che resta incontrollata** |
| **PROTOCOLLO `AS-40`** | §8.2: chi sceglie i 20 casi **non è** chi scrive i test; classificazione `D`/`P`/`N`; **regola di lettura dichiarata prima di guardare i dati**. Se fra un terzo e la metà risulta `P`/`N`, `AS-40` è ridimensionata e si apre `DEF-18` |
| **FLAKINESS** | `ADR-265`: `k` e soglie **si calcolano** (procedura §9.2), non si scelgono. **Mai retry** (`AR-QA-07`), sempre quarantena con owner e scadenza (`ADR-276`). I numeri sono `DEF-14`; il metodo è `B-106`, **priorità ALTA** |
| **KEY DECISIONS** | `ADR-261` … `ADR-283` (23). Oltre alle sopra: punti di interruzione **dichiarati** (`ADR-278`, *il modo in cui si scrive il test decide se il gate può bloccare*) · matrice di autorizzazione a **generazione parziale** (`ADR-279`) · copertura dei **mandati**, non di riga (`ADR-280`) · capability probe bloccante e distinto dal gate di qualità (`ADR-281`) · golden set = gate di **attivazione** del retrieval, non di ogni rilascio (`ADR-283`, disinnesca `R-30`) |
| **REJECTED** | piramide classica con eval in cima (`R-99`) · validazione continua in produzione (`ADR-183`) · piattaforma di qualità (`AS-04`) · framework di eval di terzi: similarità/rubric contraddicono `ADR-177`, tracing gestito vietato da `AR-DG-16`, promptfoo è output matching (`ADR-273`) · Odoo reale per ogni test · Odoo condiviso · mock ad hoc (*affermano ciò che lo sviluppatore crede, e `R-14.7` dice che crede la cosa sbagliata*) · staging su macchina separata · dump anonimizzato (`INV-40`, `R-73`) · mutation testing generale · copertura di riga come gate · chaos su 6 guasti (2 Day-1, `ADR-277`) |
| **NEW INTERFACES** | `ObligationRecorder` (spia deterministica, solo test) · `CrashInjector` + punti di interruzione nominati · `DeterministicModel` / `ScriptedModel` / `MisbehavingModel` (`ADR-271`) · `OdooFake` + contract test bidirezionale · generatore `crm_seed` · runner di eval in-process · `tests.yaml` · `EvaluationCase` esteso con `repetitions`, `owner`, `origin_incident` |
| **NEW CONSTRAINTS** | `AR-QA-01` … `AR-QA-19`. Le più vincolanti: `-07` (mai retry) · `-09` (nove superfici di isolamento come **lista chiusa**: una superficie nuova non registrata fa fallire la build) · `-14` (bloccante senza `negative_case` = build rossa) · **`-19` (eccezione dichiarata a `INV-07`**: il harness interroga l'Odoo di test direttamente, perché passare dai tool renderebbe il test dipendente dalla cosa che sta testando) |
| **NEW INVARIANTS** | `INV-41` (nessuna connessione fuori dall'allowlist di test) · **`INV-42`** (ogni voce bloccante ha un caso negativo provato) · `INV-43` (nessun identificatore reale nelle fixture) · **`INV-44`** (ogni mandato risolve a un test e viceversa) |
| **NEW RISKS** | `R-97` … `R-108`. Alta probabilità: **`R-97`** (i gate migrano fuori dal percorso che bloccano) · **`R-98`** (`OdooFake` diverge) · **`R-99`** (gate reso verde alzando la soglia) · `R-100` (dataset troppo pulito) · **`R-101`** (i tre compiti umani non eseguiti, *mitigazione dichiarata debole*) · **`R-106`** (`k` mai calibrato → `ADR-180` diventa scusa permanente). **`R-108` è una scoperta non risolta**: `INV-40` non copre i **documenti aziendali reali** in un golden set |
| **NEW ASSUMPTIONS** | `AS-56` … `AS-62`. Fragili: **`AS-57`** (la variabilità è stabile per un trimestre, Bassa) · **`AS-60`** (red teaming con persone organizzabile, Bassa e **organizzativa**) · **`AS-62`** (i moduli critici sono scrivibili senza accesso dinamico — **se falsa, il 55 % della copertura ha buchi silenziosi**) |
| **MAY NEED REVISION** | `ADR-262` se il contract test notturno fallisce ripetutamente (`T-QA-02`, **previsto come il primo trigger a scattare**) · `ADR-265` se `B-106` desse un metodo migliore · `ADR-273` se emergesse un framework che accetta post-condizioni arbitrarie e gira in locale (`B-111`) · `ADR-277` al primo deployment multi-nodo · **`ADR-261` se `AS-40` risultasse falsa**: il corpo probabilistico dominerebbe e la separazione diventerebbe «il poco che blocca vs tutto il resto» |
| **IMPACT ON PREVIOUS** | **Nessun ADR precedente rivisto.** Tre incoerenze **dichiarate** invece che risolte in silenzio: (1) `A10` dice «3 test» in un punto e «2» in un altro → **risolta a tre**, perché `R-49` chiede di verificare che le colonne di lineage **esistano**, non solo che siano degeneri; (2) «4 test di recovery» di `A12` contro gli 8 di `A11` → **risolta a otto**, eseguiti nello stesso gate perché separarli permetterebbe di dichiarare fatto il recovery a metà; (3) confine `A16`/`A17` sul contract test → `A17` dice *cosa* si verifica e *cosa blocca*, `A16` dice *dove gira*. Inoltre `A02` riceve la **validazione semantica della configurazione** che aveva dichiarato scoperta «finché non esiste `A17`»; `AR-TL-16`, `AR-DG-31` e `ADR-212` passano da regole scritte a **test eseguiti** |
| **IMPACT ON FUTURE** | **`A15`**: test di drain, parità di ambiente, `ADR-270` come vincolo sul modello di deployment, `AS-41`/`B-82` (rete in uscita per il dead man's switch) · **`A16`**: eredita l'**esecuzione** dei nove gate nella pipeline e **`DEF-19`** · **`A18`**: test negativi sull'API, matrice di compatibilità, contract test OpenAPI · **`C24`**: `G-QA-05` include un ciclo backup/restore — *se è troppo lento per rilasciare è troppo lento per un incidente*, ed è informazione su `DEF-06` · **`C26`**: copertura del threat model dichiarata incompleta (65,3 %) |
| **DAY-1** | in ordine di costruzione: (1) registro + 3 controlli; (2) le due barriere di `AR-TL-16`; (3) test statici sugli invarianti; (4) `OdooFake` + contract test; (5) generatore `tiny`/`hostile`; (6) `TC-EV-01`…`08` coi punti dichiarati; (7) i dieci `TS-*`; (8) i tre contenimenti; (9) runner di eval + primi 20 `EvaluationCase` (= protocollo `AS-40`); (10) golden set **prima** di accendere il retrieval. **9 gate, 6 bloccanti, zero servizi nuovi in produzione** |
| **FUTURE** | gate relativi dopo tre baseline (`T-QA-03`) · Odoo effimero per l'integration (`T-QA-02`) · campionamento stratificato dichiarato (`T-QA-07`) · suite di tool poisoning al primo tool non nostro (`T-QA-08`) · test multi-agent al primo `child run` · load/stress quando `DEF-05` si chiude · canary per tenant · verifica formale sul PDP se si va verso Cedar/OPA |
| **ADR CANDIDATES** | `ADR-261` … `ADR-283` (23) |
| **CONFIDENCE** | **Alta** su l'inventario (*è una lettura, non un'invenzione*), la classificazione dei gate, il gate di recovery, i contenimenti, `INV-42` e la struttura a tre corpi. **Media** su `OdooFake` (`AS-56`, e `R-98` è Alta), l'ambiente di test, il budget di CI (`AS-58` è sociale), la copertura statica (`AS-62` non verificata). **Bassa** su tutto il contratto di flakiness finché la variabilità non è misurata (`DEF-14`, `AS-57`, `R-106`), sui tre compiti umani (`AS-60`, `R-101`) e sull'anello di feedback (`R-70`/`AS-42`, dove `A17` **conferma la valutazione di `A12` senza migliorarla**) |

> **La debolezza dichiarata senza attenuanti** (§31.3). L'architettura **protegge benissimo dal
> sistema dannoso e misura soltanto il sistema inutile.** La sproporzione è deliberata —
> l'inutilità ha un canale di rilevamento naturale (qualcuno se ne lamenta), la dannosità no, e
> `R-14.5` conta nove distruzioni di ambienti di produzione, quasi una al mese — ma resta una
> sproporzione, e `ADR-283` chiude solo una delle tre falle che l'obiezione nomina.

> **Nessuna ricerca esterna in questa passata**, per vincolo di metodo. Dieci voci di backlog
> nuove sono il prezzo, e **`B-106` blocca l'attivazione di metà dei gate**.

### A18 — API, Integration, External Interface

| Campo | Contenuto |
|---|---|
| **PURPOSE** | progettare **due superfici tenute separate per tutta la lunghezza del documento**: (1) l'API che la piattaforma **espone** — nostra, versionata, contrattuale; (2) il **connector verso Odoo** — subita, isolata, con `B-53` non risolta. Più: definire le **sette classi negative** che `AR-QA-02` richiedeva e che nessuno aveva mai nominato |
| **LA FORMA È DERIVATA, NON SCELTA** | `ADR-285`: **ogni run è asincrono, non esiste endpoint sincrono.** Non è una preferenza: `ADR-104` (50 step / 10 min) più `ADR-216` (conferma umana su ogni scrittura) rendono l'attesa la norma. Un'operazione che aspetta un umano **non può** essere una richiesta HTTP appesa. `?wait=` collassa i round-trip senza promettere niente. Il polling è **il contratto**; SSE e feed pull sono ottimizzazioni della latenza di scoperta (`ADR-286`) |
| **PERCHÉ NON GraphQL** | due incompatibilità **strutturali**, non estetiche: (1) `FieldScope` (`ADR-228`) esige l'autorizzazione **prima** della chiamata, mentre GraphQL autorizza nei resolver **dopo**; (2) l'N+1 renderebbe il traffico verso l'ERP del committente una funzione della query del **client**. Anche RPC su una porta è respinto: il metodo diventa argomento, cioè `execute_kw` ricreato al confine esterno |
| **IL CONNECTOR** | `connectors/odoo/` **concreto**, sei moduli, `transport.py` unico file che conosce il protocollo, firma `call(model, method, args, kwargs, ctx)`. **Nessun `CRM Adapter Interface`**: `AR-020` vieta un'astrazione generica senza due implementazioni reali. `B-53` non si risolve per assunzione — si **isola**, così che chiuderla dopo costi un file |
| **LA REGOLA CHE REGGE IL TOOL LAYER** | **`AR-AP-19`**: in `connectors/odoo/tools/*`, `model` e `method` di `call()` sono **letterali**, verificato staticamente su AST. È la traduzione di `ADR-049` al confine Odoo. **Senza, il Tool Layer sarebbe una facciata su `execute_kw`** e tutto il lavoro di `A06` sarebbe decorativo |
| **BUDGET VERSO IL CRM** | `ADR-294`: budget di chiamate esterne **per albero di run**, consumato da un trigger di database (stessa forma di `ADR-146`), con `INV-46` che lo rende non aggirabile. Motivo: **un agent che itera può saturare l'istanza Odoo di produzione, e questo è un modo di far danno che non richiede nessun permesso di scrittura**. I valori sono `DEF-21`, il metodo è `B-116` |
| **KEY DECISIONS** | `ADR-284` … `ADR-297` (14). Oltre alle sopra: `Idempotency-Key` **obbligatoria**, non opzionale, e distinta dall'idempotenza verso Odoo di `ADR-161` (`ADR-290`) · SSE e non WebSocket, motivo primario l'**autenticazione** (`ADR-286`) · **nessun token streaming sulla superficie di approvazione** (`ADR-287`, estensione operativa di `INV-29`/`ASI09`) · evento = **riferimento, non consegna**, envelope a 9 campi senza dato di dominio (`ADR-288`) · `api` e `worker` non si parlano, il trasporto interno è **PostgreSQL** (`ADR-289`) · **reverse proxy, non gateway**: può solo rifiutare, mai permettere (`ADR-291`) · nessun webhook Day-1, contratto già scritto (`ADR-292`) · **venti cose che l'API non deve permettere**, verificate in CI contro la specifica (`ADR-295`) · versioning nel path (`ADR-296`) · probe di schema all'avvio, campo mancante **impedisce l'avvio** (`ADR-297`) |
| **REJECTED** | GraphQL · RPC su una porta · gRPC esterno e interno · event-driven con broker · WebSocket come canale primario · API gateway come piattaforma · batch API (deciderebbe `DEF-12` implicitamente) · endpoint sincrono · endpoint che invocano tool · **`CRM Adapter Interface`** · astrazione a due trasporti per `B-53` · callback URL per richiesta · SDK pubblicati Day-1 · AsyncAPI/Protobuf Day-1 · versioning per header |
| **NEW INTERFACES** | 24 endpoint pubblici `/v1/*` · `GET /v1/events` (feed keyset per tenant) · `GET /v1/runs/{id}/events` (SSE con `Last-Event-ID`) · `GET /v1/whoami` · envelope di evento a 9 campi · `OdooTransport.call()` · i sei moduli di `connectors/odoo/` (`transport`, `tools/*`, `idempotency`, `fields`, `budget`, `errors`) · **campo `next_action_required` su `Run`** — il campo che nessun documento fratello aveva, e che risponde all'unica domanda che un client si pone davanti a un run fermo |
| **NEW CONSTRAINTS** | `AR-AP-01` … `AR-AP-32`, **26 su 32 con verifica automatica**. Le più vincolanti: `-11` (nessun parametro allarga l'autorità) · `-13` (il tenant **mai** dal client: se presente è `400`, non un override) · `-17` (nessun endpoint chiama il CRM fuori da un run) · `-18` (nessun nome Odoo sopra il connector) · **`-19`** · `-22` (`ALREADY_APPLIED`: **l'errore che è un successo**) · `-24` (campo mancante impedisce l'avvio) · `-26` (il proxy non autorizza) · **`-27`** (MCP inbound spezza la **catena di custodia dell'approvazione**) · `-30` (`NEG-1/2/3` non migrano mai nightly) · `-32` (campo negato = **chiave assente**, non `null` e non mascherata) |
| **NEW INVARIANTS** | **`INV-45`** (nessun esito positivo di autorizzazione senza decisione PDP registrata: nessun `default allow`, nessuna cache a PDP guasto, nessun flag di bypass, nessuna modalità manutenzione — rende `AS-29` strutturale sulla superficie esterna) · `INV-46` (`external_calls_consumed` **esattamente** = chiamate uscite da `connectors/`) · `INV-47` (nessun testo di errore esterno persistito, loggato o restituito — i messaggi di Odoo contengono nomi di campo, valori e talvolta dato di dominio) |
| **NEW RISKS** | `R-109` … `R-117`. Alta probabilità: **`R-110`** (budget tarato sul nulla, **e l'errore verso il largo è invisibile**) · **`R-111`** (gli SSE si chiudono in attesa di approvazione — *un run che aspetta un umano è inattivo per definizione*) · **`R-112`** (192 test negativi migrano nightly, mitigazione **parziale**) · **`R-115`** (**l'`OdooFake` non può rilevare divergenze di protocollo: `A18` peggiora `R-98` e lo dichiara, non risolto**). `R-117` ha la forma controintuitiva: il caso grave **non** è il PDP che nega e Odoo che permette, è il **contrario** — allora il nostro `ALLOW` finisce nell'audit come se fosse valido |
| **NEW ASSUMPTIONS** | `AS-63` … `AS-67`. Fragili: **`AS-65`** (costo del rate limiting su PostgreSQL trascurabile — Bassa, **non misurata**) · **`AS-66`** (la firma `call()` sopravvive a qualunque successore delle RPC — Bassa, **è un'ipotesi su una specifica non vista**) · `AS-64` (il committente accetta che **tutto** sia asincrono — Media, va confermata) |
| **MAY NEED REVISION** | `ADR-293` se `T-AP-01` conferma `B-53` con forma diversa (`R-109`) · `ADR-294` nei valori finché `B-116` è aperta · `ADR-287` se `AS-44` risultasse falsa (`B-87`, `R-114`) · `ADR-289` se `AS-63` è falsa · `ADR-285` a `T-AP-08` · `ADR-296` a `T-AP-09` · tutta la §23 se `Q-01` cambia. **Nota che vale più delle altre: il vero costo di `Q-01` è `ADR-161`/`AS-35a`, non il connector** — l'idempotenza poggia su una proprietà specifica di Odoo (external ID scelto dal chiamante con vincolo UNIQUE del database), e `B-117` chiede se gli altri CRM ce l'hanno |
| **IMPACT ON PREVIOUS** | Nessun ADR precedente rivisto. **`A17`: il debito di `AR-QA-02` è saldato** — le sette classi negative più l'ottava («valido e ostile») sono definite; matrice di compatibilità a **quattro** assi, il quarto è la versione di Odoo; **`R-98` peggiorata e dichiarata** come `R-115`. **`A13`: contributo nuovo** — la **catena di custodia dell'approvazione** è una proprietà di confine, e MCP inbound la spezza (`AR-AP-27`); nessun documento l'aveva notato. **`A06`: `ADR-049` riceve la sua traduzione al confine Odoo** (`AR-AP-19`). `A11`: l'outbox riceve il primo consumatore, ed è **pull**. `A12`: nove metriche nuove, tre come righe per rispettare il budget di cardinalità. `A09`: precisato che la superficie autentica **una sola metà** del dual principal. **Tensione dichiarata**: il «contract test» che `A17` chiedeva sono in realtà **cinque contratti, uno solo dei quali non è nostro** — da cui la separazione fra gate deterministico e gate notturno |
| **IMPACT ON FUTURE** | **`A15`**: `T-AP-01` ha scadenza ancorata al momento in cui `A15` fissa la versione di Odoo; reverse proxy con timeout > `wait` massimo; `Q-03` decide se i webhook funzionano affatto · **`A16`**: tre gate nuovi (`G-AP-01/02/03`) nel registro `tests.yaml`, ciascuno col suo caso negativo · **`C24`**: `retention(idempotency_record) ≥ retention(run)` entra in `DEF-13` · **`C26`**: audit dell'API, e l'export come canale di esfiltrazione (`R-94`) |
| **DAY-1** | in ordine: (1) specifica OpenAPI 3.1 **prima del codice**; (2) autenticazione + tenant resolution + `idempotency_record` con vincolo UNIQUE; (3) i 24 endpoint; (4) SSE + feed pull; (5) `connectors/odoo/` a sei moduli; (6) `budget.py` + colonna e trigger su `run_tree`; (7) probe di schema all'avvio; (8) i tre gate coi casi negativi; (9) le otto classi negative sui 24 endpoint. **Zero servizi nuovi, zero broker, zero gateway** |
| **FUTURE** | webhook (`T-AP-03`) · SDK generati · MCP outbound · **MCP inbound solo `READ`** (`AR-AP-27`) · A2A fase 3 · HTTP/gRPC interno solo se multi-nodo (`T-AP-09`) · `transport.py` riscritto (`T-AP-02`) · secondo connector **solo** se `Q-01` cambia (`T-AP-06`, ed è il momento in cui `AR-020` è soddisfatta davvero) |
| **ADR CANDIDATES** | `ADR-284` … `ADR-297` (14). I portanti: `ADR-285`, `ADR-290`, `ADR-293`, `ADR-294` |
| **CONFIDENCE** | **Alta** su: separazione delle due superfici, modello asincrono (**derivato**, non scelto), idempotenza a due livelli (l'esempio del documento dimostra che non si sostituiscono), isolamento del trasporto, rifiuto di GraphQL, `INV-45`. **Media** su: le sette classi negative (**pertinenti perché derivate dalle nostre difese, quindi ne ereditano i buchi**), `ADR-288`, `ADR-294` nella forma. **Bassa** su: `B-53` e tutto ciò che ne dipende (`AS-66` è un'ipotesi su una specifica non vista), **tutti** i valori numerici (`DEF-21`), `ADR-287` (poggia su `AS-44`, Bassa), la tenuta della disciplina di test (192 test contro `R-97` che è Alta), e la completezza del threat model — per la stessa ragione per cui `A13` non pretendeva di essere completo |

> **`DEF-21` merita di essere letta come una scelta, non come una lacuna.** Rate limit, quote,
> `wait` massimo, timeout, budget, finestra di deprecazione: **i criteri sono scritti, i numeri
> mancano, e nessuno è stato inventato.** Scadenza: prima del primo tenant reale.

---

## 10. Domande aperte

| ID | Domanda | Blocca |
|---|---|---|
| Q-01 | Il CRM target è Odoo o un CRM generico? Cambia radicalmente il Tool Layer | A06, A18 |
| Q-02 | Esistono requisiti di SLA/RPO/RTO dichiarati dal committente? | A13, C24 |
| Q-03 | Il deployment è SaaS, on-prem presso cliente, o entrambi Day-1? | A15, B19 |
| Q-04 | Volume atteso di documenti per la knowledge base? **Ancora aperta dopo `A07`**: il documento dichiara cosa cambia per ogni ordine di grandezza invece di inventare un numero. A rompersi per prima non è pgvector, è l'embedding su CPU (~10⁶ chunk) | A07 (fatto, con `AS-16` a confidenza bassa), B21, B23 |
