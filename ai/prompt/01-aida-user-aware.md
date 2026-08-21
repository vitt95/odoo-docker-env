# ROLE

Agisci come **Senior Software Architect + Lead AI Engineer + Odoo Integration Engineer** responsabile dell'evoluzione di **AIDA**, il mio agente AI integrato con Odoo.

Non devi limitarti a suggerire una soluzione teorica.

Il tuo compito è:

1. analizzare il codice esistente di AIDA;
2. capire come vengono gestiti oggi utente, sessione, tool, agent, contesto e chiamate Odoo;
3. identificare le lacune architetturali;
4. progettare una soluzione robusta;
5. implementarla direttamente nel codebase;
6. aggiornare i prompt/agent instructions dove necessario;
7. aggiungere test;
8. verificare che la soluzione funzioni end-to-end.

**Non voglio una semplice risposta descrittiva. Voglio che tu lavori sul progetto e implementi concretamente la funzionalità.**

---

# OBIETTIVO

Voglio rendere AIDA un agente Odoo realmente **user-aware**.

AIDA deve essere consapevole dell'utente autenticato con cui sta interagendo e deve poter utilizzare questa identità come parte fondamentale del proprio ragionamento.

L'utente non deve essere costretto a specificare continuamente il proprio nome, ID o account.

Se l'utente dice:

* "i miei lead"
* "le mie opportunità"
* "le mie vendite"
* "i miei appuntamenti"
* "le mie attività"
* "i miei clienti"
* "quello che devo fare"
* "cosa ho in programma"
* "come sto andando?"
* "fammi vedere quello che ho"
* "cosa devo seguire?"
* "quali sono assegnati a me?"
* "cosa ho chiuso questo mese?"
* "cosa devo ancora fare?"

AIDA deve capire automaticamente che **"io / me / mio / mia / miei / mie / a me / per me / assegnato a me / che seguo / che gestisco / ecc." = utente Odoo autenticato corrente**.

Questa risoluzione deve essere sistemica e non una serie di hack sparsi nei singoli tool.

---

# IMPORTANTE: NON FARE UNA SOLUZIONE SUPERFICIALE

Non implementare semplicemente regole come:

```text
"miei" -> user_id
```

dentro un singolo prompt.

Voglio una soluzione architetturale.

Deve esistere un concetto centrale di:

**CURRENT USER / USER IDENTITY / USER CONTEXT**

che venga utilizzato coerentemente dall'agente, dai tool e dal layer Odoo.

---

# FASE 1 — ANALISI DEL CODEBASE

Prima di modificare il codice, analizza l'intero progetto.

Individua:

* entry point dell'agente;
* orchestrazione dell'LLM;
* system prompt;
* agent prompt;
* tool definitions;
* Odoo connector;
* gestione sessione;
* autenticazione;
* gestione dell'utente corrente;
* gestione company;
* gestione dei permessi;
* gestione dei contesti;
* gestione conversation state;
* memoria;
* eventuali MCP/tool server;
* query builder;
* mapping dei modelli Odoo;
* filtri;
* gestione `user_id`;
* eventuali meccanismi già esistenti di personalization;
* eventuali hardcoded user references.

Cerca nel codebase tutti i punti in cui viene utilizzato o potrebbe essere utilizzato:

```text
user_id
uid
partner_id
employee_id
company_id
salesperson
assigned
owner
responsible
assignee
current user
logged user
session user
context
allowed_company_ids
```

Non assumere che l'architettura attuale sia corretta.

Prima ricostruisci come AIDA funziona realmente.

---

# FASE 2 — DEFINISCI IL CONCETTO DI CURRENT USER

Introduci, se non esiste già, un livello centrale di identità utente.

Concettualmente deve esistere qualcosa come:

```text
CurrentUserContext
```

o un equivalente coerente con l'architettura esistente.

Deve rappresentare almeno:

```text
id
name
display_name
email
login
partner_id
company_id
allowed_company_ids
groups
roles
permissions
sales_team
department
manager
timezone
language
```

Non inventare campi se non sono disponibili.

Utilizza i dati realmente forniti da Odoo.

Il contesto deve essere disponibile all'agente in modo strutturato.

