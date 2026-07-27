# Modello Semantico
## Dizionario, Catalogo e Copertura — AI Agent per Odoo

---

| Voce | Valore |
|---|---|
| **Titolo** | Modello Semantico — Dizionario, Catalogo e Copertura |
| **Versione** | 1.0 (bozza) |
| **Data** | 27 luglio 2026 |
| **Stato** | Bozza sottoposta ad approvazione dell'Architect |
| **Destinatari** | Software Architect, Team Leader, Sviluppatori, Consulenti di attivazione, Product Owner |
| **Documenti sorgente** | `02-visione-prodotto.md`, `03-specifica-dsl.md`, `04-architettura.md` |
| **Piattaforma verificata** | Odoo 18.0, sorgenti in `core/` |
| **Risolve** | Decisioni **D10**, **D16**, **D17**, **D21**, **D22** |
| **Ambito** | Struttura del Dizionario, tipi di voce, costruzione del Catalogo, misura della copertura, attivazione, arricchimento dall'uso, governo delle modifiche |
| **Fuori ambito** | Schema dei dati, interfaccia di amministrazione, strategia di prompting, piano di valutazione *(documento dedicato)* |

---

## 1. Executive Summary

### 1.1 Perché questo documento decide il successo del prodotto

Il documento di visione identifica nel Dizionario Semantico uno dei tre asset proprietari e l'unico fossato competitivo difendibile: l'integrazione con un modello linguistico è replicabile in poche settimane, due anni di dizionario affinato sui dati di un cliente non lo sono.

Il documento sul DSL aggiunge il rovescio della medaglia: **RC3**, il tetto di accuratezza. Se il riferimento corretto non è nel catalogo fornito all'Interprete, l'interpretazione giusta è irraggiungibile — per quanto capace sia il modello.

Questo documento definisce entrambe le facce: il dato curato che cresce nel tempo, e il meccanismo che ne seleziona la porzione giusta a ogni richiesta.

### 1.2 Le quattro decisioni portanti

**DS1 — Il Dizionario è stratificato, e i livelli non si sovrascrivono a caso.**
Quattro livelli con precedenza dichiarata: derivato dai metadati, pacchetto base del fornitore, personalizzazione del cliente, proposte apprese dall'uso. **Il livello appreso non è attivo**: è una coda di proposte che diventano attive solo per approvazione (§2).

**DS2 — Esistono due classi di voce con governo diverso.**
L'*arricchimento del vocabolario* — *"anche «commerciale» significa venditore"* — è additivo e non cambia il risultato di nulla. La *modifica di definizione* — *"«recente» significa 60 giorni"* — **cambia il risultato di ogni interrogazione salvata che la usa**. Trattarle allo stesso modo è il modo più rapido per far cambiare in silenzio il significato di un report ricorrente (§4).

**DS3 — Il Catalogo espone una selezione curata, non lo schema Odoo.**
Un modello Odoo espone abitualmente oltre cento campi, la maggior parte dei quali priva di significato per un utente. Riversarli nel catalogo peggiora l'interpretazione e consuma il budget. Ogni attributo ha uno stato di **esposizione**, derivato deterministicamente e correggibile (§5).

**DS4 — La copertura è una metrica di primo livello, misurata per fase.**
Non un indicatore interno: si riporta sempre accanto all'accuratezza, e separata fra determinazione dell'entità e selezione degli attributi, perché le due hanno cause e rimedi diversi (§6).

### 1.3 Il primo giorno di un cliente — e perché non parte da zero

Il rischio **R4** del documento di visione colloca la qualità peggiore nel momento in cui si forma la fiducia: il primo giorno, con un dizionario vuoto.

La verifica sui sorgenti mostra che il punto di partenza è migliore di quanto sembri. **Un'installazione Odoo contiene già gran parte del lessico dell'azienda**, in forma strutturata e leggibile senza alcun lavoro di configurazione:

| Fonte | Cosa contiene | Riferimento |
|---|---|---|
| `ir.model.fields.field_description` | Etichetta di ogni campo, **tradotta** | `ir_model.py:555` |
| `ir.model.name` | Denominazione di ogni entità, **tradotta** | `ir_model.py:217` |
| `ir.filters.name` + `model_id` + `domain` | **Le parole scelte dagli utenti** per i concetti che gli interessano, già legate a un'entità e a una condizione | `ir_filters.py:14–21` |

La terza riga è la più preziosa e la meno ovvia. Un filtro salvato chiamato *"Fatture scadute"* è esattamente una voce di dizionario già scritta da un utente: un termine dell'azienda, l'entità a cui si riferisce, e la condizione che lo definisce. **Le installazioni mature ne contengono decine.**

Poiché le prime due fonti sono tradotte, il livello base del dizionario **nasce multilingua senza costo aggiuntivo** — proprietà tutt'altro che scontata in un prodotto che deve comprendere il gergo aziendale misto.

### 1.4 Ciò che il documento non promette

Il dizionario non elimina la necessità di lavoro umano. Le metriche aziendali — cosa entra nel *"fatturato"*, chi è un *"cliente attivo"* — sono convenzioni che nessuna introspezione può dedurre, perché non sono scritte da nessuna parte nel sistema.

Il documento mira a un obiettivo più modesto e più realistico: **ridurre il lavoro umano a ciò che solo un umano può fare**, e renderlo incrementale anziché preliminare.

---

## 2. Architettura del Dizionario

### 2.1 I quattro livelli

