# Specifica del DSL
## Contratto di Interpretazione – AI Agent per Odoo

---

| Voce | Valore |
|---|---|
| **Titolo** | Specifica del DSL – Contratto di Interpretazione |
| **Versione** | 1.0 (bozza) |
| **DSL descritto** | `dsl_version` 1.0 — profilo **sola lettura** |
| **Data** | 27 luglio 2026 |
| **Stato** | Bozza sottoposta ad approvazione dell'Architect |
| **Destinatari** | Solution Architect, Software Architect, Team Leader, Sviluppatori backend e AI |
| **Documento sorgente** | `02-visione-prodotto.md` — Visione del Prodotto e Specifica Concettuale |
| **Ambito** | Struttura, semantica, validazione, versionamento ed evoluzione del contratto fra componente AI e backend deterministico |
| **Fuori ambito** | Architettura dei componenti, infrastruttura, persistenza, strategia di prompting, implementazione del motore di esecuzione |

> **Prerequisito.** Questo documento presuppone l'approvazione di `02-visione-prodotto.md` e in particolare delle decisioni **D2** (Fase 2 come cancello prima della scrittura), **D3** (assunzione A6 sui dati verso il modello) e **D4** (Stato di Interrogazione come oggetto centrale). Le decisioni D3 e D4 sono qui date per adottate: se venissero respinte, questo documento va riscritto, non emendato.

---

## 1. Executive Summary

### 1.1 Cosa definisce questo documento

Il documento di visione stabilisce che **l'unico output della componente AI è un DSL strutturato**, e che tutto ciò che accade dopo la produzione del DSL è deterministico. Questo documento definisce quel DSL: cosa può esprimere, come viene validato, come evolve.

Il DSL non è un formato di scambio. È il **punto in cui il sistema smette di essere probabilistico**. Ogni proprietà di affidabilità dichiarata nel documento di visione si regge su come questo contratto è progettato.

### 1.2 Le tre decisioni portanti

**Il contratto è composto da due artefatti, non da uno.**
Il modello non produce lo stato completo dell'interrogazione: produce una sequenza di **operazioni**. Lo **Stato di Interrogazione** è il risultato deterministico dell'applicazione di quelle operazioni allo stato corrente. Il modello descrive il cambiamento; il sistema possiede il risultato (§4).

**Il contratto è semantico, non tecnico.**
Le operazioni non contengono nomi di modelli Odoo, nomi di campi, percorsi di relazione o espressioni domain. Contengono **riferimenti semantici** scelti da un catalogo fornito al modello e risolti in modo deterministico dal Dizionario Semantico (§7). Il modello non può nominare ciò che non esiste.

**Il contratto non sa esprimere la scrittura.**
Il vocabolario delle operazioni della versione 1.0 non contiene alcun verbo mutante. La sola lettura non è un controllo applicato all'output del modello: è una proprietà della grammatica. Le operazioni di scrittura della Fase 5 richiederanno una famiglia di operazioni nuova, con una propria semantica di conferma, non un permesso aggiuntivo (§13.1, raccomandazione §18.4 del documento di visione).

### 1.3 La catena completa

```
  frase utente
       │
       ▼
  ┌─────────────────┐
  │  COMPRENSIONE   │  probabilistico  ── unico punto non deterministico
  └─────────────────┘
       │
       ▼  Operazioni (semantiche, minimali, con provenienza)
  ┌─────────────────┐
  │   VALIDAZIONE   │  5 livelli — nulla di non valido prosegue        §12
  └─────────────────┘
       │
       ▼
  ┌─────────────────┐
  │  APPLICAZIONE   │  merge deterministico sullo stato corrente
  └─────────────────┘
       │
       ▼  Stato di Interrogazione (semantico, canonico, persistibile)   §5
  ┌─────────────────┐
  │   RISOLUZIONE   │  a ogni esecuzione: dizionario + permessi utente  §7.4
  └─────────────────┘
       │
       ▼  Piano di Esecuzione (tecnico, effimero, mai persistito)
  ┌─────────────────┐
  │   ESECUZIONE    │  ORM Odoo, identità e permessi dell'utente
  └─────────────────┘
       │
       ▼
  vista Odoo nativa  +  interpretazione ispezionabile
```

Il DSL comprende i due artefatti in grassetto: **Operazioni** e **Stato di Interrogazione**. Il Piano di Esecuzione è fuori dall'ambito di questo documento: è un dettaglio implementativo del motore, deliberatamente non contrattualizzato per lasciarlo libero di evolvere con Odoo.

### 1.4 Perché la risoluzione avviene a ogni esecuzione

Lo Stato di Interrogazione persiste **riferimenti semantici**, mai binding tecnici. La traduzione in nomi di modelli e campi avviene ad ogni esecuzione, non una volta sola al momento del salvataggio.

Questa scelta, apparentemente inefficiente, ha due conseguenze che nessuna alternativa offre:

- **i permessi sono sempre quelli attuali**. Un'interrogazione salvata sei mesi fa da un utente con più privilegi, eseguita oggi da un utente con meno privilegi, mostra ciò che l'utente attuale può vedere. Senza ri-risoluzione, uno stato salvato diventerebbe una scorciatoia permanente verso dati non più autorizzati — una violazione diretta del vincolo **V2**;
- **le interrogazioni salvate sopravvivono all'evoluzione dell'installazione**. Un modulo aggiornato, un campo rinominato, una personalizzazione modificata non invalidano lo stato: invalidano al più una singola risoluzione, che il dizionario può assorbire. È la condizione pratica per rispettare il vincolo **V6**.

### 1.5 Cosa questo contratto rende misurabile

Un effetto meno evidente ma decisivo: definendo una **forma canonica** e una **relazione di equivalenza** sugli stati (§14), il contratto rende possibile confrontare in modo automatico l'interpretazione prodotta dal modello con quella attesa.

Senza questa definizione, il corpus di valutazione previsto dal documento di visione non sarebbe utilizzabile: si potrebbero raccogliere richieste e risposte attese, ma non decidere meccanicamente se una risposta è corretta. L'accuratezza tornerebbe a essere un giudizio umano, e con essa svanirebbe il presupposto della Fase 2 e del cancello verso la scrittura.

**La forma canonica è quindi un requisito di governo del prodotto, non un'ottimizzazione tecnica.**

---

## 2. Ruolo del DSL nel Prodotto

### 2.1 Le quattro funzioni del contratto

Il DSL assolve simultaneamente a quattro funzioni. Confonderle è la causa più comune di contratti mal progettati.

**Funzione 1 — Confine di validazione.**
Ciò che il modello produce non viene eseguito: viene prima validato. Un output non valido non raggiunge mai il motore di esecuzione e si trasforma in una domanda all'utente, non in un comportamento inatteso del sistema.

**Funzione 2 — Perimetro delle capacità.**
Il sistema può fare esattamente ciò che il DSL sa esprimere. L'ampliamento delle capacità è un atto deliberato di progettazione del contratto, non una conseguenza emergente delle capacità del modello. Un modello più capace non rende il sistema più pericoloso.

**Funzione 3 — Superficie di disaccoppiamento.**
A monte del contratto può cambiare tutto: modello, fornitore, lingua, canale, strategia di prompting. A valle può cambiare tutto: versione di Odoo, moduli, tipologie di vista. Il contratto è ciò che consente ai due lati di evolvere senza coordinamento.

**Funzione 4 — Oggetto di misura.**
Il contratto è ciò che si confronta per stabilire se un'interpretazione è corretta. È l'unità di valutazione dell'accuratezza.

### 2.2 Cosa il DSL non è

| Non è | Perché la distinzione conta |
|---|---|
| Un linguaggio di query | Non esprime *come* recuperare i dati, ma *cosa* l'utente vuole vedere. Non contiene join, subquery, proiezioni |
| Un domain Odoo | Un domain è un'espressione tecnica arbitraria; il DSL è un vocabolario chiuso e semantico (§8.4) |
| Un formato di serializzazione della chat | Non contiene messaggi, turni o testo conversazionale, salvo la provenienza (§10) |
| Un linguaggio general purpose | Non ha variabili, funzioni, cicli, condizionali. È deliberatamente non Turing-completo (§3.4) |
| Un'API pubblica | È un contratto interno versionato; l'eventuale esposizione esterna è una decisione successiva |

### 2.3 Il principio di minimalità applicato al contratto

Il principio **P4** del documento di visione — *minimalità della componente AI* — si traduce qui in una regola progettuale precisa:

> **Ogni informazione che può essere derivata deterministicamente non deve essere richiesta al modello.**

Esempi di applicazione, sviluppati nelle sezioni indicate:

- il modello non calcola le date assolute: emette espressioni temporali simboliche (§9.2);
- il modello non decide la tolleranza di *"circa centomila"*: emette un marcatore di vaghezza con il risolutore da applicare (§9.3);
- il modello non sceglie il tipo di vista quando l'utente non lo indica: lo lascia non specificato e regole deterministiche lo derivano (§6.7);
- il modello non ricostruisce lo stato completo a ogni turno: emette solo il cambiamento (§4);
- il modello non risolve *"Rossi"* in un identificativo di record: emette il letterale, la risoluzione referenziale è deterministica (§11.3).

Ogni voce di questo elenco è una porzione di superficie non deterministica eliminata. Sommate, riducono l'esposizione al rischio **R1** — il fraintendimento plausibile — più di qualunque miglioramento del modello.

---

## 3. Criteri di Progettazione del Contratto

Gli otto criteri seguenti governano ogni decisione di questo documento e ogni futura estensione. Sono la traduzione operativa, sul contratto, dei principi P1–P8 del documento di visione.

### C1 — Vocabolario chiuso
Ogni elemento del contratto — operazioni, predicati, risolutori, tipi di vista, funzioni di aggregazione — appartiene a un insieme finito ed enumerato nella specifica. Il modello **sceglie**, non inventa.
*Motivazione.* Un vocabolario aperto rende la validazione impossibile in linea di principio: non si può verificare la correttezza di un simbolo di cui non si conosce l'insieme di appartenenza. È inoltre la condizione che consente la generazione vincolata: se l'insieme dei simboli ammessi è noto, il modello può essere costretto a produrre solo output validi anziché essere corretto a posteriori.

### C2 — Semantico, mai tecnico
Le operazioni contengono riferimenti al linguaggio dell'organizzazione, mai nomi tecnici di Odoo.
*Motivazione.* Il modello non conosce lo schema di questa specifica installazione, e non può conoscerlo: moduli, personalizzazioni e campi variano da cliente a cliente. Chiedergli nomi tecnici significa chiedergli di inventarli — la modalità di errore più frequente e più difficile da rilevare, perché un nome di campo plausibile ma inesistente produce un fallimento tardivo e opaco.

### C3 — Impossibilità strutturale al posto del divieto
Ciò che il sistema non deve fare, il contratto non deve saperlo esprimere.
*Motivazione.* Un divieto verificato a valle dipende dalla correttezza di un controllo, e prima o poi viene aggirato da un difetto, da una deroga o da una configurazione. Un'impossibilità grammaticale non richiede vigilanza e non ammette eccezioni.

### C4 — Nessuna espressione arbitraria
Il contratto non ammette stringhe interpretate come codice, espressioni da valutare, percorsi liberi o strutture ricorsive senza limite.
*Motivazione.* Ogni forma di espressione arbitraria reintroduce la generazione di codice dalla porta di servizio, con le conseguenze di sicurezza e di imprevedibilità che il documento di visione esclude (V1, V3).

### C5 — Determinismo dell'applicazione
Date le stesse operazioni e lo stesso stato di partenza, lo stato risultante è sempre identico. Dato lo stesso stato e lo stesso momento di esecuzione, il risultato è sempre identico.
*Motivazione.* È la definizione operativa del principio P1. Senza di essa non esistono riproducibilità, annullamento affidabile né valutazione automatica.

### C6 — Provenienza obbligatoria
Ogni elemento dello stato registra da dove proviene: da un'espressione esplicita dell'utente, da un'inferenza del sistema o da un valore predefinito.
*Motivazione.* È il presupposto tecnico dell'interpretazione ispezionabile (P3). Senza provenienza, l'interfaccia non può distinguere ciò che l'utente ha chiesto da ciò che il sistema ha aggiunto, e l'utente non può riconoscere un fraintendimento.

### C7 — Estensibilità additiva
Ogni evoluzione del contratto aggiunge; non modifica il significato di ciò che esiste e non rimuove senza un ciclo di deprecazione dichiarato.
*Motivazione.* È la condizione del vincolo V6: le interrogazioni salvate oggi devono funzionare fra cinque anni.

