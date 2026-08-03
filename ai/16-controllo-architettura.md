# PROMPT — AUDIT COMPLETO DEL MOTORE DI QUERY SEMANTICA DEL CRM

Assumi il ruolo di **Principal Software Architect**, **Staff AI Engineer**, **Database Architect**, **NLP Engineer**, **QA Lead** e **Security Engineer**.

Il tuo obiettivo NON è aggiungere nuove funzionalità, ma portare il progetto ad un livello **enterprise**, individuando qualsiasi bug, debolezza, incoerenza o rischio presente nell'intera architettura.

Devi analizzare criticamente ogni componente del progetto, senza dare nulla per scontato.

Non limitarti al codice modificato recentemente.

Analizza l'intero progetto.

---

# OBIETTIVO FINALE

Il prodotto dovrà essere in grado di trasformare qualsiasi richiesta scritta da un essere umano in una query semanticamente perfetta sul CRM.

L'utente deve poter scrivere liberamente, ad esempio:

* mostrami tutti i lead
* quanti lead abbiamo
* quanti lead sono aperti
* quanti lead sono stati creati questo mese
* quanti lead sono stati creati ieri
* quali sono i 10 lead più recenti
* mostrami i lead ordinati per fatturato
* qual è il fatturato medio dei lead
* qual è il lead con il fatturato massimo
* qual è il lead con il fatturato minimo
* quanti lead ci sono per stato
* quanti lead ci sono per owner
* mostrami i lead senza email
* mostrami i lead senza telefono
* mostrami i lead creati negli ultimi 30 giorni
* mostrami le aziende con più di 10 lead
* mostrami i lead che hanno almeno un'opportunità
* mostrami i lead che non hanno attività
* quali città hanno più lead
* quali regioni hanno meno lead
* dammi il numero di opportunità vinte
* dammi la media del valore delle opportunità
* mostrami le attività della settimana scorsa
* mostrami i ticket aperti negli ultimi 7 giorni

e migliaia di interrogazioni analoghe.

Il sistema deve comprendere perfettamente il linguaggio naturale.

Non deve mai inventare dati.

Non deve mai inventare campi.

Non deve mai inventare entità.

Non deve mai inventare relazioni.

Non deve mai inventare operatori.

In presenza di ambiguità deve chiedere chiarimenti oppure produrre un errore semanticamente corretto.

---

# PRINCIPIO FONDAMENTALE

L'LLM NON DEVE GENERARE SQL.

L'LLM deve produrre esclusivamente una rappresentazione semantica della query (AST / Query Object).

Solo successivamente il sistema convertirà tale rappresentazione nella query SQL/ORM.

Questo è un requisito imprescindibile.

---

# ANALISI COMPLETA

Analizza in profondità ogni parte del progetto.

Non fermarti alla superficie.

Analizza:

* architettura generale
* prompt
* parser
* entity resolver
* field resolver
* operator resolver
* date resolver
* synonym resolver
* validator
* query builder
* execution layer
* formatter della risposta
* gestione errori
* logging
* sicurezza
* performance
* estendibilità
* manutenzione
* scalabilità
* multi-entità
* supporto future entità CRM

---

# ANALISI DELLA PIPELINE

Verifica ogni passaggio.

L'intera pipeline deve essere trattata come un compilatore.

```
Utente

↓

Natural Language

↓

Intent Detection

↓

Entity Resolution

↓

Field Resolution

↓

Operator Resolution

↓

Date Resolution

↓

Relationship Resolution

↓

Semantic Validation

↓

AST

↓

Business Validation

↓

SQL Builder / ORM Builder

↓

Execution

↓

Formatter

↓

Risposta Finale
```

Per ogni livello individua:

* bug
* edge case
* errori logici
* condizioni di race
* ambiguità
* casi non gestiti
* prompt fragili
* mapping incompleti
* possibilità di hallucination
* incoerenze

---

# ENTITY RESOLUTION

Verifica che ogni entità possa essere identificata con sinonimi differenti.

Esempi:

Lead

* lead
* prospect
* potenziale cliente

Company

* azienda
* società
* account
* cliente

Contact

* contatto
* referente
* persona

Opportunity

* opportunità
* trattativa
* deal

Activity

* attività
* task
* appuntamento

Ticket

* ticket
* segnalazione
* richiesta

Se manca qualunque mapping, segnalalo.

---

# FIELD RESOLUTION

Verifica che tutti i campi siano risolvibili con sinonimi naturali.

Esempi:

email

* mail
* posta elettronica
* indirizzo email

telefono

* telefono
* cellulare
* numero

azienda

* company
* società
* ragione sociale

created_at

* creato
* data creazione
* quando è stato creato

owner

* assegnato a
* responsabile
* commerciale

status

* stato
* situazione

Se manca un sinonimo importante deve essere segnalato.

---

# INTENT DETECTION

Verifica tutti gli intenti.

SELECT

COUNT

SUM

AVG

MIN

MAX

DISTINCT

GROUP BY

HAVING

ORDER BY

LIMIT

OFFSET

JOIN

EXISTS

NOT EXISTS

FILTER

SEARCH

EXPORT

PAGINATION

Ogni intento deve essere rilevato correttamente.

---

# OPERATORI

Verifica il supporto di:

=

!=

>

<

> =

<=

LIKE

ILIKE

IN

NOT IN

BETWEEN

IS NULL

IS NOT NULL

CONTAINS

STARTS WITH

ENDS WITH

EXISTS

NOT EXISTS

---

