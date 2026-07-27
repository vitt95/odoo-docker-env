# Nota Tecnica — Adattatore dei Modelli e Pannello di Configurazione
## Modelli locali e remoti, configurabili dall'amministrazione

---

| Voce | Valore |
|---|---|
| **Titolo** | Adattatore dei Modelli — configurazione di modelli locali e remoti dal pannello |
| **Tipo** | Nota tecnica decisionale (ADR) |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Stato** | Proposta sottoposta ad approvazione dell'Architect |
| **Risolve** | **D8** — modalità di erogazione. Specifica `04` §8 e `08` §3.5 |
| **Ambito** | Profili di modello, configurazione dall'amministrazione, segreti, endpoint ammessi, capacità dell'adattatore, cambio di profilo |
| **Fuori ambito** | Scelta del fornitore; prompting; schema dei dati |

> **Requisito dell'Architect (27/07/2026).** *«Deve essere prevista l'adozione direttamente da pannello di configurazione di modelli locali, modelli remoti, insomma devo poter settare qualsiasi tipologia di modello. Il resto non cambia.»*
>
> **D8 è quindi chiusa in senso più ampio di quanto il documento di visione prevedesse**: non si sceglie una modalità di erogazione, si supportano tutte, e la scelta diventa configurazione dell'installazione.

---

## 1. Che cosa cambia, e che cosa no

### 1.1 Non cambia l'architettura

Il requisito è già soddisfatto strutturalmente. `04` §8 concentra la conoscenza dei fornitori in **un solo componente**, l'Adattatore, e **D23** colloca l'Interprete dietro quel confine. **V5** impone che nessuna capacità dipenda da un fornitore esclusivo.

Ne discende che supportare modelli arbitrari non è un'estensione dell'architettura: è **l'uso previsto** del confine che esiste già. Ciò che manca non è un componente, è la configurazione.

### 1.2 Cambia il modello di configurazione

| Prima | Adesso |
|---|---|
| Fornitore e modello nell'ambiente (`04` §14.5) | **Profili** nel database, gestiti dall'amministrazione |
| Una scelta per ambiente | N profili, uno attivo, commutabile |
| Cambio = rilascio | Cambio = operazione di amministrazione |

**È qui che nascono i problemi**, e sono tre, tutti reali:

1. i **segreti** finirebbero nel database, in contrasto con `08` §7.1;
2. un **endpoint arbitrario** configurabile dal pannello trasforma la compromissione di un amministratore in un canale di esfiltrazione;
3. il **cambio di modello** diventa banale, mentre **D51** impone che sia qualificato.

Il resto di questo documento risolve i tre problemi senza rinunciare al requisito.

---

## 2. Il Profilo di Modello

### 2.1 Che cosa contiene

Un profilo descrive **come** si raggiunge un modello, non che cosa gli si chiede. Il prompting resta nell'Interprete e non è configurabile dal pannello: è parte del prodotto, ed è soggetto a regressione (`07` §4.3).

| Campo | Esempio | Nota |
|---|---|---|
| Nome | *«Locale — Ollama»* | Etichetta per l'amministratore |
| Protocollo | `openai-compat`, `anthropic`, `ollama`, … | Insieme **chiuso**: un protocollo è codice, non configurazione |
| Endpoint | `http://localhost:11434` | Soggetto a §4 |
| Modello | `qwen2.5:14b-instruct` | Stringa libera: la conosce il fornitore |
| Riferimento al segreto | `AIDA_KEY_PROD` | Mai il segreto. Vedi §3 |
| **Finestra di contesto** | `32768` | Dichiarata, non indovinata. Vedi §5 |
| **Generazione vincolata** | `json_schema` · `grammar` · `nessuna` | Determina il comportamento di validazione |
| Parametri | temperatura, limite di uscita, tempo massimo | Con predefiniti sensati |
| Stato | bozza · qualificato · attivo · ritirato | Vedi §6 |

**Il protocollo è un insieme chiuso e non un campo libero.** Parlare un protocollo richiede codice — serializzazione, gestione degli errori, mappatura delle capacità. Un pannello che promettesse «qualsiasi protocollo» starebbe promettendo che l'amministratore scriva codice in un campo di testo. Aggiungere un protocollo è un'estensione additiva del prodotto, coerente con **C7**.

Il requisito dell'Architect è comunque soddisfatto: con `openai-compat` si raggiungono oggi la quasi totalità dei servizi di inferenza locali — Ollama, vLLM, llama.cpp, LM Studio, TGI — e la maggior parte di quelli remoti.

### 2.2 Uno attivo, molti definiti

Un solo profilo è attivo per installazione. Gli altri restano definiti per essere qualificati (§6) o come ripiego dichiarato.