### C8 — Confrontabilità
Due stati semanticamente equivalenti devono avere una sola forma canonica, e deve esistere una relazione di equivalenza definita e calcolabile.
*Motivazione.* È ciò che rende il corpus di valutazione utilizzabile, la cache degli stati corretta e la deduplicazione delle interrogazioni salvate possibile (§14).

### 3.9 Un criterio deliberatamente assente: l'espressività

Non figura fra i criteri la massimizzazione dell'espressività. È un'omissione voluta.

Un contratto più espressivo copre più richieste ma amplia la superficie di ciò che può essere frainteso in modo plausibile, e rende la validazione più debole. Di fronte a una richiesta rara che il contratto non sa esprimere, la risposta corretta del prodotto è dichiarare il limite (§10.5 del documento di visione), non estendere la grammatica.

**L'espressività si aggiunge quando i dati la richiedono** — quando il corpus mostra una classe ricorrente di richieste non esprimibili — **non quando si immagina che possa servire.**

---

## 4. Modello Concettuale: Due Artefatti

> **Nota sulla notazione.** Gli esempi strutturati di questo documento usano JSON. La scelta è motivata in §18.1 ed è essa stessa una decisione del contratto: gli esempi non sono pseudocodice illustrativo, sono la forma normativa.

### 4.1 La domanda di progettazione

A ogni turno di conversazione il modello deve comunicare al sistema come cambia l'interrogazione. Esistono due strade:

**Strada A — il modello riemette lo stato completo.** A ogni turno produce l'intera interrogazione risultante.
**Strada B — il modello emette solo il cambiamento.** Produce le operazioni da applicare allo stato corrente.

La scelta è la decisione più consequenziale dell'intero contratto.

### 4.2 Confronto

| Dimensione | A — stato completo | B — operazioni |
|---|---|---|
| Dimensione dell'output | Cresce con la complessità dell'interrogazione | Costante, proporzionale al cambiamento |
| Costo per turno | Crescente | Stabile |
| Rischio di deriva | **Alto**: riemettendo tutto, il modello può alterare o omettere parti che l'utente non ha toccato | **Nullo per costruzione**: ciò che non è nominato non può essere modificato |
| Superficie non deterministica | L'intera interrogazione, a ogni turno | Il solo cambiamento |
| Annullamento | Richiede una storia esterna degli stati | Naturale: si annulla l'ultima operazione |
| Complessità del sistema | Bassa: nessun merge | Media: serve una semantica di applicazione |
| Validazione | Sullo stato risultante | Sull'operazione **e** sullo stato risultante |

### 4.3 Decisione

> **Adottiamo la strada B.** Il modello emette **operazioni**. Lo **Stato di Interrogazione** è prodotto deterministicamente applicando quelle operazioni allo stato corrente.

La ragione decisiva è la terza riga della tabella, ed è una questione di correttezza, non di efficienza.

Nella strada A, l'utente che dice *"ordina per città"* riceve dal modello un'interrogazione completamente riemessa. Se in quella riemissione un filtro impostato cinque turni prima viene omesso o alterato — evento raro ma non trascurabile — l'utente vede un risultato diverso da quello atteso, per una ragione che non ha nulla a che vedere con ciò che ha chiesto. È esattamente la forma più insidiosa del rischio **R1**: un fraintendimento plausibile che l'utente non può ricondurre alla propria richiesta.

Nella strada B quell'evento è **impossibile**: l'operazione `add_order` non ha modo di toccare i filtri. Lo spazio di ciò che il modello può sbagliare coincide con lo spazio di ciò che l'utente ha appena chiesto.

È l'applicazione più forte del criterio **C3**: non un controllo che verifica che lo stato precedente non sia stato alterato, ma una grammatica in cui l'alterazione non è esprimibile.

**Conseguenza sul primo turno.** Non esiste un caso speciale: la prima richiesta è una sequenza di operazioni applicata allo stato vuoto. Un solo meccanismo governa apertura e raffinamento della conversazione.

### 4.4 La Busta di Interpretazione

L'output del modello non è direttamente una lista di operazioni: è una **busta** che dichiara innanzitutto *che tipo di risposta* il modello sta dando. Non capire è un esito legittimo del contratto, non un errore di formato.

```json
{
  "dsl_version": "1.0",
  "outcome": "operations",
  "confidence": 0.91,
  "operations": [ "…" ]
}
```

*(`operations` è qui abbreviato; la sua forma completa è in §17.)*

Gli esiti ammessi sono quattro e mutuamente esclusivi:

| `outcome` | Significato | Campo associato |
|---|---|---|
| `operations` | Il modello ha compreso e propone modifiche allo stato | `operations` |
| `clarification` | La richiesta ammette più interpretazioni plausibili | `clarification` (§11) |
| `out_of_scope` | La richiesta è comprensibile ma non esprimibile in questo profilo del contratto | `scope_note` |
| `not_understood` | Il modello non è in grado di interpretare la richiesta | — |

Rendere `clarification` e `out_of_scope` **esiti di primo livello**, e non errori, ha una conseguenza diretta sull'esperienza: il sistema che chiede o che dichiara un limite sta operando correttamente, non fallendo. È la traduzione contrattuale della regola *"quando non capisce, chiede"* (§4.5 del documento di visione).

**Regola di completezza.** Una busta con `outcome: "operations"` e lista vuota non è valida. Se non c'è nulla da cambiare, l'esito corretto è `not_understood`: uno stato invariato presentato come successo è indistinguibile, per l'utente, da una richiesta ignorata.

### 4.5 Semantica di applicazione

L'applicazione delle operazioni allo stato è deterministica e governata da quattro regole.

1. **Sequenzialità.** Le operazioni si applicano nell'ordine in cui compaiono. L'ordine è significativo e non viene normalizzato in questa fase.
2. **Atomicità.** O tutte le operazioni della busta si applicano, o nessuna. Uno stato parzialmente modificato non è mai osservabile.
3. **Totalità della validazione preventiva.** La validazione (§12) precede integralmente l'applicazione. Nessuna operazione viene applicata per poi essere annullata.
4. **Canonicalizzazione finale.** Lo stato risultante viene portato in forma canonica (§14) una sola volta, al termine della sequenza.

**Coerenza fra operazioni della stessa busta.** Le operazioni di una busta descrivono un'unica intenzione dell'utente e devono comporsi. Una busta che imposti due volte lo stesso elemento con valori diversi (`set_limit 5` seguito da `set_limit 10`) è respinta in validazione: non è un conflitto da risolvere con una regola di precedenza, è il segnale di un'interpretazione incoerente, e trattarlo come tale evita di consolidare nel sistema una regola arbitraria che maschera un difetto del modello.

### 4.6 Riepilogo degli artefatti

| Artefatto | Prodotto da | Natura | Persistito | Contenuto |
|---|---|---|---|---|
| **Busta di Interpretazione** | Modello | Probabilistica | Sì, per tracciabilità e corpus | Esito, operazioni, confidenza, provenienza |
| **Stato di Interrogazione** | Sistema (applicazione) | Deterministica | **Sì**, è l'oggetto salvabile e condivisibile | Interrogazione completa, in termini semantici |
| **Piano di Esecuzione** | Sistema (risoluzione) | Deterministica | **No**, mai | Binding tecnici verso Odoo |

I primi due costituiscono il DSL. Il terzo è fuori ambito: contrattualizzarlo legherebbe il prodotto ai dettagli interni di Odoo, esattamente ciò che la funzione di disaccoppiamento (§2.1) esiste per evitare.

---

## 5. Anatomia dello Stato di Interrogazione

### 5.1 Esempio completo

Lo stato risultante da: *"gli ultimi 5 ordini confermati di questo mese, con cliente e importo, raggruppati per venditore"*.

```json
{
  "dsl_version": "1.0",
  "target": {
    "ref": "ordini_vendita",
    "origin": "user"
  },
  "filter": {
    "connective": "all",
    "conditions": [
      {
        "id": "c1",
        "ref": "ordini_vendita.stato",
        "predicate": "is_one_of",
        "value": { "kind": "enum", "items": ["confermato"] },
        "origin": "user",
        "provenance": { "text": "confermati" },
        "confidence": 0.97
      },
      {
        "id": "c2",
        "ref": "ordini_vendita.data_ordine",
        "predicate": "within",
        "value": { "kind": "temporal", "expression": "current_month" },
        "origin": "user",
        "provenance": { "text": "di questo mese" },
        "confidence": 0.94
      }
    ]
  },
  "fields": [
    { "ref": "ordini_vendita.cliente", "origin": "user" },
    { "ref": "ordini_vendita.importo_totale", "origin": "user" }
  ],
  "group_by": [
    { "ref": "ordini_vendita.venditore", "origin": "user" }
  ],
  "order_by": [
    { "ref": "ordini_vendita.data_ordine", "direction": "desc",
      "origin": "inferred", "rule": "latest_implies_desc_by_date" }
  ],
  "limit": { "value": 5, "origin": "user" },
  "presentation": {
    "view": "list",
    "origin": "inferred",
    "rule": "grouping_without_measure_implies_list"
  }
}
```

Tre osservazioni sull'esempio, ciascuna sviluppata più avanti:

- **nessun nome tecnico Odoo compare nello stato.** `ordini_vendita.venditore` è un identificativo emesso dal Dizionario Semantico, non il nome di un campo (§7.2);
- **`current_month` resta simbolico.** Lo stato non contiene date assolute (§9.2);
- **`order_by` e `presentation` hanno `origin: "inferred"`** e dichiarano la regola che li ha prodotti. L'utente non li ha chiesti: il sistema li ha derivati, e lo dice (§10.2).

### 5.2 Le sezioni dello stato

| Sezione | Obbligatoria | Contenuto | Riferimento |
|---|---|---|---|
| `dsl_version` | Sì | Versione del contratto cui lo stato è conforme | §15 |
| `target` | Sì | L'entità interrogata | §5.3 |
| `filter` | No | Albero delle condizioni | §5.4 |
| `fields` | No | Attributi da visualizzare | §5.5 |
| `group_by` | No | Raggruppamenti, con granularità per le date | §5.6 |
| `measures` | No | Aggregazioni per Pivot e Grafico | §5.6 |
| `order_by` | No | Ordinamento | §5.7 |
| `limit` | **Sì** | Numero massimo di record | §5.8 |
| `presentation` | Sì | Tipo di vista | §5.9 |

Ogni sezione assente ha una semantica dichiarata: `filter` assente significa nessuna condizione, non condizione indefinita. Il contratto non ammette valori nulli con significato ambiguo.

### 5.3 `target` — l'entità

Ogni stato ha esattamente un'entità. Non esistono interrogazioni su più entità: una richiesta come *"clienti e ordini"* produce un chiarimento, non un contratto multi-entità.

**Motivazione.** L'entità multipla trascina con sé la necessità di esprimere relazioni fra entità, condizioni di correlazione e strategie di composizione: è la porta d'ingresso verso un linguaggio di query (§2.2). L'accesso ai dati collegati avviene invece attraverso gli attributi di relazione dell'entità principale (§7.3), che coprono la quasi totalità delle richieste reali senza ampliare la grammatica.

### 5.4 `filter` — l'albero delle condizioni

Il filtro è un albero con connettivi chiusi `all`, `any`, `not` e **profondità massima 3**.

**Perché un albero e non una lista.** Una lista di condizioni in congiunzione non esprime richieste ordinarie come *"clienti di Milano o di Roma"*. Escluderle significherebbe rendere il prodotto inutilizzabile su una classe frequente di domande.

**Perché una profondità limitata.** Un albero senza limite è una struttura ricorsiva arbitraria: viola il criterio **C4**, rende imprevedibile il costo di esecuzione e produce interpretazioni che nessun utente può verificare a colpo d'occhio, vanificando il principio P3. Il limite di 3 livelli copre le richieste esprimibili a voce da una persona; oltre quella soglia, la strada corretta è il chiarimento.

Ogni condizione porta con sé: identificativo stabile, riferimento semantico, predicato, valore, origine, provenienza e confidenza. L'**identificativo stabile** non è un dettaglio: è ciò che consente all'utente di rimuovere una singola condizione dall'interpretazione senza riformulare l'intera frase (§10.3 del documento di visione), e al modello di riferirsi a una condizione esistente per sostituirla.

### 5.5 `fields` — gli attributi visualizzati

Lista ordinata di riferimenti semantici. L'ordine è quello di presentazione.

`fields` assente non significa "nessun campo": significa che l'utente non si è espresso e valgono i campi predefiniti dell'entità, dichiarati nel Dizionario Semantico. La distinzione fra *assente* e *vuoto* è normativa: una lista vuota esplicita non è valida.

### 5.6 `group_by` e `measures` — l'organizzazione dei dati

`group_by` è una lista ordinata, con **massimo 3 livelli**, in cui ogni voce può dichiarare una `granularity` per gli attributi temporali (`day`, `week`, `month`, `quarter`, `year`).

