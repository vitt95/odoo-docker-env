# Modello di Sicurezza e Conformità
## AI Agent per Odoo — Natural Language Interaction Layer

---

| Voce | Valore |
|---|---|
| **Titolo** | Modello di Sicurezza e Conformità — identità, confine dei dati, tracciabilità, trattamento |
| **Tipo** | Documento di progettazione — sicurezza |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Dipende da** | `03` §13 · `04` §12 · `06` §11 · `07` §3.7 e §11.3 · `00-registro-decisioni.md` (delibera 27/07/2026) |
| **Risolve** | **D3** come qualificata in delibera · **D39** · **D40** · **RV8** · rischio **R8** del documento di visione |
| **Ambito** | Modello di identità e autorizzazione; confine dei dati verso il fornitore; superficie di iniezione; dati personali nel sistema; ritenzione e cancellazione; segreti; tracciabilità; verifiche |
| **Fuori ambito** | Parere legale; testi contrattuali; valutazione d'impatto sulla protezione dei dati del singolo cliente; sicurezza infrastrutturale di Odoo e PostgreSQL |

> **Avvertenza sulla natura del documento.** Questo è un documento di progettazione della sicurezza, non un parere legale. Dove tocca obblighi normativi, descrive **fatti tecnici** — quali dati esistono, dove, per quanto, chi li vede — e indica ciò che va sottoposto a valutazione legale. La qualificazione giuridica di un trattamento non è una decisione architetturale e non viene presa qui.

---

## 1. Executive Summary

### 1.1 La posizione di partenza è forte, e va detto

Gran parte del lavoro di sicurezza di questo prodotto è già stata fatta, e non in un documento di sicurezza: è stata fatta nella forma del contratto e nella struttura del catalogo.

**Il contratto non contiene operazioni di scrittura.** Non esiste un'operazione mutante che viene respinta: non esiste (`03` §13.1). Non è un controllo, è una proprietà grammaticale, e non si aggira perché non c'è nulla da aggirare.

**Il catalogo è costruito per il singolo utente.** Ciò che l'utente non può vedere non entra nello spazio delle interpretazioni possibili (**D10**). L'autorizzazione agisce prima dell'interpretazione, non dopo l'esecuzione, e non produce trasferimento di informazione per negazione.

**Il contratto non ha superfici di espressione arbitraria.** Nessuna espressione da valutare, nessun domain grezzo, nessun percorso libero, nessun testo interpretato come istruzione (`03` §13.3).

Ne discende una proprietà che vale la pena enunciare per intero, perché è l'argomento di sicurezza più forte del prodotto ed è quello che va difeso da ogni evoluzione futura:

> **Un'iniezione riuscita non può produrre più di un'interrogazione valida su dati che l'utente può già vedere.**

### 1.2 Le quattro decisioni portanti

**L'impronta dei permessi è un meccanismo, non un attributo** (§2.5). `04` §7.6 la usa come chiave di memorizzazione e `04` §10.4 vi fonda una proprietà di sicurezza. Odoo non la fornisce: va costruita, e va costruita in modo che il fallimento sia sicuro. È **D39**, e §2.5 ne definisce la composizione.

**Il catalogo è informazione riservata, non «solo metadati»** (§3.3). È la constatazione meno intuitiva del documento. La terminologia aziendale, i campi personalizzati e la struttura di un'installazione Odoo descrivono l'organizzazione che la usa: linee di prodotto, processi, segmentazione della clientela. Trattarlo come innocuo perché non contiene record è un errore di classificazione.

**L'enunciato dell'utente è un dato personale in uscita, e resta anche dentro** (§3.2, §5.2). `04` §12.3 lo dichiara onestamente per il flusso verso il fornitore. Nessun documento lo affronta per il **Registro**, che conserva enunciati grezzi per dodici mesi.

**La pseudonimizzazione avviene all'ingresso, non alla cancellazione** (§5.3). È l'unica costruzione che concilia l'immutabilità degli stati — proprietà voluta, **D19** — con la cancellabilità di un riferimento personale.

### 1.3 Dove passano i dati

```
UTENTE
  │ enunciato ─────────────────────────────────┐
  ▼                                             │
nli_web ──▶ nli_core ──▶ nli_semantics          │  dati personali possibili
             │  turno       catalogo per utente │  (nomi di clienti, importi)
             │             (filtrato permessi)  │
             │                    │             │
             │                    ▼             ▼
             │             nli_engine ──▶ FORNITORE DEL MODELLO
             │              adattatore     enunciato + catalogo
             │                             ── nessun record ──
             ▼
        nli_observability
         Registro: enunciato, busta, catalogo (impronta), stato, tempi
         ── mai i risultati ──                    12 / 24 mesi
             │
             └──▶ Corpus  ── con segnaposto, D47 ──  anni
```

Due confini contano. Il primo — verso il fornitore — è quello che tutti guardano, ed è già disciplinato dall'architettura. Il secondo — verso il Registro — è quello che nessuno guarda, e conserva più a lungo.

### 1.4 Che cosa questo documento non risolve

Non stabilisce la base giuridica di alcun trattamento: dipende dal cliente, dal contesto e dalla giurisdizione. Non sostituisce la valutazione d'impatto dove serve. Non riduce l'obbligo di verifica del singolo cliente sul proprio fornitore di modello.

Fa una cosa sola: mette il progettista in condizione di sapere **quali dati esistono, dove, per quanto tempo e chi li vede** — che è il presupposto di ogni valutazione successiva, e ciò che di solito manca quando la valutazione viene fatta.

---

## 2. Identità e Autorizzazione

### 2.1 Il principio, e perché costa poco

Ogni esecuzione avviene nell'ambiente Odoo con l'identità dell'utente richiedente. Nessun percorso eleva i privilegi. Nessun servizio esterno accede ai dati.

Ne consegue che **regole di accesso, permessi sui campi e regole sui record continuano a valere senza che il prodotto debba conoscerli**. Il livello conversazionale non reimplementa il modello di sicurezza di Odoo: lo attraversa.

È la scelta che rende il prodotto difendibile davanti a una valutazione di sicurezza con un argomento breve: *se un dato non è visibile nell'interfaccia nativa, non è visibile nemmeno tramite conversazione, e non perché lo controlliamo — perché passiamo dagli stessi controlli.*

### 2.2 Due difese indipendenti, in quest'ordine

| Difesa | Dove agisce | Che cosa impedisce |
|---|---|---|
| **Catalogo filtrato sui permessi** | Prima dell'interpretazione | Che il modello possa **nominare** ciò che l'utente non può vedere |
| **Controllo in risoluzione** | Prima dell'esecuzione | Che un riferimento non autorizzato raggiunga l'ORM |
| **ORM di Odoo** | In esecuzione | Che una lettura aggiri regole di accesso e regole sui record |

Sono tre, non due, e la terza è quella che non abbiamo scritto noi — che è precisamente il motivo per cui è la più affidabile.

