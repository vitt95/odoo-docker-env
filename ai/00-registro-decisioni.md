# Registro delle Decisioni Architetturali

## AI Agent per Odoo — Natural Language Interaction Layer

| | |
|---|---|
| **Documento** | `00-registro-decisioni.md` |
| **Natura** | Documento di governo — vive per tutta la durata del progetto |
| **Copre** | D1–D53, con l'articolazione D20a–D20f |
| **Fonti** | `02-visione-prodotto.md` §19 · `03-specifica-dsl.md` §20 · `04-architettura.md` §17 · `05-esecuzione-asincrona.md` §10 · `06-modello-semantico.md` §13 · `07-piano-valutazione-qualita.md` §17 |
| **Autorità decisionale** | Architect — delega esercitata in questa sede |
| **Delibera** | 27 luglio 2026 |
| **Stato complessivo** | **51 decisioni adottate** (di cui 12 con vincolo), **5 superate**, **3 aperte** |

---

## 1. Perché questo documento esiste

Le decisioni sono nate distribuite: ogni documento di progettazione ha chiuso con la propria tabella, in continuità di numerazione ma senza un luogo unico dove leggerne lo stato. Questo produce tre problemi concreti.

**Il primo è la tracciabilità dello stato.** Le tabelle d'origine dicono cosa *si raccomanda*, non cosa *è stato deciso*.

**Il secondo è la supersessione silenziosa.** Cinque decisioni sono state assorbite da decisioni successive (D20 → D20a–D20f; D16 e D21 → D32; D17 → D29; D22 → D34). Chi legge `03-specifica-dsl.md` §20 in isolamento troverebbe D16 come questione aperta quando è chiusa in `06-modello-semantico.md`.

**Il terzo è l'ordine.** D9, D10 e D4 sono dichiarate come prerequisiti in testa a `03` e `04`. Se venissero respinte, quei documenti andrebbero riscritti, non emendati.

Il registro non sostituisce le tabelle nei documenti: quelle restano il luogo dove la decisione è **motivata**. Il registro è il luogo dove la decisione è **deliberata**.

---

## 2. Convenzioni

### 2.1 Stati

| Stato | Significato |
|---|---|
| ☑ **Adottata** | Deliberata e vincolante |
| ⊡ **Adottata con vincolo** | Deliberata, con una condizione aggiunta in sede di delibera. La condizione è parte della decisione |
| ⊘ **Superata** | Assorbita da una decisione successiva; conservata, mai cancellata |
| ☐ **Aperta** | Non deliberabile su base tecnica: richiede un'informazione commerciale o di mercato |
| ✗ **Respinta** | Deliberata in senso negativo, con motivazione |

### 2.2 Criterio di delibera

Le decisioni sono state valutate contro quattro obiettivi dichiarati — **semplicità, velocità, scalabilità, livello enterprise** — con la seguente regola di conflitto, che vale la pena esplicitare perché è stata applicata più volte:

> Dove semplicità e scalabilità confliggono, prevale la scalabilità **solo se** il costo di introdurla dopo è superlineare. Altrimenti prevale la semplicità e la scalabilità si rinvia con percorso dichiarato.

È il criterio che ha portato ad adottare D23 e D20f (rinvii a costo nullo) e per contro a irrigidire D24 e D39 (controlli che dopo costano molto di più).

---

## 3. Registro

### 3.1 Fondamenta — `02-visione-prodotto.md` §19

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D1** | Fase 0 come fase autonoma | ☑ Adottata | I contratti fondativi non sono attività di release. Senza fase autonoma vengono compressi |
| **D2** | Fase 2 come cancello obbligatorio prima di qualunque scrittura | ☑ Adottata | Il salto lettura → scrittura è il maggiore del programma. Autorizzarlo senza misura è indifendibile |
| **D3** | Assunzione **A6** sui dati verso il modello | ⊡ Con vincolo | Adottata. **Vincolo:** A6 protegge il contenuto dei record, **non l'enunciato dell'utente** — vedi §5.3 |
| **D4** | Stato di Interrogazione come oggetto centrale | ☑ Adottata | È anche la Leva 2 delle prestazioni (`04` §10.2): contesto costante nelle conversazioni lunghe |
| **D5** | Soglie dei KPI | ⊡ Con vincolo | Confermate come riferimento iniziale. **Vincolo:** la latenza va scomposta — vedi §6.1 |
| **D6** | Denominazione del prodotto | ☐ Aperta (parziale) | **Parte tecnica decisa:** prefisso `nli_`. Parte commerciale non tecnica — vedi §7 |
| **D7** | Clienti pilota e attività di riferimento | ☐ Aperta | Non deliberabile tecnicamente. **Requisiti di scelta fissati** in §7 |
| **D8** | Erogazione per clienti regolamentati | ☐ Aperta | Commerciale. A6 e il confine dell'Adattatore la rendono già praticabile a costo basso |