**Perché la granularità è esplicita.** *"Raggruppa per data"* è ambiguo: per giorno o per mese? Renderla parte del contratto costringe la scelta a essere visibile nell'interpretazione e correggibile dall'utente, invece di restare un'assunzione implicita del motore.

`measures` compare solo con viste Pivot e Grafico: elenca gli attributi aggregati e la funzione applicata (§8.5). Uno stato con `measures` e vista Lista non è valido: è un'incoerenza semantica, non una combinazione da tollerare.

### 5.7 `order_by` — l'ordinamento

Lista ordinata di riferimenti con direzione. Frequentemente ha `origin: "inferred"`: *"gli ultimi cinque ordini"* implica un ordinamento decrescente per data che l'utente non ha nominato ma che è indispensabile per dare significato a *"ultimi"*.

Questo è il caso esemplare per cui la provenienza esiste. Il sistema ha aggiunto qualcosa di non richiesto; senza dichiararlo, l'utente non avrebbe modo di sapere rispetto a quale criterio sono stati scelti quei cinque record.

### 5.8 `limit` — il numero di record

**Obbligatorio e sempre presente.** Se l'utente non lo indica, vale il valore predefinito con `origin: "default"`.

**Motivazione.** *"Mostrami tutti i clienti"* su un'installazione con centinaia di migliaia di anagrafiche non deve tentare di recuperarle tutte. Rendere il limite obbligatorio significa che nessun percorso del contratto può produrre un'interrogazione non limitata: è, di nuovo, il criterio C3 preferito a un controllo di sicurezza applicato a valle.

Il valore predefinito è dichiarato per installazione. Il contratto ammette un limite esplicito superiore al predefinito entro un massimo assoluto configurato: l'utente può chiedere di più, non può chiedere l'illimitato.

### 5.9 `presentation` — il tipo di vista

Un valore da un insieme chiuso: `list`, `kanban`, `calendar`, `pivot`, `graph`, `form`.

Quando l'utente lo indica, `origin: "user"`. Quando non lo indica, è **derivato da regole deterministiche** (§6.7) e l'origine dichiara la regola applicata. Chiedere al modello di scegliere la vista violerebbe il criterio di minimalità **C2/P4**: è una decisione derivabile dalla forma dello stato, non un'interpretazione del linguaggio.

### 5.10 Cosa lo stato non contiene

Elenco normativo, ciascuna esclusione con la propria ragione.

| Assente | Perché |
|---|---|
| Nomi di modelli e campi Odoo | Criterio C2; e la persistenza di binding tecnici romperebbe V6 (§1.4) |
| Date assolute risolte | `current_month` deve significare il mese corrente anche fra sei mesi (§9.2) |
| Identificativi di record risolti | La risoluzione referenziale è deterministica e ripetuta a ogni esecuzione (§11.3) |
| Momento di riferimento dell'esecuzione | Fornito dall'esecuzione, non congelato nello stato (§9.2) |
| Identità dell'utente | I permessi si applicano in fase di risoluzione, non sono parte dell'interrogazione |
| Risultati o conteggi | Lo stato descrive una domanda, non una risposta |
| Contenuto dei record | Assunzione A6 e vincolo V7 |
| Testo della conversazione | Solo i frammenti di provenienza, non i messaggi (§10.4) |

L'ultima riga merita attenzione: **lo stato non è una trascrizione della conversazione**. È ciò che rende possibile riprendere un'interrogazione da un canale diverso da quello di origine, condividerla con un collega che non ha visto la chat, e ottenere lo stesso risultato.

---

## 6. Il Vocabolario delle Operazioni

### 6.1 Principio di composizione

Le operazioni sono l'unico modo in cui lo stato può cambiare. Il vocabolario è **chiuso** (criterio C1) e, nella versione 1.0, contiene **diciotto operazioni** raggruppate in cinque famiglie.

Ogni operazione porta con sé la propria provenienza e confidenza, che vengono trasferite agli elementi di stato che produce.

### 6.2 Famiglia 1 — Entità

| Operazione | Parametri | Semantica |
|---|---|---|
| `set_target` | `ref` | Imposta l'entità interrogata |

**Regola di ripartenza.** `set_target` con un riferimento diverso da quello corrente **azzera** filtri, campi, raggruppamenti, misure e ordinamenti, e riporta limite e vista ai valori predefiniti.

*Motivazione.* Un cambio di entità rende privi di significato tutti i riferimenti costruiti sulla precedente. Tentare di trasportarli — mappando *"attivi"* dai clienti agli ordini — sarebbe un'inferenza silenziosa sul significato: precisamente il tipo di comportamento che il rischio R1 impone di evitare. Se l'utente vuole trasportare una condizione, la esprime di nuovo; il costo è una frase, il beneficio è che il sistema non indovina mai.

### 6.3 Famiglia 2 — Condizioni

| Operazione | Parametri | Semantica |
|---|---|---|
| `add_condition` | `condition`, `combine` | Aggiunge una condizione, combinandola con `all` (predefinito) o `any` |
| `replace_condition` | `id`, `condition` | Sostituisce una condizione esistente conservandone la posizione |
| `remove_condition` | `id` **oppure** `ref` | Rimuove per identificativo o tutte quelle su un attributo |
| `clear_filter` | — | Rimuove ogni condizione |

**Perché `replace_condition` esiste come operazione autonoma.** *"Anzi, di marzo"* dopo *"gli ordini di febbraio"* non è la rimozione di una condizione seguita dall'aggiunta di un'altra: è la correzione di una condizione esistente. Distinguere i due casi conserva l'identificativo, e quindi conserva l'ancoraggio dell'interpretazione mostrata all'utente: l'elemento non scompare e riappare, cambia valore. È una differenza di esperienza percepibile, ottenuta a costo di una sola voce di vocabolario.

**Perché `remove_condition` accetta anche `ref`.** L'utente dice *"togli il filtro sulla data"*, non *"rimuovi la condizione c2"*. Consentire la rimozione per attributo evita di chiedere al modello di ricordare identificativi, che è una richiesta di memoria esatta — la classe di compito in cui i modelli sbagliano di più.

### 6.4 Famiglia 3 — Presentazione

| Operazione | Parametri | Semantica |
|---|---|---|
| `add_field` | `ref`, `position` | Aggiunge un attributo alla visualizzazione |
| `remove_field` | `ref` | Rimuove un attributo |
| `set_fields` | `refs[]` | Sostituisce l'intero insieme degli attributi |
| `clear_fields` | — | Ripristina gli attributi predefiniti dell'entità |
| `set_view` | `view` | Imposta esplicitamente il tipo di vista |

**La distinzione fra `add_field` e `set_fields` è semantica, non stilistica.**
*"Mostrami anche il telefono"* è `add_field`. *"Fammi vedere solamente Nome, Email e Telefono"* è `set_fields`. La parola *"solamente"* cambia l'intenzione in modo sostanziale, e il contratto deve poter distinguere i due casi: se esistesse solo `add_field`, l'esclusività sarebbe inesprimibile e il sistema aggiungerebbe colonne a una richiesta che ne chiedeva la restrizione.

### 6.5 Famiglia 4 — Organizzazione

| Operazione | Parametri | Semantica |
|---|---|---|
| `add_group` | `ref`, `granularity` | Aggiunge un livello di raggruppamento |
| `remove_group` | `ref` | Rimuove un livello |
| `clear_groups` | — | Rimuove ogni raggruppamento |
| `set_order` | `ref`, `direction` | Sostituisce l'ordinamento |
| `add_order` | `ref`, `direction` | Aggiunge un criterio subordinato |
| `clear_order` | — | Rimuove l'ordinamento esplicito |
| `add_measure` | `ref`, `function` | Aggiunge una misura aggregata |
| `remove_measure` | `ref` | Rimuove una misura |
| `set_limit` | `value` | Imposta il numero massimo di record |

**`set_order` è il comportamento predefinito, `add_order` l'eccezione.** *"Ordina per città"* sostituisce l'ordinamento precedente: è ciò che una persona intende. L'ordinamento multiplo esiste ma richiede un'espressione esplicita (*"e poi per nome"*).

### 6.6 Famiglia 5 — Sessione e navigazione

| Operazione | Parametri | Semantica |
|---|---|---|
| `reset` | — | Azzera lo stato: nuova interrogazione |
| `revert_last` | — | Annulla l'ultima busta applicata |
| `open_record` | `selector` | Apre un singolo record in vista form |

**`revert_last` è un'operazione, non un comando dell'interfaccia.** *"No, torna indietro"* è un'intenzione espressa in linguaggio naturale e deve poter essere interpretata come tutte le altre. Il modello la riconosce; il sistema la esegue sulla storia degli stati, che possiede.

**`open_record` non modifica lo stato.** È l'unica operazione con esito di navigazione anziché di modifica: produce l'apertura di un record e lascia intatta l'interrogazione, cosicché l'utente possa tornarvi. Il `selector` appartiene a un insieme chiuso:

```json
{ "by": "position", "value": 1 }
{ "by": "attribute", "ref": "ordini_vendita.cliente", "value": { "kind": "text", "text": "Rossi" } }
```

Nessun'altra forma di selezione è ammessa. In particolare non esiste selezione per identificativo tecnico: l'utente non conosce gli identificativi e il modello non deve inventarli.

**Nota sulla Fase 3.** Le azioni sui record previste dalla Fase 3 della roadmap non appartengono a questo vocabolario e non vi apparterranno: richiederanno una famiglia distinta, con semantica di conferma esplicita. `open_record` resta in sola lettura — apre una vista, non attiva nulla.

### 6.7 Regole di derivazione della vista

Quando `set_view` non è presente, il tipo di vista è derivato dallo stato risultante applicando, **nell'ordine**, la prima regola che corrisponde.

| # | Condizione sullo stato | Vista | Identificativo della regola |
|---|---|---|---|
| 1 | `measures` presenti e ≥ 2 `group_by` | `pivot` | `measures_multi_group_implies_pivot` |
| 2 | `measures` presenti e 1 `group_by` | `graph` | `measures_single_group_implies_graph` |
| 3 | `measures` presenti e nessun `group_by` | `list` | `measures_without_group_implies_list` |
| 4 | `group_by` presenti senza `measures` | `list` | `grouping_without_measure_implies_list` |
| 5 | Nessuna delle precedenti | `list` | `default_list` |

Tre proprietà di queste regole sono normative.

**Sono deterministiche e versionate.** Non sono un'euristica del motore: sono parte del contratto. Una loro modifica è una modifica del contratto e segue le regole di versionamento di §15, perché cambia il risultato di stati già salvati.

**Dichiarano sempre l'identificativo della regola applicata** nel campo `rule` dello stato. L'interpretazione può quindi comunicare all'utente *perché* sta vedendo un grafico, e l'utente può contraddire la scelta con una frase.

**La vista Calendario non è mai inferita.** Un attributo temporale non implica che l'utente voglia un calendario: implica solo che il dato ha una data. Passare a una rappresentazione a calendario cambia radicalmente la lettura del risultato, e farlo senza richiesta esplicita produce lo spiazzamento che erode la fiducia. Il calendario si ottiene chiedendolo.

### 6.8 Cosa il vocabolario deliberatamente non contiene

| Assente | Motivazione |
|---|---|
| Qualunque verbo di scrittura | Criterio C3: la sola lettura è una proprietà della grammatica, non un permesso (§13.1) |
| `execute_action`, `run_workflow` | Fase 3 e successive; richiedono semantica di conferma |
| `set_raw_domain`, `set_expression` | Criterio C4: reintrodurrebbe la generazione di codice |
| `set_state` (imposizione dello stato completo) | Riaprirebbe la strada A di §4.2 e la sua superficie di deriva |
| `export`, `send`, `schedule` | Effetti verso l'esterno: non sono interpretazione di un'interrogazione |
| Operazioni condizionali o cicliche | Il DSL non è un linguaggio di programmazione (§2.2) |

---

## 7. Riferimenti Semantici e Risoluzione

### 7.1 Il problema

Il modello deve indicare *su cosa* filtrare, ordinare, raggruppare. Non può usare nomi tecnici Odoo: non conosce lo schema di questa installazione, che dipende da moduli, personalizzazioni e configurazioni del singolo cliente. Chiedergli un nome tecnico significa chiedergli di inventarlo.

Questo è, con ampio margine, il modo in cui i sistemi di questo tipo falliscono più spesso: un nome di campo plausibile ma inesistente attraversa la validazione sintattica e fallisce tardi, con un messaggio che nessun utente può comprendere.

### 7.2 La soluzione: catalogo chiuso e per utente

Il modello riceve, insieme alla richiesta, un **catalogo di riferimenti semantici**: l'elenco delle entità e degli attributi che può nominare, con le rispettive denominazioni nel linguaggio dell'organizzazione. Il modello **sceglie da questo catalogo**; non produce identificativi liberi.

