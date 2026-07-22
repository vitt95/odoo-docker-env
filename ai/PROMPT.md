# Role

Agisci come un **Senior Frontend Engineer**, **Senior UX/UI Designer Enterprise** e **Design System Architect**, specializzato in:

- Enterprise UX
- Design Systems
- Dark Mode
- CSS Architecture
- Bootstrap
- Accessibilità (WCAG AA/AAA)
- Micro-interazioni premium
- Refactoring CSS non distruttivo

Il tuo obiettivo è correggere esclusivamente i problemi visivi descritti, mantenendo la piena compatibilità con il resto del CMR, senza introdurre regressioni.

---

# Regole Generali

Prima di modificare qualsiasi file:

1. Analizza completamente i componenti coinvolti.
2. Comprendi la gerarchia CSS esistente.
3. Individua eventuali CSS Variables già presenti e riutilizzale ove possibile.
4. Se necessario crea nuove variabili coerenti con il Design System.
5. Non introdurre colori casuali.
6. Mantieni la palette cromatica del CMR.
7. Mantieni uno stile enterprise, moderno, premium e minimale.
8. Evita CSS duplicato o ridondante.
9. Non rompere layout esistenti.
10. Non modificare la logica applicativa se non strettamente necessario.
11. Verifica ogni modifica sia in **Light Mode** che in **Dark Mode**.

Per ogni componente verifica sempre:

- Default
- Hover
- Active
- Focus
- Disabled
- Selected (quando presente)
- Responsive
- Accessibilità
- Contrasto WCAG

---

# 1. Fix `.btn-close`

La classe:

```css
.btn-close
```

in Dark Mode risulta poco visibile.

## Obiettivi

- Analizzare il motivo della scarsa visibilità.
- Correggere colori, opacity, filter o SVG se necessario.
- Garantire un contrasto elevato in entrambe le modalità.
- Mantenere coerenza con Bootstrap e con il Design System del CMR.
- Verificare anche:
  - hover
  - active
  - focus
- Il pulsante deve essere immediatamente riconoscibile senza risultare invasivo.

---

# 2. Restyling Activity Summary Table

Classe coinvolta:

```css
table.table.table-bordered.mb-5.bg-view.o_activity_view_table
```

Questa tabella deve essere completamente rifinita dal punto di vista UX/UI.

L'obiettivo è ottenere una tabella dal look enterprise, premium, moderna e molto più elegante.

## Analizza completamente

- struttura
- header
- tbody
- celle
- padding
- spacing
- border
- radius
- allineamenti
- background
- hover
- focus
- responsive

---

## Verifica tutte le celle dinamiche

Analizza tutti gli stati, inclusi:

```css
.o_activity_summary_cell

.o_activity_summary_cell.today

.o_activity_summary_cell.overdue

.o_activity_summary_cell.p-0.h-100
```

e qualsiasi altra variante presente nel codice.

Per ogni variante verifica:

- leggibilità
- contrasto
- colori
- riempimenti
- hover
- active
- focus

---

## Palette

I colori devono essere:

- coerenti con il CMR
- armoniosi
- poco saturi
- eleganti
- professionali
- gradevoli anche dopo molte ore di utilizzo

Particolare attenzione alla Dark Mode.

---

## Border

Le linee della tabella sono troppo pesanti.

Devono essere ripensate completamente.

Obiettivo:

- border molto più delicati
- separatori meno invasivi
- maggiore pulizia
- migliore gerarchia visiva
- aspetto premium

La tabella deve risultare moderna e leggera.

---

## Verificare inoltre

- badge
- icone
- numeri
- testi
- allineamenti verticali
- celle vuote
- celle piene
- overflow
- responsive

Ogni elemento deve risultare perfettamente leggibile sia in Light che in Dark Mode.

---

# 3. Tabella presente dentro `.o_action_manager`

Analizza completamente anche la tabella visualizzata sotto:

```css
.o_action_manager
```

## Verifica

- header
- tbody
- footer
- hover
- selected
- focus
- active
- contrasto
- leggibilità
- spaziature
- padding

Particolare attenzione alla Dark Mode.

Verifica che siano sempre perfettamente visibili:

- testo
- badge
- link
- icone
- pulsanti
- righe selezionate
- hover

---

## Border

Anche qui le linee della tabella devono essere meno invasive.

Devono risultare:

- leggere
- moderne
- eleganti
- coerenti con il resto del CMR

Lo stile deve essere coerente con quello adottato nella Activity Summary.

---

# 4. Sidebar (`.pui-sidebar`)

La sidebar deve essere completamente migliorata dal punto di vista UX.

---

## Hover Expand

Quando la sidebar è collapsed:

- passando il mouse deve espandersi automaticamente
- l'espansione deve essere estremamente fluida
- nessun flickering
- nessun layout shift
- nessun salto visivo

L'animazione deve risultare premium.

---

## Pin

Inserire una nuova icona nella parte superiore della sidebar.

### Stato normale

La sidebar:

- rimane collapsed
- in hover si espande
- uscendo con il mouse torna collapsed

---

### Stato Pinnato

Premendo il pin:

- la sidebar rimane sempre espansa
- il pin cambia stato visivamente
- la preferenza viene salvata (es. localStorage se coerente con l'architettura del progetto)
- la sidebar mantiene lo stesso livello qualitativo delle animazioni

---

### Unpin

Premendo nuovamente il pin:

- la sidebar torna collapsed
- riprende il comportamento Hover Expand

---

## Animazioni

Le animazioni devono essere curate nei minimi dettagli.

Requisiti:

- easing naturale
- transizioni morbide
- apertura elegante
- chiusura elegante
- nessun movimento brusco
- nessun flickering
- nessun layout shift
- comparsa progressiva delle label
- icone perfettamente stabili

L'interazione deve trasmettere la qualità di un software enterprise di fascia alta.

---

# Design Goal

L'interfaccia deve trasmettere la stessa qualità percepita dei migliori software enterprise moderni.

Prendi ispirazione (non copiare) dai principi UX/UI adottati da prodotti come:

- Linear
- Stripe Dashboard
- Vercel Dashboard
- Notion Enterprise
- Raycast
- Arc Browser

L'obiettivo è ottenere:

- maggiore pulizia
- migliore gerarchia visiva
- contrasto ottimizzato
- migliore leggibilità
- eleganza
- consistenza
- qualità percepita superiore

senza alterare l'identità visiva del CMR.

---

# Audit Finale Obbligatorio

Prima di terminare:

- verifica tutte le modifiche in Light Mode
- verifica tutte le modifiche in Dark Mode
- verifica responsive
- verifica hover
- verifica active
- verifica focus
- verifica accessibilità WCAG
- verifica contrasto
- verifica eventuali regressioni
- elimina CSS inutilizzato introdotto durante il refactoring
- assicurati che ogni modifica sia coerente con il Design System del CMR

Non limitarti a correggere i bug: esegui un audit UX/UI completo dei componenti coinvolti e, dove individui incoerenze visive, correggile mantenendo uno stile uniforme, moderno e premium.