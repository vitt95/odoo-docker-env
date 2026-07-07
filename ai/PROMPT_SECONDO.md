# UI Reference Specification (VINCOLANTE)

## Premessa

L'immagine presente nel percorso:

```text
.ai/ui-example/
```

costituisce la **specifica visiva ufficiale** del progetto.

Non deve essere considerata una semplice ispirazione grafica, ma il riferimento principale da seguire durante l'intero redesign dell'interfaccia.

L'obiettivo è realizzare una UI moderna che riproduca il linguaggio visivo del riferimento mantenendo la piena compatibilità con Odoo e con l'architettura già implementata.

---

# Obiettivo del redesign

Questa iterazione **NON introduce nuove funzionalità**.

L'obiettivo è esclusivamente migliorare l'esperienza utente attraverso un redesign completo dell'interfaccia.

La logica applicativa, i flussi, le API e il comportamento del sistema devono rimanere invariati.

L'intervento deve concentrarsi sulla qualità della UI.

---

# Immagine di riferimento

Utilizza come riferimento tutte le immagini presenti nella directory:

```text
.ai/ui-example/
```

Durante ogni fase dell'implementazione confronta costantemente il risultato ottenuto con tali immagini.

Se esistono più immagini, considerale come un unico Design System coerente.

---

# Livello di fedeltà richiesto

**Target: circa 80% di fedeltà visiva** rispetto alle immagini presenti in:

```text
.ai/ui-example/
```

La fedeltà deve riguardare principalmente:

- linguaggio visivo
- gerarchia delle informazioni
- layout
- organizzazione dei componenti
- proporzioni
- spacing
- tipografia
- palette colori
- stile dei componenti
- comportamento responsive

Non è richiesta una replica pixel-perfect, ma il risultato finale deve risultare chiaramente ispirato allo stesso design system.

---

# Elementi da replicare

L'analisi deve comprendere almeno:

- Header
- Navbar
- Sidebar
- Dashboard
- Search
- Control Panel
- Form View
- List View
- Kanban
- Calendar
- Chatter
- Dialog
- Notification
- Systray
- Discuss
- Breadcrumb
- Menu
- Dropdown
- Badge
- Tabs
- Buttons
- Inputs
- Cards
- Toolbar

Per ogni componente individua:

- struttura
- gerarchia visiva
- dimensioni
- densità delle informazioni
- allineamenti
- spacing
- colori
- radius
- ombre
- stati hover
- stati active
- stati focus
- animazioni
- micro-interazioni

---

# Redesign completo

Non limitarti a modificare:

- colori
- font
- border-radius
- ombre

È richiesto un redesign dell'intera composizione della UI.

Se necessario modifica:

- OWL Components
- Template QWeb
- struttura HTML
- SCSS
- CSS
- Design Tokens
- CSS Variables
- Layout
- Grid
- Spacing
- Component Composition

---

# Design System

Prima di implementare estrai dal riferimento un Design System composto almeno da:

## Typography

- font family
- font scale
- font weight
- line height

## Colors

- primary
- secondary
- neutrals
- background
- surface
- border
- semantic colors

## Layout

- spacing scale
- gutters
- grid
- container width
- responsive breakpoints

## Components

- button system
- inputs
- cards
- navigation
- sidebar
- dialogs
- tables
- kanban cards
- badges
- tabs

## Interactions

- hover
- focus
- active
- disabled
- transitions
- animations

Tutti i componenti devono utilizzare gli stessi Design Tokens per garantire uniformità visiva.

---

# Vincoli

Devono rimanere invariati:

- logica applicativa
- business logic
- API
- servizi
- registries
- hook
- patch
- flussi utente
- accessibilità
- compatibilità con Odoo
- compatibilità con i moduli custom

Può essere modificato tutto ciò che riguarda esclusivamente la presentazione della UI.

---

# Priorità

Ordine di priorità:

1. Coerenza con il Design System presente in `.ai/ui-example/`
2. Qualità della UI
3. Coerenza tra tutte le schermate
4. Riutilizzabilità dei componenti
5. Manutenibilità del codice

---

# Cosa evitare

Non mantenere componenti esistenti soltanto per ridurre il lavoro.

Se un componente impedisce di ottenere una resa coerente con il riferimento, ridisegnalo.

Non adattare il design di riferimento alla UI esistente.

Adatta invece la UI esistente al Design System definito dalle immagini presenti in:

```text
.ai/ui-example/
```


L'interfaccia deve essere progettata fin dall'inizio per supportare nativamente due modalità:

- Light Mode
- Dark Mode

La modalità Light costituisce il riferimento principale e deve essere derivata dalle immagini presenti in:

```text
.ai/ui-example/
```

La modalità Dark deve rappresentare una conversione coerente dello stesso Design System, mantenendo identica la gerarchia visiva, le proporzioni e l'esperienza utente.

---

## Architettura del Theme Engine

Non implementare due fogli di stile separati.

Realizza un vero Theme Engine basato su Design Tokens.