**L'ordine è normativo.** Il filtro sui permessi precede la selezione e il budget, mai il contrario (`06` §5.9). Un catalogo selezionato e poi filtrato risulterebbe più povero del previsto senza che nulla lo segnali: il budget sarebbe stato speso su attributi poi rimossi, e la perdita di copertura verrebbe attribuita al budget anziché ai permessi. È un caso in cui un errore di ordine produce una **diagnosi sbagliata**, non solo un difetto.

### 2.3 L'esecuzione asincrona è il punto in cui la tentazione diventa concreta

Con **D20a** l'esecuzione avviene su un processo cron, fuori da una richiesta autenticata. Il codice non ha più un utente «corrente»: va ricostruito dal turno.

È il luogo in cui eseguire con privilegi propri diventa la soluzione più semplice — e sarebbe la violazione di **V2** più difficile da notare, perché il sistema funzionerebbe perfettamente per tutti, mostrando a ciascuno più di quanto deve.

| Requisito | Verifica |
|---|---|
| Ogni thread costruisce l'ambiente con l'identità del richiedente | Controllo sintattico di **D24** esteso ai percorsi del dispatcher |
| Nessun uso di contesti privilegiati nel dispatcher | Come sopra |
| Il contesto societario è ripristinato | **D40**, §2.6 |
| L'impronta dei permessi è ricalcolata, non ereditata dal turno | **D39**, §2.5 |

**L'ultima riga merita una nota.** Fra l'accettazione del turno e la sua esecuzione passa del tempo — poco in condizioni normali, fino alla scadenza del turno sotto carico. Se in quell'intervallo i permessi dell'utente cambiano, l'esecuzione deve usare i permessi **al momento dell'esecuzione**, non quelli registrati all'accettazione. È la stessa regola già applicata alle interrogazioni salvate (`04` §9.5): i permessi sono sempre quelli attuali.

### 2.4 Ciò che il sistema non deve sapere

**Il Dizionario Semantico non conosce gli utenti** (`06` §2.5, **RA8**). Non contiene riferimenti a persone o gruppi, e la tentazione di scrivere *«per l'utente Rossi, "i miei ordini" significa venditore = Rossi»* va respinta: renderebbe il dizionario dipendente dagli utenti e i permessi persistiti, quindi disallineabili.

La regola generale che ne discende, e che vale oltre il dizionario: **nessun componente persiste una decisione di autorizzazione.** L'autorizzazione si valuta, non si conserva. Ogni conservazione è un disallineamento in attesa di accadere, e i disallineamenti di autorizzazione non si manifestano come errori — si manifestano come accessi riusciti.

### 2.5 D39 — Come si costruisce l'impronta dei permessi

`04` §7.6 include *«versione dei permessi»* nella chiave di memorizzazione del catalogo. Odoo non espone alcun valore del genere. Va costruito, e la costruzione è materia di sicurezza perché su di essa poggia la proprietà di `04` §10.4: due utenti condividono un'impronta di catalogo solo se hanno gli stessi permessi, quindi il riuso fra utenti non viola **V2**.

**Composizione.** L'impronta è calcolata su:

| Componente | Perché |
|---|---|
| Gruppi dell'utente | Determinano l'accesso ai modelli e ai campi |
| Stato delle regole di accesso ai modelli | Una modifica cambia ciò che l'utente può leggere |
| Stato delle regole sui record applicabili | Cambiano il perimetro, non solo la struttura |
| Configurazione degli accessi a livello di campo | Determina la presenza di un attributo nel catalogo |
| **Contesto societario** (**D40**) | Le regole sui record sono spesso condizionate dalla società |
| Versione del dizionario | Non è un permesso, ma cambia il catalogo |

**Tre proprietà normative:**

**Fallimento in sicurezza.** Se l'impronta non è calcolabile, il catalogo viene ricostruito. Mai servito da memoria con impronta incerta. Un errore di calcolo deve produrre un costo, non un rischio.

**L'invalidazione a evento è un'ottimizzazione, non la correttezza.** `04` §7.6 prevede l'invalidazione su tre eventi. È giusto averla — riduce le ricostruzioni — ma la correttezza dipende dall'impronta. **Una notifica persa non deve poter produrre una violazione di V2.** È la differenza fra un sistema che è sicuro e uno che è sicuro finché tutti i messaggi arrivano.

**Nessuna impronta condivisa fra utenti diversi per costruzione.** L'identità è nella chiave (`04` §7.6, che lo dichiara non negoziabile). L'impronta serve a invalidare, non a condividere.

### 2.6 D40 — Il contesto societario

In Odoo il perimetro dei record visibili dipende dalle società attive dell'utente, non solo dai suoi gruppi. Dentro una richiesta HTTP quel contesto è presente e nessuno deve occuparsene; con **D20a** non lo è più.

Un'esecuzione che ricostruisce l'utente ma non le sue società attive restituisce gli stessi record che l'utente vedrebbe, **più quelli di una società che aveva deselezionato**. Nessun errore, nessun avviso, un numero diverso.

È una violazione di V2 nella forma più difficile da rilevare, perché non produce un rifiuto mancato ma un risultato più ampio del dovuto — e un risultato più ampio non ha alcun sintomo dal lato di chi lo riceve.

| Requisito | Contenuto |
|---|---|
| **Il turno persiste il contesto** | Società attive, lingua, fuso orario dell'utente al momento della richiesta |
| **L'esecuzione lo ripristina integralmente** | Prima di costruire l'ambiente |
| **Il contesto entra nell'impronta** | Catalogo (**D39**) e riuso delle interpretazioni (`04` §10.4) |
| **Lo stato non lo congela** | Un'interrogazione salvata resa domani da un altro utente rende ciò che *quell'utente* vede adesso |

L'ultima riga è la coerenza con `04` §9.5 e con la regola generale del prodotto: il contesto appartiene all'esecuzione, mai alla domanda — come già il tempo e i permessi.

**Va aggiunto un caso che nessun documento affronta.** Il riuso delle interpretazioni memorizzate (`04` §10.4) usa l'impronta del catalogo come chiave. Poiché il contesto societario entra nel catalogo, due utenti con società attive diverse hanno impronte diverse e non condividono interpretazioni. È il comportamento corretto e si ottiene senza alcun controllo aggiuntivo — ma si ottiene **solo se** il contesto è effettivamente dentro l'impronta. È la ragione per cui §2.5 lo elenca fra i componenti e non fra le note.

---

## 3. Il Confine verso il Fornitore del Modello

### 3.1 Che cosa esce, esattamente

Verso il fornitore viaggiano due cose, e due soltanto:

1. l'**enunciato** dell'utente;
2. il **catalogo**: metadati di struttura e denominazioni, filtrati sui permessi di quell'utente.

