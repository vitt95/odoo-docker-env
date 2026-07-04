# Bootstrap Prompt

Prima di eseguire qualsiasi attività, leggi integralmente tutti i file presenti nella cartella `.ai/`.

Leggi poi il file MODEL_STRATEGY dove ci sono le indicazioni su quali modelli usare e in quali fasi.

Considera tali file come **direttive progettuali vincolanti**, non come semplice documentazione.

Il loro scopo è definire:

* il modo in cui deve essere sviluppato il progetto;
* le regole ingegneristiche da rispettare;
* la filosofia del redesign;
* i vincoli architetturali;
* il processo decisionale da seguire.

Se durante l'analisi individui incongruenze tra il codice esistente e le direttive, **non adeguare automaticamente le direttive al codice esistente**.

Segnala invece il conflitto, spiegane le conseguenze e proponi una o più soluzioni motivate.

---

## Fase 1 — Discovery

Prima di qualsiasi implementazione esegui una fase completa di analisi del progetto.

L'obiettivo non è produrre documentazione, ma costruire un modello mentale accurato dell'architettura del sistema.

Analizza in particolare:

* struttura del repository;
* moduli custom;
* architettura frontend;
* asset bundle;
* componenti OWL;
* template QWeb;
* viste XML e relativa ereditarietà;
* JavaScript;
* SCSS;
* registries;
* services;
* patch;
* hook;
* punti di estensione;
* dipendenze tra componenti;
* personalizzazioni già presenti.

Per la UI analizza attentamente almeno:

* Login
* App Shell
* Navbar
* Sidebar
* Dashboard
* Search
* Control Panel
* Form View
* List View
* Kanban
* Calendar
* Chatter
* Dialog
* Notification
* Systray
* Discuss
* ogni altro componente rilevante individuato durante l'analisi.

Per ciascuno identifica:

* dove viene renderizzato;
* quali componenti lo compongono;
* quali dipendenze possiede;
* quali override sono già presenti;
* quali classi CSS fanno parte del contratto funzionale con JavaScript o OWL;
* quali classi sono invece esclusivamente presentazionali.

---

## Output atteso

Al termine della Discovery non implementare nulla.

Restituisci esclusivamente:

1. Executive Summary
2. Frontend Architecture
3. UI Dependency Map
4. Critical Points
5. Theme Engine Proposal
6. Roadmap tecnica consigliata

Se ritieni che l'architettura proposta nelle direttive possa essere migliorata, proponi un'alternativa motivandola.

Non creare file.

Non modificare file.

Non scrivere codice, salvo piccoli esempi utili a spiegare una proposta architetturale.

Attendi il mio via libera prima di iniziare qualsiasi implementazione.
