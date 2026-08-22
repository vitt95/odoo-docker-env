# AI CRM Agent — Analisi completa di architettura, costi, infrastruttura, parallelismo e scalabilità (2026)

## Executive summary

Per il progetto descritto — un **AI Agent general-purpose integrabile in CRM, web app, mobile app, ERP e altri software**, capace di interrogazioni, CRUD, tool use, automazioni, workflow, task asincroni e azioni autonome — un percorso **open-source/open-weight è tecnicamente ed economicamente sensato**.

La scelta iniziale di **Qwen3.5-9B** è compatibile con questa strategia perché il modello può essere eseguito localmente in quantizzazione 4-bit su una GPU relativamente piccola. Un benchmark pubblico su RTX 4090 riporta per Qwen3.5-9B Q4_K_M un file di circa 5.24 GiB, circa 5.83 GiB di VRAM aggiuntiva sopra l'idle nel test e ~122.9 tok/s in generazione su un workload `tg128`; un altro benchmark indipendente riporta 5.23 GiB e circa 61 tok/s su Apple MTL/CPU-specifico. Questi dati mostrano bene la variabilità in base a hardware e runtime: non devono essere interpretati come SLA. citeturn924381search8turn924381search0

La conclusione più importante è:

> **Il collo di bottiglia di un agente enterprise non è quasi mai il solo modello. È la combinazione di inference concurrency + KV cache + numero di model calls per task + tool latency + stato + database + policy + reliability.**

Per questo il progetto va costruito attorno a:

```text
Application
  ↓
Agent Gateway
  ↓
Agent Orchestrator
  ↓
Policy / Capability Layer
  ↓
Model Router
  ↓
Qwen / eventuali altri modelli
  ↓
Tool Runtime
  ↓
CRM / ERP / APIs / Knowledge
  ↓
Workflow / Async Execution
  ↓
Audit / Observability / Evaluation
```

La strategia economica raccomandata è:

```text
Fase 1 → hardware locale / dev
Fase 2 → singola GPU dedicata
Fase 3 → 2+ inference replicas + queue + HA database
Fase 4 → cluster GPU / cloud burst / multi-region
```

vLLM oggi offre già continuous batching, gestione KV cache, tool calling, structured outputs, LoRA, metriche, tracing e un Production Stack per deployment Kubernetes, riducendo drasticamente il software di inference che devi costruire in proprio. citeturn924381search2turn924381search4turn924381search6

---

# 1. L'obiettivo del prodotto

Il sistema non dovrebbe essere progettato come:

```text
Chatbot
  ↓
LLM
```

ma come una:

> **Agent Execution Platform**

capace di eseguire:

- interrogazioni CRM;
- ricerca;
- analytics;
- CRUD;
- assegnazioni;
- task;
- email;
- meeting;
- automazioni;
- workflow;
- processi asincroni;
- customer service;
- enrichment;
- forecasting;
- knowledge management;
- decision support;
- azioni autonome;
- integrazioni con ERP e sistemi esterni;
- eventuale multi-agent.

---

# 2. Catalogo operativo dell'agente CRM

## 2.1 Read / query

```text
find_customer
search_contacts
search_leads
search_opportunities
search_cases
search_products
search_tasks
search_activities
get_customer
get_contact
get_opportunity
get_case
get_order
get_task
get_customer_timeline
get_opportunity_history
get_case_history
count
sum
average
group_by
trend
conversion_rate
pipeline_value
revenue_by_segment
```

## 2.2 CRUD

```text
create_contact
create_lead
create_opportunity
create_case
create_task
create_note
create_activity
create_quote

update_contact
update_lead
update_opportunity
update_case
update_task

delete_record
archive_record
merge_record
```

## 2.3 Relazioni

```text
link_contact_to_account
link_contact_to_opportunity
assign_owner
assign_sales_rep
add_stakeholder
remove_stakeholder
move_opportunity_stage
associate_case_to_customer
```

## 2.4 Sales

```text
research_lead
enrich_lead
score_lead
qualify_lead
convert_lead
assign_lead

research_opportunity
assess_risk
identify_stakeholders
summarize_deal
recommend_next_action
update_stage
create_followup

pipeline_analysis
forecast
risk_analysis
deal_probability
revenue_projection
```

## 2.5 Comunicazioni

```text
draft_email
send_email
reply_email
forward_email
schedule_email
followup_email

send_sms
send_whatsapp
send_chat
reply_customer

schedule_meeting
reschedule_meeting
cancel_meeting
invite_participants
summarize_meeting
extract_actions
```

## 2.6 Task management

```text
create_task
assign_task
update_task
complete_task
cancel_task
prioritize_task
reschedule_task
delegate_task

create_task_from_email
create_task_from_meeting
create_task_from_case
create_task_from_opportunity
```

## 2.7 Automation

```text
create_workflow
update_workflow
enable_workflow
disable_workflow
create_trigger
create_schedule
```

Pattern:

```text
event
  ↓
condition
  ↓
action 1
  ↓
action 2
  ↓
action 3
```

## 2.8 Customer service

```text
create_case
classify_case
prioritize_case
assign_case
update_case
retrieve_case_history
draft_response
send_response
escalate_case
resolve_case
close_case
reopen_case
```

## 2.9 Knowledge

```text
search_knowledge
create_knowledge
update_knowledge
validate_knowledge
publish_knowledge
archive_knowledge
```

## 2.10 Intelligence / research

```text
research_customer
research_company
research_lead
research_opportunity
research_competitor
analyze_account
detect_risk
detect_churn
find_anomalies
identify_patterns
recommend_actions
```

---

# 3. Reference architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         APPLICATIONS                             │
│ CRM UI │ Mobile │ Web │ Slack │ Email │ API │ Background Event │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         AGENT GATEWAY                            │
│ OAuth / OIDC │ tenant │ user identity │ rate limit │ sessions    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     AGENT ORCHESTRATOR                           │
│ Intent │ Planning │ State │ Routing │ Policies │ Retry │ Timeout │
└──────────────┬───────────────────┬───────────────────────────────┘
               │                   │
               │                   ▼
               │          ┌──────────────────┐
               │          │  KNOWLEDGE LAYER │
               │          │ RAG / CRM / Docs │
               │          │ Memory / State   │
               │          └──────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                         MODEL LAYER                              │
│ Model Router                                                     │
│ Qwen │ Gemma │ Llama │ Cloud fallback                           │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         TOOL LAYER                               │
│ MCP / Internal tools / APIs / Functions                         │
│ CRM │ ERP │ Email │ Calendar │ Payments │ Search │ Documents     │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     POLICY / SECURITY                            │
│ RBAC │ ABAC │ scopes │ approval │ validation │ limits            │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     EXECUTION / WORKFLOW                        │
│ sync │ async │ scheduled │ event-driven │ retry │ compensation   │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                 OBSERVABILITY / GOVERNANCE                       │
│ OpenTelemetry │ audit │ evaluations │ metrics │ feedback         │
└──────────────────────────────────────────────────────────────────┘
```

---

# 4. Il modello deve essere sostituibile

Non:

```text
Application
  ↓