Non i record, non i risultati, non i conteggi, non gli identificativi. È l'assunzione **A6** e il vincolo **V7**, ed è la proprietà che chiude alla radice il vettore di iniezione classico (§4).

Va riconosciuto che `04` §12.3 affronta già la questione dell'enunciato, e la affronta con onestà — *«presentare il sistema come se nulla uscisse dal perimetro sarebbe inesatto e verrebbe smentito alla prima valutazione fornitori seria»*. Questo documento non scopre il problema: lo **disciplina**, che è cosa diversa, e aggiunge la parte che nessun documento tocca — il catalogo (§3.3) e la permanenza interna (§5).

### 3.2 L'enunciato

L'enunciato è scritto dall'utente e può contenere qualunque cosa l'utente scriva: un nome di cliente, un importo, un riferimento a una trattativa, il nome di un collega.

**Va classificato correttamente**, perché la classificazione determina gli obblighi:

| Contenuto tipico | Natura |
|---|---|
| *«mostrami gli ordini di Mario Rossi»* | Dato personale di un terzo |
| *«le fatture non pagate del gruppo X»* | Informazione commerciale riservata |
| *«quanto ha venduto Giulia questo mese»* | Dato personale **e** valutazione professionale di un dipendente |
| L'identità di chi scrive, con data e ora | Dato personale di attività lavorativa |

**La terza riga è quella che cambia la natura del problema.** Un enunciato che nomina un dipendente in relazione alla sua prestazione non è solo un dato personale: in diversi ordinamenti europei tocca la disciplina del controllo sull'attività dei lavoratori, e questo vale a prescindere dal fatto che il dato esistesse già in Odoo. **La novità non è il dato: è che ora esiste un archivio delle domande.**

Vale la pena essere precisi su un punto che verrà frainteso: il fatto che la risoluzione referenziale (`03` §11.3) sia deterministica e avvenga nel sistema **non protegge l'enunciato**. La risoluzione è a valle dell'interpretazione. Il nome è già uscito.

### 3.3 Il catalogo è riservato

È la constatazione meno intuitiva del documento, ed è quella che viene classificata male con più frequenza, perché la frase *«sono solo metadati»* è tecnicamente vera e commercialmente pericolosa.

Il catalogo di un'installazione Odoo personalizzata contiene:

- i nomi delle entità che l'organizzazione usa, incluse quelle create su misura;
- la **terminologia aziendale interna**, che è precisamente ciò che il Dizionario Semantico esiste per raccogliere (L2);
- i campi personalizzati, che descrivono i processi e le distinzioni che quell'azienda ritiene rilevanti;
- i valori ammessi degli enumerati: stati di un processo, categorie di clientela, tipologie di prodotto.

Un concorrente che leggesse il catalogo di un'azienda ne ricaverebbe la struttura dei processi, la segmentazione della clientela e le linee di prodotto. Non contiene un solo record, e resta informazione competitiva.

**Conseguenza pratica.** Le tutele contrattuali di §3.4 devono coprire **entrambi** i flussi. Un accordo che escluda l'uso per addestramento dei dati dei clienti ma consideri i metadati un'eccezione tecnica lascia scoperta la parte che descrive l'azienda meglio dei suoi record.

### 3.4 Requisiti verso il fornitore

Sono requisiti di selezione, non preferenze. Un fornitore che non li soddisfa non è utilizzabile in questo prodotto, e la verifica va fatta prima dell'integrazione — l'Adattatore rende sostituibile il fornitore, non retroattivo il trattamento già avvenuto.

| # | Requisito | Perché |
|---|---|---|
| **F-1** | Nessun uso dei dati trasmessi per addestramento | Enunciato e catalogo, senza eccezioni per i metadati (§3.3) |
| **F-2** | Ritenzione nulla o dichiarata e limitata | Una ritenzione «per abuso» di durata indefinita è un archivio non governato |
| **F-3** | Luogo del trattamento dichiarato e selezionabile | Determina il regime applicabile; per alcuni clienti è dirimente |
| **F-4** | Accordo sul trattamento dei dati, con sub-responsabili elencati | Obbligo del cliente, che ricade sul prodotto |
| **F-5** | Cifratura in transito, e nessuna registrazione in chiaro nei sistemi di supporto | Il vettore più frequente non è il modello: sono i log |
| **F-6** | Notifica delle violazioni con tempi dichiarati | Il cliente ha obblighi propri, con scadenze proprie |
| **F-7** | Nessuna revisione umana dei contenuti senza consenso esplicito | Molti fornitori la prevedono in via predefinita |

**F-7 è quello che si scopre tardi.** La revisione umana per il miglioramento del servizio è spesso attiva per impostazione predefinita e disattivabile su richiesta. Significa che una persona presso il fornitore può leggere l'enunciato di un dipendente del cliente. Va disattivato in fase di configurazione, e la disattivazione va verificata, non assunta.

### 3.5 Le tre modalità di erogazione — D8

**D8** resta aperta perché è commerciale. Le sue conseguenze tecniche, però, sono determinate e possono essere fissate qui.

| Modalità | Che cosa esce | Costo | Adatta a |
|---|---|---|---|
| **A — Fornitore pubblico** | Enunciato + catalogo | Basso, variabile per interazione | Uso generale |
| **B — Fornitore con isolamento contrattuale** | Come A, con F-1…F-7 rafforzati e regione dichiarata | Medio | Clienti con requisiti di residenza |
| **C — Modello in ambiente controllato** | **Nulla esce dal perimetro del cliente** | Alto, fisso | Clienti regolamentati, difesa, sanità |

**L'architettura ammette tutte e tre senza modifiche**, perché un solo componente conosce i fornitori (`04` §8) e l'Interprete sta dietro l'Adattatore (**D23**). È il beneficio di **V5**, e va sottolineato che si ottiene senza costo: la modalità C non richiede un prodotto diverso, richiede un adattatore diverso.

**A6 rende la modalità C più praticabile di quanto sarebbe altrimenti.** Poiché il modello riceve solo metadati ed enunciato, il compito che deve svolgere è circoscritto: scegliere da un catalogo. È una classe di compito alla portata di modelli molto più piccoli di quelli generalisti — il che rende l'esecuzione in ambiente controllato una scelta di dimensionamento, non un progetto di ricerca.

### 3.6 Che cosa si può dichiarare, e che cosa no

Vale la pena fissarlo in forma di tabella, perché la dichiarazione sbagliata non produce un difetto tecnico: produce un impegno che qualcuno verificherà.

| Dichiarazione | Ammissibile |
|---|---|
| *«Il contenuto dei record non viene mai trasmesso al modello»* | **Sì** — è A6/V7, verificabile sul grafo delle dipendenze (**D24**) |
| *«Il modello non può accedere ai dati»* | **Sì** — `nli_engine` non dipende dai modelli di dati, ed è un controllo automatico |
| *«Nessun dato aziendale esce dal perimetro»* | **No** — falso per l'enunciato e per il catalogo |
| *«Le domande degli utenti non escono»* | **No** — è precisamente ciò che esce |
| *«Il sistema non può modificare dati»* | **Sì** — non esiste operazione di scrittura nel contratto (`03` §13.1) |
| *«Un utente non può vedere più di quanto vede in Odoo»* | **Sì**, con le tre difese di §2.2 |

