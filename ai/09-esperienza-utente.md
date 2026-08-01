# Linee Guida di Esperienza Utente
## AI Agent per Odoo — Natural Language Interaction Layer

---

| Voce | Valore |
|---|---|
| **Titolo** | Linee guida di Esperienza Utente — interpretazione ispezionabile, stati non ideali, disambiguazione |
| **Tipo** | Documento di progettazione — esperienza |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Dipende da** | `02` §10 · `03` §10 e §11 · `04` §11 · `05` §3.5 e §4.2 · `07` §12.5 · `00-registro-decisioni.md` |
| **Risolve** | Assunzione **A9** · principio **P3** · vincolo **V4** · **D53** · la parte di esperienza di **D20c** e **D13** |
| **Ambito** | Interpretazione ispezionabile; correzione diretta; disambiguazione; stati non ideali; attesa; conversazione progressiva; coerenza visiva; accessibilità; misura dell'esperienza |
| **Fuori ambito** | Grafica e specifiche visive puntuali; testi definitivi dell'interfaccia; struttura dei componenti web |

> **Prerequisiti.** Il documento presuppone adottate **D4** (Stato di Interrogazione come oggetto centrale), **D25** (token di `ui_brand_tokens`), **D13** (limite 80 / 500), **D20c** (limiti di carico con rifiuto esplicito) e **D53** (origine, provenienza e presenza come indicatori propri).

---

## 1. Executive Summary

### 1.1 Perché l'esperienza è una questione di sicurezza del prodotto

Il documento di visione fonda su **A9** — *l'utente legge l'interpretazione mostrata e la corregge quando non corrisponde all'intenzione* — l'intera difesa contro **R1**, il rischio di rango 1 del progetto.

A9 è dichiarata come assunzione **da validare con i clienti pilota**, e non è mai stata validata. Ne discende che il lavoro descritto qui non è rifinitura: è la realizzazione di una difesa che l'architettura ha progettato e che solo l'interfaccia può rendere effettiva. Un'interpretazione corretta e mostrata male equivale a un'interpretazione non mostrata.

### 1.2 Le quattro decisioni portanti

**L'interpretazione non si apre: è già lì** (§3.5). Se leggerla richiede un'azione, A9 è falsa per costruzione — nessuno compie un'azione per verificare qualcosa che di solito è giusto. L'interpretazione sta sopra il risultato, sempre visibile, senza interazione.

**La salienza è graduata per origine, non uniforme** (§3.3). Mostrare tutto con lo stesso peso è il modo più efficace per non far leggere nulla. Ciò che l'utente ha chiesto si conferma da sé; **ciò che il sistema ha inferito è la parte che può sorprenderlo**, ed è quella che deve attirare l'occhio.

**Il rifiuto per carico non è un errore** (§6.7). **D20c** produce rifiuti visibili, ed è la decisione che verrà contestata per prima. Un messaggio scritto male la farà rimuovere entro un trimestre — e con essa la protezione dell'ERP.

**La conferma della Fase 3 va progettata adesso** (§8.4). Se la conferma esplicita risulterà fastidiosa, i clienti ne chiederanno la disattivazione, ed è esattamente il percorso descritto da **RG6**. Rendere la conferma economica è un requisito di sicurezza travestito da requisito di esperienza.

### 1.3 Il paradosso che governa tutto il documento

Va enunciato subito perché condiziona ogni scelta successiva.

> **La difesa fondata su A9 si indebolisce proprio quando il sistema migliora.**

Un utente che riceve interpretazioni corrette per settimane smette di verificarle. Non per negligenza: è il comportamento razionale di fronte a uno strumento affidabile. Man mano che l'accuratezza sale, la vigilanza scende — e i fraintendimenti residui, che sono per selezione i più plausibili, incontrano una verifica sempre più debole.

Ne discende che **la difesa non può essere la vigilanza uniforme**. Chiedere all'utente di leggere ogni volta tutto è una richiesta che verrà disattesa, e progettare su una richiesta disattesa significa progettare sul nulla.

La strategia di questo documento è diversa: rendere la lettura **gratuita** per la parte che si conferma da sé, e **inevitabile** per la parte che può sorprendere. Il costo cognitivo va speso dove serve, e solo lì.

### 1.4 Che cosa questo documento non fa

Non specifica la grafica. Non fissa i testi definitivi: gli esempi sono indicazioni di registro e di contenuto informativo, da rifinire con la revisione linguistica e la prova con utenti reali.

Non sostituisce la validazione di A9. §11 dice come misurarla; l'esito potrebbe imporre di rivedere scelte di questo documento, ed è il modo corretto di procedere.

---

## 2. Il Fraintendimento Plausibile

### 2.1 Perché è diverso da un errore

Un errore ordinario si annuncia: un messaggio, un risultato assurdo, un'operazione che non parte. L'utente lo vede e reagisce.

Il fraintendimento plausibile no. Il sistema comprende una cosa diversa da quella richiesta e produce un risultato **credibile**: l'utente riceve ventitré ordini quando la sua domanda ne avrebbe prodotti diciannove, e non ha alcun motivo di sospettare.

| | Errore ordinario | Fraintendimento plausibile |
|---|---|---|
| Si manifesta | Subito | Mai, o molto dopo |
| Chi lo rileva | L'utente | Nessuno |
| Costo | Un tentativo perso | Una decisione presa su un dato sbagliato |
| Difesa | Messaggio d'errore | **Solo l'interpretazione ispezionabile** |

L'ultima riga è la ragione per cui questo documento esiste. Per questa classe di guasti non c'è un rilevatore automatico: se l'interpretazione fosse verificabile da una macchina, non ci sarebbe bisogno di interpretare.

### 2.2 Dove nasce, concretamente

Vale la pena elencare i casi reali, perché orientano dove concentrare la salienza.

| Richiesta | Lettura plausibile e sbagliata |
|---|---|
| *«gli ultimi cinque ordini»* | Ordinati per data d'ordine anziché per data di conferma |
| *«le fatture di questo mese»* | Data di emissione anziché data di scadenza |
| *«quest'anno»* | Anno solare in un'azienda con esercizio non solare |
| *«gli ordini di Rossi»* | Rossi cliente anziché Rossi venditore |
| *«i clienti importanti»* | Una definizione di *importante* diversa da quella che l'utente ha in mente |
| *«mostrami tutto»* | Primi 80 record, presentati come se fossero tutti |

**Hanno una cosa in comune: nessuna riguarda l'entità.** L'entità è la parte che il sistema individua meglio ed è anche quella che l'utente verifica per prima, perché è la più visibile. I fraintendimenti vivono nei **criteri**: quale data, quale ruolo, quale definizione, quale ordinamento.

È l'indicazione di progetto più utile del documento: **la salienza va sui criteri, non sull'entità.**

### 2.3 La coerenza è una condizione della fiducia

`02` §10.6 lo dichiara: la stessa richiesta deve produrre sempre la stessa interpretazione. Un sistema che risponde in modo diverso a parità di domanda è percepito come inaffidabile **anche quando entrambe le risposte sono corrette**.

È il punto in cui l'esperienza incontra la metrica di stabilità di **D48**. Una stabilità del 96% è tecnicamente buona e si traduce in un utente su venticinque che vede il sistema cambiare idea senza motivo apparente — e quell'utente lo racconta ai colleghi.

