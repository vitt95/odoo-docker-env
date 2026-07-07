# Phase 5 — Dark Mode Completion & UI Consistency Audit (OBBLIGATORIO)

Questa rappresenta la quinta ed ultima fase del redesign.

L'obiettivo NON è introdurre nuove funzionalità.

L'obiettivo è completare definitivamente l'integrazione della Dark Mode ed eliminare qualsiasi incoerenza grafica residua.

La Dark Mode deve essere considerata una funzionalità completamente supportata dall'intera applicazione.

---

# Bug Review

Prima di qualsiasi modifica leggi integralmente tutti i file presenti nella directory:

```text
.ai/bugs/
```

Tutti i bug presenti devono essere risolti.

Non limitarti esclusivamente ai bug documentati.

Durante l'analisi individua autonomamente ulteriori problemi grafici, di layout o di leggibilità e correggili nella stessa iterazione.

---

# Full UI Audit

Esegui una revisione completa di tutti i componenti dell'interfaccia.

Non limitarti alle schermate principali.

Analizza qualsiasi componente presente nell'applicazione.

Compresi:

- Login
- Dashboard
- Navbar
- Sidebar
- Search
- Global Search
- Control Panel
- Breadcrumb
- Menu
- Dropdown
- Context Menu
- Toolbar
- Form View
- List View
- Kanban
- Calendar
- Pivot
- Graph
- Activity
- Chatter
- Discuss
- Notification
- Toast
- Dialog
- Modal
- Tooltip
- Popover
- Tabs
- Accordion
- Cards
- Buttons
- Button Groups
- Inputs
- Select
- Multi Select
- Checkbox
- Radio
- Switch
- Textarea
- Date Picker
- Time Picker
- Badges
- Chips
- Avatars
- Tables
- Pagination
- Statusbar
- Progress Bar
- Upload
- Attachment Viewer
- File Preview
- Systray
- User Menu
- Settings
- Developer Tools
- Owl Components
- Custom Components
- QWeb Templates

Ogni componente deve essere verificato singolarmente.

---

# Dark Mode Integration

Ogni componente deve possedere una versione Dark Mode progettata intenzionalmente.

Non devono più esistere componenti che utilizzano colori della Light Mode.

Sono vietati:

- sfondi bianchi;
- pannelli chiari;
- popup chiari;
- modali chiare;
- dropdown chiari;
- tooltip chiari;
- input chiari;
- card chiare;
- placeholder poco leggibili;
- bordi incoerenti;
- icone poco visibili;
- badge errati;
- elementi HTML nativi non tematizzati.

Qualsiasi elemento dell'interfaccia deve rispettare il Design System Dark.

---

# Complete Theme Consistency

L'interfaccia deve risultare completamente coerente.

Verifica che tutti i componenti utilizzino esclusivamente i Design Tokens.

Non devono esistere:

- colori hardcoded;
- componenti con palette differenti;
- radius differenti;
- ombre differenti;
- spacing differenti;
- tipografia differente;
- pulsanti appartenenti a sistemi grafici differenti.

L'intera applicazione deve sembrare progettata come un unico prodotto.

---

# Color Palette Audit

Rivedi completamente la palette cromatica.

La palette deve risultare:

- premium;
- elegante;
- moderna;
- rilassante;
- raffinata;
- professionale.

L'interazione con l'interfaccia non deve mai risultare aggressiva.

Evita:

- contrasti estremi;
- colori troppo saturi;
- superfici indistinguibili;
- testi poco leggibili.

La palette deve essere perfettamente bilanciata sia in Light Mode sia in Dark Mode.

---

# Typography Audit

Controlla tutti i testi presenti nell'applicazione.

Verifica:

- contrasto;
- leggibilità;
- dimensioni;
- peso;
- line-height;
- spaziatura.

Ogni testo deve risultare immediatamente leggibile.

---

# Layout Audit

Analizza completamente il layout.

Correggi qualsiasi problema relativo a:

- sovrapposizioni;
- overflow;
- wrapping;
- elementi fuori contenitore;
- scrollbar indesiderate;
- testi tagliati;
- colonne disallineate;
- card deformate;
- toolbar incoerenti;
- navbar;
- sidebar.

---

# Component Consistency

Ogni componente deve essere verificato in tutti gli stati.

Compresi:

- default;
- hover;
- active;
- focus;
- disabled;
- loading;
- selected;
- expanded;
- collapsed;
- error;
- warning;
- success.

Tutti gli stati devono essere coerenti con il Design System.

---

# Responsive Audit

Ripeti tutti i controlli su:

- Desktop
- Laptop
- Tablet
- Mobile

La qualità grafica deve rimanere identica su ogni dispositivo.

---

# Design Reference

Continua ad utilizzare come riferimento principale le immagini presenti nella directory:

```text
.ai/ui-example/
```

L'obiettivo finale rimane una fedeltà visiva pari ad almeno il **95%** rispetto al Design System di riferimento.

---

# Quality Gate

Il lavoro NON può essere considerato concluso finché non vengono soddisfatte tutte le condizioni seguenti:

- tutti i bug presenti nella cartella `.ai/bugs/` sono stati risolti;
- tutti i componenti supportano completamente la Dark Mode;
- non esiste alcun elemento della Light Mode visibile nella Dark Mode;
- tutti i testi risultano leggibili;
- tutti gli stati dei componenti sono coerenti;
- non esistono sovrapposizioni;
- non esistono overflow;
- non esistono componenti non tematizzati;
- tutta la UI utilizza esclusivamente il Theme Engine;
- la palette cromatica è coerente, equilibrata e non affatica la vista;
- la UI trasmette la qualità di un prodotto enterprise premium.

---

# Bug segnalati
1. Spesso nei menu c'è scarsa visibilità delle voci
2. Ci sono alcuni componentu UI che rimangono light e non sono integrati nella dark mode
3. la dashboard iniziale è fatta male, se gli applicativi vanno in overflow non si può scrollare, voglio mostrarli come una griglia devo poterli vedere tutti.
4. I bordi dei form e delle timeline voglio che vengano eliminati, deve essere come i form della light mode
5. Controlla poi eventuali bug visivi che disturbano la UI/UX fai dei check e risolvi nel caso.

# Output

Prima di modificare qualsiasi file restituisci esclusivamente:

1. Elenco dei bug presenti nella cartella `.ai/bugs/`.
2. Componenti ancora non completamente compatibili con la Dark Mode.
3. Componenti non ancora conformi al Design System.
4. Piano di integrazione della Dark Mode.
5. Piano di revisione della palette cromatica.
6. Piano di verifica finale di tutti i componenti UI.