La terza e la quarta riga sono le formulazioni che nascono spontaneamente in una presentazione commerciale. Vanno sostituite, non attenuate, e la sostituzione è facile: *«il contenuto dei vostri dati non esce mai; escono la domanda dell'utente e la terminologia della vostra installazione, con queste tutele»* è più lunga di una riga e regge a una verifica.

---

## 4. Superficie di Iniezione

### 4.1 Il vettore classico è chiuso alla radice

L'iniezione di istruzioni attraverso i dati — un record contenente testo costruito per alterare il comportamento del modello che lo legge — è il vettore caratteristico di questi sistemi.

**Nel profilo 1.0 è chiuso**, perché **A6** esclude che il contenuto dei record raggiunga il modello. Non è una difesa che filtra: è l'assenza del canale.

### 4.2 I tre ingressi che restano

| Ingresso | Natura | Presidio |
|---|---|---|
| **Enunciato dell'utente** | Non fidato per definizione | La busta è validata dai cinque livelli; i riferimenti appartengono al catalogo di quell'utente |
| **Dizionario, livello L2** | Curato, immesso da un amministratore del cliente | **D38**: diritti separati; ogni voce è tipizzata, nessun testo libero destinato al modello |
| **Dizionario, livello L3** | Derivato dal linguaggio degli utenti | **D28**: L3 **non è attivo**. Nessuna voce diventa attiva senza approvazione |

**La terza riga è la ragione per cui D28 è una decisione di sicurezza e non solo di qualità.** L'arricchimento automatico costituirebbe un percorso dal linguaggio degli utenti al contesto del modello, senza revisione. Che l'apprendimento errato sia auto-rinforzante (`06` §2.3) è l'argomento di qualità; che sia un ingresso non validato verso il modello è l'argomento di sicurezza, e i due si sommano.

**Requisito aggiuntivo su L2.** Le voci del dizionario sono tipizzate e il vocabolario dei tipi è chiuso (**D30**). Va aggiunto un vincolo sul contenuto: **nessun campo di una voce di dizionario è testo libero destinato al modello.** Denominazioni e sinonimi sono termini, non frasi; la loro lunghezza e la loro forma sono verificabili. È ciò che impedisce che il dizionario diventi il posto dove qualcuno inserisce istruzioni.

### 4.3 Perché la difesa regge comunque

Anche ipotizzando un'iniezione riuscita — il modello si comporta come l'attaccante desidera — l'esito è vincolato:

```
qualunque cosa il modello produca
   └─▶ è una BUSTA                       (nessun altro artefatto è accettato)
        └─▶ vocabolario chiuso            (livello 2)
             └─▶ riferimenti dal CATALOGO DI QUELL'UTENTE   (livello 3)
                  └─▶ nessuna operazione di scrittura       (non esiste)
                       └─▶ esecuzione con i permessi dell'utente
```

> **Il massimo esito di un'iniezione è un'interrogazione valida su dati che l'utente può già vedere.**

È l'argomento di sicurezza più forte del prodotto. **Vale finché nessuna evoluzione consente all'Interprete di produrre qualcosa che non sia una busta validata** — ed è la proprietà da difendere quando la Fase 6 introdurrà la comprensione documentale, che riapre il vettore per definizione portando contenuti non fidati davanti al modello.

Ne discende un vincolo permanente, che vale la pena numerare:

> **V8 — Nessun componente può accettare dall'Interprete un artefatto diverso da una Busta di Interpretazione validata.**

Non è un vincolo nuovo: è la formulazione esplicita di una proprietà che i documenti precedenti danno per acquisita. Renderla esplicita costa una riga e la rende verificabile con il controllo architetturale di **D24**.

### 4.4 Quello che non è un rischio, e va detto

**Il modello non esegue nulla.** Non ha accesso a strumenti, non emette query, non chiama funzioni, non naviga. Produce un documento strutturato che un sistema deterministico valida e applica.

Va detto perché la valutazione di sicurezza di un prodotto con «AI» nel nome parte quasi sempre dal presupposto opposto, e perché la risposta corretta non è rassicurare: è mostrare il grafo delle dipendenze e i quattro controlli automatici di **D24**. Una proprietà verificabile vale più di una dichiarazione, e in questo caso esiste.

---

## 5. Dati Personali dentro il Sistema

### 5.1 Dove vivono

Il prodotto crea tre archivi che prima non esistevano. Nessuno dei tre contiene record aziendali; tutti e tre contengono dati personali.

| Archivio | Contenuto | Ritenzione | Dato personale? |
|---|---|---|---|
| **Turni** | Enunciato, busta, esito di validazione, stato prodotto, utente, data e ora | **12 mesi** | **Sì** — chi ha chiesto cosa, e quando |
| **Registro** | Impronte, tempi, costi, esiti, catalogo per impronta | **24 mesi** | **Sì** — attività per utente |
| **Corpus** | Casi annotati | Anni | Mitigato da **D47** |

### 5.2 La lacuna: il Registro conserva enunciati grezzi

`04` §9.3 motiva la ritenzione lunga così: *«la ritenzione lunga è sostenibile perché nulla di tutto ciò contiene dati aziendali: sono domande, non risposte»*. E `04` §4.9: *«il registro può essere conservato a lungo e consultato ampiamente proprio perché non contiene dati aziendali»*.

**L'argomento è corretto per i dati aziendali e non trasferisce ai dati personali.**

Un turno contiene l'enunciato. L'enunciato può contenere il nome di un cliente. Quindi il Registro contiene, per dodici mesi, un archivio di frasi scritte da dipendenti identificati, con data e ora, alcune delle quali nominano terzi identificati.

Il fatto che non contenga risposte lo rende leggero e lo rende sostenibile; **non lo rende privo di dati personali.** Anzi: un archivio di domande è, sotto il profilo della protezione dei dati, più delicato di un archivio di risultati — le risposte descrivono i dati aziendali, le domande descrivono le persone che le hanno poste.

Questa è la stessa forma di imprecisione già rilevata su A6 in sede di delibera, applicata al confine interno anziché a quello esterno. **`07` ha risolto il problema per il corpus con D47** — sostituzione con segnaposto stabili — e nessun documento lo ha risolto per il Registro, che conserva più a lungo ed è consultato più spesso.

### 5.3 La pseudonimizzazione avviene all'ingresso

La soluzione non è cancellare meglio: è **non scrivere in chiaro**.