Dal lato dell'interfaccia ne discende una regola: **le richieste risolte per via deterministica non devono poter variare.** Il percorso rapido lessicale (Fase A), le interrogazioni salvate e le correzioni fatte dall'interfaccia sono già deterministici. Vanno preferiti anche quando una chiamata al modello sarebbe altrettanto rapida, perché comprano coerenza percepita oltre che costo.

---

## 3. L'Interpretazione Ispezionabile

### 3.1 Che cosa deve contenere

Tutto ciò che determina il risultato. Se un elemento influenza quali record l'utente vede, deve comparire — senza eccezioni per gli elementi «tecnici», che sono precisamente quelli che l'utente non può indovinare.

| Elemento | Sempre visibile |
|---|---|
| Entità | Sì |
| Condizioni di filtro | Sì, tutte |
| Raggruppamenti | Sì |
| Ordinamento | Sì — è la sede del fraintendimento di *«ultimi»* |
| Limite | Sì — vedi §6.5 |
| Attributi mostrati | Sì |
| Vista | Sì, in forma discreta |
| Periodo risolto | **Sì** — *«luglio 2026»*, non *«questo mese»* |

**L'ultima riga è un requisito, non una preferenza.** Un'espressione temporale mostrata come l'utente l'ha scritta non è verificabile: *«questo mese»* conferma sé stesso. Mostrare il periodo **risolto** è ciò che consente di accorgersi che l'anno fiscale inizia a luglio, o che *«questa settimana»* parte di lunedì e non di domenica.

### 3.2 Come si scrive

In linguaggio umano. Mostrare un'espressione tecnica equivale a non mostrare nulla (`02` §10.3).

> Sto mostrando: **Ordini di vendita** · confermati · di **luglio 2026** · raggruppati per **venditore** · ordinati per data d'ordine, dal più recente · primi 5

Quattro regole di redazione:

**Nessun nome tecnico.** Né modelli, né campi, né operatori. Il vocabolario è quello del Dizionario Semantico, cioè quello dell'azienda.

**Nessuna sintassi.** Niente parentesi, niente `AND`/`OR` in forma letterale, niente simboli di confronto. Le condizioni si compongono in una frase; se non si compongono, la struttura è troppo complessa per essere mostrata così — e §3.7 dice cosa fare.

**I criteri si esplicitano.** *«ordinati per data»* non basta: quale data, e in quale verso.

**Si scrive in prima persona e al presente.** *«Sto mostrando»*, non *«Risultato della query»*. Non è una scelta di tono: dichiara che c'è un'interpretazione in corso, e quindi qualcosa da verificare.

### 3.3 La salienza graduata — D53 resa visibile

Ogni elemento dello stato porta la propria `origin` (`03` §10.2). È il dato che rende possibile la strategia di §1.3.

| `origin` | Che cos'è | Come si mostra |
|---|---|---|
| `user` | L'utente lo ha chiesto | Normale. Si conferma da sé |
| `inferred` | Il sistema lo ha derivato | **Distinto e leggibile a colpo d'occhio**, con la regola applicata accessibile |
| `default` | Valore predefinito dell'installazione | Discreto ma presente, ispezionabile |

**È la decisione di progetto più importante del documento.**

Quando l'utente chiede *«gli ultimi cinque ordini»* e riceve cinque record, il criterio con cui sono stati scelti — decrescente per data d'ordine — è un'inferenza. Se non fosse dichiarata come tale, l'utente non avrebbe modo di sapere che *«ultimi»* è stato letto come *«più recenti per data d'ordine»* e non per data di conferma.

Mostrare l'inferito come tutto il resto lo rende invisibile: l'occhio scorre una riga uniforme e si ferma sulla prima cosa che riconosce, cioè l'entità. Distinguerlo concentra l'attenzione dove i fraintendimenti effettivamente vivono (§2.2), e costa all'utente uno sguardo invece di una lettura.

**Regola sulla forma della distinzione:** deve funzionare senza colore. Il colore è il primo canale che si perde — daltonismo, alto contrasto, stampa, schermi economici — e la distinzione fra chiesto e inferito è troppo importante per dipendere da esso. Forma, posizione o marcatura testuale, con il colore come rinforzo e non come portante.

### 3.4 La provenienza, e l'evidenziazione incrociata

Ogni elemento derivato da un'espressione dell'utente registra il frammento che lo ha generato (`03` §10.3).

Ne discende l'interazione più efficace dell'intero prodotto per far riconoscere un fraintendimento: **l'evidenziazione incrociata** fra la frase scritta e l'interpretazione. Passando sull'elemento *«luglio 2026»*, si illumina *«di questo mese»* nella frase; e viceversa.

L'utente vede che *«di questo mese»* ha prodotto un filtro sulla **data d'ordine** anziché sulla data di consegna, e lo corregge in due secondi. È il caso d'uso per cui la provenienza è nel contratto anziché nella diagnostica.

**Limite da rispettare:** l'evidenziazione incrociata richiede un dispositivo di puntamento. Su mobile e per chi naviga da tastiera va sostituita da un equivalente esplicito — la provenienza mostrata accanto all'elemento — non omessa.

### 3.5 Dove sta

**Sopra il risultato. Sempre visibile. Senza interazione.**

È il requisito da cui dipende A9, e va difeso contro le tre proposte che si presenteranno, tutte ragionevoli e tutte da respingere:

| Proposta | Perché no |
|---|---|
| *«Mettiamola in un pannello che si apre»* | Un'azione per verificare qualcosa che di solito è giusto non viene compiuta. Equivale a non mostrarla |
| *«Mostriamola solo quando la confidenza è bassa»* | La confidenza è debolmente calibrata (**RC6**): un fraintendimento plausibile è precisamente il caso in cui il modello è sicuro |
| *«Occupa spazio»* | Ne occupa. È il costo della difesa contro il rischio di rango 1, e va pagato |

La seconda è la più insidiosa perché sembra un'ottimizzazione intelligente. È invece l'inversione esatta: userebbe come filtro proprio il segnale che fallisce nei casi che contano.

**V4 lo impone comunque**: nessun risultato può essere presentato senza la relativa interpretazione, ed è un invariante misurato al 100% (**D53**).

### 3.6 Ogni elemento è azionabile

L'interpretazione non serve solo a mostrare: ogni suo elemento è **direttamente correggibile** (`04` §11.3). Rimuovere una condizione, cambiare l'ordinamento, cambiare vista, togliere una colonna sono operazioni che l'interfaccia costruisce da sé, senza passare dall'Interprete.

Tre benefici che si sommano, ed è raro che accada:

- **esperienza**: il fraintendimento costa due secondi anziché una riformulazione;
- **prestazioni**: è la Leva 1 di `04` §10.2, l'unica ottimizzazione di un ordine di grandezza — nessuna chiamata al modello, nessun costo variabile, nessuna latenza;
- **resilienza**: la parte deterministica del prodotto resta interamente utilizzabile quando il modello non risponde (§6.8).

**Regola:** se un elemento è mostrato, deve essere modificabile. Un elemento visibile e non azionabile insegna all'utente che l'interpretazione è una decorazione, e da quel momento smette di leggerla.

### 3.7 Quando l'interpretazione è troppo lunga

