## 5. Icone nei Modal (`.modal-header` e azioni)

Analizza tutte le icone presenti all'interno dei modal, con particolare attenzione alla **Dark Mode**.

Componenti coinvolti:

```css
.modal-header
```

e tutte le icone di azione presenti nei modal, ad esempio:

```html
<i class="fa d-print-none fa-trash-o"></i>
```

e qualsiasi altra icona Font Awesome (o libreria equivalente) utilizzata per:

- chiusura
- eliminazione
- modifica
- stampa
- download
- upload
- conferma
- annullamento
- navigazione
- utility
- azioni secondarie

### Obiettivi

Esegui un audit completo della visibilità delle icone.

Per ogni icona verifica:

- contrasto
- colore
- opacità
- hover
- active
- focus
- disabled
- stato selezionato (se presente)

In particolare in **Dark Mode** nessuna icona deve risultare:

- sbiadita
- poco contrastata
- grigia su sfondo grigio
- difficile da individuare
- poco leggibile

Le icone devono essere immediatamente riconoscibili senza risultare eccessivamente luminose o invasive.

Mantieni uno stile coerente con il resto del Design System del CMR.

Se necessario, differenzia i colori delle icone in base alla loro funzione (es. destructive, warning, primary, secondary), mantenendo una palette elegante e armonizzata.

---

## Verifica direttamente la UI

Non limitarti all'analisi del codice.

Dopo aver implementato le modifiche, **accedi personalmente al CRM in ambiente locale** utilizzando le credenziali che ti fornirò.

Durante la verifica dovrai:

- navigare le principali schermate del CRM;
- aprire tutti i modal rilevanti;
- verificare il comportamento sia in **Light Mode** che in **Dark Mode**;
- individuare eventuali problemi visivi non evidenti dal solo codice;
- correggere ogni problema di contrasto, leggibilità o consistenza grafica che riscontri.

L'obiettivo è effettuare una **verifica reale dell'interfaccia**, non limitarsi a modificare il CSS sulla base di supposizioni. Se durante l'ispezione individui ulteriori incoerenze visive strettamente correlate ai componenti analizzati, correggile mantenendo piena coerenza con il Design System del CMR e senza introdurre regressioni.

## 6. Uniformare gli Hover delle Quick Actions (Light Mode)

Verifica il comportamento delle quick actions che utilizzano icone Font Awesome, con particolare attenzione alla **Light Mode**.

Attualmente l'azione con icona:

```html
<i class="fa fa-lg fa-comments"></i>
```

presenta un effetto hover corretto e gradevole.

Al contrario, l'azione relativa al tempo:

```html
<i class="fa fa-lg fa-clock-o"></i>
```

(e il relativo contenitore/div) **non replica lo stesso comportamento**, generando un'incoerenza visiva.

### Obiettivo

Uniformare completamente il comportamento delle due azioni.

L'elemento che contiene:

```html
<i class="fa fa-lg fa-clock-o"></i>
```

deve avere **esattamente lo stesso comportamento UX/UI** dell'elemento che contiene:

```html
<i class="fa fa-lg fa-comments"></i>
```

### Verificare

- background in hover
- colore dell'icona
- colore del testo
- border
- transizioni
- easing
- durata dell'animazione
- area cliccabile
- padding
- border-radius
- stati active
- stati focus
- feedback visivo

L'interazione deve risultare perfettamente coerente tra le due azioni.

L'utente non deve percepire alcuna differenza nel comportamento tra **Comments** e **Clock**: entrambe devono seguire le stesse regole del Design System.

Se durante l'analisi emergono altre quick actions con hover incoerenti rispetto al comportamento standard adottato dal CMR, correggile per uniformare l'intera esperienza utente, mantenendo piena coerenza con il Design System esistente e senza introdurre regressioni.


Credenziali di acceso sono:
user : vittorioaiello95@gmail.com
pass : NuovaPassword123!