### 3.2 Contratto di interpretazione — `03-specifica-dsl.md` §20

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D9** | Due artefatti: il modello emette operazioni, il sistema possiede lo stato | ☑ Adottata | Decisione corretta e non sostituibile. Rende **impossibile** la deriva dello stato, non improbabile. Output di dimensione costante: è anche la scelta più economica per turno |
| **D10** | Riferimenti semantici con catalogo per utente | ☑ Adottata | La restrizione opera a livello di vocabolario, prima di ogni controllo. **V2** diventa una proprietà della forma dello spazio interpretativo, non un filtro a valle |
| **D11** | JSON con schema formale come forma normativa | ☑ Adottata | Nessun parser proprietario da mantenere per dieci anni; generazione vincolata supportata. La distinzione trasporto/contratto di §18.1 è corretta e va mantenuta |
| **D12** | Limiti strutturali: 2 salti, filtri a 3 livelli, 3 raggruppamenti | ☑ Adottata | Valori iniziali confermati. Sono ciò che rende la validazione di costo (livello 5) calcolabile a priori anziché stimata |
| **D13** | Limite predefinito e massimo dei record | ⊡ Con vincolo | **Valori fissati:** predefinito **80**, massimo assoluto **500** — vedi §6.2 |
| **D14** | Simboli sconosciuti: respingere, mai ignorare | ☑ Adottata | Ignorare un simbolo produce un risultato meno filtrato del richiesto, che è la forma di **R1** che nessuno rileva |
| **D15** | Ripristino con un solo tentativo | ☑ Adottata | Il limite è normativo. Un secondo tentativo maschera un difetto sistematico e lo toglie dalle metriche |
| **D16** | Pre-selezione del catalogo | ⊘ Superata da **D32** | — |
| **D17** | Versionamento delle voci di definizione | ⊘ Superata da **D29** | — |

### 3.3 Architettura — `04-architettura.md` §17

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D18** | Cinque moduli `nli_*` con il grafo di §6.2 | ☑ Adottata | La separazione non è organizzativa: il grafo dei manifest Odoo è ciò che rende i confini **verificabili**. Cinque moduli mal separati sarebbero peggio di uno — ed è per questo che D24 è adottata insieme, non dopo |
| **D19** | Stato persistito come record Odoo | ☑ Adottata | Nessun archivio aggiuntivo da gestire per dieci anni. Ripresa, cambio canale, condivisione, annullamento e tracciabilità sono conseguenze, non funzionalità da costruire |
| **D20** | Interpretazione fuori dal ciclo di richiesta | ⊘ Superata da **D20a–D20f** | — |
| **D21** | Catalogo a due fasi con percorso rapido | ⊘ Superata da **D32** | — |
| **D22** | Copertura come metrica di primo livello | ⊘ Superata da **D34** | — |
| **D23** | Interprete nello stesso processo, dietro l'Adattatore | ☑ Adottata | Rinvio a costo nullo: l'accodamento disaccoppia già, l'Adattatore è già un confine. Estrarre in seguito è cambiare un'implementazione, non ridisegnare |
| **D24** | I quattro controlli automatici dei confini nella prima consegna | ☑ Adottata | **Non rinviabile.** Costano poco ora e in modo superlineare dopo, quando le violazioni esistono e vanno prima sanate |
| **D25** | `nli_web` usa i token di `ui_brand_tokens`, con degradazione | ☑ Adottata | Verificato: `custom_addons/ui_brand_tokens` esiste. Un livello conversazionale visivamente estraneo è il fallimento descritto da **R3** |
| **D26** | Politica di ritenzione di §9.3 | ⊡ Con vincolo | Valori confermati. **Vincolo:** cancellazione a lotti sul dispatcher differito — vedi §6.3 |