Qwen-specific code
  ↓
CRM
```

Ma:

```text
Application
  ↓
Agent Runtime
  ↓
Model Router
  ↓
┌───────────────┬──────────────┬──────────────┐
│ Qwen          │ Gemma        │ Cloud API    │
└───────────────┴──────────────┴──────────────┘
```

Questo permette:

- self-hosting;
- fallback;
- A/B test;
- sostituzione futura del modello;
- modelli diversi per task diversi;
- eventuale LoRA specifico.

---

# 5. Stack open-source consigliato

## Inference

### vLLM

Scelta preferita per produzione GPU.

Supporta:

- continuous batching;
- KV cache;
- prefix caching;
- tool calling;
- structured output;
- LoRA;
- distributed inference;
- metriche;
- OpenTelemetry;
- Kubernetes;
- routing e scaling.

Il Production Stack ufficiale include Helm, Grafana e routing model-aware/prefix-aware; supporta anche strategie di ottimizzazione del KV cache. citeturn924381search2turn924381search1

## Development / hardware molto limitato

### llama.cpp

Ottimo per:

- laptop;
- desktop;
- prototipazione;
- CPU/GPU consumer;
- GGUF.

## Backend

```text
Python
FastAPI
```

## Database

```text
PostgreSQL
pgvector
```

## Cache / queue

Inizialmente:

```text
PostgreSQL
```

poi:

```text
Redis
```

quando serve.

## Observability

```text
OpenTelemetry
Prometheus
Grafana
```

## Container

```text
Docker
```

## Orchestration iniziale

```text
Docker Compose
```

poi eventualmente:

```text
Kubernetes
```

---

# 6. Qwen3.5-9B: requisiti hardware

Una quantizzazione Q4_K_M di Qwen3.5-9B è nell'ordine di 5.2–5.3 GiB per i pesi.

Un benchmark su RTX 4090 24 GiB riporta:

| Quantizzazione | Dimensione | tok/s generation | Peak VRAM sopra idle |
|---|---:|---:|---:|
| F16 | 16.69 GiB | 211.9 | 16.2 GiB |
| Q8_0 | 8.87 GiB | 85.1 | 9.1 GiB |
| Q6_K | 6.85 GiB | 99.35 | 7.24 GiB |
| Q5_K_M | 6.02 GiB | 113.97 | 6.52 GiB |
| **Q4_K_M** | **5.24 GiB** | **122.88** | **5.83 GiB** |
| Q3_K_M | 4.31 GiB | 140.83 | 5.01 GiB |

Questi valori sono specifici del benchmark, hardware e runtime usati e non costituiscono uno SLA. Sono però molto utili per capire l'ordine di grandezza. citeturn924381search8

Un altro benchmark pubblico su Q4 mostra ~61 tok/s su un backend Apple/MTL per `tg128`, dimostrando quanto l'hardware e il runtime influenzino fortemente la velocità. citeturn924381search0

---

# 7. Perché VRAM ≠ solo peso del modello

La memoria necessaria non è:

```text
VRAM = model_size
```

ma più simile a:

```text
VRAM =
model weights
+
KV cache
+
runtime buffers
+
CUDA graphs / compilation
+
batching
+
temporary buffers
```

Il **KV cache** cresce con il numero di richieste concorrenti e con la lunghezza dei contesti.

vLLM espone esplicitamente `kv_cache_memory` e `max_concurrency`; la documentazione indica che la capacità teorica di concorrenza dipende dalla quantità di KV cache disponibile e dalla lunghezza massima per richiesta. citeturn924381search4turn924381search6

---

# 8. La concorrenza è il vero problema

Supponiamo:

```text
1 utente
```

La GPU può dedicarsi quasi tutta alla sua richiesta.

Con:

```text
10 utenti simultanei
```

vLLM può schedulare e batchare token provenienti dalle varie richieste.

Con:

```text
50 utenti simultanei
```

non significa necessariamente che 50 utenti siano serviti istantaneamente.

Significa:

> 50 richieste condividono una capacità di calcolo e una KV cache finite.

La capacità utile dipende da:

- prompt length;
- output length;
- context length;
- numero di tool call;
- numero di model calls;
- batch size;
- GPU;
- quantizzazione;
- target latency;
- modello;
- CPU/RAM;
- networking.

---

# 9. Continuous batching

Questo è uno dei motivi per cui un inference server come vLLM è fondamentale.

Senza batching:

```text
Request A
  ↓
GPU
  ↓
Request B
  ↓
GPU
```

Con continuous batching:

```text
Request A ─┐
Request B ─┼─→ Scheduler → GPU
Request C ─┤
Request D ─┘
```

Il sistema può aggiungere e rimuovere richieste mentre il batch evolve.

Questo aumenta molto l'utilizzo della GPU e permette di servire più utenti concorrenti, al prezzo di una gestione più complessa della latenza. vLLM supporta continuous batching e configurazioni di throughput/concurrency mirate al capacity planning. citeturn924381search6

---

# 10. Throughput ≠ concurrency ≠ utenti

Questi tre numeri devono essere separati.

## Utenti

Quante persone hanno accesso al sistema.

## Concurrency

Quante richieste agentiche sono attivamente in esecuzione nello stesso momento.

## Throughput

Quante unità di lavoro il sistema completa per unità di tempo.

Ad esempio:

```text
1.000 utenti registrati
```

potrebbero generare soltanto:

```text
5 richieste concorrenti
```

in media.

Viceversa:

```text
100 utenti
```

potrebbero generare:

```text
50 richieste concorrenti
```

durante un picco.

Quindi **non è corretto dire "una GPU supporta 100 utenti" senza specificare il workload**.

---

# 11. Una metrica migliore: Agent Task

Per un CRM agentico bisogna misurare:

```text
completed business tasks / second
```

e non solamente:

```text
tokens / second
```

Definizione utile:

```text
Agent Task Cost =
GPU
+
CPU
+
DB
+
network
+
storage
+
observability
+
retries
+
failed work
```

diviso:

```text
completed tasks
```

---

# 12. Esempio di task semplice

Task:

> "Qual è il valore della pipeline?"

Possibile percorso:

```text
user
 ↓
intent
 ↓
query CRM
 ↓
result
 ↓
response
```

Potrebbe richiedere:

```text
1 model call
+
1 tool call
```

Questo è relativamente economico.

---

# 13. Esempio di task medio

Task:

> "Trova i lead inattivi da 90 giorni e crea un follow-up."

Possibile:

```text
LLM
 ↓
search_leads
 ↓
result
 ↓
LLM
 ↓
classify
 ↓
