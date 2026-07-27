# Strategia del Corpus Fondativo
## Costruire il corpus iniziale senza clienti pilota

---

| Voce | Valore |
|---|---|
| **Titolo** | Strategia del Corpus Fondativo — fonti, metodo, limiti, transizione |
| **Tipo** | Nota tecnica decisionale (ADR) |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Risolve** | La parte di **D7** che non richiede clienti. Specifica `07` §3.3 |
| **Ambito** | Fonti del corpus iniziale; metodo di generazione; perturbazione; bilanciamento; limiti dichiarati; transizione al corpus reale |
| **Fuori ambito** | Il corpus sigillato di **D42**, che richiede utenti reali |
| **Artefatti** | `ai/corpus/estrai_lessico.py` · `ai/corpus/lessico_l1.json` · `ai/corpus/genera_corpus.py` |

> **Vincolo dichiarato dall'Architect (27/07/2026).** Non sono disponibili clienti pilota. Il corpus va costruito senza accesso a utenti che usino Odoo per lavorare.
>
> **Questo documento non aggira il vincolo: lo attraversa dichiarando che cosa resta ottenibile e che cosa no.** La seconda parte è la più importante, ed è in §5.

---

## 1. Executive Summary

### 1.1 La situazione

`07` fonda l'intero impianto di misura su un corpus di richieste reali annotate. `02` fa della Fase 0 il prerequisito di tutto, e il corpus è il suo unico deliverable non ancora prodotto. **D7** è aperta, e il resto della progettazione è chiuso.

Senza clienti, la reazione naturale è rinviare. È la reazione sbagliata, per una ragione quantitativa: **la maggior parte del lavoro del corpus non richiede utenti.**

### 1.2 Che cosa si è rivelato disponibile

La ricognizione ha prodotto numeri che cambiano il quadro. Estratti dai soli sorgenti presenti in `core/`, in pochi secondi e senza alcun giudizio umano:

| Fonte | Quantità | Che cos'è |
|---|---|---|
| File di traduzione italiana | **380** | La lingua ufficiale dell'installazione |
| Entità con denominazione italiana | **813** | Il vocabolario T1 di partenza |
| Attributi esposti con etichetta | **12 411** | Il vocabolario degli attributi, già tradotto |
| Valori enumerati con etichetta | **2 668** | Le voci T2, già tradotte |
| **Filtri nominati nelle viste** | **1 378**, di cui **1 304 tradotti** | Le categorie **T5**, già curate |

L'ultima riga è la più preziosa e la meno ovvia. **D35** aveva individuato negli artefatti esistenti la fonte a costo più basso e qualità più alta; la ricognizione mostra che vale anche **prima** di avere un cliente, perché Odoo stessa dichiara nelle proprie viste di ricerca centinaia di categorie aziendali: *«Da fatturare»*, *«Da riordinare»*, *«Prossime chiusure»*, *«I miei ordini»*. Sono giudizi di pertinenza già espressi da chi ha progettato i moduli, e sono tradotti professionalmente.

### 1.3 Le quattro decisioni portanti

**Il corpus si genera dallo stato alla frase, mai il contrario** (§4.1). È ciò che rende la chiave di risposta corretta **per costruzione** ed elimina il passaggio che senza clienti non è eseguibile: l'annotazione umana.

**La perturbazione linguistica è dichiarata e reversibile** (§4.3). Segue una metodologia pubblicata e validata — Spider-Syn, Spider-Realistic, Spider-DK — non un'invenzione locale.

**Il corpus fondativo non è, e non può essere, un corpus sigillato** (§5.2). Chi scrive il generatore ne conosce la distribuzione. È il limite che nessuna disciplina rimuove, e da cui discende che **D49 resta chiusa**.

**Esiste una terza via che non richiede clienti** (§7): l'elicitazione. Non serve un prodotto attivo né un'installazione: servono persone che facciano quel lavoro. È il salto di qualità più grande disponibile a costo quasi nullo.