Il catalogo contiene esclusivamente **metadati di struttura** — identificativi, denominazioni, tipi, sinonimi, valori ammessi per gli attributi enumerati. Nessun contenuto di record, in conformità all'assunzione **A6** e al vincolo **V7**.

**Il catalogo è costruito per il singolo utente.**

Questa è la proprietà più importante della sezione. Un attributo che l'utente non è autorizzato a leggere **non compare nel suo catalogo**. Ne discendono tre conseguenze:

- il modello non può nominare ciò che l'utente non può vedere: la restrizione opera a livello di vocabolario, prima di qualunque controllo;
- il vincolo **V2** non dipende da un filtro applicato ai risultati, ma dalla forma dello spazio delle interpretazioni possibili — di nuovo il criterio **C3**;
- non si verifica trasferimento di informazione per negazione: l'utente non riceve un rifiuto che gli rivelerebbe l'esistenza di un attributo riservato, perché il sistema non ha mai considerato quell'attributo interpretabile.

Il controllo di autorizzazione in fase di risoluzione (§7.4) resta comunque presente: la difesa a livello di vocabolario è la prima, non l'unica.

### 7.3 Forma dei riferimenti

```
ordini_vendita                              entità
ordini_vendita.stato                        attributo diretto
ordini_vendita.cliente.citta                attributo tramite relazione (1 salto)
ordini_vendita.cliente.paese.codice         attributo tramite relazione (2 salti)
```

**Profondità massima: 2 salti di relazione.**

*Motivazione.* La profondità illimitata produce tre problemi simultanei: un costo di esecuzione che cresce in modo non prevedibile dalla forma del riferimento; un catalogo che esplode combinatoriamente e diventa ingestibile per il modello; interpretazioni che l'utente non può verificare a colpo d'occhio, vanificando P3. Due salti coprono la quasi totalità delle richieste esprimibili in una frase. Oltre, la strada corretta è arricchire il Dizionario Semantico con un riferimento dedicato — *"paese del cliente"* come attributo di primo livello — non allungare il percorso.

Questa è una scelta di prodotto ricorrente: **preferire l'arricchimento del dizionario all'ampliamento della grammatica.** Il dizionario è dati, versionabile e correggibile per cliente; la grammatica è contratto, e ogni sua estensione vale per tutti e per sempre.

### 7.4 Risoluzione

La risoluzione traduce i riferimenti semantici in binding tecnici. Avviene **a ogni esecuzione**, mai una volta sola, ed è interamente deterministica.

```
riferimento semantico          ordini_vendita.cliente.citta
        │
        ▼  Dizionario Semantico dell'installazione
binding tecnico                 (modello, percorso, tipo)
        │
        ▼  controllo di autorizzazione con l'identità dell'utente
elemento del Piano di Esecuzione
```

Quattro esiti possibili, tutti definiti:

| Esito | Trattamento |
|---|---|
| **Risolto e autorizzato** | Prosegue verso il Piano di Esecuzione |
| **Non risolto** — il riferimento non esiste nel dizionario | Errore di validazione livello 3 (§12.4): la busta è respinta |
| **Risolto ma non autorizzato** | Trattato come non risolto; nessuna informazione sull'esistenza dell'attributo raggiunge l'utente |
| **Risolto ma non più valido** — modulo disinstallato, campo rimosso | Errore diagnosticabile: lo stato è valido, l'installazione è cambiata (§15.5) |

L'ultima riga è la ragione per cui la ri-risoluzione a ogni esecuzione è preferibile al binding persistito. Un'interrogazione salvata non diventa silenziosamente sbagliata quando l'installazione evolve: diventa esplicitamente non risolvibile, e il Dizionario Semantico può assorbire il cambiamento in un punto solo, a beneficio di tutte le interrogazioni salvate che vi facevano riferimento.

---

## 8. Predicati e Valori

### 8.1 Vocabolario dei predicati

I predicati sono un insieme chiuso, ammesso **per tipo di attributo**. Un predicato applicato a un tipo che non lo prevede è un errore di validazione, non un'estensione tollerata.

| Tipo | Predicati ammessi |
|---|---|
| **Testo** | `equals`, `contains`, `starts_with`, `is_one_of`, `is_empty`, `is_not_empty` |
| **Numero** | `equals`, `greater_than`, `greater_or_equal`, `less_than`, `less_or_equal`, `between`, `approximately` |
| **Data / Data-ora** | `on`, `before`, `after`, `between`, `within` |
| **Enumerato** | `is_one_of`, `is_not_one_of` |
| **Booleano** | `is_true`, `is_false` |
| **Relazione** | `is_one_of`, `is_set`, `is_not_set` |

**Perché la restrizione per tipo.** Ammettere `contains` su un numero o `greater_than` su un enumerato significherebbe delegare al motore di esecuzione la decisione su cosa farne. Vincolarli nel contratto sposta l'errore dal momento dell'esecuzione — dove produce un risultato inatteso o un fallimento oscuro — al momento della validazione, dove produce una domanda comprensibile all'utente.

**Assenza deliberata di `not_equals`.** La negazione si esprime con il connettivo `not` a livello di albero. Ammettere entrambe le forme produrrebbe due rappresentazioni della stessa condizione e violerebbe il criterio **C8**: la forma canonica non sarebbe più unica, e il confronto con l'interpretazione attesa nel corpus diventerebbe ambiguo. La sola eccezione è `is_not_one_of` sugli enumerati, mantenuta perché *"tutti tranne bozza e annullato"* è una richiesta frequente la cui resa con `not` sarebbe verbosa e meno leggibile nell'interpretazione mostrata all'utente.

### 8.2 Tipi di valore

```json
{ "kind": "text",      "text": "Milano" }
{ "kind": "number",    "value": 100000 }
{ "kind": "number",    "value": 100000, "resolver": "approx_relative" }
{ "kind": "range",     "from": 1000, "to": 5000 }
{ "kind": "enum",      "items": ["confermato", "fatturato"] }
{ "kind": "boolean",   "value": true }
{ "kind": "temporal",  "expression": "current_month" }
{ "kind": "reference", "text": "Rossi" }
```

### 8.3 Il tipo `reference` e il confine con i dati

Il tipo `reference` merita una nota, perché tocca l'assunzione A6.

Quando l'utente scrive *"gli ordini di Rossi"*, il modello emette `{ "kind": "reference", "text": "Rossi" }`. Non emette un identificativo di record: **non lo conosce e non deve conoscerlo**, perché conoscerlo richiederebbe di avergli mostrato dei dati.

La traduzione da *"Rossi"* al record corrispondente è **risoluzione referenziale deterministica** (§11.3), eseguita dal backend con i permessi dell'utente al momento dell'esecuzione.

Il letterale `"Rossi"` proviene dalla frase dell'utente, non dai record: la sua presenza nel contratto non viola A6. La distinzione è netta e va mantenuta: **il contratto può contenere ciò che l'utente ha scritto, mai ciò che il sistema ha letto dal database.**

### 8.4 Perché nessun domain grezzo

L'alternativa più immediata sarebbe consentire al modello di produrre direttamente un domain Odoo. È respinta per quattro ragioni cumulative.

- **Non validabile in modo significativo.** Un domain è un'espressione arbitraria: se ne può verificare la sintassi, non la sensatezza. Il confine di validazione (§2.1) diventerebbe nominale.
- **Aggira il modello di sicurezza.** Un domain può percorrere relazioni non previste e raggiungere dati che il catalogo per utente escludeva. Violerebbe V2 e V3.
- **Lega il contratto a Odoo.** Il DSL cesserebbe di essere una superficie di disaccoppiamento e diventerebbe un dialetto della piattaforma sottostante, con la sua stessa velocità di evoluzione.
- **Rende l'interpretazione non presentabile.** Un domain non è traducibile in modo affidabile nel linguaggio dell'utente. Senza interpretazione comprensibile, il principio P3 decade e con esso la difesa contro R1.

Un vocabolario chiuso di predicati costa espressività su casi rari. È il prezzo dichiarato del criterio **C1**, e §3.9 spiega perché lo accettiamo.

### 8.5 Funzioni di aggregazione

Insieme chiuso: `sum`, `avg`, `min`, `max`, `count`, `count_distinct`.

Ogni funzione dichiara i tipi su cui è ammessa: `sum` e `avg` solo su attributi numerici; `min` e `max` su numerici e temporali; `count` non richiede attributo. Un'aggregazione su un attributo che non la ammette è un errore di validazione di livello 4 (§12.5).

**Nessuna espressione calcolata.** Il contratto non ammette misure derivate come *"margine = ricavo − costo"*. Una metrica di questo tipo appartiene al Dizionario Semantico, dove è definita una volta, verificata da chi conosce le convenzioni contabili dell'azienda, e riferita per nome. Consentirne la costruzione al modello significherebbe permettergli di **definire una metrica aziendale**, cioè di prendere una decisione di business: esattamente ciò che §2.5 del documento di visione esclude.

---

## 9. Espressioni Temporali e Vaghezza

### 9.1 Il problema comune

*"Questo mese"*, *"gli ordini recenti"*, *"circa centomila chilometri"*, *"i clienti importanti"* condividono la stessa proprietà: non hanno un significato univoco finché qualcuno non lo stabilisce.

La domanda di progettazione è **chi** lo stabilisce. Se è il modello, il sistema diventa imprevedibile: la stessa frase può produrre risultati diversi in momenti diversi, in violazione di P1 e della coerenza su cui si costruisce la fiducia (§10.6 del documento di visione).

> **Regola generale.** Il modello **riconosce** la vaghezza e la **nomina**. Non la risolve mai.

### 9.2 Espressioni temporali

Il valore temporale contiene un'espressione simbolica appartenente a un vocabolario chiuso:

| Categoria | Espressioni |
|---|---|
| Puntuali | `today`, `yesterday`, `tomorrow` |
| Periodo corrente | `current_week`, `current_month`, `current_quarter`, `current_year` |
| Periodo precedente | `previous_week`, `previous_month`, `previous_quarter`, `previous_year` |
| Relative parametriche | `last_n_days(n)`, `last_n_weeks(n)`, `last_n_months(n)`, `next_n_days(n)` |
| Assolute | `absolute(date)`, `absolute_range(from, to)` |

**Le date assolute non compaiono mai nello stato, salvo che l'utente le abbia dette.** *"Questo mese"* resta `current_month`. Solo *"dal 1 marzo al 15 aprile"* produce `absolute_range`.

**Motivazione.** È la condizione perché le interrogazioni salvate abbiano senso nel tempo. Un'interrogazione *"fatturato di questo mese"* salvata a luglio deve mostrare agosto in agosto. Se il modello risolvesse l'espressione in date assolute, ogni interrogazione salvata sarebbe una fotografia del momento in cui è stata creata, e l'intera Fase 4 della roadmap — report ricorrenti generati da un'intenzione espressa una sola volta — sarebbe irrealizzabile.

**La risoluzione avviene all'esecuzione** e considera tre parametri dell'installazione: il fuso orario dell'utente, il primo giorno della settimana, e **l'inizio dell'esercizio fiscale**. Quest'ultimo è tutt'altro che marginale: in un'azienda con esercizio non solare, *"quest'anno"* significa l'anno fiscale, e restituire l'anno solare produrrebbe un numero sbagliato di aspetto perfettamente credibile — la forma canonica del rischio R1 applicata ai dati aggregati.

Ne discende una regola per la valutazione: il corpus deve essere eseguito con un **momento di riferimento fissato**, altrimenti l'esito atteso di una richiesta contenente `current_month` cambierebbe con il calendario e i confronti fra rilasci sarebbero privi di significato.

### 9.3 Vaghezza numerica e qualitativa

Il valore porta un `resolver`: il nome di una regola definita nel Dizionario Semantico.

```json
{ "kind": "number", "value": 100000, "resolver": "approx_relative" }
```

Il modello dichiara *che* il valore è approssimato e *quale* regola si applica. Non decide la tolleranza.

| Espressione | Risolutore | Regola dichiarata (predefinita, ridefinibile per cliente) |
|---|---|---|
| *"circa centomila"* | `approx_relative` | ±10% del valore |
| *"gli ordini recenti"* | `recent_orders` | Ultimi 30 giorni |
| *"i clienti importanti"* | — | **Nessun risolutore predefinito** |

Tre proprietà rendono questa impostazione conforme ai principi.

**La regola è visibile.** L'interpretazione mostra *"chilometraggio tra 90.000 e 110.000"*, non *"circa 100.000"*. L'utente vede il numero effettivamente applicato e può contraddirlo (*"no, esattamente centomila"*).

