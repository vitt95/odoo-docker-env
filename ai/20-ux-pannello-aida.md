# AIDA come pannello — analisi del riferimento, decisioni, implementazione

**Data**: 5 agosto 2026 · **Ramo**: `new-ai-agent` · **Riferimento**:
`ai/screenvideo/screen-capture.webm` (agente Rovo di Jira Cloud, 126 secondi)

Questo documento sostituisce `ai/15-implementazione-ui.md` come specifica viva
dell'interfaccia. `15` resta il documento dei requisiti (cosa deve fare); questo è il
documento delle decisioni (come lo fa, e perché così).

---

## 1. Che cosa è cambiato, in una frase

AIDA non è più una pagina: è **una colonna a destra che sta aperta mentre si lavora**,
e mentre pensa dice a che punto è.

Sono due cambiamenti, e il secondo è quello che è costato di più — perché ha richiesto
di toccare la coda.

---

## 2. Come è stato analizzato il riferimento

Un file `.webm` non si legge. È stato scomposto con `ffmpeg`:

| Passaggio | Comando, in sostanza | A cosa è servito |
|---|---|---|
| Fotogrammi a 1/s | `fps=1` | 126 immagini, la trama del video |
| Ritaglio del pannello | `crop=520:1080:1400:0` | leggere il testo piccolo |
| Cambi di scena | `select='gt(scene,0.06)'` | trovare i tagli: 2,9 s · 35 s · 41 s · 71 s · 102 s · 107 s |
| Micro-estrazioni | `fps=15` e `fps=20` su finestre di 1,5 s | apertura, invio, collasso del blocco dei passi |
| Ingrandimento a mosaico | `crop=32:32 … scale=192:192 … tile=10x3` | isolare il segno animato, 30 fotogrammi affiancati |
| Misura dei bordi | lettura riga di pixel, `rgb24` grezzo | **larghezze reali del pannello** |

### 2.1 Le misure, non le impressioni

La larghezza del pannello è stata ricavata cercando i salti di luminanza lungo una
riga di pixel a metà altezza:

| Istante | Bordo sinistro (px) | Larghezza |
|---|---|---|
| all'apertura (t = 5 s) | 1481 | **439 px** |
| dopo il primo trascinamento (t = 16 s) | 1312 | 608 px |
| dopo il secondo (t = 42 s) | 1215 | 705 px |

Da qui la larghezza di partenza di AIDA: **440 px**, che è quel numero arrotondato.

### 2.2 L'apertura non anima la larghezza

Fotogrammi a 15/s intorno a t = 2,9 s:

| Fotogramma | Istante | Cosa si vede |
|---|---|---|
| 03 | 2,73 s | pannello chiuso, tooltip sul pulsante |
| 04 | 2,80 s | **spazio già alla larghezza piena, e vuoto** |
| 05 | 2,87 s | idem |
| 06 | 2,93 s | contenuto in dissolvenza, titolo ancora smorto |

In meno di 66 millisecondi lo spazio è già aperto. **Non c'è nessuna animazione di
larghezza**: si anima solo il contenuto. È una scelta di prestazioni, e AIDA la copia
per la stessa ragione — animare una larghezza obbliga il browser a rifare il layout
dell'intera pagina a ogni fotogramma.

### 2.3 Il segno che pensa

Trenta fotogrammi del solo segno, ingranditi sei volte e affiancati, mostrano un
**poligono che si deforma** — quadrato smussato → esagono → triangolo — mentre il
colore scorre lungo una scala verde → turchese → blu → indaco → viola → magenta. Ciclo
lento, intorno ai 3-4 secondi.

### 2.4 La lista dei passi

Da t = 20 a t = 31 il pannello mostra una **finestra scorrevole di tre passi**: filo
verticale a sinistra, un'icona per passo, titolo in grassetto e descrizione grigia
troncata. Il quarto passo entra in fondo e il primo esce dall'alto: l'altezza del
blocco non cambia mai.

A t = 31,5, appena parte la risposta, tutto collassa in **«Completed 6 steps ›»**.

### 2.5 Un difetto del riferimento, non copiato

A t = 32,1 s il testo in arrivo mostra il markdown grezzo:

```
…tramite questo link: [Tutti i miei ticket](https://rcsuejira.atlassian.net/issues/?jql=…
```