---

## 2. Perché non basta scrivere qualche frase

Vale la pena chiudere subito la scorciatoia, perché è quella che verrà proposta.

Un corpus scritto a mano da chi costruisce il prodotto misura una cosa sola: **quanto il sistema capisce il suo autore**. Ha tre difetti simultanei, e nessuno è correggibile con l'impegno.

**È piccolo.** Poche centinaia di frasi al massimo, cioè sotto la soglia di §3.5 di `07`: la variazione di un punto percentuale resta indistinguibile dal rumore, e la regola di regressione zero diventa inapplicabile.

**È distorto verso ciò che si sa già gestire.** Chi scrive conosce il contratto e, senza volerlo, formula richieste esprimibili. Le classi di richieste che il DSL non copre — cioè quelle che alimentano **RC1** e determinano le priorità di ampliamento — non compaiono.

**Non ha una chiave affidabile.** L'autore annota l'interpretazione attesa dopo aver pensato alla frase, spesso guardando che cosa il sistema produce. È il meccanismo descritto da `07` §3.4: l'atteso si allinea al prodotto anziché all'intenzione.

La strategia che segue non elimina la terza difficoltà con la disciplina, ma con l'inversione del procedimento (§4.1).

---

## 3. Le Fonti

### 3.1 L0 — Il vocabolario ufficiale, estratto

**Fonte:** `core/addons/*/i18n/it.po` e le viste di ricerca dei moduli.
**Strumento:** `ai/corpus/estrai_lessico.py`.
**Natura:** deterministica, rigenerabile in modo identico, nessun giudizio.

Produce entità, attributi, valori enumerati e filtri nominati, ciascuno nella forma italiana e in quella originale. È simultaneamente due cose: **il livello L0 del Dizionario** (`06` §2.4) e **il vocabolario della chiave di risposta** del corpus.

Lo strumento applica già le esclusioni deterministiche di `06` §5.3: campi di sistema e campi di mixin tecnico non entrano. È il motivo per cui i 12 411 attributi estratti sono già filtrati e non sono l'intero schema.

**Due difetti rilevati e corretti in fase di realizzazione**, entrambi istruttivi:

- le etichette dei filtri compaiono in inglese nelle viste, perché la traduzione risiede altrove nel file `.po` come voce autonoma. Senza il recupero incrociato, la fonte T5 più preziosa sarebbe stata inutilizzabile in italiano — 1 304 categorie perse;
- il filtro sui campi tecnici si applicava agli attributi ma non ai valori enumerati, che entravano quindi con voci come `activity_state`. Corretto, con una riduzione da 2 971 a 2 668 voci.

Sono difetti minori, e vale la pena registrarli perché mostrano che **l'estrazione automatica non è priva di giudizio**: le regole vanno verificate sull'esito, non solo scritte.

### 3.2 L1 — Il gergo, curato

**Fonte:** glossari di settore italiani e terminologia ricorrente nella comunità Odoo italiana.
**Artefatto:** `ai/corpus/lessico_l1.json`.
**Natura:** curata, versionata, con provenienza dichiarata.

È lo strato che i sorgenti non contengono e non possono contenere. Odoo dice *«Fattura cliente non pagata»*; in azienda si dice *«insoluto»*, *«arretrato»*, *«da incassare»*, *«scaduto»*, *«moroso»*.

Il lessico copre sei famiglie:

| Famiglia | Contenuto |
|---|---|
| Verbi di richiesta | Neutri, colloquiali, interrogativi, ellittici |
| Entità | Sinonimi per entità, **con marcatura del gergo ambiguo** |
| Attributi | Forme nominali e forme interrogative, distinte |
| Categorie (T5) | Termini che valgono una condizione, con la condizione dichiarata |
| Temporali | Puntuali, correnti, precedenti, relativi, assoluti, vaghi |
| Vaghezza | Approssimazione e confronto |

