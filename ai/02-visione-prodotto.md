# Visione del Prodotto e Specifica Concettuale
## AI Agent per Odoo

---

| Voce | Valore |
|---|---|
| **Titolo** | Visione del Prodotto e Specifica Concettuale – AI Agent per Odoo |
| **Versione** | 1.0 |
| **Data** | 26 luglio 2026 |
| **Stato** | Bozza sottoposta ad approvazione dell'Architect |
| **Classificazione** | Documento di riferimento di prodotto |
| **Destinatari** | Product Owner, Solution Architect, Software Architect, Team Leader, Sviluppatori, Stakeholder |
| **Ambito** | Visione, filosofia, obiettivi, ambito funzionale, roadmap, metriche |
| **Fuori ambito** | Architettura software, API, infrastruttura, database, sicurezza applicativa, definizione del DSL, implementazione |
| **Documenti collegati** | *(da produrre)* Specifica del DSL, Architettura di Sistema, Modello di Sicurezza, Piano di Valutazione della Qualità |

> **Nota di lettura.** Questo documento definisce *cosa* costruiamo e *perché*. Non definisce *come*. Ogni riferimento a componenti, flussi o tecnologie è puramente concettuale e non vincola le scelte architetturali, che saranno oggetto di documenti separati.

---

## 1. Executive Summary

### 1.1 Il problema

Odoo è un ERP potente e completo. La sua potenza è però accessibile soltanto a chi ne conosce la struttura: menu, viste, filtri, raggruppamenti, campi tecnici, relazioni fra modelli. L'utente che deve rispondere a una domanda di business — *"quali fatture sono scadute?"*, *"quali ordini ha chiuso Marco questo mese?"* — è costretto a tradurre da solo la propria intenzione in una sequenza di operazioni sull'interfaccia.

Questa traduzione ha un costo che oggi è invisibile perché distribuito su ogni utente, ogni giorno, per anni:

- una curva di apprendimento che rallenta ogni nuovo assunto;
- una dipendenza strutturale da pochi utenti esperti, che diventano colli di bottiglia organizzativi;
- un tasso di adozione parziale, in cui gran parte delle funzionalità dell'ERP resta inutilizzata perché non raggiungibile;
- un tempo di accesso all'informazione che si misura in minuti anziché in secondi.

### 1.2 La proposta

Introduciamo un **livello di interazione in linguaggio naturale** (*Natural Language Interaction Layer*, NLIL) sopra Odoo.

L'utente esprime la propria **intenzione**. Il sistema la interpreta, la traduce in un **DSL strutturato**, e il backend esegue quel DSL in modo **completamente deterministico** attraverso l'ORM di Odoo, aprendo una vista nativa contenente il risultato.

Il cambio di paradigma si riassume in una frase:

> **L'utente non deve più conoscere il software. Deve conoscere soltanto il proprio lavoro.**

### 1.3 Il principio non negoziabile

La componente di intelligenza artificiale **non esegue nulla**. Interpreta e basta.

L'unico artefatto che l'AI produce è un DSL: un contratto strutturato, validabile, ispezionabile e versionabile. Tutto ciò che accade dopo la produzione del DSL è deterministico, ripetibile e verificabile. Nessuna query è generata dall'AI. Nessun codice è generato dall'AI. Nessuna decisione di business è presa dall'AI.

Questo confine è la scelta di progetto più importante del prodotto ed è la ragione per cui il sistema può essere considerato affidabile in un contesto enterprise. Ogni futura evoluzione dovrà rispettarlo.

### 1.4 L'ambito della prima release

Deliberatamente minimo: **interrogazione conversazionale dei dati e visualizzazione dinamica dei risultati**. Nessuna scrittura, nessun workflow, nessuna automazione.

Questa limitazione non è una rinuncia: è la scelta di attraversare per primo il perimetro a rischio più basso — la sola lettura, protetta dai permessi dell'utente — per costruire in condizioni di sicurezza le fondamenta semantiche e di misura su cui poggeranno tutte le fasi successive.

### 1.5 Il vero asset del prodotto

Il modello linguistico è un componente sostituibile e commodizzato. Il valore difendibile del prodotto si accumula altrove, in tre asset proprietari:

1. **il Dizionario Semantico** — la mappa fra il linguaggio dell'azienda e la struttura dei dati;
2. **lo Stato di Interrogazione** — l'oggetto che rende la conversazione un'entità manipolabile, salvabile e condivisibile anziché una sequenza di messaggi;
3. **il Corpus di Valutazione** — l'insieme delle richieste reali con l'interpretazione corretta attesa, che consente di misurare la qualità e di cambiare modello senza perdere affidabilità.

Chi costruisce questi tre asset costruisce un prodotto. Chi costruisce soltanto un'integrazione con un modello linguistico costruisce una funzionalità replicabile in poche settimane.

### 1.6 Raccomandazione di sintesi

Il progetto è solido nella visione e correttamente delimitato nella prima release. Le raccomandazioni principali di questo documento, argomentate nelle sezioni dedicate, sono tre:

- **anteporre la misurabilità alla funzionalità**: nessun ampliamento d'ambito — in particolare nessuna operazione di scrittura — prima che esista un sistema di valutazione continua della qualità interpretativa (§15, §18.2);
- **rendere l'interpretazione sempre visibile e correggibile dall'utente**: l'affidabilità percepita non nasce dall'assenza di errori, ma dalla loro immediata riconoscibilità (§10.3, §16.1);
- **non esporre mai i dati aziendali al modello linguistico**: il modello riceve la frase dell'utente e i metadati di struttura, mai il contenuto dei record (§11.4, §18.5).

---

## 2. Visione del Prodotto

### 2.1 Dichiarazione di visione

> Trasformare Odoo da sistema che l'utente deve **imparare** a sistema con cui l'utente può semplicemente **parlare**, senza sacrificare un grammo di determinismo, controllo e affidabilità.

### 2.2 Il cambio di paradigma

L'interazione con un ERP ha attraversato tre generazioni:

| Generazione | Modello di interazione | Cosa deve sapere l'utente |
|---|---|---|
| **Prima** | Terminale e codici transazione | La sintassi del sistema |
| **Seconda** | Interfaccia grafica: menu, form, filtri | La struttura del sistema |
| **Terza** *(proposta)* | Espressione dell'intenzione | Il proprio lavoro |

Il salto della terza generazione non consiste nell'aggiungere una chat a un ERP. Consiste nello **spostare l'onere della traduzione**: oggi è l'utente a tradurre la propria intenzione in operazioni; domani è il sistema a tradurre l'intenzione in operazioni, e l'utente rimane l'unico titolare della decisione.

### 2.3 Cosa cambia concretamente

**Oggi.** L'utente vuole vedere gli ordini confermati del mese, per venditore. Apre il modulo Vendite, sceglie la vista lista, apre il pannello dei filtri, cerca il filtro sullo stato, applica il periodo, apre i raggruppamenti, seleziona il venditore, aggiunge le colonne mancanti dall'elenco dei campi opzionali. Otto o dieci interazioni, ciascuna delle quali richiede di sapere *dove* si trova il comando.

**Domani.** L'utente scrive: *"ordini confermati di questo mese, raggruppati per venditore"*. Il sistema apre la vista corrispondente, mostrando in chiaro come ha interpretato la richiesta. L'utente aggiunge: *"fammi vedere anche l'importo"*. La vista si aggiorna.

### 2.4 Indipendenza dal canale

La chat è il primo canale, non il prodotto.

Il motore di comprensione è progettato come componente **indipendente dal canale**: riceve un'intenzione espressa in linguaggio naturale e un contesto, restituisce un DSL. Non conosce il mezzo attraverso cui l'intenzione è arrivata.

Questa separazione consente di abilitare progressivamente, senza riscrivere il cuore del sistema:

- chat integrata in Odoo (canale di riferimento della prima release);
- voce;
- applicazione mobile;
- Microsoft Teams e Slack;
- email;
- API per integrazioni di terze parti;
- interfacce multimodali.

Il canale determina *come* l'intenzione viene raccolta e *come* il risultato viene presentato. Non determina *come* viene compresa.

### 2.5 Ciò che il prodotto **non** è

Chiarire i confini vale quanto dichiarare gli obiettivi.

| Non è | Perché è importante dirlo |
|---|---|
| Una chatbot | L'obiettivo non è conversare, ma raggiungere un risultato operativo nel minor numero di passi |
| Un assistente generico | Il dominio è l'ERP dell'azienda; non risponde a domande di cultura generale |
| Un sistema che decide | Non interpreta politiche aziendali, non sceglie al posto dell'utente, non agisce senza richiesta |
| Un generatore di codice o di query | Non produce Python, non produce SQL, non produce domain arbitrari: produce esclusivamente DSL validato |
| Un sostituto dell'interfaccia Odoo | È un livello **additivo**: l'interfaccia nativa resta pienamente disponibile e autorevole |
| Un motore di business logic | La logica di business resta interamente in Odoo, dove è già validata |

### 2.6 Orizzonte decennale

Il prodotto è concepito per evolvere per almeno dieci anni. Ciò impone due conseguenze immediate sulla visione:

- **il modello linguistico deve essere sostituibile**. I modelli si evolvono su cicli di mesi; il prodotto su cicli di anni. Nessuna scelta di prodotto può presupporre uno specifico fornitore o una specifica generazione di modelli;
- **il DSL è il vero contratto di lungo periodo**. Sopravvive ai modelli, ai canali e alle interfacce. Merita perciò la cura progettuale che si riserva a un formato pubblico e a un'estensione retrocompatibile.

---

## 3. Missione

### 3.1 Dichiarazione di missione

> Ridurre a zero la distanza fra ciò che una persona vuole sapere dal proprio ERP e ciò che deve fare per saperlo, mantenendo l'esecuzione interamente deterministica, tracciabile e soggetta ai permessi dell'utente.

### 3.2 Le tre promesse

La missione si articola in tre promesse verso categorie diverse di destinatari, tutte e tre da mantenere simultaneamente.

**Verso l'utente finale — *"non devi imparare il software"*.**
Chi lavora deve poter esprimere ciò che gli serve con le parole che userebbe con un collega, e ottenerlo. Errori di battitura, abbreviazioni, gergo aziendale e frasi incomplete sono parte normale del linguaggio, non eccezioni da gestire.

**Verso l'azienda — *"il sistema non ti sorprende"*.**
Ogni interpretazione è visibile, ogni esecuzione è deterministica, ogni accesso rispetta i permessi già configurati in Odoo. Il sistema non introduce nuove strade per raggiungere dati che l'utente non è autorizzato a vedere.

**Verso il team di prodotto — *"la complessità resta piccola e circoscritta"*.**
La componente non deterministica è la più piccola possibile e ha un unico punto di ingresso e un unico punto di uscita. Tutto il resto del sistema è software tradizionale, testabile con strumenti tradizionali.

### 3.3 Il criterio di decisione permanente

Ogni futura decisione di prodotto sarà valutata con la stessa domanda:

> *Questa scelta riduce ciò che l'utente deve sapere, senza aumentare ciò che il sistema può fare di imprevedibile?*

Se una funzionalità semplifica la vita dell'utente ma allarga la superficie di comportamento non deterministico, va riprogettata o rinviata. Se una funzionalità allarga le capacità del sistema senza ridurre il carico cognitivo dell'utente, non appartiene a questo prodotto.