```
┌─ L3 ── APPRESO ────────────── coda di proposte, NON attiva ──────┐
│  candidati da disambiguazioni, correzioni, fallimenti di liv. 3  │
│  diventano attivi solo per approvazione → confluiscono in L2     │
└──────────────────────────────────────────────────────────────────┘
┌─ L2 ── CLIENTE ─────────────────────── proprietà: il cliente ────┐
│  gergo aziendale · metriche · risolutori · preferenze            │
│  versionato · modifiche tracciate                                │
└──────────────────────────────────────────────────────────────────┘
┌─ L1 ── BASE ────────────────────────── proprietà: il fornitore ──┐
│  pacchetti per dominio: vendite, acquisti, contabilità, CRM…     │
│  sinonimi comuni, risolutori predefiniti, forme colloquiali      │
└──────────────────────────────────────────────────────────────────┘
┌─ L0 ── DERIVATO ────────────────── nessun proprietario, generato ┐
│  introspezione dei metadati Odoo · rigenerato a ogni aggiornam.  │
│  etichette, entità, valori enumerati — già tradotti              │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Precedenza

> **L2 › L1 › L0.** L3 non partecipa: è una coda, non un livello attivo.

Due regole ne discendono, entrambe normative.

**Il cliente ha sempre l'ultima parola.** Se in un'azienda *"pratica"* significa ordine di vendita, quella definizione prevale sul pacchetto base che la associa a un progetto. Nessun aggiornamento del fornitore può sovrascrivere una scelta del cliente: sarebbe la modalità di guasto più grave del sistema, perché si manifesterebbe come un peggioramento improvviso e inspiegabile dopo un aggiornamento.

**Il livello derivato non è mai modificato a mano.** È rigenerato a ogni aggiornamento dei moduli. Una correzione a L0 andrebbe persa: la correzione si scrive in L2, che ha precedenza.

### 2.3 Perché L3 non è attivo

È la decisione più importante della sezione, e va difesa perché costa lavoro.

L'arricchimento automatico è previsto dalla Fase 2 della roadmap ed è il meccanismo con cui la qualità cresce con l'uso. La tentazione di rendere attive le voci apprese senza revisione è forte: elimina un passaggio umano e accelera visibilmente il miglioramento.

Tre ragioni per non farlo.

**È un percorso dal linguaggio degli utenti al contesto del modello.** L'architettura lo segnala in §12.4: il dizionario alimenta il catalogo, che raggiunge l'Interprete. Voci apprese e attivate senza revisione costituiscono un ingresso non validato verso il modello.

**Un apprendimento errato è auto-rinforzante.** Se il sistema apprende una corrispondenza sbagliata, la applica; gli utenti che ottengono un risultato plausibile non la correggono; la corrispondenza si consolida. L'errore diventa la nuova normalità e nessun indicatore lo segnala.

**Alcune voci cambiano il significato dei dati.** Se il sistema apprendesse una metrica — e le metriche sono precisamente ciò che gli utenti chiariscono più spesso — l'attivazione automatica modificherebbe il risultato di interrogazioni salvate (§4.3). Nessun apprendimento automatico deve poter fare questo.

**Il costo dell'approvazione è contenuto** perché le proposte sono aggregate: non una per interazione, ma una per termine ricorrente, ordinate per frequenza. Il consulente non esamina migliaia di eventi ma una lista di poche decine di termini, ordinata per impatto.

### 2.4 Il livello derivato: cosa entra e cosa no

L0 è generato per introspezione, ma **non è una copia dello schema**. Già in questa fase si applica una selezione, perché è qui che nasce la qualità del catalogo (§5.2).

| Entra in L0 | Non entra |
|---|---|
| Entità con etichetta significativa | Modelli tecnici, transienti, di collegamento |
| Campi con etichetta, tipo interrogabile | Campi tecnici di sistema, binari, calcolati non memorizzati e onerosi |
| Valori ammessi degli enumerati, con etichetta | Campi con etichetta assente o non distintiva |
| Relazioni dichiarate percorribili | Relazioni oltre la profondità ammessa dal contratto |
| Traduzioni delle etichette | — |

I criteri di esclusione sono deterministici e dichiarati (§5.2), non giudizi presi caso per caso: L0 deve poter essere rigenerato in modo identico a ogni aggiornamento.

### 2.5 Ciò che il Dizionario non contiene

| Assente | Perché |
|---|---|
| Contenuto dei record | Assunzione **A6**, vincolo **V7**: il dizionario alimenta il catalogo, che raggiunge il modello |
| Riferimenti a utenti o gruppi | **RA8** dell'architettura: il dizionario non conosce l'utente; i permessi si applicano al catalogo |
| Binding tecnici persistiti come verità | §1.4 del DSL: il dizionario mappa i riferimenti, la risoluzione avviene a ogni esecuzione |
| Testo libero destinato al modello | Ogni voce è tipizzata (§3); non esistono istruzioni immesse come dati |

**La seconda riga è quella che verrà violata per prima.** La tentazione di scrivere *"per l'utente Rossi, «i miei ordini» significa venditore = Rossi"* è naturale e sbagliata: renderebbe il dizionario dipendente dagli utenti e i permessi persistiti e disallineabili. Le preferenze personali, se serviranno, appartengono alla sessione o a un livello di preferenze separato — mai al dizionario.

---

## 3. Tipi di Voce

### 3.1 Il vocabolario è chiuso anche qui

Il dizionario non è un insieme di annotazioni libere: ogni voce appartiene a **uno di sette tipi**, ciascuno con una struttura propria e un effetto dichiarato sul sistema.

La ragione è la stessa che governa il DSL (criterio C1): ciò che non è tipizzato non è validabile, e un dizionario non validabile diventa nel tempo un deposito di annotazioni contraddittorie che nessuno sa più interpretare.

### 3.2 T1 — Denominazione

Associa un riferimento semantico ai termini con cui l'organizzazione lo nomina.

```
riferimento   ordini_vendita.venditore
termini       venditore · commerciale · agente · rappresentante · sales
lingua        it, en
```

È il tipo più numeroso e il più innocuo: aggiungere un sinonimo non cambia il risultato di nulla, allarga soltanto ciò che il sistema riconosce.

**Origine tipica:** L0 per le etichette, L1 per i sinonimi comuni di dominio, L2 per il gergo aziendale, L3 per i termini osservati nell'uso.

### 3.3 T2 — Valore enumerato

Associa le etichette umane ai valori tecnici degli attributi a scelta chiusa.

```
riferimento   ordini_vendita.stato
valore        confermato   ← "confermato", "confermati", "ordine confermato"
valore        bozza        ← "bozza", "preventivo", "non confermato"
```

Deriva quasi interamente da L0, poiché Odoo espone le etichette dei valori ammessi, tradotte. È ciò che consente al catalogo di fornire al modello i valori validi **senza mostrargli alcun record**: sono metadati di schema, non contenuto (§15.1 dell'architettura).

### 3.4 T3 — Risolutore di vaghezza

Assegna un significato preciso e stabile a un'espressione intrinsecamente imprecisa.

```
nome          approx_relative      regola   ±10% del valore
nome          recent_orders        regola   ultimi 30 giorni
nome          soon                 regola   prossimi 7 giorni
```

Realizza §9.3 del DSL: il modello riconosce la vaghezza e la nomina, il dizionario la risolve. **Una modifica qui cambia il risultato di ogni interrogazione che usa il risolutore** — appartiene quindi alla classe delle definizioni (§4).

### 3.5 T4 — Metrica aziendale

Definisce una grandezza calcolata che l'organizzazione nomina come un concetto unico.

```
nome        fatturato
entità      fatture
misura      somma di importo_totale
condizioni  tipo = vendita · stato = confermata · escluse note di credito
```

È il tipo con l'impatto più alto e il numero di voci più basso. Realizza §8.5 del DSL — nessuna espressione calcolata prodotta dal modello: una metrica è **definita una volta da chi conosce le convenzioni contabili dell'azienda** e successivamente riferita per nome.

**È anche il tipo più pericoloso**, perché un errore qui produce numeri credibili e sbagliati — la forma di R1 con l'impatto maggiore, poiché i numeri aggregati finiscono nelle riunioni.

### 3.6 T5 — Categoria

Un termine dell'azienda che corrisponde a una condizione, non a un attributo.

```
termine     clienti importanti
entità      clienti
condizione  fatturato ultimi 12 mesi > 50.000
```

*"Clienti importanti"*, *"ordini urgenti"*, *"pratiche ferme"* non esistono nel database: esistono nella testa di chi lavora. Senza questo tipo, ogni loro uso produrrebbe un chiarimento, e il sistema apparirebbe incapace di comprendere il linguaggio più naturale dell'azienda.

Appartiene alla classe delle definizioni: modificare la soglia cambia i risultati.

### 3.7 T6 — Preferenza di disambiguazione

Registra come un'ambiguità ricorrente viene abitualmente risolta in quella specifica organizzazione.

```
ambiguità   "ordini di <persona>" su ordini_vendita
preferenza  cliente        (osservata nel 94% delle scelte)
```

Realizza il meccanismo previsto in §11.2 del DSL: se quasi tutti scelgono la stessa opzione, la domanda smette di essere posta.

**Regola prudenziale:** una preferenza registrata **non elimina la trasparenza**. L'interpretazione continua a mostrare che *"Rossi"* è stato inteso come cliente, e l'utente può contraddirla. La preferenza sopprime la domanda, non la visibilità della scelta — altrimenti si otterrebbe un sistema che indovina in silenzio, che è precisamente ciò che il prodotto esclude.

### 3.8 T7 — Riferimento promosso

Espone come attributo di primo livello un percorso di relazione, tipicamente per superare il limite di due salti del contratto.

```
riferimento   ordini_vendita.paese_cliente
percorso      ordini_vendita.cliente.paese
termini       paese del cliente · nazione
```

È il meccanismo previsto da §7.3 del DSL: **arricchire il dizionario anziché ampliare la grammatica**. Un percorso che gli utenti nominano spesso diventa un riferimento diretto, senza che il contratto debba ammettere percorsi più lunghi.

### 3.9 Riepilogo

| Tipo | Cosa definisce | Livello tipico | Classe |
|---|---|---|---|
| **T1** Denominazione | Termini per un riferimento | L0–L3 | Vocabolario |
| **T2** Valore enumerato | Etichette dei valori ammessi | L0–L2 | Vocabolario |
| **T3** Risolutore | Significato di un'espressione vaga | L1–L2 | **Definizione** |
| **T4** Metrica | Grandezza calcolata dell'azienda | L2 | **Definizione** |
| **T5** Categoria | Condizione nominata | L2 | **Definizione** |
| **T6** Preferenza | Risoluzione abituale di un'ambiguità | L2–L3 | Vocabolario\* |
| **T7** Riferimento promosso | Percorso esposto come attributo | L1–L2 | Vocabolario |

*\* T6 è vocabolario perché non cambia il risultato di interrogazioni esistenti: agisce sulle interpretazioni future. Resta però la voce più vicina al confine, ed è la ragione della regola prudenziale di §3.7.*

---

## 4. Vocabolario e Definizione

### 4.1 La distinzione

> **Vocabolario:** allarga ciò che il sistema riconosce. Non cambia il risultato di alcuna interrogazione esistente.
> **Definizione:** stabilisce che cosa significa una grandezza. **Cambia il risultato di ogni interrogazione salvata che vi fa riferimento.**

Il documento sul DSL la anticipa in §15.6; qui diventa il criterio che determina chi può modificare cosa, con quale procedura e con quali conseguenze.

### 4.2 Perché la distinzione è indispensabile

Consideriamo due modifiche apparentemente equivalenti, entrambe legittime, entrambe fatte da un amministratore competente:

**(a)** aggiungere *"agente"* fra i sinonimi di venditore;
**(b)** portare `recent_orders` da 30 a 60 giorni.

La prima non tocca nulla di esistente: interrogazioni salvate, report ricorrenti, corpus di valutazione restano identici. Il sistema riconosce una parola in più.

La seconda **cambia il valore di ogni report ricorrente** che usa *"recente"*. Un responsabile che riceve ogni lunedì lo stesso report vedrà un numero diverso, e nulla nel report glielo dirà.

Trattare (b) come (a) significa consentire che il significato di un dato aziendale cambi senza che nessuno se ne accorga. **È la modalità di guasto più difficile da diagnosticare dell'intero sistema**, perché non produce errori: produce numeri diversi, tutti plausibili.

### 4.3 Governo differenziato

| | Vocabolario | Definizione |
|---|---|---|
| **Chi può modificare** | Amministratore del cliente | Amministratore del cliente, con approvazione dichiarata |
| **Versionamento della voce** | No | **Sì**, con storia completa |
| **Notifica** | No | **Sì**, ai proprietari delle interrogazioni salvate che la usano |
| **Effetto sul corpus** | Nessuno | Riesecuzione richiesta con la nuova versione |
| **Origine da L3** | Approvazione ordinaria | **Mai automatica** (§2.3) |
| **Tracciamento** | Registro delle modifiche | Registro + motivazione obbligatoria |

**La notifica ai proprietari è il punto che rende la distinzione operativa e non teorica.** Poiché ogni interrogazione salvata è uno stato che riferisce i termini del dizionario (§9.2 dell'architettura), l'insieme delle interrogazioni interessate da una modifica è **calcolabile in modo esatto**. Non è una stima: è una selezione.

Chi modifica una definizione vede, prima di confermare, quante e quali interrogazioni salvate ne saranno influenzate. È l'informazione che trasforma una modifica avventata in una decisione consapevole.

### 4.4 Interazione con il corpus di valutazione

Il corpus si esegue con una **versione del dizionario fissata** (§13.3 dell'architettura). Una modifica di definizione richiede quindi una riesecuzione, e i due esiti vanno letti separatamente:

- variazione di accuratezza dovuta al **modello** → riguarda l'interpretazione;
- variazione dovuta al **dizionario** → riguarda la semantica.

Confonderle porta a conclusioni sbagliate in entrambe le direzioni: un arricchimento del dizionario che migliora l'accuratezza viene attribuito al modello, e un cambio di modello che la peggiora viene mascherato da un arricchimento contemporaneo. Il rimedio è elementare e va imposto come regola: **non si modificano dizionario e modello nello stesso rilascio.**

---

## 5. Costruzione del Catalogo

### 5.1 Il compito

Il Catalogo è l'insieme dei riferimenti che l'Interprete può nominare per **un dato utente e una data richiesta** (§4.2 dell'architettura). Deve essere simultaneamente:

- **completo** rispetto a ciò che serve — ogni riferimento mancante è accuratezza perduta per sempre (**RC3**);
- **compatto** — un catalogo grande costa, rallenta e **peggiora l'interpretazione**;
- **filtrato sui permessi** — è la frontiera di autorizzazione (**V2**);
- **deterministico** — altrimenti introduce un secondo punto probabilistico non misurato.

I quattro requisiti sono in tensione. Le sezioni che seguono descrivono come vengono conciliati.

### 5.2 Esposizione: perché lo schema Odoo non è un catalogo

La verifica sui sorgenti quantifica il problema:

| Fonte | Campi |
|---|---|
| `sale.order`, campi propri | **61** |
| `mail.thread` + `mail.activity.mixin` | **~20** (`message_ids`, `message_follower_ids`, `message_needaction_counter`, `message_has_error`, `activity_ids`, `activity_state`, …) |
| Campi di base | ~6 (`create_uid`, `create_date`, `write_uid`, `write_date`, `id`, `display_name`) |
| **Totale** | **oltre 85** |

Di questi, gli attributi che un utente potrebbe nominare in una frase sono nell'ordine dei venti.

Riversare tutti gli 85 nel catalogo produce tre danni simultanei: consuma il budget, aumenta latenza e costo, e **peggiora l'accuratezza** — un modello a cui si offre `message_needaction_counter` accanto a `importo_totale` ha più modi di sbagliare, non più capacità di indovinare.

Ogni attributo ha quindi uno stato di **esposizione**, derivato da regole deterministiche e correggibile in L2.

### 5.3 Regole di esposizione

Applicate in ordine; la prima che corrisponde decide.

| # | Regola | Esito |
|---|---|---|
| 1 | Campo dichiarato in L2 come esposto o nascosto | **Decisione del cliente, prevale** |
| 2 | Campo di sistema (`create_uid`, `write_date`, `id`, …) | Nascosto |
| 3 | Campo di mixin tecnico (messaggistica, attività, valutazioni) | Nascosto |
| 4 | Tipo non interrogabile in modo utile (binario, HTML) | Nascosto |
| 5 | Non memorizzato **e** non ricercabile | Nascosto — non è filtrabile né ordinabile |
| 6 | Etichetta assente, o coincidente con il nome tecnico | Nascosto — non è nominabile in linguaggio naturale |
| 7 | Campo dichiarato in L1 come rilevante per il dominio | **Esposto** |
| 8 | Campo presente nelle viste predefinite dell'entità | **Esposto** |
| 9 | Ogni altro caso | Esposto con priorità bassa (§5.4) |

**La regola 8 è la più produttiva.** I campi che Odoo mostra nelle viste lista e form predefinite sono quelli che i progettisti del modulo hanno giudicato rilevanti per l'utente: è un giudizio di pertinenza già espresso, gratuito e allineato per costruzione a ciò che gli utenti vedono ogni giorno.

**La regola 5 elimina una classe di guasti tardivi.** Un campo calcolato non memorizzato non può essere filtrato né ordinato dall'ORM. Se entrasse nel catalogo, il modello potrebbe usarlo legittimamente e il fallimento emergerebbe solo in esecuzione, con un errore incomprensibile. Escluderlo a monte trasforma un guasto in una non-possibilità.

### 5.4 Budget e ordinamento

Se un'entità supera il budget di attributi esposti, si applica un ordinamento deterministico:

1. attributi dichiarati in L2 dal cliente;
2. attributi presenti nelle viste predefinite;
3. attributi con **frequenza d'uso storica** nelle interrogazioni di quell'installazione;
4. attributi dichiarati rilevanti in L1;
5. i rimanenti, in ordine stabile.

Il terzo criterio è l'unico che migliora nel tempo, e chiude un anello utile: **gli attributi che gli utenti nominano di più diventano quelli che il sistema espone per primi.** È misurabile e deterministico — è una frequenza calcolata dal Registro, non una previsione.

**Nota sul budget.** Con le regole di §5.3, la maggior parte delle entità resta ampiamente sotto qualunque soglia ragionevole: 85 campi si riducono a poche decine. Il budget è una protezione per i casi estremi — entità molto personalizzate — non il meccanismo ordinario.

### 5.5 Fase A — Corrispondenza lessicale deterministica

Quando l'entità non è nota (primo turno o dopo `reset`), il sistema tenta prima di determinarla **senza chiamare il modello**.

```
richiesta   "mostrami le fatuere scadute"
   │
   ▼ normalizzazione
   minuscole · accenti rimossi · punteggiatura rimossa · tokenizzazione
   │
   ▼ confronto con l'indice dei termini T1 delle entità
   corrispondenza esatta        peso 1,00
   corrispondenza su forma base peso 0,90     (plurali, forme flesse)
   corrispondenza approssimata  peso 0,70     (distanza di edit ≤ 1, parole ≥ 5 caratteri)
   │
   ▼ decisione
   migliore ≥ SOGLIA  e  (migliore − secondo) ≥ MARGINE   → entità determinata
   altrimenti                                             → Fase B