**Due scelte di struttura meritano una nota**, perché sono nate da difetti osservati nel primo generato.

*Le forme nominali sono separate dalle interrogative.* Il sinonimo *«a che punto»* per `state` è corretto in una domanda e assurdo dopo una preposizione — *«raggruppati per a che punto»*. Sono usi diversi dello stesso concetto, e mescolarli produce frasi che nessun italiano scriverebbe.

*Le categorie portano genere e numero.* *«Trattative operativi»* è sbagliato: l'aggettivo va accordato all'entità. Il lessico distingue quindi `termini_m`, `termini_f` e `termini_inv`, dove l'ultimo raccoglie le locuzioni preposizionali — *«da incassare»*, *«in sospeso»* — che sono invarianti.

Un corpus di italiano sgrammaticato insegna a misurare un linguaggio che nessuno usa.

### 3.3 La marcatura del gergo ambiguo

Alcuni termini sono deliberatamente marcati come ambigui: *«pratiche»*, *«lavori»*, *«documenti»*, *«bolle»*, *«deal»*.

Non sono errori del lessico: sono la materia dei casi con esito atteso `clarification`. *«Pratiche»* significa ordini di vendita in un'azienda e progetti in un'altra (`02` §4.4); un sistema che scegliesse senza chiedere starebbe indovinando.

**È l'unico modo di generare casi di chiarimento con chiave affidabile**: l'ambiguità è nel lessico, quindi è dichiarata prima che la frase esista.

---

## 4. Il Metodo

### 4.1 Si genera lo stato, poi si verbalizza

> **Il procedimento è invertito rispetto all'annotazione: prima l'interpretazione attesa, poi la frase che la produrrebbe.**

È la decisione centrale del documento, e risolve il problema che senza clienti sarebbe insolubile.

```
1. si campiona un'entità dal catalogo
2. si campionano 0–3 condizioni, con i vincoli di coerenza di §4.2
3. si campionano raggruppamento, ordinamento, attributi, limite
        │
        ▼  STATO DI INTERROGAZIONE ATTESO   ← è la chiave, ed è corretta
        │                                      per costruzione
        ▼  verbalizzazione con il lessico L1
        │
        ▼  perturbazione dichiarata (§4.3)
        │
        ▼  CASO DEL CORPUS
```

L'annotazione umana serve a stabilire l'interpretazione corretta di una frase esistente. Se la frase è derivata da un'interpretazione, quel passaggio non serve — non perché sia stato automatizzato, ma perché **non c'è nulla da stabilire**.

Ne discende anche che i **riferimenti necessari** di ogni caso — il termine di confronto della copertura (**D34**) — sono noti esattamente, e non stimati.

### 4.2 La coerenza dello stato è un requisito, non una rifinitura

Il primo generato ha prodotto casi come:

> *«dammi merce con disponibilità sotto i 10 000 con disponibilità oltre 500 con disponibilità almeno 1 000»*

Tre condizioni sullo stesso attributo, e due espressioni temporali in conflitto — *«nell'ultimo anno … l'anno scorso»*.

**Non sono frasi brutte: sono casi il cui atteso è sbagliato.** Uno stato incoerente verrebbe respinto dalla validazione di livello 4 (`03` §12.5); un corpus che lo dichiara corretto misurerebbe il sistema contro una risposta che il sistema deve rifiutare.

Vincoli introdotti, tutti verificabili:

- una sola condizione per attributo;
- una sola condizione temporale;
- una categoria non si combina con un'altra che tocca gli stessi attributi implicati;
- il confronto numerico si applica solo ad attributi numerici.

Il controllo automatico su 1 200 casi restituisce **zero stati incoerenti**. È una verifica da mantenere nella generazione, non un'ispezione una tantum.

### 4.3 La perturbazione