---

## 4. Filosofia del Prodotto

### 4.1 L'AI come livello di traduzione, non come motore

L'errore più comune nei prodotti che uniscono AI e sistemi gestionali è affidare al modello linguistico l'esecuzione. Il modello genera una query, la query viene eseguita, il risultato viene mostrato. È un'architettura che funziona nelle dimostrazioni e fallisce in produzione, per una ragione strutturale: un componente probabilistico viene messo in una posizione dove il sistema richiede garanzie.

La nostra impostazione è opposta. Il modello occupa la sola posizione in cui la sua natura probabilistica è accettabile: la **comprensione dell'intenzione**. Da lì in poi, il sistema è software convenzionale.

```
 intenzione        interpretazione        contratto        esecuzione        risultato
 (linguaggio  →   (componente AI)    →     (DSL)      →  (deterministica) →  (vista
  naturale)         probabilistica        validato         Odoo/ORM          nativa)
                          ↑                    ↑                ↑
                  unico punto non      confine di        permessi utente
                   deterministico      validazione        sempre applicati
```

Da questo schema discendono tre proprietà che definiscono il prodotto.

**Il DSL è un confine di validazione.** Ciò che il modello produce non viene eseguito: viene prima validato. Un DSL sintatticamente o semanticamente non valido non arriva mai al motore di esecuzione. L'errore del modello diventa quindi un errore *gestibile* — una richiesta di chiarimento all'utente — anziché un comportamento inatteso del sistema.

**Il DSL è il contratto fra due mondi.** A monte può cambiare tutto: modello, fornitore, prompt, lingua, canale. A valle può cambiare tutto: versione di Odoo, moduli installati, tipologie di vista. Il DSL è la superficie stabile che permette a entrambi i lati di evolvere in autonomia.

**Il DSL è il perimetro delle capacità.** Il sistema può fare esattamente ciò che il DSL sa esprimere: né più né meno. L'ampliamento delle capacità è quindi un atto deliberato di progettazione, non una conseguenza emergente delle capacità di un modello. Nella prima release il DSL è espressivo solo in lettura: l'impossibilità di scrivere non è un divieto imposto al modello, è una proprietà strutturale del contratto.

### 4.2 Il paradosso dell'affidabilità

Un sistema in linguaggio naturale non può essere accurato al cento per cento. La lingua è ambigua per costruzione: *"gli ordini di Rossi"* può significare gli ordini del cliente Rossi o quelli del venditore Rossi, e nessun sistema — né umano né artificiale — può risolvere l'ambiguità senza contesto.

Da qui una considerazione centrale per il prodotto: **l'affidabilità percepita non nasce dall'assenza di errori, ma dalla loro immediata riconoscibilità e correggibilità.**

Il rischio più grave non è la richiesta fraintesa in modo evidente — l'utente se ne accorge e riformula. Il rischio grave è la richiesta fraintesa in modo **plausibile**: un filtro leggermente diverso da quello inteso, un periodo che parte dal giorno sbagliato, un raggruppamento su un campo omonimo. Il risultato appare corretto, viene esportato, finisce in una riunione, sostiene una decisione.

La risposta di prodotto è il principio di **interpretazione ispezionabile**: il sistema mostra sempre, in forma leggibile e in un linguaggio non tecnico, come ha compreso la richiesta. L'utente non deve fidarsi: deve poter verificare in un colpo d'occhio. Questo principio non è una funzionalità dell'interfaccia, è un requisito di correttezza del prodotto.

### 4.3 La conversazione modifica un oggetto, non produce testo

Una conversazione operativa non è uno scambio di messaggi: è la **raffinazione progressiva di un risultato**.

> *"Mostrami tutti i clienti"* → *"solo quelli attivi"* → *"ordina per città"* → *"mostrami anche il telefono"* → *"apri il primo"*

Trattare questa sequenza come una cronologia di testo da rileggere ad ogni turno è inefficiente, fragile e costoso: il contesto cresce senza limite, l'ambiguità si accumula, il costo per turno aumenta e la qualità degrada man mano che la conversazione si allunga.

Adottiamo un modello concettuale diverso. Esiste un oggetto — lo **Stato di Interrogazione** — che rappresenta in ogni istante *cosa l'utente sta guardando*: entità, filtri, campi, ordinamento, raggruppamenti, tipo di vista. Ogni frase dell'utente è un'**operazione di modifica** su questo oggetto. La conversazione è la storia delle modifiche; lo stato è il risultato.

Le conseguenze si estendono ben oltre l'efficienza:

- il modello riceve un contesto **compatto e strutturato** anziché una cronologia crescente: qualità stabile e costo costante anche nelle conversazioni lunghe;
- diventa naturale **annullare** l'ultima modifica: l'utente può sbagliare senza timore;
- il risultato diventa **salvabile e condivisibile**: uno stato è un oggetto, non una chat, quindi può diventare un filtro preferito, un collegamento inviato a un collega, una vista ricorrente;
- diventa possibile **riprendere** un'interrogazione a distanza di giorni, da un canale diverso da quello di origine;
- l'intera esecuzione diventa **riproducibile**: dato uno stato, il risultato è sempre lo stesso.

Questa è una decisione concettuale, non implementativa, e va assunta in fase di visione perché condiziona ogni fase successiva della roadmap.

### 4.4 Il linguaggio dell'azienda è un asset, non un dettaglio

Ogni azienda parla la propria lingua. *"Le pratiche"* sono ordini di vendita in un'azienda e progetti in un'altra. *"Il fatturato del trimestre"* può includere o escludere le note di credito a seconda della prassi contabile interna. *"Cliente strategico"* è una categoria che esiste nella testa del commerciale e in un campo personalizzato del database.

Nessun modello linguistico può conoscere questo lessico: non è pubblico, non è documentato e cambia da installazione a installazione.

Il prodotto deve quindi possedere un **Dizionario Semantico** per ciascun cliente: la mappa curata e versionata fra il linguaggio dell'organizzazione e la struttura dei suoi dati. Comprende sinonimi, abbreviazioni, gergo, metriche aziendali, categorie implicite e convenzioni temporali.

Due implicazioni strategiche:

- **è il fossato competitivo**. Il dizionario si costruisce con l'uso e diventa progressivamente più preciso. Un concorrente può replicare l'integrazione con un modello in poche settimane; non può replicare due anni di dizionario affinato sui dati di un cliente specifico;
- **è un onere di adozione**. Un nuovo cliente parte con un dizionario vuoto e quindi con la qualità più bassa che sperimenterà mai. Il prodotto deve prevedere fin dall'inizio la costruzione assistita del dizionario e la sua crescita automatica a partire dall'uso reale.

### 4.5 Degradare con dignità

Il sistema dipende da un componente esterno e non deterministico. Deve quindi essere progettato per il momento in cui quel componente non risponde, risponde lentamente o risponde male.

Tre regole di comportamento:

- **quando non capisce, chiede**. Non indovina. Una domanda di chiarimento specifica (*"Rossi è il cliente o il venditore?"*) è un'esperienza migliore di una risposta sbagliata;
- **quando non è disponibile, il lavoro continua**. L'indisponibilità del livello di comprensione non deve impedire l'uso di Odoo né l'esecuzione di interrogazioni già salvate: sono deterministiche e non richiedono il modello;
- **quando è incerto, lo dichiara**. Un'interpretazione a bassa confidenza va segnalata come tale, non presentata con la stessa autorevolezza di una certa.

### 4.6 Additivo, mai sostitutivo

Il fallimento tipico dei prodotti conversazionali applicati al software gestionale è di essere costruiti come un'interfaccia parallela: una finestra separata che l'utente prova due volte e poi smette di aprire, perché tornare all'interfaccia che già conosce è sempre più veloce che imparare a fidarsi di quella nuova.

Il prodotto deve quindi essere **incorporato nel flusso di lavoro esistente**, non affiancato ad esso. Il risultato di un'interrogazione non è un blocco di testo dentro una chat: è una **vista Odoo nativa**, con tutti gli strumenti che l'utente già conosce — filtri, esportazione, azioni, apertura del record. Il linguaggio naturale sostituisce la fatica di *arrivare* alla vista, non la vista.

Questa scelta ha un ulteriore vantaggio: rende il prodotto immediatamente utile anche quando l'interpretazione è imperfetta. Se il sistema porta l'utente al 90% del risultato, l'utente completa il restante 10% con gli strumenti nativi. Il valore non è tutto-o-niente.

---

## 5. Principi Guida

Gli otto principi seguenti sono ordinati per priorità. In caso di conflitto, il principio di rango superiore prevale. L'ordine è esso stesso una decisione di prodotto: dichiara che preferiamo un sistema che fa poche cose in modo impeccabile a uno che ne fa molte in modo incerto.

### P1 — Determinismo dell'esecuzione
Nessuna operazione sui dati è prodotta da un componente probabilistico. L'AI produce esclusivamente un DSL; il DSL viene validato; l'esecuzione è deterministica e ripetibile. A parità di DSL, il risultato è sempre identico.
*Conseguenza operativa:* qualunque proposta che preveda l'esecuzione diretta di output generativo è respinta a prescindere dai benefici funzionali.

### P2 — Rispetto integrale del modello di sicurezza di Odoo
Il livello conversazionale non è mai una via privilegiata di accesso ai dati. Ogni esecuzione avviene con l'identità e i permessi dell'utente richiedente. Se un dato non è visibile nell'interfaccia nativa, non è visibile nemmeno tramite conversazione.
*Conseguenza operativa:* nessuna cache condivisa fra utenti di risultati contenenti dati; nessuna esecuzione con privilegi elevati per "comodità".

### P3 — Interpretazione ispezionabile
Il sistema mostra sempre come ha compreso la richiesta, in forma leggibile da chi non conosce la struttura dei dati. L'utente deve poter riconoscere un fraintendimento senza analizzare i risultati.
*Conseguenza operativa:* nessun risultato è presentato senza la sua interpretazione; la comprensibilità dell'interpretazione è un criterio di accettazione, non un dettaglio estetico.

### P4 — Minimalità della componente AI
La superficie non deterministica è ridotta al minimo indispensabile. Ogni volta che una capacità può essere ottenuta in modo deterministico, lo è.
*Conseguenza operativa:* di fronte a due soluzioni equivalenti, si sceglie quella che chiede meno al modello.

### P5 — Indipendenza dal canale
Il motore di comprensione non conosce il mezzo. Nessuna logica di comprensione è duplicata o specializzata per canale.
*Conseguenza operativa:* un requisito che vale solo per la chat non entra nel motore; entra nell'adattatore del canale.

### P6 — Indipendenza dal fornitore del modello
Nessuna capacità di prodotto dipende da caratteristiche esclusive di un singolo fornitore o di una singola generazione di modelli. Il modello è un componente sostituibile.
*Conseguenza operativa:* la sostituzione del modello deve essere una decisione operativa misurabile, non un progetto di migrazione.

### P7 — Il valore si misura in risultati, non in conversazioni
Il successo è l'utente che ottiene ciò che cercava nel minor numero di passi. Una conversazione più lunga è un peggioramento, non un miglioramento dell'ingaggio.
*Conseguenza operativa:* le metriche di prodotto premiano la risoluzione al primo tentativo, non il volume di messaggi.

