# Task — Complete Navigation Path & Control Header Redesign (Light & Dark)

## Obiettivo

Riprogettare completamente la Navigation Path (Breadcrumb), il View Header e il Control Panel affinché risultino visivamente indistinguibili dal Design System mostrato nelle immagini di riferimento.

Le immagini presenti in:

```text
.ai/ui-example/light/path-navbar.png
.ai/ui-example/dark/path-navbar.png
```

costituiscono la **specifica progettuale ufficiale**.

Non rappresentano una semplice ispirazione grafica.

Devono essere replicate con una fedeltà visiva del **95–100%**, compatibilmente con i vincoli architetturali di Odoo.

---

# Ambito della modifica

La modifica riguarda l'intera area superiore di ogni vista.

Comprende:

- Navigation Path (Breadcrumb)
- View Header
- Control Panel
- Toolbar
- Search
- Search Panel
- Filters
- Group By
- Favorites
- Pagination
- View Switcher
- Smart Buttons
- Action Buttons
- Context Buttons
- Header Buttons
- Qualsiasi altro componente appartenente al Control Header

L'obiettivo è sostituire completamente il layout standard di Odoo con quello definito dal Design System presente in:

```text
.ai/ui-example/
```

---

# Analisi preventiva (OBBLIGATORIA)

Prima di implementare qualsiasi modifica:

Analizza attentamente tutte le immagini presenti nelle directory:

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

Ricostruisci il comportamento del Control Header individuando:

- struttura
- gerarchia
- spacing
- griglia
- allineamenti
- tipografia
- colori
- elevazione
- componenti
- interazioni
- responsive

Successivamente individua tutti i componenti Odoo coinvolti nella renderizzazione del breadcrumb e del control panel.

Analizza almeno:

- componenti OWL
- Template QWeb
- XML
- Controller
- Renderer
- Services
- Registries
- Hooks
- Asset Bundle
- SCSS

Individua inoltre:

- dipendenze
- punti di override
- punti di patch
- template inheritance
- eventuali limitazioni architetturali

---

# Nuova Architettura

La parte superiore della pagina deve essere organizzata su due livelli.

---

## Prima riga

La prima riga contiene esclusivamente il percorso di navigazione.

Esempio:

```
CRM
>
Vendite
>
Pipeline
```

oppure

```
Vendite
>
Ordini
>
SO00034
```

Caratteristiche:

- estremamente compatta
- tipografia ridotta
- peso semibold
- colore secondario
- altezza minima
- perfettamente allineata alla griglia principale
- separatori tramite icona ">"
- nessun elemento superfluo

Il breadcrumb deve avere un'importanza visiva inferiore rispetto al titolo della pagina.

---

## Seconda riga

La seconda riga rappresenta il vero Header della vista.

Comprende:

- titolo della vista
- pulsanti principali
- smart buttons
- action buttons
- search
- filtri
- group by
- view switcher
- toolbar
- controlli

La disposizione deve replicare fedelmente il riferimento presente nelle immagini.

---

# Gerarchia Visiva

Replica fedelmente il Design System.

Il titolo della vista deve essere il punto focale.

Il breadcrumb deve risultare discreto.

Toolbar e controlli devono avere un peso visivo coerente con il riferimento.

---

# Layout

Replica:

- spacing
- margini
- padding
- griglia
- proporzioni
- distribuzione degli spazi
- ritmo verticale
- ritmo orizzontale

Ogni elemento deve risultare perfettamente allineato.

---

# Tipografia

Replica:

- font family
- fallback
- font size
- font weight
- line-height
- letter spacing
- gerarchia

L'intera Navigation Path deve utilizzare il sistema tipografico del Design System.

---

# Componenti

Verifica e uniforma ogni componente presente nel Control Header.

Compresi:

## Pulsanti

- Primary
- Secondary
- Ghost
- Outline
- Toolbar
- Icon Buttons
- Dropdown Buttons
- Smart Buttons
- Action Buttons

Verifica:

- dimensioni
- radius
- padding
- colori
- border
- hover
- active
- disabled
- focus

---

## Search

Replica completamente:

- Search Input
- Search Panel
- Placeholder
- Search Icon
- Focus
- Hover
- Border
- Background
- Radius

---

## Dropdown

Replica:

- background
- shadow
- spacing
- tipografia
- hover
- selected
- active

---

## Toolbar

Replica:

- spacing
- dimensioni
- allineamenti
- icone
- separazioni
- responsive

---

# Responsive

La nuova struttura deve essere completamente responsive.

Desktop

- breadcrumb completo
- toolbar completa

Tablet

- toolbar adattiva
- breadcrumb compatto

Mobile

- breadcrumb collassabile
- titolo prioritario
- toolbar ridistribuita

Non limitarti a comprimere il layout desktop.

---

# Theme Engine

La stessa architettura deve essere implementata contemporaneamente per:

- Light Mode
- Dark Mode

Utilizzando esclusivamente come riferimento:

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

Le due modalità devono condividere:

- identico layout
- identica gerarchia
- identico spacing
- identica composizione
- identico responsive

Devono differire esclusivamente per:

- palette
- superfici
- contrasti
- ombre
- bordi
- colori semantici

---

# Design Tokens

È obbligatorio utilizzare esclusivamente il Theme Engine.

È vietato utilizzare:

- colori hardcoded
- valori differenti tra Light e Dark
- CSS duplicato

Ogni componente deve utilizzare Design Tokens.

---

# Compatibilità

È severamente vietato modificare direttamente il core di Odoo.

Qualsiasi modifica deve essere realizzata esclusivamente attraverso:

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

Per ogni componente:

1. Analizza il riferimento.
2. Analizza il componente Odoo.
3. Individua le differenze.
4. Implementa la modifica.
5. Confronta il risultato con le immagini in `.ai/ui-example/`.
6. Correggi le discrepanze.
7. Ripeti fino a raggiungere la massima fedeltà possibile.

Non interrompere il processo al primo risultato soddisfacente.

---

# Criteri di Accettazione

La Navigation Path e il Control Header saranno considerati completati soltanto quando:

- il layout replica fedelmente il riferimento;
- il breadcrumb risulta compatto e discreto;
- il titolo della vista è il punto focale;
- toolbar e controlli sono perfettamente allineati;
- pulsanti, dropdown e search rispettano il Design System;
- Light e Dark condividono la stessa architettura;
- tutte le differenze sono esclusivamente cromatiche;
- il componente è completamente responsive;
- vengono utilizzati esclusivamente Design Tokens;
- nessun elemento conserva lo stile originale di Odoo;
- non sono state apportate modifiche al core.

---

# Definizione di "Completato"

Il lavoro può considerarsi completato esclusivamente quando un utente esperto di Odoo, osservando la parte superiore della pagina, **non è più in grado di riconoscere il Control Panel standard della piattaforma**.

La Navigation Path, il View Header e il Control Panel devono apparire come componenti nativi del Design System definito nelle immagini presenti in:

```text
.ai/ui-example/light/
.ai/ui-example/dark/
```

con una fedeltà visiva stimata tra il **95% e il 100%**.