I fenomeni linguistici di `02` §10.2 — refusi, abbreviazioni, gergo, sinonimi, frasi incomplete, mescolanza di lingue — vanno esercitati, e vanno esercitati **senza alterare l'interpretazione attesa**.

Il metodo non è originale, ed è un vantaggio: la ricerca su text-to-SQL ha prodotto una famiglia di insiemi di prova costruiti perturbando sistematicamente un insieme di partenza.

| Riferimento | Trasformazione | Nostro corrispettivo |
|---|---|---|
| **Spider-Syn** | Sostituzione con sinonimi dei termini di schema | Sinonimi L1 al posto delle etichette ufficiali |
| **Spider-Realistic** | Rimozione dei nomi di colonna espliciti | Categorie T5 e forme ellittiche |
| **Spider-DK** | Richieste che esigono conoscenza di dominio | Termini che richiedono definizione L2 |

Le trasformazioni applicate sono cinque, ciascuna registrata sul caso: abbreviazione, refuso, mescolanza di lingue, minuscole, rimozione degli accenti. La registrazione è ciò che consente di misurare l'accuratezza **per fenomeno** — cioè di sapere se il sistema cade sui refusi o sul gergo, che è l'informazione utile.

### 4.4 I casi non ideali si generano per costruzione

`07` §3.2 richiede che il corpus contenga esiti diversi da `operations`, e §3.6 ne fissa le quote. Sono generabili tutti:

| Esito | Come si genera | Chiave |
|---|---|---|
| `clarification` | Da termini marcati ambigui in L1 (§3.3) | Il motivo dell'ambiguità è dichiarato |
| `out_of_scope` | Da modelli di richiesta mutante o fuori profilo | La categoria `scope_note` è dichiarata |
| `not_understood` | Da enunciati privi di riferimenti interpretabili | Nessuna |
| Raffinamento | Stato di partenza + una sola operazione | L'operazione è la chiave |

L'ultima riga soddisfa il requisito di **D46** — almeno il 40% di turni di raffinamento — che `07` §3.6 indica come il primo a essere sacrificato, perché con l'annotazione manuale è il più laborioso. Con la generazione costa quanto gli altri.

### 4.5 Che cosa è stato prodotto

`genera_corpus.py`, con seme fissato e quindi riproducibile:

| Grandezza | Valore |
|---|---|
| Casi generati | **1 200** |
| Raffinamenti | 42,0% *(D46: ≥ 40%)* |
| Aperture | 37,0% |
| Chiarimenti | 11,0% *(D46: ≥ 10%)* |
| Fuori ambito | 6,0% *(D46: ≥ 5%)* |
| Incompresi | 4,0% *(D46: ≥ 3%)* |
| Entità più frequente | 14,2% *(D46: ≤ 30%)* |
| Stati incoerenti | **0** |

Il bilanciamento di **D46** è soddisfatto per costruzione, perché è il piano di generazione a imporlo anziché una verifica successiva.

---

## 5. I Limiti, Dichiarati

È la sezione che dà valore alle altre. Un corpus sintetico presentato per ciò che non è produrrebbe misure rassicuranti e decisioni sbagliate.

### 5.1 Che cosa il corpus fondativo permette

| Obiettivo | Perché funziona |
|---|---|
| Verificare la correttezza della catena | Ogni caso ha un atteso esatto |
| Misurare la **copertura** (**D34**) | I riferimenti necessari sono noti per costruzione |
| Esercitare i cinque livelli di validazione | I casi fuori ambito e incoerenti sono deliberati |
| Collaudare la forma canonica e il registro delle equivalenze (**D43**) | Servono coppie confrontabili, non frasi vere |
| Fare da rete di regressione | Il confronto è fra esecuzioni, non con la realtà |
| Tarare limiti e budget (**D12**, **D31**, **D79**) | Servono interrogazioni strutturalmente varie |
| Qualificare un nuovo modello (**D51**) | Il confronto è relativo, non assoluto |