### P8 — Evoluzione senza rotture
Il DSL e lo Stato di Interrogazione sono contratti versionati ed estesi in modo retrocompatibile. Le interrogazioni salvate oggi devono funzionare fra cinque anni.
*Conseguenza operativa:* ogni estensione del contratto è additiva; le rimozioni seguono un ciclo di deprecazione dichiarato.

---

## 6. Obiettivi Strategici

Gli obiettivi sono espressi in forma verificabile. I valori numerici sono proposte di riferimento da confermare con l'Architect e da ricalibrare sul primo corpus di richieste reali (§17.5).

### OS1 — Azzerare la distanza fra intenzione e risultato
Portare l'utente dalla domanda al dato in una singola espressione in linguaggio naturale, per le richieste ricorrenti che oggi costano più interazioni.
*Traguardo di riferimento:* riduzione dell'80% del tempo medio di accesso all'informazione sui casi d'uso frequenti, rispetto alla misurazione iniziale sull'interfaccia nativa.

### OS2 — Rendere l'ERP accessibile a chi non lo conosce
Consentire a un utente senza formazione specifica di ottenere informazioni corrette entro il primo giorno di utilizzo.
*Traguardo di riferimento:* un nuovo utente completa correttamente un insieme di attività di riferimento senza formazione preliminare sull'interfaccia.

### OS3 — Costruire una comprensione affidabile e misurabile
Ottenere e mantenere un'accuratezza interpretativa verificata su un corpus di valutazione rappresentativo, con misura continua e non aneddotica.
*Traguardo di riferimento:* ≥ 90% di interpretazioni corrette al primo tentativo sul corpus di valutazione, con nessuna regressione ammessa fra rilasci.

### OS4 — Eliminare la dipendenza dagli utenti esperti
Ridurre il numero di richieste informative inoltrate ai key user interni e ai consulenti.
*Traguardo di riferimento:* riduzione misurabile delle richieste interne di estrazione dati, rilevata presso i clienti pilota.

### OS5 — Costruire una piattaforma, non una funzionalità
Chiudere la prima release con un motore già indipendente dal canale e dal fornitore del modello, e con i tre asset proprietari (§1.5) avviati.
*Traguardo di riferimento:* aggiunta di un secondo canale senza modifiche al motore di comprensione; sostituzione del modello con misura di impatto in meno di una settimana.

### OS6 — Meritare la fiducia dell'organizzazione
Assicurare che ogni interpretazione sia visibile, ogni esecuzione tracciabile e ogni accesso conforme ai permessi esistenti.
*Traguardo di riferimento:* zero incidenti di accesso a dati non autorizzati; tracciabilità completa di ogni interrogazione eseguita.

---

## 7. Valore per il Business

### 7.1 Dove si genera il valore

Il valore non nasce dalla novità tecnologica. Nasce dall'eliminazione di un costo ricorrente, oggi invisibile perché frammentato su ogni utente e ogni giorno.

| Dimensione | Situazione attuale | Situazione attesa | Beneficiario |
|---|---|---|---|
| **Tempo di ricerca** | Minuti per ogni informazione non presente nelle viste predefinite | Secondi | Ogni utente, ogni giorno |
| **Curva di apprendimento** | Settimane per operare con autonomia | Ore | Nuovi assunti, personale stagionale |
| **Dipendenza da esperti** | Interruzioni continue dei key user | Autonomia dell'utente finale | Key user, IT interno |
| **Adozione dell'ERP** | Funzionalità inutilizzate perché non raggiungibili | Superficie realmente accessibile | Direzione, sponsor del progetto |
| **Qualità delle decisioni** | Decisioni prese senza consultare il dato, perché costa troppo ottenerlo | Dato disponibile nel momento in cui serve | Management |
| **Costo di formazione** | Sessioni ricorrenti su come usare il software | Formazione sul processo, non sullo strumento | HR, direzione operativa |

### 7.2 Il valore nascosto: le domande che oggi nessuno pone

L'effetto più rilevante non è rendere più veloci le domande che già si pongono, ma rendere possibili quelle che oggi non si pongono affatto.

Quando ottenere un dato costa cinque minuti e la conoscenza di dove cercarlo, la maggior parte delle domande legittime non viene formulata: si decide a intuito, si rimanda, si chiede a qualcun altro. Abbassando il costo marginale della domanda quasi a zero, cambia la frequenza con cui l'organizzazione consulta i propri dati. È un cambiamento di comportamento, non di prestazione.

Questo valore è reale ma difficile da misurare direttamente: va rilevato attraverso indicatori indiretti (§17.3), in particolare la crescita del numero di interrogazioni per utente attivo e l'ampliamento dell'insieme di modelli Odoo effettivamente interrogati.

### 7.3 Valore per profilo

**Utente operativo.** Smette di essere rallentato dallo strumento. Ottiene ciò che gli serve con le parole che già usa.

**Responsabile di funzione.** Ottiene risposte immediate senza dipendere dall'IT o dai key user, e può verificare l'interpretazione prima di fidarsi del dato.

**Direzione.** Aumenta il ritorno sull'investimento già sostenuto in Odoo: le funzionalità pagate diventano effettivamente accessibili.

**IT interno e partner implementatore.** Riduce il carico di richieste di estrazione dati e di formazione ricorrente, e riduce la proliferazione di viste e filtri personalizzati creati per esigenze temporanee.

**Chi vende il prodotto.** Ottiene un elemento di differenziazione dimostrabile in pochi secondi durante una presentazione, su dati reali del cliente.

### 7.4 Costi e condizioni da considerare

Un documento di visione onesto dichiara anche il lato passivo del bilancio.

- **Costo variabile per interazione.** Ogni richiesta interpretata ha un costo unitario. Il modello economico del prodotto deve reggere alla crescita d'uso: è una condizione di sostenibilità, non un dettaglio operativo (§16.6).
- **Costo di attivazione per cliente.** La costruzione iniziale del Dizionario Semantico richiede lavoro di configurazione. Va previsto nel modello di erogazione, altrimenti il primo giorno di ogni cliente coincide con la peggiore qualità percepita.
- **Costo di fiducia.** La fiducia si perde più rapidamente di quanto si costruisca. Alcuni errori evidenti nelle prime settimane di adozione hanno un impatto sull'adozione superiore a mesi di funzionamento corretto. Questo è il motivo per cui la prudenza sull'ampliamento d'ambito (§15) è una scelta di business, non solo tecnica.

---

## 8. Ambito della Prima Release

### 8.1 Dichiarazione di ambito

> La prima release consente all'utente di **interrogare** i dati di Odoo in linguaggio naturale, attraverso una conversazione, e di ottenere il risultato in una **vista Odoo nativa generata dinamicamente**.

Nient'altro.

### 8.2 Perché un ambito così ristretto

La restrizione è deliberata e risponde a quattro ragioni.

**Il rischio è minimo.** La sola lettura, eseguita con i permessi dell'utente, non può danneggiare i dati. Un fraintendimento produce un risultato sbagliato, non un danno permanente. È il perimetro corretto per far maturare un componente probabilistico.

**Il valore è già pieno.** L'interrogazione è ciò che gli utenti fanno più spesso. Un prodotto che risolve solo questo risolve già la parte maggiore del problema quotidiano.

**La misura è possibile.** Su un ambito ristretto si può costruire un corpus di valutazione rappresentativo e sapere davvero quanto il sistema è accurato. È il prerequisito indispensabile per autorizzare, più avanti, qualunque operazione di scrittura.

**Il contratto si stabilizza.** Il DSL, lo Stato di Interrogazione e il Dizionario Semantico devono assestarsi su un dominio limitato prima di essere estesi. Estendere un contratto instabile è la via più rapida al debito tecnico.

### 8.3 Incluso nella prima release

| Area | Contenuto |
|---|---|
| **Canale** | Chat integrata nell'interfaccia Odoo |
| **Comprensione** | Linguaggio naturale, colloquiale, con errori ortografici, abbreviazioni, sinonimi, frasi incomplete; multilingua |
| **Contesto** | Conversazione multi-turno con raffinamento progressivo dello Stato di Interrogazione |
| **Interrogazione** | Selezione dell'entità, filtri, ordinamenti, raggruppamenti, limiti, selezione dei campi visualizzati |
| **Viste** | Generazione dinamica di Lista, Kanban, Calendario, Pivot, Grafico; apertura del singolo record |
| **Trasparenza** | Interpretazione sempre visibile e comprensibile; segnalazione dei casi ambigui |
| **Disambiguazione** | Richiesta di chiarimento quando la richiesta è ambigua o la confidenza è bassa |
| **Semantica** | Dizionario Semantico di base per installazione, alimentabile dall'uso |
| **Qualità** | Corpus di valutazione e misurazione continua dell'accuratezza interpretativa |
| **Tracciabilità** | Registrazione di ogni richiesta, interpretazione ed esecuzione |

### 8.4 Escluso dalla prima release

| Escluso | Motivazione |
|---|---|
| Creazione, modifica, eliminazione di record | Richiede un livello di affidabilità dimostrato, non presunto |
| Workflow e automazioni | Comportano effetti che si propagano oltre la sessione dell'utente |
| Generazione di codice Python | Viola il principio di determinismo (P1) |
| Generazione di SQL | Aggirerebbe l'ORM e con esso il modello di sicurezza (P2) |
| Logiche di business generate | La logica di business appartiene a Odoo |
| Canali diversi dalla chat Odoo | Rinviati; l'architettura deve però già consentirli senza modifiche al motore |
| Interazione vocale | Fase successiva; nessun impatto sul motore di comprensione |
| Dashboard e report generati | Richiedono capacità analitiche più ampie del DSL di prima release |
| Suggerimenti proattivi | Il sistema risponde, non anticipa: coerente con §2.5 |

### 8.5 Criteri di completamento della prima release

La release si considera completa quando tutte le condizioni seguenti sono verificate:

1. un utente senza formazione ottiene correttamente il risultato atteso su un insieme di attività di riferimento definito con i clienti pilota;
2. l'accuratezza interpretativa misurata sul corpus di valutazione raggiunge la soglia stabilita (§6, OS3);
3. ogni risultato è accompagnato dall'interpretazione in forma comprensibile a un utente non tecnico;
4. le richieste ambigue producono una domanda di chiarimento, non un'ipotesi silenziosa;
5. nessun percorso consente l'accesso a dati che l'utente non vedrebbe nell'interfaccia nativa;
6. l'indisponibilità del modello non impedisce l'uso di Odoo né l'esecuzione di interrogazioni salvate;
7. le prestazioni percepite rientrano nella soglia definita (§17.2);
8. l'aggiunta di un secondo canale non richiede modifiche al motore di comprensione (verifica documentale o prototipale).

---

## 9. Funzionalità Attese

### 9.1 Le sei capacità della prima release

**F1 — Interrogazione in linguaggio naturale.**
L'utente esprime cosa vuole vedere; il sistema individua l'entità pertinente e le condizioni implicite nella frase.
> *"Mostrami gli ultimi cinque ordini"* · *"Mostra solo le fatture scadute"* · *"Le auto con circa centomila chilometri"*

**F2 — Raffinamento conversazionale.**
Ogni frase successiva modifica il risultato corrente, senza che l'utente debba ripetere il contesto.
> *"Fammi vedere solo quelli confermati"* · *"Ordina per data"* · *"Mostra solamente quelli di questo mese"*

