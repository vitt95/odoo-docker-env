---

# Dynamic UI Exploration (OBBLIGATORIO)

L'ispezione non deve limitarsi ai componenti visibili al caricamento iniziale della pagina.

È obbligatorio esplorare ricorsivamente l'intera applicazione simulando il comportamento reale di un utente.

Durante l'analisi apri e verifica qualsiasi componente venga renderizzato dinamicamente.

Compresi:

## Menu

- Dropdown
- Context Menu
- Systray
- User Menu
- Action Menu
- Smart Button Menu
- View Switcher

---

## Overlay

- Modal
- Dialog
- Wizard
- Popover
- Tooltip
- Confirm Dialog
- Notification
- Toast

---

## Editor

Analizza completamente tutti gli editor presenti nell'applicazione.

Compresi:

- WYSIWYG
- HTML Editor
- Rich Text Editor
- Mail Composer
- Chatter Composer
- Discuss Composer

Verifica ogni pulsante, ogni icona e ogni stato dell'interfaccia.

---

## Form Components

Espandi e verifica tutti i componenti interattivi.

Compresi:

- Date Picker
- Time Picker
- Datetime Picker
- Color Picker
- Select
- Multi Select
- Many2One
- Many2Many
- One2Many
- Search Autocomplete
- Command Palette

---

## Views

Per ogni modulo analizza tutte le viste disponibili.

Compresi:

- Dashboard
- Form
- List
- Kanban
- Calendar
- Activity
- Pivot
- Graph
- Cohort
- Gantt
- Discuss
- Chatter

Apri inoltre tutte le viste secondarie raggiungibili.

---

## Stati Dinamici

Verifica anche tutti gli elementi che compaiono esclusivamente durante le interazioni.

Compresi:

- Hover
- Focus
- Active
- Disabled
- Selected
- Expanded
- Collapsed
- Loading
- Empty State
- Error State
- Success State

---

# Esplorazione Ricorsiva

Per ogni vista esegui ricorsivamente il seguente processo:

1. Apri la vista.
2. Individua tutti i componenti interattivi.
3. Interagisci con ciascun componente.
4. Individua eventuali nuovi componenti comparsi.
5. Analizza anche questi nuovi componenti.
6. Ripeti il processo fino a quando non vengono più renderizzati nuovi elementi.

L'obiettivo è raggiungere il 100% della copertura dell'interfaccia utente.

Nessun componente deve rimanere non verificato.

---

# Icon Discovery

Non limitarti alle icone immediatamente visibili.

Analizza qualsiasi icona venga renderizzata durante l'utilizzo dell'applicazione.

Compresi:

- SVG dinamici
- Font Icons
- Icone dei menu contestuali
- Icone del WYSIWYG
- Icone delle toolbar
- Icone delle notifiche
- Icone dei dialog
- Icone dei wizard
- Icone del Chatter
- Icone di Discuss
- Icone dei moduli custom
- Icone renderizzate tramite JavaScript
- Icone generate dinamicamente dai componenti OWL

Ogni icona deve essere verificata.

---

# Controlli da eseguire

Per ogni elemento individuato verifica:

- leggibilità;
- contrasto;
- visibilità;
- allineamento;
- dimensione;
- spaziatura;
- padding;
- margin;
- coerenza tipografica;
- coerenza con il Design System;
- comportamento in Hover;
- comportamento in Focus;
- comportamento in Active;
- comportamento in Disabled;
- adattamento alla modalità Dark;
- adattamento alla modalità Light.

Qualsiasi incongruenza deve essere corretta.

---

# Ciclo di Validazione

L'ispezione deve essere ripetuta più volte.

Dopo ogni ciclo di correzioni:

- riesplora l'interfaccia;
- verifica nuovamente tutti i moduli;
- verifica nuovamente tutte le viste;
- verifica nuovamente tutti i componenti dinamici;
- verifica nuovamente tutte le icone.

Il processo termina esclusivamente quando un'intera esplorazione dell'applicazione non produce più nuove anomalie visive o problemi di leggibilità.

La qualità finale deve essere paragonabile a quella di un prodotto enterprise rifinito manualmente da un team di UX/UI Design.

Se serve fai ispezione da web browser con le credenziali odoo 
user = vittorioaiello95@gmail.com
pass = NuovaPassword123!