**Sono sette obiettivi su otto della Fase 0.** È molto più di quanto suggerisca l'assenza di clienti.

### 5.2 Che cosa non permette

| Obiettivo | Perché no |
|---|---|
| Rappresentare la distribuzione reale del linguaggio | La distribuzione è quella del generatore |
| Fare da **corpus sigillato** (**D42**) | Chi scrive il generatore ne conosce tutto |
| Chiudere il cancello di Fase 2 (**D49**) | Discende dalla riga precedente |
| Validare **A9** | Richiede persone, non frasi |
| Misurare la risoluzione al primo tentativo | È una metrica di esercizio |
| Alimentare **RC1** con dati veri | Le classi fuori ambito sono quelle che abbiamo immaginato |

> **La riga sul sigillo è definitiva e vale la pena non attenuarla.** Un corpus sintetico non è sigillabile in alcun senso utile: l'autore del generatore conosce la distribuzione, i modelli di frase e i punti deboli. Aggiungere un controllo di accesso non cambierebbe nulla — proteggerebbe un segreto che non esiste.
>
> **Ne discende che D42 e D49 restano non soddisfatte fino a quando non esistono utenti reali.** Il corpus fondativo non è un sostituto in attesa: è un artefatto diverso, con un uso diverso.

### 5.3 Il rischio da sorvegliare

Il pericolo non è avere un corpus sintetico. È **dimenticare che lo è**.

Un'accuratezza del 94% sul corpus fondativo comparirebbe in una relazione, poi in una presentazione, e a quel punto nessuno ricorderebbe che misura la capacità del sistema di interpretare frasi generate da un modello di frase noto.

Presidi:

- il corpus fondativo è una **popolazione distinta e nominata**, mai fusa con le altre;
- ogni misura riporta la popolazione (`07` §15.3);
- il cancello di **D49** nomina esplicitamente il corpus sigillato, che il fondativo non è.

---

## 6. Verifica del Corpus

Un corpus generato va verificato, perché un difetto del generatore è un difetto sistematico su migliaia di casi — la forma peggiore.

| Controllo | Esito atteso | Stato |
|---|---|---|
| Nessuno stato incoerente | 0 | ✅ verificato su 1 200 casi |
| Bilanciamento di **D46** | Tutte le quote | ✅ |
| Riferimenti necessari non vuoti sui casi `operations` | 100% | Da automatizzare |
| Nessun duplicato esatto di frase | < 2% | Da automatizzare |
| Ispezione umana a campione | 100 casi per revisione | **Non sostituibile** |

**L'ultima riga resta indispensabile**, e non contraddice §4.1. La generazione elimina l'annotazione — stabilire l'interpretazione corretta — non l'ispezione, che verifica una cosa diversa: che la frase generata sia italiano che qualcuno direbbe.

È lo stesso principio del campione di casi *giudicati corretti* di `07` §9.4: un difetto del generatore produrrebbe casi coerenti, correttamente etichettati e linguisticamente assurdi, e nessun controllo automatico li segnalerebbe.

---

## 7. La Terza Via

L'Architect ha escluso due strade — due clienti reali, un cliente più uso interno. Ne resta una terza, che non richiede né clienti né prodotto attivo, e non è stata considerata.

### 7.1 L'elicitazione

> **Non serve un'installazione, non serve il prodotto, non serve un cliente. Servono persone che facciano quel lavoro.**

Un contabile, un impiegato amministrativo, un commerciale, un magazziniere. Si mostra loro un compito — *«devi trovare le fatture non ancora pagate scadute da più di un mese»* — e si chiede: **come lo diresti a un collega?**

| Aspetto | Valore |
|---|---|
| Cosa serve | 8–10 persone, 20 formulazioni ciascuna |
| Tempo | ~30 minuti a persona |
| Risultato | **~200 enunciati autentici** |
| Costo | Praticamente nullo |
| Prerequisiti | Nessuno |

