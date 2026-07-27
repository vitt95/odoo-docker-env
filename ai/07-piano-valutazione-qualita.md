# Piano di Valutazione della Qualità
## AI Agent per Odoo — Natural Language Interaction Layer

---

| Voce | Valore |
|---|---|
| **Titolo** | Piano di Valutazione della Qualità — corpus, metodo, soglie, regressioni |
| **Tipo** | Documento di progettazione — metodo di misura |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Dipende da** | `03-specifica-dsl.md` §14 · `04-architettura.md` §13 · `06-modello-semantico.md` §6 · `00-registro-decisioni.md` (delibera 27/07/2026) |
| **Risolve** | **RC5**, la parte di **RC3** relativa alla misura, il rischio **R5** del documento di visione |
| **Ambito** | Definizione operativa di correttezza; corpus; riproducibilità; metriche e soglie; regressione come cancello; analisi dei fraintendimenti; qualificazione di un nuovo modello |
| **Fuori ambito** | Autorizzazioni e conformità (documento 08); interfaccia degli stati non ideali (documento 09); implementazione degli strumenti |

> **Prerequisiti.** Il documento presuppone adottate **D9** (due artefatti), **D34** (copertura scomposta, soglia ≥ 99%), **D41** (conservazione deduplicata del catalogo) e **D27** (prova di isolamento). Presuppone inoltre i valori fissati in delibera: le tre soglie di latenza di **D5**, il limite record di **D13**, il budget di **D31**.
>
> **Resta aperta D7** — clienti pilota. È l'unica dipendenza non soddisfatta, e il documento è scritto per essere applicabile prima che venga chiusa: il metodo è completo, le soglie sono fissate, e ciò che dipende dal pilota è isolato in §3.3 e §12.4 anziché sparso.

---

## 1. Executive Summary

### 1.1 Che cosa decide questo documento

Il documento di visione stabilisce che nessun ampliamento d'ambito è autorizzato senza misura, e fa della Fase 2 il cancello prima di qualunque scrittura (**D2**). Il contratto rende quella misura meccanizzabile definendo quando due interpretazioni coincidono (`03` §14). Il modello semantico aggiunge la seconda metà della diagnosi, la copertura (`06` §6).

Manca il pezzo che li rende un sistema di governo anziché tre buone intenzioni: **che cosa si misura esattamente, su quali dati, con quale procedura, contro quali soglie, e che cosa accade quando una soglia non è raggiunta.**

Questo documento definisce quel pezzo. Non introduce funzionalità: definisce il criterio con cui si decide se le funzionalità esistenti sono abbastanza buone da procedere.

### 1.2 Le quattro decisioni portanti

**Il corpus è diviso in tre popolazioni con regole di accesso diverse** (§3.1). La più importante è la terza, il corpus sigillato: un insieme di casi che chi lavora su prompt e dizionario **non può leggere**. Senza di essa, la misura degrada da valutazione a conferma nel giro di pochi mesi, e nessuno se ne accorge perché i numeri migliorano.

**La correttezza è un confronto fra forme canoniche, esteso da un registro chiuso di equivalenze semantiche** (§2.3). Il registro è chiuso e versionato come il vocabolario del contratto: un'equivalenza aggiunta per far passare un caso è un modo per spostare la soglia senza dichiararlo.

**Accuratezza e copertura non sono mai riportate separatamente** (§5.4). Non è una raccomandazione di presentazione: è una regola sugli strumenti. Una schermata che consenta di leggere l'accuratezza da sola produce sistematicamente la diagnosi sbagliata, e la produce con convinzione.

**La regressione blocca il rilascio, ed è valutata per sezione** (§7). Un peggioramento sui raggruppamenti compensato da un miglioramento sui filtri resta una regressione. Le metriche aggregate nascondono i peggioramenti localizzati, ed è nei peggioramenti localizzati che vivono i fraintendimenti plausibili.

### 1.3 La catena della misura

```
CORPUS                    interpretazione attesa, annotata da una persona
   │
   ▼  esecuzione a parametri congelati  (§4.1)
   │  istante · versione dizionario · versione contratto · modello+prompt
   │
   ├──▶ interpretazione prodotta  ──┐
   │                                 ├─▶ CONFRONTO  (§2)
   ├──▶ interpretazione attesa    ──┘   canonica + equivalenze dichiarate
   │                                        │
   │                                        ├─▶ accuratezza complessiva
   │                                        └─▶ accuratezza per sezione
   │
   └──▶ catalogo fornito (dal Registro, §6.2 di 06)
                │
                └─▶ COPERTURA  ─────────────▶ lettura congiunta  (§5.4)
                     necessari ⊆ disponibili        │
                                                     ▼
                                              DIAGNOSI, non un numero
```

Il punto della catena è l'ultimo riquadro. Una misura che produce un numero dice se procedere; una misura che produce una diagnosi dice **dove intervenire**, ed è l'unica che riduce il tempo speso a migliorare la cosa sbagliata.

### 1.4 Che cosa questo piano non promette

**Non promette che l'accuratezza misurata sia l'accuratezza percepita.** Il corpus misura l'interpretazione; l'utente giudica l'esito. Fra i due c'è la qualità dell'interpretazione mostrata, la chiarezza dei chiarimenti e la ragionevolezza dei limiti. §12 introduce le misure che coprono quello spazio, ma nessuna di esse è meccanizzabile come l'accuratezza.

**Non promette che una soglia raggiunta sia una soglia meritata.** Ogni metrica sufficientemente importante viene ottimizzata, e ottimizzare la metrica non è migliorare il prodotto (**RV5**). Il corpus sigillato e la revisione manuale periodica di §9.4 sono le due difese, e sono difese parziali per costruzione.

**Non promette stabilità dal primo giorno.** Le soglie di §6 sono valori di riferimento fissati in delibera; §6.4 dichiara quando e come si ricalibrano. Mantenere una soglia che i dati hanno smentito è peggio che non averla.

---

## 2. Che cosa significa «corretto»

### 2.1 Il problema, e perché il contratto lo ha già risolto a metà

Misurare l'accuratezza significa confrontare l'interpretazione prodotta con quella attesa e decidere se coincidono. Se «coincidono» non è definito meccanicamente, l'accuratezza torna a essere un giudizio umano su ogni caso: non ripetibile, non applicabile a ogni rilascio, non scalabile al volume necessario.

`03` §14 ha risolto la metà difficile definendo la **forma canonica**: una riduzione dello Stato di Interrogazione che conserva solo la semantica dell'interrogazione, eliminando ordine di inserimento, identificativi, provenienza, origine e confidenza.

Resta da definire che cosa si fa quando le forme canoniche differiscono ma l'interpretazione è ugualmente corretta. È la metà che questo documento chiude, ed è la metà da cui dipende **RC5**.

### 2.2 I tre livelli, e quello vietato

| Livello | Definizione | Uso in valutazione |
|---|---|---|
| **Identità** | Forme canoniche uguali | **Corretto** |
| **Equivalenza semantica** | Forme canoniche diverse, risultato provabilmente identico per ogni insieme di dati | **Corretto**, se l'equivalenza è nel registro di §2.3 |
| **Equivalenza di esito** | Stesso insieme di record restituito su questi dati | **Vietata come criterio** |

**Il divieto sull'equivalenza di esito va ribadito qui perché è la scorciatoia che qualcuno proporrà**, e la proporrà con un argomento ragionevole: *l'utente vede i record, quindi ciò che conta è che i record siano giusti.*

L'argomento non regge, per una ragione che riguarda l'ambiente in cui la misura viene eseguita. Due interrogazioni diverse restituiscono gli stessi record ogni volta che i dati non le discriminano — per esempio quando tutti gli ordini del mese risultano confermati. Negli ambienti di prova i dati sono pochi e poco vari, quindi la non discriminazione è la norma, non l'eccezione.

Il risultato è una metrica che **migliora quando i dati di prova impoveriscono**. È il modo più efficace di costruire un indicatore che sale mentre il prodotto scende, e ha la caratteristica peggiore possibile: non produce alcun sintomo finché non arriva in produzione, dove i dati discriminano.

### 2.3 Il registro delle equivalenze semantiche

Le equivalenze semantiche esistono perché il contratto, pur avendo eliminato le forme ridondanti (`03` §8.1), non può azzerarle. Il caso tipico è `between(1, 5)` rispetto a `greater_or_equal(1) AND less_or_equal(5)`.

Se queste occorrenze non sono riconosciute, la misura penalizza interpretazioni corrette e la soglia risulta artificialmente bassa: è **RC5**, e il suo danno non è sulla qualità del prodotto ma sul **governo** — porta a rinviare avanzamenti legittimi e a intervenire su problemi che non esistono.

Il rimedio non può però essere un riconoscimento discrezionale caso per caso, perché aprirebbe la strada opposta: ogni caso giudicato errato diventerebbe negoziabile.

> **Regola.** Le equivalenze semantiche sono un **registro chiuso, versionato e dichiarato**, con la stessa disciplina del vocabolario del contratto. Un confronto usa il registro alla versione fissata per quell'esecuzione. Nessuna equivalenza è applicata perché ragionevole: è applicata perché è nel registro.

Ogni voce del registro dichiara la trasformazione, la dimostrazione che il risultato è identico **per ogni insieme di dati** — non per quelli di prova — e la data di inserimento.

**Aggiungere una voce al registro è un evento che va trattato come una modifica del contratto**, non come una correzione della valutazione. Va richiesta la riesecuzione del corpus e riportata la variazione di accuratezza attribuibile alla sola aggiunta. Senza questa disciplina, il registro diventa il luogo in cui la soglia viene spostata senza che nessuno debba dichiararlo — e sarebbe la forma più elegante di **RV5**.

### 2.4 Il confronto per sezione

Il confronto complessivo dice se procedere. Il confronto **sezione per sezione** dice dove intervenire, ed è la ragione per cui il modello a due artefatti produce un beneficio di governo oltre a quello di correttezza: lo stato è strutturato in sezioni indipendenti, quindi è confrontabile per parti.

