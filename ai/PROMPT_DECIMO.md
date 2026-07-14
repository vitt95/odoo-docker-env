# Step 12 — Complete Visual QA, UX Audit & Bug Resolution (OBBLIGATORIO)

## Obiettivo

Questa rappresenta la fase finale del progetto.

Non devono essere introdotte nuove funzionalità.

L'obiettivo è ottenere un'interfaccia di qualità enterprise, completamente rifinita, coerente, leggibile e perfettamente allineata al Design System definito nelle immagini presenti in:

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

Il lavoro termina esclusivamente quando ogni schermata dell'applicazione risulta visivamente coerente, priva di bug grafici e conforme al Design System.

---

# Bug Fix (OBBLIGATORIO)

Prima di qualsiasi altra attività analizza ricorsivamente tutti i file presenti nella directory:

```text
.ai/bugs/
```

Ogni bug documentato rappresenta un requisito progettuale.

Per ciascun bug:

- individua il componente coinvolto;
- individua la causa;
- individua le dipendenze;
- implementa la correzione;
- verifica che la correzione non introduca regressioni.

Nessun bug presente nella cartella `.ai/bugs/` può essere ignorato.

---

# Navigazione completa dell'applicazione

Esplora sistematicamente l'intera applicazione.

Per ogni modulo individua automaticamente tutte le viste disponibili.

Ad esempio:

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
- Wizard
- Dialog
- Search View
- Report View

Per ogni vista individua le viste figlie, le finestre modali, i dialog, i menu contestuali e qualsiasi elemento raggiungibile tramite l'interfaccia.

L'obiettivo è ottenere la copertura completa dell'intera UI.

---

# Ispezione automatica

Se l'ambiente di sviluppo mette a disposizione strumenti di browser automation (ad esempio Playwright, Puppeteer o equivalenti), utilizzali per:

- aprire ogni modulo;
- navigare tutte le viste;
- ispezionare le schermate;
- acquisire screenshot di verifica;
- confrontare il risultato con il Design System;
- individuare anomalie visive.

Se tali strumenti non sono disponibili, esegui comunque un'ispezione sistematica del codice e dei componenti coinvolti.

---

# Visual QA

Per ogni schermata verifica attentamente:

## Layout

- allineamenti
- griglia
- padding
- margin
- spacing verticale
- spacing orizzontale
- ritmo visivo
- distribuzione degli spazi
- densità delle informazioni

---

## Tipografia

Verifica:

- font family
- fallback
- font weight
- font size
- line-height
- letter spacing
- gerarchia
- leggibilità
- contrasto

Nessun testo deve risultare difficile da leggere.

---

## Pulsanti

Controlla tutti i pulsanti.

Verifica:

- dimensioni
- padding
- radius
- border
- contrasto
- icone
- allineamenti
- hover
- active
- focus
- disabled
- loading

Ogni pulsante deve appartenere chiaramente al Design System.

---

## Campi di Input

Verifica ogni campo.

Compresi:

- Input
- Textarea
- Select
- Search
- Date Picker
- Time Picker
- Many2One
- Many2Many
- Tags

Controlla:

- placeholder
- contrasto del placeholder
- colore del testo
- leggibilità
- background
- focus
- hover
- active
- disabled
- padding
- altezza
- radius

Il placeholder deve essere sempre leggibile ma distinguibile dal valore inserito.

---

## Hover States

Analizza tutti gli stati interattivi.

Compresi:

- hover
- active
- focus
- selected
- disabled
- loading
- expanded
- collapsed

Ogni stato deve risultare coerente con il Design System.

---

## Menu

Verifica:

- Sidebar
- Navbar
- Dropdown
- Context Menu
- Breadcrumb
- Systray
- Search Panel

Controlla:

- spacing
- leggibilità
- hover
- active
- selected
- contrasto
- allineamenti

---

## Tabelle

Verifica:

- header
- righe
- celle
- hover
- sorting
- selection
- footer
- toolbar

---

## Kanban

Controlla:

- card
- header
- footer
- badge
- avatar
- pulsanti
- spacing
- ombre
- elevazione

---

## Dialog

Verifica:

- Dialog
- Modal
- Wizard
- Confirmation
- Popover
- Tooltip

---

## Notification

Controlla:

- Toast
- Banner
- Alert
- Success
- Error
- Warning
- Empty State
- Loading
- Skeleton

---

# Spacing Audit

Ogni componente deve rispettare una scala di spacing coerente.

Verifica:

- padding interni
- margini esterni
- distanza tra componenti
- distanza tra titolo e contenuto
- distanza tra icone e testo
- distanza tra pulsanti
- distanza tra gruppi di controlli

Qualsiasi incoerenza deve essere corretta.

---

# Alignment Audit

Verifica:

- allineamento orizzontale
- allineamento verticale
- baseline tipografica
- allineamento delle icone
- allineamento dei pulsanti
- allineamento dei campi input
- allineamento delle card

L'intera UI deve apparire perfettamente allineata.

---

# Visual Consistency

Nessun componente deve apparire appartenente ad un Design System differente.

Qualsiasi differenza relativa a:

- colori
- radius
- ombre
- font
- spacing
- elevazione
- dimensioni
- bordi

deve essere eliminata.

---

# Light & Dark

Ogni correzione deve essere implementata contemporaneamente in:

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

Le due modalità devono condividere:

- identico layout
- identica architettura
- identico spacing
- identica tipografia
- identico responsive

Le differenze devono essere esclusivamente cromatiche.

---

# Core Compatibility

È severamente vietato modificare direttamente il core di Odoo.

Utilizza esclusivamente:

- OWL Patch
- Template Inheritance
- XML Inheritance
- Registries
- Services
- Hooks
- Asset Bundle
- SCSS
- CSS Variables
- Moduli custom

---

# Processo Iterativo (OBBLIGATORIO)

Il lavoro NON termina dopo la prima revisione.

Dopo ogni ciclo di correzioni:

1. riesegui l'ispezione completa;
2. verifica tutte le viste;
3. verifica tutti i moduli;
4. verifica tutti gli stati interattivi;
5. verifica entrambe le modalità (Light e Dark);
6. verifica che i bug della cartella `.ai/bugs/` siano risolti;
7. individua eventuali nuove incongruenze;
8. correggile.

Ripeti il processo fino a quando non vengono più rilevate anomalie visive significative.

---

# Definizione di "Completato"

Il lavoro può considerarsi concluso esclusivamente quando:

- tutti i bug presenti in `.ai/bugs/` sono stati risolti;
- tutte le viste di tutti i moduli sono state ispezionate;
- tutti i componenti rispettano il Design System;
- tutti gli hover risultano coerenti;
- tutti i placeholder sono leggibili;
- tutti i testi hanno il corretto contrasto;
- tutti gli spazi risultano uniformi;
- tutti gli allineamenti risultano perfetti;
- non esistono componenti con stile standard di Odoo;
- Light e Dark risultano completamente coerenti;
- non sono presenti regressioni funzionali.

L'interfaccia deve raggiungere un livello qualitativo tale da risultare uniforme, rifinita e pronta per una distribuzione in produzione.

le credenziali di accesso ad odoo via web sono 
user: "vittorioaiello95@gmail.com"
pass: "NuovaPassword123!"