```

**Le due condizioni della decisione sono entrambe necessarie**, e la seconda è quella che protegge dal rischio R1.

Una corrispondenza forte non basta: se *"ordine"* corrisponde bene sia a *ordini di vendita* sia a *ordini di acquisto*, scegliere il migliore per un margine minimo significa **indovinare in silenzio**. Il requisito di margine trasforma quel caso in un chiarimento, che costa all'utente un istante e al sistema una domanda onesta.

**Sulla corrispondenza approssimata.** È deterministica — la distanza di edit è una funzione, non una stima — ma va usata con prudenza: mai applicata a un termine che corrisponde già esattamente a qualcos'altro, e mai su parole brevi, dove una singola sostituzione cambia parola anziché correggere un errore di battitura.

**Effetto atteso.** La maggior parte delle richieste di apertura contiene il nome dell'entità (*"mostrami i clienti"*, *"le fatture scadute"*, *"gli ordini di marzo"*). Il percorso rapido dovrebbe coprirne la maggioranza, eliminando una chiamata al modello, il suo costo e la sua latenza. **La quota di casi risolti in Fase A è un indicatore da sorvegliare** (§6.4): la sua crescita misura direttamente l'efficacia del dizionario.

### 5.6 Fase B — Determinazione dell'entità con il modello

Quando la Fase A non decide, l'Interprete riceve un catalogo ridotto: **solo i nomi delle entità**, con le rispettive denominazioni e sinonimi. Nessun attributo.

È un catalogo piccolo — centinaia di voci brevi — e il compito è circoscritto: scegliere un elemento da un elenco. È la classe di compito in cui i modelli sono più affidabili.

### 5.7 Fase C — Catalogo completo dell'entità

Nota l'entità, il catalogo contiene:

- **tutti** i suoi attributi esposti, con termini e tipi;
- i valori ammessi degli attributi enumerati (T2);
- gli attributi raggiungibili con un salto di relazione, limitati a quelli dichiarati percorribili;
- i riferimenti promossi (T7);
- le metriche e le categorie applicabili (T4, T5);
- l'elenco dei nomi di entità, per consentire un cambio di argomento.

> **Proprietà decisiva: in Fase C non c'è selezione.** Tutti gli attributi esposti dell'entità sono presenti. La copertura sugli attributi è quindi **esatta per costruzione**, e l'unico punto di possibile perdita resta la determinazione dell'entità (Fasi A/B), che è un problema piccolo, isolato e misurabile a parte.

È il beneficio architetturale del vincolo di entità singola del contratto, già anticipato in §7.2 dell'architettura: qui è ciò che consente di dichiarare che **non esiste un secondo componente probabilistico non misurato** nel percorso.

### 5.8 Cambio di entità in conversazione

L'elenco dei nomi di entità è sempre presente nel catalogo, anche in Fase C. Quando il modello emette `set_target` verso un'entità diversa, lo stato riparte (§6.2 del DSL) e il turno successivo riceverà il catalogo completo della nuova entità.

**Conseguenza da accettare:** il turno che cambia entità dispone dei nomi ma non degli attributi della nuova entità. Una richiesta come *"passa alle fatture, solo quelle scadute"* può quindi richiedere una seconda interpretazione. È un costo raro e preferibile all'alternativa — trasmettere gli attributi di tutte le entità — che riporterebbe il problema di dimensione da cui la strategia a fasi esiste per liberarsi.

### 5.9 Filtro sui permessi

Applicato **prima** della selezione e del budget, mai dopo (§7.4 dell'architettura).

Un catalogo selezionato e poi filtrato potrebbe risultare più povero del previsto senza che nulla lo segnali: il budget sarebbe stato speso su attributi successivamente rimossi, e la perdita di copertura risulterebbe invisibile — attribuita al budget anziché ai permessi.

---

## 6. Copertura

### 6.1 Definizione

> **Copertura del catalogo** = percentuale di casi in cui **tutti** i riferimenti necessari all'interpretazione corretta erano presenti nel catalogo fornito all'Interprete.

Il quantificatore *tutti* è essenziale: un caso in cui manca un solo riferimento su cinque è un caso scoperto, perché l'interpretazione corretta resta irraggiungibile.

### 6.2 Come si calcola

Il calcolo è deterministico e non richiede giudizio umano, perché entrambi i termini del confronto sono strutturati:

```
caso del corpus
   ├─ interpretazione attesa  →  insieme dei riferimenti necessari
   └─ catalogo registrato     →  insieme dei riferimenti disponibili
                                   (il Registro conserva il catalogo fornito, §4.9 arch.)
