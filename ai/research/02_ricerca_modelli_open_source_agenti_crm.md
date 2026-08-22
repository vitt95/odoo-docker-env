# Modelli Open-Source per un AI Agent CRM a Budget Quasi Zero

## Obiettivo

Per un progetto con:

- budget nullo o molto basso;
- forte preferenza per open source/open-weight;
- esecuzione locale o self-hosted;
- possibilità di deployment presso clienti;
- necessità di integrazione con CRM, web app, mobile app, ERP e API;
- possibilità di fare LoRA/QLoRA in futuro;
- modello relativamente piccolo e sostenibile in termini di RAM/VRAM;

la scelta del modello va fatta considerando non soltanto la qualità linguistica, ma soprattutto:

1. tool/function calling;
2. capacità agentiche;
3. ecosistema open;
4. quantizzazione;
5. supporto a LoRA/QLoRA;
6. qualità con modelli piccoli;
7. facilità di deployment;
8. stabilità del comportamento;
9. disponibilità di framework e tooling;
10. possibilità di sostituire il modello senza cambiare l'architettura dell'agente.

---

# 1. Shortlist dei modelli

| Modello | Taglia | Valutazione per il progetto | LoRA | Tool calling / agent | Risorse |
|---|---:|---|---|---|---|
| **Qwen3.5-9B** | 9B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medie |
| **Qwen3-8B** | 8B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medie |
| **Gemma 3 4B** | 4B | ⭐⭐⭐⭐½ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Basse |
| **Llama 3.2 3B** | 3B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐½ | Molto basse |
| **FunctionGemma 270M** | 270M | ⭐⭐⭐⭐ per routing/tool | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐* | Minime |
| **Mistral 7B-class** | ~7B | ⭐⭐⭐½ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medie |

\* FunctionGemma è un modello specializzato per function calling, non un chatbot generalista.

---

# 2. Scelta principale: Qwen3.5-9B

## Perché è il candidato principale

Per questo progetto, la scelta più razionale come modello principale è **Qwen3.5-9B**.

I motivi principali sono:

- dimensione ancora ragionevole per inference locale;
- ecosistema open-weight molto ampio;
- supporto al function calling;
- tooling per agenti;
- integrazione con MCP;
- possibilità di LoRA/PEFT;
- ampia disponibilità di quantizzazioni;
- enorme ecosistema di derivati e adapter;
- buon compromesso tra capacità di reasoning e costi computazionali.

Qwen dispone di documentazione e tooling specifici per il function calling e Qwen-Agent offre componenti per function calling, MCP, RAG e agent workflow.

Fonti:

- Qwen3.5-9B Base su Hugging Face: https://huggingface.co/Qwen/Qwen3.5-9B-Base
- Qwen function calling: https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md

---

# 3. Perché Qwen è particolarmente adatto a un CRM Agent

Un agente CRM non deve semplicemente generare testo.

Deve poter fare:

```text
Utente
  ↓
Comprensione richiesta
  ↓
Decisione
  ↓
Tool call
  ↓
CRM API
  ↓
Risultato strutturato
  ↓
Eventuale seconda decisione
  ↓
Risposta
```

Per esempio:

```text
"Mostrami i clienti lombardi che non hanno avuto contatti negli ultimi 90 giorni"

        ↓

search_customers(
    region="Lombardia",
    days_since_contact=90
)

        ↓

CRM / Database

        ↓

risultati

        ↓

Qwen

        ↓

risposta all'utente
```

Questa è un'area dove il supporto nativo al function calling è più importante della semplice capacità conversazionale.

---

# 4. Qwen3-8B come seconda baseline

**Qwen3-8B** è un'altra scelta molto interessante.

È utile soprattutto perché:

- appartiene alla stessa famiglia;
- ha un enorme ecosistema;
- dispone di tooling per function calling;
- può costituire una baseline più leggera;
- permette di sperimentare senza cambiare architettura.

Per un progetto con budget quasi zero, avere:

```text
Qwen3-8B
Qwen3.5-9B
```

come due baseline compatibili è molto utile.

La documentazione Qwen sul function calling è particolarmente rilevante per agenti che devono usare strumenti in modo strutturato:

https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md

