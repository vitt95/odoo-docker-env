# Final Visual QA & Dark Mode Completion (OBBLIGATORIO)

Questa rappresenta la fase finale del redesign.

L'obiettivo NON è introdurre nuove funzionalità.

L'obiettivo è consegnare una UI pronta per la produzione, eliminando qualsiasi bug grafico, problema di leggibilità o incoerenza tra Light e Dark Mode.

---

# Bug Review

Prima di qualsiasi modifica leggi integralmente tutti i file presenti nella directory:

```text
.ai/bugs/
```

Tutti i bug presenti devono essere risolti.

Per ciascun bug:

- individua la causa reale;
- correggi il problema alla radice;
- evita workaround;
- verifica che la correzione non introduca regressioni;
- verifica il comportamento sia in Light Mode che in Dark Mode.

Non limitarti esclusivamente ai bug documentati.

Durante l'analisi esegui una revisione completa dell'interfaccia e correggi anche eventuali anomalie non ancora segnalate.

---

# Dark Mode Completion

La Dark Mode deve essere considerata **incompleta** finché anche un solo componente mantiene elementi appartenenti alla modalità Light.

L'intera applicazione deve essere completamente compatibile con la Dark Mode.

Non devono esistere:

- sfondi chiari non intenzionali;
- componenti con colori della Light Mode;
- pannelli bianchi;
- popup bianchi;
- dialog chiari;
- menu contestuali chiari;
- dropdown chiari;
- tooltip chiari;
- modali chiare;
- input con sfondi errati;
- card con colori incoerenti;
- bordi troppo chiari;
- icone poco visibili;
- placeholder illeggibili;
- badge con contrasto insufficiente;
- scrollbar incoerenti;
- elementi HTML nativi che mantengano il tema Light.

Ogni superficie deve appartenere al Design System Dark.

---

# Leggibilità

Verifica accuratamente tutti i testi presenti nell'applicazione.

Ogni font deve essere chiaramente leggibile.

Controlla:

- colore del testo principale;
- testo secondario;
- testo disabilitato;
- placeholder;
- label;
- helper text;
- breadcrumb;
- menu;
- dropdown;
- notifiche;
- tooltip;
- dialog;
- tab;
- badge;
- pulsanti;
- tabelle;
- form;
- kanban;
- chatter;
- sidebar;
- navbar.

Scegli colori che garantiscano:

- elevata leggibilità;
- ottimo contrasto;
- nessun affaticamento visivo;
- esperienza premium.

---

# Visual Verification

Non limitarti a correggere il codice.

Verifica visivamente ogni schermata.

Ogni componente deve essere controllato sia in:

- Light Mode
- Dark Mode

La verifica deve comprendere almeno:

- Login
- Dashboard
- Navbar
- Sidebar
- Search
- Control Panel
- Form View
- List View
- Kanban
- Calendar
- Dialog
- Notification
- Discuss
- Chatter
- Systray
- Dropdown
- Menu
- Tooltip
- Modali
- Settings

---

# Layout Verification

Correggi qualsiasi problema relativo a:

- sovrapposizione di testo;
- overflow;
- wrapping errato;
- testo tagliato;
- componenti che escono dai contenitori;
- icone disallineate;
- pulsanti deformati;
- padding incoerenti;
- margini incoerenti;
- elementi fuori griglia;
- scrollbar indesiderate;
- elementi sovrapposti.

L'interfaccia deve risultare pulita in ogni schermata.

---

# Theme Consistency

Entrambe le modalità devono utilizzare lo stesso Design System.

Light e Dark devono differire esclusivamente per il tema cromatico.

La gerarchia visiva deve rimanere identica.

Ogni componente deve avere una versione Dark progettata intenzionalmente.

Non è accettabile una semplice inversione dei colori.

---

# Premium Quality

Prendi come riferimento qualitativo Material UI 3 esclusivamente per:

- qualità delle superfici;
- contrasto;
- elevazione;
- profondità;
- leggibilità;
- accessibilità;
- comfort visivo.

Non copiarne lo stile.

Continua ad utilizzare come riferimento grafico principale il Design System presente nella directory:

```text
.ai/ui-example/
```

---

# Color Palette Review

Esegui una revisione completa dell'intera palette cromatica dell'applicazione.

L'obiettivo non è semplicemente scegliere colori esteticamente piacevoli.

La palette deve trasmettere una sensazione di:

- prodotto enterprise;
- qualità premium;
- eleganza;
- esclusività;
- equilibrio;
- modernità.

L'interazione con l'interfaccia deve risultare naturale, rilassante e visivamente soddisfacente anche durante utilizzi prolungati.

---

## Principi

La palette deve essere:

- armoniosa;
- ben bilanciata;
- coerente;
- poco aggressiva;
- raffinata;
- facilmente leggibile;
- professionale.

Evita colori:

- eccessivamente saturi;
- troppo brillanti;
- troppo freddi;
- troppo contrastati;
- troppo scuri;
- troppo vicini tra loro;
- che generino affaticamento visivo.

Ogni colore deve avere uno scopo preciso all'interno del Design System.

---

## Revisione dei Design Tokens

Verifica e ricalibra tutti i token cromatici.

In particolare:

- Primary
- Secondary
- Accent
- Background
- Surface
- Surface Variant
- Border
- Divider
- Text Primary
- Text Secondary
- Text Disabled
- Icon Primary
- Icon Secondary
- Hover
- Active
- Selected
- Focus
- Success
- Warning
- Error
- Info
- Overlay
- Shadow

La relazione tra questi colori deve risultare coerente in tutta l'applicazione.

---

## Light Mode

La modalità Light deve risultare:

- luminosa;
- pulita;
- elegante;
- ariosa;
- rilassante.

Evita bianchi assoluti (#FFFFFF) utilizzati in modo eccessivo quando superfici leggermente attenuate migliorano la qualità percepita.

Le superfici devono avere profondità senza dipendere esclusivamente dalle ombre.

---

## Dark Mode

La modalità Dark deve essere progettata per lunghe sessioni di utilizzo.

Evita:

- neri assoluti;
- contrasti estremi;
- superfici indistinguibili;
- testi troppo luminosi;
- colori che affaticano la vista.

Utilizza una gerarchia di superfici che renda immediatamente riconoscibili i diversi livelli dell'interfaccia.

Il contrasto deve risultare elevato ma naturale.

---

## Esperienza Visiva

L'interfaccia deve dare la sensazione di utilizzare un software premium.

Ogni schermata deve risultare:

- equilibrata;
- coerente;
- piacevole da osservare;
- intuitiva;
- estremamente soddisfacente durante l'interazione.

L'utente deve percepire immediatamente ordine, qualità e cura del dettaglio.

La palette cromatica deve accompagnare l'esperienza, senza mai diventare protagonista o creare distrazioni.

---

## Qualità finale

Prima di considerare conclusa l'implementazione verifica che:

- nessun colore risulti casuale;
- ogni tonalità appartenga allo stesso Design System;
- la palette sia coerente tra Light e Dark Mode;
- ogni componente utilizzi esclusivamente i Design Tokens;
- l'interfaccia trasmetta una sensazione di prodotto enterprise moderno, premium ed esclusivo.

La qualità cromatica complessiva deve essere comparabile a quella dei migliori software SaaS professionali.

# Responsive Verification

Ripeti tutti i controlli anche su:

- Desktop
- Laptop
- Tablet
- Mobile

Verifica che:

- non esistano sovrapposizioni;
- nessun testo venga tagliato;
- nessun componente esca dal viewport;
- navbar e sidebar siano sempre corrette;
- dialog e dropdown siano perfettamente leggibili.

---

# Obiettivo finale

Considera il lavoro concluso **solo quando**:

- tutti i bug presenti in `.ai/bugs/` sono stati risolti;
- tutti i componenti supportano completamente la Dark Mode;
- non esiste alcun elemento della Light Mode visibile nella Dark Mode;
- tutti i testi risultano leggibili e con contrasto adeguato;
- non esistono sovrapposizioni o problemi di layout;
- entrambe le modalità risultano coerenti, eleganti e premium;
- l'interfaccia raggiunge una fedeltà visiva di almeno **95%** rispetto alle immagini presenti in `.ai/ui-example/`.

---

# Output

Prima di modificare qualsiasi file restituisci esclusivamente:

1. Elenco dei bug trovati nella cartella `.ai/bugs/`.
2. Eventuali bug aggiuntivi individuati durante la revisione.
3. Componenti ancora non pienamente compatibili con la Dark Mode.
4. Piano di correzione.
5. Piano di verifica finale della Light Mode e della Dark Mode.

Attendi il mio via libera prima di modificare qualsiasi file.