---

# FASE 3 — IDENTITY RESOLUTION

Implementa un vero livello di **Identity Resolution / Reference Resolution**.

L'agente deve essere in grado di riconoscere che espressioni diverse si riferiscono allo stesso soggetto.

Esempi:

```text
io
me
mio
mia
miei
mie
a me
per me
da me
con me
assegnato a me
assegnata a me
assegnati a me
assegnate a me
che seguo
che gestisco
che possiedo
di mia competenza
sotto la mia responsabilità
nel mio portafoglio
nel mio team
le mie cose
quello che ho
quello che gestisco
quello che seguo
```

La soluzione deve essere estensibile.

Non voglio una semplice lista hardcoded nel prompt se è possibile ottenere una soluzione semantica migliore.

---

# FASE 4 — SEMANTICA DEL POSSESSIVO

Devi progettare un meccanismo che interpreti correttamente il possessivo in base al modello Odoo.

Esempio:

```text
"i miei lead"
```

non significa necessariamente:

```python
{"owner_id": current_user.id}
```

Deve significare:

> trova il campo/relation che rappresenta l'assegnazione o responsabilità dell'utente per quel modello.

Per esempio:

CRM Lead:

```text
user_id = current_user.id
```

Sales Order:

```text
salesperson/user relation = current_user.id
```

Activities:

```text
assigned user = current_user.id
```

Calendar:

```text
user/organizer/attendee relation
```

Project Task:

```text
assigned user / user_ids
```

Helpdesk:

```text
assigned user
```

ecc.

Devi quindi verificare come AIDA/Odoo mappa i diversi modelli e costruire un sistema coerente.

---

# FASE 5 — ENTITY RESOLUTION

AIDA deve inoltre distinguere correttamente:

```text
io
```

da:

```text
Mario
```

da:

```text
il mio team
```

da:

```text
il team di Mario
```

da:

```text
tutti
```

Esempio:

Utente:

> Mostrami i miei lead.

→ current user.

Poi:

> E quelli di Mario?

→ Mario.

Poi:

> E quelli di ieri?

→ mantiene Mario come soggetto.

Poi:

> E i miei?

→ torna al current user.

Questa logica deve funzionare anche tra turni diversi della conversazione.

---

# FASE 6 — CONVERSATION CONTEXT

Analizza come AIDA mantiene il contesto conversazionale.

Implementa una soluzione che permetta di mantenere:

```text
current subject
current entity
current filters
current date range
current user reference
```

Esempio:

```text
"Fammi vedere i miei lead."

→ subject = current_user
→ entity = crm.lead

"Quali sono caldi?"

→ subject = current_user
→ entity = crm.lead
→ add filter = hot

"E quelli senza attività?"

→ subject = current_user
→ entity = crm.lead
→ add filter = no activity
```

Non bisogna perdere il riferimento all'utente corrente tra i turni.

---

# FASE 7 — USER CONTEXT NEL PROMPT

Analizza l'attuale system prompt di AIDA.

Integra il contesto utente nel punto architetturalmente corretto.

Non voglio necessariamente inserire una quantità enorme di dati statici nel system prompt.

Valuta se sia preferibile:

* structured context;
* runtime context;
* dynamic system message;
* tool context;
* session context;
* identity resolver;
* middleware.

Scegli la soluzione più robusta considerando:

* token usage;
* sicurezza;
* caching;
* consistenza;
* multi-tenancy;
* performance;
* manutenzione.

---

# FASE 8 — TOOL CALLING

Questa parte è fondamentale.

I tool Odoo devono poter utilizzare il current user senza costringere l'LLM a conoscere o inventare il suo ID.

Per esempio, non voglio affidarmi a:

```text
LLM → "user_id = 42"
```

se il sistema può risolverlo deterministicamente.

Preferisco:

```text
LLM
 ↓
semantic intent
 ↓
tool
 ↓
CurrentUserContext
 ↓
Odoo
```

Il sistema deve evitare che il modello possa accidentalmente utilizzare un altro `user_id` quando l'utente ha detto "miei".

Valuta quindi quali filtri debbano essere:

### LLM-controlled

e quali invece:

### application-controlled.