### 3.4 Esecuzione asincrona — `05-esecuzione-asincrona.md` §10

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D20a** | Accettazione immediata + `ir.cron._trigger()` + notifica su bus | ☑ Adottata | Verificata sui sorgenti (F1, F2, F3). Risolve RA3 senza servizi nuovi. La garanzia post-commit di `ir_cron.py:701` è ciò che chiude la corsa critica |
| **D20b** | Un solo cron dispatcher con pool di thread, `CICLO_MAX` 15 s | ⊡ Con vincolo | Imposta da V-A e V-B. **Vincolo:** dimensione del pool derivata da `db_maxconn`, non scelta — vedi §6.4 |
| **D20c** | I cinque limiti di carico, con rifiuto esplicito e scadenza dei turni | ☑ Adottata | **Difesa in anticipo.** Senza limiti il sistema smette di rallentare l'ERP e comincia ad accumulare lavoro che nessuno riceverà: il guasto non scompare, diventa non diagnosticabile |
| **D20d** | Carico differito su dispatcher separato | ☑ Adottata | Il ricalcolo del corpus è il carico più massiccio che il sistema genera. Condividerlo con l'interattivo lo renderebbe visibile a ogni utente |
| **D20e** | `--max-cron-threads` da 2 a 4 | ⊡ Con vincolo | Adottata. **Vincolo:** vale il tetto di connessioni di §6.4; il valore va riconfermato sul primo pilota |
| **D20f** | Esecutore dedicato come opzione, non nella prima release | ⊡ Con vincolo | Rinvio senza debito. **Vincolo:** il percorso di scala corretto sono **N record cron dispatcher, non N istanze** — vedi §5.1 |
| **D27** | Prova di isolamento come criterio di accettazione | ☑ Adottata | È la sola prova che verifica RA3. Un livello conversazionale rapido su un ERP rallentato è un fallimento |

### 3.5 Modello semantico — `06-modello-semantico.md` §13

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D28** | Quattro livelli, precedenza L2 › L1 › L0; L3 non attivo | ☑ Adottata | L3 inattivo è corretto: un apprendimento errato è auto-rinforzante e nessun indicatore lo segnala |
| **D29** | Distinzione vocabolario / definizione con governo differenziato | ☑ Adottata | Impedisce che il significato di un dato aziendale cambi senza che nessuno se ne accorga. La notifica ai proprietari è **calcolabile in modo esatto**, non stimata: è ciò che la rende operativa |
| **D30** | Sette tipi di voce, vocabolario chiuso | ⊡ Con vincolo | Adottata. **Vincolo:** dichiarare sette non obbliga a implementarne sette in Fase 1 — vedi §6.5 |
| **D31** | Regole di esposizione §5.3 e budget §5.4 | ⊡ Con vincolo | Regole adottate. **Budget fissato: 60 attributi esposti per entità** — vedi §6.2 |
| **D32** | Strategia a tre fasi A / B / C per il catalogo | ☑ Adottata | Chiude **RC3**. In Fase C non c'è selezione: la copertura sugli attributi è esatta per costruzione, e il punto di perdita si riduce alla sola determinazione dell'entità |
| **D33** | In Fase A servono soglia **e** margine | ☑ Adottata | Il margine è ciò che distingue una corrispondenza da un'ipotesi. Senza, il percorso rapido indovina in silenzio |
| **D34** | Copertura scomposta entità/attributi, soglia ≥ 99% | ⊡ Con vincolo | Adottata. **Vincolo:** richiede D41, altrimenti il costo di conservazione la rende insostenibile |
| **D35** | Attivazione come componente, estrazione da `ir.filters` | ☑ Adottata | I filtri salvati sono definizioni già scritte da utenti dell'azienda: la fonte a costo più basso e qualità più alta |
| **D36** | Versione del dizionario; voci orfane sospese, mai cancellate | ☑ Adottata | Coerente con D29 e con la riproducibilità del corpus |
| **D37** | Indice dei termini unico e multilingua | ☑ Adottata | — |
| **D38** | Diritti separati per vocabolario e definizioni | ☑ Adottata | È l'applicazione di D29 al modello di autorizzazione |