**F3 — Controllo dei campi visualizzati.**
L'utente decide cosa vedere, usando i nomi che conosce, non i nomi tecnici dei campi.
> *"Visualizza cliente, commerciale e importo"* · *"Fammi vedere solamente Nome, Email e Telefono"* · *"Mostrami anche il telefono"*

**F4 — Aggregazione e organizzazione.**
Raggruppamenti e ordinamenti espressi in linguaggio naturale.
> *"Raggruppa per venditore"* · *"Ordina per città"*

**F5 — Scelta della rappresentazione.**
L'utente sceglie come vedere il risultato; in assenza di indicazione, il sistema propone la rappresentazione più adatta alla forma del dato.
> *"Visualizza il risultato in Kanban"* · *"Fammelo vedere come grafico"*

**F6 — Navigazione al record.**
Passaggio dall'insieme al singolo elemento, restando nella conversazione.
> *"Apri il primo"* · *"Apri quello di Rossi"*

### 9.2 Generazione dinamica delle viste

È una delle capacità distintive del prodotto e merita una trattazione a sé.

Oggi ogni vista Odoo è un artefatto progettato in anticipo: qualcuno ha deciso quali colonne mostrare, in quale ordine, con quali filtri predefiniti. Quando l'esigenza dell'utente si discosta da quella previsione, l'utente adatta manualmente la vista oppure chiede una personalizzazione.

Il prodotto costruisce la vista **a partire dall'intenzione**, senza configurazione preventiva:

- **quali colonne** mostrare e quali nascondere;
- **come ordinare** e **come raggruppare**;
- **quanti record** presentare;
- **quale tipo di vista** utilizzare fra Lista, Kanban, Calendario, Pivot e Grafico.

Tre requisiti governano questa capacità.

**Deve restare una vista Odoo autentica.** Non una tabella riprodotta dentro una chat, ma la vista nativa con tutte le sue funzioni: esportazione, filtri aggiuntivi, azioni, apertura del record. È ciò che rende il prodotto additivo (§4.6).

**La scelta implicita deve essere prevedibile.** Quando l'utente non specifica il tipo di vista, la scelta del sistema deve seguire regole dichiarate e stabili — ad esempio: una dimensione temporale suggerisce il Calendario, un'aggregazione numerica suggerisce Pivot o Grafico, in assenza di segnali si usa la Lista. Regole deterministiche, non una decisione del modello: è un'applicazione diretta del principio P4.

**La vista deve essere conservabile.** Un risultato ottenuto conversando deve poter diventare un oggetto riutilizzabile — un preferito, un collegamento condiviso, una vista ricorrente — altrimenti ogni interrogazione utile va ricostruita da capo, e il valore si disperde.

### 9.3 Comprensione delle espressioni vaghe

Alcune richieste contengono termini intrinsecamente imprecisi: *"circa centomila chilometri"*, *"gli ordini recenti"*, *"i clienti importanti"*, *"questo mese"*.

Il sistema deve gestirle, ma il principio P1 impone che la loro risoluzione sia **deterministica e dichiarata**, non improvvisata dal modello ad ogni richiesta. *"Circa centomila"* deve significare sempre la stessa cosa, e quella cosa deve essere visibile all'utente e modificabile.

Il comportamento richiesto è duplice: applicare una regola nota (definita nel Dizionario Semantico e, se necessario, configurabile per cliente) e **mostrare la regola applicata** nell'interpretazione, così che l'utente possa correggerla immediatamente (*"no, esattamente centomila"*).

Una vaghezza risolta in modo diverso ad ogni richiesta produrrebbe un sistema imprevedibile: sarebbe una violazione dei principi P1 e P3, non una funzionalità intelligente.

### 9.4 Gestione dell'ambiguità

Quando la richiesta ammette più interpretazioni plausibili, il sistema **chiede**. Non sceglie.

> Utente: *"gli ordini di Rossi"*
> Sistema: *"Rossi come cliente o come venditore?"*

La domanda deve essere specifica e a scelta chiusa quando possibile: costa all'utente un istante, mentre un fraintendimento costa fiducia. Le disambiguazioni ripetute con lo stesso esito sono, inoltre, la fonte più preziosa di alimentazione automatica del Dizionario Semantico.

### 9.5 Comportamento in caso di risultato vuoto

Un risultato vuoto è uno dei momenti più delicati: l'utente non sa se il dato non esiste o se il sistema ha frainteso.

Il sistema deve distinguere e comunicare i due casi: *"non ci sono fatture scadute"* è un'informazione; *"non ho trovato nulla"* è un'ambiguità irrisolta. Nel secondo caso deve proporre la strada per procedere, ad esempio suggerendo di rimuovere la condizione più restrittiva.

---

## 10. Esperienza Utente

### 10.1 Il principio dell'esperienza

> L'utente deve potersi esprimere come farebbe parlando con un collega competente — e ottenere la stessa cosa che otterrebbe da quel collega: il risultato, più la certezza di aver capito la stessa cosa.

### 10.2 Cosa il sistema deve accettare

Il linguaggio reale non è quello dei manuali. Il sistema deve trattare come normali, non come eccezioni:

| Fenomeno | Esempio |
|---|---|
| Errori ortografici | *"mostrami le fatuere scadute"* |
| Abbreviazioni | *"ord. confermati di gen"* |
| Gergo aziendale | *"le pratiche aperte"* |
| Sinonimi | *"clienti"*, *"anagrafiche"*, *"contatti"* |
| Frasi incomplete | *"solo quelli attivi"* |
| Deissi e riferimenti | *"apri il primo"*, *"anche il telefono"* |
| Mescolanza di lingue | *"mostrami i deal in stage negotiation"* |
| Registro colloquiale | *"fammi un po' vedere chi non ha pagato"* |

### 10.3 Cosa l'utente non deve conoscere

Nessuna competenza sui modelli Odoo, sui campi tecnici, sull'ORM, sui domain, su SQL, su XML o sulla struttura del database.

Questo vincolo ha una conseguenza diretta e spesso trascurata sull'interpretazione ispezionabile (P3): **anche l'interpretazione deve essere espressa in linguaggio umano**. Mostrare all'utente un'espressione tecnica equivarrebbe a non mostrare nulla. L'interpretazione corretta è del tipo:

> Sto mostrando: **Ordini di vendita** · confermati · di **luglio 2026** · raggruppati per **venditore** · ordinati per data · primi 5

Ogni elemento dell'interpretazione deve inoltre essere **direttamente correggibile**: rimuovere una condizione senza dover riformulare l'intera frase è ciò che rende il fraintendimento un inconveniente da due secondi anziché una ragione per abbandonare lo strumento.

### 10.4 Il flusso di riferimento

```
1. L'utente scrive           "mostrami tutti i clienti"
2. Il sistema interpreta      → Contatti, tipo cliente
3. Il sistema mostra          Interpretazione visibile + vista Lista nativa
4. L'utente raffina           "solo quelli attivi"
5. Lo stato si aggiorna       Interpretazione aggiornata + vista aggiornata
6. L'utente prosegue          "ordina per città" → "mostrami anche il telefono"
7. L'utente conclude          "apri il primo" → record aperto in vista form
```

In nessun punto del flusso l'utente deve sapere dove si trova un comando, come si chiama un campo o quale vista usare.

### 10.5 Gli stati che l'esperienza deve gestire bene

Un prodotto conversazionale si giudica dai casi non ideali più che da quelli ideali.

| Stato | Comportamento richiesto |
|---|---|
| **Attesa** | L'attesa deve essere leggibile: l'utente deve sapere che il sistema sta lavorando, e su cosa |
| **Ambiguità** | Domanda specifica, preferibilmente a scelta chiusa |
| **Bassa confidenza** | Risultato presentato con riserva esplicita e invito alla verifica |
| **Incomprensione** | Dichiarazione onesta e proposta di riformulazione; mai un'ipotesi arbitraria |
| **Risultato vuoto** | Distinzione fra "non esiste" e "non ho capito" (§9.5) |
| **Fuori ambito** | Dichiarazione chiara del limite (*"in questa versione posso solo consultare i dati"*), senza tentare surrogati |
| **Servizio non disponibile** | Messaggio esplicito e accesso invariato a Odoo e alle interrogazioni salvate |
| **Risultato molto ampio** | Avviso e proposta di restringere, prima di presentare decine di migliaia di record |

### 10.6 Fiducia e apprendimento

La fiducia si costruisce con la coerenza: la stessa richiesta deve produrre sempre la stessa interpretazione. Un sistema che risponde in modo diverso a parità di domanda è percepito come inaffidabile anche quando entrambe le risposte sono corrette.

Il prodotto deve inoltre raccogliere in modo non invasivo il segnale dell'utente sull'esito dell'interpretazione (conferma, correzione, riformulazione). Questo segnale alimenta il Dizionario Semantico e il corpus di valutazione: è il meccanismo attraverso cui la qualità cresce con l'uso anziché restare ferma al giorno dell'installazione.

---

## 11. Assunzioni

Le assunzioni sono le fondamenta su cui poggia la visione. Ciascuna è dichiarata insieme alla sua conseguenza in caso di caduta, perché un'assunzione non verificabile è un rischio travestito.

### A1 — Esiste un backend deterministico
Esiste un livello applicativo che riceve il DSL, lo valida ed esegue le operazioni corrispondenti in modo ripetibile.
*Se cade:* il principio P1 non è realizzabile e il prodotto perde la sua caratteristica distintiva. **Assunzione non negoziabile.**

### A2 — Esiste un DSL intermedio
Esiste un linguaggio strutturato, validabile e versionato che costituisce l'unico output della componente AI.
*Se cade:* il confine di validazione scompare e l'output generativo raggiunge direttamente l'esecuzione. **Assunzione non negoziabile.**

### A3 — Odoo resta l'unico motore esecutivo
Nessuna logica di business viene reimplementata al di fuori di Odoo.
*Se cade:* nasce un secondo sistema da mantenere allineato al primo, con divergenze di comportamento inevitabili nel tempo.

### A4 — L'ORM è l'unico livello di accesso ai dati
Nessun accesso diretto al database. Ogni lettura passa dall'ORM e quindi dai controlli di accesso, dalle regole sui record e dalla logica applicativa di Odoo.
*Se cade:* il modello di sicurezza (P2) è compromesso. **Assunzione non negoziabile.**

### A5 — L'AI interpreta esclusivamente le intenzioni
Nessuna esecuzione, nessuna decisione, nessuna generazione di codice o di query.
*Se cade:* il prodotto diventa un generatore di query con i rischi e i limiti di affidabilità che questo comporta. **Assunzione non negoziabile.**

### A6 — I dati aziendali non vengono esposti al modello linguistico
Il modello riceve la frase dell'utente, il contesto della conversazione e i **metadati di struttura** (entità disponibili, campi, terminologia). Non riceve il contenuto dei record.
*Se cade:* nascono obblighi di conformità, esposizione di dati riservati e ostacoli commerciali significativi presso clienti regolamentati.
*Nota:* questa assunzione **non compare fra quelle originarie del mandato** ed è proposta come aggiunta. La sua ricaduta è tanto di sicurezza quanto commerciale, e condiziona scelte che vanno prese ora, non a valle.

### A7 — Esiste una fonte di verità sulla semantica aziendale
È possibile costruire, per ciascuna installazione, una mappa fra il linguaggio dell'organizzazione e la struttura dei suoi dati, e mantenerla nel tempo.
*Se cade:* l'accuratezza si ferma alla comprensione generica e non raggiunge livelli utilizzabili in produzione sul gergo aziendale.