Dai priorità alla sicurezza e alla determinismo.

---

# FASE 9 — SICUREZZA E ODOO PERMISSIONS

L'identità dell'utente non deve essere soltanto informativa.

Deve essere utilizzata correttamente per rispettare:

* Odoo ACL;
* record rules;
* company isolation;
* allowed companies;
* user permissions;
* sales team restrictions;
* access rights.

Non creare scorciatoie che bypassino Odoo security.

Non permettere che l'LLM possa semplicemente cambiare:

```text
user_id
company_id
allowed_company_ids
```

per accedere a dati non autorizzati.

Il current user deve derivare dalla sessione/autenticazione reale.

---

# FASE 10 — "TUTTO SUL MIO ACCOUNT"

AIDA deve poter rispondere a richieste relative al proprio account.

Esempi:

```text
Chi sono?
Come mi chiamo?
Qual è il mio account?
Qual è la mia email?
Che ruolo ho?
A quale azienda appartengo?
Quali aziende posso utilizzare?
Qual è il mio team?
Qual è il mio reparto?
Chi è il mio responsabile?
Quali permessi ho?
Quali sono i miei lead?
Quali sono le mie opportunità?
Quali sono le mie vendite?
Quali sono i miei appuntamenti?
Quali attività ho?
```

Deve poter rispondere usando dati reali Odoo.

Non hardcodare queste informazioni.

---

# FASE 11 — LINGUAGGIO NATURALE

Non limitarti all'italiano.

L'architettura dovrebbe essere semanticamente generalizzabile almeno a:

Italiano:

```text
io
me
mio
mia
miei
mie
i miei lead
le mie vendite
```

Inglese:

```text
I
me
my
mine
my leads
my sales
my appointments
```

e idealmente ad altre lingue supportate da AIDA.

Il concetto deve essere:

```text
SELF_REFERENCE → CURRENT_USER
```

non:

```text
Italian_word → user_id
```

---

# FASE 12 — FALLBACK E AMBIGUITÀ

Se AIDA non riesce a determinare con certezza il soggetto, deve chiedere chiarimento.

Esempio:

```text
Mostrami i lead di Marco.
```

Se esistono:

```text
Marco Rossi
Marco Bianchi
```

non scegliere casualmente.

Chiedi:

```text
Intendi Marco Rossi o Marco Bianchi?
```

Se invece l'utente dice:

```text
i miei lead
```

non chiedere mai:

```text
Quale utente?
```

perché il riferimento è deterministico: current user.

---

# FASE 13 — TEST

Non considerare il lavoro completato senza test.

Crea test automatici per almeno questi casi.

### Identity

```text
"Quali sono i miei lead?"
"Mostrami le mie opportunità."
"Quante vendite ho?"
"Quali sono i miei appuntamenti?"
"Mostrami le mie attività."
"Quali clienti seguo?"
```

Devono tutti risolvere il soggetto verso CURRENT_USER.

### Context

```text
"Mostrami i miei lead."
"Quali sono caldi?"
"E quelli senza attività?"
```

Il riferimento all'utente deve essere mantenuto.

### Subject switching

```text
"Mostrami i miei lead."
"E quelli di Marco?"
"E i miei?"
```

Deve passare:

```text
CURRENT_USER → MARCO → CURRENT_USER
```

### Ambiguity

```text
"Mostrami i lead di Marco."
```

con due Marco deve produrre una richiesta di disambiguazione.

### Security

Verifica che l'LLM non possa:

```text
forzare user_id di un altro utente
```

per bypassare le autorizzazioni.

### Multi-company

Verifica che current company e allowed companies siano rispettate.

---

# FASE 14 — OSSERVABILITÀ

Aggiungi logging/debugging utile per capire come AIDA ha interpretato una richiesta.

Idealmente deve essere possibile osservare internamente qualcosa come:

```text
USER:
Luca Rossi

RAW REQUEST:
"fammi vedere i miei lead"

RESOLUTION:
"miei" → CURRENT_USER

CURRENT_USER:
42

ENTITY:
crm.lead

RELATION:
user_id

RESOLVED FILTER:
user_id = 42
```

Non esporre necessariamente questo dettaglio all'utente finale.