```
enunciato     "mostrami gli ordini di Mario Rossi"
     │
     ▼  riconoscimento dei riferimenti a persone e organizzazioni
        (deterministico: confronto con le anagrafiche dell'installazione)
     │
     ├──▶ TURNO         "mostrami gli ordini di ‹P-4471›"      12 mesi
     │
     └──▶ MAPPATURA     ‹P-4471› → res.partner id 4471          separata
                        cifrata · accesso ristretto · cancellabile
```

Tre proprietà, ciascuna necessaria:

**La forma linguistica è conservata.** Il segnaposto occupa la posizione del nome, quindi il turno resta utilizzabile per l'analisi dei fraintendimenti e per il corpus: esercita la risoluzione referenziale esattamente come l'originale (`07` §3.7).

**La mappatura è separata e cifrata.** È l'unico luogo in cui il legame fra segnaposto e persona esiste. La sua cancellazione rende i turni definitivamente anonimi senza toccarli.

**Il riconoscimento è deterministico.** Non è un modello che indovina i nomi: è un confronto con le anagrafiche dell'installazione, che il sistema già conosce. Un riconoscimento probabilistico introdurrebbe un componente non misurato in un percorso di sicurezza — esattamente ciò che l'impianto evita ovunque.

**Limite dichiarato.** Un enunciato può contenere un nome che non corrisponde ad alcuna anagrafica, o un riferimento indiretto. La pseudonimizzazione riduce l'esposizione, non la azzera, e va dichiarata per ciò che è: una misura di minimizzazione, non una garanzia di anonimato. Chi la presenta come anonimizzazione compie lo stesso errore di chi dichiara che nulla esce dal perimetro.

**Nota sul flusso in uscita.** La pseudonimizzazione riguarda la **persistenza**, non la trasmissione: verso il fornitore l'enunciato deve partire integro, altrimenti il modello non può interpretarlo. È la ragione per cui §3.4 e §5.3 sono due presidi distinti e nessuno dei due sostituisce l'altro.

### 5.4 Cancellazione e immutabilità

Gli stati sono immutabili per scelta (**D19**, `04` §9.2): un'operazione non modifica lo stato, ne produce uno nuovo che riferisce il precedente. È la proprietà che rende il sistema diagnosticabile a posteriori, e non va sacrificata.

Confligge però con la cancellazione di un riferimento personale su richiesta. Il conflitto è reale e va risolto per costruzione, non per eccezione:

| Richiesta | Come si soddisfa |
|---|---|
| **Cancellare i riferimenti a una persona** | Si cancella la voce di mappatura (§5.3). I turni restano, i segnaposto diventano privi di corrispondenza. Nessun record immutabile viene toccato |
| **Cancellare l'attività di un utente** | Ritenzione ordinaria, oppure cancellazione dei turni di quell'utente — che non sono immutabili: lo sono gli *stati* |
| **Estrarre l'attività di un utente** | Selezione sui turni, con i segnaposto risolti tramite la mappatura |

**La prima riga è la ragione per cui la pseudonimizzazione va fatta all'ingresso e non a richiesta.** Cancellare un nome da dodici mesi di enunciati in chiaro significa cercare occorrenze di testo in un archivio, con esito incerto e nessuna prova di completezza. Cancellare una riga di mappatura è un'operazione esatta, istantanea e dimostrabile.

È l'applicazione al dominio della protezione dei dati dello stesso criterio che governa tutto l'impianto: **preferire l'impossibilità strutturale al controllo applicativo** (C3).

### 5.5 Che cosa va sottoposto a valutazione legale

Fatti tecnici accertati, che il cliente e il suo consulente devono poter valutare. Non sono qualificazioni giuridiche.

| Fatto | Rilievo |
|---|---|
| Esiste un archivio di enunciati per utente, con data e ora, conservato 12 mesi | Base giuridica; informativa; in alcuni ordinamenti, disciplina del controllo sull'attività lavorativa |
| Gli enunciati possono nominare terzi | Informativa verso i terzi; diritti degli interessati |
| Enunciato e catalogo sono trasmessi a un fornitore esterno | Responsabile del trattamento; sub-responsabili; trasferimento extra-UE se applicabile |
| Il catalogo descrive la struttura dell'organizzazione | Riservatezza contrattuale, non protezione dei dati |
| Il corpus può essere condiviso fra clienti | Ammissibile **solo** con segnaposto (**D47**); da verificare comunque |
| Il sistema non prende decisioni sulle persone | Rilevante: non c'è processo decisionale automatizzato con effetti giuridici |

**L'ultima riga va difesa attivamente.** Nel profilo 1.0 il prodotto interroga dati e li mostra: non valuta, non seleziona, non decide. La Fase 3 introduce azioni previa conferma esplicita, e finché la conferma resta umana ed esplicita la proprietà regge. Il giorno in cui qualcuno proponesse di saltare la conferma in funzione della confidenza — la proposta che **RC6** dichiara come segnale anticipatore — questa riga cambierebbe di segno, e cambierebbe insieme a essa il regime applicabile.

---

## 6. Ritenzione e Cancellazione

### 6.1 I valori

Confermati in delibera (**D26**), con l'esecuzione vincolata:

| Entità | Ritenzione | Note |
|---|---|---|
| Stati intermedi | 30 giorni | Coprono annullamento e ripresa |
| Turni | 12 mesi | Metriche, analisi, candidati per il corpus |
| Interrogazioni salvate | Illimitata | Sono oggetti dell'utente |
| Registro | 24 mesi | Tracciabilità e tendenze |
| **Mappatura dei segnaposto** | **Pari al turno più lungo che vi fa riferimento** | §5.3 — mai più a lungo |
| Corpus | Anni | Con segnaposto (**D47**) |

**La riga sulla mappatura è normativa e va sorvegliata**, perché è la sola che può silenziosamente sopravvivere al proprio scopo. Una mappatura conservata oltre i turni che la usano è un archivio di identità senza finalità.

### 6.2 L'esecuzione

Vincolo di delibera: la cancellazione avviene **a lotti limitati, sul dispatcher differito di D20d**, mai sul pool interattivo e mai in transazione unica.

Cancellare dodici mesi di turni su un'installazione attiva è un evento di blocco sulla banca dati, non un'operazione di manutenzione. È lo stesso carico differito che esegue il corpus (`07` §14.2), e per la stessa ragione: le attività che servono al governo del prodotto non devono essere visibili agli utenti, altrimenti diventano impopolari presso le persone che dovrebbero difenderle.

### 6.3 Cancellazione di un cliente

Alla cessazione, l'installazione va rimossa per intero: turni, registro, mappature, dizionario L2, corpus derivato dai suoi casi.

**Il corpus è il punto delicato**, perché è l'unico archivio progettato per attraversare i confini fra clienti (`06` §7.4, l'asset che si accumula). La regola: i casi con segnaposto e terminologia generalizzata restano; i casi che contengono terminologia specifica dell'organizzazione seguono il cliente. La distinzione va registrata **all'inserimento**, perché a posteriori richiederebbe di rileggere l'intero corpus.