**Nessuna selezione automatica del modello per richiesta.** Un instradamento dinamico — modello piccolo per le richieste semplici, grande per le complesse — sarebbe un secondo componente probabilistico non misurato nel percorso, cioè esattamente ciò che **D32** ha eliminato dal catalogo. Se un giorno servirà, sarà una decisione con la propria misura, non un'opzione di configurazione.

---

## 3. I Segreti

### 3.1 Il conflitto, e come si risolve

`08` §7.1 stabilisce che le credenziali risiedono nella configurazione dell'ambiente, **mai nel database**. Un pannello che le raccolga sembra violarlo.

Vale la pena ricostruire l'**intento** della regola, perché è lì che si trova la soluzione: impedire che una copia della banca dati — un salvataggio, un ambiente di collaudo popolato dalla produzione, un accesso in lettura — produca credenziali utilizzabili.

> **Regola.** Un salvataggio della banca dati, da solo, non deve mai produrre una credenziale utilizzabile.

Due realizzazioni ammesse:

| Modalità | Come | Quando |
|---|---|---|
| **Riferimento** *(raccomandata)* | Il profilo contiene il **nome** di una variabile d'ambiente; il valore vive fuori | Produzione, e sempre per i fornitori remoti a pagamento |
| **Campo cifrato** | Il valore è cifrato con una chiave che risiede **nell'ambiente** | Comodità operativa, installazioni piccole |

Nella seconda modalità la chiave di cifratura non è mai nel database: un salvataggio contiene testo cifrato inutilizzabile senza l'ambiente. L'intento di `08` §7.1 è rispettato, la regola letterale va aggiornata — ed è una modifica alla decisione, registrata come tale.

### 3.2 Che cosa resta vietato

- il segreto in chiaro nel database, in qualunque campo;
- il segreto restituito da un'interfaccia dopo essere stato scritto — si scrive, non si rilegge;
- il segreto nei registri diagnostici, negli errori, nelle risposte (**D60**);
- il segreto in un profilo esportato o duplicato: l'esportazione porta il riferimento, non il valore.

**I modelli locali spesso non hanno segreto.** È un vantaggio operativo della modalità C che vale la pena rendere esplicito: un endpoint su rete interna senza credenziale elimina l'intera classe di problemi di questa sezione.

---

## 4. Gli Endpoint Ammessi

### 4.1 Il rischio, detto per intero

Un pannello che accetti un endpoint arbitrario crea un canale che prima non esisteva: **chi controlla un account di amministrazione può far partire verso un server proprio ogni enunciato e ogni catalogo dell'installazione.**

Non è un attacco teorico ed è particolarmente efficace, perché il sistema continuerebbe a funzionare perfettamente. Gli utenti otterrebbero risposte corrette — l'attaccante inoltra al vero fornitore — mentre ogni domanda e la terminologia interna dell'azienda passano da lui. Nessun indicatore di `07` lo rileverebbe: accuratezza normale, copertura normale, latenza appena superiore.

Va aggiunto che l'endpoint è raggiungibile dal **server Odoo**, non dal browser: un indirizzo su rete interna diventa uno strumento di ricognizione della rete del cliente.

### 4.2 La regola

> **L'elenco degli host ammessi vive nell'ambiente, non nel pannello.** Il pannello consente di scegliere fra ciò che l'ambiente permette; non consente di estendere il permesso.

È lo stesso principio applicato ovunque nell'impianto: **l'impossibilità strutturale al posto del controllo** (C3). Un amministratore compromesso non può esfiltrare verso un host non previsto perché quell'host non è configurabile, non perché un controllo lo respinge.

| Voce | Comportamento |
|---|---|
| Elenco ammessi | Variabile d'ambiente, con host e schema |
| Predefinito | Loopback (`127.0.0.1`, `::1`) — abilita i modelli locali senza configurazione |
| Rete interna oltre il loopback | Ammessa **solo se dichiarata esplicitamente** nell'ambiente |
| Redirezioni | Non seguite |
| Schema | `https` obbligatorio fuori dal loopback |
| Modifica dell'elenco | Richiede accesso all'ambiente, quindi un rilascio o un intervento operativo |

**Il predefinito è deliberatamente permissivo verso il locale e restrittivo verso il resto**, perché riflette il profilo di rischio reale: un endpoint su loopback è raggiungibile solo da chi è già sulla macchina, un endpoint remoto è raggiungibile da chiunque.

### 4.3 Che cosa si registra

Ogni modifica di profilo e ogni cambio di profilo attivo entrano nel Registro con autore, momento, valori precedenti e successivi. Il segreto non compare mai, nemmeno in forma di riferimento modificato.