| Sezione | Che cosa misura la sua accuratezza | Se bassa, si interviene su |
|---|---|---|
| `target` | Determinazione dell'entità | Termini T1 del dizionario, soglia e margine di Fase A |
| `filter` | Comprensione delle condizioni | Dizionario (T2, T3, T5), prompt, ambiguità del contratto |
| `fields` | Attributi da mostrare | Esposizione (`06` §5.3), termini degli attributi |
| `group_by` | Raggruppamenti | Prompt, forme colloquiali nel dizionario |
| `order` | Ordinamento | Prompt |
| `limit` | Numero di record | Prompt, regole di derivazione del predefinito |
| `presentation` | Tipo di vista | Regole deterministiche di `03` §6.7 — **non** il modello |

L'ultima riga è un controllo utile in sé: la vista è derivata da regole, non interpretata. Un'accuratezza inferiore al 100% su `presentation` non è un problema del modello — è un difetto nelle regole di derivazione, e va cercato lì.

### 2.5 Che cosa la canonicalizzazione esclude, e va misurato altrove

La regola 1 della canonicalizzazione rimuove `origin`, `provenance` e `confidence`. È corretto ai fini dell'accuratezza interpretativa: due stati che differiscono solo per chi ha deciso l'ordinamento chiedono la stessa cosa.

Ma ne discende una conseguenza che `03` §14.3 segnala e delega esplicitamente a questo documento: **un sistema che inferisse tutto correttamente senza mai dichiarare l'origine risulterebbe perfettamente accurato, pur violando P3.**

Tre proprietà escono quindi dall'accuratezza e diventano indicatori propri (§5.5): correttezza dell'origine, correttezza della provenienza, e presenza dell'interpretazione ispezionabile. Non sono raffinamenti: sono ciò che distingue un sistema che indovina bene da un sistema di cui ci si può fidare.

---

## 3. Il Corpus

### 3.1 Tre popolazioni, non una

Il corpus non è un insieme unico. Trattarlo come tale è l'errore che rende la misura inservibile nel giro di due trimestri, e lo rende in modo invisibile.

| Popolazione | Origine | Chi la può leggere | Uso |
|---|---|---|---|
| **Corpus di sviluppo** | Casi raccolti in Fase 0 e casi reali annotati | Chiunque lavori sul prodotto | Sviluppo di prompt, dizionario, regole; diagnosi |
| **Corpus di regressione** | Sottoinsieme stabile del precedente | Chiunque | Esecuzione a ogni modifica; confronto fra rilasci |
| **Corpus sigillato** | Casi reali annotati, **mai esposti** | **Nessuno** che lavori su prompt o dizionario | Misura di riferimento per le soglie e per i cancelli di fase |

**Il corpus sigillato è la decisione più importante di questa sezione**, e va difesa perché costa lavoro e produce attrito.

Chi lavora su un prompt lo migliora guardando i casi che sbaglia. È il procedimento corretto, ed è anche il procedimento che, ripetuto abbastanza a lungo, produce un prompt che funziona su quei casi e non oltre. Il fenomeno non richiede cattiva fede né incompetenza: è il funzionamento normale di un ciclo di miglioramento con un insieme di prova fisso e visibile.

L'effetto è che l'accuratezza sul corpus di sviluppo continua a salire mentre l'accuratezza reale si è fermata. Non esiste alcun segnale interno che lo riveli — i numeri migliorano, ed è esattamente ciò che ci si aspetta da un lavoro che sta andando bene.

> **Regola.** Le soglie di §6 e i cancelli di fase si giudicano **sul corpus sigillato**. L'accuratezza sul corpus di sviluppo è uno strumento di lavoro, non un risultato riportabile.

Il costo del sigillo è modesto: separare l'annotazione dall'accesso e mantenere due esecuzioni anziché una. Il beneficio è che la divergenza fra le due misure diventa essa stessa un indicatore — se il corpus di sviluppo è al 94% e quello sigillato all'86%, il numero da guardare non è nessuno dei due ma la loro distanza.

### 3.2 Struttura di un caso

Un caso non è una coppia richiesta/risposta. Deve contenere tutto ciò che serve a rieseguirlo identicamente e a diagnosticarlo.

| Campo | Contenuto | Perché serve |
|---|---|---|
| **Testo della richiesta** | La frase, come è stata scritta | L'ingresso |
| **Stato di partenza** | Forma canonica, oppure vuoto per un turno di apertura | Un turno di raffinamento non ha senso senza lo stato su cui opera |
| **Interpretazione attesa** | Busta attesa: esito e operazioni | Il termine di confronto |
| **Esito atteso** | `operations`, `clarification`, `out_of_scope`, `not_understood` | Un chiarimento atteso è una risposta corretta, non un fallimento |
| **Riferimenti necessari** | Insieme dei riferimenti semantici richiesti dall'interpretazione attesa | Calcolo della copertura (§10) |
| **Contesto di esecuzione** | Utente di riferimento, società attive, lingua, fuso | **D40**: senza, il caso non è riproducibile in multi-società |
| **Istante di riferimento** | Data e ora fissate | Le espressioni temporali sono relative |
| **Etichette** | Entità, difficoltà, lingua, origine, classe linguistica | Bilanciamento e analisi (§3.6, §9.1) |
| **Provenienza** | Come il caso è entrato nel corpus | Distingue i casi raccolti dai casi costruiti |

**Il campo `esito atteso` merita attenzione.** Un corpus che contenga solo casi con esito `operations` misura una parte del prodotto e la spaccia per il tutto. Un sistema che non chiede mai chiarimenti e non dichiara mai i propri limiti è un sistema che indovina, e l'indovinare è precisamente ciò che il prodotto esiste per evitare. I casi con esito atteso `clarification` e `out_of_scope` sono **parte obbligatoria** del corpus, con la quota di §3.6.

### 3.3 Da dove vengono i casi

```
FASE 0 — costruzione iniziale                    dipende da D7
   │
   ├─ richieste reali raccolte presso i pilota   ← fonte primaria
   ├─ attività di riferimento dei pilota         ← copertura dei casi d'uso
   ├─ filtri salvati esistenti (ir.filters)      ← D35: definizioni già scritte
   └─ casi costruiti per i limiti del contratto  ← out_of_scope, profondità, budget

ESERCIZIO — crescita continua                    dal Registro, 04 §13.3
   │
   ├─ chiarimenti risolti          ─┐
   ├─ correzioni dell'utente         │
   ├─ fallimenti di validazione liv.3├─▶ candidati ─▶ annotazione ─▶ corpus
   ├─ riformulazioni immediate       │                  umana
   └─ esiti out_of_scope            ─┘
```

**La quarta fonte iniziale è quella che si dimentica.** Un corpus costruito solo su richieste reali contiene ciò che gli utenti hanno chiesto a un sistema che non esisteva ancora — cioè, nei fatti, ciò che i pilota immaginano di poter chiedere. Non contiene i casi che sondano i confini del contratto: profondità oltre due salti, richieste non esprimibili, interrogazioni oltre il budget. Quei casi vanno **costruiti deliberatamente**, perché il comportamento ai confini è dove il prodotto viene giudicato.

**Sull'assegnazione fra popolazioni.** Un caso raccolto in esercizio entra nel corpus sigillato o in quello di sviluppo secondo una ripartizione dichiarata e casuale — non secondo scelta. Se l'assegnazione fosse discrezionale, i casi difficili finirebbero sistematicamente dalla parte visibile, dove si possono aggredire, e il sigillato diventerebbe una selezione di casi facili.

### 3.4 L'annotazione

**È indispensabile e non è automatizzabile.** Un caso entra nel corpus con l'interpretazione **corretta**, che solo una persona che conosce il dominio può stabilire. Un corpus popolato con ciò che il sistema ha prodotto misurerebbe la stabilità, non la correttezza, e mostrerebbe risultati eccellenti mentre il prodotto sbaglia in modo costante.

Quattro regole di procedura, ciascuna con la sua ragione:

**L'annotatore non vede l'interpretazione prodotta dal sistema.** Vederla àncora il giudizio: un'interpretazione plausibile mostrata prima del giudizio viene accettata molto più spesso di quanto verrebbe prodotta da zero. È lo stesso meccanismo del fraintendimento plausibile, applicato a chi valuta.

**Doppia annotazione su un campione.** Almeno il 10% dei casi è annotato indipendentemente da due persone. Il tasso di disaccordo è un indicatore proprio: se supera una soglia, il problema non è il sistema ma la definizione di corretto.

**Il disaccordo si risolve dichiarando una regola, non scegliendo un vincitore.** Quando due annotatori competenti divergono, il caso è ambiguo — e un caso ambiguo nel corpus insegna al sistema a indovinare. Le due strade legittime sono: dichiarare una convenzione, che entra nelle linee guida di annotazione e vale per tutti i casi simili; oppure riclassificare il caso con esito atteso `clarification`, che è spesso la risposta giusta.

**Le linee guida di annotazione sono un artefatto versionato.** Crescono con i casi limite risolti. Senza di esse, la definizione di corretto deriva silenziosamente con il cambiare delle persone, e il confronto fra rilasci distanti perde significato.

### 3.5 Dimensione

La dimensione non è un obiettivo in sé, ma sotto una certa soglia la misura non distingue un miglioramento dal rumore. La domanda operativa è: **quale variazione di accuratezza deve essere rilevabile?**

Con la regressione fissata a zero (§7.1) serve poter distinguere una variazione di **un punto percentuale** dal rumore campionario. Su una proporzione attorno al 90%, l'ordine di grandezza necessario è di **alcune migliaia di casi** per il corpus di regressione.

| Popolazione | Dimensione iniziale | Traguardo |
|---|---|---|
| **Sviluppo** | ≥ 300 casi | Cresce senza limite dichiarato |
| **Regressione** | ≥ 1 000 casi | ≥ 3 000 entro il completamento della Fase 2 |
| **Sigillato** | ≥ 300 casi | ≥ 1 000 entro il completamento della Fase 2 |

I valori iniziali sono ciò che la Fase 0 può realisticamente produrre con due pilota; i traguardi sono ciò che serve perché le soglie di §6 siano affermazioni e non impressioni. **Finché il corpus sigillato è sotto i 1 000 casi, l'intervallo di confidenza va riportato accanto a ogni misura**, e va riportato sempre: una misura senza intervallo su 300 casi comunica una precisione che non ha.

Un corpus di regressione grande ha un costo per esecuzione. È la ragione per cui il carico differito ha un dispatcher separato (**D20d**): il ricalcolo del corpus è il carico più massiccio che il sistema genera, e non deve essere visibile agli utenti.

### 3.6 Bilanciamento

