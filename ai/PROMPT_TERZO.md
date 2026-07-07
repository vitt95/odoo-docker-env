# UI Polish & Visual QA (OBBLIGATORIO)

Questa fase rappresenta l'ultima iterazione del redesign.

L'obiettivo NON è implementare nuove funzionalità.

L'obiettivo è eliminare ogni imperfezione visiva e portare l'interfaccia ad un livello qualitativo premium.

---

# Bug Review

Prima di qualsiasi modifica leggi integralmente tutti i file presenti nella directory:

```text
.ai/bugs/
```

Tutti i bug descritti in tale cartella devono essere considerati prioritari.

Per ciascun bug:

- individua la causa reale;
- correggi il problema alla radice;
- evita workaround temporanei;
- verifica che la correzione non introduca regressioni;
- mantieni la coerenza con il Design System.

Se durante l'analisi individui ulteriori problemi non documentati nei file della cartella `.ai/bugs/`, correggili nella stessa iterazione.

---

# Design Reference

Continua ad utilizzare come riferimento principale le immagini presenti nella directory:

```text
.ai/ui-example/
```

Queste immagini rappresentano la specifica grafica ufficiale del progetto.

---

# Livello di fedeltà richiesto

Il redesign dovrà raggiungere una fedeltà visiva pari ad almeno:

**95% rispetto al Design System presente in `.ai/ui-example/`.**

La UI finale deve risultare immediatamente riconoscibile come appartenente allo stesso linguaggio visivo del riferimento.

Non limitarti ad una somiglianza generale.

Rivedi ogni dettaglio fino ad ottenere un'interfaccia che trasmetta la stessa qualità percepita del design di riferimento.

---

# Navbar

Rivedi completamente la Navbar superiore.

Analizza attentamente:

- spacing orizzontale;
- spacing verticale;
- padding;
- margini;
- allineamenti;
- altezza;
- distribuzione degli elementi;
- ricerca;
- pulsanti;
- avatar;
- breadcrumb;
- toolbar;
- icone;
- responsive behavior.

Ogni elemento dovrà essere perfettamente allineato.

Gli spazi dovranno essere armoniosi e costanti.

La Navbar dovrà trasmettere la stessa pulizia ed eleganza del riferimento grafico.

---

# Theme Review

Rivedi completamente il Theme Engine.

Entrambe le modalità devono essere rifinite:

- Light Mode
- Dark Mode

La qualità percepita deve essere equivalente in entrambe.

Non devono esistere componenti progettati meglio in una modalità rispetto all'altra.

---

# Dark Mode

La Dark Mode deve essere completamente rivista.

Non limitarti ad invertire i colori.

Progetta una vera interfaccia nativa per ambienti scuri.

Prendi come riferimento qualitativo il Design System di **Material UI 3 (MUI)** esclusivamente per quanto riguarda:

- qualità delle superfici;
- gestione dell'elevazione;
- profondità visiva;
- contrasti;
- accessibilità;
- leggibilità;
- comfort durante utilizzi prolungati.

**Non replicare Material UI dal punto di vista estetico.**

Il linguaggio visivo deve continuare ad essere quello definito dalle immagini presenti in:

```text
.ai/ui-example/
```

Material UI rappresenta esclusivamente un benchmark qualitativo per la progettazione della modalità scura.

La Dark Mode dovrà risultare:

- premium;
- elegante;
- esclusiva;
- moderna;
- professionale;
- raffinata;
- coerente;
- rilassante per la vista.

---

## Revisione completa Dark Mode

Verifica attentamente ogni componente:

- Sidebar
- Navbar
- Dashboard
- Control Panel
- Search
- Form
- List
- Kanban
- Calendar
- Dialog
- Notification
- Systray
- Chatter
- Discuss
- Dropdown
- Menu
- Tooltip
- Badge
- Tabs
- Inputs
- Buttons
- Cards
- Tables
- Breadcrumb

Controlla inoltre:

- contrasto dei testi;
- contrasto delle icone;
- superfici;
- layering;
- separazione tra componenti;
- hover;
- focus;
- active;
- disabled;
- ombre;
- bordi;
- overlay;
- modali.

Nessun elemento deve risultare:

- troppo scuro;
- troppo chiaro;
- poco leggibile;
- poco distinguibile;
- affaticante per la vista.

Ogni superficie deve essere chiaramente distinguibile dalle altre senza utilizzare contrasti aggressivi.

---

# Light Mode

Anche la modalità Light deve essere rifinita.

L'obiettivo è ottenere un'interfaccia:

- luminosa;
- ariosa;
- elegante;
- premium;
- professionale.

Rivedi attentamente:

- palette;
- superfici;
- tipografia;
- separatori;
- radius;
- ombre;
- spacing;
- gerarchia visiva;
- hover;
- focus;
- active.

Evita:

- bianchi troppo aggressivi;
- grigi privi di contrasto;
- ombre pesanti;
- elementi che sembrino appartenere a Design System differenti.

---

# Visual Consistency

Effettua una revisione completa dell'interfaccia.

Verifica che:

- tutti gli spacing siano coerenti;
- tutti i padding utilizzino la stessa scala;
- tutti i margini siano consistenti;
- tutti i radius appartengano allo stesso sistema;
- tutte le ombre seguano la stessa logica;
- tutti gli input abbiano la stessa altezza;
- tutti i pulsanti utilizzino la stessa gerarchia;
- tutte le toolbar abbiano la stessa struttura;
- tutte le icone abbiano dimensioni coerenti;
- tutta la tipografia utilizzi la stessa scala;
- tutta la UI utilizzi gli stessi Design Tokens.

L'interfaccia deve apparire come un unico prodotto progettato da un solo Design Team.

---

# Responsive Review

Riesegui una revisione completa della responsività.

Verifica:

- Desktop
- Laptop
- Tablet
- Mobile

Controlla:

- overflow;
- wrapping;
- allineamenti;
- sidebar;
- navbar;
- toolbar;
- dialog;
- dashboard;
- kanban;
- list;
- form;
- control panel.

Ogni breakpoint deve mantenere la stessa qualità grafica.

---

# Qualità finale

Prima di considerare conclusa l'implementazione esegui una revisione completa dell'interfaccia.

Agisci come un Senior Product Designer incaricato della release finale di un software enterprise.

Non interrompere il lavoro quando tutti i bug risultano risolti.

Continua a rifinire l'interfaccia fino a quando:

- ogni schermata risulti premium;
- ogni dettaglio grafico sia coerente;
- ogni spacing sia armonioso;
- ogni tema sia perfettamente leggibile;
- ogni componente sembri appartenere allo stesso Design System;
- la qualità percepita raggiunga un livello comparabile ai migliori software SaaS moderni.

---

# Output

Prima di modificare qualsiasi file restituisci esclusivamente:

1. Analisi dei bug presenti in `.ai/bugs/`
2. Eventuali bug aggiuntivi individuati
3. Strategia di correzione
4. Componenti che verranno rifiniti
5. Piano di miglioramento della Dark Mode
6. Piano di miglioramento della Light Mode
7. Piano di revisione della Navbar
8. Piano di miglioramento della responsività
9. Stima del livello di fedeltà finale rispetto alle immagini presenti in `.ai/ui-example/`

Attendi il mio via libera prima di modificare qualsiasi file.