### A8 — La qualità interpretativa è misurabile
È possibile costruire un corpus rappresentativo di richieste reali con l'interpretazione corretta attesa.
*Se cade:* il prodotto non è governabile: non si può sapere se un rilascio migliora o peggiora, né autorizzare con cognizione l'ampliamento d'ambito.

### A9 — L'utente accetta di verificare l'interpretazione
Gli utenti leggono l'interpretazione mostrata e la correggono quando non corrisponde all'intenzione.
*Se cade:* il principio P3 non produce l'effetto atteso e il rischio del fraintendimento plausibile (§4.2) resta scoperto. **Assunzione da validare con i clienti pilota**, perché riguarda il comportamento umano e non può essere data per acquisita.

### A10 — L'infrastruttura di modello è disponibile con continuità e latenza accettabile
Il servizio di comprensione è raggiungibile con tempi di risposta compatibili con un'interazione conversazionale.
*Se cade:* l'esperienza degrada al punto da rendere più rapida l'interfaccia nativa. Da qui deriva il requisito di degradazione dignitosa (§4.5).

---

## 12. Vincoli

### 12.1 Vincoli di ambito della prima release

La prima release **non comprende**: creazione, modifica ed eliminazione di record; workflow; automazioni; codice Python generato; SQL generato; logiche di business generate.

L'unico obiettivo è l'interrogazione conversazionale dei dati e la visualizzazione dinamica dei risultati.

Questi vincoli non sono un elenco di divieti da far rispettare a un componente probabilistico. Sono **proprietà strutturali** del DSL: ciò che il contratto non sa esprimere, il sistema non può fare. È l'unico modo per rendere un vincolo effettivo anziché auspicato.

### 12.2 Vincoli di prodotto permanenti

Restano validi oltre la prima release e vincolano ogni evoluzione futura.

| Vincolo | Formulazione |
|---|---|
| **V1** | Nessuna operazione sui dati può derivare direttamente da output generativo non validato |
| **V2** | Nessuna esecuzione può avvenire con privilegi diversi da quelli dell'utente richiedente |
| **V3** | Nessun accesso ai dati può bypassare l'ORM |
| **V4** | Nessun risultato può essere presentato senza la relativa interpretazione |
| **V5** | Nessuna capacità di prodotto può dipendere in modo esclusivo da un singolo fornitore di modelli |
| **V6** | Nessuna modifica al DSL o allo Stato di Interrogazione può invalidare interrogazioni salvate in precedenza |
| **V7** | Nessun dato di contenuto dei record può essere trasmesso al modello linguistico (cfr. A6) |

### 12.3 Vincoli di contesto

- **Piattaforma.** Il prodotto vive dentro l'ecosistema Odoo e ne segue i vincoli funzionali, il ciclo di rilascio e le convenzioni di interfaccia.
- **Eterogeneità delle installazioni.** Ogni installazione ha moduli, personalizzazioni e terminologia differenti. Il prodotto non può presupporre uno schema dati fisso: deve adattarsi a ciò che trova.
- **Linguistico.** L'italiano è la lingua primaria dei casi d'uso di riferimento; il prodotto deve però nascere multilingua, poiché il gergo aziendale mescola abitualmente termini in più lingue.
- **Economico.** Il costo variabile per interazione impone di trattare l'efficienza come requisito di prodotto e non come ottimizzazione successiva.

### 12.4 Vincoli di processo

- **Nessun ampliamento d'ambito senza misura.** Ogni fase successiva alla prima è subordinata al raggiungimento documentato delle soglie di qualità della fase precedente (§15).
- **Nessuna regressione ammessa.** Un cambio di modello, di prompt o di dizionario che peggiori l'accuratezza sul corpus di valutazione non viene rilasciato.
- **Nessuna capacità introdotta senza il corrispondente caso di valutazione.** Una funzionalità non misurabile non è considerata completa.

---

## 13. Elementi Fuori Ambito

### 13.1 Fuori ambito per questo documento

Questo documento non progetta e non anticipa: architettura software, componenti applicativi, API, infrastruttura, database, sicurezza applicativa, DSL, implementazione tecnica.

Ogni riferimento a concetti quali *Stato di Interrogazione*, *Dizionario Semantico* o *corpus di valutazione* è di natura **concettuale**: definisce cosa il prodotto deve possedere, non come sarà realizzato. La forma tecnica di questi elementi è responsabilità dei documenti successivi.

### 13.2 Documenti successivi previsti

| Documento | Contenuto | Prerequisito |
|---|---|---|
| **Specifica del DSL** | Struttura, semantica, validazione, versionamento del contratto | Questo documento approvato |
| **Architettura di Sistema** | Componenti, flussi, confini, punti di estensione, indipendenza dal canale | Specifica del DSL |
| **Modello di Sicurezza e Conformità** | Identità, autorizzazioni, tracciabilità, trattamento dei dati verso il modello | In parallelo all'architettura |
| **Piano di Valutazione della Qualità** | Corpus, metodo di misura, soglie, criteri di regressione | Contestuale alla prima release |
| **Modello Semantico** | Struttura e ciclo di vita del Dizionario Semantico | Contestuale alla prima release |
| **Linee guida di Esperienza Utente** | Presentazione dell'interpretazione, stati non ideali, disambiguazione | Contestuale alla prima release |

### 13.3 Fuori ambito per il prodotto — in modo permanente

Alcune esclusioni non sono un rinvio: definiscono cosa il prodotto non diventerà mai, per coerenza con la propria filosofia.

- **Assistente generalista.** Il dominio è l'ERP dell'organizzazione.
- **Sistema che decide autonomamente.** L'utente resta l'unico titolare della decisione, in ogni fase della roadmap, inclusa quella di orchestrazione multi-agente.
- **Generatore di codice eseguibile.** Nessuna evoluzione può introdurre l'esecuzione di codice prodotto da un modello.
- **Livello di accesso privilegiato.** Il prodotto non potrà mai mostrare più di quanto l'utente sia autorizzato a vedere.
- **Sostituto dell'interfaccia Odoo.** Il prodotto resta additivo per costruzione.

Dichiarare queste esclusioni come permanenti ha una funzione precisa: proteggere il prodotto dalla pressione incrementale che, funzionalità dopo funzionalità, tende a erodere i principi fondativi fino a renderli inapplicabili.

---

## 14. Visione Evolutiva

### 14.1 Il criterio di coerenza

Ogni evoluzione deve rispettare la stessa struttura: **l'AI interpreta, il DSL contrattualizza, il sistema esegue in modo deterministico**. Le fasi successive ampliano ciò che il DSL sa esprimere e i canali attraverso cui l'intenzione può arrivare. Non spostano mai il confine dell'esecuzione.

Una evoluzione che richiedesse di superare quel confine non sarebbe un'evoluzione di questo prodotto: sarebbe un prodotto diverso.

### 14.2 Le direttrici di evoluzione

L'evoluzione procede lungo quattro direttrici indipendenti fra loro. Trattarle come tali consente di avanzare su una senza attendere le altre.

**Direttrice 1 — Ampiezza del canale.**
Dalla chat alla voce, al mobile, a Teams e Slack, all'email, alle API, alle interfacce multimodali. Ogni nuovo canale è un adattatore: non tocca il motore di comprensione. È la direttrice a rischio più basso.

**Direttrice 2 — Profondità dell'interazione.**
Dalla sola lettura alla navigazione, all'azione sul record, alla creazione e modifica guidata. Ogni passo amplia il DSL e alza il livello di affidabilità richiesto. È la direttrice a rischio più alto, e quella su cui la disciplina di misura è imprescindibile.

**Direttrice 3 — Ricchezza della comprensione.**
Dal testo ai documenti, alle immagini, alla comprensione del contesto operativo dell'utente. Amplia le forme in cui l'intenzione può essere espressa; il modello di esecuzione resta invariato.

**Direttrice 4 — Ampiezza analitica.**
Dall'interrogazione all'aggregazione avanzata, alle dashboard generate, ai report intelligenti, alle serie storiche e ai confronti. Amplia le capacità espressive del DSL sul versante analitico, restando in sola lettura: rischio contenuto, valore percepito elevato.

### 14.3 Le evoluzioni previste

| Evoluzione | Descrizione | Direttrice | Condizione abilitante |
|---|---|---|---|
| **Interazione vocale** | Esprimere l'intenzione parlando, sul campo o in mobilità | 1 | Motore già indipendente dal canale |
| **Comprensione documentale** | Interrogare a partire da un documento (ordine, fattura, contratto) | 3 | Trattamento dei contenuti conforme ad A6 |
| **Comprensione delle immagini** | Fotografare un articolo, un'etichetta, un codice e ottenere il dato collegato | 3 | Comprensione documentale consolidata |
| **Navigazione assistita** | Portare l'utente al punto giusto del sistema, non solo al dato | 2 | Accuratezza interpretativa consolidata |
| **Dashboard automatiche** | Comporre più interrogazioni in una vista d'insieme persistente | 4 | Stato di Interrogazione salvabile e componibile |
| **Report intelligenti** | Generare report ricorrenti a partire da un'intenzione espressa una sola volta | 4 | Dashboard automatiche |
| **Suggerimenti contestuali** | Proporre l'informazione pertinente al contesto operativo, su richiesta implicita | 3 | Fiducia consolidata; nessuna proattività invasiva |
| **Operazioni guidate** | Creazione e modifica di record sotto conferma esplicita dell'utente | 2 | Soglie di affidabilità raggiunte e documentate |
| **AI Copilot** | Assistenza continuativa nel processo operativo, non nella singola richiesta | 2+3 | Operazioni guidate consolidate |
| **Piattaforma multi-agente** | Orchestrazione di più competenze specializzate su compiti articolati | 2+3+4 | Tutte le precedenti; governance della tracciabilità |

### 14.4 Il punto di attenzione sulle evoluzioni "autonome"

Le ultime due evoluzioni — Copilot e piattaforma multi-agente — sono quelle in cui il rischio di tradire la filosofia del prodotto è più concreto.

Un copilota che agisce senza richiesta esplicita, o un insieme di agenti che si coordinano fra loro producendo effetti non riconducibili a una singola intenzione dell'utente, violerebbero il principio secondo cui **il sistema non decide** (§2.5).

L'interpretazione corretta di queste evoluzioni, coerente con la visione, è la seguente: più competenze specializzate possono cooperare per **comprendere meglio** un'intenzione articolata e per **proporre** un piano di operazioni, ma ogni operazione con effetto sui dati resta subordinata a una conferma umana esplicita e resta eseguita in modo deterministico. L'orchestrazione riguarda la comprensione, mai l'autorizzazione.

---

## 15. Roadmap di Prodotto

### 15.1 Impostazione e scostamento dalla proposta iniziale

La roadmap proposta nel mandato è condivisibile nell'impianto. Sono introdotte tre modifiche, argomentate di seguito.

**Modifica 1 — Introduzione di una Fase 0 (Fondamenta).**
Il Dizionario Semantico, il corpus di valutazione e il contratto DSL non sono attività della prima release: ne sono il prerequisito. Trattarli come parte della Fase 1 significa, nella pratica, comprimerli sotto la pressione della consegna. Sono resi espliciti come fase autonoma con propri criteri di completamento.