create_task
```

Quindi:

```text
2 model calls
+
2 tool calls
```

---

# 14. Esempio di task pesante

Task:

> "Analizza tutta la pipeline enterprise, individua le opportunità a rischio, studia lo storico, prepara una strategia e crea le attività."

Possibile percorso:

```text
LLM
 ↓
search opportunities
 ↓
retrieve histories
 ↓
aggregate
 ↓
LLM
 ↓
reason
 ↓
identify risks
 ↓
LLM
 ↓
generate actions
 ↓
create tasks
 ↓
verify
```

Qui possono esserci:

```text
5–10+ model calls
+
molti tool calls
+
query DB
+
RAG
+
workflow state
```

La differenza di costo e latenza rispetto al task semplice è enorme.

---

# 15. Task pesanti: non lasciarli in HTTP sincrono

Per operazioni lunghe:

```text
POST /agent/tasks
```

ritorna:

```text
202 Accepted
```

con:

```text
task_id
```

poi:

```text
Queue
 ↓
Worker
 ↓
Agent
 ↓
Tool calls
 ↓
Result
```

Il client può seguire:

```text
GET /tasks/{task_id}
```

oppure usare:

```text
SSE
WebSocket
Webhook
```

Questo evita che un task lungo blocchi un web server.

---

# 16. Stati del task

Consigliati:

```text
RECEIVED
CLASSIFIED
PLANNED
RUNNING
WAITING_FOR_INPUT
WAITING_FOR_APPROVAL
WAITING_FOR_EXTERNAL_SYSTEM
RETRYING
VERIFYING
COMPLETED
FAILED
CANCELED
ESCALATED
```

---

# 17. Quanto utenti può supportare una GPU?

Non esiste un numero universale.

La risposta corretta è:

> **una GPU supporta un certo carico, non un certo numero di utenti.**

Per Qwen3.5-9B Q4 su hardware tipo RTX 4090, un benchmark mostra ~123 tok/s in generazione su un determinato workload. citeturn924381search8

Questo consente di fare una stima concettuale.

### Esempio puramente illustrativo

Supponiamo:

```text
4 model calls / task
1.000 output token complessivi / task
```

Con 123 tok/s, una singola stream seriale avrebbe:

```text
1.000 / 123 ≈ 8,1 secondi
```

di sola generazione complessiva.

Con 4.000 token:

```text
4.000 / 123 ≈ 32,5 secondi
```

Questo **non significa** che un sistema vLLM reale impiegherà esattamente 32,5 secondi per task: batching, prompt processing, KV cache e parallelismo cambiano molto il risultato.

Serve solo a capire perché un task con molte generazioni diventa rapidamente costoso.

---

# 18. Un'altra metrica: task/minuto

Supponiamo ipoteticamente un workload medio:

```text
1.000 generated tokens / task
```

e una capacità effettiva sostenibile di:

```text
100 generated tok/s
```

allora:

```text
100 / 1.000
= 0,1 task/s
= 6 task/min
= 360 task/hour
```

Se ogni task dura in media 4 model calls con 250 token medi ciascuna, la quantità totale di lavoro generativo resta 1.000 token/task.

Questo esempio è volutamente semplificato.

La capacità reale va misurata con benchmark di concurrency, come raccomandato dalla stessa documentazione vLLM. citeturn924381search6

---

# 19. Perché utenti simultanei non significano 1:1 richieste GPU

Supponiamo:

```text
100 utenti
```

ma:

```text
10% attivi nello stesso momento
```

hai:

```text
10 concurrent requests
```

Se ogni richiesta dura mediamente:

```text
10 secondi
```

e il sistema completa:

```text
60 tasks/min
```

puoi servire un volume ben maggiore di 60 utenti totali.

Il modello di capacity planning deve quindi usare:

```text
Peak concurrency
+
requests/minute
+
tokens/request
+
task complexity
+
SLA latency
```

non il numero di account.

---

# 20. Capacity planning: modello pratico

Per ogni tenant/cliente raccogli:

```text
active_users
requests_per_user_per_day
peak_concurrency
tokens_per_request
model_calls_per_task
tool_calls_per_task
avg_task_duration
p95_task_duration
```

Poi:

```text
GPU demand
≈
peak generated tokens/sec
÷
sustainable generated tokens/sec per GPU
```

con un margine operativo:

```text
target utilization
≈ 60–80%
```

Il valore preciso va stabilito tramite benchmark del tuo workload.

---

# 21. Perché non usare il 100% della GPU

Perché a saturazione completa:

- la latenza tende a peggiorare;
- la coda cresce;
- i picchi diventano pericolosi;
- una richiesta lunga può penalizzare le altre;
- il sistema ha meno margine per retry e burst.

Per questo la capacità utile va misurata ben sotto il limite teorico.

La documentazione vLLM suggerisce, per i test di capacity planning, di testare realisticamente il limite di concurrency e tenere un margine rispetto alla capacità massima teorica della KV cache. citeturn924381search6

---

# 22. Concorrenza e KV cache

vLLM mostra esplicitamente una relazione tra:

```text
KV cache capacity
```

e:

```text
maximum concurrency at a given max_model_len
```

La documentazione fornisce anche un esempio:

```text
GPU KV cache size: 15,728,640 tokens
max concurrency for 8,192 tokens/request: 1920
```

Il valore è un esempio della documentazione, non una capacità da attribuire a Qwen3.5-9B su qualsiasi GPU. citeturn924381search6

La lezione architetturale è:

> **più lungo è il contesto massimo che vuoi mantenere, minore può essere la concurrency disponibile a parità di VRAM.**

---

# 23. Context length e performance

Non imposterei:

```text
max_model_len = 262k
```

per ogni richiesta solo perché il modello lo supporta.

Per un CRM agent, spesso è meglio:

```text
short context
+
RAG
+
retrieval
+
state
```

invece di:

```text
huge context
```

Questo migliora:

- VRAM;
- latency;
- throughput;
- costo;
- precisione del retrieval.

---

# 24. Prefix caching

Se molti utenti usano lo stesso:

```text
system prompt
+
tool schemas
+
policy
```

il prefix cache può evitare di ricalcolare parti identiche.

Questo diventa particolarmente interessante per un agent CRM con:

```text
tool registry
+
business policy
+
system instructions
```

uguali tra molte richieste.

vLLM supporta prefix-aware routing e strategie di caching per migliorare performance quando i prompt condividono prefissi. citeturn924381search1turn924381search2

---

# 25. Parallelismo: cosa succede realmente

Il parallelismo ha più livelli.

## Livello 1 — parallelismo tra utenti

```text
User A ─┐
User B ─┼→ vLLM scheduler
User C ─┤
User D ─┘
```

È il caso più comune.

## Livello 2 — parallelismo tra tool

Se il task richiede:

```text
CRM query
+
Calendar query
+
Knowledge search
```

e sono indipendenti, il workflow può eseguirli in parallelo:

```text
             Agent
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
     CRM     Calendar   RAG
      │        │        │
      └────────┼────────┘
               ▼
             Qwen