È l'unica difesa contro l'uso legittimo del pannello a fini illegittimi, e appartiene alla stessa famiglia di **D62**: non si previene tutto, ma nulla accade senza traccia.

---

## 5. Le Capacità del Modello

### 5.1 Non tutti i modelli sanno fare le stesse cose

È l'aspetto tecnico più rilevante del requisito, e quello che nessun documento precedente affronta perché nasce con la configurabilità.

**La generazione vincolata non è disponibile ovunque.** `03` §12.3 fonda su di essa un'aspettativa precisa — i fallimenti di validazione ai livelli 1 e 2 dovrebbero essere rari, perché l'uscita del modello può essere vincolata allo schema — e ne trae una diagnosi: un tasso non trascurabile a quei livelli *«non è un problema di validazione: è il segnale che la generazione vincolata non è applicata correttamente»*.

Con profili configurabili quella diagnosi diventa ambigua. Un modello locale senza vincolo produce legittimamente più fallimenti di livello 1–2, e il segnale diagnostico si spegne.

> **Regola.** Il profilo **dichiara** la propria modalità di generazione vincolata. Le soglie di fallimento dei livelli 1–2 sono valutate rispetto a quella dichiarazione, non rispetto a un valore assoluto.

Un profilo senza generazione vincolata è ammesso — è la condizione di molti modelli locali — ed è marcato come **degradato**. Nessuna busta non valida viene mai accettata: cambia la frequenza dei rifiuti, mai il rigore. Il ripristino con un solo tentativo (**D15**) resta il limite, e su un profilo degradato il tasso di ripristino sale: è atteso, e va letto come costo del profilo, non come difetto del sistema.

### 5.2 La finestra di contesto governa il budget del catalogo

**D31** fissa il budget a 60 attributi per entità, calcolato su modelli con finestra ampia. Un modello locale con finestra di 4 096 gettoni non regge un catalogo di 60 attributi più il prompt più la conversazione — e il modo in cui fallirebbe è il peggiore: **troncamento silenzioso del contesto**, che si manifesta come copertura apparentemente alta e accuratezza inspiegabilmente bassa.

Sarebbe il quadrante in basso a destra di `07` §5.4 prodotto da una causa che quella tabella non contempla, e la diagnosi porterebbe a lavorare sul dizionario per settimane.

> **Modifica a D31.** Il budget del catalogo non è una costante: è **derivato dalla finestra di contesto dichiarata dal profilo**, entro il massimo di 60.

```
budget_attributi  =  min( 60,  f(finestra_contesto − prompt − margine) )
```

Con il vincolo operativo: se il budget derivato scende sotto una soglia minima utile — indicativamente 20 attributi — il profilo **non è idoneo** e va segnalato come tale in qualificazione, non scoperto in esercizio.

La misura che sorveglia questa condizione esiste già: *dimensione media del catalogo* e *rifiuti per budget* (`07` §10.3).

---

## 6. Il Cambio di Profilo

### 6.1 Perché non può essere un menù a tendina

**D51** impone un protocollo di qualificazione in otto passi per un nuovo modello, e l'ottavo è la prova di isolamento — perché un modello più lento dimezza la capacità del dispatcher e la conseguenza ricade sull'ERP, non sull'accuratezza.

Un pannello che consenta di cambiare modello in produzione con due clic rende quel protocollo aggirabile per distrazione, non per decisione.

### 6.2 Gli stati del profilo

```
bozza ──▶ qualificato ──▶ attivo ──▶ ritirato
  │            ▲              │
  │            │              └── un solo profilo alla volta
  └── protocollo D51 ─────────┘
      otto passi, esito registrato
```

| Stato | Significato |
|---|---|
| **bozza** | Definito e raggiungibile. Utilizzabile **solo** in ambiente di collaudo |
| **qualificato** | Ha superato **D51**, con esito e data registrati |
| **attivo** | In uso. Uno per installazione |
| **ritirato** | Conservato per tracciabilità. Le misure passate restano attribuibili |

**Un profilo in bozza non può diventare attivo in produzione.** È il presidio, ed è strutturale: non un avviso che si può chiudere, uno stato che non ammette la transizione.

### 6.3 Che cosa comporta l'attivazione

| Effetto | Origine |
|---|---|
| Riesecuzione del corpus di regressione | `07` §4.3 |
| Ricalcolo della soglia di rumore | **D48** — è proprietà del modello |
| Ricalibrazione delle soglie di confidenza | **RC6**, **D51** |
| Ricalcolo del budget del catalogo | §5.2 |
| Invalidazione delle interpretazioni memorizzate | `04` §10.4 — sono state prodotte da un altro modello |
| Registrazione nel Registro | §4.3 |

