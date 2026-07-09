# Visual Fix Mission – Record Detail Views

È rimasta una fase finale di rifinitura delle **viste di dettaglio dei record**.

All'interno della cartella **`bugs/`** trovi alcuni screenshot che rappresentano problemi reali dell'interfaccia.

Non limitarti a correggere solo quei punti: usali come riferimento per individuare e correggere lo stesso tipo di problema in **tutte le altre viste di dettaglio dell'applicazione**.

## Screenshot da analizzare

### `bugs-details`

Analizza attentamente tutti i bug evidenziati.

* Le aree **cerchiate in verde** devono essere integrate correttamente nella Dark Mode.

  * colori coerenti
  * sfondi corretti
  * bordi coerenti
  * contrasto adeguato
  * nessun elemento rimasto con stile Light

* Le aree **cerchiate in rosso** devono essere rese molto più leggibili e visivamente evidenti.
  Valuta autonomamente come migliorarle intervenendo su:

  * gerarchia visiva
  * contrasto
  * tipografia
  * spaziature
  * sfondo
  * separatori
  * bordi
  * dimensioni
  * allineamenti

L'obiettivo è che tali sezioni siano immediatamente individuabili senza rompere l'equilibrio grafico dell'interfaccia.

---

### `hover-li.png`

Correggi il problema dell'hover.

Attualmente la voce diventa poco visibile o invisibile.

Controlla:

* colore del testo
* colore dello sfondo
* contrasto
* stato hover
* stato active
* stato selected
* focus
* dark mode
* light mode (se presente)

L'hover deve risultare immediatamente leggibile.

---

### `sovrapposizione.png`

Individua la causa della sovrapposizione.

Verifica:

* z-index
* overflow
* stacking context
* position absolute/fixed/sticky
* flex
* grid
* responsive
* padding
* margin

Correggi definitivamente il problema evitando regressioni.

---

# Estendi il controllo a TUTTE le Detail View

Non limitarti alle schermate presenti negli screenshot.

Dopo aver corretto quei bug, esegui un audit completo di **tutte le viste di dettaglio dei record** dell'applicazione.

Ad esempio:

* dettaglio Cliente
* dettaglio Contatto
* dettaglio Azienda
* dettaglio Lead
* dettaglio Opportunità
* dettaglio Ordine
* dettaglio Progetto
* dettaglio Ticket
* dettaglio Utente
* dettaglio Documento

e qualsiasi altra Detail View presente nel progetto.

Ogni pagina di dettaglio deve essere verificata integralmente.

---

# Controlli obbligatori

Per ogni Detail View verifica:

## Header

* titolo
* sottotitolo
* badge
* avatar
* breadcrumb
* pulsanti azione
* menu azioni

---

## Sezioni

Controlla:

* card
* pannelli
* box
* widget
* statistiche
* timeline
* attività
* note
* allegati
* tabelle correlate

Le sezioni devono essere chiaramente distinguibili.

---

## Layout

Verifica:

* allineamenti
* padding
* margin
* gap
* colonne
* responsive
* overflow
* elementi tagliati
* scrollbar
* componenti fuori asse

---

## Tipografia

Controlla:

* pesi
* gerarchie
* dimensioni
* colori
* leggibilità

---

## Dark Mode

Verifica ogni componente.

Individua:

* sfondi incoerenti
* card errate
* testi poco leggibili
* badge errati
* divider invisibili
* pulsanti non coerenti
* icone
* placeholder
* link
* hover
* tooltip
* dropdown

---

## Hover

Controlla tutti gli elementi interattivi.

Compresi:

* link
* pulsanti
* icone
* badge
* menu
* dropdown
* righe tabella
* timeline
* allegati
* azioni rapide

Ogni hover deve essere chiaramente percepibile.

---

## Stati

Verifica:

* loading
* empty
* error
* disabled
* selected
* expanded
* collapsed

---

# Ricerca di problemi simili

Ogni bug trovato negli screenshot potrebbe essere presente anche altrove.

Una volta corretto un problema:

* individua tutti i componenti che utilizzano la stessa implementazione
* verifica se presentano lo stesso difetto
* correggili tutti

Non limitarti all'istanza mostrata nello screenshot.

Correggi la causa alla radice quando possibile.

---

# Processo di lavoro

Per ogni Detail View:

1. aprila realmente
2. ispezionala completamente
3. acquisisci uno screenshot
4. confrontala con le altre Detail View
5. individua ogni incoerenza
6. correggi il codice
7. verifica il risultato
8. controlla che non siano state introdotte regressioni
9. passa alla vista successiva

---

# Obiettivo finale

Tutte le viste di dettaglio devono apparire perfettamente uniformi.

L'utente non deve percepire differenze qualitative tra una Detail View e l'altra.

Ogni pagina deve trasmettere la sensazione di un prodotto professionale, rifinito nei minimi dettagli, con una Dark Mode impeccabile, hover sempre leggibili, sezioni ben evidenziate, layout ordinato e nessun problema di sovrapposizione o incoerenza visiva.