```

Questo riduce molto la latenza.

## Livello 3 — parallelismo tra GPU

```text
Load balancer
    │
 ┌──┼──┐
 ▼  ▼  ▼
GPU1 GPU2 GPU3
```

Per un 9B, questo è generalmente più utile del mettere lo stesso modello in tensor parallel su più GPU, almeno nelle fasi iniziali.

---

# 26. Scale-out vs scale-up

## Scale-up

Una GPU più grande:

```text
L4
→ RTX 6000
→ GPU più grande
```

vantaggi:

- più VRAM;
- più throughput per replica;
- gestione contesti più lunghi.

svantaggi:

- costo maggiore;
- single point of failure se c'è una sola GPU.

## Scale-out

Più GPU:

```text
GPU1
GPU2
GPU3
GPU4
```

vantaggi:

- maggiore concurrency;
- fault tolerance;
- rolling deployment;
- horizontal scaling.

Per un modello da 9B, il **scale-out** è spesso più naturale per servire utenti piuttosto che il tensor parallel su GPU enormi.

---

# 27. Quando è davvero necessaria una seconda GPU?

Non quando hai:

```text
10 utenti registrati
```

Ma quando hai:

```text
peak concurrency
>
capacity sostenibile della prima replica
```

o:

```text
SLA
richiede
zero downtime
```

o:

```text
background jobs
rubano capacità
alle chat interattive
```

o:

```text
tenant enterprise
richiede isolamento
```

---

# 28. Un solo server per MVP

Configurazione:

```text
1 GPU
64 GB RAM
NVMe
PostgreSQL
vLLM
Backend
```

Può bastare per:

- demo;
- pilot;
- piccoli clienti;
- sviluppo;
- validazione del product-market fit.

Non è HA.

---

# 29. Due GPU per la prima vera produzione

Configurazione:

```text
Load Balancer
   │
 ┌─┴───────────────┐
 ▼                 ▼
vLLM GPU 1      vLLM GPU 2
 │                 │
 └────────┬────────┘
          ▼
     Agent Queue
          │
          ▼
      PostgreSQL
```

Vantaggi:

- rolling deployment;
- manutenzione senza downtime;
- failover;
- parallelismo;
- separazione dei task.

---

# 30. Separare interactive e background workloads

Questa è una decisione architetturale molto importante.

Non fare:

```text
                    GPU
                     │
      ┌──────────────┼──────────────┐
      │              │              │
   Chat 1         Chat 2         Background
```

senza priorità.

Meglio:

```text
                    Workload Router
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Interactive                Async
        high priority             low priority
              │                       │
              ▼                       ▼
          vLLM pool A             vLLM pool B
```

All'inizio, i due pool possono anche essere logici e usare la stessa GPU; in produzione puoi separarli.

---

# 31. Priority scheduling

Task:

```text
"Dimmi il cliente X"
```

dovrebbe avere priorità maggiore di:

```text
"Analizza 20.000 clienti per churn"
```

Il sistema dovrebbe quindi avere almeno:

```text
priority:
  realtime
  interactive
  background
  batch
```

Questo impedisce che un task analitico lungo blocchi le interazioni umane.

---

# 32. Task pesanti: usa job queue

Per:

- analisi di migliaia di record;
- enrichment;
- churn analysis;
- recap di grandi dataset;
- batch email drafting;
- knowledge generation;

usare:

```text
Job Queue
+
Worker
+
Checkpoint
```

Non una singola richiesta HTTP.

---

# 33. Checkpoint dei task

Se un task deve analizzare:

```text
50.000 clienti
```

non bisogna fare:

```text
one giant LLM run
```

Meglio:

```text
50.000
 ↓
chunks
 ↓
worker
 ↓
checkpoint
 ↓
aggregate
 ↓
final reasoning
```

Questo consente:

- retry parziale;
- resume;
- parallelismo;
- controllo dei costi;
- progress reporting.

---

# 34. Map / Reduce agentico

Esempio:

```text
50k customers
      ↓
   MAP
 ┌────┼────┐
 ▼    ▼    ▼
worker worker worker
 └────┼────┘
      ▼
   REDUCE
      ↓
  Qwen final