I limiti strutturali di **D12** — tre livelli di filtri, tre raggruppamenti — consentono interrogazioni che in forma di frase risultano illeggibili.

La risposta corretta non è troncare né abbreviare, perché entrambe nascondono proprio la parte che l'utente non ha chiesto. È **cambiare forma**: da frase a elenco strutturato, mantenendo tutti gli elementi, la distinzione per origine e l'azionabilità.

La soglia va fissata sperimentalmente con utenti reali. Il criterio è che l'interpretazione resti verificabile **con uno sguardo**: se richiede una lettura attenta, la verifica non avverrà, ed è indifferente che tutto sia formalmente presente.

---

## 4. La Disambiguazione

### 4.1 Due classi, due esperienze

Il contratto distingue l'ambiguità **interpretativa** — il linguaggio ammette più letture — da quella **referenziale** — il letterale corrisponde a più record (`03` §11.1). La distinzione è strutturale e va mantenuta anche nell'interfaccia, perché le due domande hanno forma diversa.

| | Interpretativa | Referenziale |
|---|---|---|
| Esempio | *«gli ordini di Rossi»* — cliente o venditore? | *«gli ordini di Rossi»* — quale dei tre Rossi? |
| Forma della domanda | Scelta fra letture, 2–4 opzioni | Elenco di candidati |
| Che cosa mostra | Il significato di ciascuna opzione | I dati distintivi di ciascun candidato |
| Costo | Nessuna seconda chiamata al modello | Nessuna chiamata al modello |

**Entrambe sono gratuite in termini di modello**, ed è una proprietà da sfruttare senza esitazione: chiedere non costa. Ogni opzione di chiarimento porta con sé le operazioni che produrrebbe (`03` §11.2), quindi la selezione applica operazioni già validate.

### 4.2 Come si formula una domanda onesta

**Specifica, mai generica.** *«Puoi essere più preciso?»* scarica sull'utente un lavoro che il sistema ha già fatto: se il sistema sa che ci sono due letture, deve nominarle.

**Nel linguaggio dell'utente.** Le etichette non contengono nomi tecnici: è un vincolo del contratto (`03` §11.2), non una raccomandazione.

**Con la provenienza in evidenza.** La domanda mostra quale frammento l'ha causata — *«di Rossi»* — così l'utente capisce **perché** gli si sta chiedendo, e non solo che cosa.

**Da 2 a 4 opzioni.** Una sola non è un chiarimento ma una conferma travestita, ed è vietata dal contratto. Oltre quattro, la scelta costa più della riformulazione.

**Ordinate per plausibilità, non per alfabeto.** È l'unico uso legittimo della confidenza: segnale di ordinamento, mai misura (`03` §10.5).

**Con una via d'uscita.** Nessuna delle opzioni può essere quella giusta. Deve essere sempre possibile riformulare senza sceglierne una — e la riformulazione non deve costare la perdita di ciò che era già stato costruito nei turni precedenti.

### 4.3 Il chiarimento è un buon esito, non un fallimento

`03` §4.4 rende `clarification` un esito di primo livello e non un errore. L'interfaccia deve rifletterlo: nessun tono di scusa, nessuna icona di avviso, nessun colore di errore.

Il sistema che chiede **sta funzionando correttamente** — sta evitando di indovinare, che è ciò per cui esiste. Presentarlo come un inciampo insegna all'utente che chiedere è un difetto, e prepara il terreno alla richiesta di ridurre i chiarimenti, che è il segnale anticipatore di **RC6**.

Va detto anche il rovescio: il tasso di disambiguazione ha una soglia **superiore** (5–15%). Un sistema che chiede troppo è faticoso, e la risposta corretta non è chiedere meno ma arricchire il dizionario — ogni chiarimento ricorrente su uno stesso termine è un candidato T6, e una volta registrata la preferenza la domanda smette di essere posta (`03` §11.2).

### 4.4 La scelta non si ripete

La risoluzione referenziale non modifica lo stato: continua a contenere il riferimento testuale anche dopo che l'utente ha scelto un candidato (`03` §11.3). È corretto — un'interrogazione condivisa deve risolversi secondo i permessi di chi la esegue.

Ne discende un requisito di esperienza esplicito: **la scelta dell'utente va conservata per la sessione.** Riproporre la stessa disambiguazione a ogni turno della stessa conversazione è il modo più rapido per rendere insopportabile una funzione corretta.

---

## 5. L'Attesa

### 5.1 Che cosa è cambiato con l'esecuzione asincrona

Con **D20a** la richiesta è accettata in circa 10 millisecondi e l'elaborazione avviene altrove. L'utente non attende una risposta HTTP: attende una notifica.

È un vantaggio di esperienza, non solo di architettura: **il sistema può dire a che punto è.** Un'attesa spiegata è percepita come sensibilmente più breve di un'attesa muta di pari durata, e il meccanismo per comunicarla esiste già — il bus, servito dal processo gevent, senza occupare alcun worker.

### 5.2 Gli stati dell'attesa

| Stato | Momento | Che cosa comunica |
|---|---|---|
| **Accettata** | Immediato | La richiesta è arrivata. Chiude il dubbio più fastidioso |
| **In interpretazione** | Entro pochi ms | Il sistema sta capendo |
| **In esecuzione** | Dopo la validazione | Ha capito, sta recuperando i dati |
| **Pronto** | A esito | Risultato e interpretazione insieme |

**Il primo stato è quello che conta di più.** L'incertezza peggiore non è aspettare: è non sapere se la richiesta è partita. Costa nulla — è già la risposta dell'accettazione — e rimuove la causa più frequente di doppio invio.

**Nessuna barra di avanzamento con percentuale.** La durata dipende da un servizio esterno e non è prevedibile; una percentuale che si ferma al 60% comunica un guasto che non c'è.

### 5.3 Le soglie percepite

| Tempo | Comportamento |
|---|---|
| < 1 s | Nessun bisogno di comunicare oltre l'accettazione |
| 1–3 s | Stato di avanzamento visibile |
| 3–10 s | Avviso esplicito che sta durando più del previsto |
| > 10 s | Possibilità di annullare, con conferma che l'annullamento è avvenuto |

**L'annullamento è un requisito, non un lusso.** Un utente che ha cambiato idea e non può fermare il sistema riformula in un'altra scheda, raddoppiando il carico proprio quando il sistema è lento — e il limite L1 di **D20c** trasformerebbe quella seconda richiesta in una sostituzione, con un esito che l'utente non capirebbe.

### 5.4 Il ripiego

Se il websocket non è disponibile — rete d'impresa restrittiva — il client interroga lo stato con frequenza decrescente (`05` §3.5). Dal punto di vista dell'utente non deve cambiare nulla.

Va però **misurato**: una quota elevata di sessioni in ripiego riporta il carico sui worker HTTP, cioè riapre parzialmente il problema che **D20a** esiste per chiudere. È una metrica di esercizio (`07` §12.2), non un dettaglio realizzativo.

---

## 6. Gli Stati non Ideali

### 6.1 Il principio

> **Un prodotto conversazionale si giudica dai casi non ideali più che da quelli ideali.**

Il caso ideale è indistinguibile fra un sistema buono e uno mediocre: entrambi mostrano dei record. La differenza si vede quando qualcosa non funziona, ed è lì che si decide se lo strumento viene adottato o abbandonato.