Un corpus rappresentativo del linguaggio reale non è un corpus casuale: le richieste reali si concentrano su poche entità e poche forme, e un campione fedele misurerebbe benissimo i casi frequenti e per nulla tutto il resto.

| Dimensione | Requisito |
|---|---|
| **Entità** | Nessuna entità oltre il 30% dei casi; tutte le entità delle attività di riferimento presenti |
| **Sezione** | Ogni sezione dello stato esercitata da almeno il 15% dei casi |
| **Esito atteso** | ≥ 10% `clarification`, ≥ 5% `out_of_scope`, ≥ 3% `not_understood` |
| **Turno** | ≥ 40% turni di raffinamento con stato di partenza non vuoto |
| **Lingua** | Le lingue dei pilota, più una quota di richieste in lingua mista (`06` §10.3) |
| **Difficoltà** | Tre livelli dichiarati, con il livello difficile ≥ 20% |
| **Contesto** | Casi in multi-società, se presente presso i pilota — **D40** |

**Il requisito sui turni di raffinamento è quello che verrà sacrificato per primo**, perché i casi di raffinamento sono più laboriosi da annotare: richiedono lo stato di partenza. Vale la pena fissarne ora la ragione. Il prodotto è progettato attorno alla conversazione progressiva — *"solo quelli attivi"*, *"ordina per città"*, *"mostrami anche il telefono"* — e sono precisamente i turni in cui **D9** produce il suo beneficio. Un corpus fatto di sole aperture misurerebbe la parte del prodotto che somiglia di più a un motore di ricerca, ignorando quella che lo distingue.

### 3.7 Igiene

Tre regole che proteggono la misura da se stessa.

**Nessun caso appartiene a due popolazioni.** Un caso presente sia nello sviluppo sia nel sigillato annulla il sigillo per quel caso, e nessuno se ne accorge.

**Il sigillo si rompe una volta sola.** Se un caso sigillato viene esaminato per diagnosticare un difetto — cosa legittima e talvolta necessaria — quel caso **esce definitivamente** dal corpus sigillato e passa a quello di sviluppo. Non torna indietro. È la regola che rende il sigillo credibile: senza di essa, «guardo solo questo» ripetuto trenta volte svuota il sigillato dei suoi casi più informativi.

**I dati personali non entrano nel corpus.** Le richieste reali contengono nomi di clienti, di fornitori, di dipendenti. Il corpus è conservato per anni, condiviso fra ambienti e usato per il collaudo: è la peggiore collocazione possibile per dati personali. I riferimenti a persone e organizzazioni vanno **sostituiti con segnaposto stabili** prima dell'inserimento, mantenendo la forma linguistica — *"gli ordini di ‹cliente-1›"* esercita la risoluzione referenziale esattamente come l'originale.

La sostituzione è anche l'unico modo per rendere il corpus condivisibile fra clienti, che è ciò che rende possibile l'accumulo di `06` §7.4.

---

## 4. Riproducibilità

### 4.1 I quattro parametri congelati

Un confronto fra due esecuzioni ha significato solo se tutto ciò che non si sta misurando è rimasto identico. `04` §13.3 ne fissa tre; la delibera ne aggiunge un quarto, implicito ma non dichiarato.

| Parametro | Se non congelato |
|---|---|
| **Istante di riferimento** | `current_month` cambia esito con il calendario: due esecuzioni a un mese di distanza non sono confrontabili |
| **Versione del dizionario** | Un arricchimento si confonde con un miglioramento del modello |
| **Versione del contratto** | Cambia la forma dell'atteso, non la qualità dell'interpretazione |
| **Modello e prompt** | Sono l'oggetto della misura: vanno dichiarati insieme al risultato, mai variati insieme ad altro |

A questi si aggiunge il **registro delle equivalenze** (§2.3), che è parte della definizione di corretto: due esecuzioni con registri diversi misurano cose diverse.

**La riproducibilità dell'istante è possibile per una ragione architetturale precisa**: il Risolutore è il solo componente consapevole del tempo (`04` §4.6), e l'Applicatore non accede a data e ora correnti — è una delle regole di non dipendenza verificate automaticamente (`04` §6.3). Fissare l'istante è quindi un parametro di un componente, non un artificio che attraversa il sistema.

Vale la pena notare che il controllo architetturale di **D24** che verifica la purezza dell'Applicatore è, di fatto, un test di questo piano: fallisce nel momento in cui qualcuno introduce una dipendenza dal tempo, cioè nel momento in cui la riproducibilità del corpus si romperebbe silenziosamente.

### 4.2 La regola che rende attribuibili le variazioni

> **Non si modificano dizionario e modello nello stesso rilascio** (`06` §4.4).

È la regola più semplice del piano e quella con il rapporto benefici/costo più alto. Senza di essa, un arricchimento del dizionario che migliora l'accuratezza viene attribuito al modello, e un cambio di modello che la peggiora viene mascherato da un arricchimento contemporaneo.

Estesa ai quattro parametri, diventa: **una esecuzione, una variabile.** Quando la pressione di consegna impone di cambiare due cose insieme, la strada corretta è eseguire tre volte — base, prima variazione, entrambe — non rinunciare all'attribuzione.

### 4.3 La matrice di esecuzione

| Occasione | Popolazione | Frequenza |
|---|---|---|
| Modifica di prompt | Regressione | A ogni modifica, automatica |
| Modifica del dizionario | Regressione | A ogni modifica, automatica |
| Modifica del contratto o delle regole di derivazione | Regressione | A ogni modifica, automatica |
| Cambio di modello o di fornitore | Regressione + sigillato | Protocollo di §13 |
| Rilascio | Regressione + sigillato | A ogni rilascio |
| Cancello di fase | Sigillato | Su richiesta, con intervallo di confidenza |
| Riesame periodico | Tutte | Mensile |

**L'esecuzione automatica non è un dettaglio realizzativo.** Una misura che dipende da qualcuno che si ricorda di lanciarla è una misura periodica, e una misura periodica viene rinviata sotto pressione — che è precisamente il rischio **R5** del documento di visione e il **RV7** di questo.

---

## 5. Le Metriche

### 5.1 Tre ranghi, non un elenco

Un elenco piatto di indicatori produce schermate che nessuno legge e decisioni prese sul primo numero visibile. Gli indicatori hanno ranghi diversi, e il rango determina che cosa succede quando l'indicatore si muove.

| Rango | Definizione | Conseguenza di uno scostamento |
|---|---|---|
| **Primarie** | Governano i cancelli di fase e i rilasci | Bloccano |
| **Diagnostiche** | Indicano dove intervenire | Orientano il lavoro |
| **Di guardia** | Sorvegliano la validità della misura stessa | Sospendono il giudizio sulle primarie |

Le metriche di guardia sono la categoria che manca quasi sempre, ed è quella che protegge dal caso peggiore: una misura sbagliata sulla quale si decide con sicurezza.

### 5.2 Metriche primarie

| Metrica | Definizione | Popolazione |
|---|---|---|
| **Accuratezza interpretativa** | Casi in cui l'interpretazione prodotta è identica o semanticamente equivalente all'attesa | Sigillato |
| **Copertura del catalogo** | Casi in cui **tutti** i riferimenti necessari erano presenti nel catalogo fornito | Sigillato |
| **Accuratezza per sezione** | Come sopra, limitata a una sezione dello stato | Sigillato |
| **Variazione rispetto alla misurazione precedente** | Per sezione e complessiva | Regressione |

Sono quattro, e sono poche di proposito. Ogni metrica aggiunta a questo rango riduce il peso decisionale delle altre.

### 5.3 Metriche diagnostiche

| Metrica | Che cosa rivela |
|---|---|
| **Accuratezza per entità** | Entità con dizionario insufficiente |
| **Accuratezza per classe linguistica** | Forme colloquiali, negazioni, espressioni temporali, vaghezza: dove il linguaggio batte il sistema |
| **Distribuzione dei fallimenti per livello di validazione** | Livelli 1–2 alti ⇒ generazione vincolata mal applicata; livello 3 alto ⇒ lacune del dizionario; livello 5 alto ⇒ budget o limiti tarati stretti |
| **Tasso di ripristino** | Frequenza del singolo tentativo di **D15**: se sale, difetto sistematico del modello |
| **Quota risolta in Fase A** | Efficacia dei termini T1: la sua crescita riduce costo e latenza |
| **Dimensione media del catalogo** | Se cresce, esposizione troppo permissiva |
| **Rifiuti per budget** | Se non trascurabili, il budget di 60 attributi è tarato stretto per qualche entità |
| **Chiarimenti per termine** | Termini ricorrenti non ancora mappati — ingresso diretto del lavoro sul dizionario |
| **Distribuzione degli `out_of_scope` per classe** | **RC1**: se una classe ricorre, è candidata a estensione documentata |

### 5.4 La lettura congiunta, che è una regola sugli strumenti

Accuratezza e copertura **non sono mai riportate separatamente**. Non è una preferenza di presentazione: è un vincolo sugli strumenti, e va realizzato come tale.

| | **Copertura alta** | **Copertura bassa** |
|---|---|---|
| **Accuratezza alta** | Sistema in salute. Sorvegliare | Instabile: il modello sta indovinando. Peggiorerà con dati più vari |
| **Accuratezza bassa** | Problema di **interpretazione**: prompt, modello, ambiguità del contratto | Problema **semantico**: dizionario ed esposizione. Lavorare sul modello è tempo sprecato |

Il quadrante in basso a destra è il più frequente all'inizio ed è quello in cui l'errore diagnostico costa di più: si cambia modello, si riscrivono i prompt, non cambia nulla, e la causa resta a monte.

Il quadrante in alto a destra è il più insidioso perché non produce sintomi: il sistema funziona bene su un insieme ristretto di casi mentre la copertura è insufficiente. Regredirà quando il linguaggio degli utenti si allargherà, e la regressione apparirà inspiegabile.

> **Requisito sugli strumenti.** Nessuna schermata, nessun rapporto e nessun messaggio automatico espone l'accuratezza senza la copertura corrispondente. Una schermata che consenta di leggere l'accuratezza da sola verrà usata per leggerla da sola.

### 5.5 Le proprietà che l'accuratezza non cattura

Escono dalla canonicalizzazione (§2.5) e diventano indicatori propri. Sono tre, e sono ciò che separa un sistema che indovina bene da un sistema di cui ci si può fidare.

