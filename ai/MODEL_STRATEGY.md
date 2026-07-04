# MODEL_STRATEGY.md

# Scopo

Questo documento definisce quale livello di modello AI utilizzare nelle diverse fasi del progetto.

L'obiettivo è massimizzare la qualità delle decisioni riducendo il consumo di risorse.

---

# Principio generale

Le decisioni architetturali devono essere prese dal modello con le migliori capacità di ragionamento.

L'implementazione quotidiana deve essere eseguita dal modello più efficiente.

Una volta approvata una strategia, l'implementazione non deve ridefinire autonomamente l'architettura.

---

# Modelli utilizzati

## Modello di Ragionamento Avanzato

Attualmente:

**Claude Fable 5**

Responsabilità:

* analisi del repository
* Discovery iniziale
* analisi dell'architettura
* progettazione del Theme Engine
* progettazione del Design System
* definizione della Component Library
* analisi delle dipendenze
* UX Review
* proposta della Roadmap
* decisioni architetturali
* refactoring complessi
* valutazione di alternative progettuali
* revisione delle direttive presenti nella cartella `.ai/`

Non dovrebbe essere utilizzato per implementazioni ripetitive.

---

## Modello di Implementazione

Attualmente:

**Claude Opus 4.8**

Responsabilità:

* implementazione delle feature
* sviluppo dei componenti
* sviluppo SCSS
* override CSS
* implementazione OWL
* modifiche QWeb
* bug fixing
* refactoring locale
* review del codice
* ottimizzazioni
* test di regressione
* aggiornamento delle direttive quando richiesto

Deve rispettare l'architettura già approvata.

Non deve modificarla autonomamente.

---

# Workflow

## Fase 1

Discovery

↓

Modello di Ragionamento Avanzato

Output:

* Executive Summary
* Frontend Architecture
* UI Dependency Map
* Theme Engine Proposal
* Roadmap

---

## Fase 2

Discussione con l'Architect

↓

Approvazione

---

## Fase 3

Implementazione

↓

Modello di Implementazione

Per ogni task:

* analisi locale
* implementazione
* verifica regressioni
* review finale

---

## Fase 4

Se durante l'implementazione emerge un dubbio architetturale:

interrompere il task

↓

escalare al Modello di Ragionamento Avanzato

↓

ottenere una decisione

↓

proseguire con l'implementazione

---

# Escalation obbligatoria

È necessario utilizzare il Modello di Ragionamento Avanzato quando:

* l'architettura potrebbe cambiare;
* una modifica coinvolge numerosi moduli;
* sono presenti più soluzioni equivalenti;
* è necessario riprogettare una parte della UI;
* bisogna introdurre nuovi pattern;
* bisogna ridefinire il Design System;
* si valuta una modifica con impatto elevato.

---

# Implementazione ordinaria

Utilizzare il Modello di Implementazione quando:

* si sviluppa una feature già progettata;
* si modifica una vista;
* si aggiorna il CSS o SCSS;
* si implementa un componente;
* si corregge un bug;
* si migliora una schermata seguendo direttive già approvate.

---

# Regola fondamentale

Il modello di implementazione non deve reinventare l'architettura.

Se ritiene che una decisione architetturale possa essere migliorata deve:

1. fermarsi;
2. spiegare il motivo;
3. proporre l'escalation al Modello di Ragionamento Avanzato.

L'ultima decisione spetta sempre all'Architect.