Tre regole valgono per tutti gli stati che seguono:

**Dire che cosa è successo, in linguaggio umano.** Mai un errore tecnico, mai un codice, mai il nome di un componente.

**Dire che cosa può fare l'utente adesso.** Uno stato senza via d'uscita è un vicolo cieco, e i vicoli ciechi si ricordano.

**Non fingere.** Nessun surrogato, nessuna approssimazione presentata come risultato, nessuna ipotesi arbitraria travestita da comprensione.

### 6.2 Non ho capito

`not_understood`. Il modello non è in grado di interpretare.

> Non ho capito la richiesta. Puoi riformularla?
> *Ho capito che stai parlando di **ordini di vendita**, ma non il resto.*

**Va mostrato ciò che è stato capito**, quando qualcosa lo è stato. È l'informazione che consente all'utente di riformulare solo la parte mancante anziché tutto.

**Non va proposta un'ipotesi.** *«Forse intendevi…»* seguito da un'interpretazione arbitraria è precisamente il comportamento che il prodotto esiste per evitare: se il sistema avesse un'ipotesi plausibile, l'esito corretto sarebbe `clarification`.

**Sul piano interno è un difetto di sistema**, non della richiesta (`03` §12.7). Va registrato come tale e non conteggiato come errore dell'utente — che è anche il motivo per cui il messaggio non deve avere tono di rimprovero.

### 6.3 Non posso farlo

`out_of_scope`. Richiesta compresa ma non esprimibile in questo profilo del contratto.

> Ho capito che vuoi **cambiare lo stato di questo ordine**. In questa versione posso solo consultare i dati, non modificarli.
> *Puoi aprire l'ordine e modificarlo direttamente.*

Tre proprietà:

**Dichiarare che si è capito.** È la differenza fra un limite e un'incomprensione, e l'utente le distingue perfettamente.

**Dichiarare il limite senza scusarsi.** Il perimetro di sola lettura è una scelta di prodotto, non una mancanza.

**Indicare la strada nativa.** Il prodotto è additivo: Odoo continua a esistere. Accompagnare l'utente dove può fare ciò che chiede è coerente con la filosofia e trasforma un rifiuto in un aiuto.

Il valore di `scope_note` appartiene a un insieme chiuso, quindi il messaggio è specifico per categoria e **misurabile**: la distribuzione degli `out_of_scope` è l'evidenza quantitativa su cui basare le priorità di ampliamento (**RC1**). È l'unico stato non ideale che produce direttamente una decisione di prodotto.

### 6.4 Nessun risultato

La distinzione più importante di questa sezione, e la più trascurata nei prodotti di questa classe:

| Situazione | Messaggio |
|---|---|
| **Interrogazione corretta, zero record** | *Non ci sono ordini confermati di luglio 2026.* Con l'interpretazione ben visibile |
| **Riferimento non trovato** | *Non ho trovato nessun cliente chiamato «Rossini».* Con proposta di alternative simili |
| **Non ho capito** | §6.2 |

**Un risultato vuoto non è un errore**, ed è un'informazione: *non ci sono fatture scadute* è una risposta utile. Presentarlo con tono di fallimento induce l'utente a pensare di aver sbagliato a chiedere.

**Ma un risultato vuoto è anche il travestimento più comune di un fraintendimento**, ed è per questo che l'interpretazione deve essere particolarmente visibile qui: se il sistema ha filtrato sulla data sbagliata, lo zero è credibile e l'unico modo per accorgersene è leggere il criterio.

`07` §12.2 include i risultati vuoti fra le metriche di esercizio proprio per questa ambivalenza: sono una fonte produttiva di candidati per il corpus.

### 6.5 Troppi risultati, e il limite di 80

**D13** fissa il limite predefinito a 80 record — la paginazione nativa delle viste lista Odoo — e il massimo assoluto a 500.

Il rischio di esperienza è che 80 record presentati senza spiegazione siano letti come **tutti** i record. È il caso *«mostrami tutto»* di §2.2, ed è un fraintendimento plausibile prodotto dall'interfaccia anziché dal modello.

| Situazione | Comportamento |
|---|---|
| Record ≤ 80 | Nessun avviso. Il limite non ha morso |
| Record > 80 | *Sto mostrando i primi **80** di **1 240**.* Con azione per restringere o cambiare vista |
| Richiesta oltre 500 | *La richiesta produce troppi risultati.* Con proposta concreta di restringimento |

**Due requisiti**, entrambi conseguenza di scelte già prese:

**Il conteggio precede il recupero** (`04` §10.5). È ciò che consente di dire *«primi 80 di 1 240»* invece di *«primi 80»*, e la differenza fra le due frasi è la differenza fra un'informazione e un'omissione.

**Il limite è nell'interpretazione** con la sua origine. Se vale 80 perché l'utente non ha indicato nulla, l'origine è `default` e va mostrata come tale: l'utente deve poter capire che quel numero non l'ha scelto lui.

Quando il limite morde, la proposta corretta non è *«vuoi vederne di più?»* — che porta verso i 500 e verso una vista inutilizzabile — ma **restringere o cambiare forma**: un raggruppamento, un pivot, un filtro aggiuntivo. È lo strumento giusto per la domanda che l'utente sta effettivamente ponendo.

### 6.6 Le richieste che non superano la validazione

I cinque livelli producono esiti diversi, e vanno comunicati diversamente (`03` §12.7).

| Livello | Messaggio | Natura |
|---|---|---|
| **1–2** Struttura, vocabolario | *Non ho capito, puoi riformulare?* | **Difetto di sistema**, non della richiesta |
| **3** Risoluzione | *Non conosco «fatturato» per gli ordini. Intendevi «importo totale»?* | Lacuna del dizionario |
| **4** Coerenza | Messaggio specifico, non tecnico | Difetto di sistema |
| **5** Costo | *La richiesta produce troppi risultati* + restringimento | **Comportamento atteso** |

**Il livello 3 è quello che produce l'esperienza migliore del prodotto.** Proporre l'alternativa corretta dal catalogo — *«non conosco X, intendevi Y?»* — è il comportamento che l'utente percepisce come competenza, ed è possibile solo perché i riferimenti sono semantici e non tecnici (**D10**, `03` §18.3). Un sistema che emettesse nomi tecnici potrebbe solo dire che qualcosa non esiste.

Ogni fallimento di livello 3 è inoltre **materiale prezioso**: indica un termine che gli utenti usano e il dizionario non conosce. L'interfaccia deve raccogliere quel segnale senza chiedere nulla di esplicito.

### 6.7 Il rifiuto per carico

**D20c** produce rifiuti visibili all'utente, ed è la decisione che verrà messa in discussione per prima. Il messaggio è ciò che determina se sopravvive.

Il rifiuto avviene per cinque limiti distinti (`05` §4.2), e vanno comunicati diversamente perché hanno cause diverse:

| Limite | Messaggio | Che cosa deve capire l'utente |
|---|---|---|
| **Una richiesta per sessione** | *Sto ancora lavorando alla richiesta precedente.* | Non è un rifiuto: è un'attesa |
| **Limite per utente** | *Hai diverse richieste in corso. Attendi che si completino.* | Riguarda lui, è temporaneo |
| **Coda globale piena** | *In questo momento c'è molto traffico. Riprova fra poco.* | Non è colpa sua, non è un guasto |
| **Turno scaduto** | *La richiesta ha atteso troppo a lungo e non è stata elaborata.* Con azione per ripetere | Riprovare è ragionevole |
| **Circuito di protezione aperto** | *Il servizio di comprensione non risponde. Le interrogazioni salvate funzionano.* | È il fornitore, e c'è un'alternativa |

**Tre regole di redazione, tutte con la stessa ragione:**

**Mai un tono di errore.** Il sistema sta funzionando come progettato: sta proteggendo l'ERP. Un messaggio che sembra un guasto genera una segnalazione, e una segnalazione genera la richiesta di alzare i limiti.

**Mai attribuire all'utente.** *«Hai fatto troppe richieste»* è vero e controproducente. La formulazione corretta descrive lo stato del sistema, non il comportamento della persona.

**Sempre un'azione possibile.** Riprovare fra poco, usare un'interrogazione salvata, restringere. Un rifiuto senza via d'uscita è ciò che produce la pressione a rimuovere il limite.

> **La ragione da fissare adesso, quando la discussione è ancora teorica:** senza i limiti, il sistema smette di rallentare l'ERP e comincia ad accumulare lavoro che nessuno riceverà. Il guasto non scompare — diventa più difficile da diagnosticare. Un rifiuto immediato e comprensibile è preferibile a un'attesa di quaranta secondi per una risposta che l'utente ha smesso di aspettare.

### 6.8 Quando il modello non risponde

È lo stato in cui il prodotto dimostra di essere additivo, e va comunicato come tale.

> In questo momento non riesco a capire le richieste scritte.
> *Le tue interrogazioni salvate funzionano, e puoi modificare l'interpretazione corrente direttamente.*

`04` §11.2 lo dice con precisione: il messaggio corretto non è *«il servizio non è disponibile»* ma la dichiarazione di che cosa continua a funzionare. È una differenza di comunicazione che riflette una differenza reale di capacità.

Restano disponibili:

- eseguire e rieseguire **interrogazioni salvate** — percorso interamente deterministico;
- **modificare l'interpretazione** dall'interfaccia — rimuovere un filtro, cambiare vista, aggiungere una colonna;
- **usare Odoo normalmente** — il livello conversazionale è additivo e la sua assenza non toglie nulla.

È qui che §3.6 ripaga il proprio costo: un'interpretazione azionabile trasforma un'indisponibilità totale in un degrado parziale.

---

## 7. La Conversazione Progressiva

### 7.1 Non è una chat

È la distinzione di prodotto più importante da rendere visibile, e l'interfaccia può tradirla senza che nessuno lo decida.

Il sistema non conserva una cronologia di messaggi: conserva uno **stato** (**D4**). Ogni turno produce un nuovo stato che riferisce il precedente. Ne discendono proprietà che una chat non ha — annullamento naturale, condivisione, ripresa a distanza di tempo, costo costante per turno — e una conseguenza sull'interfaccia:

> **L'oggetto centrale dello schermo è l'interrogazione corrente, non lo scorrimento dei messaggi.**

Un'interfaccia costruita come una chat spinge l'utente a leggere l'ultima risposta e a dimenticare lo stato accumulato. Un'interfaccia costruita attorno allo stato lo tiene davanti agli occhi — che è precisamente ciò che serve perché §3 funzioni.

I messaggi precedenti restano consultabili. Non sono il centro.

### 7.2 Il raffinamento

```
"mostrami tutti i clienti"      →  Contatti · tipo cliente
"solo quelli attivi"            →  + attivi
"ordina per città"              →  + ordinati per città
"mostrami anche il telefono"    →  + telefono fra le colonne
"apri il primo"                 →  record aperto in vista form
```

**Ciò che l'utente non nomina non cambia.** È la proprietà di **D9**: l'operazione `add_order` non ha modo di toccare i filtri, e lo spazio di ciò che il sistema può sbagliare coincide con quello di ciò che l'utente ha appena chiesto.

L'interfaccia deve renderla visibile: quando lo stato cambia, **si evidenzia ciò che è cambiato**, non si ridisegna tutto. Un'interpretazione che si riscrive interamente a ogni turno costringe a rileggerla ogni volta, e §1.3 dice che cosa succede a una lettura richiesta troppe volte.

### 7.3 L'annullamento

Poiché gli stati sono immutabili e ciascuno riferisce il precedente, l'annullamento è una **selezione**, non un ricalcolo (`04` §9.2).

Ne discende che può essere immediato, gratuito e senza limite di profondità. Va offerto come tale: un annullamento che richiede una conferma, o che può fallire, non sfrutta una proprietà che il sistema possiede già.

### 7.4 Il cambio di argomento

Quando l'utente passa a un'altra entità, lo stato riparte (`03` §6.2). È corretto — i filtri sugli ordini non hanno senso sulle fatture — ed è anche **una perdita di lavoro che va segnalata prima, non dopo**.

> Passo alle **fatture**. I filtri sugli ordini non si applicano più.

Senza questa segnalazione, l'utente che ha costruito cinque condizioni e cambia argomento le perde senza capire perché, e attribuisce al sistema un difetto che è invece una scelta di correttezza.

**Nota tecnica con effetto sull'esperienza:** il turno che cambia entità dispone dei nomi ma non degli attributi della nuova entità (`06` §5.8). Una richiesta come *«passa alle fatture, solo quelle scadute»* può quindi richiedere una seconda interpretazione, ed è un caso in cui l'attesa è più lunga del solito. Va coperto dagli stati di §5.2, non spiegato all'utente: la ragione è interna e non lo riguarda.

### 7.5 Salvare e condividere

Un'interrogazione salvata è uno stato promosso a oggetto riutilizzabile. Una condivisa è un **riferimento** a uno stato, non una copia dei risultati.

Ne discende un comportamento che va comunicato esplicitamente, perché altrimenti viene letto come un difetto:

> Due utenti che aprono la stessa interrogazione salvata possono legittimamente vedere risultati diversi.

Ciascuno ottiene ciò che i **propri** permessi consentono, al momento in cui la esegue, con le date risolte **adesso**. Un utente che confronta il proprio schermo con quello di un collega deve poter capire perché differiscono — e la spiegazione va messa dove nasce la domanda, cioè accanto al risultato di un'interrogazione condivisa, non in una pagina di documentazione.

È anche il motivo per cui *«gli ordini di questo mese»* salvato a luglio funziona ad agosto: lo stato non congela le date. Vale la pena dirlo all'utente, perché è una proprietà che l'utente non si aspetta e che apprezza.

---

## 8. Verso le Fasi Successive

Le linee guida di questo documento riguardano la Fase 1. Tre estensioni sono già determinate dalle decisioni prese, e fissarle ora costa poco.

### 8.1 Navigazione ai record — Fase 3

*«Apri il primo»* apre il record in vista form nativa. Il prodotto non costruisce una propria vista di dettaglio: consegna a Odoo.

È coerente con **A3** — Odoo resta l'unico motore esecutivo — ed è anche la scelta che riduce la superficie di manutenzione: la vista form di un modulo evolve con il modulo, senza che il livello conversazionale debba seguirla.