### 7.2 Perché vale più di quanto costa

Duecento enunciati sono pochi per misurare, ma non servono a misurare. Servono a **validare il lessico L1**, ed è un uso completamente diverso.

Il lessico di §3.2 è curato da glossari: è vocabolario *attestato*, non vocabolario *usato*. La differenza si scopre solo ascoltando. Se otto persone su dieci dicono *«insoluti»* e nessuna dice *«in sofferenza»*, il lessico va ripesato — e con esso ogni frase generata da qui in avanti.

**Un'ora di ascolto corregge migliaia di casi generati**, perché corregge il generatore anziché i casi.

### 7.3 I limiti dell'elicitazione

Va detto per non ripetere l'errore che questo documento contesta.

Ciò che una persona dichiara di dire non coincide con ciò che dice davanti a uno schermo: manca il contesto, manca la fretta, mancano i turni di raffinamento che nascono da un risultato appena visto. L'elicitazione produce **aperture plausibili**, non conversazioni.

Resta il fatto che è linguaggio umano autentico prodotto da chi fa quel mestiere, e che è la migliore approssimazione disponibile senza un prodotto attivo.

---

## 8. La Transizione

Il corpus fondativo è un punto di partenza con una fine dichiarata.

```
FASE 0        corpus fondativo generato          1 200 casi
   │          + elicitazione (§7)                ~200 enunciati reali
   │
   ▼
FASE 1        primi utenti reali, anche interni
   │          Registro → candidati → annotazione umana
   │          nasce il CORPUS SIGILLATO (D42)
   ▼
FASE 2        corpus reale ≥ 1 000 sigillati (D45)
              cancello D49 valutabile
```

| Momento | Che cosa accade al corpus fondativo |
|---|---|
| Arrivano i primi casi reali | Restano popolazioni separate; nessuna fusione |
| Il sigillato raggiunge la dimensione minima | Le **soglie** si giudicano solo su quello |
| Il corpus reale cresce | Il fondativo resta come rete di regressione strutturale |
| Sempre | Il fondativo non entra mai nel sigillato |

**Il corpus fondativo non va dismesso quando arriva quello reale.** Continua a servire per ciò che fa meglio: esercitare in modo esaustivo la struttura del contratto, che il linguaggio reale copre in modo disomogeneo. Un corpus reale contiene poche richieste con tre raggruppamenti; quello generato ne contiene quante ne servono.

---

## 9. Rischi

### RF1 — Il corpus sintetico viene scambiato per reale

**Descrizione.** Le misure sul fondativo circolano senza qualificazione e diventano il dato di riferimento.
**Impatto. Alto sul governo.** Si aprirebbero fasi sulla base di una misura che non descrive il linguaggio degli utenti.
**Mitigazione.** §5.3; popolazione nominata; **D86**.
**Segnale anticipatore.** Una percentuale di accuratezza citata senza la popolazione.

### RF2 — Il generatore ha un difetto sistematico

**Descrizione.** Un errore nei modelli di frase o nel lessico produce migliaia di casi sbagliati nello stesso modo.
**Impatto. Alto**, e insidioso: i casi sarebbero coerenti e correttamente etichettati.
**Mitigazione.** Ispezione umana a campione (§6); controllo di coerenza automatico; seme fissato e generazione riproducibile.
**Segnale anticipatore.** Accuratezza molto alta su una classe e molto bassa su un'altra, senza causa linguistica.

### RF3 — Il lessico L1 non è il linguaggio reale

**Descrizione.** Il gergo curato da glossari differisce da quello effettivamente usato.
**Impatto. Medio-alto**, e strutturale: è la differenza fra vocabolario attestato e vocabolario usato.
**Mitigazione.** Elicitazione (§7), che esiste per questo; ripesatura del lessico sui dati reali appena disponibili.
**Segnale anticipatore.** Termini del lessico che non compaiono mai nei primi usi reali.