```

È una delle architetture più adatte per task analitici pesanti.

---

# 35. Quando CPU diventa importante

Il sistema non è solo GPU.

CPU serve per:

- API;
- preprocessing;
- retrieval;
- parsing;
- DB;
- JSON validation;
- tool execution;
- queue;
- embeddings;
- orchestration.

Con task intensivi di RAG o SQL, una GPU veloce può diventare inutile se:

```text
DB query = 2 s
API = 3 s
LLM = 0.8 s
```

Il collo di bottiglia non è più il modello.

---

# 36. Database scaling

Per un primo prodotto:

```text
PostgreSQL
```

basta.

Poi:

```text
Read replicas
Connection pooling
Partitioning
Indexes
pgvector tuning
```

Solo dopo eventualmente:

```text
separate vector DB
Elastic
ClickHouse
data warehouse
```

La regola:

> **non introdurre un componente distribuito finché un benchmark non dimostra la necessità.**

---

# 37. Memory architecture

Separare:

### Conversation state

```text
session
messages
current task
```

### Long-term memory

```text
preferences
business context
past outcomes
```

### CRM truth

```text
database
```

### Knowledge

```text
RAG
```

Non mettere tutto nella context window.

---

# 38. Context window e parallelismo

Se ogni richiesta porta:

```text
100k tokens
```

anche se la generazione è breve, la pressione su:

```text
prefill
KV cache
memory bandwidth
latency
```

diventa elevata.

Per un sistema enterprise conviene quindi:

```text
retrieval
+
summaries
+
state
+
small context
```

anziché inviare continuamente lo storico completo.

---

# 39. Hardware: livelli pratici

## Livello A — Development

```text
CPU
32 GB RAM
GPU opzionale 8–16 GB
```

Usare:

```text
Qwen Q4
llama.cpp
```

Costo:

```text
€0–1.500
```

a seconda dell'hardware che già possiedi.

---

## Livello B — MVP

```text
1 GPU
16–24 GB VRAM
64 GB RAM
2 TB NVMe
```

Esempio:

```text
RTX 4000 SFF Ada 20 GB
```

Hetzner propone il GEX44 con RTX 4000 SFF Ada 20 GB e 64 GB RAM come server dedicato adatto a modelli 7B–14B. Il prezzo pubblicato per GEX44-1 è oggi €232,30/mese + setup, IVA esclusa. citeturn177941search4turn177941search5

---

## Livello C — Production

```text
2 GPU
+
2 application nodes
+
Postgres HA
+
Redis / Queue
+
object storage
+
backup
```

---

## Livello D — Enterprise

```text
multiple GPU replicas
+
multi-zone
+
HA DB
+
WAF
+
SIEM
+
DR
+
private networking
+
audit
```

---

# 40. Cloud GPU

Google Cloud oggi pubblica per NVIDIA L4 24 GB un prezzo GPU on-demand di circa **$0,56004/ora** per GPU; le VM G2 complete costano di più. Una `g2-standard-4` con una L4 e 16 GiB RAM è pubblicata a circa **$0,70683/ora**. citeturn177941search0turn177941search1

Ordine di grandezza 24/7:

```text
$0.70683 × 730
≈ $516/mese
```

prima di:

- storage;
- network;
- database;
- load balancer;
- log;
- backup.

Google offre anche prezzi commitment e Spot, che possono ridurre sensibilmente il costo. citeturn177941search0turn177941search3

---

# 41. Dedicated GPU vs Cloud

| | Dedicated GPU | Cloud |
|---|---|---|
| Costo prevedibile | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Scalabilità | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Burst | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| HA | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Sovranità dati | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Semplicità | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Costo MVP | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

Strategia consigliata:

```text
Development → local
MVP → dedicated GPU
Growth → hybrid
Enterprise → multi-node / cloud / private
```

---

# 42. Costo infrastrutturale indicativo

## Prototype

```text
€0–100/mese
```

con:

- hardware locale;
- Docker;
- PostgreSQL;
- Qwen locale.

## MVP / pilot

```text
€250–500/mese
```

con:

- 1 GPU server;
- application server;
- DB;
- backup;
- monitoring.

## Primi clienti

```text
€700–1.500/mese
```

con:

- 2 backend;
- 1–2 GPU nodes;
- Postgres HA;
- Redis;
- object storage;
- monitoring;
- backup.

## Enterprise piccolo

```text
€2k–10k+/mese
```

con:

- più GPU;
- multi-zone;
- HA;
- WAF;
- SIEM;
- DR;
- private networking;
- logging avanzato.

Sono ordini di grandezza, non preventivi.

---

# 43. Costo di sviluppo

## Prototype

```text
400–800 ore
```

Possibile contenuto:

- agent;
- tool calling;
- CRM connector;
- RAG;
- basic UI;
- auth;
- local deployment.

## MVP serio

```text
1.200–2.500 ore
```

Con:

- multi-user;
- multi-tenant;
- permissions;
- workflows;
- async jobs;
- MCP;
- memory;
- observability;
- audit;
- retry;
- evaluation;
- deployment;
- administration.

## Production v1

```text
2.500–5.000 ore
```

Con:

- HA;
- security hardening;
- backups;
- DR;
- scaling;
- comprehensive evaluation;
- API stability;
- migration tooling.

## Enterprise maturo

```text
5.000–10.000+ ore
```

Se servono:

- SSO/SAML;
- SCIM;
- RBAC/ABAC;
- private deployment;
- on-prem;
- VPC deployment;
- data residency;
- SOC2/ISO 27001;
- enterprise SLA;
- advanced support.

---

# 44. Valore economico dell'engineering

Con range indicativi di €60–120/h:

### Prototype

```text
400h × €60 = €24k
800h × €100 = €80k
```

### MVP

```text
1.200h × €60 = €72k
2.500h × €100 = €250k
```

### Production

```text
2.500h × €70 = €175k
5.000h × €110 = €550k
```

Questi sono valori indicativi del lavoro, non necessariamente cash da investire.

Per un founder tecnico:

```text
cash cost ↓
time cost ↑
```

---

# 45. Dove spenderei il budget

Se avessi €10k:

```text
€5.000  engineering
€1.500  hardware/inference
€1.000  security
€1.000  testing/monitoring
€500    infrastructure
€1.000  contingency
```

Se avessi €50k:

```text
€30k  product engineering
€5k   infrastructure
€5k   security/QA
€5k   integrations
€5k   contingency
```

Non spenderei il capitale iniziale in GPU enterprise enormi.

---

# 46. Il vero collo di bottiglia economico

Non è:

```text
model license
```

nel percorso open-weight.

È:

```text
engineering
+
GPU utilization
+
tool latency
+
retries
+
background workload
+
database
+
observability
+
security
```

Per questo il KPI più importante è:

> **costo per business task completato**

non costo per token.

---

# 47. Ottimizzazione numero di model calls

Questo è uno dei modi più efficaci per risparmiare.

Inefficiente:

```text
Qwen
 ↓
tool
 ↓
Qwen
 ↓
tool
 ↓
Qwen
 ↓
tool
 ↓
Qwen
```

Meglio:

```text
Workflow
 ↓
tool batch
 ↓
Qwen
 ↓
final action
```

Ridurre:

```text
8 model calls
→
3 model calls
```

può avere più impatto che passare a una GPU molto più costosa.

---

# 48. Tool parallelism

Se hai operazioni indipendenti:

```text
get_customer()
get_orders()
get_cases()
get_calendar()
```

non fare:

```text
customer
 ↓
orders
 ↓
cases
 ↓
calendar
```

se non c'è dipendenza.

Fai:

```text
           Agent
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
 customer  orders   cases
     │       │       │
     └───────┼───────┘
             ▼
          combine
```

Questo riduce la latenza end-to-end.

---

# 49. Async parallelism su task grandi

Per 100.000 record:

```text
100k
 ↓
chunk 1
chunk 2
chunk 3
...
chunk N
```

worker paralleli:

```text
Worker A
Worker B
Worker C
Worker D
```

poi:

```text
aggregate
 ↓