| Metrica | Definizione | Soglia |
|---|---|---|
| **Correttezza dell'origine** | Casi in cui `origin` distingue correttamente ciò che l'utente ha chiesto da ciò che il sistema ha inferito | ≥ 98% |
| **Correttezza della provenienza** | Casi in cui i frammenti di `provenance` corrispondono al testo che ha effettivamente determinato l'elemento | ≥ 90% |
| **Presenza dell'interpretazione** | Risultati presentati con la loro interpretazione | **100%** — è **V4** |

La terza non è una metrica di qualità ma un invariante, e compare qui perché un invariante non verificato è un'intenzione. Il valore atteso è 100% e qualunque scostamento è un difetto bloccante, non una tendenza da sorvegliare.

**Sulla soglia della provenienza.** È deliberatamente più bassa delle altre. La provenienza alimenta l'analisi dei fraintendimenti (§9.2) e la spiegazione all'utente; un errore di attribuzione del frammento degrada entrambe ma non produce un risultato sbagliato. Chiedere il 98% qui significherebbe spendere sul problema meno grave.

### 5.6 Metriche di guardia

| Metrica | Che cosa protegge | Azione se fuori soglia |
|---|---|---|
| **Distanza sviluppo − sigillato** | Adattamento al corpus visibile (**RV2**) | Oltre 5 punti: le misure sullo sviluppo non sono riportabili; indagare |
| **Tasso di disaccordo fra annotatori** | Definizione di corretto (**RV4**) | Oltre 10%: sospendere il giudizio sulle primarie; rivedere le linee guida |
| **Casi giudicati errati ma corretti a esame umano** | Sottostima da canonicalizzazione (**RC5**, **RV3**) | Oltre 5% del campione: manca un'equivalenza nel registro |
| **Varianza fra esecuzioni identiche** | Rumore letto come segnale (**RV6**) | Se supera la variazione osservata, la variazione non è interpretabile (§8) |
| **Erosione del corpus sigillato** | Rottura ripetuta del sigillo (§3.7) | Se il sigillato scende sotto la dimensione minima, va ricostituito |
| **Età mediana dei casi** | Corpus fermo mentre il linguaggio cambia | Se cresce senza limite, la crescita da esercizio si è fermata |

**La quarta riga è quella che rende oneste tutte le altre.** Senza una misura della varianza, ogni fluttuazione diventa un risultato: un rilascio «migliora dello 0,4%» e qualcuno lo scrive in una relazione. §8 la definisce.

### 5.7 Metriche vietate

| Vietata | Perché |
|---|---|
| **Equivalenza di esito** come criterio di correttezza | Migliora quando i dati di prova impoveriscono (§2.2) |
| **Confidenza dichiarata dal modello** come misura di qualità | **RC6**: non è una probabilità. Il suo uso per decisioni automatiche è il percorso per cui un fraintendimento plausibile diventa una scrittura errata |
| **Accuratezza aggregata** senza scomposizione per sezione | Nasconde i peggioramenti localizzati, che sono quelli pericolosi |
| **Accuratezza** senza copertura | Induce sistematicamente la diagnosi sbagliata (§5.4) |
| **Volume di messaggi** come indicatore di ingaggio | **P7**: una conversazione più lunga è un peggioramento |
| **Accuratezza sul corpus di sviluppo** come risultato riportabile | §3.1 |

La seconda riga va sorvegliata attivamente, perché la proposta si presenterà in una forma ragionevole: *saltare la conferma quando la confidenza è alta*. Il segnale anticipatore dichiarato da **RC6** è precisamente questo, e va trattato come tale quando compare.

---

## 6. Soglie

### 6.1 Due famiglie con funzioni diverse

**Soglie di rilascio** — si applicano a ogni rilascio e proteggono dalla regressione. Sono relative: confrontano con la misurazione precedente.

**Soglie di fase** — si applicano ai cancelli fra fasi e autorizzano un ampliamento d'ambito. Sono assolute e si giudicano sul corpus sigillato con intervallo di confidenza.

Confonderle produce due errori simmetrici: bloccare un rilascio perché non raggiunge una soglia di fase, o aprire una fase perché nessun rilascio è stato bloccato.

### 6.2 Le soglie

| Metrica | Soglia | Famiglia | Origine |
|---|---|---|---|
| **Accuratezza interpretativa** | ≥ 90% | Fase | `02` §17.2, confermata in delibera |
| **Copertura del catalogo** | ≥ 99% | Fase | **D34** |
| — copertura entità | ≥ 99% | Fase | **D34** |
| — copertura attributi | ≥ 99,5% | Fase | Esatta per costruzione in Fase C (`06` §5.7): uno scostamento indica un difetto nelle regole di esposizione, non un limite |
| **Accuratezza per sezione** | ≥ 85% su ogni sezione | Fase | Nuova: impedisce che una media alta nasconda una sezione inservibile |
| **Regressione fra rilasci** | Zero, per sezione | Rilascio | `02` §17.2, **D2** |
| **Correttezza dell'origine** | ≥ 98% | Fase | §5.5 |
| **Correttezza della provenienza** | ≥ 90% | Fase | §5.5 |
| **Presenza dell'interpretazione** | 100% | Rilascio | **V4** |
| **Risoluzione al primo tentativo** | ≥ 75% | Fase | `02` §17.2 — misurata su utenti reali (§12) |
| **Tasso di disambiguazione** | 5–15% | Sorveglianza | Troppo basso: ipotesi silenziose. Troppo alto: attrito |
| **Tempo alla risposta, P95** | ≤ 3 s | Rilascio | **D5**, delibera |
| **Attesa in coda, P95** | ≤ 500 ms | Rilascio | **D5**, delibera |
| **Accettazione, P95** | ≤ 50 ms | Rilascio | **D5**, delibera |
| **Incidenti di accesso oltre i permessi** | **Zero** | Rilascio | `02` §17.4, **V2** |

**La riga sull'accuratezza per sezione è aggiunta da questo documento** e vale la pena motivarla. Con la sola soglia complessiva al 90%, un sistema che individua l'entità nel 99% dei casi e i raggruppamenti nel 62% può superare il cancello. L'utente che usa i raggruppamenti — tipicamente chi ha più bisogno del prodotto, perché sta facendo analisi — troverebbe un sistema inservibile in un prodotto dichiarato conforme.

### 6.3 Il cancello verso la scrittura

**D2** stabilisce che nessuna scrittura è autorizzata prima del completamento della Fase 2. Questo documento ne fissa le condizioni verificabili. Tutte, non alcune:

1. accuratezza interpretativa ≥ 90% sul corpus sigillato, con **estremo inferiore** dell'intervallo di confidenza al 95% sopra il 90% — non la stima puntuale;
2. copertura ≥ 99%, scomposta, entrambe le componenti sopra soglia;
3. accuratezza per sezione ≥ 85% su ogni sezione;
4. corpus sigillato ≥ 1 000 casi, bilanciato secondo §3.6;
5. nessuna regressione non spiegata negli ultimi tre rilasci;
6. metriche di guardia tutte entro soglia;
7. tasso di disambiguazione entro l'intervallo — un sistema che non chiede mai non è pronto a scrivere;
8. accuratezza misurata separatamente sulle **intenzioni di azione**, che sono un dominio nuovo e non ereditano la misura della lettura.

**Il punto 1 è il più esigente e il più importante.** Chiedere l'estremo inferiore anziché la stima puntuale significa che un corpus piccolo non basta: con 300 casi, una stima puntuale del 91% ha un intervallo che scende sotto l'87%, e il cancello resta chiuso. È corretto che sia così — autorizzare la scrittura sui dati aziendali sulla base di una misura imprecisa è esattamente il rischio che **D2** esiste per impedire.

**Il punto 8 va detto adesso**, perché sarà sgradito quando arriverà: l'accuratezza sulla lettura non trasferisce alla scrittura. Sono intenzioni diverse, con un linguaggio diverso e conseguenze incomparabili. Il corpus di Fase 3 va costruito, non ereditato.

### 6.4 Ricalibrazione

Le soglie sono ipotesi formulate prima di disporre di dati. **Vanno riviste dopo il primo trimestre di uso reale**, e la revisione segue tre regole:

**Si ricalibra sui dati, non sui risultati.** Una soglia si abbassa se i dati mostrano che era irrealistica per il dominio, mai perché il prodotto non la raggiunge. La distinzione è verificabile: nel primo caso esiste un'analisi che mostra *perché* il valore era sbagliato.

**Un abbassamento è una decisione registrata.** Entra nel registro delle decisioni con motivazione, come qualunque altra. Una soglia che si abbassa senza traccia è una soglia che non esiste.

**Le soglie di fase non si ricalibrano durante il cancello.** Modificare il criterio mentre si sta decidendo se superarlo è la forma più diretta di **RV5**. Se una soglia di fase risulta sbagliata, si registra, si rinvia, si ricalibra a cancello chiuso.

---

## 7. La Regressione come Cancello

### 7.1 Che cosa costituisce regressione

Il documento di visione non ammette regressioni fra rilasci. Perché la regola sia applicabile e non solo dichiarata, serve stabilire cosa si confronta.

> **Regressione** = variazione negativa dell'accuratezza **su una qualunque sezione**, oltre la soglia di rumore di §8.3, rispetto alla misurazione precedente sullo stesso corpus di regressione a parametri congelati.

Tre proprietà della definizione, ciascuna necessaria:

**Per sezione, non aggregata.** Un peggioramento sui raggruppamenti compensato da un miglioramento sui filtri resta una regressione. È il punto che distingue una verifica seria da una formale: le medie nascondono i peggioramenti localizzati, e i peggioramenti localizzati sono dove vivono i fraintendimenti plausibili.

**Oltre la soglia di rumore.** Senza questa clausola, ogni esecuzione produrrebbe qualche sezione in calo per fluttuazione e il cancello si bloccherebbe da solo fino a essere disattivato. Un cancello che scatta sempre viene rimosso.

**Sullo stesso corpus.** Un corpus cresciuto fra due esecuzioni rende il confronto privo di significato. La crescita è desiderata, ma il confronto avviene sul sottoinsieme comune, e il resto è una misura nuova.

### 7.2 Le altre regressioni

L'accuratezza non è l'unica cosa che può peggiorare. Sono regressioni bloccanti allo stesso titolo:

| Regressione | Soglia |
|---|---|
| Copertura del catalogo | Qualunque calo oltre il rumore |
| Presenza dell'interpretazione | Qualunque scostamento da 100% |
| Incidenti di accesso oltre i permessi | Qualunque valore diverso da zero |
| Tempo alla risposta P95 | Oltre il 20% di aumento |
| Attesa in coda P95 | Oltre soglia — indica capacità, non qualità |
| Esito della prova di isolamento (**D27**) | Qualunque fallimento |

**La terza riga non è una metrica ma un invariante**, e un invariante violato non è una regressione da valutare: è un difetto che ferma tutto. Compare in questa tabella perché è il posto dove qualcuno la cercherà.

### 7.3 Che cosa fa scattare l'esecuzione

| Evento | Esecuzione |
|---|---|
| Modifica di prompt, dizionario, contratto, regole di derivazione | Corpus di regressione, automatica |
| Cambio di modello o fornitore | Protocollo di §13 |
| Modifica del registro delle equivalenze | Corpus di regressione, con attribuzione della variazione |
| Rilascio | Regressione + sigillato |
| Aggiornamento di Odoo o dei moduli | Regressione **e** rigenerazione di L0 (`06` §9.3) |

**L'ultima riga è quella che si dimentica.** Un aggiornamento dei moduli rigenera il livello derivato del dizionario e può spostare l'esposizione degli attributi: è una modifica del dizionario, anche se nessuno l'ha scritta. Senza esecuzione, un aggiornamento di Odoo può abbassare la copertura e il calo verrebbe attribuito, mesi dopo, a qualsiasi altra cosa.

### 7.4 Blocco e deroga

**Una regressione blocca il rilascio, come un test fallito.** Non è una segnalazione da valutare.

La deroga esiste, perché un processo senza via d'uscita viene aggirato anziché rispettato, ed è governata da tre condizioni:

1. la deroga è concessa dall'Architect, non da chi ha prodotto la modifica;
2. è registrata con la sezione interessata, l'entità della variazione e la ragione;
3. porta una **scadenza**: la regressione va sanata entro un numero dichiarato di rilasci, oppure la soglia va ricalibrata secondo §6.4 — cioè dichiarando che il valore precedente era sbagliato.

La terza condizione è quella che impedisce alla deroga di diventare il funzionamento ordinario. Senza scadenza, la prima deroga stabilisce che le regressioni sono negoziabili, e la seconda non ha più bisogno di essere motivata.

---

## 8. Il Rumore

### 8.1 Perché questa sezione esiste

Nessuno dei documenti precedenti affronta il fatto che due esecuzioni identiche producono risultati diversi. È un'omissione comprensibile — riguarda la misura, non la progettazione — ma non colmarla renderebbe inutilizzabile la regola sulla regressione: ogni esecuzione mostrerebbe qualche sezione in calo, e il cancello di §7 scatterebbe a caso.

I modelli linguistici non sono deterministici. Abbassare la temperatura a zero riduce la variabilità ma non la elimina: restano l'ordinamento non deterministico delle operazioni in virgola mobile, i cambiamenti lato fornitore che non producono un cambio di identificativo, e il comportamento vicino ai punti di indifferenza fra due alternative quasi equivalenti.

Va aggiunto che il prodotto **riduce strutturalmente questa esposizione**: la generazione vincolata allo schema (**C1**), il vocabolario chiuso e il percorso rapido lessicale di Fase A — che è deterministico e non chiama il modello — sottraggono al non determinismo una quota rilevante dei casi. La varianza attesa è quindi bassa. Non è però nulla, e trattarla come nulla è ciò che trasforma una fluttuazione in un risultato.

### 8.2 La stabilità come metrica propria

> **Stabilità** = percentuale di casi che producono la stessa interpretazione canonica su **K esecuzioni ripetute** a parametri identici.

Con **K = 5** su un sottoinsieme del corpus di regressione, eseguito a ogni cambio di modello e mensilmente in esercizio.

La stabilità è una metrica di prodotto, non solo di misura. Un sistema instabile è un sistema in cui lo stesso utente, con la stessa frase, ottiene risultati diversi in momenti diversi — che è una forma di **R1** particolarmente corrosiva per la fiducia, perché l'utente non ha modo di capire cosa è cambiato.

**Soglia: ≥ 98%.** I casi instabili sono materiale diagnostico di prima qualità: sono precisamente quelli in cui il modello è indeciso fra due interpretazioni, ed è quasi sempre il segnale che la richiesta è genuinamente ambigua e l'esito corretto sarebbe `clarification`.

### 8.3 Distinguere il miglioramento dalla fluttuazione

Dalla stabilità si ricava la soglia che rende applicabile §7.1.

> **Soglia di rumore** = due deviazioni standard della variazione osservata su K esecuzioni identiche, calcolata per sezione.

Una variazione entro la soglia **non è interpretabile**: non è un miglioramento e non è una regressione. Va riportata come tale, non arrotondata a favore.

Due conseguenze operative, entrambe sgradite e entrambe corrette:

- un rilascio che «migliora dello 0,3%» quando la soglia di rumore è 0,8% **non ha migliorato nulla**, e scriverlo in una relazione è produrre un'informazione falsa;
- un corpus troppo piccolo ha una soglia di rumore troppo alta per rilevare i miglioramenti reali. È la ragione quantitativa dei valori di §3.5: sotto il migliaio di casi, un guadagno di un punto è indistinguibile dal caso.

**La soglia di rumore va ricalcolata a ogni cambio di modello**, perché è una proprietà del modello attivo, non del corpus.

---

## 9. Analisi dei Fraintendimenti

### 9.1 Tassonomia

Un errore va classificato su due assi, perché la sezione dice *dove* e la causa dice *cosa fare*. Sono informazioni indipendenti e conflarle produce liste di errori che non orientano il lavoro.

| Causa | Segnale caratteristico | Rimedio |
|---|---|---|
| **Lacuna del dizionario** | Fallimento di validazione livello 3; chiarimenti ricorrenti sullo stesso termine | Arricchire il vocabolario (L2) |
| **Copertura insufficiente** | Il riferimento necessario non era nel catalogo | Esposizione, budget, termini T1 |
| **Interpretazione errata** | Riferimento presente nel catalogo e non scelto | Prompt, modello, esempi |
| **Ambiguità del contratto** | Due interpretazioni entrambe esprimibili e plausibili | Contratto, oppure esito `clarification` |
| **Limite strutturale** | Fallimento livello 4 o 5 su una classe ricorrente | **RC4**: ricalibrare **D12** o arricchire il dizionario |
| **Difetto delle regole deterministiche** | Errore su `presentation` o su `limit` predefinito | Regole di derivazione — **non** il modello |
| **Atteso sbagliato** | A esame umano l'interpretazione prodotta è corretta | Registro delle equivalenze, o correzione del caso |

**L'ultima riga è la più importante e la meno praticata.** Un piano di valutazione che non ammette che l'atteso possa essere sbagliato produce lavoro su difetti inesistenti, ed è **RC5** nella sua forma operativa. Il campione di revisione di §9.4 esiste per intercettarla.

### 9.2 Dalla sezione alla causa

Il confronto per sezione indica dove; la **provenienza** indica su cosa. L'analisi combina i due assi: raggruppare i fraintendimenti per sezione e per frammento di testo produce l'elenco ordinato delle espressioni che il sistema comprende peggio.

```
fraintendimenti
   ├─ raggruppa per SEZIONE       →  quale parte dell'interrogazione
   ├─ raggruppa per FRAMMENTO     →  quali parole
   └─ ordina per FREQUENZA        →  quali prima
                                        │
                                        ▼
                       elenco ordinato di termini e forme
                                        │
                                        ▼
                       ingresso del lavoro sul dizionario (Fase 2)
```

È il collegamento che rende la Fase 2 un'attività con un ingresso definito anziché un proposito. Senza di esso, «arricchire il dizionario» è un'attività senza criterio di priorità, e verrebbe fatta sui termini che qualcuno ricorda anziché su quelli che costano di più.

### 9.3 Il fraintendimento plausibile

**R1** è il rischio di rango 1 dell'intero progetto, e ha una proprietà che lo rende diverso da tutti gli altri: **non produce sintomi.** L'utente riceve un risultato credibile e non ha ragione di dubitarne.

Ne discende che il tasso di correzione da parte dell'utente **non** è una misura di R1: misura i fraintendimenti che l'utente ha notato, che sono per definizione quelli meno pericolosi. Un tasso di correzione basso è compatibile con due situazioni opposte — un sistema accurato e un sistema che sbaglia in modo credibile — e da solo non le distingue.

Tre misure lo aggrediscono, e nessuna basta da sola:

| Misura | Che cosa coglie |
|---|---|
| **Accuratezza sul corpus sigillato** | I fraintendimenti che l'utente non avrebbe notato, perché l'atteso è annotato indipendentemente |
| **Casi con esito plausibile ma errato**, classificati a parte | La quota di errori che superano l'esame superficiale: sono quelli che contano |
| **Verifica campionaria su risultati reali** (§12.5) | Gli errori che il corpus non contiene perché nessuno ha pensato a quel caso |

La seconda merita una regola: nell'analisi, un errore va etichettato come **plausibile** quando l'interpretazione prodotta è internamente coerente e produrrebbe un risultato credibile. Il tasso di errori plausibili sul totale degli errori è un indicatore proprio, e **il suo aumento è un peggioramento anche a accuratezza costante**: significa che gli errori residui si stanno spostando verso la categoria che nessuno rileva.

### 9.4 La revisione manuale

Automatizzata la misura, resta necessaria una verifica umana periodica, con due obiettivi distinti che vanno tenuti separati.

**Campione di casi giudicati errati** — verifica che l'errore sia reale. Alimenta il registro delle equivalenze e la metrica di guardia su **RC5**. Ampiezza: almeno 30 casi per esecuzione di riferimento.

**Campione di casi giudicati corretti** — verifica che il corretto sia corretto. È il controllo che quasi nessuno esegue, e l'unico che intercetta un atteso annotato male: un caso con atteso sbagliato che il sistema riproduce fedelmente risulta corretto due volte, e la misura non se ne accorgerà mai. Ampiezza: almeno 20 casi.

Entrambi i campioni sono estratti in modo casuale. Un campione scelto produce la conferma di chi lo sceglie.