Tutti gli elementi grafici devono utilizzare esclusivamente token semantici, evitando colori hardcoded all'interno dei componenti.

Ad esempio:

- background
- surface
- surface-secondary
- border
- border-subtle
- text-primary
- text-secondary
- text-muted
- primary
- primary-hover
- success
- warning
- danger
- info
- shadow
- overlay
- focus-ring

I componenti OWL, i template QWeb e gli stylesheet non devono conoscere direttamente i colori reali.

Devono fare riferimento esclusivamente ai Design Tokens.

---

## Cambio tema

L'applicazione deve consentire il passaggio tra:

- Light
- Dark

senza richiedere modifiche al codice dei componenti.

Il cambio tema deve avvenire modificando esclusivamente il set di Design Tokens.

---

## Requisiti

Entrambe le modalità devono garantire:

- identica UX
- identica gerarchia visiva
- identica struttura dei layout
- stessi componenti
- stessi spacing
- stessi radius
- stessa tipografia
- stessa accessibilità

La differenza deve riguardare esclusivamente il tema cromatico e gli adattamenti necessari per garantire leggibilità e contrasto.

---

## Compatibilità

Il Theme Engine deve essere progettato in modo da permettere l'aggiunta futura di ulteriori temi senza modificare i componenti esistenti.

L'aggiunta di un nuovo tema dovrà richiedere esclusivamente la definizione di un nuovo set di Design Tokens.

---

## Obiettivo

L'intera UI deve essere completamente theme-aware.

Nessun componente deve dipendere direttamente dalla modalità Light o Dark.

Tutte le decisioni cromatiche devono essere centralizzate nel Theme Engine.

# Responsive Design (OBBLIGATORIO)

L'intera interfaccia deve essere progettata secondo un approccio **Responsive First**.

Il responsive non rappresenta una fase successiva del progetto, ma un requisito architetturale da considerare durante tutta l'implementazione.

Ogni componente deve adattarsi correttamente alle diverse dimensioni dello schermo senza compromettere usabilità, leggibilità o coerenza del Design System.

---

## Dispositivi supportati

L'interfaccia deve offrire un'esperienza ottimale su:

- Desktop (Full HD e superiori)
- Laptop
- Tablet (portrait e landscape)
- Mobile

Ogni breakpoint deve essere progettato intenzionalmente e non ottenuto tramite semplici ridimensionamenti.

---

## Comportamento atteso

Ogni schermata deve prevedere un layout specifico per i diversi breakpoint.

In particolare:

- Sidebar collassabile sui display ridotti.
- Navbar adattiva.
- Toolbar responsive.
- Search responsive.
- Control Panel adattivo.
- Kanban con colonne ridistribuite.
- Form responsive.
- List View con gestione intelligente delle colonne.
- Dialog ridimensionabili.
- Dashboard con griglie adattive.
- Chatter adattivo.
- Menu e dropdown ottimizzati per touch.

---

## Layout

Utilizzare layout fluidi.

Evitare:

- larghezze fisse
- altezze fisse
- posizionamenti assoluti non necessari
- valori hardcoded che impediscano il ridimensionamento

Preferire:

- CSS Grid
- Flexbox
- container fluidi
- spacing scalabili
- dimensioni relative

---

## Breakpoints

Definire un sistema di breakpoint coerente e centralizzato.

Ogni componente deve rispettare gli stessi breakpoint del Design System.

Non introdurre media query isolate all'interno dei singoli componenti quando è possibile utilizzare un sistema condiviso.

---

## Esperienza utente

Il comportamento responsive deve preservare:

- gerarchia visiva
- densità delle informazioni
- facilità di navigazione
- accessibilità
- leggibilità
- performance

La riduzione dello spazio disponibile non deve comportare la perdita di funzionalità.

---

## Componenti

Tutti i componenti devono essere completamente responsive, inclusi:

- Login
- Navbar
- Sidebar
- Dashboard
- Search
- Control Panel
- Form View
- List View
- Kanban
- Calendar
- Chatter
- Discuss
- Dialog
- Notification
- Systray
- Menu
- Breadcrumb
- Dropdown
- Badge
- Tabs
- Buttons
- Inputs

---

## Qualità richiesta

La UI deve mantenere lo stesso livello qualitativo su ogni dispositivo.

Non sono accettabili soluzioni che funzionino esclusivamente su desktop.

L'esperienza deve risultare naturale sia con mouse e tastiera sia con dispositivi touch.

Il risultato finale deve essere coerente con il Design System definito dalle immagini presenti nella directory `.ai/ui-example/`, indipendentemente dalle dimensioni dello schermo.
---

# Output atteso

Prima di modificare qualsiasi file restituisci esclusivamente:

1. Analisi comparativa tra la UI attuale e il Design System presente in `.ai/ui-example/`
2. Componenti che richiedono un redesign
3. Strategia di implementazione
4. Piano delle modifiche
5. Eventuali limitazioni tecniche
6. Stima del livello di fedeltà raggiungibile

Attendi esplicitamente il via libera prima di procedere con qualsiasi implementazione.