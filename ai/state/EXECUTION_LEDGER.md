# EXECUTION LEDGER — stato di avanzamento della sintesi architetturale

Questo file è il **registro di esecuzione**. Serve a sapere, in qualsiasi momento e anche
dopo una interruzione, a che punto siamo e cosa manca.

Regola: si aggiorna **dopo** aver scritto il documento, mai prima.

Legenda stato:

| Stato | Significato |
|---|---|
| `TODO` | non ancora eseguito |
| `IN CORSO` | prompt letto, documento non ancora completo |
| `FATTO` | documento scritto e checkpoint registrato in `ARCHITECTURE_STATE.md` |
| `DA RIVEDERE` | un documento successivo ha invalidato una decisione qui dentro |

---

## Metodo di esecuzione (deciso il 2026-08-22)

Modalità **ibrida**, scelta per evitare la saturazione del contesto principale.

| Chi scrive | Quali documenti | Perché |
|---|---|---|
| **Thread principale** | `A01`, `A02`, `A03`, `A04`, `A13`, tutti i **gate di livello**, `FINAL_ARCHITECTURE.md` | sono i documenti che *prendono* le decisioni fondanti; devono essere scritti da chi ha in testa tutto lo stato |
| **Subagent isolato** | tutti gli altri (`A05`-`A12`, `A14`-`A18`, Level B, Level C) | sono documenti che *consumano* decisioni già prese; il testo del prompt (32-85 KB) non deve entrare nel contesto principale |

Contratto per ogni subagent:

1. riceve: percorso del prompt, percorso del documento da produrre, `ARCHITECTURE_STATE.md`,
   `research-log.md`, la convenzione linguistica;
2. produce: il documento su disco;
3. restituisce: **solo il checkpoint** nel formato del Master Entrypoint §11, non il documento.

Il thread principale integra il checkpoint in `ARCHITECTURE_STATE.md` e prosegue.

### Contromisure contro gli API Error

- blocchi di scrittura da ~150-200 righe per chiamata, mai documenti interi;
- i prompt lunghi si leggono a sezioni (`offset`/`limit`), non interi;
- non si rileggono mai i documenti già prodotti: vale `ARCHITECTURE_STATE.md`.

---

## Regole di esecuzione (dal Master Entrypoint)

1. Un prompt alla volta. Mai in parallelo.
2. Ordine obbligatorio: **LEVEL A → LEVEL B → LEVEL C**.
3. Dopo ogni livello: **gate** (review) + **falsification**. Non si prosegue con difetti noti.
4. Nessuna decisione è definitiva prima della sintesi finale.
5. Ogni documento produce un **checkpoint** in `ARCHITECTURE_STATE.md`.

---

## LEVEL A — Core Day 1

> **⚠️ Deviazione dall'ordine, decisa dal committente il 2026-08-23.**
> `A15` (Deployment) e `A16` (CI/CD) sono **rimandati**. L'ordine di esecuzione diventa
> **`A17` → `A18`**, poi `A15` e `A16` **quando il committente lo dirà esplicitamente**.
> Il gate di Level A **non può chiudersi** finché `A15` e `A16` mancano.

