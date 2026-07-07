# Bootstrap Prompt — Odoo UI Redesign

## Premessa

Prima di eseguire qualsiasi attività, leggi integralmente tutti i file presenti nella cartella `.ai/`.

Leggi poi il file `MODEL_STRATEGY` e considera tutte le indicazioni contenute come direttive progettuali vincolanti.

Tutti i file presenti nella cartella `.ai/` costituiscono la documentazione ufficiale del progetto e definiscono:

- obiettivi;
- architettura;
- filosofia del redesign;
- metodologia;
- vincoli tecnici;
- standard qualitativi.

Non considerarli semplice documentazione.

Sono parte integrante della specifica di progetto.

---

# Obiettivo del progetto

L'obiettivo NON è creare un nuovo tema grafico.

L'obiettivo è sostituire completamente il Design System di Odoo mantenendo invariata la piattaforma.

Il risultato finale dovrà dare l'impressione che Odoo sia stato progettato nativamente utilizzando il Design System presente nella cartella:

```text
.ai/ui-example/
```

senza alterare il comportamento dell'applicazione.

---

# UI Reference (SPECIFICA UFFICIALE)

Le immagini presenti nelle cartelle

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

costituiscono la **specifica visiva ufficiale** del progetto.

NON rappresentano una semplice ispirazione.

NON devono essere reinterpretate.

Devono essere considerate il riferimento principale durante ogni decisione progettuale.

---

# Livello di fedeltà richiesto

Target:

**95–100% di fedeltà visiva**

La replica deve riguardare:

- layout
- proporzioni
- spacing
- typography
- colori
- border
- radius
- elevation
- ombre
- icone
- toolbar
- navbar
- sidebar
- dashboard
- search
- control panel
- kanban
- form
- list
- calendar
- chatter
- discuss
- dialogs
- notifications
- systray
- dropdown
- menu
- breadcrumb
- badges
- tabs
- buttons
- inputs
- cards
- hover
- focus
- active
- disabled
- animations
- micro-interactions

L'obiettivo è ottenere una replica quanto più vicina possibile al Design System mostrato nelle immagini.

---

# Design System First

Qualsiasi decisione estetica deve essere presa esclusivamente osservando le immagini presenti in:

```text
.ai/ui-example/
```

e non osservando la UI originale di Odoo.

Il tema standard di Odoo deve essere considerato esclusivamente infrastruttura tecnica.

---

# Discovery (OBBLIGATORIA)

Prima di qualsiasi implementazione completa una fase approfondita di analisi.

Analizza:

- repository
- moduli custom
- frontend architecture
- asset bundles
- componenti OWL
- template QWeb
- XML
- JavaScript
- SCSS
- CSS Variables
- registries
- services
- hooks
- patches
- controllers
- renderers
- models
- view architecture
- dependency graph
- extension points

Per ogni componente individua:

- punto di rendering
- gerarchia
- dipendenze
- ereditarietà
- possibilità di override
- possibilità di patch
- servizi utilizzati
- registries utilizzati
- hooks utilizzati

---

# UI Audit

Analizza completamente tutte le immagini presenti in

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

Ricostruisci automaticamente il Design System identificando:

## Typography

- font family
- fallback
- font scale
- weights
- line height
- letter spacing

## Colors

- primary
- secondary
- neutrals
- semantic colors
- background
- surfaces
- borders

## Layout

- spacing scale
- gutters
- grid
- breakpoints
- containers

## Components

- button system
- cards
- dialogs
- forms
- tables
- kanban
- navigation
- search
- dashboard
- notifications
- overlays

## Motion

- animations
- transitions
- interaction states

---

# Component Mapping

Per ogni componente presente nelle immagini individua il corrispondente componente di Odoo.

Costruisci una matrice contenente almeno:

Reference Component

↓

Odoo Component

↓

OWL Component

↓

XML

↓

QWeb

↓

SCSS

↓

JS

↓

Override Strategy

↓

Risk

---

# Dependency Analysis

Costruisci una mappa completa delle dipendenze.

Per ogni componente individua:

- chi lo renderizza
- chi lo utilizza
- chi lo estende
- chi dipende da lui
- quali hook utilizza
- quali services utilizza
- quali registries utilizza
- quali assets utilizza
- quali template eredita
- quali patch esistono

---

# UI Contract Analysis

Per ogni componente separa chiaramente:

## Classi funzionali

Classi utilizzate da:

- OWL
- JavaScript
- servizi
- drag & drop
- renderer
- controller
- eventi

Queste NON devono essere alterate se comprometterebbero il funzionamento.

## Classi puramente visuali

Queste possono essere completamente ridisegnate.

---

# Component Inventory

Il redesign deve comprendere ogni componente UI.

Inclusi:

- Login
- Navbar
- Sidebar
- App Shell
- Dashboard
- Search
- Search Panel
- Control Panel
- Form View
- List View
- Kanban
- Calendar
- Activity
- Pivot
- Graph
- Cohort
- Gantt
- Chatter
- Discuss
- Dialog
- Notification
- Toast
- Popover
- Tooltip
- Dropdown
- Context Menu
- Breadcrumb
- Tabs
- Buttons
- Inputs
- Checkbox
- Radio
- Toggle
- Select
- Date Picker
- Time Picker
- Avatar
- Badges
- Cards
- Tables
- KPI
- Charts
- Widgets
- Empty States
- Error States
- Skeleton
- Loading
- Systray
- qualsiasi altro componente individuato durante l'analisi.

Nessun componente deve essere escluso.

---

# Theme Engine (OBBLIGATORIO)

L'interfaccia deve supportare nativamente:

- Light Mode
- Dark Mode

La modalità Light deve essere derivata dalle immagini in:

```text
.ai/ui-example/light/
```

La modalità Dark deve essere derivata dalle immagini in:

```text
.ai/ui-example/dark/
```

---

## Design Tokens

È obbligatorio utilizzare un Theme Engine basato su Design Tokens.

È vietato utilizzare colori hardcoded.

Tutti i componenti devono utilizzare esclusivamente token semantici.

---

# Responsive (OBBLIGATORIO)

L'interfaccia deve essere progettata secondo un approccio Responsive First.

Supportare completamente:

- Desktop
- Laptop
- Tablet
- Mobile

Ogni breakpoint deve avere un layout studiato.

Non limitarti a comprimere il layout desktop.

---

# Tipografia

Replica fedelmente:

- font
- pesi
- dimensioni
- line-height
- spaziatura
- gerarchia

L'intera applicazione deve utilizzare un unico sistema tipografico coerente con il Design System.

---

# Precisione del Layout

Ogni componente deve rispettare rigorosamente:

- allineamenti
- margini
- padding
- proporzioni
- ritmo verticale
- ritmo orizzontale
- griglia

Non sono accettabili disallineamenti.

---

# Refactoring del Core

È assolutamente vietato modificare direttamente il core di Odoo.

Qualsiasi personalizzazione deve essere realizzata esclusivamente attraverso:

- OWL Patch
- Template Inheritance
- XML Inheritance
- Registries
- Services
- Hooks
- Asset Bundle
- SCSS Inheritance
- CSS Variables
- Moduli Custom

Il progetto deve rimanere completamente aggiornabile.

---

# Processo Iterativo

Per ogni componente eseguire:

1. Analisi del componente.
2. Confronto con il riferimento.
3. Implementazione.
4. Confronto visivo.
5. Individuazione delle differenze.
6. Correzione.
7. Nuovo confronto.

Ripetere il processo fino a raggiungere il livello qualitativo richiesto.

---

# Criteri di Accettazione

Il redesign può considerarsi completato soltanto se:

- fedeltà visiva tra il 95% e il 100%;
- nessuna regressione funzionale;
- nessuna modifica diretta al core;
- copertura completa di tutti i componenti UI;
- supporto completo Light/Dark Mode;
- completamente responsive;
- utilizzo esclusivo di Design Tokens;
- tipografia coerente;
- allineamenti perfetti;
- Design System uniforme;
- nessun elemento riconducibile al tema standard di Odoo;
- codice modulare, estendibile e manutenibile.

---

# Output Atteso

Prima di qualsiasi implementazione restituisci esclusivamente:

1. Executive Summary
2. Frontend Architecture
3. UI Dependency Map
4. Component Inventory
5. Design System estratto dalle immagini
6. Component Mapping
7. Dependency Analysis
8. UI Contract Analysis
9. Theme Engine Proposal
10. Responsive Strategy
11. Piano di Refactoring
12. Piano di Implementazione
13. Analisi dei rischi
14. Eventuali conflitti architetturali
15. Stima della fedeltà visiva raggiungibile

Non implementare nulla fino al mio esplicito via libera.