---

## 7. Segreti e Configurazione

### 7.1 Dove vivono le credenziali

Nella configurazione dell'ambiente. Mai nel database, mai nel codice, mai nel registro, mai nei messaggi di errore, mai nelle risposte.

Il repository usa già `.env` con `.env.example` versionato: la convenzione esiste e va estesa, non sostituita. La rotazione di una credenziale non deve richiedere modifiche al codice né un rilascio.

### 7.2 La configurazione che non è un segreto ma è sensibile

| Parametro | Ambito | Nota |
|---|---|---|
| Fornitore e modello attivo | Ambiente | Va registrato con ogni misura (`07` §4.1) |
| Credenziali | Ambiente | §7.1 |
| Soglie di confidenza | Installazione | Calibrate sul modello attivo (**D51**) |
| Limite predefinito e massimo | Installazione | 80 / 500 (**D13**) |
| Budget di complessità | Installazione | 60 attributi (**D31**) |
| Ritenzione | Installazione | §6.1 |
| **Modalità di erogazione** | Installazione | A / B / C — §3.5 |

**L'ultima riga va resa visibile nell'interfaccia di amministrazione**, non solo nella configurazione. Un cliente che ha scelto la modalità C deve poter verificare in ogni momento che sia quella attiva, senza chiederlo a nessuno. Una garanzia contrattuale che non è ispezionabile dal cliente vale meno di quanto costa.

### 7.3 Ciò che non deve finire nei registri diagnostici

È il vettore più frequente e il meno progettato. In ordine di probabilità:

- credenziali del fornitore in un messaggio di errore di rete;
- enunciato completo in un registro diagnostico a livello di debug, che sopravvive alla ritenzione dei turni perché vive altrove;
- catalogo completo in un registro di traccia, con la terminologia del cliente (§3.3);
- risposta del fornitore in chiaro in caso di errore di parsing.

**Il quarto è quello che si introduce in buona fede** mentre si diagnostica un problema di generazione vincolata, e resta. Va trattato come i controlli di **D24**: una verifica automatica che cerchi la scrittura di enunciati e cataloghi al di fuori dei componenti autorizzati costa poco all'inizio e molto dopo.

---

## 8. Isolamento fra Installazioni