| # | Prompt | Output | Stato |
|---|---|---|---|
| A01 | `level-a/prompt/01-master-architecture-principles.txt` | `level-a/01_ARCHITECTURE_PRINCIPLES.md` | **FATTO** |
| A02 | `level-a/prompt/02-control-plane-architecture.txt` | `level-a/02_CONTROL_PLANE.md` | **FATTO** |
| A03 | `level-a/prompt/03-governance-policy-plane.txt` | `level-a/03_GOVERNANCE_POLICY.md` | **FATTO** |
| A04 | `level-a/prompt/04-agent-runtime-architecture.txt` | `level-a/04_AGENT_RUNTIME.md` | **FATTO** |
| A05 | `level-a/prompt/05-model-and-inference-architecture.txt` | `level-a/05_MODEL_INFERENCE.md` | **FATTO** |
| A06 | `level-a/prompt/06-tool-architecture.txt` | `level-a/06_TOOL_ARCHITECTURE.md` | **FATTO** |
| A07 | `level-a/prompt/07-knowledge-and-data-architecture.txt` | `level-a/07_KNOWLEDGE_DATA.md` | **FATTO** (4.026 righe). Chiude `AS-08`: embedding su CPU, `ADR-039` invariato |
| A08 | `level-a/prompt/08-memory-architecture.txt` | `level-a/08_MEMORY.md` | **FATTO** (3.196 righe). Salda `AR-RT-14` con un digest deterministico; chiude `DEF-04` |
| A09 | `level-a/prompt/09-identity-authentication-authorization-architecture.txt` | `level-a/09_IDENTITY_AUTHZ.md` | **FATTO** (4.404 righe). Dual principal; salda il contratto del secret store chiesto da `A06` |
| A10 | `level-a/prompt/10-agent-communication-and-multi-agent-architecture.txt` | `level-a/10_AGENT_COMMUNICATION.md` | **FATTO** (2.050 righe). Chiude `DEF-07`: niente comunicazione agent→agent Day-1, ma 4 colonne di lineage subito |
| A11 | `level-a/prompt/11-eventing-workflow-durable-execution-architecture.txt` | `level-a/11_EVENTING_WORKFLOW.md` | **FATTO** (~3.400 righe). Nessun engine: il motore è il loop su PostgreSQL. Disinnesca `R-50` con un trigger di database |
| A12 | `level-a/prompt/12-observability-evaluation-and-ai-reliability-architecture.txt` | `level-a/12_OBSERVABILITY_EVAL.md` | **FATTO** (3.630 righe). **63 metriche mandate, 63 coperte.** Il prompt non si conserva: si ricostruisce |
| A13 | `level-a/prompt/13-security-architecture.txt` | `level-a/13_SECURITY.md` | **FATTO** (1.766 righe, **thread principale**). Chiude `ASI09`, il buco che nessun documento aveva visto. Trova un difetto in `T-GP-02` |
| A14 | `level-a/prompt/14-data-governance-privacy-compliance-architecture.txt` | `level-a/14_DATA_GOVERNANCE.md` | **FATTO** (4.674 righe). Chiude `R-32` sul percorso strutturato con `FieldScope`; scopre che `ADR-221` erode `INV-07` |
| A15 | `level-a/prompt/15-deployment-infrastructure-runtime-platform-architecture.txt` | `level-a/15_DEPLOYMENT_PLATFORM.md` | **RIMANDATO** (decisione del committente, 2026-08-23). Da riprendere **solo su indicazione esplicita** |
| A16 | `level-a/prompt/16-ci-cd-release-engineering-software-supply-chain-architecture.txt` | `level-a/16_CICD_SUPPLY_CHAIN.md` | **RIMANDATO** (decisione del committente, 2026-08-23). Da riprendere **solo su indicazione esplicita** |
| A17 | `level-a/prompt/17-testing-quality-assurance-validation-architecture.txt` | `level-a/17_TESTING_QA.md` | **FATTO** (3.781 righe). Raccoglie il conto: **145 mandati di test** estratti da `A02`-`A14`, ~55% verificabili staticamente. Nove gate `G-QA-01`…`09`, sei bloccanti. Scopre `R-108`: `INV-40` non copre i documenti aziendali reali |
| A18 | `level-a/prompt/18-api-integration-external-interface-architecture.txt` | `level-a/18_API_INTEGRATION.md` | **FATTO** (3.635 righe). Due superfici separate: API esposta (REST/OpenAPI 3.1, tutto asincrono) e connector Odoo (`transport.py` isolato, `B-53` non risolta). Salda il debito di `AR-QA-02`. Peggiora e dichiara `R-98` come `R-115` |
| — | **LEVEL A GATE** (review + falsification) | `level-a/00_LEVEL_A_REVIEW.md` | TODO — **bloccato finché `A15` e `A16` non sono fatti** |

---

## LEVEL B — Day-1 Foundations / Future-Ready