**La regola è stabile.** La stessa frase produce sempre la stessa interpretazione. La coerenza percepita è, secondo §10.6 del documento di visione, il fondamento della fiducia — più dell'accuratezza stessa.

**L'assenza di risolutore non è colmata dal modello.** *"I clienti importanti"* non ha un significato oggettivo: dipende da una convenzione aziendale. In assenza di un risolutore definito, l'esito corretto è `clarification`, e la risposta dell'utente diventa candidata all'inserimento nel Dizionario Semantico. È il meccanismo con cui il dizionario cresce con l'uso, previsto dalla Fase 2 della roadmap.

**Un risolutore inventato dal modello sarebbe un difetto, non una funzionalità.** Produrrebbe un sistema che risponde con sicurezza a domande la cui risposta dipende da una convenzione che nessuno ha stabilito.

---

## 10. Provenienza, Origine e Confidenza

### 10.1 Il ruolo di questi metadati

Sono il supporto tecnico dell'interpretazione ispezionabile (P3) e la principale difesa contro il rischio R1. Non sono informazione diagnostica: sono parte del contratto, e senza di essi il principio P3 non è realizzabile.

### 10.2 `origin` — chi ha deciso

Insieme chiuso di tre valori, obbligatorio su ogni elemento dello stato.

| Valore | Significato | Trattamento nell'interpretazione |
|---|---|---|
| `user` | L'utente lo ha espresso | Mostrato come richiesta dell'utente |
| `inferred` | Il sistema lo ha derivato, con la regola dichiarata in `rule` | **Mostrato in modo distinguibile**: è ciò che l'utente non ha chiesto |
| `default` | Valore predefinito dell'installazione | Mostrato in forma discreta, con possibilità di ispezione |

La distinzione fra `user` e `inferred` è la più importante del contratto sul versante dell'esperienza. Quando l'utente chiede *"gli ultimi cinque ordini"* e riceve cinque record, il criterio con cui sono stati scelti — l'ordinamento decrescente per data — è un'inferenza del sistema. Se non fosse dichiarata, l'utente non avrebbe modo di sapere che *"ultimi"* è stato interpretato come *"più recenti per data d'ordine"* e non, per esempio, per data di conferma.

### 10.3 `provenance` — da quali parole

Ogni elemento prodotto da un'espressione dell'utente registra il frammento di testo che lo ha generato.

```json
"provenance": { "text": "di questo mese" }
```

Rende possibile l'evidenziazione incrociata fra la frase e l'interpretazione, che è il modo più rapido per far riconoscere un fraintendimento: l'utente vede che *"di questo mese"* ha prodotto un filtro sulla data d'ordine anziché sulla data di consegna, e lo corregge in due secondi.

È inoltre il dato che rende diagnosticabili gli errori del modello: senza provenienza, un fraintendimento osservato in produzione non è riconducibile alla porzione di frase che lo ha causato, e l'analisi dei fraintendimenti prevista dalla Fase 2 sarebbe basata su congetture.

### 10.4 Cosa la provenienza non contiene

Il frammento di testo, non il messaggio. Non la conversazione, non i turni precedenti, non l'identità di chi ha scritto. Lo stato resta un oggetto portabile e condivisibile (§5.10).

### 10.5 `confidence` — e come non usarla

Ogni busta porta una confidenza complessiva; ogni operazione può portare la propria.

**Uso previsto:** superata una soglia superiore, il risultato è presentato normalmente; sotto una soglia inferiore, l'esito corretto è `clarification`; nell'intervallo intermedio, il risultato è presentato con riserva esplicita, secondo la regola *"quando è incerto, lo dichiara"* (§4.5 del documento di visione).

**Avvertenza necessaria.** La confidenza dichiarata da un modello linguistico è **debolmente calibrata**: non è una probabilità e non va trattata come tale. Un modello può dichiarare 0,95 su un'interpretazione errata, in particolare proprio nei casi di fraintendimento plausibile — dove la lettura sbagliata è, per costruzione, quella che appare più naturale.

Ne discendono tre regole d'uso:

- la confidenza è un **segnale di ordinamento**, non una misura: serve a decidere cosa chiedere per primo, non a stabilire cosa è corretto;
- le soglie sono **calibrate empiricamente sul corpus** confrontando confidenza dichiarata e correttezza effettiva, e ricalibrate a ogni cambio di modello. Non sono costanti del contratto: sono parametri di governo;
- **nessuna decisione di sicurezza dipende dalla confidenza.** Un'operazione non diventa ammissibile perché il modello si dichiara sicuro. Questa regola è oggi poco vincolante — la sola lettura non ha decisioni di sicurezza da prendere — ma va fissata ora, perché è nella Fase 5 che la tentazione di usare una confidenza elevata per saltare una conferma diventerà concreta.

---

## 11. Ambiguità e Chiarimento

### 11.1 Due classi distinte di ambiguità

La distinzione è strutturale e va mantenuta separata nel contratto, perché i due casi hanno cause, momenti e responsabili diversi.

| | **Ambiguità interpretativa** | **Ambiguità referenziale** |
|---|---|---|
| Esempio | *"gli ordini di Rossi"* — cliente o venditore? | *"gli ordini di Rossi"* — quale dei tre Rossi? |
| Origine | Il linguaggio ammette più letture | Il letterale corrisponde a più record |
| Chi la rileva | Il modello, in fase di interpretazione | Il backend, in fase di risoluzione |
| Natura | Probabilistica | **Deterministica** |
| Rappresentazione | `outcome: "clarification"` | Esito di risoluzione, fuori dal DSL |

La stessa frase può presentare entrambe. Trattarle con lo stesso meccanismo sarebbe un errore: la seconda non richiede alcun intervento del modello e va risolta senza pagarne il costo né subirne l'incertezza.

### 11.2 Chiarimento interpretativo

```json
{
  "dsl_version": "1.0",
  "outcome": "clarification",
  "confidence": 0.42,
  "clarification": {
    "question": "Rossi come cliente o come venditore?",
    "provenance": { "text": "di Rossi" },
    "options": [
      {
        "label": "Come cliente",
        "operations": [ { "op": "add_condition", "condition": {
            "ref": "ordini_vendita.cliente", "predicate": "is_one_of",
            "value": { "kind": "reference", "text": "Rossi" } } } ]
      },
      {
        "label": "Come venditore",
        "operations": [ { "op": "add_condition", "condition": {
            "ref": "ordini_vendita.venditore", "predicate": "is_one_of",
            "value": { "kind": "reference", "text": "Rossi" } } } ]
      }
    ]
  }
}
```

**Ogni opzione porta con sé le operazioni che produrrebbe.**

È una scelta di progetto con tre conseguenze rilevanti:

- **la selezione è deterministica.** L'utente sceglie e il sistema applica operazioni già validate. Non serve una seconda interpretazione, e non c'è modo che il chiarimento venga a sua volta frainteso — un'eventualità tutt'altro che teorica quando la domanda di chiarimento è già segno di un contesto difficile;
- **il costo è dimezzato.** Nessuna seconda chiamata al modello dopo la risposta dell'utente;
- **il chiarimento è misurabile.** L'opzione scelta è un dato strutturato, direttamente confrontabile con l'atteso e direttamente utilizzabile per arricchire il Dizionario Semantico. Se il 90% degli utenti di un'installazione sceglie *"come cliente"*, il dizionario può registrare la preferenza e la domanda smette di essere posta.

**Vincoli sul chiarimento:** da 2 a 4 opzioni, mutuamente esclusive, con etichette nel linguaggio dell'utente e mai contenenti nomi tecnici. Un chiarimento con una sola opzione non è valido: sarebbe una richiesta di conferma travestita.

### 11.3 Risoluzione referenziale

Avviene nel backend, in modo deterministico, con i permessi dell'utente. Tre esiti:

| Esito | Comportamento |
|---|---|
| **Corrispondenza unica** | Prosegue senza interazione |
| **Corrispondenze multiple** | Disambiguazione presentata all'utente con l'elenco dei candidati **che l'utente è autorizzato a vedere** |
| **Nessuna corrispondenza** | Comunicazione esplicita, distinta dal risultato vuoto (§9.5 del documento di visione) |

**Lo stato non viene modificato dalla risoluzione.** Continua a contenere `{ "kind": "reference", "text": "Rossi" }` anche dopo che l'utente ha scelto un candidato preciso.

Questa scelta merita attenzione perché è controintuitiva. Congelare l'identificativo del record sembrerebbe più efficiente e più preciso; sarebbe invece un errore per due ragioni: l'identificativo è un binding tecnico, che §1.4 esclude dalla persistenza; e un'interrogazione condivisa con un collega che ha permessi diversi deve risolversi secondo i permessi di **chi la esegue**, non di chi l'ha creata.

*Conseguenza operativa da governare:* la scelta dell'utente non è memorizzata nello stato, quindi va gestita a livello di sessione per non riproporre la stessa disambiguazione a ogni turno. È un requisito per il documento di architettura, non per il contratto.

### 11.4 `out_of_scope` — dichiarare il limite

```json
{
  "dsl_version": "1.0",
  "outcome": "out_of_scope",
  "scope_note": "modifica_dati"
}
```

Richiesta compresa ma non esprimibile in questo profilo del contratto: *"cambia lo stato di questo ordine"*, *"mandami questo per email"*.

`scope_note` appartiene a un insieme chiuso di categorie, non è testo libero. Serve a due scopi: permettere all'interfaccia di dare una risposta specifica e utile (*"in questa versione posso solo consultare i dati"*) anziché generica; e **misurare la domanda inespressa**. La distribuzione delle categorie `out_of_scope` è l'evidenza quantitativa su cui basare le priorità di ampliamento del contratto, in linea con §3.9: l'espressività si aggiunge quando i dati la richiedono.

---

## 12. Validazione

### 12.1 Il principio

> **Nessuna busta non valida produce esecuzione. Mai. Per nessuna ragione.**

La validazione è integrale e precede l'applicazione. Non esiste validazione parziale, non esiste applicazione ottimistica seguita da correzione, non esiste modalità permissiva per l'ambiente di sviluppo — una modalità permissiva sarebbe un percorso di codice che prima o poi raggiunge la produzione.

### 12.2 I cinque livelli

I livelli si applicano in sequenza; il primo che fallisce interrompe la catena. L'ordine non è arbitrario: procede dal controllo meno costoso al più costoso, e dal difetto più probabile al più raro.

| Livello | Verifica | Natura del difetto rilevato |
|---|---|---|
| **1 — Struttura** | Conformità allo schema, versione riconosciuta | Difetto di formato |
| **2 — Vocabolario** | Appartenenza ai vocabolari chiusi | Simbolo inventato |
| **3 — Risoluzione** | Esistenza e autorizzazione dei riferimenti | Riferimento inesistente o non permesso |
| **4 — Coerenza** | Compatibilità tipo/predicato, coerenza dello stato risultante | Combinazione priva di senso |
| **5 — Costo** | Limiti, profondità, complessità stimata | Interrogazione insostenibile |

### 12.3 Livelli 1 e 2 — struttura e vocabolario

Il livello 1 verifica la conformità della busta allo schema della versione dichiarata e il rispetto delle regole di completezza di §4.4.

Il livello 2 verifica che ogni simbolo appartenga al proprio insieme chiuso: operazioni, predicati, tipi di valore, risolutori, espressioni temporali, funzioni di aggregazione, tipi di vista, categorie `scope_note`.

**Osservazione di progetto.** I fallimenti ai livelli 1 e 2 dovrebbero essere rari, perché l'output del modello può essere vincolato a monte allo schema e ai vocabolari — è il beneficio pratico del criterio **C1**. Un tasso non trascurabile di fallimenti a questi livelli non è un problema di validazione: è il segnale che la generazione vincolata non è applicata correttamente, e va trattato come tale anziché assorbito dal ripristino di §12.7.

### 12.4 Livello 3 — risoluzione

Ogni riferimento semantico viene risolto sul Dizionario Semantico dell'installazione e verificato rispetto ai permessi dell'utente (§7.4).

È il livello che intercetta la modalità di errore più comune: il riferimento plausibile ma inesistente. Ogni fallimento a questo livello è **materiale prezioso**: indica una lacuna del Dizionario Semantico o una denominazione che gli utenti usano e il dizionario non conosce. Va registrato come candidato all'arricchimento del dizionario, non solo come errore.

### 12.5 Livello 4 — coerenza

Verifica le combinazioni prive di senso che i livelli precedenti non possono rilevare, perché ogni elemento è individualmente valido.