### 8.2 Analitica — Fase 4

Le viste pivot e grafico sono native. L'interpretazione ispezionabile vale identicamente: una misura aggregata ha **più** bisogno di dichiarare i propri criteri, non meno, perché un numero singolo non lascia trasparire come è stato calcolato.

**Requisito specifico:** quando un'interrogazione usa una metrica definita nel dizionario (T4), l'interpretazione deve mostrare la **definizione applicata** e la sua versione. Discende da **D29**: una definizione può cambiare, e chi legge un numero deve poter sapere secondo quale definizione è stato prodotto.

### 8.3 Interpretazione con riserva

Nell'intervallo intermedio di confidenza, il risultato è presentato con riserva esplicita (`03` §10.5) — la regola *«quando è incerto, lo dichiara»*.

**La riserva riguarda la presentazione, mai la decisione.** Un risultato con riserva è comunque un risultato completo, non ridotto né filtrato. La riserva invita a verificare l'interpretazione, che è già lì.

### 8.4 La conferma della Fase 3, e perché si progetta adesso

La Fase 3 introduce l'esecuzione di azioni previa **conferma esplicita**. È il primo momento in cui il prodotto ha effetti sui dati, ed è governato da un criterio di completamento netto: nessuna azione eseguita senza conferma.

Il rischio dichiarato è che le conferme siano **percepite come attrito e disattivate su richiesta dei clienti** — ed è precisamente **RG6**, il percorso per cui un fraintendimento plausibile diventa un'azione sui dati.

> **La qualità dell'esperienza di conferma è una misura di sicurezza.** Una conferma fastidiosa verrà rimossa; una conferma economica sopravvive.

Quattro requisiti, tutti derivabili da ciò che il prodotto già possiede:

**Mostrare l'azione, non chiedere se si è sicuri.** *«Sei sicuro?»* non porta informazione e viene confermato per riflesso. *«Sto per confermare **3 ordini**: OS-1042, OS-1043, OS-1051»* porta l'informazione su cui la decisione si prende.

**Mostrare la portata prima di tutto.** Il numero di record interessati è il dato che distingue un'azione ordinaria da un incidente, e va nella posizione più visibile.

**Una conferma per intenzione, non per record.** Confermare venticinque volte produce venticinque conferme automatiche.

**Nessuna scorciatoia basata sulla confidenza.** È il divieto permanente di `07` §5.7 e la mitigazione di **RG6**. Va scritto qui perché è qui che la proposta arriverà, formulata come miglioramento dell'esperienza.

---

## 9. Coerenza Visiva e Accessibilità

### 9.1 Il prodotto non deve sembrare un ospite

**D25** stabilisce che `nli_web` usi i token di `ui_brand_tokens` e il motore dei temi esistenti, con degradazione agli stili standard di Odoo quando la famiglia `ui_*` non è installata.

Non è una questione estetica. Il documento di visione richiede che il prodotto sia **additivo e incorporato nel flusso di lavoro**: un livello conversazionale che appaia visivamente estraneo viene percepito come uno strumento separato, e uno strumento separato viene aperto quando ci si ricorda che esiste. È il fallimento descritto da **R3**.

Ne discendono tre conseguenze operative:

- i risultati sono **viste native Odoo**, non tabelle costruite dal prodotto;
- l'interpretazione usa i token di tipografia, spaziatura e colore esistenti;
- il tema chiaro/scuro segue quello di Odoo, senza commutatore proprio.

L'ultima riga merita attenzione data la storia del repository: la sincronizzazione del tema è già stata fonte di difetti nel lavoro sull'interfaccia premium. Il livello conversazionale non deve introdurre un secondo meccanismo di tema, ma usare quello esistente.

### 9.2 Accessibilità

Non è un adempimento: è una condizione perché §3 funzioni. Un'interpretazione che alcune persone non possono leggere è, per quelle persone, un'interpretazione assente — e con essa cade A9.

| Requisito | Ragione |
|---|---|
| **L'interpretazione precede il risultato nell'ordine di lettura** | Chi usa un lettore di schermo deve incontrarla prima, come chi vede |
| **La distinzione per origine non dipende dal colore** | §3.3 — il colore è il primo canale che si perde |
| **L'evidenziazione incrociata ha un equivalente non a puntamento** | §3.4 — tastiera e touch |
| **Ogni elemento azionabile è raggiungibile da tastiera** | §3.6 — altrimenti la correzione è disponibile solo per alcuni |
| **Il cambio di stato è annunciato** | Un aggiornamento silenzioso non esiste per chi non guarda lo schermo |
| **L'attesa è annunciata, non solo animata** | §5.2 |
| **Contrasto conforme sui testi dell'interpretazione** | È il testo che va letto con attenzione |

**La quinta riga è specifica dell'esecuzione asincrona.** Il risultato arriva tramite notifica, quindi lo schermo cambia senza che l'utente abbia compiuto un'azione immediatamente prima. Per chi non vede lo schermo, un aggiornamento non annunciato equivale a un sistema che non ha risposto.

---

## 10. Multilingua

### 10.1 Due lingue nella stessa schermata

Il prodotto vive in un'installazione multilingua e il gergo aziendale mescola abitualmente termini di lingue diverse (`02` §12.3). Ne discende una regola che va fissata perché è controintuitiva:

| Elemento | Lingua |
|---|---|
| Testi dell'interfaccia | Lingua dell'utente |
| Messaggi di sistema | Lingua dell'utente |
| **Nomi di entità e attributi** | **Come nel dizionario dell'organizzazione** |
| Valori enumerati | Traduzione Odoo, che è già disponibile |

**La terza riga è la regola importante.** Se in azienda si dice *«le pratiche»*, l'interpretazione mostra *«pratiche»* anche a un utente che lavora in inglese. Tradurre il gergo aziendale lo distruggerebbe: il termine è un asset dell'organizzazione (`02` §4.4), non una stringa da localizzare.

L'effetto è una schermata con due lingue, ed è corretto: è la stessa mescolanza che le persone usano parlando fra loro.

### 10.2 Richieste in lingua mista

*«mostrami i deal in stage negotiation»* è una richiesta normale, non un'eccezione (`02` §10.2). L'indice dei termini è unico e multilingua (**D37**), quindi il riconoscimento non richiede che l'utente dichiari una lingua.

L'interfaccia non deve chiedere in quale lingua si sta scrivendo, né segnalare la mescolanza come anomalia.

---

## 11. Misurare l'Esperienza

### 11.1 Le metriche

Provengono dal Registro e sono definite in `07` §12.2. Qui conta la lettura che ne fa questo documento:

| Metrica | Soglia | Che cosa dice sull'esperienza |
|---|---|---|
| **Risoluzione al primo tentativo** | ≥ 75% | La misura più diretta di **P7** |
| **Passi per risultato** | ≤ 2 | Più passi = più attrito, non più ingaggio |
| **Tasso di abbandono** | ≤ 10% | Sessioni chiuse senza risultato utile |
| **Tasso di correzione** | Sorvegliato | Vedi §11.2 |
| **Tasso di disambiguazione** | 5–15% | Troppo basso: ipotesi silenziose. Troppo alto: attrito |
| **Risultati vuoti** | Sorvegliato | Fraintendimento travestito, o filtri troppo stretti |
| **Autonomia del nuovo utente** | ≥ 80% entro il primo giorno | Sulle attività di riferimento (**D7**) |