È l'artefatto di un renderer markdown ingenuo in streaming. Copiare fedelmente vuol
dire copiare anche i difetti: qui no.

---

## 3. Le due decisioni di partenza

| Domanda | Scelta | Alternativa scartata |
|---|---|---|
| Pagina intera o colonna? | **Colonna laterale ridimensionabile** | Pagina intera restilizzata: più sicura, ma non risolve il problema vero |
| Passi finti o passi veri? | **Passi veri, con modifica alla coda** | Solo l'attesa animata; oppure passi retroattivi dalla traccia diagnostica |

### Perché la colonna

Un'azione client **sostituisce** quello che si stava guardando. Ma la domanda tipica
di AIDA è *«quali di questi sono scaduti?»*, e ha senso solo se **questi** sono ancora
sullo schermo. La colonna è l'unica forma che tiene insieme la domanda e la cosa di
cui parla.

Il pannello **restringe** la vista invece di coprirla: costa un riflusso all'apertura e
uno alla chiusura — due volte in tutta la sessione — e in cambio non costringe mai a
chiudere per rileggere.

**Ma restringe solo il contenuto, mai la barra in alto.** Il rientro sta su
`.o_action_manager` e non sul `body`, che in Odoo 18 contiene anche
`header.o_navbar`. Con il rientro sul `body`, aprire AIDA faceva scivolare a sinistra
il menu applicazioni e il systray, e chiuderla li riportava indietro: la barra è
l'unica cosa dello schermo che deve restare ferma qualunque cosa succeda sotto, perché
è il riferimento con cui si ritrova tutto il resto.

E il pannello comincia **esattamente** dove la barra finisce: l'altezza si misura sul
nodo vero (`--aida-top`), all'apertura e a ogni ridimensionamento della finestra. Vale
46 pixel in Classic e 48 in Premium, e un giorno sarà un altro numero — un valore
cablato è giusto finché qualcuno non cambia la barra, e quel giorno il pannello la
coprirebbe di due pixel: abbastanza per tagliare il bordo, non abbastanza perché
qualcuno capisca perché.

### Perché i passi veri

La lista dei passi è la parte più caratteristica del riferimento, ed è anche l'unica
cosa che sta sullo schermo durante l'attesa: **mediana 8,8 secondi, novantacinquesimo
percentile 16,3 secondi**, misurati su 414 chiamate vere al modello.

Inventare passi decorativi sarebbe stato il male peggiore: mostrare qualcosa che ha
l'aria di essere vero e non lo è. È lo stesso principio per cui **D2** (la decisione
che vieta qualunque scrittura sui dati finché la Fase 2 non è misurata e superata)
esiste, applicato all'interfaccia.

---

## 4. Il protocollo degli avanzamenti

### 4.1 Il vincolo che ha deciso tutto

`core/addons/bus/models/bus.py:106` — `bus.bus._sendone` **non manda niente subito**:
accoda il messaggio su `cr.precommit` e la sveglia del processo del bus su
`cr.postcommit`. Parte tutto al `commit`, e non un istante prima.

E `runtime/worker.py` fa girare l'intero turno **dentro una sola transazione**, con un
`commit` alla fine.

Quindi un avanzamento mandato sul cursore del lavoratore arriverebbe **insieme alla
risposta**: un'animazione che racconta un'attesa già finita.

**L'unica soluzione che funziona**: un cursore proprio per ogni evento, che committa
subito e si chiude.

### 4.2 Le tre proprietà non negoziabili

`custom_addons/nli_dispatch/runtime/progress.py` (178 righe)

| Proprietà | Come | Perché |
|---|---|---|
| **Non solleva mai** | ogni errore ingoiato e registrato | un avviso di cortesia che uccide il turno che descrive è il peggior scambio possibile |
| **È strozzato** | minimo 250 ms fra due eventi | un turno veloce aprirebbe sei transazioni in cinquanta millisecondi, e nessun occhio distingue sei passi in un ventesimo di secondo |
| **Ha un tetto** | massimo 12 eventi per turno | il pipeline ne emette sei; il tetto è per il ciclo scritto male che qualcuno introdurrà fra due anni |

Il primo passo parte **subito** (`force`), saltando lo strozzamento: è quello che
toglie dallo schermo l'attesa muta.

### 4.3 I sette passi, e dove si agganciano