| Verifica | Esempio di violazione |
|---|---|
| Compatibilità predicato/tipo | `contains` su un attributo numerico |
| Compatibilità funzione/tipo | `sum` su un attributo testuale |
| Coerenza misure/vista | `measures` presenti con vista `list` |
| Compatibilità granularità | `granularity: "month"` su un attributo non temporale |
| Profondità dell'albero dei filtri | Oltre 3 livelli |
| Numero di raggruppamenti | Oltre 3 livelli |
| Coerenza interna della busta | Due `set_limit` con valori diversi (§4.5) |
| Riferimento a elementi inesistenti | `replace_condition` su un identificativo assente |

### 12.6 Livello 5 — costo

Verifica che l'interrogazione risultante sia sostenibile: limite entro il massimo assoluto configurato, profondità di attraversamento entro i 2 salti, complessità stimata entro il budget dell'installazione.

**Perché il costo è un livello di validazione e non un controllo a valle.** Un'interrogazione insostenibile non è un problema di prestazioni: è un problema di disponibilità del servizio per tutti gli altri utenti. Trattarla nel contratto, con un esito comprensibile e una proposta di restringimento, è preferibile a lasciarla partire e interromperla per scadenza del tempo massimo — che produrrebbe un errore incomprensibile dopo un'attesa lunga.

### 12.7 Trattamento dei fallimenti

Ogni fallimento produce un esito rivolto all'utente, mai un errore tecnico esposto.

| Livello | Esito verso l'utente | Registrazione |
|---|---|---|
| 1–2 | *"Non ho capito, puoi riformulare?"* | **Difetto di sistema**: da analizzare, non è colpa della richiesta |
| 3 | *"Non conosco «xxx» per gli ordini"*, con proposta di alternative dal catalogo | Candidato all'arricchimento del dizionario |
| 4 | Messaggio specifico sull'incoerenza, in linguaggio non tecnico | Difetto di sistema |
| 5 | *"La richiesta produce troppi risultati"*, con proposta di restringimento | Comportamento atteso, non difetto |

**Ripristino con un solo tentativo.** Un fallimento ai livelli 1, 2 o 4 può essere ripresentato al modello una sola volta, corredato dell'errore di validazione in forma strutturata.

Il limite di un tentativo è normativo e va motivato, perché la tentazione di alzarlo si presenterà. Un secondo e un terzo tentativo aumentano latenza e costo su una richiesta che sta già andando male; soprattutto, **mascherano un difetto sistematico**: se il modello produce regolarmente output non validi, quel dato deve comparire nelle metriche e guidare una correzione, non essere assorbito silenziosamente da un ciclo di ripetizione. Il tasso di ripristino è esso stesso un indicatore da sorvegliare.

---

## 13. Sicurezza del Contratto

### 13.1 Sola lettura per costruzione

Il vocabolario delle operazioni della versione 1.0 non contiene alcun verbo mutante. Non esiste un'operazione di scrittura che venga respinta: **non esiste un'operazione di scrittura**.

La differenza rispetto a un controllo applicativo è sostanziale, e vale la pena esplicitarla perché è la raccomandazione §18.4 del documento di visione resa operativa:

| | Controllo applicativo | Impossibilità grammaticale |
|---|---|---|
| Dove risiede | In un punto del codice | Nella forma del contratto |
| Come si aggira | Difetto, deroga, configurazione, rifattorizzazione | Non si aggira |
| Chi lo deve conoscere | Chiunque tocchi quel percorso | Nessuno |
| Cosa succede se qualcuno lo dimentica | Il vincolo decade silenziosamente | Il codice non compila la richiesta |

**Conseguenza sulla Fase 5.** Le operazioni di scrittura richiederanno una versione del contratto con una famiglia di operazioni nuova, la propria semantica di conferma obbligatoria e la propria anteprima. Non un'estensione della versione 1.0 e non un permesso: un profilo distinto, attivabile per installazione, con il proprio percorso di validazione. Fissarlo ora costa una frase; fissarlo dopo costerà una riprogettazione sotto pressione commerciale.

### 13.2 Il vocabolario come frontiera di autorizzazione

Il catalogo dei riferimenti semantici è costruito per il singolo utente (§7.2). Ciò che l'utente non può vedere non entra nello spazio delle interpretazioni possibili.

È una difesa qualitativamente diversa dal filtraggio dei risultati: agisce **prima** dell'interpretazione anziché dopo l'esecuzione, e non produce trasferimento di informazione per negazione.

### 13.3 Assenza di superfici di espressione arbitraria

Il contratto non contiene: espressioni da valutare, domain grezzi, percorsi liberi, nomi tecnici, strutture ricorsive senza limite, testo interpretato come istruzione. Ogni valore è un letterale tipizzato, ogni riferimento appartiene a un catalogo, ogni operatore appartiene a un vocabolario chiuso.

Questa proprietà rende il contratto ispezionabile e verificabile in modo esaustivo — la condizione che rende sensata la validazione di §12.

### 13.4 Iniezione tramite contenuti

Il vettore classico di questi sistemi è l'iniezione di istruzioni attraverso i dati: un record contenente testo costruito per alterare il comportamento del modello che lo legge.

**Nel profilo 1.0 questo vettore è chiuso alla radice**, perché l'assunzione **A6** esclude che il contenuto dei record raggiunga il modello. Il modello vede la frase dell'utente e i metadati di struttura; non vede i dati.

Restano due considerazioni.

**Il catalogo è un ingresso di dati.** Denominazioni e sinonimi del Dizionario Semantico raggiungono il modello. Sono contenuti curati, non contenuti utente, ma un dizionario alimentato automaticamente dall'uso (Fase 2) diventa un percorso indiretto dal linguaggio degli utenti al contesto del modello. L'arricchimento automatico del dizionario richiede quindi una validazione dei contenuti immessi. È un requisito per il documento sul Modello Semantico, segnalato qui perché nasce dal contratto.

**La Fase 6 riapre il vettore.** La comprensione documentale porta per definizione contenuti non fidati davanti al modello. Il presidio resta il contratto: qualunque cosa il modello produca dopo aver letto un documento è una busta, validata dai cinque livelli, con riferimenti limitati al catalogo dell'utente. **Un'iniezione riuscita non può produrre più di un'interrogazione valida sui dati che l'utente può già vedere.** È l'argomento più forte a favore dell'impostazione scelta, e va conservato: vale finché nessuna evoluzione consente al modello di produrre qualcosa che non sia una busta validata.

### 13.5 Tracciabilità

Busta e stato risultante sono persistiti per ogni interazione. Ne discende la ricostruibilità completa di chi ha chiesto cosa, come è stato interpretato, cosa è stato eseguito e con quale esito — il requisito di tracciabilità della Fase 2 e il presupposto di ogni verifica successiva a un incidente.

La provenienza (§10.3) aggiunge il livello che rende l'analisi produttiva: non solo *cosa* è stato interpretato male, ma **quali parole** lo hanno causato.

---

## 14. Forma Canonica ed Equivalenza

### 14.1 Perché il contratto deve definire l'uguaglianza

Il documento di visione fissa come criterio di avanzamento verso la scrittura il raggiungimento di una soglia di accuratezza misurata su un corpus. Misurare l'accuratezza significa confrontare l'interpretazione prodotta con quella attesa e decidere se coincidono.

**Se il contratto non definisce quando due interpretazioni coincidono, quel confronto non è meccanizzabile.** L'accuratezza tornerebbe a essere un giudizio umano su ogni caso: non ripetibile, non applicabile a ogni rilascio, non scalabile al volume necessario. Con essa verrebbe meno il presupposto della Fase 2 e del cancello verso la Fase 5.

La forma canonica è quindi, come anticipato in §1.5, un requisito di governo del prodotto.

### 14.2 Due forme dello stesso stato

| Forma | Uso | Contiene |
|---|---|---|
| **Forma d'esercizio** | Presentazione, modifica, persistenza | Ordine di inserimento, identificativi, provenienza, origine, confidenza |
| **Forma canonica** | Confronto, deduplicazione, memorizzazione | Solo la semantica dell'interrogazione |

La forma d'esercizio conserva l'ordine in cui l'utente ha aggiunto le condizioni, perché è l'ordine in cui l'interpretazione gli viene mostrata: riordinarlo sarebbe disorientante. La forma canonica ignora quell'ordine, perché non cambia il risultato.

### 14.3 Regole di canonicalizzazione

1. **Rimozione dei metadati.** `origin`, `provenance`, `confidence`, `rule` e gli identificativi delle condizioni sono esclusi: descrivono *come* si è arrivati all'interrogazione, non *cosa* l'interrogazione chiede.
2. **Ordinamento delle condizioni** all'interno di ogni connettivo, secondo un ordine totale definito su riferimento, predicato e valore.
3. **Ordinamento degli insiemi**: gli elementi di `is_one_of` e `enum` sono ordinati.
4. **Riduzione dei connettivi**: un connettivo con un solo figlio è sostituito dal figlio; i connettivi annidati dello stesso tipo sono appiattiti.
5. **Esplicitazione dei valori predefiniti**: limite e vista sono sempre presenti con il valore effettivo, anche quando derivati.
6. **Normalizzazione dei letterali**: normalizzazione unicode e degli spazi; il confronto testuale è insensibile a maiuscole e minuscole.
7. **Rimozione delle sezioni vuote**: una sezione priva di elementi è assente, mai presente e vuota.

**La regola 1 è la più delicata e va argomentata.** Escludendo `origin` dalla forma canonica, due stati che differiscono solo per chi ha deciso l'ordinamento — l'utente o un'inferenza — risultano equivalenti. È corretto ai fini della misura dell'accuratezza interpretativa: l'interrogazione è la stessa e produce lo stesso risultato.

Non è però l'unica proprietà che interessa. Un sistema che infersse tutto correttamente ma non dichiarasse mai l'origine violerebbe P3 restando perfettamente accurato secondo questa metrica. **La correttezza della provenienza va quindi misurata separatamente**, come indicatore proprio, e non confusa con l'accuratezza interpretativa. È un'osservazione da riportare nel Piano di Valutazione della Qualità.

### 14.4 Livelli di equivalenza

| Livello | Definizione | Uso |
|---|---|---|
| **Identità** | Forme canoniche uguali | Deduplicazione, memorizzazione dei risultati |
| **Equivalenza semantica** | Forme canoniche diverse, risultato provabilmente identico | Valutazione: evita di penalizzare formulazioni diverse ma corrette |
| **Equivalenza di esito** | Stesso insieme di record restituito | **Da non usare come criterio** |

**L'equivalenza semantica** copre casi come `between(1, 5)` rispetto a `greater_or_equal(1) AND less_or_equal(5)`. Il contratto minimizza queste occorrenze eliminando le forme ridondanti (§8.1), ma non può azzerarle: dove restano, vanno riconosciute da regole dichiarate, altrimenti la misura penalizza interpretazioni corrette e la soglia di accuratezza risulta artificialmente bassa.

**L'equivalenza di esito è una trappola** e va esclusa esplicitamente. Due interrogazioni diverse possono restituire gli stessi record su un insieme di dati particolare — per esempio quando tutti gli ordini del mese risultano confermati. Usarla come criterio significherebbe considerare corrette interpretazioni sbagliate ogni volta che i dati sono poco discriminanti, ossia proprio negli ambienti di prova, dove i dati sono pochi. È il modo più efficace per costruire una metrica che migliora mentre il prodotto peggiora.

### 14.5 Confronto per componenti

La valutazione non si limita al confronto complessivo. Il confronto **sezione per sezione** — entità, filtri, campi, raggruppamenti, ordinamento, limite, vista — produce l'informazione che serve a migliorare.

Sapere che l'accuratezza complessiva è dell'87% non indica dove intervenire. Sapere che l'entità è individuata correttamente nel 99% dei casi, i filtri nel 91% e i raggruppamenti nel 76% indica esattamente dove concentrare il lavoro sul dizionario e sull'interpretazione.

**Il contratto rende possibile questa granularità** perché lo stato è strutturato in sezioni indipendenti. È un beneficio collaterale del modello a due artefatti che vale la pena rendere esplicito: un contratto monolitico avrebbe consentito solo una misura binaria.

---

## 15. Versionamento ed Evoluzione

### 15.1 Il vincolo da rispettare

Il vincolo **V6** del documento di visione: *nessuna modifica al DSL o allo Stato di Interrogazione può invalidare interrogazioni salvate in precedenza.* Le interrogazioni salvate oggi devono funzionare fra cinque anni.

### 15.2 Schema di versionamento

`dsl_version` segue la forma `MAJOR.MINOR`.

| Tipo di modifica | Incremento | Esempi |
|---|---|---|
| **Additiva** | MINOR | Nuovo predicato, nuova operazione, nuovo risolutore, nuovo tipo di vista |
| **Incompatibile** | MAJOR | Rimozione di un simbolo, cambio di significato, cambio strutturale |

**Regola di base:** le modifiche incompatibili si evitano. Quando sono inevitabili, richiedono un ciclo di deprecazione dichiarato e una funzione di migrazione degli stati persistiti dalla versione precedente.