final model reasoning
```

Questo è molto più scalabile di un singolo mega-task.

---

# 50. Background workloads non devono competere con la chat

Implementare almeno:

```text
priority = realtime
priority = interactive
priority = background
priority = batch
```

e idealmente:

```text
interactive GPU pool
background GPU pool
```

quando il volume lo giustifica.

---

# 51. Capacity planning: tabella pratica

La seguente tabella **non è un benchmark universale**; è un modello di pianificazione iniziale.

| Scenario | Peak concurrency | Complessità | Infrastruttura iniziale consigliata |
|---|---:|---|---|
| Dev / PoC | 1–5 | bassa | 1 GPU locale |
| Pilot | 5–10 | bassa-media | 1 GPU 16–24 GB |
| Small SaaS | 10–25 | media | 1 GPU + queue + buona CPU |
| SaaS in crescita | 25–50 | media-alta | 2 GPU / 2 replicas |
| Production seria | 50–100 | media-alta | 2–4 GPU + queue + HA |
| Enterprise | 100+ | alta | GPU pool + autoscaling |

Questa classificazione va validata sul **tuo task mix reale**.

---

# 52. Perché non posso dirti "100 utenti per GPU"

Perché:

```text
100 utenti
```

possono significare:

### Scenario A

```text
1 richiesta ogni 5 minuti
```

oppure:

### Scenario B

```text
100 richieste contemporanee
```

oppure:

### Scenario C

```text
10 utenti
×
un task da 20 model calls
```

Sono carichi completamente diversi.

Il numero utile è:

```text
peak concurrent agent tasks
```

non:

```text
registered users
```

---

# 53. Una metodologia per ottenere il numero reale

Quando avrai il primo MVP:

## Step 1

Definisci 5 workload standard:

```text
T1 read/query
T2 CRM update
T3 email/task workflow
T4 research/RAG
T5 heavy multi-step analysis
```

## Step 2

Registra:

```text
input tokens
output tokens
model calls
tool calls
wall-clock time
GPU utilization
VRAM
KV cache
DB latency
```

## Step 3

Genera carico con:

```text
1
2
5
10
20
50
100
```

concurrent tasks.

## Step 4

Misura:

```text
p50 latency
p95 latency
p99 latency
tasks/min
tokens/sec
error rate
queue depth
GPU utilization
KV cache utilization
```

## Step 5

Trova il punto in cui:

```text
p95 > SLA
```

Quello è il limite di capacità della replica.

---

# 54. Benchmarking vLLM

La documentazione vLLM indica esplicitamente che il pattern:

```text
request-rate = infinity
+
max-concurrency = limit
```

è il pattern più comune per benchmark di throughput, perché simula un sistema in cui il load balancer controlla la concorrenza massima. citeturn924381search6

Questa metodologia è molto più corretta rispetto a stimare il numero di utenti guardando soltanto il tok/s.

---

# 55. Quando comprare hardware più potente?

## Non serve quando:

```text
GPU utilization < 50%
queue ~ 0
p95 latency ok
```

## Serve quando:

```text
GPU utilization > 80–90%
queue grows
p95 latency exceeds SLA
KV cache saturates
```

## Serve una seconda replica quando:

```text
capacity insufficient
OR
need HA
OR
background jobs interfere
```

---

# 56. GPU più grande o seconda GPU?

Per un modello 9B:

### preferirei seconda GPU se:

```text
model already fits
need concurrency
need HA
```

### preferirei GPU più grande se:

```text
need bigger model
need much longer contexts
need very large batch
model no longer fits
```

Questo è un punto molto importante.

---

# 57. 20 GB vs 24 GB vs 48+ GB

Per Qwen3.5-9B Q4:

### 12 GB

può essere sufficiente per alcuni deployment con attenzione a context e runtime.

### 16 GB

molto più comoda.

### 20–24 GB

eccellente per un singolo modello 9B + contesti ragionevoli + concurrency utile.

### 48+ GB

non necessaria per il modello in sé, ma utile se vuoi:

- più modelli;
- context molto lungo;
- batch elevati;
- altri processi;
- LoRA multipli;
- modelli più grandi.

---

# 58. Multi-LoRA

Una capability interessante di vLLM è poter servire adapter LoRA senza replicare necessariamente il modello base per ogni adapter.

Questo è molto utile per:

```text
Base Qwen
   │
   ├── CRM Adapter
   ├── Customer Service Adapter
   ├── Sales Adapter
   └── Client-specific Adapter
```

Tuttavia il design deve essere valutato con benchmark reali perché gli adapter aumentano complessità di scheduling e gestione.

---

# 59. Open-source come strategia commerciale

L'open-source/open-weight offre al tuo prodotto:

```text
lower model licensing cost
+
self-hosting
+
on-prem
+
data sovereignty
+
model control
+
custom fine-tuning
```

Questo è particolarmente forte nei CRM enterprise perché puoi vendere:

```text
SaaS
Private Cloud
On-Prem
```

con lo stesso runtime logico.

---

# 60. Open-source non significa zero costi

I costi che sposti sono:

```text
Licensing
  ↓
Engineering
Operations
Security
Hardware
```

Quindi l'open-source è conveniente se hai:

```text
technical capability
+
willingness to operate infrastructure
```

Nel tuo caso, data la direzione già scelta, è una strategia sensata.

---

# 61. Il vero competitive moat

Non è:

```text
Qwen
```

e non è:

```text
MCP
```

Il valore accumulabile è:

```text
CRM-specific tools
+
workflow knowledge
+
business policies
+
evaluation datasets
+
historical trajectories
+
tool execution logs
+
human feedback
```

Dopo decine di migliaia di task avrai:

```text
intent
→ plan
→ tool choice
→ arguments
→ tool results
→ final outcome
→ human feedback
```

Questo dataset può diventare il tuo vero vantaggio competitivo.

---

# 62. LoRA / QLoRA

Il fine-tuning dovrebbe essere usato per insegnare:

```text
tool selection
tool arguments
workflow behavior
business terminology
response style
policy patterns
```

Non per memorizzare:

```text
customers
prices
inventory
live CRM data
current documentation
```

Questi devono restare in:

```text
DB
RAG
APIs
Tools
```

Traction data reale → dataset → QLoRA → modello specializzato.

---

# 63. Reliability architecture

Un sistema enterprise dovrebbe avere:

```text
timeout
retry
backoff
idempotency
circuit breaker
dead-letter queue
checkpoint
compensation
```

perché gli errori più importanti non sono sempre errori del modello.

Possono essere:

```text
CRM timeout
email provider down
DB unavailable
rate limit
network failure
tool schema mismatch
external API change
```

---

# 64. Security architecture

```text
User
 ↓
Identity Provider
 ↓
Gateway
 ↓
Agent Identity
 ↓
Policy Engine
 ↓
Capability Registry
 ↓
Tool
 ↓
CRM
```

Mai:

```text
User
 ↓
LLM
 ↓
CRM admin
```

Il modello non deve essere il punto di enforcement.

---

# 65. Observability

Ogni run dovrebbe poter essere ricostruito:

```text
tenant_id
user_id
agent_id
session_id
run_id
task_id
tool_call_id
trace_id
```

E il trace:

```text
request
 ↓
router
 ↓
model
 ↓
tool
 ↓
policy
 ↓
approval
 ↓
execution
 ↓
result
```

---

# 66. Enterprise-grade significa

## Reliability

```text
99.9%+
```

come obiettivo iniziale ragionevole per un SaaS serio, con SLA effettivo da definire in base al prodotto.

## Security

```text
RBAC
SSO
OAuth/OIDC
secret management
encryption
audit
```

## Agent safety

```text
policy
approval
tool permissions
rate limits
sandbox
```

## Observability

```text
metrics
logs
traces
agent traces
tool traces
cost
latency
```

## Scalability

```text
horizontal workers
GPU replicas
queue
async tasks
```

## Governance

```text
versioning
evaluation
model registry
prompt versioning
audit
```

## Recovery

```text
backup
restore
DR
retry
idempotency
compensation
```

---

# 67. Open-source vs closed API

| Dimension | Open-weight self-hosted | Closed API |
|---|---|---|
| Licenza model | molto bassa / zero | usage-based |
| Capex | maggiore | minimo |
| Opex | prevedibile | variabile |
| Data control | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| On-prem | ⭐⭐⭐⭐⭐ | ⭐ |
| Latency control | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Scalability | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Engineering burden | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Custom LoRA | ⭐⭐⭐⭐⭐ | dipende dal provider |
| Model portability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Compliance/customization | ⭐⭐⭐⭐⭐ | dipende dal provider |
| Time to market | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

La strategia migliore per il tuo progetto non è necessariamente "100% open-source per sempre", ma:

> **open-weight come default + cloud fallback opzionale.**

---

# 68. Architettura ibrida consigliata

```text
                    MODEL ROUTER
                         │
         ┌───────────────┼────────────────┐
         │               │                │
      Local Qwen      Local small       Cloud
         │               │                │
      standard         simple          complex
        tasks           tasks          reasoning