| Chiave | Punto in `pipeline.py` | Cosa dice all'utente |
|---|---|---|
| `dictionary` | prima della fase A | «Cerco di che cosa parli» |
| `entity` | prima della fase B (modello) | «Non l'ho riconosciuto: lo chiedo al modello» |
| `catalogue` | prima della fase C | «Preparo quello che posso leggere» |
| `reading` | strada corta di **D121** | «Applico la lettura che hai scelto» |
| `interpret` | prima della chiamata al modello | «Interpreto la domanda» + nome dell'entità |
| `validate` | prima dei livelli 3-5 | «Controllo che la richiesta si possa fare» |
| `execute` | prima della query | «Interrogo Odoo» |

**Gli eventi si mandano prima dell'attesa, non dopo.** Dire «sto per chiamare il
modello» serve; dire «l'ho chiamato» dieci secondi dopo no.

### 4.4 Cosa viaggia e cosa no

Viaggia: `turn_id`, `interrogation_id`, la chiave del passo, il numero d'ordine, e un
dettaglio neutro (il nome di casa dell'entità — «fatture», «lead»).

**Non viaggia**: la frase dell'utente, il catalogo, la busta del modello. Il canale è
già il partner di chi ha scritto la frase, quindi non c'è un problema di destinatario:
è **D60** (nessuna frase e nessun catalogo nei registri diagnostici) letto come
principio invece che come regola sul solo `_logger`. Il payload minimo che funziona è
quello che non può diventare un archivio.

**Le parole non stanno sul server.** Il server manda chiavi, il client le traduce: la
lingua dell'interfaccia è una scelta dell'interfaccia.

### 4.5 La deroga architetturale

Aprire un cursore è vietato dal controllo statico (**V3**, l'accesso diretto a
PostgreSQL). Il controllo l'ha intercettato al primo tentativo, e la deroga è stata
**dichiarata con la sua motivazione** in `tools/arch/spec.py` — accanto a quella di
`worker.py`, che è l'unica altra del progetto.

### 4.6 Come si prova

| Livello | File | Cosa asserisce |
|---|---|---|
| Puro (senza database) | `nli_dispatch/pure_tests/test_progress.py` | 15 prove: forma del payload, strozzamento, tetto, silenzio, il registro che non cita la causa |
| Integrazione | `nli_dispatch/tests/test_dispatch.py::TestTheProgressSteps` | 7 prove: quali passi, in quale ordine, che nessuno porti la frase dell'utente |

Per poter provare le tre proprietà **senza una base dati**, `progress.py` importa Odoo
dentro il metodo che scrive e non in cima al file, e `tools/pure/bootstrap.py` registra
un pacchetto sintetico `nli_dispatch.runtime`. Una prova che richiede una base dati è
una prova che poi nessuno esegue.

---

## 5. Il pannello

### 5.1 Dove si aggancia

`registry.category("main_components")` — un componente montato alla radice del
webclient, accanto all'azione invece che al suo posto. È lo stesso schema della barra
laterale Premium (`ui_premium_shell/static/src/sidebar/sidebar.js`), già collaudato in
questo repository.

Il pulsante sta nel **systray**, l'unica parte della barra che resta ferma mentre le
viste cambiano.

### 5.2 Il ridimensionamento

È il punto dove le implementazioni amatoriali crollano: trascinare muove il puntatore
decine di volte al secondo, e aggiornare lo stato a ogni movimento farebbe ridisegnare
a OWL l'intera conversazione a ogni fotogramma.

Quindi durante il trascinamento **lo stato non si tocca**:

1. `pointerdown` cattura il puntatore sulla maniglia (senza, un trascinamento veloce
   che esce dalla maniglia perde gli eventi);
2. `pointermove` accumula il valore, e un solo `requestAnimationFrame` per fotogramma
   scrive **una proprietà CSS** sul `body`;
3. la stessa proprietà dà la larghezza al pannello **e** il rientro al contenuto: una
   scrittura muove entrambi, e non c'è nessun calcolo da tenere allineato;
4. `pointerup` aggiorna lo stato una volta sola e salva in `localStorage`;
5. `contain: layout paint` sul pannello dice al browser che non deve rimettere in
   dubbio il resto della pagina.

Le frecce sinistra/destra lo muovono di venti pixel per pressione: un
ridimensionamento che esiste solo per chi usa il mouse è una funzione che per una
parte delle persone non esiste.

**Confini**: minimo 360 px (sotto, una riga di testo si scansiona invece di leggersi),
massimo metà della finestra (oltre, la vista di Odoo smette di essere consultabile —
a quel punto conviene la pagina intera, che è un'altra cosa).

### 5.3 Il blocco dei passi

Finestra scorrevole di **tre** righe. Tre e non una, perché un passo solo non racconta
un percorso; tre e non tutti, perché un elenco che cresce spinge in basso la
conversazione e chi stava leggendo se la vede scappare via.

A turno finito collassa in «Completati N passi ›», espandibile. Sparire cancellerebbe
la sola spiegazione di quanto è durata l'attesa; restare aperto riempirebbe ogni
risposta di sei righe che nessuno rilegge.

### 5.4 Le due animazioni, e perché costano poco

| Elemento | Tecnica | Costo |
|---|---|---|
| Segno che pensa | `clip-path: polygon()` fra tre forme + `filter: hue-rotate()` | solo disegno, su un elemento di 14 px |
| Testo che luccica | gradiente ritagliato sul testo (`background-clip: text`), posizione animata | solo disegno, su una riga |

**Nessuna delle due tocca il layout.**

Due dettagli che sembrano pedanteria e non lo sono:

- **Le forme hanno tutte sei vertici.** `clip-path` interpola solo fra poligoni con lo
  stesso numero di vertici: il triangolo è un esagono con i vertici a due a due
  sovrapposti. Con tre vertici veri, la transizione salta.
- **L'arco di colore è di 190 gradi, non di 360.** Il giro completo, partendo da un
  blu, passa per rosso mattone e verde acido. Da −100° a +90° si copre
  verde-turchese → accento → viola-magenta: la stessa scala del riferimento, senza mai
  uscire dai colori che l'accento giustifica.

### 5.5 La tabella dentro una colonna stretta

La vista lista di Odoo incorporata (`00` §23) **resta**: è la funzione che c'è, e
toglierla per fare spazio all'estetica sarebbe un peggioramento travestito. Ma dentro
440 pixel si consulta male, quindi:

- scorre **in orizzontale dentro il proprio riquadro** invece di allargare la colonna
  (un contenuto che decide la larghezza del suo contenitore rende il
  ridimensionamento una lotta);
- l'altezza segue i record (`max-height`, non `height`): tre risultati occupano tre
  righe;
- le righe vuote di riempimento di Odoo sono nascoste — dentro una risposta fanno
  sembrare che ci siano risultati che non ci sono;
- sopra c'è **«Apri a tutta pagina»**, che lancia l'azione Odoo con lo stesso dominio.
  È anche il comportamento del riferimento, che rimanda a Jira invece di mostrare
  tutto nel pannello.

---

## 6. I token e i tre temi

Tutto lo stile legge **solo** `--aida-*`. Un solo file sa dei temi:
`static/src/aida_tokens.scss`.

### 6.1 I tre gradini

```
--aida-bg: var(--pui-color-bg, var(--body-bg, #ffffff));
            ^ Premium          ^ Odoo/Classic   ^ ultima parola
```

### 6.2 Due nomi sbagliati, tutti e due trovati guardando

**Primo — `--o-view-background-color` non esiste.** Era il gradino intermedio in tutto
lo SCSS di AIDA. `$o-view-background-color` è una variabile **SCSS**, risolta a
compilazione: come variabile CSS non arriva mai al browser. In tutto `web/static/src`
ci sono 38 variabili CSS con prefisso `--o-` e nessuna è quella.

Conseguenza: con la skin Classic il browser saltava al valore cablato, che è chiaro.

**Secondo — `--bs-body-bg` non esiste neanche.** Era la correzione ovvia, ed era
sbagliata pure lei. `web/static/src/scss/bootstrap_overridden.scss:51` imposta
`$variable-prefix: ''`, quindi Bootstrap emette `--body-bg` e non `--bs-body-bg`.
Verificato contando nel pacchetto servito: occorrenze di `--bs-`, **zero**.

Due nomi plausibili di fila, tutti e due assenti, tutti e due silenziosi. È il modo di
fallire di un fallback: non c'è nessun errore, perché il gradino successivo funziona
sempre. **L'unica prova possibile è guardare il browser.**

### 6.3 I valori veri, misurati

| Token AIDA | Premium chiaro | Premium scuro | Classic |
|---|---|---|---|
| `--aida-bg` | `#f7f8fa` | `#1d2125` | `#f8f9fa` |
| `--aida-surface` | `#ffffff` | `#22272b` | `#f8f9fa` |
| testo | `#2c3e5d` | `#c3ccd6` | `#495057` |
| `--aida-accent` | `#0c66e4` | `#579dff` | `#71639e` *(viola di Odoo)* |
| `--aida-border` | `#e3e6ec` | `#38414a` | `#dee2e6` |

In Classic l'accento è il **viola di Odoo**, e va bene così: AIDA deve sembrare parte
della piattaforma che la ospita, non portarsi dietro il blu di un altro prodotto.
È **D25** (i token di marca si usano quando ci sono e l'interfaccia degrada con grazia
quando non ci sono).

### 6.4 Sul buio della skin Classic

Odoo 18 Community **non ha un tema scuro vero**: `web.assets_web_dark` aggiunge tre
file di componente e lascia la tavolozza dov'è. Verificato in due modi — nessun
`*.dark.scss` fra gli SCSS principali, e i valori a `:root` con il cookie
`color_scheme=dark` identici a quelli chiari.

Quindi con la skin Classic AIDA è chiara perché **Odoo è chiaro**. Il giorno in cui
`web_enterprise` porta il suo pacchetto scuro, `--body-bg` si ribalta e AIDA si
ribalta con lui, senza che nessuno tocchi il file dei token.

### 6.5 La bolla si mescola invece di essere dichiarata due volte

Una tinta d'accento al 12% su bianco si vede; la stessa su un grigio scuro sparisce.
La prima versione risolveva con due blocchi, e il secondo doveva indovinare quale
pacchetto Odoo avesse servito — cosa che `prefers-color-scheme` **non dice**: quello
racconta il sistema operativo, non la skin.

`color-mix(in srgb, var(--aida-accent) 14%, var(--aida-surface))` toglie la domanda
invece di rispondere male: la bolla si compone con la superficie che ha davvero sotto.

---

## 7. I difetti trovati verificando

Nessuno di questi sarebbe emerso leggendo il codice. Tutti sono usciti compilando,
aprendo un browser e guardando.

| # | Difetto | Come si è visto | Conseguenza se non trovato |
|---|---|---|---|
| 1 | `min(300px, 88%)` in SCSS | compilazione: *«Incompatible units: '%' and 'px'»* | Sass ha un `min()` suo e prova a calcolare: l'errore **fermava tutto `web.assets_backend`**, cioè lo stile di tutto Odoo |
| 2 | `--o-view-background-color` non esiste | interrogazione delle variabili in pagina | AIDA bianca dentro una piattaforma scura |
| 3 | `--bs-*` non esiste | conteggio nel pacchetto servito: zero | idem, dopo la «correzione» |
| 4 | Lo shimmer cancellava testo | screenshot: «Sto pensando…» si leggeva «pensando…» | con `no-repeat`, una posizione fuori intervallo lascia scoperta una parte del riquadro — e lì `color: transparent` è **invisibile**, non sbiadito |
| 5 | Il segno diventava magenta acceso | screenshot in tema scuro | `hue-rotate(360deg)` da un blu passa per colori che con quel blu non c'entrano |
| 6 | Il pulsante illeggibile sulla barra | screenshot della barra | la classe `btn` di Bootstrap imponeva il colore; e `color: inherit` non bastava, perché `.o_main_navbar` calcola un colore scuro e mette il bianco sulle **voci** una per una |
| 7 | La scorciatoia non chiudeva | prova funzionale | il servizio ignora i tasti quando si scrive, e aprendo il pannello il fuoco va nella casella: la scorciatoia era inutilizzabile **nel caso normale** |
| 8 | Il suggerimento insegnava un gesto falso | prova funzionale su Mac | su macOS il token `alt` di Odoo lo produce **Ctrl**: la scritta diceva «Alt+Maiusc+A» e quella combinazione non apriva niente |
| 9 | Il velo della cronologia non si poteva cliccare al centro | il copione clicca il centro, come una persona | a larghezza minima restavano 60 px di velo, e il centro cadeva sulla cronologia |
| 10 | **La barra in alto si muoveva** | segnalato guardando | il rientro stava sul `body`, che in Odoo 18 contiene anche `header.o_navbar`: aprendo AIDA il menu applicazioni e il systray scivolavano a sinistra e tornavano indietro chiudendo |

Il numero 1 merita una riga in più: era una sola parola sbagliata in una riga di CSS, e
avrebbe spento il foglio di stile dell'intera piattaforma.

---

## 8. Budget di prestazioni

| Momento | Costo | Come è stato tenuto basso |
|---|---|---|
| Caricamento pagina, AIDA mai aperta | **zero richieste** | il servizio non parte da solo: `store.start()` alla prima apertura |
| Apertura | un riflusso | nessuna animazione di larghezza; solo opacità e traslazione |
| Trascinamento della maniglia | una scrittura CSS per fotogramma | stato non toccato, `requestAnimationFrame`, `contain: layout paint` |
| Un passo che arriva | una riga aggiunta | `t-key` sull'indice del server: OWL sposta le righe invece di ridisegnarle |
| Un turno intero | ≤ 12 transazioni brevissime | strozzamento a 250 ms e tetto a 12 |
| Pannello chiuso | **nessun DOM** | `t-if` sulla radice: niente conversazione disegnata, niente vista lista montata |

---

## 9. Accessibilità

- La maniglia è un `role="separator"` con `aria-valuenow`, raggiungibile con `Tab` e
  mossa dalle frecce.
- Il pannello è un `role="complementary"` con etichetta.
- Lo stato d'attesa è `aria-live="polite"`, e sta sull'intestazione e non sulle righe:
  chi usa un lettore di schermo deve sentire *cosa sta facendo adesso*, non farsi
  rileggere l'elenco a ogni passo.
- Il puntino del pulsante ha accanto un testo per soli lettori di schermo.
- Le azioni della cronologia si nascondono con `opacity`, mai con `display: none`, così
  restano raggiungibili da tastiera.
- `prefers-reduced-motion` spegne tutte le animazioni. **Non si perde niente**:
  l'attesa si legge dal testo, i passi dal loro elenco. Un'animazione che porta l'unica
  copia di un'informazione è un difetto, non un effetto.
- `forced-colors` disattiva il ritaglio sul testo e torna ai colori di sistema.
- **D65** (l'origine di una condizione non si distingue mai dal solo colore) è
  rispettato: una condizione dedotta ha bordo tratteggiato **e** la regola scritta
  sotto.

---

## 10. Cosa resta fuori, e perché

| Elemento del riferimento | Perché no |
|---|---|
| Testo in streaming | Non esiste streaming: il turno arriva completo. Fingerlo sarebbe teatro |
| Pollice su / pollice giù | Nessun modello dati dove quel giudizio andrebbe a finire. Un comando che non fa niente è peggio di un comando assente |
| Menu «cambia agente» | C'è un agente solo |
| Bottone di stop | Il turno in coda non è annullabile oggi |
| Chip «N Sources» | Sostituito dal conteggio record, che dice la stessa cosa con i nostri dati |
| Markdown grezzo in streaming | È un difetto del riferimento (§2.5) |

I suggerimenti della schermata iniziale **riempiono la casella invece di partire**, al
contrario di **D121** (dove il clic su una lettura scrive l'etichetta e invia) e per la
ragione opposta: lì l'opzione viene dal catalogo ed è vera per costruzione, qui è un
esempio scritto da noi, e quali entità esistono dipende dai moduli installati. Un
esempio che fallisce al primo clic insegna a non fidarsi dei suggerimenti.

---

## 11. Mappa dei file

### Backend — `nli_dispatch`

| File | Righe | Ruolo |
|---|---|---|
| `runtime/progress.py` | 178 | **nuovo** — il reporter, il cursore proprio, le tre proprietà |
| `runtime/pipeline.py` | +64 | sette punti di emissione, `reporter` filtrato fino in fondo |
| `runtime/worker.py` | +24 | costruisce il reporter dagli identificativi che ha già in mano |
| `pure_tests/test_progress.py` | 184 | **nuovo** — 15 prove senza base dati |
| `tests/test_dispatch.py` | +118 | **nuovo** — `TestTheProgressSteps`, 7 prove |

### Frontend — `nli_web`

| File | Righe | Ruolo |
|---|---|---|
| `static/src/aida_tokens.scss` | 145 | **nuovo** — i tre gradini, in un posto solo |
| `panel/aida_service.js` | 132 | **nuovo** — stato condiviso, avvio pigro, larghezza |
| `panel/aida_panel.js` | 244 | **nuovo** — il contenitore, il ridimensionamento |
| `panel/aida_launcher.js` | 68 | **nuovo** — il pulsante nel systray |
| `panel/aida_panel.xml` · `.scss` | 126 · 386 | **nuovi** |
| `chat/aida_steps.js` · `.xml` · `.scss` | 159 · 60 · 273 | **nuovi** — passi, segno, luccichio |
| `chat/aida_welcome.js` | 88 | **nuovo** — schermata iniziale |
| `chat/aida_history.js` | 85 | **nuovo** — sostituisce `aida_sidebar.js` |
| `chat/aida_store.js` | +107 | secondo canale del bus, passi orfani |
| `chat/aida_thread.js` | +84 | passi, copia, apri a tutta pagina |
| `chat/aida_chat.js` | riscritto | la voce di menu, che ora spiega dov'è AIDA |

### Strumenti

| File | Cosa |
|---|---|
| `tools/arch/spec.py` | deroga dichiarata per il cursore di `progress.py` |
| `tools/pure/bootstrap.py` | pacchetti sintetici per le sotto-cartelle |

---

## 12. Come si verifica

```bash
./manage.sh check              # 5 controlli architetturali + 504 prove pure
./manage.sh test nli_test      # 256 prove Odoo

# E la verifica che ha trovato metà dei difetti: aprire un browser e guardare.
pip install playwright && playwright install chromium
python3 tools/ui/verify_panel.py --db nli_test --password <password>
```

`tools/ui/verify_panel.py` è **il guardare, reso ripetibile**. Entra, apre una vista
lista vera, apre il pannello, legge i token risolti nei tre temi — Premium si simula
iniettando i `--pui-*` della tavolozza, che è esattamente quello che fa il pacchetto
Premium — e prova i gesti che si rompono in silenzio: trascinamento, confini,
cronologia, `Escape`, bozza che sopravvive alla chiusura, scorciatoia col fuoco nella
casella. Raccoglie **ogni** errore JavaScript della pagina e fallisce se ce n'è uno.

Non è una suite e non sostituisce i `tour` di Odoo che un giorno andranno scritti: li
anticipa nella sola cosa che sanno fare già oggi, cioè accorgersi che qualcosa non si
disegna. Ha già ripagato il costo — l'ultimo difetto trovato è il velo della
cronologia che non si poteva cliccare al centro alla larghezza minima, perché il
copione clicca il centro come farebbe una persona.

Stato al 5 agosto 2026:

| Verifica | Esito |
|---|---|
| Controlli architetturali | **5 / 5** |
| Prove pure | **504**, 0 fallite |
| Prove Odoo | **256**, 0 fallite, 0 errori (`nli_dispatch`: 108) |
| `verify_panel.py` | **47 asserzioni**, tutte verdi |
| Compilazione dei pacchetti | `web.assets_backend`, `ui_theme_engine.assets_web_premium`, `web.assets_web_dark` — tutti e tre |
| Errori JavaScript in pagina | **nessuno**, nei tre temi |

---

## 13. Il debito che resta

1. **`verify_panel.py` non è nella suite.** Va lanciato a mano e ha bisogno di
   Playwright, quindi non gira in `./manage.sh check`. Finché è così, dipende da chi si
   ricorda di eseguirlo — e le verifiche che dipendono dalla memoria sono quelle che
   spariscono. Un `tour` Odoo che apra il pannello, mandi una frase e controlli che i
   passi arrivino girerebbe insieme a tutto il resto.
   Vale la pena ricordare l'ordine di grandezza: i difetti 4, 5, 6, 7 e 8 di §7 sono
   passati indenni sotto 256 prove verdi.
2. **Il ritardo dei passi non è misurato.** Sappiamo che arrivano; non sappiamo quanto
   dopo l'istante in cui il turno li raggiunge. Una misura fra `report()` e la
   comparsa sullo schermo direbbe se lo strozzamento a 250 ms è il numero giusto.
3. **La cronologia non ha ricerca.** Con quindici conversazioni non serve; con
   trecento sì.