---

## 10. La Misura della Copertura

### 10.1 Il calcolo

```
caso del corpus
   ├─ interpretazione attesa   →  insieme dei riferimenti necessari
   └─ catalogo registrato      →  insieme dei riferimenti disponibili
                                    (Registro, per impronta — D41)

copertura del caso  =  necessari ⊆ disponibili        (quantificatore: TUTTI)
```

Il quantificatore è essenziale: un caso in cui manca un solo riferimento su cinque è un caso **scoperto**, perché l'interpretazione corretta resta irraggiungibile.

Il calcolo è deterministico e non richiede giudizio umano, perché entrambi i termini sono strutturati. È possibile **solo perché il Registro conserva il catalogo di ogni interazione** — ed è la ragione per cui **D41** è un prerequisito di questo documento e non un'ottimizzazione: una copertura ricostruita per approssimazione non può fare da soglia.

### 10.2 Perché la scomposizione è obbligatoria

| Componente | Fase | Se bassa |
|---|---|---|
| **Copertura dell'entità** | A / B | Arricchire i termini T1; rivedere soglia e margine di **D33** |
| **Copertura degli attributi** | C | **Difetto nelle regole di esposizione**, non nella selezione |

La seconda riga è una diagnosi precisa, e la precisione viene da una proprietà del disegno: in Fase C non c'è selezione, tutti gli attributi esposti dell'entità sono presenti. La copertura sugli attributi è quindi **esatta per costruzione**, e un valore sensibilmente inferiore a 100% non può essere un limite del metodo — è un attributo utile classificato come tecnico dalle regole di §5.3, oppure un budget tarato stretto.

È il motivo per cui la soglia sugli attributi (99,5%) è più alta di quella sull'entità: misurano cose di natura diversa. La prima è un controllo di correttezza delle regole; la seconda è la qualità del dizionario.

### 10.3 Gli indicatori che accompagnano la copertura

| Indicatore | Lettura |
|---|---|
| **Quota risolta in Fase A** | Efficacia dei termini T1. La sua crescita riduce simultaneamente costo, latenza e superficie non deterministica |
| **Dimensione media del catalogo** | Se cresce, l'esposizione è troppo permissiva: costo e accuratezza peggiorano insieme |
| **Rifiuti per budget** | Se non trascurabili, il budget di 60 attributi (**D31**) è stretto per qualche entità: va indagata quella, non alzato il budget |
| **Fallimenti di livello 3** | Riferimenti nominati e inesistenti: lacune del dizionario, materiale di arricchimento |
| **Chiarimenti per termine** | Termini ricorrenti non mappati |
| **Cambi di entità in conversazione** | Frequenza del caso di `06` §5.8, che costa una seconda interpretazione |

**La prima riga è l'indicatore di efficienza più importante del prodotto.** Ogni punto guadagnato in Fase A è una chiamata al modello risparmiata: costo, latenza e una quota di non determinismo che scompare. È anche l'unica leva di prestazioni di ordine di grandezza (`04` §10.2, Leva 1), e la sua crescita è la misura diretta del lavoro sul dizionario.

---

## 11. Valutazione non Interpretativa

L'accuratezza è la metrica più discussa e non è l'unica che decide se il prodotto è utilizzabile. Quattro famiglie di verifiche non riguardano la comprensione del linguaggio e sono ugualmente vincolanti.

### 11.1 La prova di isolamento

**D27** stabilisce la prova di isolamento come criterio di accettazione della prima release. È l'unica verifica che accerta **RA3**, ed è l'unica il cui esito riguarda utenti che non stanno usando il prodotto.

Il criterio è quello di `05` §7.1: sotto carico conversazionale, **l'ERP non deve degradare**. Non «deve degradare poco»: le operazioni ordinarie di Odoo — aprire una vista, salvare un record, confermare un ordine — devono restare entro i tempi misurati in assenza di carico conversazionale, con un margine dichiarato.

Alla prova va aggiunta l'ottava riga fissata in delibera: **verifica del tetto di connessioni**.

```
(worker_http)  +  (max_cron_threads)  +  (N_dispatcher × POOL)  ≤  0,8 × db_maxconn
```

È una verifica di configurazione, non di codice, e va eseguita a ogni variazione del dimensionamento. Un pool aumentato senza rifare questo calcolo esaurisce le connessioni, e il guasto si manifesta sull'ERP — cioè nel posto dove nessuno lo cercherà.

### 11.2 Prestazioni

Le tre soglie di **D5** sono già in §6.2. Qui conta il metodo, e in particolare due condizioni senza le quali la misura è ottimistica per costruzione.

**Si misura sotto carico realistico, non a vuoto.** L'attesa in coda è nulla quando nessuno usa il sistema, ed è la metrica che serve proprio quando qualcuno lo usa.

**Si misura con il catalogo freddo e caldo, separatamente.** La memorizzazione del catalogo (`04` §7.6) sposta 5–20 ms; l'invalidazione dopo un aggiornamento dei moduli li rimette in gioco per tutti gli utenti insieme. Una misura fatta solo a caldo descrive uno stato che il sistema non ha mai il giorno di un aggiornamento.

### 11.3 Sicurezza

Il KPI è **zero incidenti di accesso oltre i permessi**. Un valore atteso di zero non si misura osservando: si verifica costruendo i casi.

| Prova | Verifica |
|---|---|
| **Catalogo per utente** | Un utente senza permesso su un attributo non lo trova nel proprio catalogo — **D10** |
| **Revoca dei permessi** | Revocato un permesso, il catalogo memorizzato non viene servito — **D39** |
| **Multi-società** | Un utente con una società deselezionata non riceve record di quella società — **D40** |
| **Interrogazione condivisa** | Eseguita da un utente con meno privilegi, rende meno dati — `04` §9.5 |
| **Esecuzione asincrona** | Il dispatcher esegue con l'identità del richiedente, mai con privilegi propri — `05` §3.4 |
| **Assenza di elevazione** | Nessun contesto privilegiato nei percorsi di interrogazione — controllo di **D24** |

**Le righe su D39 e D40 sono nuove**, introdotte dalla delibera, e sono le due che nessuno costruirebbe spontaneamente: verificano proprietà che in esercizio ordinario non si manifestano mai, e falliscono in modo silenzioso. La prova sulla revoca in particolare è l'unica difesa contro un catalogo memorizzato che continua a esporre ciò che non deve.

### 11.4 Ispezionabilità

**V4** impone che nessun risultato sia presentato senza la sua interpretazione. La presenza è un invariante (§5.5); la **comprensibilità** è un'altra cosa e non è meccanizzabile.

`02` §4.2 fonda su **A9** — l'utente legge l'interpretazione e la corregge quando non corrisponde — un'intera difesa contro R1. **A9 è dichiarata come assunzione da validare con i clienti pilota, e non è mai stata validata.** Questo documento non può validarla, ma può dire come si fa: §12.5.

Se A9 cade, non cade una funzionalità: cade la principale difesa contro il rischio di rango 1, e il piano di valutazione resta l'unico presidio. È un'informazione che vale la pena avere presto.

---

## 12. Valutazione con Utenti Reali

### 12.1 Perché il corpus non basta

Il corpus misura l'interpretazione. L'utente giudica l'esito, e fra i due c'è tutto ciò che il corpus non contiene: la leggibilità dell'interpretazione, la qualità dei chiarimenti, la ragionevolezza dei limiti, la fiducia.

Un sistema può essere accurato al 92% ed essere abbandonato, e le ragioni non comparirebbero in nessuna metrica di §5: chiarimenti formulati in modo incomprensibile, un limite di 80 record percepito come troncamento arbitrario, un'attesa non spiegata.

### 12.2 Le metriche di esercizio

Provengono dal Registro, non dal corpus.

| Metrica | Definizione | Soglia |
|---|---|---|
| **Risoluzione al primo tentativo** | Richieste risolte senza riformulazione né correzione | ≥ 75% |
| **Passi per risultato** | Interazioni medie fino al risultato | ≤ 2 |
| **Tasso di abbandono** | Sessioni chiuse senza risultato utile | ≤ 10% |
| **Tasso di correzione** | Interpretazioni corrette manualmente | Sorvegliato — vedi §9.3 |
| **Risultati vuoti** | Interrogazioni con zero record | Sorvegliato: se alto, i filtri sono troppo stretti o l'utente non è capito |
| **Quota in ripiego** | Sessioni senza websocket, con interrogazione periodica | Se cresce, il carico torna sui worker HTTP — `05` §3.5 |
| **Ampiezza del dominio** | Entità distinte effettivamente interrogate | In crescita |

**La riga sui risultati vuoti è quella che collega esercizio e corpus.** Un'interrogazione che restituisce zero record è, dal punto di vista dell'utente, indistinguibile da un fraintendimento — e spesso lo è. È una fonte di candidati per il corpus fra le più produttive, e non compare fra le cinque di `04` §13.3.

### 12.3 Le attività di riferimento

**Dipendono da D7.** Sono un elenco di compiti reali che un utente deve poter completare — *"trova gli ordini non ancora consegnati del cliente X"*, *"quali fatture sono scadute da più di 30 giorni"* — definiti dal cliente, non dal fornitore.

Servono a due misure che il corpus non produce: l'**autonomia del nuovo utente** (≥ 80% delle attività completate senza formazione, entro il primo giorno) e il confronto dei tempi con l'interfaccia nativa.

### 12.4 La misura iniziale, che si può fare una volta sola

> **La misura dei tempi sull'interfaccia nativa va eseguita prima dell'attivazione del prodotto.**

Il KPI *"riduzione ≥ 80% del tempo di accesso all'informazione"* richiede un termine di paragone. Quel termine è il tempo che gli utenti impiegano oggi, con menu, filtri e viste. Dopo l'attivazione non è più ottenibile: gli utenti hanno cambiato abitudini, e una misura fatta dopo misura persone diverse da quelle di prima.

È l'unico dato del progetto che **non è ricostruibile a posteriori**, ed è per questo che compare fra i requisiti di chiusura di **D7** nel registro delle decisioni. Costa poche ore di osservazione su un campione di utenti e sulle attività di riferimento. Non farla significa rinunciare per sempre al KPI più efficace da comunicare.

### 12.5 La verifica di A9

L'assunzione che gli utenti leggano l'interpretazione va validata, e si valida con l'osservazione, non con un questionario — chiunque, interrogato, dichiara di leggere.