---

# 5. Gemma 3 4B

## Perché è interessante

Se il vincolo principale diventa l'hardware, **Gemma 3 4B** è una delle alternative più interessanti.

Google lo presenta come modello lightweight utilizzabile anche su sistemi con risorse limitate.

Caratteristiche interessanti:

- 4B parametri;
- 128K di contesto;
- multimodalità;
- buona possibilità di fine-tuning;
- ottimo rapporto costo/risorse.

Fonte:

https://ai.google.dev/gemma/docs/core/model_card_3

Per il tuo progetto lo vedrei bene per:

- classificazione;
- routing;
- estrazione;
- summarization;
- RAG semplice;
- generazione email;
- tool call relativamente semplici.

Se la differenza di qualità rispetto a Qwen3.5-9B non è critica per il caso d'uso, il risparmio computazionale può essere significativo.

---

# 6. Llama 3.2 3B

Llama rimane una famiglia estremamente importante nell'ecosistema open-weight.

Il vantaggio principale non è necessariamente la migliore qualità assoluta, ma:

- enorme community;
- moltissimi tutorial;
- moltissimi LoRA;
- moltissime quantizzazioni;
- grande compatibilità con framework;
- deployment locale molto semplice.

Il modello **Llama 3.2 3B** può funzionare bene come:

- router;
- classifier;
- extractor;
- semplice assistente;
- task a basso livello.

Lo vedrei meno come unico cervello di un agent CRM sofisticato con molte operazioni multi-step.

Fonte:

https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

---

# 7. FunctionGemma 270M

Questa è una possibilità architetturale particolarmente interessante.

Google ha creato **FunctionGemma** come modello molto piccolo e specializzato nel function calling.

Il punto importante è che non va considerato semplicemente come un piccolo chatbot.

È pensato per essere ulteriormente specializzato tramite fine-tuning sullo specifico task di tool/function calling.

Fonte:

https://ai.google.dev/gemma/docs/functiongemma/model_card

---

# 8. Architettura a due modelli

Per un progetto a budget quasi zero, può avere senso non usare sempre il modello principale.

Architettura possibile:

```text
                    AGENT
                      │
             ┌────────┴────────┐
             │                 │
          ROUTER              MAIN
             │                 │
      FunctionGemma       Qwen3.5-9B
        / small LLM       / Qwen3-8B
             │                 │
             └────────┬────────┘
                      │
                 TOOL RUNTIME
                      │
        ┌─────────────┼──────────────┐
        │             │              │
       CRM           RAG          DATABASE
```

L'idea è:

- usare il modello piccolo per compiti semplici;
- usare il modello principale solo quando serve;
- ridurre consumo energetico, memoria e latenza;
- utilizzare il modello grande soltanto per reasoning e task più complessi.

---

# 9. Model Router

La direzione più interessante per il progetto è costruire l'architettura in modo **model-agnostic**.

Non:

```text
App
 ↓
Qwen
 ↓
CRM
```

Ma:

```text
Application
    ↓
Agent Gateway
    ↓
Agent Orchestrator
    ↓
Model Router
    ↓
┌───────────────┬──────────────┬──────────────┐
│               │              │              │
Qwen        Gemma/Llama     Cloud API    Future model
```

In questo modo Qwen è un'implementazione del model layer e non il centro dell'architettura.

---

# 10. LoRA: quando usarlo

La scelta consigliata è:

> **Non fare LoRA all'inizio solo perché è possibile.**

Prima costruire:

```text
Qwen3.5-9B
+
prompt engineering
+
structured outputs
+
tool calling
+
RAG
+
workflow deterministico
```

Poi misurare gli errori.

Se, per esempio, emerge:

```text
17% degli input:
tool errato

12%:
argomenti errati

8%:
formato output errato
```

allora il fine-tuning diventa molto più giustificato.

---

# 11. LoRA non dovrebbe insegnare i dati del CRM

Questo è fondamentale.

Non usare LoRA per memorizzare:

- anagrafiche;
- clienti;
- prezzi;
- disponibilità;
- documentazione aggiornata;
- policy che cambiano frequentemente;
- dati transazionali.

Questi contenuti devono essere gestiti tramite:

```text
Database
+
RAG
+
API
+
Tool
```

Il fine-tuning dovrebbe invece insegnare **come comportarsi**.

---

# 12. Primo caso d'uso per LoRA: Tool Calling

Un dataset può essere strutturato come:

```text
query
→ tool
→ arguments
```

Esempio:

```json
{
  "query": "Mostrami i clienti lombardi senza contatti da 90 giorni",
  "tool": "search_customers",
  "arguments": {
    "region": "Lombardia",
    "days_since_contact": 90
  }
}
```

Questa è probabilmente la prima area in cui sperimentare LoRA.

---

# 13. Secondo caso d'uso: Workflow LoRA

Il modello può essere specializzato nel riconoscere sequenze di azioni.

Esempio:

```text
"Organizza il follow-up dei clienti persi"

        ↓

find_leads
        ↓
classify
        ↓
generate_email
        ↓
create_task
```

Il LoRA in questo caso insegna pattern operativi ricorrenti.

---

# 14. Terzo caso d'uso: stile e business policy

Una volta stabilizzato il tool use, il fine-tuning può essere usato per:

- tono;
- struttura delle email;
- terminologia aziendale;
- formato delle risposte;
- stile commerciale;
- policy operative.

Questa dovrebbe essere una fase successiva.

---

# 15. Cosa NON mettere nel LoRA

Da evitare:

```text
LoRA
 ↓
database CRM
```

Meglio:

```text
                 Knowledge
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      SQL DB        RAG          APIs
        │            │            │
        └────────────┴────────────┘
                     │
                     ▼
                   Agent
```

---

# 16. Qwen Base vs Qwen Instruct

Per il prototipo:

**Qwen3.5-9B-Instruct**

Per fine-tuning specializzato:

**Qwen3.5-9B-Base + LoRA/PEFT**

Il modello Base è pensato esplicitamente come punto di partenza per post-training e fine-tuning.

Fonte:

https://huggingface.co/Qwen/Qwen3.5-9B-Base

---

# 17. Stack tecnico consigliato

Per un progetto a budget quasi zero:

## Modello principale

**Qwen3.5-9B**

## Modello alternativo leggero

**Gemma 3 4B** oppure **Qwen3 piccolo**

## Tool specialist

**FunctionGemma 270M**, se utile dopo i benchmark

## Fine-tuning

**QLoRA / PEFT**

## Inference

**llama.cpp** quando l'obiettivo è minimizzare i requisiti hardware.

**vLLM** quando sarà disponibile una macchina GPU più seria e sarà prioritario il throughput.

## Database

**PostgreSQL**

## Vector search

**pgvector**

Evitare, almeno all'inizio, un vector database separato se PostgreSQL è già sufficiente.

## Stato agente

**PostgreSQL**

## Cache

**Redis solo quando necessario**

---

# 18. Architettura finale consigliata

Per il progetto specifico:

```text
                         USER / CRM / APP
                               │
                               ▼
                     ┌────────────────────┐
                     │    Agent Gateway   │
                     │ Auth / ACL / Tenant│
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │ Agent Orchestrator │
                     │                    │
                     │ state              │
                     │ workflow           │
                     │ policy             │
                     │ routing            │
                     └─────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌───────────────┐      ┌─────────────┐
             │  Model Router │      │ Knowledge   │
             └───────┬───────┘      │ Layer / RAG │
                     │              └─────────────┘
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
    Qwen3.5       Gemma         Optional
       9B           4B          Cloud API
        │             │
        └──────┬──────┘
               │
               ▼
        ┌──────────────┐
        │ Tool Runtime │
        └──────┬───────┘
               │
     ┌─────────┼───────────────┐
     ▼         ▼               ▼
    CRM       APIs          Database
```

---

# 19. Filosofia architetturale

La regola principale dovrebbe essere:

> **Il modello decide solo ciò che richiede intelligenza. Il codice gestisce tutto ciò che può essere deterministico.**

Quindi non:

```text
Qwen
 ↓
"fai tutto"
```

Ma:

```text
        USER
         │
         ▼
   Intent / Router
         │
         ▼
   Deterministic
      Workflow
         │
    ┌────┼────┐
    ▼    ▼    ▼
   RAG  TOOL  DB
    │    │    │
    └────┼────┘
         ▼
       Qwen
         │
         ▼
      Response
```