copertura del caso = necessari ⊆ disponibili
```

È possibile solo perché il Registro conserva il catalogo di ogni interazione. Se non lo facesse, la copertura sarebbe ricostruibile solo per approssimazione — e un indicatore approssimato non può fare da soglia.

### 6.3 Scomposizione obbligatoria

La copertura complessiva è poco utile da sola. Va scomposta, perché le due componenti hanno cause e rimedi diversi:

| Componente | Cosa misura | Fase | Rimedio se bassa |
|---|---|---|---|
| **Copertura dell'entità** | L'entità corretta era determinabile | A / B | Arricchire i termini T1 delle entità |
| **Copertura degli attributi** | Tutti gli attributi necessari erano esposti | C | Rivedere l'esposizione (§5.3) o il budget |

**La seconda dovrebbe essere prossima al 100% per costruzione** (§5.7): in Fase C non c'è selezione. Un valore sensibilmente inferiore non indica un problema di selezione ma un **errore nelle regole di esposizione** — un attributo utile classificato come tecnico, oppure un budget tarato troppo stretto. È una diagnosi precisa, ed è il motivo per cui la scomposizione è obbligatoria e non facoltativa.

### 6.4 Indicatori correlati

| Indicatore | Lettura |
|---|---|
| **Quota risolta in Fase A** | Efficacia del dizionario sulle entità; la sua crescita riduce costo e latenza |
| **Dimensione media del catalogo** | Se cresce, esposizione troppo permissiva |
| **Fallimenti di validazione di livello 3** | Riferimenti nominati e inesistenti: lacune del dizionario (§12.4 del DSL) |
| **Chiarimenti per termine** | Termini ricorrenti non ancora mappati |
| **Rifiuti per budget** | Se non trascurabili, entità che superano la soglia |

### 6.5 Leggere copertura e accuratezza insieme

È la ragione per cui la copertura è una metrica di primo livello. Le due misure lette insieme producono una diagnosi; lette separatamente, portano sistematicamente a intervenire nel posto sbagliato.

| | **Copertura alta** | **Copertura bassa** |
|---|---|---|
| **Accuratezza alta** | Sistema in salute. Sorvegliare | Situazione instabile: il modello sta indovinando. Peggiorerà con dati più vari |
| **Accuratezza bassa** | Problema di **interpretazione**: prompt, modello, ambiguità del contratto | Problema **semantico**: dizionario ed esposizione. **Lavorare sul modello è tempo sprecato** |

Il quadrante in basso a destra è quello che si presenta più spesso all'inizio, ed è quello in cui l'errore diagnostico è più costoso: si cambia modello, si riscrivono i prompt, non cambia nulla, e la causa resta a monte, invisibile.

Il quadrante in alto a destra è il più insidioso perché non produce sintomi: il sistema funziona bene su un insieme ristretto di casi mentre la copertura è insufficiente. Regredirà appena il linguaggio degli utenti si allargherà, e la regressione apparirà inspiegabile.

### 6.6 Soglia

**Copertura complessiva ≥ 99%.** La soglia è alta perché la copertura è un **limite superiore**: ogni punto perduto qui è un punto che l'accuratezza non potrà mai recuperare, per quanto migliori il modello.

Non è irrealistica proprio grazie a §5.7: la componente attributi è esatta per costruzione, quindi la soglia grava quasi interamente sulla determinazione dell'entità — un problema circoscritto, con un rimedio noto e a costo lineare, cioè arricchire i termini T1.

---

## 7. Attivazione di un Cliente

### 7.1 Il problema del giorno zero

Il rischio **R4** del documento di visione: la qualità peggiore si presenta nel momento in cui si forma la fiducia. Un dizionario vuoto significa entità non riconosciute, chiarimenti continui, e un utente che dopo tre tentativi torna all'interfaccia che conosce.

L'attivazione è quindi **parte del prodotto**, non un'attività di servizio (raccomandazione §18.9 del documento di visione). L'obiettivo è che il primo giorno non parta da zero.

### 7.2 Le quattro fonti, in ordine di costo

| # | Fonte | Costo | Copre |
|---|---|---|---|
| 1 | Introspezione dei metadati (L0) | **Nullo** | Entità, attributi, valori enumerati, tutti tradotti |
| 2 | Estrazione dagli artefatti del cliente | **Nullo** | Gergo aziendale già presente nell'installazione |
| 3 | Pacchetto base di dominio (L1) | Nullo per il cliente | Sinonimi comuni, risolutori, forme colloquiali |
| 4 | Intervista guidata | **Ore-uomo** | Metriche e categorie: ciò che nessuna fonte può dedurre |

Le prime tre sono automatiche. La quarta è irriducibile, e va concentrata su ciò che solo una persona può dire.

### 7.3 Estrazione dagli artefatti — la fonte sottovalutata

I filtri salvati sono voci di dizionario già scritte dagli utenti. La struttura verificata di `ir.filters` fornisce tutto ciò che serve:

| Campo | Riferimento | Cosa se ne ricava |
|---|---|---|
| `name` | `ir_filters.py:14` | **Il termine scelto da una persona** |
| `model_id` | `ir_filters.py:21` | L'entità a cui si riferisce |
| `domain` | `ir_filters.py:18` | La condizione che lo definisce |
| `context` | `ir_filters.py:19` | I raggruppamenti che interessano |
| `sort` | `ir_filters.py:20` | Gli ordinamenti abituali |
| `user_id` **vuoto** | `ir_filters.py:15–17` | **Filtro pubblico**: lessico dell'organizzazione, non individuale |

Un filtro pubblico chiamato *"Fatture scadute"* produce direttamente una proposta di **categoria (T5)**: termine, entità, condizione. Un filtro *"Ordini da evadere"* fa lo stesso per un concetto che non esiste in nessun campo del database ma che tutti in azienda usano.

**Il campo `user_id` è il discriminante di qualità.** Un filtro pubblico è stato reso disponibile a tutti: è vocabolario condiviso, ed è la proposta più affidabile. Un filtro privato riflette l'abitudine di una persona e vale come segnale più debole, da proporre con priorità inferiore.

Altre fonti dello stesso genere: le etichette dei campi personalizzati — che in un'installazione con personalizzazioni sono il gergo aziendale scritto per esteso — e i nomi delle voci di menu personalizzate.

**Tutte le proposte così ottenute entrano in L3**, non in L2: sono candidati da approvare (§2.3). Un filtro chiamato *"prova"* o *"mio 2"* non deve diventare vocabolario.

### 7.4 Il pacchetto base

Il fornitore mantiene pacchetti L1 per dominio — vendite, acquisti, contabilità, CRM, magazzino, progetti — contenenti sinonimi comuni, forme colloquiali, abbreviazioni ricorrenti e risolutori predefiniti.

Sono installati **in funzione dei moduli presenti**: un'installazione senza contabilità non riceve il pacchetto contabile.

**È l'asset che si accumula fra i clienti.** Ogni termine osservato presso un cliente e riconosciuto come generale — non specifico di quell'azienda — è candidato a entrare nel pacchetto base e a beneficiare tutti gli altri. È il meccanismo con cui il prodotto migliora con il numero di installazioni, e va gestito come un processo esplicito: senza, il lavoro fatto su ogni cliente resta confinato a quel cliente.

### 7.5 L'intervista guidata

Concentrata su ciò che nessuna introspezione può dedurre. **Non si chiedono sinonimi** — quelli arrivano dalle fonti automatiche e dall'uso.

Si chiedono:

- **le metriche (T4).** *"Cosa intendete per fatturato? Include le note di credito? Considerate la data di emissione o di competenza?"* Sono le domande dalle quali dipende la correttezza dei numeri.
- **le categorie (T5).** *"Chi è un cliente importante? Quando un ordine è urgente?"*
- **i risolutori (T3).** *"«Recente» per voi quanto è?"*
- **le ambiguità note.** *"Quando dite «Rossi», di solito intendete il cliente o il venditore?"*

Poche domande, alto valore, ed è esattamente il perimetro delle **definizioni** (§4): il tipo di voce che nessun meccanismo automatico può proporre e che va decisa da chi ha l'autorità per farlo.

### 7.6 La prima settimana

L'attivazione non finisce al collaudo. La prima settimana di uso reale è la fonte più ricca del dizionario, ed è anche il momento in cui l'intervento è più efficace: gli utenti stanno formando il proprio giudizio.

Il ciclo: chiarimenti e fallimenti di livello 3 vengono raccolti quotidianamente, aggregati per termine, approvati in blocco. La qualità percepita migliora visibilmente giorno per giorno — che è, oltre a un beneficio tecnico, il modo più efficace per costruire fiducia in un prodotto che ha appena chiesto un atto di fiducia.

### 7.7 Criterio di completamento

L'attivazione è completa quando, sulle attività di riferimento concordate con il cliente:

1. la **copertura dell'entità** supera la soglia (§6.6);
2. le metriche e le categorie nominate dagli utenti nella prima settimana sono definite;
3. le proposte L3 con frequenza rilevante sono state esaminate;
4. la quota risolta in Fase A è misurata e stabile;
5. il cliente sa come modificare il proprio dizionario in autonomia.

**Il punto 5 non è un dettaglio di formazione.** Un dizionario che solo il fornitore può modificare diventa il collo di bottiglia descritto dal rischio RC2: ogni esigenza del cliente entra in una coda esterna, e il tempo di risposta si misura in settimane.

---

## 8. Arricchimento dall'Uso

### 8.1 Le sorgenti di segnale

Il dizionario cresce con l'uso. Il Registro fornisce cinque segnali, tutti strutturati e tutti già disponibili senza strumentazione aggiuntiva:

| Segnale | Cosa indica | Tipo di proposta |
|---|---|---|
| **Chiarimento risolto** | Un'ambiguità ricorrente e come viene sciolta | T6, talvolta T1 |
| **Fallimento di livello 3** | Un termine nominato che il dizionario non conosce | T1 |
| **Correzione dell'interpretazione** | Il sistema ha compreso, ma non ciò che l'utente intendeva | T1, T6 |
| **Riformulazione immediata** | La prima interpretazione non è servita | Diagnostico |
| **`out_of_scope` ricorrente** | Una capacità mancante, non una lacuna del dizionario | Priorità di prodotto |

L'ultima riga non alimenta il dizionario: alimenta le priorità del contratto (§11.4 del DSL). Va tenuta distinta, perché confondere *"non conosco questa parola"* con *"non so fare questa cosa"* porta ad arricchire il dizionario per un problema che il dizionario non può risolvere.

### 8.2 Dal segnale alla proposta

```
eventi del Registro
   │
   ▼ aggregazione per termine normalizzato
   │
   ▼ soglia di frequenza          (un evento isolato non è un segnale)
   │
   ▼ tipizzazione                 (T1 · T6 automatiche · T3/T4/T5 solo segnalate)
   │
   ▼ ordinamento per impatto      (frequenza × utenti distinti coinvolti)
   │
   ▼ CODA L3 — proposte in attesa di approvazione