### 3.6 Valutazione della qualità — `07-piano-valutazione-qualita.md` §17

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D42** | Tre popolazioni di corpus, con **corpus sigillato** protetto da autorizzazione | ☑ Adottata | Senza sigillo la misura degrada in conferma entro pochi trimestri, e il procedimento che la degrada è il procedimento corretto di miglioramento. Il controllo di accesso è funzionale, non convenzionale |
| **D43** | **Registro delle equivalenze semantiche** chiuso e versionato | ☑ Adottata | Chiude **RC5** senza aprire la strada opposta. L'aggiunta di una voce è una modifica del contratto: altrimenti è il luogo dove la soglia si sposta senza che nessuno lo dichiari |
| **D44** | Accuratezza **per sezione ≥ 85%** | ☑ Adottata | Con la sola soglia complessiva, entità al 99% e raggruppamenti al 62% superano il cancello. Chi usa i raggruppamenti sta facendo analisi: è l'utente che ha più bisogno del prodotto |
| **D45** | Dimensioni del corpus: 1 000 / 300 iniziali, 3 000 / 1 000 a fine Fase 2 | ⊡ Con vincolo | Adottata. **Vincolo:** finché il sigillato è sotto 1 000 casi, l'intervallo di confidenza va riportato accanto a ogni misura |
| **D46** | Bilanciamento di §3.6, con ≥ 40% turni di raffinamento e casi multi-società | ☑ Adottata | Un corpus di sole aperture misura la parte del prodotto che somiglia a un motore di ricerca, ignorando quella che lo distingue. La riga multi-società discende da **D40** |
| **D47** | Sostituzione dei riferimenti a persone e organizzazioni con segnaposto stabili | ☑ Adottata | Il corpus è l'archivio peggiore possibile per dati personali: conservato per anni, replicato fra ambienti, usato in collaudo. È anche ciò che lo rende condivisibile fra clienti |
| **D48** | **Stabilità** K = 5 ≥ 98%; soglia di rumore a 2σ, ricalcolata a ogni cambio di modello | ☑ Adottata | Senza, ogni fluttuazione diventa un risultato e il cancello di regressione scatta a caso — fino a essere disattivato |
| **D49** | Cancello di Fase 2 sulle otto condizioni, con accuratezza sull'**estremo inferiore** dell'intervallo | ☑ Adottata | Autorizzare la scrittura sui dati aziendali su una stima puntuale è il rischio che **D2** esiste per impedire |
| **D50** | Regressione per sezione con blocco; deroga dall'Architect, registrata e **con scadenza** | ☑ Adottata | La scadenza è ciò che impedisce alla deroga di diventare il funzionamento ordinario |
| **D51** | Protocollo di qualificazione di un nuovo modello in otto passi | ☑ Adottata | L'ottavo passo — prova di isolamento — è quello che si dimentica: un modello più lento dimezza la capacità del dispatcher, e la conseguenza è sull'ERP |
| **D52** | **Misura iniziale sull'interfaccia nativa prima dell'attivazione** | ⊡ Con vincolo | Adottata. **Vincolo:** esecutiva solo alla chiusura di **D7**. È l'unica decisione del progetto la cui finestra si chiude da sola, senza preavviso |
| **D53** | Origine, provenienza e presenza dell'interpretazione come indicatori propri | ☑ Adottata | La canonicalizzazione le esclude per ragioni corrette: un sistema che infersse tutto bene senza dichiarare mai l'origine risulterebbe conforme violando **P3** |

---

## 4. Le decisioni portanti, confermate

Sette decisioni erano dichiarate bloccanti. Tutte adottate. La ragione per cui reggono, in una riga ciascuna:

| # | Perché regge |
|---|---|
| **D9** | Lo spazio di ciò che il modello può sbagliare coincide con lo spazio di ciò che l'utente ha appena chiesto |
| **D10** | L'autorizzazione diventa una proprietà del vocabolario, non un controllo che qualcuno deve ricordarsi di applicare |
| **D19** | Cinque proprietà di prodotto ottenute senza alcun componente aggiuntivo |
| **D20a–f** | L'unico rischio del progetto il cui danno ricade fuori dal perimetro del prodotto, risolto con ciò che la piattaforma già offre |
| **D29** | Rende impossibile la modalità di guasto che non produce errori ma numeri diversi, tutti plausibili |
| **D32** | Trasforma un tetto di accuratezza invisibile in un problema piccolo, isolato e misurabile |
| **D34** | Rende quella chiusura verificabile invece che asserita |

Un'osservazione che emerge solo leggendo i documenti insieme: **il limite L1 di D20c chiude alla radice la corsa di `04` §9.6.** Se una sessione ammette una sola interpretazione in volo, due canali non possono produrre turni concorrenti sulla stessa sessione. La reinterpretazione su stato non più corrente resta necessaria come rete, ma diventa un evento raro — come §9.6 sosteneva senza poterlo dimostrare. È un segno che l'impianto è coerente: due documenti scritti separatamente convergono.

---

## 5. Modifiche introdotte in sede di delibera

### 5.1 D20f — il percorso di scala non è per istanze

Il documento indica come capacità dell'esecutore dedicato *"scalabile per istanze"*. **Non è corretto come formulato**, e la ragione sta in un vincolo che il documento stesso ha verificato.

**V-A** stabilisce che un record `ir.cron` ammette **una sola esecuzione concorrente nell'intero cluster** (`ir_cron.py:140`, acquisizione con blocco per riga). Avviare una seconda istanza dedicata non aggiunge capacità: entrambe competono per lo stesso record, una acquisisce e l'altra salta. La capacità resterebbe quella di un pool, esattamente come prima.