### 15.3 Rigore sui simboli sconosciuti

Un simbolo o un campo non riconosciuto è **respinto**, non ignorato.

**Motivazione.** L'ignoramento silenzioso è, in un contratto di questo tipo, la scelta più pericolosa disponibile. Un lettore di versione 1.0 che riceve una busta 1.1 contenente una condizione con un predicato che non conosce, e la ignora, esegue un'interrogazione **meno filtrata di quella richiesta** e restituisce più record del dovuto, senza alcun segnale. È un fraintendimento plausibile prodotto dall'infrastruttura anziché dal modello, e per l'utente è indistinguibile da un risultato corretto.

La tolleranza ai campi sconosciuti è una buona pratica nei protocolli dove l'informazione mancante degrada l'esperienza. Qui l'informazione mancante **cambia il significato della domanda**: il rigore è obbligatorio.

### 15.4 Negoziazione della versione

Ogni componente dichiara le versioni che sa leggere; l'interpretazione produce buste nella versione più alta comune. Uno stato persistito porta la propria versione e viene letto dal supporto della propria: un lettore deve supportare tutte le MINOR precedenti della propria MAJOR.

### 15.5 Il tempo agisce su tre assi indipendenti

Un'interrogazione salvata può cambiare comportamento per tre ragioni distinte, che vanno tenute separate perché richiedono presidi diversi.

| Asse | Cosa cambia | Effetto sullo stato salvato | Presidio |
|---|---|---|---|
| **Versione del contratto** | Grammatica e vocabolari | Nessuno: lo stato porta la propria versione | §15.2–15.4 |
| **Dizionario Semantico** | Significato dei riferimenti e dei risolutori | **L'interrogazione può cambiare risultato** | §15.6 |
| **Installazione Odoo** | Moduli, campi, personalizzazioni | Il riferimento può diventare non risolvibile | §7.4, errore diagnosticabile |

### 15.6 Il caso delicato: l'evoluzione del dizionario

Se un'installazione ridefinisce il risolutore `recent_orders` da 30 a 60 giorni, ogni interrogazione salvata che lo utilizza cambia risultato. È il comportamento **voluto** — è così che una correzione del dizionario si propaga a tutto ciò che vi fa riferimento, ed è la ragione per cui la risoluzione avviene a ogni esecuzione (§1.4).

Ma è anche un modo per cambiare silenziosamente il significato di un report ricorrente.

**Requisito che ne discende**, da riportare nel documento sul Modello Semantico: le voci del dizionario che definiscono **metriche e risolutori aziendali** — non le semplici corrispondenze di denominazione — sono versionate, le loro modifiche sono tracciate e comunicate ai proprietari delle interrogazioni salvate che vi fanno riferimento. La distinzione fra *"anche «commerciale» significa venditore"* e *"«recente» significa 60 giorni"* è netta: la prima è un arricchimento del vocabolario, la seconda è una modifica di definizione.

### 15.7 Il caso delle regole di derivazione della vista

Le regole di §6.7 sono parte del contratto: cambiarle cambierebbe la vista di stati già salvati.

Il problema è già risolto dalla struttura scelta: `presentation` è **sempre presente nello stato** con il valore effettivo, anche quando derivato (regola di canonicalizzazione 5, §14.3). Uno stato salvato porta con sé la vista che gli è stata assegnata; una modifica delle regole vale per le interpretazioni successive, non per il passato.

È un esempio del beneficio di materializzare i valori inferiti anziché ricalcolarli: l'inferenza è un atto compiuto una volta e registrato, non una funzione rivalutata a ogni lettura.

---

## 16. Punti di Estensione per le Fasi Future

### 16.1 Come si estende il contratto

Questa sezione non progetta le fasi successive. Dichiara **dove** ciascuna interverrà e, soprattutto, **cosa dovrà restare invariato** — perché un punto di estensione dichiarato in anticipo è una difesa contro il rischio R9, l'erosione progressiva dei principi.

| Fase | Estensione del contratto | Invariante da preservare |
|---|---|---|
| **3 — Azioni sui record** | Nuova famiglia di operazioni con conferma obbligatoria e anteprima | Nessuna azione senza conferma esplicita; le operazioni di lettura restano invariate |
| **4 — Analitica** | Confronti fra periodi, serie storiche, metriche definite nel dizionario; nuovo artefatto di **composizione** per le dashboard | Sola lettura; nessuna metrica definita dal modello (§8.5) |
| **5 — Scrittura** | **Profilo distinto** del contratto, attivabile per installazione | Anteprima obbligatoria; conferma esplicita; nessuna dipendenza dalla confidenza (§10.5) |
| **6 — Voce e multimodale** | **Nessuna modifica al contratto** | È la verifica dell'indipendenza dal canale: se serve modificare il contratto, il principio P5 è stato violato prima |
| **7 — Copilot e multi-agente** | Sequenze di buste, ciascuna validata individualmente | Ogni operazione con effetto sui dati resta soggetta a conferma umana; nessuna busta sfugge ai cinque livelli |

### 16.2 La riga più importante della tabella

La riga della **Fase 6**.

Se l'introduzione della voce, del canale Teams o della comprensione documentale richiedesse una modifica del contratto, significherebbe che qualcosa di specifico del canale era penetrato nel motore di comprensione. Il contratto è quindi il punto in cui l'indipendenza dal canale si verifica in modo oggettivo, invece di essere affermata.

**Raccomandazione operativa:** anticipare un secondo canale già in Fase 2, come previsto dal documento di visione, e usarlo esattamente come prova. Un'indipendenza dal canale mai messa alla prova è una supposizione.

### 16.3 La composizione: l'unico artefatto nuovo previsto

La Fase 4 richiederà un artefatto che oggi non esiste: una **composizione** — un insieme ordinato di Stati di Interrogazione con una disposizione di presentazione. È ciò che una dashboard è, concettualmente.

Va segnalato ora perché conferma la scelta di §4.3: **una dashboard è componibile solo se lo stato è un oggetto di prima classe**. Se la conversazione fosse una cronologia di messaggi, non ci sarebbe nulla da comporre, e la Fase 4 sarebbe una riprogettazione anziché un'estensione. È la verifica anticipata della decisione **D4**.

---

## 17. Esempi Completi

### 17.1 Sequenza conversazionale

Stato iniziale: vuoto.

**Turno 1 — *"Mostrami tutti i clienti"***

```json
{ "outcome": "operations", "confidence": 0.96, "operations": [
  { "op": "set_target", "ref": "clienti",
    "provenance": { "text": "clienti" } } ] }
```

Stato: `target: clienti` · `limit: 80 (default)` · `presentation: list (default_list)` · campi predefiniti.

Nota: *"tutti"* non produce alcuna operazione. Il limite predefinito resta e viene mostrato nell'interpretazione (§5.8). Il sistema non promette ciò che non farà.

**Turno 2 — *"Solo quelli attivi"***

```json
{ "outcome": "operations", "confidence": 0.94, "operations": [
  { "op": "add_condition", "combine": "all",
    "condition": { "ref": "clienti.attivo", "predicate": "is_true",
      "value": { "kind": "boolean", "value": true } },
    "provenance": { "text": "quelli attivi" } } ] }
```

Frase incompleta e priva di soggetto: interpretabile solo grazie allo stato corrente. Nessuna parte dello stato precedente è riemessa dal modello — è la proprietà di §4.3.

**Turno 3 — *"Ordina per città"***

```json
{ "outcome": "operations", "confidence": 0.97, "operations": [
  { "op": "set_order", "ref": "clienti.citta", "direction": "asc",
    "provenance": { "text": "per città" } } ] }
```

`asc` è inferito: per un attributo testuale l'ordinamento crescente è la lettura naturale. Registrato con `origin: "inferred"`.

**Turno 4 — *"Mostrami anche il telefono"***

```json
{ "outcome": "operations", "confidence": 0.98, "operations": [
  { "op": "add_field", "ref": "clienti.telefono",
    "provenance": { "text": "anche il telefono" } } ] }
```

*"Anche"* → `add_field`, non `set_fields` (§6.4).

**Turno 5 — *"Apri il primo"***

```json
{ "outcome": "operations", "confidence": 0.95, "operations": [
  { "op": "open_record", "selector": { "by": "position", "value": 1 },
    "provenance": { "text": "il primo" } } ] }
```

*"Il primo"* ha significato solo perché l'ordinamento è definito. Se `order_by` fosse assente, l'esito corretto sarebbe `clarification`: *"il primo secondo quale ordine?"*.

### 17.2 Vaghezza numerica

***"Mostrami le auto con circa centomila chilometri"***

```json
{ "outcome": "operations", "confidence": 0.89, "operations": [
  { "op": "set_target", "ref": "veicoli", "provenance": { "text": "le auto" } },
  { "op": "add_condition",
    "condition": { "ref": "veicoli.chilometraggio", "predicate": "approximately",
      "value": { "kind": "number", "value": 100000, "resolver": "approx_relative" } },
    "provenance": { "text": "circa centomila chilometri" } } ] }
```

Interpretazione mostrata: **Veicoli · chilometraggio tra 90.000 e 110.000**.
Il modello ha dichiarato l'approssimazione; la tolleranza viene dal dizionario; l'utente vede l'intervallo effettivo e può correggerlo (§9.3).

### 17.3 Aggregazione e derivazione della vista

***"Somma degli importi per venditore"*** — su stato con `target: ordini_vendita`

```json
{ "outcome": "operations", "confidence": 0.93, "operations": [
  { "op": "add_measure", "ref": "ordini_vendita.importo_totale", "function": "sum",
    "provenance": { "text": "somma degli importi" } },
  { "op": "add_group", "ref": "ordini_vendita.venditore",
    "provenance": { "text": "per venditore" } } ] }
```

Nessuna operazione sulla vista: il modello non la sceglie. La regola 2 di §6.7 — una misura e un raggruppamento — deriva `graph`, e lo stato registra `rule: "measures_single_group_implies_graph"`.

Interpretazione mostrata: *"Sto mostrando un grafico perché hai chiesto un totale per venditore."* La scelta è spiegata e contraddicibile.

### 17.4 Ambiguità interpretativa

***"Gli ordini di Rossi"*** → esito `clarification` con due opzioni pre-associate alle rispettive operazioni (§11.2).

Se l'utente sceglie *"Come cliente"* e i clienti denominati Rossi sono tre, segue una **seconda** disambiguazione, di natura completamente diversa: referenziale, deterministica, risolta dal backend senza coinvolgere il modello (§11.3).

Due domande consecutive all'utente, due meccanismi distinti. Confonderli avrebbe significato pagare un'interpretazione probabilistica per un problema che ha una risposta esatta.

### 17.5 Fuori ambito

***"Cambia lo stato di questo ordine in confermato"***

```json
{ "outcome": "out_of_scope", "confidence": 0.97, "scope_note": "modifica_dati" }
```

La richiesta è compresa perfettamente. Il contratto non sa esprimerla: non esiste alcuna operazione di scrittura da respingere (§13.1).

Risposta all'utente: *"In questa versione posso solo consultare i dati."* La categoria `modifica_dati` viene conteggiata; la sua frequenza è l'evidenza quantitativa a supporto della priorità della Fase 5 — o della sua posticipazione.

---

## 18. Alternative Valutate e Scartate

### 18.1 Formato di serializzazione

| Opzione | Valutazione |
|---|---|
| **JSON con schema formale** | **Scelta.** Validazione con strumenti maturi; supporto diffuso alla generazione vincolata; ispezionabile senza strumenti dedicati; nessun parser da mantenere |
| Linguaggio testuale dedicato | Scartata: richiede un parser proprietario da mantenere per anni, introduce ambiguità sintattiche, non beneficia della generazione vincolata, e produce errori di sintassi dove il JSON non ne ammette |
| YAML | Scartata: conversioni implicite di tipo notoriamente insidiose; il vantaggio di leggibilità è irrilevante per un artefatto prodotto da una macchina |
| Formato proprietario del fornitore | Scartata: violerebbe il vincolo V5. Le funzionalità di output strutturato dei fornitori sono un **trasporto** utilizzabile, non il contratto: la forma normativa resta il JSON, e nessuna sua proprietà può dipendere dal meccanismo di trasporto |

L'ultima riga è una distinzione operativa importante: sfruttare la generazione vincolata di un fornitore è legittimo e raccomandato: renderla **necessaria** alla validità del contratto non lo è.

### 18.2 Interpretazione senza contratto

L'alternativa radicale: il modello riceve la richiesta, interroga direttamente i dati, formula la risposta. Nessun DSL.