```

Esempio:

```text
90% simple/standard
→ Qwen locale

10% hard
→ cloud frontier
```

Questo crea una combinazione molto forte tra:

- costo;
- privacy;
- performance;
- qualità.

La percentuale va misurata, non assunta.

---

# 69. Degraded mode

Se la GPU è offline:

```text
Qwen unavailable
       ↓
cloud fallback
```

Se anche il cloud non è disponibile:

```text
READ-only mode
```

Questo aumenta molto la resilienza del prodotto.

---

# 70. Multi-tenant

Per un SaaS:

```text
tenant
user
agent
memory
tools
documents
logs
permissions
```

devono essere logicamente isolati.

Ogni entità applicativa dovrebbe essere associata a:

```text
tenant_id
```

e il policy layer deve impedirne il bypass.

---

# 71. On-premise

Uno dei maggiori vantaggi dell'open-weight è offrire:

```text
Cloud SaaS
Private Cloud
On-Prem
```

con:

```text
Qwen
vLLM
Docker/K8s
Postgres
MCP
Agent Runtime
```

Questo è particolarmente interessante per aziende con:

- dati sensibili;
- requisiti di data residency;
- policy di non-esfiltrazione;
- esigenze di deployment privato.

---

# 72. Perché l'enterprise è possibile anche con hardware "normale"

Enterprise non significa automaticamente:

```text
H100
A100
```

Significa:

```text
HA
+
security
+
observability
+
backup
+
DR
+
reliability
+
scaling
```

Puoi avere un software enterprise-grade su hardware relativamente economico se il runtime è progettato correttamente.

---

# 73. Roadmap infrastrutturale

## Fase 0 — Development

```text
Developer PC
+
Qwen Q4
+
Docker Compose
+
PostgreSQL
```

Costo infrastrutturale:

```text
€0–100/mese
```

## Fase 1 — Pilot

```text
1 GPU dedicated
+
backend
+
Postgres
+
monitoring
```

Costo:

```text
€250–500/mese
```

## Fase 2 — First customers

```text
2 backend nodes
+
1–2 GPU nodes
+
Postgres HA
+
Redis/Queue
+
Object Storage
+
Backups
```

Costo:

```text
€700–1.500/mese
```

## Fase 3 — Enterprise

```text
Multi-zone
+
GPU replicas
+
HA DB
+
WAF
+
SIEM
+
DR
+
Private networking
+
Audit
```

Costo:

```text
€2k–10k+/mese
```

---

# 74. Roadmap software

## Milestone 1

```text
Qwen
+
single agent
+
single CRM
+
5–10 tools
```

## Milestone 2

```text
MCP
+
state machine
+
permissions
+
audit
+
async tasks
```

## Milestone 3

```text
RAG
+
workflow automation
+
queue
+
evaluation
+
observability
```

## Milestone 4

```text
Model Router
+
fallback
+
multiple providers
+
LoRA
```

## Milestone 5

```text
HA
+
multi-tenant
+
SSO
+
DR
+
enterprise deployment
```

---

# 75. Test di capacity da fare appena hai l'MVP

Definisci 5 workload:

```text
T1 = read/query
T2 = CRM update
T3 = email/task workflow
T4 = RAG/research
T5 = heavy multi-step analysis
```

Per ciascuno misura:

```text
input tokens
output tokens
model calls
tool calls
wall-clock
GPU utilization
VRAM
KV cache
DB latency
```

Poi carica:

```text
1
2
5
10
20
50
100
```

concurrent tasks.

Misura:

```text
p50
p95
p99
tasks/min
tokens/sec
queue depth
error rate
GPU utilization
KV cache usage
```

---

# 76. Soglie per decidere lo scaling

Indicativamente:

### Nessuna urgenza

```text
GPU utilization < 50%
queue ≈ 0
p95 SLA rispettato
```

### Ottimizzazione

```text
GPU 50–80%
queue crescente nei picchi
```

### Scala

```text
GPU > 80–90%
p95 oltre SLA
KV cache sotto pressione
```

### Seconda replica

```text
need HA
OR
need more concurrency
OR
background workload interferes
```

---

# 77. Regola fondamentale sui task pesanti

Non risolvere il problema sempre con:

> "GPU più potente."

Prima chiedere:

1. posso ridurre model calls?
2. posso fare tool call parallel?
3. posso usare un workflow deterministico?
4. posso chunkare il dataset?
5. posso fare async?
6. posso usare un modello piccolo?
7. posso usare cache/prefix cache?
8. devo realmente passare tutto il contesto al modello?

Solo dopo:

> "Mi serve altra GPU?"

---

# 78. TCO: la formula utile

Definire:

```text
TCO_month =
GPU
+ CPU
+ RAM
+ DB
+ Storage
+ Network
+ Monitoring
+ Backup
+ Engineering_ops
+ Incident_cost
```

e:

```text
Cost_per_task =
TCO_month / completed_business_tasks
```

Poi confrontare con:

```text
Closed_API_cost_per_task
```

La scelta tra self-hosting e API dovrebbe essere fatta su questo valore, non sul prezzo nominale per token.

---

# 79. Verdetto sul percorso open-source

## Fattibilità tecnica

**9.5/10**

## Fattibilità economica iniziale

**9.5/10**

## Qwen3.5-9B

**9/10**

## Self-hosting

**10/10**

## On-premise

**10/10**

## Possibilità di arrivare enterprise

**9/10**

## Complessità engineering

**9/10**

## Complessità security

**9/10**

## Complessità operations

**8/10**

---

# 80. Risposta alla domanda "quanti utenti posso supportare?"

La risposta corretta è:

> **Non esiste un numero fisso di utenti per GPU.**

Devi distinguere:

```text
registered users
active users
concurrent tasks
tokens/sec
tasks/min
```

Un'unica GPU da 20–24 GB con Qwen3.5-9B può essere assolutamente sufficiente per un pilot e un piccolo SaaS, ma il numero preciso di utenti dipenderà dal mix dei task.

Come ordine di progettazione iniziale:

```text
1 GPU
→ piccoli pilot / piccola concurrency