**Il percorso di scala corretto sono N record cron dispatcher distinti**, ciascuno con il proprio pool, distribuibili su una o più istanze. È già compatibile con il disegno senza alcuna modifica: l'acquisizione del lotto usa `SELECT … FOR UPDATE SKIP LOCKED` (§3.3), che rende sicura l'estrazione concorrente da parte di dispatcher diversi.

Capacità risultante ≈ `N_dispatcher × dimensione_pool`, con il tetto di §6.4.

**D20f resta adottata** — l'esecutore dedicato è il modo giusto di isolare — ma la riga *"scalabile per istanze"* di §5.2 va corretta in *"scalabile per record dispatcher"*. È una modifica di una riga che è la differenza fra un percorso di scala che funziona e uno che al primo tentativo non produce alcun effetto, per una ragione che nessuno cercherebbe nel posto giusto.

### 5.2 D3 — che cosa A6 protegge davvero

A6 è adottata, e va adottata: esclude il contenuto dei record dal flusso verso il fornitore, chiude il vettore di iniezione alla radice (`03` §13.4) e apre i segmenti regolamentati.

**Ma A6 non rende il flusso in uscita privo di dati personali, e questo va scritto adesso.**

Il modello riceve la frase dell'utente. Una frase come *"mostrami gli ordini di Mario Rossi"* contiene un dato personale di un cliente, e lo contiene **prima** che la risoluzione referenziale (`03` §11.3) intervenga: la risoluzione è un'operazione del sistema, che avviene a valle dell'interpretazione.

Le conseguenze sono due, entrambe pratiche:

- **commerciale**: la formulazione *"nessun dato aziendale raggiunge il modello"* è vera per il contenuto dei record e falsa per l'enunciato. Promessa in questa forma a un cliente regolamentato, diventa un problema quando qualcuno legge i log;
- **di conformità**: il trattamento dell'enunciato va disciplinato — ritenzione presso il fornitore, esclusione dall'addestramento, luogo del trattamento.

Nessuna di queste è una decisione architetturale, e nessuna appartiene a questo registro. **Sono l'ingresso obbligato del documento 08 — Sicurezza e Conformità**, e vanno affrontate lì prima di qualunque impegno commerciale. Qui viene registrato il vincolo perché non si perda.

### 5.3 D26 — la ritenzione va eseguita, non solo dichiarata

I valori sono corretti e sostenibili. Manca il come: cancellare dodici mesi di turni su un'installazione attiva è un evento di blocco sulla banca dati, non un'operazione di manutenzione.

**Vincolo aggiunto:** la cancellazione avviene a lotti limitati, sul **dispatcher differito di D20d**, mai sul pool interattivo e mai in una transazione unica. È la stessa regola di RE5 applicata a un carico che nessuno aveva contato fra i carichi.

---

## 6. Valori fissati

### 6.1 D5 — la latenza va scomposta

La soglia *"latenza percepita P95 ≤ 3 secondi"* è stata scritta prima dell'esecuzione asincrona. Con D20a il tempo totale ha due componenti con cause diverse: l'attesa in coda e l'interpretazione. Una soglia unica viene violata sotto carico senza dire quale delle due l'ha violata — cioè proprio quando serve saperlo.

| KPI | Soglia | Cosa segnala se violata |
|---|---|---|
| **Tempo alla risposta, P95** | ≤ 3 s | Metrica di prodotto, invariata |
| **Attesa in coda, P95** | ≤ 500 ms | Metrica di capacità: il sistema è sottodimensionato, va aggiunto un dispatcher |
| **Accettazione, P95** | ≤ 50 ms | Se sale, il worker HTTP non si sta liberando: regressione su D20a |

Le altre soglie di `02` §17 sono confermate come riferimento iniziale, da ricalibrare dopo il primo trimestre.

### 6.2 D13 e D31 — i numeri mancanti

| Parametro | Valore | Motivazione |
|---|---|---|
| **Limite record predefinito** | **80** | Coincide con la paginazione nativa delle viste lista Odoo. Un risultato conversazionale è così indistinguibile dalla prima pagina di una vista nativa — che è precisamente il requisito di prodotto additivo di `02` §4.6 |
| **Limite record massimo assoluto** | **500** | Oltre questa soglia la superficie conversazionale è lo strumento sbagliato: la risposta corretta è restringere o passare a pivot ed esportazione. È anche la soglia oltre la quale scatta il messaggio di §12.6 con proposta di restringimento |
| **Budget attributi esposti per entità** | **60** | Con le regole di §5.3 le entità ordinarie restano ampiamente sotto: `sale.order` scende da oltre 85 campi a poche decine. 60 non morde mai nel caso ordinario e impedisce che un'entità fortemente personalizzata entri per intero. L'indicatore *rifiuti per budget* (§6.4) dirà se il valore è sbagliato |