Ogni installazione Odoo è un perimetro separato: banca dati propria, dizionario proprio, registro proprio. Non esiste un servizio condiviso che veda più clienti — è una conseguenza di **D23** (l'Interprete vive nel processo Odoo) e non una misura aggiuntiva.

**L'unico artefatto che attraversa i confini è il corpus generalizzato** (`06` §7.4), ed è l'unico punto in cui l'isolamento va garantito da una procedura anziché dalla struttura. Le due regole sono in §6.3 e in **D47**.

Va notato che questa proprietà si perderebbe con l'estrazione dell'Interprete in un servizio separato — l'opzione rinviata da **D23**. Non è un argomento contro l'estrazione: è un requisito da portare con sé il giorno in cui verrà fatta, quando l'isolamento fra clienti smetterebbe di essere una proprietà della distribuzione e diventerebbe una responsabilità del servizio.

---

## 9. Tracciabilità

### 9.1 Che cosa si ricostruisce

Il Registro conserva, per ogni interazione: chi, quando, da quale canale, con quale contesto societario, che cosa ha chiesto, quale catalogo ha ricevuto, come è stato interpretato, che cosa è stato validato, quale stato è stato prodotto, che cosa è stato eseguito, quanto è costato.

Non conserva i risultati. È la scelta che rende sostenibile la ritenzione lunga sul piano dei **dati aziendali** — con la precisazione di §5.2 sul piano dei dati personali.

Con la provenienza (`03` §10.3), la ricostruzione arriva al livello utile: non solo *che cosa* è stato frainteso, ma **quali parole** lo hanno causato.

### 9.2 La tracciabilità è anche una difesa

Un archivio completo di chi ha chiesto cosa consente di rispondere a una domanda che, dopo un incidente, viene sempre posta: *questo utente ha avuto accesso a quei dati?*

La risposta è esatta e non richiede ricostruzioni: lo stato dichiara l'interrogazione in termini semantici, il turno dichiara l'identità e il contesto, il catalogo registrato dichiara che cosa l'utente poteva nominare in quel momento.

**È una proprietà che l'interfaccia nativa di Odoo non offre.** Nessuno registra quali filtri un utente ha applicato in una vista lista. Il livello conversazionale, come effetto collaterale del proprio impianto di misura, produce una tracciabilità di accesso migliore di quella del sistema che lo ospita. Vale la pena saperlo: è un argomento di vendita presso i clienti regolamentati, ed è anche — §5.5 — parte di ciò che va dichiarato.

### 9.3 Chi può leggere il Registro

Il Registro contiene attività per utente. **L'accesso va autorizzato come un dato personale, non come un dato tecnico.**

| Ruolo | Accesso |
|---|---|
| Utente | I propri turni |
| Amministratore del cliente | Aggregati; singoli turni solo con finalità dichiarata |
| Responsabile della qualità | Turni con segnaposto, per l'analisi dei fraintendimenti |
| Fornitore, in assistenza | Solo su richiesta del cliente, tracciata, con segnaposto |

**La terza riga è resa possibile da §5.3**: poiché gli enunciati sono già pseudonimizzati alla scrittura, il lavoro di qualità non richiede accesso ai dati personali. È il beneficio operativo della scelta di pseudonimizzare all'ingresso, e da solo la giustifica anche a prescindere dagli obblighi.

---

## 10. Degradazione Sicura

Le modalità di guasto vanno progettate, perché un sistema che degrada male degrada quasi sempre verso il permissivo.

| Guasto | Comportamento richiesto |
|---|---|
| Fornitore non raggiungibile | Nessuna interpretazione. **Mai** un ripiego che indovini |
| Impronta dei permessi non calcolabile | Catalogo ricostruito (**D39**) |
| Contesto societario assente sul turno | Turno respinto, non eseguito con contesto predefinito (**D40**) |
| Registro non disponibile | L'interazione prosegue (`04` §4.9): l'osservabilità non blocca l'uso |
| Dizionario non disponibile | Nessuna interpretazione: senza catalogo non c'è vocabolario |
| Bus non disponibile | Ripiego a interrogazione periodica (`05` §3.5), da misurare |
| Validazione non completabile | Nessuna esecuzione. **D14**, e §12.1 del DSL |

**La terza riga è quella che verrà scritta al contrario.** Di fronte a un turno privo di contesto societario, la reazione naturale è eseguire con la società predefinita dell'utente — sembra ragionevole e produce un risultato. Produce anche, in un'installazione multi-società, esattamente il risultato più ampio del dovuto descritto in §2.6. Il turno va respinto.

**La quarta riga è l'unica eccezione**, ed è deliberata: un difetto nell'osservabilità non deve diventare un'interruzione del servizio. È l'inversione di priorità che `04` §4.9 dichiara *frequente e sempre costosa*.

---

## 11. Verifiche

Le proprietà di sicurezza vanno verificate, non dichiarate. Sei prove, tutte costruite, nessuna osservazionale — un valore atteso di zero incidenti non si misura aspettando.

| # | Prova | Verifica |
|---|---|---|
| **P-1** | **Catalogo per utente** | Un utente senza permesso su un attributo non lo trova nel proprio catalogo (**D10**) |
| **P-2** | **Revoca dei permessi** | Revocato un permesso, il catalogo memorizzato non viene servito (**D39**) |
| **P-3** | **Multi-società** | Un utente con una società deselezionata non riceve record di quella società (**D40**) |
| **P-4** | **Interrogazione condivisa** | Eseguita da un utente con meno privilegi, rende meno dati (`04` §9.5) |
| **P-5** | **Esecuzione asincrona** | Il dispatcher esegue con l'identità del richiedente, mai con privilegi propri (`05` §3.4) |
| **P-6** | **Assenza di elevazione** | Nessun contesto privilegiato nei percorsi di interrogazione (**D24**) |

A queste si aggiungono tre verifiche che appartengono a questo documento e non erano previste altrove:

| # | Prova | Verifica |
|---|---|---|
| **P-7** | **Pseudonimizzazione** | Un enunciato contenente un'anagrafica nota è persistito con segnaposto; la mappatura è separata e cifrata (**D54**) |
| **P-8** | **Dispersione nei registri diagnostici** | Nessun enunciato e nessun catalogo scritto fuori dai componenti autorizzati (**D60**) |
| **P-9** | **Confine del fornitore** | Il traffico verso il fornitore contiene enunciato e catalogo, e nient'altro (**A6**, **V7**) |

**P-9 va eseguita osservando il traffico, non leggendo il codice.** Il grafo delle dipendenze di **D24** dimostra che `nli_engine` non *può* accedere ai dati; P-9 dimostra che non lo *fa*. Sono due affermazioni diverse, e davanti a una valutazione di sicurezza esterna serve la seconda.

**P-2 e P-3 sono le due che nessuno costruirebbe spontaneamente**, perché verificano proprietà che in esercizio ordinario non si manifestano mai e falliscono in silenzio. Sono anche le due introdotte dalla delibera, e la loro assenza dal piano originale è la ragione per cui compaiono qui in evidenza.

---

## 12. Rischi

### RG1 — L'enunciato viene trattato come non personale

**Descrizione.** L'argomento *«sono domande, non risposte»* viene esteso dai dati aziendali ai dati personali, e il Registro cresce come archivio non governato.
**Impatto. Alto**, e crescente con la vita del prodotto: un archivio di dodici mesi di attività dei dipendenti scoperto al terzo anno è un problema che nessuna correzione tecnica risolve retroattivamente.
**Mitigazione.** Pseudonimizzazione all'ingresso (**D54**); ritenzione della mappatura vincolata (**D61**); §5.5 sottoposto a valutazione legale prima del primo cliente.
**Segnale anticipatore.** Richieste di conservare i turni «per un po' più a lungo, per l'analisi».

### RG2 — Il catalogo viene classificato come innocuo

**Descrizione.** *«Sono solo metadati»* porta a escludere il catalogo dalle tutele contrattuali con il fornitore.
**Impatto. Medio-alto**, di natura commerciale più che normativa: è la terminologia e la struttura dei processi del cliente.
**Mitigazione.** **D57**; requisiti F-1…F-7 formulati su *entrambi* i flussi.
**Segnale anticipatore.** Accordi che distinguono «dati dei clienti» da «metadati tecnici».

### RG3 — Elevazione di privilegi nel dispatcher

**Descrizione.** Nel contesto asincrono, l'esecuzione con privilegi propri è la soluzione più rapida a un problema di ricostruzione dell'identità.
**Impatto. Critico**: violazione di **V2** che non produce alcun sintomo, perché il sistema continua a funzionare mostrando a ciascuno più del dovuto.
**Mitigazione.** Controllo sintattico di **D24** esteso ai percorsi del dispatcher; prova **P-5**.
**Segnale anticipatore.** Discussioni su prestazioni del dispatcher che menzionano il costo della costruzione dell'ambiente per utente.

### RG4 — Catalogo memorizzato servito dopo una revoca

**Descrizione.** L'invalidazione a evento non arriva e il catalogo continua a esporre riferimenti revocati.
**Impatto. Alto**: violazione di V2 a livello di vocabolario, cioè della prima delle tre difese.
**Mitigazione.** **D39**, fallimento in sicurezza; l'impronta è la correttezza, la notifica è l'ottimizzazione; prova **P-2**.
**Segnale anticipatore.** Proposte di allungare la validità della memorizzazione per ridurre le ricostruzioni.

### RG5 — Dispersione nei registri diagnostici

**Descrizione.** Enunciati, cataloghi o credenziali finiscono in registri che vivono fuori dalla ritenzione governata.
**Impatto. Alto**, e particolarmente sgradevole perché vanifica misure corrette prese altrove.
**Mitigazione.** **D60** e la verifica automatica associata; prova **P-8**.
**Segnale anticipatore.** Registrazioni a livello di debug introdotte per diagnosticare la generazione vincolata e mai rimosse.

### RG6 — La conferma umana viene erosa

**Descrizione.** In Fase 3, la conferma esplicita viene resa condizionale alla confidenza dichiarata dal modello.
**Impatto. Critico**, su due piani distinti: è il percorso per cui un fraintendimento plausibile diventa un'azione sui dati (**RC6**), ed è ciò che trasformerebbe il prodotto in un sistema che decide — cambiando il regime applicabile descritto in §5.5.
**Mitigazione.** Divieto permanente di §5.7 del piano di valutazione; **D51** impone la ricalibrazione ma non legittima l'uso decisionale.
**Segnale anticipatore.** Proposte di ridurre le conferme in funzione della confidenza. È lo stesso segnale di RC6, e qui vale doppio.

### RG7 — La mappatura sopravvive al proprio scopo

**Descrizione.** La tabella di corrispondenza fra segnaposto e identità resta dopo la scadenza dei turni che vi facevano riferimento.
**Impatto. Medio-alto**: un archivio di identità senza finalità, creato da una misura di protezione.
**Mitigazione.** **D61**: ritenzione pari al turno più lungo che vi fa riferimento, con cancellazione automatica.
**Segnale anticipatore.** Nessuno — è la ragione per cui la cancellazione dev'essere automatica e non procedurale.

### RG8 — Dichiarazione commerciale non sostenibile

**Descrizione.** Il prodotto viene presentato con formulazioni che una valutazione fornitori smentisce.
**Impatto. Alto sulla fiducia**, e difficilmente recuperabile: la scoperta avviene in sede di verifica, davanti a chi decide.
**Mitigazione.** **D63** e la tabella di §3.6; formazione di chi presenta il prodotto sulle due righe non ammissibili.
**Segnale anticipatore.** Materiali commerciali che contengono *«nessun dato esce»*.

---

## 13. Decisioni Richieste

Numerazione in continuità (D1–D53).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D54** | **Pseudonimizzazione degli enunciati all'ingresso**, con mappatura separata, cifrata e ad accesso ristretto (§5.3) | **Adottare** | Il Registro diventa un archivio non governato di dati personali; la cancellazione su richiesta resta un'operazione a esito incerto |
| **D55** | **Vincolo V8**: nessun componente accetta dall'Interprete un artefatto diverso da una Busta validata (§4.3) | **Adottare** | La proprietà che regge l'intera difesa dall'iniezione resta implicita, e la Fase 6 la eroderà senza che nessuno debba dichiararlo |
| **D56** | Requisiti **F-1…F-7** come criteri di selezione del fornitore, verificati prima dell'integrazione (§3.4) | **Adottare** | Il trattamento già avvenuto non è reversibile; l'Adattatore rende sostituibile il fornitore, non retroattivo il trasferimento |
| **D57** | Il **catalogo è classificato come informazione riservata** del cliente; le tutele contrattuali coprono entrambi i flussi (§3.3) | **Adottare** | La parte che descrive l'azienda meglio dei suoi record resta fuori dalle tutele |
| **D58** | Tre **modalità di erogazione** A / B / C, con la modalità attiva **visibile nell'amministrazione** (§3.5) | **Adottare** — chiude la parte tecnica di **D8** | Il cliente non può verificare da solo la garanzia che gli è stata data |
| **D59** | **Nessun campo di una voce di dizionario è testo libero** destinato al modello (§4.2) | **Adottare** | Il dizionario diventa il luogo dove si possono immettere istruzioni |
| **D60** | Divieto di scrittura di enunciati, cataloghi e credenziali nei registri diagnostici, con **verifica automatica** (§7.3) | **Adottare** | Il vettore più frequente resta aperto, e vanifica le misure prese altrove |
| **D61** | Ritenzione della mappatura **pari al turno più lungo che vi fa riferimento**, con cancellazione automatica (§6.1) | **Adottare** | Un archivio di identità senza finalità, prodotto da una misura di protezione |
| **D62** | **Nessun componente persiste decisioni di autorizzazione**: l'autorizzazione si valuta a ogni esecuzione (§2.4) | **Adottare** | I disallineamenti di autorizzazione non si manifestano come errori, ma come accessi riusciti |
| **D63** | Le **dichiarazioni ammissibili** di §3.6 vincolano la comunicazione verso i clienti | **Adottare** | RG8: la formulazione più naturale è anche quella falsa |

**D54, D55 e D56 sono le decisioni bloccanti.** D54 perché la pseudonimizzazione retroattiva non esiste: ogni giorno di esercizio senza di essa produce dati in chiaro che nessuna decisione successiva ripulisce. D55 perché è la formulazione esplicita della proprietà su cui poggia tutta la difesa dall'iniezione. D56 perché va verificata **prima** della prima chiamata a un fornitore, e dopo non è più una scelta.

---

## 14. Glossario

| Termine | Definizione |
|---|---|
| **Enunciato** | La frase scritta dall'utente. Unico contenuto non strutturato che raggiunge il modello |
| **Catalogo** | Metadati di struttura e denominazioni, filtrati sui permessi di un singolo utente |
| **Impronta dei permessi** | Valore calcolato che descrive lo stato di autorizzazione di un utente in un momento; chiave di memorizzazione e di invalidazione |
| **Contesto societario** | Insieme delle società attive dell'utente, che determina il perimetro dei record visibili |
| **Segnaposto** | Riferimento stabile che sostituisce un'identità in un enunciato persistito |
| **Mappatura** | Archivio separato e cifrato che lega i segnaposto alle identità |
| **Modalità di erogazione** | A: fornitore pubblico · B: fornitore con isolamento contrattuale · C: modello nel perimetro del cliente |
| **Pseudonimizzazione** | Sostituzione di un identificativo con un riferimento, reversibile solo tramite un archivio separato. **Non** anonimizzazione |
| **V8** | Nessun componente accetta dall'Interprete un artefatto diverso da una Busta validata |

---

## Chiusura

La sicurezza di questo prodotto non è stata progettata in questo documento. È stata progettata nel contratto, quando si è deciso che le operazioni di scrittura non esistessero anziché essere vietate; e nel catalogo, quando si è deciso che fosse costruito per il singolo utente anziché filtrato a valle. Quelle due scelte producono una proprietà che pochi sistemi di questa classe possono affermare: **un'iniezione riuscita non ottiene più di un'interrogazione valida su dati che l'utente già vede.**

Il compito di questo documento era diverso: verificare che la proprietà regga dove i documenti precedenti non guardavano. Regge in tre casi su quattro.

Il caso in cui non reggeva è il **confine interno**. L'attenzione era tutta sul flusso verso il fornitore — giustamente, ed è lì che `04` §12.3 ha detto la cosa onesta invece di quella comoda. Ma il prodotto crea anche tre archivi che prima non esistevano, e per uno di essi l'argomento *«sono domande, non risposte»* è stato applicato oltre il suo dominio di validità. È corretto per i dati aziendali. Non lo è per i dati personali, e sotto quel profilo un archivio di domande è più delicato di uno di risposte: le risposte descrivono i dati, le domande descrivono chi le ha poste.

**D54** risolve il problema nell'unico modo che non richiede disciplina permanente: non scrivendo in chiaro. È lo stesso criterio che governa tutto l'impianto — l'impossibilità strutturale al posto del controllo applicativo — applicato al dominio in cui di solito si sceglie la strada opposta, cioè cancellare bene invece di non scrivere.

Resta un punto che va detto per intero, perché è quello su cui il prodotto verrà giudicato da chi decide. **La formulazione commerciale più naturale è anche quella falsa.** *«Nessun dato aziendale esce dal perimetro»* è vera per i record e falsa per l'enunciato e per il catalogo, e la sua smentita non avviene in una discussione tecnica: avviene durante una valutazione fornitori, davanti al cliente. La formulazione corretta è più lunga di una riga e regge a una verifica — ed è per questo che **D63** vincola la comunicazione, cosa che un documento di sicurezza normalmente non fa.

**Documenti successivi:**

1. **Linee guida di Esperienza Utente** — interpretazione ispezionabile, stati non ideali, disambiguazione *(dipende da A9, `07` §12.5, D53)*
2. **Linee guida di Annotazione** — artefatto operativo, generato dal primo corpus *(dipende da D42, D46, D47)*
3. **Valutazione d'impatto sulla protezione dei dati** — per installazione, a carico del cliente, con §5.5 come base di fatto *(dipende da D54)*

---

*Fine del documento.*