# DATE RESOLUTION

Verifica tutte le date relative.

oggi

ieri

domani

questa settimana

settimana scorsa

questo mese

mese scorso

ultimi 7 giorni

ultimi 30 giorni

ultimi 90 giorni

quest'anno

anno scorso

Q1

Q2

Q3

Q4

gennaio

febbraio

marzo

...

---

# AGGREGAZIONI

Verifica:

COUNT

SUM

AVG

MIN

MAX

DISTINCT

GROUP BY

HAVING

GROUP BY multipli

ORDER multipli

aggregazioni annidate

---

# JOIN

Verifica:

Lead -> Company

Lead -> Contact

Lead -> Opportunity

Lead -> Activity

Company -> Opportunity

Company -> Contact

Contact -> Activity

e tutte le relazioni esistenti.

---

# QUERY COMPLESSE

Verifica interrogazioni come:

Quanti lead aperti abbiamo?

Quanti lead aperti per owner?

Quali owner hanno più lead?

Qual è la media del fatturato dei lead aperti?

Qual è il massimo fatturato per regione?

Quali aziende hanno almeno 10 lead?

Quali lead non hanno attività?

Quali opportunità sono state vinte questo mese?

Quali ticket sono aperti da oltre 30 giorni?

Quali aziende non hanno referenti?

Quali contatti hanno più attività?

Verifica migliaia di varianti.

---

# TEST LINGUAGGIO NATURALE

L'utente può scrivere:

fammi vedere

mostrami

dammi

tirami fuori

elenca

recupera

visualizza

voglio vedere

quali sono

quanti sono

mi dici

potresti mostrarmi

Il sistema deve produrre sempre lo stesso AST.

---

# GESTIONE AMBIGUITÀ

Il sistema NON deve mai indovinare.

Esempio:

"I migliori lead"

Non è definito.

Deve chiedere:

* migliori per fatturato?
* migliori per punteggio?
* migliori per probabilità?

---

# VALIDAZIONE

Verifica che venga impedita qualsiasi query che utilizzi:

* campi inesistenti
* entità inesistenti
* relazioni inesistenti
* operatori non validi
* funzioni non supportate

---

# ROBUSTEZZA

Testa:

* valori null
* stringhe vuote
* caratteri unicode
* emoji
* maiuscole
* minuscole
* typo
* accenti
* apostrofi
* input rumorosi
* input molto lunghi
* input molto corti

---

# PERFORMANCE

Valuta:

10 record

100 record

1.000 record

10.000 record

100.000 record

1.000.000 record

Individua eventuali colli di bottiglia.

---

# DATASET

Se il database non è sufficiente, genera dataset realistici.

Lead

Company

Contact

Opportunity

Activity

Ticket

Inserisci:

* stati differenti
* owner differenti
* città
* regioni
* paesi
* email mancanti
* telefoni mancanti
* duplicati
* valori estremi
* record inconsistenti
* record storici
* record recenti

Il dataset deve permettere di testare qualsiasi query.

---

# TEST SUITE

Costruisci una suite di test completa.

Ogni test deve contenere:

* input utente
* intent previsto
* entity prevista
* field previsti
* operatori previsti
* AST previsto
* query attesa
* risultato atteso

La suite deve contenere centinaia di test e coprire tutti gli edge case.

---

# SICUREZZA

Verifica:

hallucination

SQL Injection

Prompt Injection

Entity Injection

Field Injection

Bypass validator

Prompt leakage

Prompt override

Escaping

Input malevoli

---

# ESTENDIBILITÀ

Il sistema dovrà funzionare non solo con Lead.

Domani potranno essere installate nuove entità CRM.

Analizza se l'architettura è realmente plug-and-play.

L'aggiunta di una nuova entità non dovrebbe richiedere modifiche profonde al motore.

Segnala eventuali punti in cui il codice è troppo accoppiato.

---

# OUTPUT RICHIESTO

Per ogni problema individua:

* Titolo
* Gravità
* Probabilità
* Componente coinvolto
* Descrizione tecnica
* Impatto sul prodotto
* Esempio reale
* Root cause
* Soluzione consigliata
* Patch suggerita
* Test che verifica la correzione
* Priorità di implementazione

---

# OBIETTIVO FINALE

L'obiettivo NON è semplicemente "far funzionare" il sistema.

L'obiettivo è costruire un motore di interrogazione semantica affidabile, deterministico, estendibile e di livello enterprise.

Due utenti che pongono la stessa domanda devono ottenere lo stesso AST.

L'AST deve essere sempre semanticamente corretto rispetto allo schema del CRM.

Nessuna query deve essere eseguita se non supera tutte le validazioni.

Il sistema deve poter gestire qualunque interrogazione supportata dal CRM, incluse:

* SELECT
* COUNT
* SUM
* AVG
* MIN
* MAX
* DISTINCT
* GROUP BY
* HAVING
* ORDER BY
* LIMIT
* OFFSET
* JOIN
* EXISTS
* NOT EXISTS
* filtri complessi
* condizioni multiple
* aggregazioni
* interrogazioni multi-entità
* statistiche
* report
* dashboard
* confronti temporali
* analisi per periodo
* classifiche
* ranking
* percentuali
* KPI
* query annidate
* combinazioni di operatori
* qualsiasi interrogazione semanticamente supportata dal modello dati.

Non fermarti finché non avrai individuato ogni possibile bug, debolezza, malfunzionamento, comportamento ambiguo o rischio architetturale e proposto una soluzione concreta, motivata e verificabile.