2 GPU
→ produzione con maggiore concurrency + HA

4+ GPU
→ SaaS con carico significativo / separazione interactive-background

cluster
→ enterprise con SLA e crescita
```

Questi sono **livelli infrastrutturali**, non promesse di utenti supportati.

Il numero reale deve essere determinato dal benchmark del tuo workload.

---

# 81. La mia architettura target

```text
                         USERS
                           │
                 ┌─────────┴─────────┐
                 │                   │
             Interactive          Events
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    ┌───────────────┐
                    │ API GATEWAY   │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │ AGENT RUNTIME │
                    │               │
                    │ Orchestrator  │
                    │ State         │
                    │ Policy        │
                    │ Planner       │
                    └───────┬───────┘
                            │
                    ┌───────┴────────┐
                    │ MODEL ROUTER   │
                    └───────┬────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Qwen GPU Pool    Small Model     Cloud
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                      TOOL RUNTIME
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
             CRM           RAG            APIs
                            │
                            ▼
                       PostgreSQL
                            │
                      pgvector / state
                            │
                            ▼
                       Audit / OTel
```

---

# 82. La strategia che sceglierei

## Ora

```text
Qwen3.5-9B Q4/Q5
+
vLLM
+
FastAPI
+
PostgreSQL + pgvector
+
Docker
+
MCP
+
OpenTelemetry
```

## Primo deployment remoto

```text
1 GPU dedicated
```

Un esempio concreto è il GEX44 di Hetzner:

```text
RTX 4000 SFF Ada
20 GB VRAM
64 GB RAM
```

a **€232,30/mese + setup**, IVA esclusa, secondo i prezzi pubblicati a giugno 2026. citeturn177941search4turn177941search5

## Quando cresci

```text
2 GPU replicas
+
queue
+
Postgres HA
```

## Quando entri enterprise

```text
multi-zone
+
autoscaling
+
GPU pool
+
cloud burst
+
SSO
+
SIEM
+
DR
+
private deployment
```

---

# 83. Conclusione finale

**Sì, perseguirei il progetto open-source.**

È particolarmente sensato nel tuo caso perché:

- Qwen3.5-9B può girare su hardware relativamente piccolo;
- vLLM elimina gran parte del lavoro infrastrutturale di inference;
- MCP standardizza l'integrazione dei tool;
- PostgreSQL/pgvector può coprire una grande parte di state + RAG;
- puoi partire da una singola GPU;
- puoi scalare orizzontalmente aggiungendo replica;
- puoi aggiungere cloud fallback solo quando necessario;
- puoi mantenere il controllo sui dati;
- puoi offrire deployment on-premise;
- puoi fare QLoRA quando avrai dati reali.

Il principale rischio non è il modello.

È costruire un sistema in cui:

```text
LLM
+
tool loops
+
task pesanti
+
concorrenza
+
retry
+
background jobs
```

si contendono senza controllo la stessa GPU.

Per questo la struttura veramente importante è:

```text
                GOAL
                  ↓
            ORCHESTRATOR
                  ↓
            CAPABILITY LAYER
                  ↓
          ┌───────┴────────┐
          │                │
      Interactive       Async
          │                │
          ▼                ▼
      Model Router      Queue
          │                │
          ▼                ▼
       Qwen Pool        Workers
          │                │
          └───────┬────────┘
                  ▼
               TOOLS
                  ↓
            CRM / APIs / DB
                  ↓
             VERIFICATION
                  ↓
          AUDIT / TELEMETRY
```

La regola economica più importante è:

> **Prima ottimizza l'architettura del lavoro, poi l'hardware.**

Ridurre da 8 a 3 model calls, parallelizzare tool indipendenti, usare RAG invece di enormi context window, fare chunking e background execution può aumentare la capacità del sistema più di una GPU molto più costosa.

---

# 84. Fonti principali

## vLLM

Production Stack:
https://docs.vllm.ai/en/latest/deployment/integrations/production-stack/

FAQ / scaling / KV cache:
https://docs.vllm.ai/projects/production-stack/en/latest/getting_started/faq.html

Benchmarking:
https://docs.vllm.ai/en/latest/benchmarking/cli/

Configuration / KV cache:
https://docs.vllm.ai/en/latest/api/vllm/config/

Optimization:
https://docs.vllm.ai/en/latest/configuration/optimization/

## Qwen3.5-9B benchmarks

Q4 benchmark:
https://huggingface.co/steven0226/Qwen3.5-9B-GGUF-Quant-Lab/blob/main/EVAL_REPORT.md

Alternative GGUF benchmark:
https://huggingface.co/eaddario/Qwen3.5-9B-GGUF

## GPU infrastructure

Hetzner GEX44:
https://www.hetzner.com/dedicated-rootserver/gex44/

Hetzner June 2026 price adjustment:
https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/

Google Cloud GPU pricing:
https://cloud.google.com/products/compute/gpus-pricing

Google Cloud accelerator VM pricing:
https://cloud.google.com/products/compute/pricing/accelerator-optimized

Google Cloud Spot GPU pricing:
https://cloud.google.com/spot-vms/pricing

## Protocolli / standard

MCP:
https://modelcontextprotocol.io/specification/2025-11-25

A2A:
https://a2a-protocol.org/dev/specification/

OpenAPI:
https://spec.openapis.org/oas/v3.1.1.html

OAuth 2.x:
https://www.rfc-editor.org/rfc/rfc9700.html

## Governance / security

NIST AI RMF:
https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

OWASP:
https://owasp.org/

ISO/IEC 42001:
https://www.iso.org/standard/42001

---

# 85. Decisione operativa finale

Se il progetto partisse oggi con budget quasi zero:

```text
MODELLO
Qwen3.5-9B

QUANTIZZAZIONE
Q4_K_M oppure Q5_K_M dopo benchmark

INFERENCE
vLLM su GPU
llama.cpp per sviluppo/local

BACKEND
Python + FastAPI

DATABASE
PostgreSQL + pgvector

STATE
PostgreSQL

QUEUE
PostgreSQL inizialmente
Redis quando necessario

TOOLS
MCP

API
OpenAPI 3.1

AUTH
OAuth/OIDC

POLICY
RBAC + ABAC + capability permissions

OBSERVABILITY
OpenTelemetry + Prometheus + Grafana

CONTAINER
Docker

ORCHESTRATION
State machine / workflow

SCALE
verticale solo quando necessario
orizzontale con multiple GPU replicas

BACKGROUND
queue + workers + checkpoint

HEAVY TASKS
map/reduce + async

MODEL ROUTING
Qwen locale + cloud fallback opzionale

FINE-TUNING
QLoRA dopo raccolta di dati reali
```

Questa architettura consente di partire con **qualche centinaio di euro al mese**, arrivare a un MVP serio, misurare la capacità reale e poi scalare l'infrastruttura in modo proporzionale al numero di task e non semplicemente al numero di utenti.