### 6.3 D26 — ritenzione confermata

Stati intermedi 30 giorni · Turni 12 mesi · Interrogazioni salvate illimitata · Registro 24 mesi. Con il vincolo di esecuzione di §5.3.

### 6.4 D20b e D20e — il pool si deriva, non si sceglie

RE4 osserva che il limite reale non è la CPU ma il **numero di connessioni PostgreSQL**: ogni thread del pool ne occupa una. L'osservazione è corretta e va resa normativa, perché un pool scelto a sentimento esaurisce le connessioni e il guasto si manifesta sull'ERP, non sul prodotto.

```
connessioni_totali  =  (worker_http × 1)
                     + (max_cron_threads × 1)
                     + (N_dispatcher × dimensione_pool)

vincolo:  connessioni_totali  ≤  0,8 × db_maxconn
```

Con i valori proposti — 4 worker HTTP, `max-cron-threads` 4, un dispatcher con pool 8 — servono circa 16 connessioni. Sono compatibili con qualunque configurazione ragionevole, ma il calcolo va rifatto a ogni aggiunta di dispatcher, e il margine del 20% va lasciato ai processi di servizio.

**La verifica appartiene alla prova di carico di §7.2**, come ottava riga della tabella.

### 6.5 D30 — dichiarare sette non è implementarne sette

Il vocabolario dei tipi di voce si chiude ora a sette, ed è giusto che si chiuda: C7 ammette estensioni additive, quindi chiudere presto non costa nulla e impedisce la proliferazione.

L'implementazione può essere progressiva. Per la Fase 1 sono necessari **T1** (denominazione), **T2** (valore enumerato), **T3** (risolutore di vaghezza) e **T5** (categoria): sono i tipi che il percorso di interrogazione attraversa. **T4** (metrica) diventa necessario quando si espongono le aggregazioni; **T6** e **T7** sono ottimizzazioni dell'esperienza.

La sequenza non è un rinvio con debito: aggiungere l'implementazione di un tipo già dichiarato è additivo per costruzione.

---

## 7. Le tre decisioni che restano aperte

Non sono deliberabili su base tecnica. Per ciascuna è però fissato **ciò che serve per chiuderla**, così che la decisione dell'Architect sia immediata anziché da istruire.

| # | Cosa manca | Requisiti fissati qui |
|---|---|---|
| **D6** | Nome commerciale | Prefisso tecnico **deciso: `nli_`**. Sul nome commerciale resta la raccomandazione di `04` §14.3: evitare *agent*, che descrive l'opposto di ciò che il prodotto è. Decisione di posizionamento, non di architettura |
| **D7** | Clienti pilota | **Almeno due clienti, di domini diversi; almeno uno con personalizzazioni rilevanti** — è l'unico modo di mettere sotto sforzo le regole di esposizione di D31; attività di riferimento elencate per iscritto; disponibilità a cedere richieste reali; **misura iniziale sull'interfaccia nativa eseguita prima dell'attivazione**, perché dopo non è più ottenibile |
| **D8** | Erogazione in ambiente controllato | Nessun ostacolo architetturale: A6 riduce il flusso a metadati ed enunciato, e l'Adattatore è già il solo punto di contatto. Decisione commerciale |

**D7 è il vero collo di bottiglia**: da essa dipendono la taratura di D12, D20e e D31, il corpus di Fase 0 e le soglie di D5. È l'unica delle tre che blocca lavoro tecnico.

Una nota su **D7** che vale più delle altre: la misura iniziale sull'interfaccia nativa va fatta **prima** che il prodotto sia attivo. È l'unico dato del progetto che non può essere ricostruito a posteriori, e senza di esso il KPI *"riduzione ≥ 80% del tempo di accesso"* non è misurabile — resterebbe un'affermazione.

---

## 8. Decisioni nuove

Tre lacune emerse leggendo i cinque documenti insieme. Nessuna è visibile dall'interno di un singolo documento: sono tutte interazioni fra documenti diversi.

### D39 — L'impronta dei permessi va calcolata, e deve fallire in sicurezza

**Origine.** `04` §7.6 include *"versione dei permessi"* nella chiave di memorizzazione del catalogo, e `04` §10.4 fonda su quella chiave una proprietà di sicurezza: due utenti condividono un'impronta di catalogo solo se hanno gli stessi permessi, quindi il riuso fra utenti non viola **V2**.