**Modifica 2 — Inserimento di una fase di Affidabilità e Governance prima di qualunque scrittura.**
Nella proposta iniziale la Fase 2 introduce azioni sui record e la Fase 3 le operazioni di creazione e modifica. Il passaggio dalla sola lettura alla scrittura è il salto di rischio più grande dell'intero programma: un fraintendimento in lettura produce un risultato sbagliato, un fraintendimento in scrittura produce un danno permanente ai dati aziendali.

Autorizzare quel salto richiede di sapere, con dati e non con impressioni, quanto il sistema è accurato. Viene quindi inserita una fase dedicata a osservabilità, misura continua, tracciabilità e maturazione del Dizionario Semantico. **Questa è la raccomandazione più importante dell'intero documento.**

**Modifica 3 — Anticipazione delle capacità analitiche.**
Nella proposta iniziale analytics e dashboard occupano la Fase 4, dopo le operazioni di scrittura. Le capacità analitiche restano però in **sola lettura**: hanno quindi un profilo di rischio molto più basso della scrittura, a fronte di un valore percepito dal management molto alto. Sono anticipate prima delle operazioni guidate.

### 15.2 Le fasi

---

#### Fase 0 — Fondamenta *(prerequisito)*

| | |
|---|---|
| **Obiettivo** | Stabilire i contratti e gli asset su cui poggia l'intero prodotto |
| **Funzionalità introdotte** | Nessuna funzionalità utente. Definizione del DSL di lettura; definizione dello Stato di Interrogazione; struttura del Dizionario Semantico; primo corpus di valutazione costruito su richieste reali raccolte presso i clienti pilota |
| **Valore per il business** | Nessun valore diretto; abilita e mette in sicurezza tutto ciò che segue |
| **Dipendenze** | Approvazione di questo documento; accesso a clienti pilota disposti a fornire richieste reali |
| **Rischi** | Sottovalutazione della fase per la pressione a mostrare risultati; corpus non rappresentativo del linguaggio reale |
| **Criteri di completamento** | DSL di lettura definito e versionato; corpus iniziale di richieste reali con interpretazione attesa; metodo di misura dell'accuratezza definito e concordato |

---

#### Fase 1 — Interazione conversazionale e interrogazione dati

| | |
|---|---|
| **Obiettivo** | Consentire all'utente di interrogare Odoo in linguaggio naturale ottenendo viste native generate dinamicamente |
| **Funzionalità introdotte** | Le sei capacità F1–F6 (§9.1); generazione dinamica delle viste; interpretazione ispezionabile; disambiguazione; canale chat in Odoo |
| **Valore per il business** | Riduzione del tempo di ricerca; abbattimento della curva di apprendimento; accesso autonomo al dato |
| **Dipendenze** | Fase 0 completata |
| **Rischi** | Accuratezza insufficiente sul gergo aziendale; fraintendimenti plausibili non rilevati; adozione limitata per abitudine all'interfaccia nativa |
| **Criteri di completamento** | Gli otto criteri di §8.5 |

---

#### Fase 2 — Affidabilità, osservabilità e governance *(fase abilitante)*

| | |
|---|---|
| **Obiettivo** | Rendere la qualità del sistema misurata, tracciata e in crescita continua; costruire il presupposto oggettivo per autorizzare la scrittura |
| **Funzionalità introdotte** | Misura continua dell'accuratezza su corpus in crescita; raccolta strutturata del segnale utente; alimentazione del Dizionario Semantico dall'uso reale; tracciabilità completa delle interrogazioni; strumenti di analisi dei fraintendimenti; interrogazioni salvabili e condivisibili; secondo canale (validazione dell'indipendenza dal canale) |
| **Valore per il business** | Fiducia dimostrabile con dati; qualità che cresce con l'uso; riutilizzo del lavoro degli utenti; conformità e auditabilità |
| **Dipendenze** | Fase 1 in produzione presso almeno due clienti pilota con volume d'uso reale |
| **Rischi** | Percezione della fase come non produttiva e conseguente pressione a saltarla — è il rischio principale dell'intero programma; segnale utente insufficiente per alimentare il dizionario |
| **Criteri di completamento** | Accuratezza misurata con continuità e in crescita documentata; corpus di valutazione rappresentativo del linguaggio reale osservato; nessuna regressione fra rilasci; secondo canale attivo senza modifiche al motore; tracciabilità completa verificata |

---

#### Fase 3 — Navigazione e azioni sui record

| | |
|---|---|
| **Obiettivo** | Estendere l'interazione dal risultato all'oggetto: raggiungere il record e attivare le azioni già previste da Odoo |
| **Funzionalità introdotte** | Navigazione conversazionale ai record; esecuzione di azioni esistenti previa conferma esplicita; navigazione assistita nel sistema |
| **Valore per il business** | Riduzione dei passi operativi oltre la sola consultazione; primo valore misurabile sul lavoro operativo, non solo informativo |
| **Dipendenze** | Fase 2 completata con soglie di accuratezza raggiunte |
| **Rischi** | Prima superficie con effetti sui dati: un'azione confermata per errore ha conseguenze reali; conferme percepite come attrito e disattivate su richiesta dei clienti |
| **Criteri di completamento** | Nessuna azione eseguita senza conferma esplicita; interpretazione dell'azione mostrata prima dell'esecuzione; tracciabilità completa; accuratezza sulle intenzioni di azione superiore alla soglia stabilita |

---

#### Fase 4 — Analitica, dashboard e report

| | |
|---|---|
| **Obiettivo** | Estendere le capacità espressive dall'interrogazione all'analisi, restando in sola lettura |
| **Funzionalità introdotte** | Aggregazioni avanzate; confronti fra periodi; serie storiche; dashboard composte da più interrogazioni; report ricorrenti generati da un'intenzione |
| **Valore per il business** | Accesso diretto del management all'informazione aggregata senza intermediazione; riduzione del ricorso a strumenti esterni di reportistica |
| **Dipendenze** | Fase 2 completata; Stato di Interrogazione salvabile e componibile |
| **Rischi** | Numeri aggregati errati ma plausibili — impatto elevato perché sostengono decisioni; ambiguità sulle definizioni delle metriche aziendali |
| **Criteri di completamento** | Ogni valore aggregato accompagnato dalla definizione della metrica applicata e dalla possibilità di ispezionare i dati sottostanti; dashboard riproducibili in modo deterministico |

---

#### Fase 5 — Operazioni guidate

| | |
|---|---|
| **Obiettivo** | Consentire creazione e modifica di record sotto guida conversazionale e conferma umana esplicita |
| **Funzionalità introdotte** | Creazione guidata; modifica controllata; anteprima obbligatoria dell'operazione prima dell'esecuzione; annullamento ove il modello dati lo consenta |
| **Valore per il business** | Riduzione del tempo di inserimento dati e degli errori di compilazione; estensione del valore dall'informazione all'operatività |
| **Dipendenze** | Fasi 2 e 3 completate; soglie di affidabilità documentate su un periodo d'uso significativo |
| **Rischi** | Danno permanente ai dati; effetti a catena su documenti collegati; responsabilità in caso di errore; erosione della conferma esplicita per ragioni di efficienza |
| **Criteri di completamento** | Nessuna scrittura senza anteprima e conferma; tracciabilità integrale; comportamento verificato sui casi di errore e sui percorsi di annullamento; accuratezza sulle intenzioni di scrittura superiore alla soglia stabilita |

---

#### Fase 6 — Interazione vocale e multimodale

| | |
|---|---|
| **Obiettivo** | Estendere i canali e le forme in cui l'intenzione può essere espressa |
| **Funzionalità introdotte** | Voce; comprensione documentale; comprensione delle immagini; canali aggiuntivi (Teams, Slack, email, mobile) |
| **Valore per il business** | Accesso all'ERP in contesti in cui la tastiera non è disponibile: magazzino, cantiere, mobilità, assistenza sul campo |
| **Dipendenze** | Indipendenza dal canale già validata in Fase 2 |
| **Rischi** | Qualità del riconoscimento vocale in ambienti rumorosi; trattamento dei contenuti documentali in coerenza con A6 |
| **Criteri di completamento** | Ogni nuovo canale attivato senza modifiche al motore di comprensione; parità funzionale e di accuratezza con il canale chat |

---

#### Fase 7 — Copilot e piattaforma AI enterprise

| | |
|---|---|
| **Obiettivo** | Assistenza continuativa nel processo operativo e orchestrazione di competenze specializzate, nel rispetto integrale dei principi fondativi |
| **Funzionalità introdotte** | Assistenza contestuale nel flusso di lavoro; suggerimenti su richiesta; composizione di più competenze per intenzioni articolate; piani di operazioni proposti e confermati dall'utente |
| **Valore per il business** | Passaggio da strumento di accesso al dato a livello di produttività trasversale all'organizzazione |
| **Dipendenze** | Tutte le fasi precedenti |
| **Rischi** | Deriva verso l'autonomia decisionale in contrasto con §2.5 e §13.3; perdita di tracciabilità nelle interazioni composte; complessità che erode il principio P4 |
| **Criteri di completamento** | Ogni operazione con effetto sui dati resta soggetta a conferma umana esplicita; tracciabilità integrale mantenuta anche nelle interazioni composte; nessuna violazione dei vincoli permanenti V1–V7 |

---

### 15.3 Il criterio di avanzamento fra le fasi

> **Nessuna fase inizia prima che i criteri di completamento della precedente siano verificati e documentati.**

La regola è particolarmente stringente per il passaggio alla Fase 5, dove la verifica riguarda dati di accuratezza raccolti su un periodo d'uso reale significativo e non su dimostrazioni controllate.

La pressione ad accelerare arriverà, ed è legittima: le funzionalità di scrittura sono quelle che si presentano meglio e che i clienti chiedono per primi. La risposta corretta non è il rifiuto, ma il dato: **mostrare l'accuratezza misurata e lasciare che sia essa a determinare quando il passo è sostenibile.** È anche il motivo per cui la Fase 2 esiste.

---

## 16. Rischi

I rischi sono ordinati per esposizione complessiva. Per ciascuno sono indicati impatto, probabilità, mitigazione di prodotto e segnale che ne anticipa la manifestazione.

### 16.1 R1 — Il fraintendimento plausibile

| | |
|---|---|
| **Descrizione** | Il sistema interpreta la richiesta in modo leggermente diverso dall'intenzione e produce un risultato credibile ma sbagliato, che l'utente non verifica |
| **Impatto** | **Critico** — decisioni di business su dati errati; perdita di fiducia difficilmente recuperabile |
| **Probabilità** | **Alta** — è una proprietà intrinseca del linguaggio naturale, non un difetto eliminabile |
| **Mitigazione** | Interpretazione sempre visibile e comprensibile (P3); ogni condizione correggibile singolarmente; segnalazione esplicita della bassa confidenza; nelle fasi analitiche, definizione della metrica sempre esposta accanto al valore |
| **Segnale anticipatore** | Tasso di correzione dell'interpretazione prossimo allo zero: indica che gli utenti non la stanno leggendo, non che il sistema non sbaglia |

### 16.2 R2 — Salto prematuro alle operazioni di scrittura

| | |
|---|---|
| **Descrizione** | Pressione commerciale o competitiva porta ad anticipare creazione e modifica prima che l'affidabilità sia dimostrata |
| **Impatto** | **Critico** — danno permanente ai dati; esposizione di responsabilità; compromissione della reputazione del prodotto |
| **Probabilità** | **Alta** — è la richiesta più frequente e la funzionalità che si dimostra meglio |
| **Mitigazione** | Fase 2 come cancello obbligatorio; criteri di avanzamento documentati (§15.3); vincolo di scrittura reso strutturale nel DSL e non affidato a controlli applicativi |
| **Segnale anticipatore** | Richieste di "anticipare solo un caso semplice di creazione" |

### 16.3 R3 — Adozione insufficiente

| | |
|---|---|
| **Descrizione** | Gli utenti provano il prodotto e tornano all'interfaccia nativa, che conoscono e di cui si fidano |
| **Impatto** | **Alto** — investimento senza ritorno; il prodotto esiste ma non viene usato |
| **Probabilità** | **Media-alta** — è il fallimento tipico dei prodotti conversazionali su software gestionale |
| **Mitigazione** | Prodotto additivo e incorporato nel flusso di lavoro (§4.6); risultato in vista Odoo nativa; valore parziale utile anche con interpretazione imperfetta; interrogazioni salvabili che generano ritorno spontaneo |
| **Segnale anticipatore** | Uso concentrato nella prima settimana e calo rapido; numero medio di interrogazioni per utente attivo in diminuzione |

### 16.4 R4 — Dizionario Semantico insufficiente

| | |
|---|---|
| **Descrizione** | Il sistema non comprende il gergo dell'azienda e l'accuratezza si ferma a un livello inutilizzabile in produzione |
| **Impatto** | **Alto** — qualità percepita bassa fin dal primo giorno, quando la fiducia si forma |
| **Probabilità** | **Alta** in assenza di un processo strutturato di costruzione |
| **Mitigazione** | Dizionario riconosciuto come asset di prodotto (§4.4); costruzione assistita in fase di attivazione; alimentazione automatica dalle disambiguazioni e dalle correzioni; percorso di attivazione che non consegna mai un dizionario vuoto |
| **Segnale anticipatore** | Concentrazione delle disambiguazioni su pochi termini ricorrenti non ancora mappati |

### 16.5 R5 — Assenza di misura oggettiva della qualità

| | |
|---|---|
| **Descrizione** | La qualità viene valutata su impressioni e dimostrazioni anziché su un corpus rappresentativo |
| **Impatto** | **Alto** — impossibile sapere se un rilascio migliora o peggiora; impossibile autorizzare con cognizione l'ampliamento d'ambito; regressioni silenziose |
| **Probabilità** | **Media-alta** — la costruzione del corpus è un lavoro poco visibile e facilmente rinviato |
| **Mitigazione** | Corpus come criterio di completamento della Fase 0; nessuna capacità considerata completa senza il corrispondente caso di valutazione (§12.4); misura continua come oggetto della Fase 2 |
| **Segnale anticipatore** | Discussioni sulla qualità condotte per aneddoti; corpus fermo alla dimensione iniziale |

### 16.6 R6 — Insostenibilità economica dell'uso

| | |
|---|---|
| **Descrizione** | Il costo variabile per interazione cresce con l'adozione fino a erodere la marginalità |
| **Impatto** | **Alto** — successo d'uso che si traduce in perdita economica: il caso peggiore, perché il rimedio (limitare l'uso) contraddice l'obiettivo |
| **Probabilità** | **Media** |
| **Mitigazione** | Efficienza come requisito di prodotto (§12.3); contesto compatto grazie allo Stato di Interrogazione (§4.3); riuso deterministico delle interrogazioni salvate, che non richiedono il modello; monitoraggio del costo per interazione fra i KPI (§17.4) |
| **Segnale anticipatore** | Costo medio per interazione in crescita a parità di funzionalità |