**L'ultima riga della tabella prima di questa è quella che si dimentica.** Le interpretazioni memorizzate sono state prodotte da un modello diverso; riusarle dopo il cambio significa mescolare due modelli nello stesso esercizio e rendere non attribuibile qualunque variazione — cioè violare la regola *una esecuzione, una variabile* di `07` §4.2.

---

## 7. Effetti sui Documenti Esistenti

| Documento | Effetto |
|---|---|
| `04` §14.5 | La riga *«Fornitore e modello attivo — Ambito: Ambiente»* diventa *«Profilo attivo — Ambito: Installazione»*. Le credenziali restano nell'ambiente |
| `08` §7.1 | La regola letterale *«mai nel database»* è sostituita da quella di §3.1: *un salvataggio, da solo, non deve produrre una credenziale utilizzabile* |
| `08` §3.5 | Le tre modalità A/B/C restano la classificazione commerciale; qui ricevono la realizzazione tecnica |
| `08` §7.2 | La riga *«Modalità di erogazione — visibile nell'amministrazione»* è soddisfatta dal pannello |
| **D31** | Il budget di 60 attributi diventa un **massimo**, non una costante (§5.2) |
| `07` §13 | Il protocollo di qualificazione acquista uno stato di profilo che lo rende non aggirabile (§6.2) |

---

## 8. Decisioni Richieste

Numerazione in continuità (D1–D74).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D75** | **Profili di modello** gestiti dall'amministrazione, con protocollo da insieme chiuso e uno attivo per installazione (§2) | **Adottare** — chiude **D8** | Il requisito resta soddisfatto solo per i fornitori previsti a codice |
| **D76** | **I segreti non sono mai leggibili da un salvataggio della banca dati**: riferimento all'ambiente, o campo cifrato con chiave nell'ambiente (§3) | **Adottare** | Una copia di collaudo popolata dalla produzione distribuisce credenziali valide |
| **D77** | **Elenco degli host ammessi nell'ambiente**, non nel pannello; loopback ammesso di norma, resto solo se dichiarato (§4) | **Adottare** | La compromissione di un amministratore diventa esfiltrazione di ogni enunciato e catalogo, senza alcun sintomo |
| **D78** | Il profilo **dichiara** generazione vincolata e finestra di contesto; le soglie di fallimento 1–2 si valutano rispetto alla dichiarazione (§5.1) | **Adottare** | Si perde la diagnosi di `03` §12.3, e un profilo degradato appare come un difetto di sistema |
| **D79** | **Il budget del catalogo è derivato dalla finestra di contesto**, con 60 come massimo; sotto la soglia minima il profilo non è idoneo (§5.2) | **Adottare** — modifica **D31** | Troncamento silenzioso del contesto: copertura alta, accuratezza bassa, causa invisibile |
| **D80** | **Stati del profilo** e divieto strutturale di attivare in produzione un profilo non qualificato (§6.2) | **Adottare** | **D51** diventa aggirabile per distrazione |

**D77 e D79 sono le decisioni bloccanti.** D77 perché il pannello crea un canale di esfiltrazione che prima non esisteva e che nessuna metrica rileverebbe. D79 perché è la condizione senza la quale i modelli locali — cioè metà del requisito dell'Architect — falliscono nel modo più difficile da diagnosticare.

---

## Chiusura

Il requisito non ha richiesto modifiche all'architettura, e questo è di per sé la verifica di una decisione presa mesi prima: **V5** e l'Adattatore esistevano perché il fornitore fosse sostituibile, e quando la sostituibilità è stata chiesta sul serio si è rivelata già disponibile. È il ritorno di un investimento fatto quando non serviva.

Ha però prodotto tre problemi che nessun documento precedente poteva vedere, perché nascono tutti dallo stesso fatto: **spostare una scelta dall'ambiente al pannello sposta anche il confine di fiducia.** Ciò che prima richiedeva un rilascio ora richiede un accesso di amministrazione, e le tre difese di §3, §4 e §6 esistono per riportare quel confine dove era.

Il problema più insidioso resta **D79**, perché non è di sicurezza e non produce un guasto: un modello locale con finestra stretta tronca il contesto in silenzio, e il sistema mostra copertura alta e accuratezza bassa — la combinazione che `07` §5.4 attribuisce a un problema di interpretazione. Si lavorerebbe su prompt e dizionario per settimane, con la causa a monte e nessun indicatore che la nomini.

È lo stesso schema già incontrato con **D40** e con **RC3**: i guasti che contano, in questo progetto, non sono quelli che si manifestano — sono quelli che spostano la diagnosi altrove.

---

*Fine del documento.*