**Il problema.** Odoo non espone alcuna *versione dei permessi*. Non è un dato che esista: va costruito. E se viene costruito male, la proprietà di sicurezza su cui poggia il riuso fra utenti decade **senza alcun segnale** — un catalogo memorizzato prima di una revoca continuerebbe a esporre riferimenti che l'utente non deve più poter nominare.

**Decisione.** L'impronta dei permessi è un valore calcolato, composto da: gruppi dell'utente, stato delle regole di accesso ai modelli, stato delle regole sui record applicabili, configurazione degli accessi a livello di campo, e contesto societario (**D40**).

Due proprietà sono normative:

- **fallimento in sicurezza**: se l'impronta non è calcolabile, il catalogo viene ricostruito. Mai servito da memoria con impronta incerta;
- **l'invalidazione a evento di §7.6 resta**, ma è un'ottimizzazione: la correttezza dipende dall'impronta, non dalla notifica. Una notifica persa non deve poter produrre una violazione di V2.

**Stato:** ⊡ Adottata con vincolo — la ricostruzione dell'impronta è materia del documento 08 per la parte di autorizzazione.

### D40 — Il turno deve trasportare il contesto societario

**Origine.** Nessuno dei cinque documenti nomina il multi-società. La verifica è netta: zero occorrenze in `02`–`06`.

**Il problema.** In Odoo il perimetro dei record visibili dipende dalle società attive dell'utente, non solo dai suoi gruppi. Finché l'esecuzione avviene dentro la richiesta HTTP, quel contesto è presente e nessuno deve occuparsene. **Con D20a non lo è più**: l'esecuzione avviene su un processo cron, dove il contesto va ricostruito dal turno.

Un'esecuzione che ricostruisce l'utente ma non le sue società attive produce un risultato **plausibile e sbagliato**: gli stessi ordini che l'utente vedrebbe, più quelli di una società che nell'interfaccia aveva deselezionato. Nessun errore, nessun avviso, un numero diverso.

È la forma infrastrutturale di **R1**, ed è più insidiosa di quella linguistica: non deriva da un fraintendimento del linguaggio, quindi nessuna analisi dei fraintendimenti la troverebbe mai.

**Decisione.** Il turno persiste il contesto di esecuzione dell'utente al momento della richiesta — società attive, lingua, fuso orario — e l'esecuzione lo ripristina integralmente. Il contesto societario entra inoltre nella chiave del catalogo (**D39**) e nell'impronta usata per il riuso delle interpretazioni.

**Conseguenza sulle interrogazioni salvate.** Il contesto **non** viene congelato nello stato: un'interrogazione salvata eseguita domani da un utente con società diverse deve rendere ciò che quell'utente vede adesso, coerentemente con `04` §9.5. Il contesto appartiene all'esecuzione, mai alla domanda — è la stessa regola già applicata al tempo e ai permessi.

**Stato:** ☑ Adottata.

### D41 — Il catalogo si conserva deduplicato

**Origine.** D34 richiede la copertura come metrica di primo livello. Il calcolo è deterministico **perché il Registro conserva il catalogo fornito a ogni interazione** (`06` §6.2). Senza quella conservazione la copertura è ricostruibile solo per approssimazione, e un indicatore approssimato non può fare da soglia.

**Il problema.** Conservare un catalogo per turno significa scrivere alcune decine di attributi con termini e tipi a ogni interazione, e conservarli per i 24 mesi di D26. Su un'installazione attiva è la voce di crescita dominante del Registro — e la prima che qualcuno proporrà di eliminare, portandosi via D34 senza accorgersene.

**Decisione.** Il turno conserva l'**impronta** del catalogo; i cataloghi sono conservati una sola volta in una tabella indicizzata per impronta.

Il rapporto di deduplicazione è alto per costruzione: il catalogo cambia solo con il dizionario, i permessi, il contesto societario o l'aggiornamento dei moduli — eventi rari — mentre i turni sono continui. Migliaia di turni condividono la stessa impronta.

**La proprietà che si compra è che D34 resta sostenibile.** Una metrica di primo livello il cui costo cresce con l'uso viene disattivata al primo problema di spazio, e la disattivazione non sembra una decisione di prodotto — sembra manutenzione.

**Stato:** ☑ Adottata.

---

## 9. Cosa è vincolante da adesso

Riassunto operativo di ciò che le delibere impongono a chi scriverà il codice.