| # | Prompt | Output | Stato |
|---|---|---|---|
| B05 | `level-b/prompt/05-resource-gpu-architecture.txt` | `level-b/05_RESOURCE_GPU.md` | TODO |
| B12 | `level-b/prompt/12-trust-provenance-architecture.txt` | `level-b/12_TRUST_PROVENANCE.md` | TODO |
| B14 | `level-b/prompt/14-concurrency-architecture.txt` | `level-b/14_CONCURRENCY.md` | TODO |
| B19 | `level-b/prompt/19-multi-tenancy-architecture.txt` | `level-b/19_MULTI_TENANCY.md` | TODO |
| B20 | `level-b/prompt/20-cost-architecture.txt` | `level-b/20_COST.md` | TODO |
| B21 | `level-b/prompt/21-capacity-planning-architecture.txt` | `level-b/21_CAPACITY_PLANNING.md` | TODO |
| B22 | `level-b/prompt/22-networking-architecture.txt` | `level-b/22_NETWORKING.md` | TODO |
| B23 | `level-b/prompt/23-storage-architecture.txt` | `level-b/23_STORAGE.md` | TODO |
| — | **LEVEL B GATE** (review + falsification) | `level-b/00_LEVEL_B_REVIEW.md` | TODO |

> Nota: il Master Entrypoint elenca in Level B anche `28 Human-in-the-loop`, `29 Replay`,
> `33 ADR` e `34 Quality Model`. I file `28` e `29` esistono solo in `level-c/prompt/`;
> `33` e `34` non esistono come file. Vedi `ARCHITECTURE_STATE.md` → *Scostamenti dal
> Master Entrypoint* per come è stato risolto.

---

## LEVEL C — Successive Architecture

| # | Prompt | Output | Stato |
|---|---|---|---|
| C07 | `level-c/prompt/07-mcp-ecosystem-architecture.txt` | `level-c/07_MCP_ECOSYSTEM.md` | TODO |
| C24 | `level-c/prompt/24-disaster-recovery-enterprise-architecture.txt` | `level-c/24_DISASTER_RECOVERY.md` | TODO |
| C25 | `level-c/prompt/25-advanced-supply-chain-architecture.txt` | `level-c/25_ADVANCED_SUPPLY_CHAIN.md` | TODO |
| C26 | `level-c/prompt/26-enterprise-compliance-architecture.txt` | `level-c/26_ENTERPRISE_COMPLIANCE.md` | TODO |
| C27 | `level-c/prompt/27-multi-model-fallback-architecture.txt` | `level-c/27_MULTI_MODEL_FALLBACK.md` | TODO |
| C28 | `level-c/prompt/28-human-in-the-loop-architecture.txt` | `level-c/28_HUMAN_IN_THE_LOOP.md` | TODO |
| C29 | `level-c/prompt/29-replay-architecture.txt` | `level-c/29_REPLAY.md` | TODO |
| C30 | `level-c/prompt/30-offline-mobile-architecture.txt` | `level-c/30_OFFLINE_MOBILE.md` | TODO |
| C31 | `level-c/prompt/31-a2a-agent-to-agent-architecture.txt` | `level-c/31_A2A.md` | TODO |
| — | **LEVEL C GATE** (review) | `level-c/00_LEVEL_C_REVIEW.md` | TODO |

---

## SINTESI FINALE

| Passo | Output | Stato |
|---|---|---|
| Global Architecture Synthesis | `FINAL_ARCHITECTURE.md` | TODO |

---

## Come riprendere dopo una interruzione

**Leggere prima `RESTART.md`**, che contiene il metodo, lo stato completo, il template dei
prompt per i subagent e i problemi aperti. Poi:

1. Leggere questo file → trovare la prima riga `TODO`.
2. Leggere `ARCHITECTURE_STATE.md` → recuperare decisioni, interfacce, invarianti, conflitti aperti.
3. Leggere `research-log.md` → recuperare i FATTI verificati, evitando di rifare ricerca.
4. Leggere **solo** il prompt della riga `TODO`.
5. Produrre il documento, aggiornare `ARCHITECTURE_STATE.md`, aggiornare questo ledger.

Non è necessario rileggere i documenti già prodotti: `ARCHITECTURE_STATE.md` è la loro
sintesi vincolante.