```

**L'ordinamento per impatto è ciò che rende l'approvazione sostenibile.** Il consulente non esamina eventi ma una lista di termini ordinata: le prime dieci voci coprono abitualmente la maggior parte dei chiarimenti. Il lavoro è di minuti, non di giornate, e ha un effetto immediatamente misurabile.

Il fattore *utenti distinti* nell'impatto è deliberato: un termine usato cento volte da una persona è un'abitudine individuale; usato dieci volte da otto persone è lessico organizzativo.

### 8.3 Cosa può essere proposto, e con quale autorità

| Tipo | Proposta automatica | Perché |
|---|---|---|
| **T1** Denominazione | **Sì**, con valore | Il termine osservato e il riferimento scelto sono entrambi noti |
| **T2** Valore enumerato | **Sì**, con valore | Idem |
| **T6** Preferenza | **Sì**, con valore | La distribuzione delle scelte è un dato di fatto |
| **T7** Riferimento promosso | **Sì**, con valore | Il percorso usato di frequente è osservabile |
| **T3** Risolutore | **Solo segnalazione** | *"«recente» è usato spesso e non è definito"* — il valore no |
| **T4** Metrica | **Solo segnalazione** | Nessun automatismo può stabilire cosa entra nel fatturato |
| **T5** Categoria | **Solo segnalazione**\* | Idem |

*\* Con un'eccezione dichiarata: le categorie estratte dai filtri salvati (§7.3) sono proposte **con** la loro definizione, perché la condizione proviene da un artefatto che un utente dell'azienda ha creato deliberatamente. Non è un'inferenza del sistema: è la lettura di una definizione già scritta.*

La distinzione ricalca §4: **il sistema può proporre vocabolario, mai definizioni.** È lo stesso confine che vieta al modello di definire una metrica (§8.5 del DSL), applicato al meccanismo di apprendimento.

### 8.4 Sorvegliare l'apprendimento

Il rischio di rinforzo descritto in §2.3 — un apprendimento errato che si consolida perché nessuno lo contraddice — non è eliminato dall'approvazione umana: un'approvazione frettolosa lo lascia passare.

Due indicatori lo intercettano:

- **tasso di correzione delle interpretazioni che dipendono da voci promosse da L3**, confrontato con quello generale. Se è più alto, l'approvazione sta lasciando passare voci sbagliate;
- **voci promosse e successivamente rimosse**, con il tempo trascorso. Un valore elevato indica che il processo di approvazione è troppo permissivo.

Nessuno dei due richiede strumentazione nuova: il Registro conserva già quale voce ha contribuito a ciascuna interpretazione.

### 8.5 Ciò che non si apprende mai

| Non appreso | Perché |
|---|---|
| Definizioni di metriche | Convenzioni aziendali; nessun dato le contiene |
| Soglie delle categorie | Idem |
| Valori dei risolutori | Un valore inventato produrrebbe un sistema che risponde con sicurezza a domande mai poste a nessuno |
| Preferenze legate al singolo utente | Il dizionario non conosce gli utenti (§2.5) |
| Termini da fonti non fidate | L'arricchimento è un percorso verso il contesto del modello (§12.4 arch.) |

---

## 9. Versionamento e Ciclo di Vita

### 9.1 La versione del dizionario

Ogni installazione ha una **versione del dizionario** monotona crescente, indipendente dalla versione del contratto DSL (§15.5 del DSL: i due assi si muovono separatamente).

| Evento | Incrementa la versione |
|---|---|
| Aggiunta o modifica di una voce di **vocabolario** | Sì |
| Aggiunta o modifica di una voce di **definizione** | Sì, con storia della voce (§9.2) |
| Promozione di una proposta da L3 | Sì |
| Rigenerazione di L0 dopo un aggiornamento dei moduli | Sì |
| Aggiornamento di un pacchetto base L1 | Sì |

**La versione serve a tre scopi**: fissare il corpus (§13.3 arch.), invalidare la memorizzazione dei cataloghi (§7.6 arch.), e rendere attribuibile una variazione di accuratezza al dizionario anziché al modello (§4.4).

### 9.2 Storia delle definizioni

Le voci di definizione (T3, T4, T5) conservano la storia completa: valore precedente, nuovo valore, autore, data, motivazione, e **l'elenco delle interrogazioni salvate interessate** al momento della modifica.

L'ultimo elemento è ciò che rende la storia utile a posteriori. Quando fra sei mesi qualcuno chiederà perché un report mostra un numero diverso da quello di marzo, la risposta è una selezione, non un'indagine.

### 9.3 Rigenerazione di L0 e voci orfane

L0 è rigenerato a ogni aggiornamento dei moduli. Un aggiornamento può rimuovere o rinominare un campo a cui una voce L2 fa riferimento.

> **Regola: una voce che non risolve più viene sospesa, mai cancellata.**

Una voce sospesa non partecipa al catalogo, compare in un elenco diagnostico con la causa, e resta modificabile. Le interrogazioni salvate che la usano producono un errore di risoluzione **diagnosticabile** (§7.4 arch.), non un risultato silenziosamente diverso.

La cancellazione automatica sarebbe l'alternativa comoda e sbagliata: eliminerebbe la traccia del problema insieme al problema, e un'interrogazione salvata smetterebbe di funzionare senza che nessuno sappia perché.

### 9.4 Ripristino

Poiché ogni versione è uno stato completo del dizionario, il ripristino a una versione precedente è possibile. È una funzione di emergenza, non di lavoro ordinario, ma va prevista: **una modifica di definizione errata può alterare i numeri di un'intera organizzazione**, e il tempo che intercorre fra l'accorgersene e il rimediare deve essere breve.

### 9.5 Il dizionario nel ciclo di rilascio

| Regola | Motivazione |
|---|---|
| Non si modificano dizionario e modello nello stesso rilascio | Attribuzione delle variazioni (§4.4) |
| Il corpus si riesegue a ogni cambio di versione del dizionario | Rilevare le regressioni semantiche |
| Le modifiche di definizione sono annunciate prima di essere applicate | I destinatari sono noti (§9.2) |
| I pacchetti L1 non sovrascrivono mai L2 | Precedenza di §2.2 |

---

## 10. Multilingua

### 10.1 Il punto di partenza è favorevole

`ir.model.fields.field_description` e `ir.model.name` sono `translate=True` (`ir_model.py:555`, `ir_model.py:217`). **L0 nasce quindi tradotto in tutte le lingue attive dell'installazione**, senza alcun lavoro.

È un vantaggio sostanziale: la base del dizionario — la parte più numerosa — è multilingua per costruzione.

### 10.2 Termini per lingua

Le voci T1 e T2 associano termini a una lingua. La lingua dell'utente proviene dalla sua configurazione Odoo e determina la **priorità**, non l'esclusività.

### 10.3 Richieste in lingua mista

Il documento di visione elenca fra i requisiti *"mostrami i deal in stage negotiation"*: italiano nella struttura, inglese nei termini di dominio. È il modo in cui si parla realmente in molte aziende.

> **L'indice dei termini è unico e attraversa le lingue.** Non esiste un indice per lingua fra cui scegliere.

Se esistessero indici separati, il sistema dovrebbe prima determinare la lingua della frase — un compito ambiguo su una frase mista, e un punto di guasto in più. Un indice unico rende la questione irrilevante: *"deal"* e *"trattativa"* portano allo stesso riferimento, e nessuno deve decidere in che lingua stia parlando l'utente.

La lingua dell'utente interviene solo come criterio di ordinamento a parità di corrispondenza, e nella lingua in cui l'interpretazione viene mostrata.

### 10.4 Gergo intraducibile

Molto gergo aziendale non ha lingua: sigle interne, codici di prodotto, nomi di processi. Entra in L2 senza attributo di lingua e vale per tutte.

È un caso frequente e va previsto fin dall'inizio: obbligare a scegliere una lingua per un termine che non ne ha produrrebbe voci duplicate in ogni lingua attiva, con il conseguente disallineamento alla prima modifica.

---

## 11. Governo e Responsabilità

### 11.1 Chi possiede cosa

| Livello | Proprietario | Può modificare | Note |
|---|---|---|---|
| **L0** Derivato | Nessuno | Generato | Le correzioni si scrivono in L2 |
| **L1** Base | **Fornitore** | Fornitore | Distribuito con il prodotto, per dominio |
| **L2** Cliente | **Cliente** | Amministratore del cliente | Prevale sempre su L1 e L0 |
| **L3** Proposte | — | Approvazione → L2 | Non attivo |

### 11.2 Due diritti distinti

> Il diritto di modificare il **vocabolario** e quello di modificare le **definizioni** sono separati.

Il primo è di uso quotidiano e a basso rischio: aggiungere un sinonimo, approvare proposte L3, correggere l'esposizione di un attributo. Può essere assegnato ampiamente — a un key user, a chi presidia il prodotto internamente.

Il secondo cambia il significato dei numeri aziendali. Va assegnato a poche persone che hanno l'autorità per stabilire cosa significa *"fatturato"* nella loro organizzazione: tipicamente il controllo di gestione, non l'amministratore di sistema.

**Unire i due diritti è la scelta comoda e sbagliata.** Renderebbe la persona che aggiunge sinonimi ogni settimana anche quella che può ridefinire il fatturato — e la modifica avverrebbe con la stessa disinvoltura della prima, che è appropriata solo per la prima.

### 11.3 Tracciabilità

Ogni modifica registra autore, data, valore precedente e nuovo, livello e tipo. Per le definizioni si aggiungono motivazione obbligatoria e insieme delle interrogazioni salvate interessate (§9.2).

Non è un requisito di conformità: è ciò che consente di rispondere fra sei mesi alla domanda *"perché questo numero è cambiato"* con una selezione anziché con un'indagine.

---

## 12. Rischi

### RS1 — Il dizionario diventa un collo di bottiglia
**Descrizione.** Ogni esigenza richiede un intervento del fornitore; la coda cresce; i tempi di risposta si misurano in settimane.
**Impatto.** Alto: costo di esercizio crescente e insoddisfazione su richieste banali.
**Mitigazione.** Autonomia del cliente come criterio di completamento dell'attivazione (§7.7, punto 5); proposte automatiche ordinate per impatto (§8.2); pacchetti L1 che capitalizzano il lavoro fra clienti.
**Segnale.** Richieste di modifica al dizionario in coda presso il fornitore.

### RS2 — L'apprendimento si auto-rinforza
**Descrizione.** Una corrispondenza errata viene appresa, applicata, non contraddetta, e diventa la normalità.
**Impatto.** Alto: l'errore si consolida e nessun indicatore aggregato lo mostra.
**Mitigazione.** L3 non attivo (§2.3); i due indicatori di §8.4; nessuna definizione appresa automaticamente (§8.3).
**Segnale.** Tasso di correzione più alto sulle interpretazioni che dipendono da voci promosse.

### RS3 — Una definizione cambia in silenzio
**Descrizione.** Una modifica a T3, T4 o T5 altera i risultati di report ricorrenti senza che i destinatari lo sappiano.
**Impatto. Critico.** Non produce errori: produce numeri diversi, tutti plausibili. È la forma di R1 con l'impatto maggiore, perché riguarda dati aggregati usati per decidere.
**Mitigazione.** Distinzione di §4 con governo differenziato; notifica ai proprietari delle interrogazioni interessate; diritti separati (§11.2); storia completa (§9.2).
**Segnale.** Modifiche di definizione senza motivazione registrata.

### RS4 — Esposizione troppo permissiva
**Descrizione.** Il catalogo si gonfia di attributi tecnici; l'accuratezza peggiora e il costo cresce.
**Impatto.** Medio-alto, e insidioso perché il sintomo — accuratezza in calo — suggerisce un problema di modello.
**Mitigazione.** Regole deterministiche di §5.3; sorveglianza della dimensione media del catalogo (§6.4).
**Segnale.** Dimensione media del catalogo in crescita a parità di installazione.

### RS5 — L'attivazione è trattata come servizio
**Descrizione.** Il percorso di §7 viene improvvisato dal consulente di turno.
**Impatto.** Alto: il giorno zero determina l'adozione, e un prodotto eccellente con un'attivazione improvvisata viene giudicato per l'attivazione (§18.9 del documento di visione).
**Mitigazione.** Attivazione come componente del prodotto, con estrazione automatica, pacchetti base, intervista strutturata e criterio di completamento verificabile.
**Segnale.** Attivazioni con esiti molto diversi fra clienti simili.

### RS6 — L1 non capitalizza
**Descrizione.** Il lavoro sul dizionario di ogni cliente resta confinato a quel cliente; il pacchetto base non cresce.
**Impatto.** Medio-alto sul lungo periodo: ogni nuovo cliente riparte dallo stesso punto, e il fossato competitivo non si forma.
**Mitigazione.** Processo esplicito di promozione dei termini generali da L2 a L1 (§7.4), con revisione periodica.
**Segnale.** Pacchetti L1 fermi alla versione iniziale dopo diversi clienti attivati.

### RS7 — La Fase A sbaglia entità in silenzio
**Descrizione.** Soglia o margine tarati troppo permissivamente: il percorso rapido sceglie l'entità sbagliata senza chiedere.
**Impatto. Alto.** È un fraintendimento plausibile prodotto da un componente deterministico — quindi non attribuibile al modello e difficile da sospettare.
**Mitigazione.** Requisito di margine oltre alla soglia (§5.5); misura separata dell'accuratezza sulla determinazione dell'entità in Fase A rispetto alla Fase B.
**Segnale.** Accuratezza sull'entità inferiore nei casi risolti in Fase A rispetto a quelli passati per il modello. **È il confronto da tenere sempre sotto osservazione**: se il percorso rapido è meno accurato del percorso lento, sta scambiando correttezza per velocità.

### RS8 — La copertura è misurata solo in aggregato
**Descrizione.** Si riporta un unico valore invece della scomposizione fra entità e attributi.
**Impatto.** Medio-alto sulla capacità diagnostica: si perde l'informazione che indica dove intervenire.
**Mitigazione.** Scomposizione obbligatoria (§6.3); matrice diagnostica di §6.5 adottata come strumento di lettura.
**Segnale.** Rapporti sulla qualità con un solo numero di copertura.

---

## 13. Decisioni Richieste

Numerazione in continuità (D1–D27).

| # | Decisione | Raccomandazione | Risolve |
|---|---|---|---|
| **D28** | Quattro livelli con precedenza L2 › L1 › L0; **L3 non attivo** (§2) | **Adottare** | — |
| **D29** | Distinzione vocabolario / definizione con governo differenziato (§4) | **Adottare** | **D17** |
| **D30** | Sette tipi di voce, vocabolario chiuso (§3) | **Adottare** | — |
| **D31** | Regole di esposizione di §5.3 e budget di §5.4 | **Adottare** come valori iniziali | — |
| **D32** | Strategia a tre fasi A / B / C per il catalogo (§5.5–5.7) | **Adottare** | **D16**, **D21** |
| **D33** | In Fase A servono soglia **e** margine; senza margine si cede alla Fase B (§5.5) | **Adottare** | — |
| **D34** | Copertura scomposta entità/attributi, soglia ≥ 99% (§6) | **Adottare** | **D22** |
| **D35** | Attivazione come componente del prodotto, con estrazione da `ir.filters` (§7) | **Adottare** | — |
| **D36** | Versione del dizionario; voci orfane **sospese, mai cancellate** (§9) | **Adottare** | — |
| **D37** | Indice dei termini unico e multilingua (§10.3) | **Adottare** | — |
| **D38** | Diritti separati per vocabolario e definizioni (§11.2) | **Adottare** | — |

**D29, D32 e D34 sono le decisioni bloccanti.** D29 determina il governo di tutto il resto; D32 chiude la questione aperta più a lungo del progetto (RC3, il tetto di accuratezza); D34 rende quella chiusura verificabile invece che asserita.

---

## 14. Glossario

| Termine | Definizione |
|---|---|
| **Dizionario Semantico** | Mappa curata e versionata fra il linguaggio dell'organizzazione e la struttura dei suoi dati |
| **Livello** | Strato del dizionario: L0 derivato, L1 base, L2 cliente, L3 proposte |
| **Vocabolario** (classe) | Voce che allarga ciò che il sistema riconosce, senza cambiare risultati esistenti |
| **Definizione** (classe) | Voce che stabilisce il significato di una grandezza; cambia i risultati delle interrogazioni che la usano |
| **Esposizione** | Stato di un attributo: nominabile dal modello oppure no |
| **Catalogo** | Insieme dei riferimenti nominabili per un utente e una richiesta; effimero, filtrato sui permessi |
| **Fase A / B / C** | Determinazione lessicale dell'entità · determinazione con il modello · catalogo completo dell'entità |
| **Margine** | Distanza minima fra la migliore e la seconda corrispondenza in Fase A |
| **Copertura** | Percentuale di casi in cui tutti i riferimenti necessari erano nel catalogo fornito |
| **Voce sospesa** | Voce che non risolve più dopo un aggiornamento; inattiva ma conservata e diagnosticabile |
| **Proposta** | Candidato in L3, in attesa di approvazione; mai attivo |

---

## Chiusura

Il dizionario è la parte del prodotto che non si può scrivere una volta sola. Cresce, si corregge e si differenzia per cliente: è la ragione per cui è un asset difendibile ed è anche la ragione per cui richiede un governo, non solo una struttura dati.

Due decisioni portano il peso maggiore.

La prima è la distinzione fra **vocabolario e definizione**. Aggiungere un sinonimo e ridefinire il fatturato sono operazioni che si assomigliano nell'interfaccia e non hanno nulla in comune negli effetti: la prima allarga ciò che il sistema capisce, la seconda cambia i numeri su cui un'organizzazione decide. Governarle allo stesso modo significa lasciare che il significato dei dati aziendali cambi senza che nessuno se ne accorga.

La seconda è la **strategia a tre fasi** del catalogo. Chiude il rischio RC3 — il tetto di accuratezza — non con un compromesso ma con una proprietà: nota l'entità, gli attributi entrano tutti, e la copertura sugli attributi è esatta per costruzione. Ciò che resta è un problema piccolo, isolato e misurabile, ed è misurato.

Entrambe discendono da un vincolo preso altrove per ragioni diverse — una sola entità per interrogazione, nessuna espressione calcolata dal modello. È il segnale che l'impianto regge: le restrizioni accettate a monte continuano a produrre semplificazioni a valle.

**Documenti successivi:**

1. **Piano di Valutazione della Qualità** — corpus, metodo, soglie, copertura, criteri di regressione *(dipende da §6, D34)*
2. **Modello di Sicurezza e Conformità** — identità, autorizzazioni, tracciabilità, trattamento dei dati *(dipende da §12 arch.)*
3. **Linee guida di Esperienza Utente** — interpretazione ispezionabile, stati non ideali, disambiguazione

---

*Fine del documento.*