### RF4 — Il corpus fondativo ritarda quello reale

**Descrizione.** Avere un corpus funzionante riduce l'urgenza di procurarsi utenti.
**Impatto. Alto sull'orizzonte del prodotto.** Senza corpus reale la Fase 2 non chiude, quindi il prodotto resta in sola lettura.
**Mitigazione.** Dichiarare che **D42** e **D49** restano aperte (§5.2); mantenere **D7** aperta nel registro anche dopo questo documento.
**Segnale anticipatore.** **D7** che smette di comparire fra i punti in discussione.

---

## 10. Decisioni Richieste

Numerazione in continuità (D1–D80).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D81** | **Corpus fondativo sintetico** come popolazione distinta e nominata, mai fusa con sviluppo, regressione o sigillato | **Adottare** | RF1: misure sintetiche lette come reali |
| **D82** | **Generazione dallo stato alla frase**, con chiave corretta per costruzione | **Adottare** | Senza clienti non esiste altro modo di ottenere una chiave affidabile |
| **D83** | **Perturbazione dichiarata e registrata** sul caso, secondo la metodologia Spider-Syn / Realistic / DK | **Adottare** | Si perde l'accuratezza per fenomeno, che è l'informazione utile |
| **D84** | **L0 rigenerato dai sorgenti** a ogni aggiornamento di Odoo, con esito identico | **Adottare** | Un aggiornamento sposta il vocabolario e il corpus smette di essere confrontabile |
| **D85** | **Elicitazione** di ~200 enunciati presso 8–10 persone di mestiere, **prima del primo rilascio** | **Adottare** | Il lessico L1 resta vocabolario attestato e mai verificato (RF3) |
| **D86** | Il corpus fondativo **non soddisfa D42 e non chiude D49**: le due decisioni restano aperte | **Adottare** | Il cancello verso la scrittura verrebbe aperto su una misura sintetica |

**D82 e D86 sono le decisioni bloccanti.** D82 perché è il metodo senza il quale il corpus non esiste. D86 perché è la dichiarazione che gli impedisce di essere usato per ciò che non può fare — ed è l'unica delle sei che protegge da un errore già commesso in molti progetti simili.

---

## Chiusura

Il vincolo dichiarato dall'Architect sembrava bloccare la Fase 0. Alla verifica, blocca meno di quanto appariva: sette degli otto obiettivi della fase restano raggiungibili senza un solo cliente, e la parte più laboriosa del lavoro — l'annotazione — scompare invertendo il procedimento anziché automatizzandolo.

Il risultato non è però un sostituto. Il corpus fondativo misura la capacità di interpretare frasi costruite da un lessico che conosciamo, secondo modelli che abbiamo scritto. È un'affermazione forte sulla **struttura** del sistema — il contratto regge, la copertura si calcola, la validazione respinge ciò che deve — e non dice nulla sul linguaggio delle persone.

Le due cose che restano da procurarsi sono di natura diversa e vanno tenute distinte. **Il corpus sigillato** richiede utenti che usino il prodotto, e senza di esso il cancello di **D2** resta chiuso: è un vincolo di programma, non un ritardo tecnico. **L'elicitazione** richiede soltanto qualcuno che faccia quel mestiere e mezz'ora del suo tempo, e corregge il generatore anziché i suoi prodotti — che è il motivo per cui un'ora spesa lì vale più di mille casi in più.

Resta un'osservazione che il lavoro di questo documento ha reso evidente e che vale oltre il corpus. **La qualità dei dati che Odoo porta con sé era largamente sottovalutata**: 1 304 categorie aziendali già scritte, già tradotte e già giudicate rilevanti da chi ha progettato i moduli, disponibili senza chiedere nulla a nessuno. **D35** lo aveva previsto per i filtri salvati dei clienti; vale anche, e prima, per i filtri che il prodotto contiene di serie.

---

*Fine del documento.*