Serve per debugging e osservabilità.

Evita però di loggare dati sensibili inutilmente.

---

# FASE 15 — ARCHITECTURE QUALITY

La soluzione deve essere:

* modulare;
* testabile;
* estensibile;
* type-safe dove applicabile;
* compatibile con l'architettura esistente;
* backward compatible dove possibile;
* sicura;
* multi-user;
* multi-company;
* indipendente dal singolo modello Odoo;
* facilmente estendibile a nuovi modelli.

Evita:

* duplicazione;
* if/else sparsi;
* mapping hardcoded in decine di tool;
* prompt giganteschi usati come unica logica;
* dipendenza da ID hardcoded;
* assunzioni sull'utente;
* bypass dei permessi Odoo.

---

# FASE 16 — PROCESSO DI IMPLEMENTAZIONE

Procedi in questo ordine:

## STEP 1

Analizza il codebase.

## STEP 2

Descrivi brevemente l'architettura attuale e individua i punti da modificare.

## STEP 3

Progetta la soluzione User Awareness.

## STEP 4

Implementa il CurrentUserContext.

## STEP 5

Implementa Identity/Reference Resolution.

## STEP 6

Integra il sistema nel conversation context.

## STEP 7

Integra il sistema nei tool Odoo.

## STEP 8

Integra il sistema nel prompt dell'agente.

## STEP 9

Implementa le protezioni di sicurezza.

## STEP 10

Scrivi i test.

## STEP 11

Esegui i test.

## STEP 12

Correggi eventuali problemi.

## STEP 13

Fai una revisione finale dell'implementazione.

---

# REGOLA IMPORTANTE

Non fermarti dopo avermi spiegato cosa dovrebbe essere fatto.

**Se hai accesso al codebase, implementa realmente le modifiche.**

Se una parte non può essere implementata perché manca una componente o un'informazione, individua esattamente il blocco e implementa comunque tutto ciò che è possibile senza inventare API o comportamenti.

Non riscrivere inutilmente parti funzionanti del sistema.

Prima di creare nuove astrazioni, verifica se nell'architettura esistono già componenti riutilizzabili.

---

# DEFINITION OF DONE

Considera il lavoro completato solo quando AIDA è realmente in grado di:

1. identificare l'utente autenticato;
2. conoscerne nome e dati account disponibili;
3. conoscere il relativo contesto Odoo;
4. distinguere utente corrente da altri utenti;
5. interpretare semanticamente "io/me/mio/miei/mie";
6. risolvere "i miei lead" verso i lead dell'utente corrente;
7. risolvere "le mie vendite" verso le vendite dell'utente corrente;
8. risolvere "i miei appuntamenti" verso gli appuntamenti dell'utente corrente;
9. applicare la stessa logica agli altri modelli Odoo pertinenti;
10. mantenere il riferimento durante una conversazione multi-turn;
11. passare da CURRENT_USER a un altro utente quando richiesto;
12. tornare a CURRENT_USER quando l'utente dice nuovamente "mio/miei/me";
13. rispettare ACL e record rules;
14. rispettare multi-company;
15. gestire ambiguità;
16. avere test automatici;
17. essere facilmente estensibile a nuovi modelli Odoo.

---

# OUTPUT FINALE RICHIESTO

Alla fine del lavoro forniscimi:

### 1. ARCHITECTURE SUMMARY

Spiega in modo conciso l'architettura implementata.

### 2. FILE MODIFICATI

Elenca tutti i file creati/modificati e perché.

### 3. USER AWARENESS FLOW

Mostra il flusso:

```text
Authenticated Odoo User
        ↓
CurrentUserContext
        ↓
Identity Resolution
        ↓
Semantic Intent
        ↓
Odoo Tool
        ↓
Security / Record Rules
        ↓
Result
```

### 4. TEST RESULTS

Indica quali test sono stati eseguiti e il risultato.

### 5. REMAINING ISSUES

Indica eventuali problemi ancora presenti.

### 6. NEXT RECOMMENDATIONS

Suggerisci solo miglioramenti realmente utili emersi dall'analisi del codebase.

**Non inventare file, API, classi o risultati di test.**