### 16.7 R7 — Dipendenza dal fornitore del modello

| | |
|---|---|
| **Descrizione** | Il prodotto risulta vincolato a un singolo fornitore per prestazioni, disponibilità, condizioni economiche o continuità del servizio |
| **Impatto** | **Medio-alto** — perdita di potere negoziale; esposizione a variazioni di prezzo, di comportamento o di disponibilità non controllabili |
| **Probabilità** | **Media** — la dipendenza si forma per accumulo di piccole scelte, non per decisione esplicita |
| **Mitigazione** | Principio P6 e vincolo V5; corpus di valutazione che rende la sostituzione una decisione misurabile; nessuna capacità di prodotto costruita su caratteristiche esclusive |
| **Segnale anticipatore** | Impossibilità di stimare l'impatto di un cambio di modello senza un progetto dedicato |

### 16.8 R8 — Trattamento dei dati verso il modello

| | |
|---|---|
| **Descrizione** | Contenuti aziendali riservati vengono trasmessi a un servizio esterno, con implicazioni di conformità e di riservatezza |
| **Impatto** | **Alto** — ostacolo commerciale presso clienti regolamentati; esposizione normativa |
| **Probabilità** | **Bassa se A6 è rispettata**, alta se l'assunzione viene erosa per comodità funzionale |
| **Mitigazione** | Assunzione A6 e vincolo V7; trasmissione dei soli metadati di struttura; possibilità di modelli eseguiti in ambiente controllato per clienti che lo richiedono |
| **Segnale anticipatore** | Proposte di "inviare qualche record di esempio per migliorare la comprensione" |

### 16.9 R9 — Erosione progressiva dei principi

| | |
|---|---|
| **Descrizione** | Sotto la pressione di richieste puntuali, i principi fondativi vengono derogati un caso alla volta fino a perdere efficacia |
| **Impatto** | **Alto** — il prodotto diventa lentamente un generatore di query con un'interfaccia gradevole |
| **Probabilità** | **Media-alta** su un orizzonte pluriennale |
| **Mitigazione** | Principi ordinati per priorità con conseguenze operative esplicite (§5); vincoli permanenti V1–V7; esclusioni dichiarate permanenti (§13.3); revisione periodica di coerenza rispetto a questo documento |
| **Segnale anticipatore** | Deroghe motivate come "eccezione per questo cliente" |

### 16.10 R10 — Aspettative superiori alle capacità

| | |
|---|---|
| **Descrizione** | La comunicazione commerciale, o l'esperienza degli utenti con assistenti generalisti, genera l'attesa di un sistema onnisciente |
| **Impatto** | **Medio** — delusione al primo limite incontrato, indipendentemente dalla qualità reale |
| **Probabilità** | **Alta** |
| **Mitigazione** | Dichiarazione chiara e non evasiva dei limiti negli stati fuori ambito (§10.5); posizionamento come strumento specialistico sull'ERP e non come assistente generico |
| **Segnale anticipatore** | Richieste ricorrenti fuori dominio nelle prime settimane di adozione |

### 16.11 Sintesi dell'esposizione

| Rischio | Impatto | Probabilità | Priorità di presidio |
|---|---|---|---|
| R1 Fraintendimento plausibile | Critico | Alta | **1** |
| R2 Scrittura prematura | Critico | Alta | **2** |
| R4 Dizionario insufficiente | Alto | Alta | **3** |
| R5 Assenza di misura | Alto | Media-alta | **4** |
| R3 Adozione insufficiente | Alto | Media-alta | **5** |
| R9 Erosione dei principi | Alto | Media-alta | **6** |
| R6 Insostenibilità economica | Alto | Media | 7 |
| R8 Trattamento dei dati | Alto | Bassa* | 8 |
| R7 Dipendenza dal fornitore | Medio-alto | Media | 9 |
| R10 Aspettative eccessive | Medio | Alta | 10 |

*\*condizionata al rispetto dell'assunzione A6.*

---

## 17. KPI di Successo

### 17.1 Impostazione

Gli indicatori sono organizzati in quattro famiglie: **qualità dell'interpretazione**, **efficacia per l'utente**, **adozione** e **sostenibilità**. I valori indicati sono soglie di riferimento proposte, da confermare con l'Architect e da ricalibrare dopo la prima raccolta di dati reali (§17.5).

Un principio governa l'intero impianto di misura: **si misurano i risultati, non le conversazioni** (P7). Un aumento del numero di messaggi per sessione è un segnale negativo, non un segnale di ingaggio.

### 17.2 Qualità dell'interpretazione

| KPI | Definizione | Soglia di riferimento |
|---|---|---|
| **Accuratezza interpretativa** | Percentuale di richieste del corpus di valutazione interpretate correttamente | ≥ 90% |
| **Risoluzione al primo tentativo** | Percentuale di richieste reali risolte senza riformulazione né correzione | ≥ 75% |
| **Tasso di disambiguazione** | Percentuale di richieste che richiedono un chiarimento | 5–15% *(troppo basso indica ipotesi silenziose; troppo alto indica attrito)* |
| **Tasso di correzione** | Percentuale di interpretazioni corrette manualmente dall'utente | Monitorato; una diminuzione è positiva solo se accompagnata da accuratezza stabile |
| **Regressione fra rilasci** | Variazione negativa dell'accuratezza sul corpus | **Zero ammessa** |
| **Latenza percepita (P95)** | Tempo dalla richiesta alla presentazione del risultato | ≤ 3 secondi |

### 17.3 Efficacia per l'utente

| KPI | Definizione | Soglia di riferimento |
|---|---|---|
| **Tempo di accesso all'informazione** | Tempo medio dalla domanda al dato, confrontato con la misura iniziale sull'interfaccia nativa | Riduzione ≥ 80% sui casi frequenti |
| **Passi per risultato** | Numero medio di interazioni necessarie a ottenere il risultato | ≤ 2 |
| **Tasso di abbandono** | Percentuale di sessioni concluse senza risultato utile | ≤ 10% |
| **Autonomia del nuovo utente** | Percentuale di attività di riferimento completate senza formazione preliminare | ≥ 80% entro il primo giorno |
| **Ampiezza del dominio interrogato** | Numero di entità Odoo distinte effettivamente interrogate | In crescita — indicatore indiretto delle domande oggi non poste (§7.2) |

### 17.4 Adozione e sostenibilità

| KPI | Definizione | Soglia di riferimento |
|---|---|---|
| **Utenti attivi settimanali** | Percentuale di utenti Odoo che usano il prodotto ogni settimana | ≥ 40% entro sei mesi dall'attivazione |
| **Ritenzione a 30 giorni** | Percentuale di utenti ancora attivi un mese dopo il primo utilizzo | ≥ 60% |
| **Interrogazioni per utente attivo** | Media settimanale | In crescita nei primi sei mesi |
| **Riuso di interrogazioni salvate** | Percentuale di esecuzioni provenienti da interrogazioni salvate | In crescita — indica valore duraturo e riduce il costo variabile |
| **Copertura del Dizionario Semantico** | Percentuale di termini ricorrenti mappati | In crescita continua |
| **Costo per interazione** | Costo variabile medio di una richiesta interpretata | In diminuzione a parità di funzionalità |
| **Disponibilità del servizio** | Percentuale di tempo in cui il livello di comprensione è operativo | ≥ 99,5% |
| **Incidenti di accesso non autorizzato** | Numero di accessi a dati oltre i permessi dell'utente | **Zero** |

### 17.5 Come si misura, e perché conta più di cosa si misura

Tre condizioni rendono questo impianto effettivo anziché formale.

**La misura è continua, non periodica.** L'accuratezza va calcolata ad ogni rilascio e ad ogni modifica del modello, del prompt o del dizionario. Una misura annuale non protegge da nulla.