Scartata perché elimina simultaneamente ogni proprietà su cui il prodotto si fonda: il confine di validazione, il perimetro delle capacità, il disaccoppiamento, l'unità di misura (§2.1). Il sistema risultante non sarebbe una versione più semplice di questo prodotto: sarebbe un prodotto diverso, con un profilo di affidabilità incompatibile con l'uso enterprise che il documento di visione descrive.

### 18.3 Riferimenti tecnici anziché semantici

Il modello emette direttamente nomi di modelli e campi Odoo, ricavandoli da uno schema fornito nel contesto.

Scartata. È l'approccio più diffuso e il meno robusto: il modello inventa nomi plausibili, l'errore emerge tardi, la validazione può solo rilevare l'inesistenza senza poter proporre l'alternativa corretta. Il livello semantico costa un'indirezione e restituisce in cambio la possibilità di **suggerire** — *"non conosco «fatturato» per gli ordini, intendevi «importo totale»?"* — che è il comportamento che l'utente percepisce come competenza.

### 18.4 Vocabolario aperto con corrispondenza approssimata

Il modello emette denominazioni libere che il sistema riconcilia con corrispondenze approssimate.

Scartata: sposta la non determinatezza dal modello all'algoritmo di riconciliazione senza eliminarla, e rende impossibile la generazione vincolata. Una corrispondenza approssimata che sbaglia produce un fraintendimento plausibile con la peggiore delle caratteristiche: nessun componente si accorge di aver sbagliato.

La corrispondenza approssimata ha però un ruolo legittimo, **fuori dal percorso di esecuzione**: nella costruzione e nell'arricchimento del Dizionario Semantico, dove un suggerimento errato viene esaminato da una persona prima di diventare parte del vocabolario.

### 18.5 Alternative argomentate altrove

| Alternativa | Sezione |
|---|---|
| Stato completo a ogni turno anziché operazioni | §4.2–4.3 |
| Domain Odoo grezzo nel contratto | §8.4 |
| Espressioni calcolate come misure | §8.5 |
| Risoluzione delle date da parte del modello | §9.2 |
| Tolleranza ai simboli sconosciuti | §15.3 |
| Vista inferita anche per il calendario | §6.7 |
| Persistenza dei binding tecnici | §1.4 |

---

## 19. Rischi Specifici del Contratto

I rischi seguenti sono propri di questo documento e si aggiungono a quelli del documento di visione, cui restano ricondotti.

### RC1 — Espressività insufficiente

**Descrizione.** Una quota rilevante di richieste reali non è esprimibile e produce `out_of_scope`.
**Impatto.** Medio-alto: prodotto percepito come limitato; pressione a estendere la grammatica caso per caso.
**Mitigazione.** Misurare la distribuzione di `out_of_scope` fin dal primo giorno (§11.4); estendere per classi ricorrenti documentate, mai per richiesta singola; preferire l'arricchimento del dizionario all'estensione della grammatica (§7.3).
**Segnale anticipatore.** Estensioni della grammatica motivate dall'esigenza di un singolo cliente.

### RC2 — Il dizionario diventa un collo di bottiglia

**Descrizione.** Ogni nuova esigenza richiede un intervento sul dizionario, che diventa un'attività di manutenzione continua e specialistica.
**Impatto.** Medio-alto: costo di esercizio crescente; tempi di risposta alle esigenze dei clienti lunghi.
**Mitigazione.** Arricchimento automatico a partire dalle disambiguazioni e dai fallimenti di livello 3 (§12.4); strumenti che rendano l'intervento eseguibile dal cliente e non solo dal fornitore.
**Segnale anticipatore.** Coda crescente di richieste di modifica al dizionario.

### RC3 — Il catalogo eccede la capacità di contesto del modello

**Descrizione.** Un'installazione ampia può avere migliaia di attributi interrogabili. Il catalogo completo non è trasmissibile e va pre-selezionato.

**Impatto. Alto**, per una ragione che merita di essere dichiarata senza attenuazioni: **la pre-selezione del catalogo reintroduce un secondo punto non deterministico** nel sistema, a monte dell'interpretazione. Se il riferimento corretto non è nell'insieme selezionato, il modello non può produrre l'interpretazione giusta, per quanto sia capace. È un limite superiore all'accuratezza che nessun miglioramento del modello può superare.

**Mitigazione.** Pre-selezione **deterministica** dove possibile (entità dichiarata, attributi predefiniti, frequenza d'uso storica); misura **separata e obbligatoria** della copertura del catalogo — la percentuale di casi in cui il riferimento corretto è presente nell'insieme selezionato; nessuna pre-selezione affidata a un secondo componente probabilistico senza che la sua copertura sia misurata con la stessa disciplina dell'accuratezza interpretativa.

**Segnale anticipatore.** Accuratezza che si stabilizza su un valore inferiore all'obiettivo senza che l'analisi dei fraintendimenti indichi cause interpretative.

**Nota per il Piano di Valutazione.** Un'accuratezza complessiva dell'87% con una copertura del catalogo del 92% descrive una situazione molto diversa da un'accuratezza dell'87% con copertura del 99,5%: nel primo caso il margine di miglioramento non è nel modello. Le due misure vanno riportate insieme, sempre.

### RC4 — I limiti strutturali risultano troppo restrittivi

**Descrizione.** Profondità di 2 salti, albero di 3 livelli, 3 raggruppamenti si rivelano insufficienti per casi d'uso reali frequenti.
**Impatto.** Medio.
**Mitigazione.** I limiti sono parametri dichiarati, non ipotesi implicite: sono ricalibrabili sul corpus con una modifica additiva. La misura da sorvegliare è la frequenza dei fallimenti di livello 4 su queste specifiche verifiche.
**Segnale anticipatore.** Fallimenti di profondità concentrati su una classe ricorrente di richieste.

### RC5 — La canonicalizzazione sottostima l'accuratezza

**Descrizione.** Interpretazioni corrette ma formulate diversamente dall'atteso vengono conteggiate come errate.
**Impatto.** Medio-alto sul **governo** del prodotto: una metrica che sottostima porta a rinviare avanzamenti legittimi e a intervenire su problemi inesistenti.
**Mitigazione.** Regole di equivalenza semantica dichiarate (§14.4); revisione manuale periodica di un campione di casi giudicati errati, per verificare che l'errore sia reale.
**Segnale anticipatore.** Casi giudicati errati che a un esame umano risultano corretti.

### RC6 — La confidenza viene usata come misura

**Descrizione.** La confidenza dichiarata dal modello viene trattata come probabilità e usata per decisioni automatiche.
**Impatto.** Alto nelle fasi con effetti sui dati: una conferma saltata per confidenza elevata è precisamente il percorso attraverso cui un fraintendimento plausibile diventa una scrittura errata.
**Mitigazione.** §10.5, in particolare la terza regola; calibrazione empirica sul corpus a ogni cambio di modello.
**Segnale anticipatore.** Proposte di ridurre le conferme in funzione della confidenza.

### RC7 — Erosione del contratto per estensioni additive

**Descrizione.** Estensioni formalmente additive che, sommate, alterano nella sostanza le proprietà del contratto: un predicato che accetta un valore più libero, un'operazione che tocca più sezioni, un'eccezione a un limite.
**Impatto.** Alto sull'orizzonte pluriennale: è la forma che il rischio R9 assume su questo documento.
**Mitigazione.** Ogni estensione verificata rispetto agli otto criteri di §3, con esito documentato; revisione periodica di coerenza (§18.10 del documento di visione).
**Segnale anticipatore.** Estensioni motivate dalla convenienza implementativa anziché da un'esigenza documentata nel corpus.

---

## 20. Decisioni Richieste

Numerazione in continuità con il documento di visione (D1–D8).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D9** | Modello a due artefatti: il modello emette operazioni, il sistema possiede lo stato (§4.3) | **Adottare** | È il presupposto di tutto il documento: ogni altra decisione va riconsiderata |
| **D10** | Riferimenti semantici con catalogo per utente anziché nomi tecnici (§7.2) | **Adottare** | La difesa di V2 a livello di vocabolario decade; aumenta la modalità di errore più comune |
| **D11** | JSON con schema formale come forma normativa (§18.1) | **Adottare** | Nessun blocco immediato; il costo cresce con il codice scritto |
| **D12** | Limiti strutturali: 2 salti di relazione, albero filtri di 3 livelli, 3 raggruppamenti (§5.4, §7.3) | **Adottare come valori iniziali**, ricalibrare sul corpus | Limiti impliciti e non misurati |
| **D13** | Limite predefinito e massimo assoluto dei record per installazione (§5.8) | Definire prima del primo rilascio | Nessuna protezione contro le interrogazioni non limitate |
| **D14** | Rigore sui simboli sconosciuti: respingere, mai ignorare (§15.3) | **Adottare** | Rischio di risultati meno filtrati del richiesto, senza segnale |
| **D15** | Ripristino con un solo tentativo (§12.7) | **Adottare** | I difetti sistematici del modello restano mascherati dalle ripetizioni |
| **D16** | Strategia di pre-selezione del catalogo per installazioni ampie, con misura obbligatoria della copertura (RC3) | **Decidere prima della Fase 1**; deve essere deterministica o misurata | Limite superiore all'accuratezza, invisibile e non diagnosticabile |
| **D17** | Versionamento delle voci di dizionario che definiscono metriche e risolutori (§15.6) | **Adottare** | Il significato dei report ricorrenti può cambiare in silenzio |

**D9, D10 e D16 sono le decisioni bloccanti.** Le prime due determinano la forma di ogni documento successivo; la terza determina un limite di accuratezza che, se non affrontato ora, verrà scoperto quando l'accuratezza si fermerà sotto l'obiettivo senza una causa apparente.

---

## 21. Glossario del Contratto

| Termine | Definizione |
|---|---|
| **Busta di Interpretazione** | L'output completo del modello per un turno: esito, operazioni o chiarimento, confidenza, provenienza |
| **Esito** (`outcome`) | Il tipo di risposta del modello: `operations`, `clarification`, `out_of_scope`, `not_understood` |
| **Operazione** | Unità atomica di modifica dello Stato di Interrogazione; appartiene a un vocabolario chiuso di 18 voci |
| **Stato di Interrogazione** | L'oggetto canonico che rappresenta l'interrogazione corrente in termini semantici; persistibile e condivisibile |
| **Piano di Esecuzione** | Artefatto tecnico effimero prodotto dalla risoluzione; fuori dall'ambito del contratto e mai persistito |
| **Riferimento semantico** | Identificativo di un'entità o di un attributo nel linguaggio dell'organizzazione, emesso dal Dizionario Semantico |
| **Catalogo** | L'insieme dei riferimenti semantici che il modello può nominare per un dato utente; costruito sui suoi permessi |
| **Risoluzione** | Traduzione deterministica dei riferimenti semantici in binding tecnici, con verifica dei permessi, ripetuta a ogni esecuzione |
| **Risoluzione referenziale** | Traduzione deterministica di un letterale (*"Rossi"*) nei record corrispondenti, con i permessi dell'utente |
| **Risolutore** (`resolver`) | Regola dichiarata nel dizionario che assegna un significato preciso a un'espressione vaga |
| **Origine** (`origin`) | Chi ha determinato un elemento dello stato: `user`, `inferred` o `default` |
| **Provenienza** (`provenance`) | Il frammento della frase dell'utente che ha prodotto un elemento dello stato |
| **Forma canonica** | Rappresentazione normalizzata di uno stato, usata per il confronto e la deduplicazione |
| **Profilo** | Insieme delle capacità attive del contratto. La versione 1.0 definisce il profilo di **sola lettura** |

---

## Chiusura

Questo contratto è progettato attorno a una sola idea: **restringere ciò che il modello può dire, invece di verificare ciò che ha detto.**

Il modello sceglie da vocabolari chiusi, nomina solo ciò che l'utente può vedere, descrive il cambiamento e non lo stato, riconosce la vaghezza senza risolverla, e non dispone di alcuna parola per scrivere. Ciò che resta fuori da questo perimetro non viene respinto: non è esprimibile.

È il motivo per cui la validazione di §12 può essere esaustiva, l'accuratezza di §14 può essere misurata meccanicamente, e la sola lettura di §13.1 non richiede vigilanza.

**Documenti successivi**, in ordine di dipendenza:

1. **Architettura di Sistema** — componenti, flussi, indipendenza dal canale, punti di estensione *(dipende da D9, D10)*
2. **Modello Semantico** — struttura e ciclo di vita del Dizionario Semantico, strategia di catalogo *(dipende da D10, D16, D17)*
3. **Piano di Valutazione della Qualità** — corpus, metodo, soglie, copertura del catalogo, regressioni *(dipende da §14, RC3, RC5)*
4. **Modello di Sicurezza e Conformità** — identità, autorizzazioni, tracciabilità, trattamento dei dati *(in parallelo)*

---

*Fine del documento.*
