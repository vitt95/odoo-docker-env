# Step 11 — Final Visual QA, Dark Mode Audit & UI Polish (OBBLIGATORIO)

## Obiettivo

Il redesign è ormai completo.

Questa fase ha un unico obiettivo:

**raggiungere il massimo livello qualitativo possibile dell'interfaccia**, eliminando qualsiasi incongruenza visiva rispetto al Design System definito nelle immagini presenti in:

```text
.ai/ui-example/dark/
```

Questa fase NON introduce nuove funzionalità.

Non modifica la logica applicativa.

Non modifica il comportamento dell'applicazione.

È esclusivamente una fase di rifinitura e controllo qualità dell'interfaccia.

---

# Modalità di lavoro

Effettua una revisione completa dell'intera applicazione.

Non limitarti alle schermate principali.

Analizza sistematicamente tutte le viste, tutti i moduli e tutti i componenti renderizzati.

Per ogni vista controlla ogni elemento presente nell'interfaccia.

Nessun elemento può essere ignorato.

---

# Ispezione completa

L'ispezione deve comprendere almeno:

## Navigation

- Login
- App Shell
- Navbar
- Sidebar
- Breadcrumb
- Search
- Search Panel
- Systray
- Workspace
- Footer

---

## Views

- Dashboard
- Form View
- List View
- Kanban
- Calendar
- Activity
- Pivot
- Graph
- Cohort
- Gantt
- Discuss
- Chatter

---

## Control Panel

- Toolbar
- Search
- Filters
- Group By
- Favorites
- View Switcher
- Pagination

---

## Buttons

Analizza **tutti** i pulsanti.

Compresi:

- Primary
- Secondary
- Outline
- Ghost
- Toolbar
- Smart Buttons
- Floating Buttons
- Icon Buttons
- Dropdown Buttons
- Header Buttons
- Footer Buttons
- Action Buttons
- Context Buttons

Verifica per ciascuno:

- colori
- contrasto
- dimensioni
- padding
- radius
- bordi
- tipografia
- icone
- hover
- active
- focus
- disabled
- loading

Nessun pulsante deve conservare lo stile standard di Odoo.

---

## Forms

Controlla:

- Input
- Textarea
- Select
- Checkbox
- Radio
- Toggle
- Switch
- Date Picker
- Time Picker
- Datetime Picker
- Many2One
- Many2Many
- One2Many
- Attachments

Verifica:

- background
- testo
- placeholder
- focus
- hover
- border
- radius
- spacing
- contrasto

---

## Tables

Verifica:

- Header
- Celle
- Hover
- Selection
- Sorting
- Checkbox
- Pagination
- Footer
- Toolbar

---

## Kanban

Verifica:

- Header
- Colonne
- Card
- Footer
- Avatar
- Badge
- Dropdown
- Menu
- Progress
- Action Buttons

---

## Dialog & Overlay

Controlla:

- Modal
- Dialog
- Wizard
- Confirmation
- Tooltip
- Popover
- Dropdown
- Context Menu

---

## Feedback

Verifica:

- Notification
- Toast
- Alert
- Banner
- Empty State
- Error State
- Success
- Warning
- Loading
- Skeleton

---

## Widgets

Controlla ogni widget presente nell'applicazione.

Compresi quelli dei moduli custom.

---

# Audit Dark Mode

Ogni elemento deve essere confrontato con il Design System presente in:

```text
.ai/ui-example/dark/
```

Per ciascun componente verifica:

- colori
- superfici
- elevazione
- bordi
- radius
- tipografia
- contrasto
- leggibilità
- ombre
- stati interattivi

Correggi qualsiasi differenza.

---

# Uniformità

L'intera applicazione deve apparire progettata da un unico team di design.

Non devono esistere differenze di:

- padding
- margin
- radius
- shadow
- font
- dimensioni
- colori
- allineamenti
- spacing

Qualsiasi incoerenza deve essere eliminata.

---

# Pixel Alignment

Controlla con particolare attenzione:

- allineamenti verticali
- allineamenti orizzontali
- baseline tipografica
- griglia
- ritmo verticale
- ritmo orizzontale
- padding
- margin
- distribuzione dello spazio

Ogni elemento deve risultare perfettamente allineato.

---

# Tipografia

Verifica:

- font family
- fallback
- peso
- dimensioni
- line-height
- letter spacing
- gerarchia
- leggibilità

La tipografia deve risultare perfettamente coerente con il Design System.

---

# Stati Interattivi

Verifica ogni stato disponibile:

- hover
- active
- focus
- disabled
- loading
- selected
- expanded
- collapsed

Ogni stato deve essere coerente con il Design System.

---

# Componenti Core

Anche tutti i componenti appartenenti al core di Odoo devono essere ispezionati.

Se il loro aspetto non rispetta il Design System devono essere personalizzati utilizzando esclusivamente:

- OWL Patch
- Template Inheritance
- XML Inheritance
- Registries
- Services
- Hooks
- Asset Bundle
- SCSS
- CSS Variables
- Moduli Custom

È severamente vietato modificare direttamente il core di Odoo.

---

# Processo Iterativo (OBBLIGATORIO)

Questa fase deve essere eseguita in modo iterativo.

Per ogni componente:

1. Analizza il risultato corrente.
2. Confrontalo con le immagini presenti in `.ai/ui-example/dark/`.
3. Individua tutte le differenze visive.
4. Correggi le differenze.
5. Riesegui l'ispezione.
6. Ripeti il ciclo fino a quando non rimangono più differenze significative.

Non interrompere il processo dopo la prima correzione.

L'ispezione deve essere ripetuta fino a raggiungere il massimo livello qualitativo possibile.

---

# Criteri di Accettazione

Il lavoro può considerarsi completato esclusivamente quando:

- non esistono pulsanti con stile differente;
- non esistono menu con colori incoerenti;
- non esistono pannelli con superfici errate;
- non esistono dialog con stile standard Odoo;
- non esistono componenti che utilizzano ancora colori Light in modalità Dark;
- non esistono font incoerenti;
- non esistono radius differenti;
- non esistono ombre incoerenti;
- non esistono spaziature irregolari;
- non esistono componenti che rivelino il tema originale di Odoo.

---

# Definizione di "Completato"

Il redesign può considerarsi completato esclusivamente quando un utente esperto di Odoo, osservando l'interfaccia, **non è più in grado di riconoscere il tema standard della piattaforma**.

Ogni vista, ogni pulsante, ogni pannello, ogni menu, ogni dialog, ogni tabella, ogni form e ogni componente dell'applicazione deve apparire come parte integrante del Design System definito nelle immagini presenti in:

```text
.ai/ui-example/dark/
```

La qualità finale deve essere paragonabile a quella di un prodotto enterprise sviluppato con un Design System unico, coerente e professionale, senza alcuna regressione funzionale e senza modificare direttamente il core di Odoo.

credenziali di accesso a odoo
user: vittorioaiello95@gmail.com
pass: NuovaPassword123!