**Il corpus cresce con l'uso.** Ogni fraintendimento reale osservato in produzione entra nel corpus con l'interpretazione corretta. Un corpus fermo alla dimensione iniziale smette rapidamente di rappresentare il linguaggio reale degli utenti.

**Le soglie si ricalibrano.** I valori proposti sono ipotesi ragionevoli formulate prima di disporre di dati. Vanno riviste dopo il primo trimestre di uso reale: mantenere soglie che i dati hanno smentito è peggio che non averle.

---

## 18. Raccomandazioni Strategiche

Le raccomandazioni sono ordinate per impatto sul successo del prodotto. Le prime cinque riguardano decisioni da assumere ora, perché condizionano tutto ciò che segue.

### 18.1 Adottare lo Stato di Interrogazione come oggetto centrale del prodotto

**Raccomandazione.** Trattare la conversazione come una sequenza di modifiche a un oggetto strutturato (§4.3), non come una cronologia di messaggi.

**Perché.** È la scelta concettuale con il rapporto benefici/costi più alto dell'intero progetto. Rende il contesto compatto e quindi la qualità stabile e il costo costante anche nelle conversazioni lunghe; rende possibile annullare, salvare, condividere e riprendere; rende ogni risultato riproducibile.

**Se non si adotta.** La qualità degrada man mano che la conversazione si allunga, il costo per turno cresce, e capacità come dashboard e report — che presuppongono uno stato salvabile e componibile — diventano riprogettazioni anziché estensioni.

### 18.2 Non spostare mai una funzionalità prima della sua misura

**Raccomandazione.** Considerare la Fase 2 un cancello obbligatorio e non un'attività rinviabile. Nessun ampliamento d'ambito, in particolare verso la scrittura, prima che esista una misura continua della qualità interpretativa.

**Perché.** Un componente probabilistico senza misura non è governabile: non si sa se un rilascio migliora o peggiora, e non si può decidere con cognizione quando il sistema è abbastanza affidabile per operare sui dati. È l'unica difesa reale contro i due rischi critici R1 e R2.

**Se non si adotta.** Il progetto avanzerà per impressioni. Il momento in cui l'assenza di misura si manifesterà sarà il primo incidente su dati reali, quando il costo sarà massimo.

### 18.3 Trattare il Dizionario Semantico come prodotto, non come configurazione

**Raccomandazione.** Assegnare al Dizionario Semantico proprietà, ciclo di vita, versionamento e responsabilità esplicite. Prevedere fin dalla prima release la sua costruzione assistita in fase di attivazione e la sua crescita automatica a partire da disambiguazioni e correzioni.

**Perché.** È l'asset che rende il prodotto difendibile (§4.4) e, contemporaneamente, la principale causa di bassa qualità percepita al primo giorno di ogni cliente.

**Se non si adotta.** Ogni nuovo cliente sperimenta la qualità peggiore proprio quando si forma la fiducia, e il prodotto resta replicabile da chiunque integri un modello linguistico.

### 18.4 Rendere il vincolo di sola lettura strutturale, non applicativo

**Raccomandazione.** L'impossibilità di scrivere nella prima release deve derivare dal fatto che il DSL non è in grado di esprimere una scrittura, non da controlli applicativi che verificano l'output del modello.

**Perché.** Un divieto verificato a valle è un divieto che prima o poi viene aggirato — da un difetto, da una deroga, da una configurazione. Un'impossibilità strutturale non richiede vigilanza.

**Se non si adotta.** Il vincolo più importante della prima release dipende dalla correttezza di un controllo, anziché dalla forma del contratto.

### 18.5 Stabilire ora il confine sui dati verso il modello

**Raccomandazione.** Assumere fin dall'inizio che il modello riceva la frase dell'utente, il contesto e i metadati di struttura, mai il contenuto dei record (A6, V7).

**Perché.** È una decisione a senso unico: introdurla in seguito significherebbe riprogettare il flusso di comprensione. È inoltre un requisito d'accesso a interi segmenti di mercato — settore pubblico, sanità, finanza — che non è recuperabile a posteriori.

**Se non si adotta.** Il prodotto acquisisce un debito di conformità che si manifesterà nel primo processo di valutazione fornitori di un cliente strutturato.

### 18.6 Riconsiderare il nome del prodotto

**Raccomandazione.** Valutare la sostituzione della denominazione di lavoro *"AI Agent per Odoo"*.

**Perché.** Il termine *agent* indica oggi, nel linguaggio corrente del settore, un sistema che decide e agisce in autonomia: l'esatto contrario di ciò che questo prodotto è (§2.5, §13.3). Il nome costruisce l'aspettativa sbagliata presso i clienti, alimentando il rischio R10, e presso il team, alimentando il rischio R9. Una denominazione centrata sull'interpretazione dell'intenzione — nella famiglia di *Intent Layer* o *Natural Language Interaction Layer* — descrive il prodotto reale e ne protegge i confini.

**Osservazione.** È una raccomandazione di posizionamento, non un vincolo tecnico. Va presa ora perché il costo di un cambio di nome cresce rapidamente con la comunicazione già fatta.

### 18.7 Validare la premessa comportamentale con i clienti pilota

**Raccomandazione.** Verificare presso i pilota l'assunzione A9: che gli utenti leggano davvero l'interpretazione mostrata e la correggano quando non corrisponde all'intenzione.

**Perché.** L'intera difesa contro il rischio critico R1 poggia su un comportamento umano che stiamo assumendo, non misurando. Se gli utenti ignorano l'interpretazione, il principio P3 è formalmente rispettato e sostanzialmente inefficace, e servono forme diverse — conferme più esplicite sui casi a bassa confidenza, evidenziazione delle condizioni inferite e non dichiarate.

### 18.8 Misurare la situazione attuale prima di introdurre il prodotto

**Raccomandazione.** Rilevare presso i clienti pilota, prima dell'attivazione, i tempi e i passi necessari a ottenere le informazioni ricorrenti con l'interfaccia nativa.

**Perché.** Diversi KPI (§17.3) sono definiti come riduzione rispetto alla situazione attuale. Senza una misura iniziale, il beneficio principale del prodotto resterà un'affermazione non dimostrabile — proprio davanti agli stakeholder che devono finanziarne l'evoluzione.

### 18.9 Progettare l'attivazione di un nuovo cliente come parte del prodotto

**Raccomandazione.** Considerare il percorso di attivazione — costruzione iniziale del dizionario, raccolta delle prime richieste reali, definizione delle attività di riferimento — una componente del prodotto e non un'attività di servizio.

**Perché.** La qualità percepita nei primi giorni determina l'adozione (R3) e la qualità dei primi giorni dipende quasi interamente dall'attivazione. Un prodotto eccellente con un'attivazione improvvisata viene giudicato per l'attivazione.

### 18.10 Istituire una revisione periodica di coerenza

**Raccomandazione.** Sottoporre a revisione periodica la coerenza fra le decisioni prese e i principi di questo documento, con esito documentato.

**Perché.** Il rischio R9 — l'erosione progressiva dei principi — non si manifesta mai come una singola decisione sbagliata: si manifesta come una successione di deroghe ciascuna ragionevole in sé. L'unico presidio efficace è una verifica esplicita e ricorrente rispetto a un riferimento scritto. È la ragione per cui questo documento esiste.

---

## 19. Punti Aperti e Decisioni Richieste

Le decisioni seguenti spettano all'Architect e condizionano i documenti successivi. Sono elencate con la raccomandazione di questo documento.

| # | Decisione richiesta | Raccomandazione | Impatto se rinviata |
|---|---|---|---|
| **D1** | Approvazione della Fase 0 come fase autonoma | Approvare | I contratti fondativi vengono compressi sotto la pressione della prima consegna |
| **D2** | Approvazione della Fase 2 come cancello obbligatorio prima di qualunque scrittura | Approvare | R2 resta senza presidio |
| **D3** | Adozione dell'assunzione A6 sui dati verso il modello | Adottare | Decisione a senso unico: il costo cresce con l'avanzamento |
| **D4** | Adozione dello Stato di Interrogazione come oggetto centrale | Adottare | Le fasi 4 e successive diventano riprogettazioni |
| **D5** | Conferma o revisione delle soglie dei KPI (§17) | Confermare come riferimento iniziale, ricalibrare dopo il primo trimestre | Misura senza criterio di giudizio |
| **D6** | Denominazione del prodotto | Valutare alternative a *"AI Agent"* | Il costo del cambio cresce con la comunicazione già effettuata |
| **D7** | Individuazione dei clienti pilota e delle attività di riferimento | Definire prima dell'avvio della Fase 0 | Corpus non rappresentativo; KPI privi di misura iniziale |
| **D8** | Modalità di erogazione del modello per clienti regolamentati | Prevedere l'opzione in ambiente controllato | Segmenti di mercato preclusi |

---

## 20. Glossario

| Termine | Definizione |
|---|---|
| **NLIL** | *Natural Language Interaction Layer*. Il livello di interazione in linguaggio naturale sopra Odoo; il prodotto oggetto di questo documento |
| **Intenzione** | Ciò che l'utente vuole ottenere, espresso nelle sue parole, indipendentemente dalla struttura del sistema |
| **DSL** | *Domain Specific Language*. Il linguaggio strutturato e validato che costituisce l'unico output della componente AI e il contratto verso il backend deterministico |
| **Stato di Interrogazione** | L'oggetto che rappresenta in ogni istante cosa l'utente sta guardando: entità, filtri, campi, ordinamento, raggruppamenti, tipo di vista |
| **Dizionario Semantico** | La mappa curata e versionata fra il linguaggio di una specifica organizzazione e la struttura dei suoi dati |
| **Corpus di valutazione** | L'insieme di richieste reali con l'interpretazione corretta attesa, usato per misurare l'accuratezza e rilevare le regressioni |
| **Interpretazione ispezionabile** | La presentazione, in linguaggio comprensibile a un utente non tecnico, di come il sistema ha compreso la richiesta |
| **Disambiguazione** | La richiesta di chiarimento rivolta all'utente quando la richiesta ammette più interpretazioni plausibili |
| **Fraintendimento plausibile** | Interpretazione errata che produce un risultato credibile e quindi non riconosciuto come sbagliato (rischio R1) |
| **Determinismo** | Proprietà per cui, a parità di DSL, il risultato dell'esecuzione è sempre identico |
| **Canale** | Il mezzo attraverso cui l'intenzione viene raccolta e il risultato presentato: chat, voce, mobile, email, API |
| **Degradazione dignitosa** | Il comportamento del sistema quando il livello di comprensione è indisponibile, lento o incerto (§4.5) |

---

## Chiusura

Questo documento definisce un prodotto che si distingue non per ciò che l'intelligenza artificiale gli consente di fare, ma per ciò che gli impedisce deliberatamente di fare.

L'AI interpreta. Il DSL contrattualizza. Il sistema esegue in modo deterministico. L'utente decide.

Questa struttura è la ragione per cui il prodotto può essere affidato a un'organizzazione senza chiederle un atto di fede, ed è la ragione per cui può evolvere per dieci anni senza che ogni nuova generazione di modelli ne rimetta in discussione le fondamenta.

Le raccomandazioni di §18 e le decisioni di §19 sono la traduzione operativa di questa visione. La loro adozione — in particolare la disciplina di misura prima della funzionalità — determinerà se il prodotto manterrà le promesse qui dichiarate.

---

*Fine del documento.*