| Vincolo | Origine | Verificabile con |
|---|---|---|
| I quattro controlli dei confini esistono dalla prima consegna | D24 | Pipeline |
| Nessun percorso privilegiato, nemmeno nel dispatcher | D20a, V2 | Controllo sintattico di §6.4 |
| Il contesto societario viaggia sul turno | **D40** | Prova funzionale multi-società |
| Il catalogo non è mai servito con impronta incerta | **D39** | Prova di revoca permessi |
| Il catalogo è conservato deduplicato | **D41** | Ispezione dello schema del Registro |
| Il pool rispetta il tetto di connessioni | §6.4 | Ottava riga della prova di carico |
| I cron di business non subiscono starvation | D20b, V-B | Prova di §7.2 |
| Non si modificano dizionario e modello nello stesso rilascio | `06` §4.4 | Procedura di rilascio |
| La cancellazione per ritenzione gira sul dispatcher differito | D26 | Ispezione della configurazione cron |
| Il corpus sigillato è protetto da autorizzazione, non da consuetudine | **D42** | Prova di accesso negato |
| Nessun rapporto espone l'accuratezza senza la copertura | `07` §5.4 | Ispezione degli strumenti |
| Nessun dato personale entra nel corpus | **D47** | Controllo sull'inserimento |
| L'esecuzione del corpus gira sul dispatcher differito | `07` §14.2 | Ispezione della configurazione cron |

---

## 10. Procedura

**Per modificare una decisione adottata** serve una nuova decisione, non un emendamento. La voce originale resta, con lo stato aggiornato.

**Per superare una decisione**: `⊘ Superata da Dn`. Mai cancellata. Le quattro supersessioni già presenti sono la prova che la disciplina serve.

**Per aggiungere una decisione**: numerazione in continuità da **D54**.

**Vincoli aggiunti in delibera.** Le dodici decisioni marcate ⊡ portano una condizione che è parte della decisione: rimuoverla è modificare la decisione, non semplificarla.

---

## 11. Registro dei cambiamenti

| Data | Cambiamento |
|---|---|
| 2026-07-27 | Creazione del registro. Consolidate D1–D38 e D20a–D20f. Rilevate quattro supersessioni non tracciate. Nessuna decisione approvata. |
| 2026-07-27 | **Delibera.** 39 decisioni adottate, 11 con vincolo. Fissati i valori di D13 (80 / 500), D31 (budget 60), D5 (latenza scomposta in tre soglie), D26 (ritenzione confermata con esecuzione a lotti), D20e (4 processi cron entro il tetto di connessioni). Corretto il percorso di scala di D20f: N record dispatcher, non N istanze. Qualificata la portata di A6 sotto D3. Introdotte **D39** (impronta dei permessi), **D40** (contesto societario sul turno), **D41** (conservazione deduplicata del catalogo). Restano aperte D6 (parte commerciale), D7, D8. |
| 2026-07-27 | **Recepito `07-piano-valutazione-qualita.md`.** Adottate **D42–D53** (2 con vincolo). Corretti i conteggi della delibera precedente: le decisioni superate sono **cinque** (D16, D17, D20, D21, D22) in quattro eventi di supersessione, non quattro; le adottate erano 39 e non 38; le decisioni con vincolo 11 e non 9. **D52** è adottata ma non eseguibile finché **D7** resta aperta, ed è l'unica con una finestra che si chiude da sola. |

---

## 12. Giudizio complessivo

L'impianto regge, e regge per una ragione strutturale che vale la pena dichiarare: **le decisioni prese per correttezza producono, quasi ovunque, anche il comportamento più veloce e più semplice.**

Lo stato invece della cronologia (D4) è la scelta corretta contro la deriva ed è anche quella che mantiene il costo per turno costante. Il catalogo a tre fasi (D32) è la scelta corretta contro il tetto di accuratezza ed è anche quella che riduce latenza e costo. Il limite obbligatorio (D13) è una regola di contratto ed è anche la protezione della disponibilità. L'esecuzione asincrona (D20a) protegge l'ERP e rende l'attesa leggibile. Quando questo accade in modo sistematico, l'impianto non è un compromesso fra obiettivi in conflitto: è coerente.

Le tre lacune di §8 non contraddicono questo giudizio — lo confermano. Sono tutte e tre **interazioni fra documenti**, invisibili dall'interno di ciascuno: l'impronta dei permessi vive fra architettura e sicurezza, il contesto societario fra architettura ed esecuzione asincrona, la deduplicazione fra modello semantico e ritenzione. Nessuna è un errore di progettazione; tutte e tre sarebbero diventate difetti in produzione, e D40 sarebbe stata la più difficile da trovare, perché non produce errori.

Restano tre decisioni aperte, e una sola conta davvero: **D7**. Senza clienti pilota il corpus non esiste, e senza corpus il cancello di D2 non può essere aperto — il che significa che il prodotto può essere costruito ma non può crescere oltre la sola lettura. È il vincolo su cui vale la pena agire per primo, e non è un vincolo tecnico.