Tre misure, in ordine di costo crescente:

**Il tasso di correzione, letto per utente.** Se una quota rilevante di utenti non ha mai corretto un'interpretazione, o non sbaglia mai o non la legge. Il corpus dice quale delle due.

**L'iniezione controllata**, sui pilota e con il loro consenso: un campione di interpretazioni contiene una discrepanza deliberata e innocua rispetto alla richiesta. La quota di utenti che la rilevano **è** la misura di A9. Va fatta su un campione ristretto e dichiarata al cliente, perché è un esperimento sulle persone e va trattato come tale.

**La verifica campionaria sui risultati reali**: un revisore controlla un campione di interrogazioni realmente eseguite e ne giudica la corrispondenza all'intenzione dichiarata dall'utente. È la sola misura che coglie i fraintendimenti plausibili che il corpus non contiene perché nessuno ha pensato a quel caso (§9.3).

---

## 13. Qualificazione di un Nuovo Modello

### 13.1 Perché serve un protocollo

**V5** impone che nessuna capacità dipenda in modo esclusivo da un fornitore, e `04` §8 concentra la conoscenza dei fornitori in un solo componente. La sostituibilità è quindi architetturalmente risolta.

Ma sostituibile non significa equivalente: un modello diverso produce interpretazioni diverse, con una distribuzione di errori diversa. Il cambio va trattato come una modifica al cuore del prodotto, perché lo è. Senza protocollo, la decisione verrebbe presa su un confronto di prezzo o su un'impressione tratta da qualche esempio.

### 13.2 Il protocollo

| Passo | Verifica | Criterio |
|---|---|---|
| 1 | Conformità allo schema | Fallimenti di validazione livello 1–2 **non superiori** al modello attivo. Un tasso alto indica generazione vincolata non applicata (`03` §12.3) |
| 2 | Accuratezza su corpus di regressione | Non inferiore, per sezione |
| 3 | Accuratezza su corpus sigillato | Non inferiore |
| 4 | Stabilità su K = 5 | ≥ 98% (§8.2) |
| 5 | Ricalcolo della soglia di rumore | È una proprietà del modello (§8.3) |
| 6 | Calibrazione della confidenza | Empirica, sul corpus |
| 7 | Latenza e costo | Entro le soglie di **D5**; costo per interazione dichiarato |
| 8 | Prova di isolamento | Un modello più lento cambia il profilo di carico — **D27** |

**Il passo 8 è quello che si dimentica.** Un modello con latenza doppia raddoppia il tempo di occupazione dei thread del pool, dimezza la capacità del dispatcher e sposta il carico verso i limiti di **D20c**. Le conseguenze non sono sull'accuratezza: sono sull'ERP. Un cambio di modello è anche una modifica del dimensionamento.

### 13.3 La confidenza va ricalibrata, non ereditata

**RC6** avverte che la confidenza non è una probabilità. Ne discende che la calibrazione osservata su un modello **non trasferisce** a un altro: due modelli che dichiarano 0,9 non dichiarano la stessa cosa.

Il valore ha un uso legittimo — ordinare i casi per revisione, individuare le richieste da sottoporre a chiarimento — e un uso vietato: decidere automaticamente di saltare una conferma. La ricalibrazione a ogni cambio di modello è ciò che mantiene legittimo il primo uso; il divieto sul secondo non dipende dalla calibrazione ed è permanente.

### 13.4 Il criterio di accettazione

> Un nuovo modello è accettato se **nessuno degli otto passi peggiora**, oppure se un peggioramento è compensato da un beneficio dichiarato e approvato come deroga di §7.4, con scadenza.

Un modello che migliora l'accuratezza complessiva peggiorando una sezione **non** è accettato senza deroga: è la stessa regola di §7.1, applicata alla sostituzione anziché al rilascio. La ragione è identica — le medie nascondono i peggioramenti localizzati — e vale la pena applicarla qui perché un cambio di modello è precisamente l'occasione in cui si guarda un numero solo.

---

## 14. Strumenti e Collocazione

### 14.1 Dove vive che cosa

Tutto in `nli_observability`, che nel grafo di **D18** dipende dal solo `nli_core`.

| Componente | Responsabilità |
|---|---|
| **Registro** | Turni, buste, esiti di validazione, impronte di catalogo |
| **Archivio cataloghi** | Cataloghi deduplicati per impronta — **D41** |
| **Corpus** | Le tre popolazioni, con controllo di accesso distinto sul sigillato |
| **Esecutore di valutazione** | Esecuzione a parametri congelati, confronto, aggregazione |
| **Registro delle equivalenze** | Versionato — §2.3 |
| **Rapporti** | Con il vincolo di §5.4: mai accuratezza senza copertura |

**Il controllo di accesso sul corpus sigillato è un requisito funzionale, non una convenzione.** Un sigillo che dipende dalla disciplina delle persone non è un sigillo: è una richiesta. Va realizzato come autorizzazione, con la stessa serietà di **D38** sul dizionario.

### 14.2 Esecuzione

L'esecuzione automatica del corpus a ogni modifica è il carico più massiccio che il sistema produce. Gira sul **dispatcher differito di D20d**, mai sul pool interattivo.

È una conseguenza diretta della delibera: senza separazione, la verifica della qualità degraderebbe l'esperienza degli utenti — un esito che avrebbe la spiacevole proprietà di rendere la misura impopolare presso le persone che dovrebbero difenderla.

### 14.3 Il corpus è un artefatto versionato

Con versione, storia delle modifiche e possibilità di rieseguire una misura passata. Senza versionamento, un confronto fra un rilascio di oggi e uno di sei mesi fa non ha significato: il corpus è cambiato, e non si sa come.

Il versionamento del corpus si combina con quello del dizionario (**D36**) e del contratto: una misura è **completamente descritta** dalla quaterna corpus, dizionario, contratto, modello+prompt, più la versione del registro delle equivalenze. È l'insieme minimo che rende una misura riproducibile a distanza di anni — che è l'orizzonte dichiarato dal documento di visione.

---

## 15. Governo

### 15.1 Responsabilità

| Chi | Che cosa |
|---|---|
| **Architect** | Approva le soglie; concede le deroghe di §7.4; decide i cancelli di fase |
| **Responsabile della qualità** | Possiede il corpus e le linee guida di annotazione; esegue la revisione manuale; **non** lavora su prompt e dizionario |
| **Chi sviluppa** | Accede a sviluppo e regressione; **mai** al sigillato |
| **Cliente** | Fornisce le attività di riferimento; annota i casi del proprio dominio |

**La separazione fra chi possiede il corpus e chi lavora sul prompt non è organizzativa: è la condizione di validità del sigillo.** In un gruppo piccolo può coincidere con una separazione di ruoli nella stessa persona in momenti diversi — ma allora il controllo di accesso di §14.1 diventa l'unica difesa effettiva, e va realizzato prima, non dopo.

### 15.2 Cadenza

| Attività | Frequenza |
|---|---|
| Esecuzione sul corpus di regressione | A ogni modifica rilevante, automatica |
| Esecuzione sul sigillato | A ogni rilascio |
| Revisione manuale dei campioni (§9.4) | A ogni esecuzione di riferimento |
| Riesame delle metriche di guardia | Mensile |
| Riesame del bilanciamento del corpus | Trimestrale |
| Ricalibrazione delle soglie | Dopo il primo trimestre, poi annuale |
| Verifica di A9 | Una volta in Fase 1, ripetuta in Fase 2 |

### 15.3 Che cosa si pubblica

Ogni misura riportata all'esterno del gruppo di lavoro dichiara: popolazione usata, dimensione, intervallo di confidenza, quaterna dei parametri congelati, e **copertura accanto all'accuratezza**.

Una misura pubblicata senza questi elementi non è verificabile, e una misura non verificabile diventa, con il tempo, un numero che circola senza che nessuno ricordi da dove viene.

---

## 16. Rischi del Piano

I rischi seguenti sono propri della misura. Si aggiungono a quelli dei documenti precedenti e hanno una caratteristica comune che li rende insidiosi: **quando si manifestano, i numeri migliorano.**

### RV1 — Il corpus non è rappresentativo

**Descrizione.** Il corpus riflette ciò che i pilota hanno immaginato di poter chiedere, non il linguaggio reale della popolazione di utenti.
**Impatto. Alto.** L'accuratezza misurata non predice quella percepita; le soglie autorizzano avanzamenti non meritati.
**Mitigazione.** Crescita continua dal Registro (§3.3); bilanciamento verificato trimestralmente (§3.6); età mediana dei casi come metrica di guardia; almeno due pilota di domini diversi (**D7**).
**Segnale anticipatore.** Accuratezza alta sul corpus e tasso di correzione alto in esercizio.

### RV2 — Adattamento al corpus visibile

**Descrizione.** Il lavoro su prompt e dizionario ottimizza i casi noti. L'accuratezza sale sul corpus di sviluppo e non sulla popolazione reale.
**Impatto. Alto sul governo.** È il rischio che rende una misura inservibile senza che nessuno se ne accorga: il procedimento che lo produce è il procedimento corretto di miglioramento.
**Mitigazione.** Corpus sigillato (§3.1) con controllo di accesso realizzato come autorizzazione (§14.1); distanza sviluppo − sigillato come metrica di guardia; sigillo che si rompe una volta sola (§3.7).
**Segnale anticipatore.** La distanza fra le due misure che cresce nel tempo.

### RV3 — La canonicalizzazione sottostima

**Descrizione.** Interpretazioni corrette ma formulate diversamente vengono conteggiate come errate. È **RC5** nella sua forma operativa.
**Impatto. Medio-alto sul governo.** Porta a rinviare avanzamenti legittimi e a lavorare su difetti inesistenti.
**Mitigazione.** Registro delle equivalenze (§2.3); campione di revisione sui casi giudicati errati (§9.4); metrica di guardia con soglia al 5%.
**Segnale anticipatore.** Casi giudicati errati che a esame umano risultano corretti.

### RV4 — L'annotazione è incoerente