**Il volume di messaggi non è una metrica di successo.** Una conversazione più lunga è un peggioramento (**P7**), ed è vietata come indicatore di ingaggio (`07` §5.7).

### 11.2 Il tasso di correzione non misura ciò che sembra

Un tasso di correzione basso è compatibile con due situazioni opposte: un sistema accurato, e un sistema che sbaglia in modo credibile mentre nessuno verifica. Da solo non le distingue.

Va letto **insieme** all'accuratezza sul corpus sigillato:

| | Accuratezza alta | Accuratezza bassa |
|---|---|---|
| **Correzioni basse** | Sistema in salute | **A9 non regge**: gli utenti non stanno verificando |
| **Correzioni alte** | Gli utenti verificano e il sistema sbaglia poco: sorvegliare l'attrito | Sistema immaturo, ma la difesa funziona |

Il quadrante in alto a destra è quello che si vorrebbe non trovare mai, ed è anche quello che nessuna metrica di esercizio rivela da sola. Serve il corpus per interpretarlo — che è la ragione per cui `07` e questo documento vanno letti insieme.

### 11.3 La validazione di A9

L'assunzione va validata con l'osservazione, non con un questionario: chiunque, interrogato, dichiara di leggere l'interpretazione.

**L'iniezione controllata** (`07` §12.5) è la misura diretta: un campione di interpretazioni contiene una discrepanza deliberata e innocua rispetto alla richiesta — un ordinamento diverso, un periodo spostato di un mese. La quota di utenti che la rileva **è** la misura di A9.

Tre vincoli sull'esecuzione, e sono vincoli seri:

- si esegue **solo presso i pilota, con il loro consenso informato**, ed è un esperimento sulle persone che va trattato come tale;
- la discrepanza è **innocua** e non deve poter produrre una decisione sbagliata: mai su dati usati per operazioni, mai su richieste che precedono un'azione;
- l'esito è **aggregato**, mai per singolo utente. Non è una valutazione delle persone.

**Che cosa fare dell'esito.** Se la quota di rilevamento è alta, A9 regge e le scelte di §3 sono confermate. Se è bassa, non si conclude che gli utenti sbagliano: si conclude che **la difesa non può poggiare sulla vigilanza**, e vanno rafforzate le difese che non la richiedono — salienza dell'inferito, chiarimento più frequente sui criteri a rischio, e nella Fase 3 conferme più larghe.

È l'informazione che vale la pena avere **presto**, quando il costo di reagire è ancora una modifica di interfaccia.

---

## 12. Rischi dell'Esperienza

### RU1 — L'interpretazione viene spostata dietro un'interazione

**Descrizione.** Per guadagnare spazio o alleggerire la schermata, l'interpretazione finisce in un pannello che si apre, in un suggerimento al passaggio, o compare solo a bassa confidenza.
**Impatto. Critico.** È l'unica difesa contro **R1**, e un'azione richiesta per verificare qualcosa che di solito è giusto non viene compiuta. Il prodotto continuerebbe a funzionare, con la difesa disattivata e nessun segnale.
**Mitigazione.** **D64**; **V4** come invariante misurato al 100% (**D53**); §3.5 elenca in anticipo le tre proposte da respingere.
**Segnale anticipatore.** Discussioni sullo spazio occupato dall'interpretazione.

### RU2 — L'erosione della vigilanza

**Descrizione.** Con l'aumentare dell'accuratezza, gli utenti smettono di verificare. La difesa si indebolisce proprio mentre il sistema migliora (§1.3).
**Impatto. Alto**, e **strutturale**: non è un difetto da correggere, è una proprietà del comportamento umano di fronte a uno strumento affidabile.
**Mitigazione.** Salienza graduata (**D65**): l'attenzione va spesa sull'inferito, non su tutto. Validazione periodica di A9 (**D73**), non una sola volta. Difese che non richiedono vigilanza dove possibile — chiarimento anziché ipotesi.
**Segnale anticipatore.** Tasso di correzione in calo con accuratezza stabile (§11.2, quadrante in alto a destra).

### RU3 — Il limite viene letto come completezza

**Descrizione.** Ottanta record presentati senza contesto sono letti come tutti i record esistenti.
**Impatto. Alto.** È un fraintendimento plausibile prodotto dall'interfaccia, e conduce a decisioni su un insieme parziale creduto totale.
**Mitigazione.** **D68**: conteggio prima del recupero, e *«primi 80 di 1 240»* invece di *«primi 80»*; limite nell'interpretazione con la sua origine.
**Segnale anticipatore.** Richieste di alzare il limite predefinito «perché mancano dei record».

### RU4 — I rifiuti di carico fanno rimuovere i limiti

**Descrizione.** I messaggi di **D20c** vengono percepiti come guasti, generano segnalazioni, e la risposta è alzare o disattivare i limiti.
**Impatto. Critico**, perché il danno ricade **fuori** dal perimetro del prodotto: senza limiti si torna a **RA3**, cioè alla degradazione dell'ERP per utenti che non stanno usando il livello conversazionale.
**Mitigazione.** **D69**: nessun tono di errore, nessuna attribuzione all'utente, sempre un'azione possibile; distinzione dei cinque limiti, che hanno cause diverse.
**Segnale anticipatore.** Segnalazioni di assistenza che descrivono i rifiuti come errori.

### RU5 — La conferma della Fase 3 viene disattivata

**Descrizione.** Le conferme risultano faticose e i clienti ne chiedono la rimozione o la condizionano alla confidenza.
**Impatto. Critico.** È **RG6**, il percorso per cui un fraintendimento plausibile diventa un'azione sui dati, e cambierebbe anche il regime applicabile descritto in `08` §5.5.
**Mitigazione.** **D74**: conferma per intenzione e non per record, portata in evidenza, azione mostrata invece della domanda *«sei sicuro?»*; divieto permanente sulla confidenza.
**Segnale anticipatore.** Richieste di ridurre le conferme «per gli utenti esperti».

### RU6 — L'interfaccia diventa una chat

**Descrizione.** Il centro dello schermo diventa lo scorrimento dei messaggi anziché l'interrogazione corrente.
**Impatto. Medio-alto.** Lo stato accumulato esce dal campo visivo, e con esso la possibilità di verificarlo. Erode **D4** dal lato dell'esperienza senza toccarne l'implementazione.
**Mitigazione.** §7.1; l'interpretazione corrente come oggetto centrale, i messaggi come storia consultabile.
**Segnale anticipatore.** Richieste di funzioni tipiche delle chat — reazioni, thread, cronologia infinita.

### RU7 — L'instabilità è percepita come inaffidabilità

**Descrizione.** La stessa domanda produce interpretazioni diverse in momenti diversi. Entrambe possono essere corrette.
**Impatto. Alto sulla fiducia**, che è più difficile da recuperare dell'accuratezza: un utente che ha visto il sistema cambiare idea lo racconta ai colleghi.
**Mitigazione.** Stabilità ≥ 98% (**D48**); preferenza per i percorsi deterministici anche quando il modello sarebbe altrettanto rapido (§2.3).
**Segnale anticipatore.** Segnalazioni che riportano *«ieri funzionava diversamente»*.