Con un modello 4B-9B questa strategia è particolarmente importante perché riduce le richieste di reasoning complesso.

---

# 20. Classifica finale specifica per il progetto

## 🥇 Qwen3.5-9B

Scelta principale.

Motivi:

- equilibrio tra capacità e risorse;
- grande ecosistema;
- tool calling;
- agent tooling;
- LoRA/PEFT;
- quantizzazioni;
- compatibilità con deployment locale;
- grande ecosistema open-weight.

## 🥈 Qwen3-8B

Alternativa molto forte.

Particolarmente utile come baseline comparativa e alternativa leggermente più leggera.

## 🥉 Gemma 3 4B

Scelta molto interessante quando il vincolo hardware diventa prioritario.

## 4. Llama 3.2 3B

Ottimo mini-model per routing e task semplici.

## 5. FunctionGemma 270M

Interessante come specialista per function calling e routing.

## 6. Mistral 7B-class

Alternativa valida, ma non sarebbe la prima scelta per questo progetto.

---

# 21. Conclusione

Per un progetto con budget quasi zero, non sceglierei Qwen3.5-9B semplicemente perché è "un modello piccolo".

La scelta è più interessante:

> **Qwen3.5-9B è oggi un ottimo compromesso tra dimensione, capacità, tool use, ecosistema open-weight, possibilità di fine-tuning e disponibilità di tooling agentico.**

L'architettura dovrebbe però rimanere indipendente dal modello:

```text
Application
    ↓
Agent Gateway
    ↓
Orchestrator
    ↓
Model Router
    ↓
Qwen / Gemma / Llama / eventuale Cloud Model
    ↓
Tool Runtime
    ↓
CRM / RAG / DB / APIs
```

Questo permette di partire con **Qwen3.5-9B self-hosted a costo quasi zero**, ma senza vincolare il prodotto al modello.

La strategia di crescita può essere:

### Fase 1

```text
Qwen3.5-9B-Instruct
+
workflow deterministico
+
tool calling
+
RAG
```

### Fase 2

```text
benchmark
+
dataset di errori
+
QLoRA tool calling
```

### Fase 3

```text
router
+
modello piccolo per task semplici
+
Qwen per reasoning
```

### Fase 4

```text
Model abstraction
+
eventuale supporto Gemini / Claude / GPT
+
eventuale modello proprietario verticale
```

Questa strategia consente di iniziare con infrastruttura minima, ma mantenere un'architettura adatta a diventare un prodotto enterprise.

---

# 22. Fonti principali

### Qwen

- Qwen3.5-9B Base — Hugging Face  
  https://huggingface.co/Qwen/Qwen3.5-9B-Base

- Qwen Function Calling  
  https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md

### Gemma

- Gemma 3 model card  
  https://ai.google.dev/gemma/docs/core/model_card_3

- FunctionGemma model card  
  https://ai.google.dev/gemma/docs/functiongemma/model_card

### Llama

- Llama 3.2 3B Instruct  
  https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

### Ecosistema open models

- Hugging Face — State of Open Models  
  https://github.com/huggingface/blog/blob/main/state-of-open-models-summer-2026.md

### Enterprise AI / model adoption

- Menlo Ventures — State of Generative AI in the Enterprise  
  https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/

---

# Decisione operativa

Se dovessi iniziare il progetto domani con budget quasi zero:

```text
MODELLO:
Qwen3.5-9B-Instruct

INFERENCE:
llama.cpp

DATABASE:
PostgreSQL + pgvector

AGENT:
state machine / workflow deterministico

TOOLS:
function calling

MEMORY:
PostgreSQL

RAG:
pgvector

FINE-TUNING FUTURO:
Qwen3.5-9B-Base + QLoRA

SPECIALIST:
FunctionGemma solo se i benchmark giustificano un secondo modello
```

La priorità non dovrebbe essere "fare il LoRA il prima possibile", ma **costruire un dataset di conversazioni → tool calls → risultati → errori**. Quel dataset diventerà in seguito il vero asset competitivo del sistema.