**Descrizione.** Persone diverse, o la stessa persona in momenti diversi, annotano lo stesso caso in modo diverso. La definizione di corretto deriva silenziosamente.
**Impatto. Alto**, perché degrada il termine di confronto: un corpus incoerente rende non confrontabili anche misure per il resto ineccepibili.
**Mitigazione.** Linee guida versionate (§3.4); doppia annotazione sul 10%; disaccordo risolto dichiarando una regola, mai scegliendo un vincitore; sospensione del giudizio sulle primarie oltre il 10% di disaccordo.
**Segnale anticipatore.** Casi limite risolti a voce e non scritti nelle linee guida.

### RV5 — La metrica diventa l'obiettivo

**Descrizione.** L'accuratezza sale perché si lavora sull'accuratezza, non sul prodotto. Nelle forme più eleganti: equivalenze aggiunte al registro per far passare casi, casi difficili spostati dal sigillato, soglie ricalibrate durante il cancello.
**Impatto. Alto sull'orizzonte pluriennale.** È il rischio **R9** applicato alla misura.
**Mitigazione.** Aggiunta di equivalenze trattata come modifica del contratto, con riesecuzione e attribuzione (§2.3); assegnazione casuale fra popolazioni (§3.3); divieto di ricalibrare durante un cancello (§6.4); metriche primarie limitate a quattro (§5.2).
**Segnale anticipatore.** Miglioramenti dell'accuratezza che nessun utente percepisce.

### RV6 — Il rumore viene letto come segnale

**Descrizione.** Fluttuazioni entro la variabilità del modello vengono riportate come miglioramenti o regressioni.
**Impatto. Medio-alto.** Produce lavoro su problemi inesistenti e, nella direzione opposta, blocca rilasci per regressioni che non sono avvenute — fino a quando il cancello viene disattivato perché scatta a caso.
**Mitigazione.** Stabilità su K = 5 e soglia di rumore a due deviazioni standard (§8); ricalcolo a ogni cambio di modello; corpus abbastanza grande da rendere la soglia utile (§3.5).
**Segnale anticipatore.** Relazioni che riportano variazioni con due decimali.

### RV7 — La misura viene rinviata

**Descrizione.** Sotto pressione di consegna, l'esecuzione del corpus, l'annotazione e la revisione manuale vengono differite. È il rischio **R5** del documento di visione, e il rischio principale dichiarato della Fase 2.
**Impatto. Alto.** Una misura periodica non protegge da nulla, e la Fase 2 senza misura è una fase senza contenuto.
**Mitigazione.** Esecuzione automatica a evento, non a decisione (§4.3); regressione che blocca il rilascio (§7.4); carico su dispatcher differito perché non entri in competizione con l'esercizio (§14.2).
**Segnale anticipatore.** Rilasci con deroga concessa senza scadenza.

### RV8 — Il corpus diventa un archivio di dati personali

**Descrizione.** Le richieste reali contengono nomi di clienti, fornitori, dipendenti. Il corpus è conservato per anni, replicato fra ambienti e usato in collaudo.
**Impatto. Alto in conformità**, e crescente con la vita del prodotto: è un archivio che nessuno considera tale finché qualcuno non lo cerca.
**Mitigazione.** Sostituzione con segnaposto stabili prima dell'inserimento (§3.7); nessuna eccezione per «casi difficili da anonimizzare», che sono precisamente quelli con più dati personali. Il trattamento complessivo è materia del **documento 08**.
**Segnale anticipatore.** Casi inseriti «temporaneamente» in forma originale.

---

## 17. Decisioni Richieste

Numerazione in continuità con il registro deliberato (D1–D41).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D42** | Tre popolazioni di corpus, con **corpus sigillato** protetto da controllo di accesso realizzato come autorizzazione (§3.1, §14.1) | **Adottare** | La misura degrada in conferma entro pochi trimestri, senza alcun segnale |
| **D43** | **Registro delle equivalenze semantiche** chiuso, versionato; aggiunta trattata come modifica del contratto (§2.3) | **Adottare** | O si sottostima l'accuratezza (RC5), o la soglia diventa negoziabile caso per caso |
| **D44** | Soglia di **accuratezza per sezione ≥ 85%**, in aggiunta alla soglia complessiva (§6.2) | **Adottare** | Una media conforme può nascondere una sezione inservibile |
| **D45** | Dimensioni del corpus: 1 000 casi di regressione e 300 sigillati iniziali; 3 000 e 1 000 al completamento della Fase 2 (§3.5) | **Adottare** | La soglia di rumore resta più alta dei miglioramenti da rilevare |
| **D46** | Requisiti di bilanciamento di §3.6, incluso ≥ 40% di turni di raffinamento e i casi multi-società | **Adottare** | Si misura la parte del prodotto che somiglia a un motore di ricerca |
| **D47** | **Sostituzione dei riferimenti a persone e organizzazioni** con segnaposto stabili prima dell'inserimento nel corpus (§3.7) | **Adottare** | RV8; e il corpus resta non condivisibile fra clienti |
| **D48** | **Stabilità** su K = 5 con soglia ≥ 98%, e soglia di rumore a due deviazioni standard, ricalcolata a ogni cambio di modello (§8) | **Adottare** | Ogni fluttuazione diventa un risultato; il cancello di regressione scatta a caso |
| **D49** | Cancello di Fase 2 sulle **otto condizioni** di §6.3, con l'accuratezza giudicata sull'**estremo inferiore** dell'intervallo di confidenza | **Adottare** | La scrittura sui dati aziendali viene autorizzata su una misura imprecisa |
| **D50** | Regressione **per sezione** con blocco del rilascio; deroga concessa dall'Architect, registrata e **con scadenza** (§7) | **Adottare** | La prima deroga senza scadenza stabilisce che le regressioni sono negoziabili |
| **D51** | Protocollo di qualificazione di un nuovo modello in **otto passi**, inclusa la prova di isolamento (§13.2) | **Adottare** | Un cambio di modello deciso sul prezzo può degradare l'ERP |
| **D52** | **Misura iniziale sull'interfaccia nativa prima dell'attivazione** presso ogni pilota (§12.4) | **Adottare** — dipende da **D7** | Il KPI di riduzione del tempo di accesso non è più ottenibile. Mai |
| **D53** | Le tre metriche di §5.5 — origine, provenienza, presenza dell'interpretazione — come indicatori propri con le rispettive soglie | **Adottare** | Un sistema accurato che non dichiara mai l'origine risulterebbe conforme pur violando P3 |

**D42, D43, D49 e D52 sono le decisioni bloccanti.** Le prime tre determinano se la misura è una valutazione o una conferma, e senza di esse il cancello di **D2** non è difendibile. **D52** è diversa dalle altre tre: non è bloccante per il metodo, è bloccante nel tempo. È l'unica decisione dell'intero progetto la cui finestra si chiude da sola — il giorno dell'attivazione del primo pilota, e senza preavviso.

---

## 18. Glossario

| Termine | Definizione |
|---|---|
| **Corpus di sviluppo** | Casi accessibili a chi lavora sul prodotto; strumento di lavoro, non di giudizio |
| **Corpus di regressione** | Sottoinsieme stabile eseguito a ogni modifica per il confronto fra rilasci |
| **Corpus sigillato** | Casi non accessibili a chi lavora su prompt e dizionario; misura di riferimento per soglie e cancelli |
| **Forma canonica** | Riduzione dello Stato di Interrogazione alla sola semantica (`03` §14.3) |
| **Equivalenza semantica** | Forme canoniche diverse con risultato provabilmente identico per ogni insieme di dati |
| **Equivalenza di esito** | Stesso insieme di record su questi dati. **Vietata come criterio** |
| **Registro delle equivalenze** | Elenco chiuso e versionato delle equivalenze semantiche riconosciute |
| **Copertura** | Percentuale di casi in cui **tutti** i riferimenti necessari erano nel catalogo fornito |
| **Stabilità** | Percentuale di casi che producono la stessa interpretazione su K esecuzioni identiche |
| **Soglia di rumore** | Variazione entro la quale un movimento non è interpretabile |
| **Errore plausibile** | Errore internamente coerente, che produce un risultato credibile |
| **Metrica di guardia** | Indicatore che sorveglia la validità della misura, non la qualità del prodotto |
| **Parametri congelati** | Istante, versione del dizionario, versione del contratto, modello e prompt |
| **Attività di riferimento** | Compiti reali definiti dal cliente, usati per autonomia e confronto dei tempi |

---

## Chiusura

Il documento di visione afferma che nessun ampliamento d'ambito è autorizzato senza misura. È una promessa che si mantiene o si perde qui, e si perde in un modo particolare: non rinunciando a misurare, ma continuando a misurare qualcosa che ha smesso di significare ciò che si crede.

È la ragione per cui questo piano dedica più spazio alle difese della misura che alla misura stessa. Calcolare l'accuratezza è meccanico una volta definita la forma canonica, e il contratto l'aveva già definita. Ciò che non è meccanico è mantenere quella misura onesta per anni, mentre le stesse persone che la producono hanno interesse a vederla salire — non per disonestà, ma perché è il segnale che il loro lavoro sta funzionando.

Le tre difese che contano sono il **corpus sigillato**, che sottrae al miglioramento i casi su cui si giudica; il **registro delle equivalenze**, che impedisce di spostare la soglia definendo diversamente la correttezza; e la **lettura congiunta di accuratezza e copertura**, che impedisce la diagnosi sbagliata più frequente. Tutte e tre costano attrito, e tutte e tre verranno messe in discussione. Vale la pena aver scritto adesso perché esistono.

Resta un punto che nessuna disciplina interna può risolvere. **A9** — l'utente legge l'interpretazione e la corregge — regge da sola l'intera difesa contro il rischio di rango 1, è dichiarata da validare con i pilota, e non è mai stata validata. Se cade, non cade una funzionalità: cade la ragione per cui il prodotto può mostrare un risultato senza che qualcuno lo verifichi. §12.5 dice come misurarla, e vale la pena farlo presto, quando il costo di scoprirlo è ancora una modifica di interfaccia.

**Documenti successivi**, in ordine di dipendenza:

1. **Modello di Sicurezza e Conformità** — identità, autorizzazioni, tracciabilità, trattamento dell'enunciato verso il fornitore *(dipende da D3 come qualificata in delibera, D39, D40, RV8)*
2. **Linee guida di Esperienza Utente** — interpretazione ispezionabile, stati non ideali, disambiguazione *(dipende da A9, §12.5, D53)*
3. **Linee guida di Annotazione** — artefatto operativo, versionato, generato dal primo corpus *(dipende da D42, D46)*

---

*Fine del documento.*