### RU8 — L'iniezione controllata viene percepita come inganno

**Descrizione.** La misura di A9 (§11.3) introduce deliberatamente discrepanze. Scoperta senza contesto, appare come un sistema che sbaglia apposta.
**Impatto. Alto sulla fiducia**, e il danno sarebbe autoinflitto da una misura pensata per proteggere.
**Mitigazione.** **D73**: solo presso i pilota, con consenso informato, discrepanze innocue mai su percorsi che precedono un'azione, esito aggregato e mai per singolo utente.
**Segnale anticipatore.** Proposte di estendere la misura alla popolazione generale «per avere numeri migliori».

---

## 13. Decisioni Richieste

Numerazione in continuità (D1–D63).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D64** | **L'interpretazione è sempre visibile sopra il risultato**, senza interazione (§3.5) | **Adottare** | RU1: la difesa contro il rischio di rango 1 resta progettata e non effettiva |
| **D65** | **Salienza graduata per origine**, con distinzione non dipendente dal colore (§3.3) | **Adottare** | Un'interpretazione uniforme non viene letta; l'attenzione si ferma sull'entità, dove i fraintendimenti non vivono |
| **D66** | **Ogni elemento mostrato è azionabile** dall'interfaccia (§3.6) | **Adottare** | Si perde la Leva 1 delle prestazioni, la resilienza senza modello, e l'utente impara che l'interpretazione è decorativa |
| **D67** | L'interpretazione mostra il **periodo risolto**, non l'espressione dell'utente (§3.1) | **Adottare** | *«Questo mese»* conferma sé stesso: l'errore di esercizio fiscale resta invisibile |
| **D68** | **Conteggio prima del recupero** e formulazione *«primi 80 di N»* (§6.5) | **Adottare** | RU3: un insieme parziale creduto totale |
| **D69** | **Messaggi di rifiuto per carico** secondo §6.7: nessun tono di errore, nessuna attribuzione all'utente, sempre un'azione | **Adottare** | RU4, e con essa **RA3**: la protezione dell'ERP viene rimossa su pressione degli utenti |
| **D70** | La **scelta referenziale è conservata per la sessione** (§4.4) | **Adottare** | La stessa disambiguazione riproposta a ogni turno rende insopportabile una funzione corretta |
| **D71** | I **requisiti di accessibilità** di §9.2, incluso l'annuncio del cambio di stato asincrono | **Adottare** | Per una parte degli utenti l'interpretazione è assente, e con essa A9 |
| **D72** | I **nomi di entità e attributi non si traducono**: restano come nel dizionario dell'organizzazione (§10.1) | **Adottare** | Tradurre il gergo aziendale distrugge l'asset che il Dizionario esiste per raccogliere |
| **D73** | **Validazione di A9 per iniezione controllata**, con i tre vincoli di §11.3, ripetuta e non una tantum | **Adottare** | L'assunzione che regge la difesa contro R1 resta non verificata; e senza i vincoli, RU8 |
| **D74** | **Progetto della conferma di Fase 3** secondo §8.4, con divieto di scorciatoie sulla confidenza | **Adottare** | RU5 → **RG6**: la conferma viene disattivata su richiesta commerciale |

**D64, D65 e D73 sono le decisioni bloccanti.** Le prime due determinano se A9 ha una possibilità di reggere: un'interpretazione nascosta o uniforme non viene letta, e il resto del documento diventa irrilevante. **D73** è diversa — non rende la difesa più forte, la rende **verificabile**. È l'unica che può dirci che le altre due non stanno funzionando, e va eseguita presto: il costo di reagire cresce con ogni mese di esercizio.

---

## 14. Glossario

| Termine | Definizione |
|---|---|
| **Interpretazione ispezionabile** | Rappresentazione in linguaggio umano di come il sistema ha compreso la richiesta, mostrata sempre e con ogni elemento azionabile |
| **Salienza graduata** | Distinzione visiva degli elementi per `origin`: ciò che il sistema ha inferito è più evidente di ciò che l'utente ha chiesto |
| **Evidenziazione incrociata** | Corrispondenza interattiva fra il frammento della frase e l'elemento dell'interpretazione che ne è derivato |
| **Stato non ideale** | Situazione diversa dal risultato atteso: incomprensione, fuori ambito, vuoto, troppo ampio, rifiuto, indisponibilità |
| **Rifiuto per carico** | Esito di uno dei cinque limiti di **D20c**. Comportamento corretto del sistema, non guasto |
| **Riserva esplicita** | Presentazione di un risultato con invito alla verifica, nell'intervallo intermedio di confidenza |
| **Iniezione controllata** | Discrepanza deliberata e innocua introdotta in un campione di interpretazioni per misurare A9 |
| **Conversazione progressiva** | Raffinamento successivo di un'interrogazione, in cui ciò che non viene nominato non cambia |

---

## Chiusura

Questo documento realizza una difesa che gli altri hanno progettato. L'architettura ha reso l'interpretazione disponibile, il contratto l'ha resa strutturata, il piano di valutazione l'ha resa misurabile. Nessuno dei tre può renderla **letta**, e se non viene letta il rischio di rango 1 resta scoperto — con la particolarità che nulla lo segnalerebbe, perché un fraintendimento plausibile non produce sintomi né in chi lo subisce né nelle metriche di esercizio.

Il documento poggia su un fatto che vale la pena tenere davanti: **A9 non è una scelta di progettazione, è un'ipotesi sul comportamento umano**, e le ipotesi sul comportamento umano si verificano o si sbagliano. Peggio: questa si indebolisce nel tempo, perché la vigilanza scende man mano che il sistema diventa affidabile. È il paradosso di §1.3, ed è la ragione per cui la strategia scelta non è chiedere attenzione ma **dirigerla** — gratuita dove il contenuto si conferma da sé, inevitabile dove il sistema ha deciso al posto dell'utente.

Due conseguenze meritano di essere ricordate perché non appartengono al dominio dell'esperienza e ci finiscono comunque.

La prima è che **la qualità di due messaggi determina la sopravvivenza di due decisioni tecniche**. I rifiuti di **D20c** proteggono l'ERP e sono visibili all'utente: scritti come guasti, verranno rimossi, e con essi la protezione. La conferma della Fase 3 è l'unica barriera fra un fraintendimento e un'azione sui dati: resa faticosa, verrà disattivata su richiesta commerciale. In entrambi i casi la difesa non cadrà per un difetto tecnico, ma perché qualcuno ha scritto male tre righe di testo.

La seconda è che **l'interpretazione azionabile ripaga tre volte**. Nasce come requisito di esperienza — il fraintendimento deve costare due secondi — e si rivela l'unica ottimizzazione di prestazioni di un ordine di grandezza, oltre che il motivo per cui il prodotto resta parzialmente utilizzabile quando il modello non risponde. È l'ennesimo caso, in questo progetto, in cui una scelta fatta per correttezza produce anche il comportamento più veloce. Quando accade con questa regolarità, l'impianto non è un compromesso: è coerente.

Resta da fare la cosa che nessun documento può fare al posto di qualcuno: **guardare persone reali usare il prodotto**. §11.3 dice come, e dice anche che l'esito potrebbe imporre di rivedere scelte prese qui. È il modo corretto di procedere.

---

*Fine del documento.*
