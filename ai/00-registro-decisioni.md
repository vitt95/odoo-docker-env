# Registro delle Decisioni Architetturali

## AI Agent per Odoo — Natural Language Interaction Layer

| | |
|---|---|
| **Documento** | `00-registro-decisioni.md` |
| **Natura** | Documento di governo — vive per tutta la durata del progetto |
| **Copre** | D1–D91, con l'articolazione D20a–D20f; **D93 proposta** in §16 |
| **Fonti** | `02-visione-prodotto.md` §19 · `03-specifica-dsl.md` §20 · `04-architettura.md` §17 · `05-esecuzione-asincrona.md` §10 · `06-modello-semantico.md` §13 · `07-piano-valutazione-qualita.md` §17 · `08-sicurezza-conformita.md` §13 |
| **Autorità decisionale** | Architect — delega esercitata in questa sede |
| **Delibera** | 27 luglio 2026 |
| **Stato complessivo** | **90 decisioni adottate** (di cui 16 con vincolo), **5 superate**, **1 aperta** — **D7**, che resta aperta per volontà esplicita: nessun corpus sintetico la soddisfa |

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
| **D6** | Denominazione del prodotto | ☑ **Chiusa — «AIDA»** | Deliberata dall'Architect il 27/07/2026. Evita il termine *agent*, come raccomandato da `04` §14.3. **Il prefisso tecnico resta `nli_`**: la denominazione commerciale e quella tecnica sono indipendenti per costruzione, e `nli` descrive la funzione (*Natural Language Interaction*) indipendentemente dal marchio |
| **D7** | Clienti pilota e attività di riferimento | ☐ Aperta | Non deliberabile tecnicamente. **Requisiti di scelta fissati** in §7 |
| **D8** | Erogazione per clienti regolamentati | ☑ **Chiusa — tutte le modalità** | Deliberata dall'Architect il 27/07/2026 in senso più ampio: non si sceglie una modalità, si supportano tutte e la scelta diventa configurazione. Realizzazione in **D75–D80**, `10-adattatore-modelli.md` |

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

### 3.7 Sicurezza e conformità — `08-sicurezza-conformita.md` §13

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D54** | **Pseudonimizzazione degli enunciati all'ingresso**, mappatura separata e cifrata | ☑ Adottata | La pseudonimizzazione retroattiva non esiste: ogni giorno senza produce dati in chiaro che nessuna decisione successiva ripulisce. Cancellare una riga di mappatura è esatto e dimostrabile; cercare un nome in dodici mesi di testo non lo è |
| **D55** | **Vincolo V8** — nessun artefatto dall'Interprete che non sia una Busta validata | ☑ Adottata | È la formulazione esplicita della proprietà su cui poggia tutta la difesa dall'iniezione. Implicita, la Fase 6 la eroderebbe senza che nessuno debba dichiararlo |
| **D56** | Requisiti **F-1…F-7** verso il fornitore, verificati prima dell'integrazione | ☑ Adottata | L'Adattatore rende sostituibile il fornitore, non retroattivo il trasferimento già avvenuto. **F-7** — revisione umana dei contenuti — è spesso attiva per impostazione predefinita |
| **D57** | Il **catalogo è informazione riservata** del cliente | ☑ Adottata | Terminologia, campi personalizzati e valori enumerati descrivono processi, segmentazione e linee di prodotto. *«Sono solo metadati»* è vero e commercialmente pericoloso |
| **D58** | Modalità di erogazione **A / B / C**, con quella attiva visibile in amministrazione | ☑ Adottata — **chiude la parte tecnica di D8** | L'architettura le ammette tutte senza modifiche (**V5**, **D23**). A6 rende la modalità C un problema di dimensionamento, non di ricerca. Una garanzia non ispezionabile dal cliente vale meno di quanto costa |
| **D59** | Nessun campo di voce di dizionario è **testo libero** verso il modello | ☑ Adottata | Completa **D30**: il vocabolario dei tipi è chiuso, ora lo è anche la forma del contenuto |
| **D60** | Divieto di enunciati, cataloghi e credenziali nei registri diagnostici, con verifica automatica | ☑ Adottata | È il vettore più frequente e il meno progettato, e vanifica misure corrette prese altrove |
| **D61** | Ritenzione della mappatura pari al turno più lungo che vi fa riferimento | ☑ Adottata | Senza cancellazione automatica, una misura di protezione produce un archivio di identità senza finalità. **RG7 non ha segnale anticipatore** |
| **D62** | Nessun componente persiste decisioni di **autorizzazione** | ☑ Adottata | Generalizza **RA8** e la regola del dizionario: i disallineamenti di autorizzazione non si manifestano come errori, ma come accessi riusciti |
| **D63** | Le **dichiarazioni ammissibili** di §3.6 vincolano la comunicazione verso i clienti | ☑ Adottata | Insolito per un documento di sicurezza, e necessario: la formulazione commerciale più naturale — *«nessun dato esce»* — è anche quella falsa, e viene smentita durante una valutazione fornitori |

### 3.8 Esperienza utente — `09-esperienza-utente.md` §13

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D64** | **Interpretazione sempre visibile sopra il risultato**, senza interazione | ☑ Adottata | Un'azione richiesta per verificare qualcosa che di solito è giusto non viene compiuta. Dietro un pannello, **A9 è falsa per costruzione** e la difesa contro R1 resta progettata ma non effettiva |
| **D65** | **Salienza graduata per origine**, distinzione non dipendente dal colore | ☑ Adottata | Mostrare tutto con lo stesso peso è il modo più efficace per non far leggere nulla. I fraintendimenti vivono nei criteri, non nell'entità: l'attenzione va spesa lì |
| **D66** | Ogni elemento mostrato è **azionabile** | ☑ Adottata | Ripaga tre volte: esperienza, Leva 1 delle prestazioni, resilienza senza modello. Un elemento visibile e non azionabile insegna che l'interpretazione è decorativa |
| **D67** | L'interpretazione mostra il **periodo risolto** | ☑ Adottata | *«Questo mese»* conferma sé stesso. Solo il periodo risolto rende verificabile l'esercizio non solare — la forma canonica di R1 sui dati aggregati |
| **D68** | **Conteggio prima del recupero**, formulazione *«primi 80 di N»* | ☑ Adottata | Ottanta record senza contesto sono letti come tutti. È un fraintendimento plausibile prodotto dall'interfaccia anziché dal modello |
| **D69** | Messaggi di **rifiuto per carico**: nessun tono di errore, nessuna attribuzione all'utente, sempre un'azione | ☑ Adottata | **D20c** sopravvive o cade con questi messaggi. Scritti come guasti, generano segnalazioni, e le segnalazioni fanno alzare i limiti — ritorno a RA3 |
| **D70** | La scelta referenziale è **conservata per la sessione** | ☑ Adottata | Riproporre la stessa disambiguazione a ogni turno rende insopportabile una funzione corretta. Lo stato resta invariato: è una proprietà di sessione |
| **D71** | Requisiti di **accessibilità**, incluso l'annuncio del cambio di stato asincrono | ☑ Adottata | Non è adempimento: un'interpretazione che alcune persone non possono leggere è, per loro, assente — e con essa cade A9. L'annuncio è specifico di **D20a** |
| **D72** | I **nomi dal dizionario non si traducono** | ☑ Adottata | Il gergo aziendale è un asset dell'organizzazione, non una stringa da localizzare. Due lingue nella stessa schermata sono corrette |
| **D73** | Validazione di **A9 per iniezione controllata**, ripetuta, con i tre vincoli | ☑ Adottata | Non rafforza la difesa: la rende **verificabile**. È l'unica decisione che può dirci che D64 e D65 non stanno funzionando |
| **D74** | Progetto della **conferma di Fase 3**, con divieto di scorciatoie sulla confidenza | ☑ Adottata | La qualità dell'esperienza di conferma è una misura di sicurezza: una conferma fastidiosa viene rimossa, ed è il percorso di **RG6** |

### 3.9 Adattatore dei modelli — `10-adattatore-modelli.md` §8

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D75** | **Profili di modello** gestiti dall'amministrazione, protocollo da insieme chiuso, uno attivo | ☑ Adottata — **chiude D8** | Il requisito non ha richiesto modifiche architetturali: **V5** e l'Adattatore esistevano perché il fornitore fosse sostituibile, e alla prova lo era già |
| **D76** | I segreti non sono leggibili da un salvataggio della banca dati | ☑ Adottata — **modifica `08` §7.1** | L'intento della regola originale era che una copia non producesse credenziali. Riferimento all'ambiente o cifratura con chiave nell'ambiente lo rispettano; il divieto letterale no |
| **D77** | **Elenco host ammessi nell'ambiente**, non nel pannello | ☑ Adottata · **bloccante** | Il pannello crea un canale che prima non esisteva: un amministratore compromesso invierebbe ogni enunciato e catalogo altrove, **con accuratezza e latenza normali**. Nessuna metrica di `07` lo rileverebbe |
| **D78** | Il profilo dichiara generazione vincolata e finestra di contesto | ☑ Adottata | Senza dichiarazione si spegne la diagnosi di `03` §12.3 e un profilo degradato appare come difetto di sistema |
| **D79** | **Budget del catalogo derivato dalla finestra di contesto**, 60 come massimo | ☑ Adottata · **bloccante** — **modifica D31** | Un modello locale con finestra stretta tronca il contesto in silenzio: copertura alta, accuratezza bassa, causa fuori da ogni tabella diagnostica |
| **D80** | **Stati del profilo**; divieto strutturale di attivare in produzione un profilo non qualificato | ☑ Adottata | Rende **D51** non aggirabile per distrazione |

### 3.10 Corpus fondativo — `11-corpus-fondativo.md` §10

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D81** | **Corpus fondativo sintetico** come popolazione distinta e nominata | ☑ Adottata | Mai fuso con sviluppo, regressione o sigillato |
| **D82** | **Generazione dallo stato alla frase** | ☑ Adottata · **bloccante** | Inverte il procedimento anziché automatizzare l'annotazione: la chiave è corretta per costruzione, che è l'unico modo di averne una senza clienti |
| **D83** | **Perturbazione dichiarata e registrata** sul caso | ☑ Adottata | Metodologia Spider-Syn / Realistic / DK, pubblicata e validata. La registrazione abilita l'accuratezza per fenomeno |
| **D84** | **L0 rigenerato dai sorgenti** a ogni aggiornamento | ☑ Adottata | Coerente con `06` §2.4 e con l'evento di regressione di `07` §7.3 |
| **D85** | **Elicitazione** di ~200 enunciati presso 8–10 persone di mestiere | ☑ Adottata | Non richiede clienti né prodotto attivo. Corregge il **generatore**, non i casi: un'ora vale più di mille casi in più |
| **D86** | Il corpus fondativo **non soddisfa D42 e non chiude D49** | ☑ Adottata · **bloccante** | Un corpus sintetico non è sigillabile: chi scrive il generatore ne conosce la distribuzione. È la decisione che impedisce di usarlo per ciò che non può fare |

### 3.11 Contratto — questioni emerse dall'implementazione

| # | Decisione | Stato | Delibera |
|---|---|---|---|
| **D87** | Predicato `is_category` per la condizione nominata T5 | ⊡ Adottata con vincolo | Deliberata su delega dell'Architect il 28/07/2026. Senza, il contratto non esprime una voce che D30 richiede in Fase 1, e il 68,8% del corpus non è rappresentabile. **Tre vincoli** in §14, tutti prerequisiti della parte 3 |
| **D88** | `origin` opzionale sull'operazione; la direzione di ordinamento non ha valore predefinito | ⊡ Adottata con vincolo | §15. Senza, l'atteso di §17.1 turno 3 non è raggiungibile. Il vincolo conta più della chiave: `asc` predefinito su una data restituisce i cinque più vecchi per *«gli ultimi cinque»* |
| **D89** | Misure con vista `list` sono valide; incoerenti solo **con** un raggruppamento | ⊡ Adottata con vincolo | §15. Delle due letture, quella scartata **rifiuta** una richiesta che la vista lista di Odoo soddisfa nativamente. Una lettura che può negare una risposta perde |
| **D90** | Il vocabolario delle operazioni conta **ventidue** voci, non diciotto | ☑ Adottata | §15. Le tabelle di §6.2–6.6 sono normative; il conteggio in prosa è stantio |
| **D91** | `year_to_date` aggiunto; assolute senza anno → chiarimento | ⊡ Adottata con vincolo | §15. Fare nulla avrebbe costretto ad aggiungere una categoria di `scope_note`: modificare comunque un vocabolario chiuso, per dire che non sappiamo dire una cosa esprimibile con un simbolo |

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
| ~~**D6**~~ | ~~Nome commerciale~~ | **Chiusa il 27/07/2026: «AIDA».** Prefisso tecnico invariato: `nli_` |
| **D7** | Clienti pilota | **Almeno due clienti, di domini diversi; almeno uno con personalizzazioni rilevanti** — è l'unico modo di mettere sotto sforzo le regole di esposizione di D31; attività di riferimento elencate per iscritto; disponibilità a cedere richieste reali; **misura iniziale sull'interfaccia nativa eseguita prima dell'attivazione**, perché dopo non è più ottenibile |
| ~~**D8**~~ | ~~Erogazione in ambiente controllato~~ | **Chiusa il 27/07/2026 da D75–D80**: tutte le modalità supportate, configurabili dall'amministrazione |

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
| Gli enunciati non sono mai persistiti in chiaro | **D54** | Prova P-7 |
| Nessun artefatto dall'Interprete oltre la Busta validata | **D55** (**V8**) | Controllo architetturale di D24 |
| Enunciati e cataloghi non finiscono nei registri diagnostici | **D60** | Prova P-8 |
| Un turno senza contesto societario è respinto, non eseguito | **D40**, `08` §10 | Prova P-3 |
| Il traffico verso il fornitore contiene solo enunciato e catalogo | **A6**, **V7** | Prova P-9, osservando il traffico |
| Nessun risultato è presentato senza la sua interpretazione | **V4**, **D64** | Invariante misurato al 100% (**D53**) |
| L'inferito è distinguibile senza ricorso al colore | **D65** | Prova con simulazione di daltonismo e alto contrasto |
| L'interpretazione precede il risultato nell'ordine di lettura | **D71** | Prova con lettore di schermo |

---

## 10. Procedura

**Per modificare una decisione adottata** serve una nuova decisione, non un emendamento. La voce originale resta, con lo stato aggiornato.

**Per superare una decisione**: `⊘ Superata da Dn`. Mai cancellata. Le quattro supersessioni già presenti sono la prova che la disciplina serve.

**Per aggiungere una decisione**: numerazione in continuità da **D93**. D87–D91 sono deliberate (§14, §15); D92 è corretta.

**Vincoli aggiunti in delibera.** Le dodici decisioni marcate ⊡ portano una condizione che è parte della decisione: rimuoverla è modificare la decisione, non semplificarla.

---

## 11. Registro dei cambiamenti

| Data | Cambiamento |
|---|---|
| 2026-07-27 | Creazione del registro. Consolidate D1–D38 e D20a–D20f. Rilevate quattro supersessioni non tracciate. Nessuna decisione approvata. |
| 2026-07-27 | **Delibera.** 39 decisioni adottate, 11 con vincolo. Fissati i valori di D13 (80 / 500), D31 (budget 60), D5 (latenza scomposta in tre soglie), D26 (ritenzione confermata con esecuzione a lotti), D20e (4 processi cron entro il tetto di connessioni). Corretto il percorso di scala di D20f: N record dispatcher, non N istanze. Qualificata la portata di A6 sotto D3. Introdotte **D39** (impronta dei permessi), **D40** (contesto societario sul turno), **D41** (conservazione deduplicata del catalogo). Restano aperte D6 (parte commerciale), D7, D8. |
| 2026-07-27 | **Recepito `07-piano-valutazione-qualita.md`.** Adottate **D42–D53** (2 con vincolo). Corretti i conteggi della delibera precedente: le decisioni superate sono **cinque** (D16, D17, D20, D21, D22) in quattro eventi di supersessione, non quattro; le adottate erano 39 e non 38; le decisioni con vincolo 11 e non 9. **D52** è adottata ma non eseguibile finché **D7** resta aperta, ed è l'unica con una finestra che si chiude da sola. |
| 2026-07-27 | **Recepito `08-sicurezza-conformita.md`.** Adottate **D54–D63**. Introdotto il vincolo permanente **V8** (D55). **D58** chiude la parte tecnica di **D8**: restano aperte solo la scelta commerciale di erogazione, **D6** (nome) e **D7** (pilota). Rilevata una lacuna sul confine interno: il Registro conserva enunciati grezzi per 12 mesi, e l'argomento *«sono domande, non risposte»* di `04` §4.9 e §9.3 vale per i dati aziendali ma non per i dati personali — risolta da **D54**. |
| 2026-07-27 | **Recepito `09-esperienza-utente.md`.** Adottate **D64–D74**. Il documento realizza la difesa che gli altri avevano progettato: **A9** è un'ipotesi sul comportamento umano, non una scelta di progettazione, e si indebolisce man mano che il sistema migliora. **D69** e **D74** sono decisioni di esperienza con effetto di sicurezza: da esse dipende la sopravvivenza di **D20c** e della conferma di Fase 3. Corpus documentale completo: 00 e 02–09. |
| 2026-07-27 | **D6 chiusa dall'Architect: il prodotto si chiama «AIDA».** Il prefisso tecnico resta `nli_` per la ragione già dichiarata in `04` §14.3 — marchio e struttura tecnica devono poter evolvere separatamente. Restano aperte **D7** e **D8**. |
| 2026-07-27 | **D8 chiusa dall'Architect, in senso più ampio del previsto:** modelli locali e remoti configurabili dall'amministrazione. Recepito `10-adattatore-modelli.md`, adottate **D75–D80**. L'architettura non ha richiesto modifiche — è il ritorno dell'investimento fatto su **V5** e sull'Adattatore. Spostare la scelta dall'ambiente al pannello sposta però il confine di fiducia: da qui **D76**, **D77** e **D80**. **D79** modifica **D31**: il budget del catalogo si deriva dalla finestra di contesto. |
| 2026-07-28 | **Parte 5 implementata; il profilo non qualifica.** Adattatore di fornitore (§8), profili amministrati (**D75**) con host nell'ambiente (**D77**), segreto per nome di variabile (**D76**), capacita' dichiarate (**D78**) e divieto strutturale di attivare un profilo non qualificato (**D80**). Ripristino con un solo tentativo (**D15**). **Prima misura di accuratezza del progetto**, contro un qwen2.5 7B locale su 20 casi di apertura del corpus: **15% complessiva**, tutte le sezioni sotto la soglia di **D44** — `target` 65%, `filter` 35%, `order_by` 55%. Il profilo resta quindi in `qualified: no` e D80 ne rifiuta l'attivazione, che e' il comportamento voluto: la macchina funziona e dice di no. Il primo giro di misura ha corretto due difetti del **prompt**, non del modello: la forma di un'operazione non era mostrata (il modello emetteva `type` e `field`) e nulla vietava di inventare `set_limit` e `set_fields` non richiesti — da 10% a 15%, con `limit` da 40% a 70%. |
| 2026-07-28 | **Parte 4 completa.** Risolutore, validazione livelli 3-5, Esecutore con conteggio prima del recupero (**D68**), Presentatore a viste native (**V4**), stato come record (**D19**), contesto societario sul turno (**D40**). Prima interrogazione end-to-end da uno stato scritto a mano: 40 test Odoo, 269 puri. Introdotta nei controlli di D24 la **zona deterministica** — puo' calcolare con le date, non puo' leggere l'orologio — perche' `04` §4.6 distingue l'essere consapevoli del tempo dal leggerlo, e senza la distinzione il Risolutore sarebbe o incapace di aritmetica o non controllato. **La provenienza non e' persistita** finche' D54 non esiste: i frammenti sono parole dell'utente, e scriverli in chiaro per i dodici mesi di D26 e' esattamente cio' che D54 dice non essere sanabile a posteriori. |
| 2026-07-28 | **Parte 3 completa.** Aggiunta la meta' che richiede Odoo: **L0 per introspezione** dei metadati (D84), **estrazione da `ir.filters`** come proposte T5 inerti in coda L3 (D35, D28), **impronta dei permessi** (D39, D40). Due rilievi dall'esecuzione in **§16.5** e **§16.6**: l'impronta non e' leggibile dalle tabelle delle regole — un utente ordinario non puo' leggere `ir.model.access` e `sudo` e' vietato — e si costruisce sugli **effetti osservabili**, con le regole sui record deliberatamente escluse perche' filtrano record, non riferimenti; e il divieto sui contesti privilegiati e' stato reso *scoped* ai percorsi di interrogazione, come §6.3 dice, perche' altrimenti la proprieta' che protegge non e' testabile. 27 test Odoo, 236 puri. |
| 2026-07-28 | **Parte 3, nucleo puro.** Dizionario e catalogo in `nli_semantics`, 236 test puri, i tre criteri misurati: copertura **100%** su 948 casi (esatta per costruzione in Fase C, D32), Fase A **86,2%** con **zero** determinazioni sbagliate, budget derivato dalla finestra. I tre vincoli di **D87** sono realizzati **per costruzione**: la condizione di una categoria e' una struttura tipizzata, quindi i campi implicati si derivano — il buco di `sottoscorta` non e' piu' dimenticabile. Quattro rilievi su `06` §5.5 in **§16**, fra cui **D93 proposta** (un attributo batte un'entita' sulla stessa porzione di frase: +8 punti di percorso rapido rispetto all'alternativa, a pari zero errori). Corretti i due difetti nei dati di §14.6. |
| 2026-07-28 | **D88–D91 deliberate su delega dell'Architect** (§15). **D88**: `origin` opzionale sull'operazione, e la direzione di ordinamento **non ha un valore predefinito** — `asc` su una data restituirebbe i cinque piu' vecchi per *«gli ultimi cinque»*, cinque record col numero giusto e la risposta rovesciata. **D89**: delle due letture della contraddizione misure/vista, scartata quella che **rifiuta** cio' che la vista lista di Odoo fa nativamente. **D90**: le operazioni sono ventidue. **D91**: aggiunto `year_to_date`, risolto contro l'esercizio fiscale; le assolute senza anno restano un chiarimento. Il limite residuo di D88 — origine per parametro su `group_by`.granularity — e' dichiarato e **non** risolto: la sua estensione e' subordinata all'evidenza di D73 e D53, non a un'intuizione. |
| 2026-07-28 | **D87 deliberata su delega dell'Architect: ⊡ adottata con vincolo.** Il contratto ammette `is_category` per la condizione nominata T5. Analisi completa in §14. Cercata e scartata l'alternativa a costo zero — esporre la categoria come attributo booleano del dizionario — perche' ammetterebbe `is_false` su una condizione, la cui negazione non e' la negazione di un campo, e perche' renderebbe una **definizione** indistinguibile dal **vocabolario**, riaprendo la modalita' di guasto che **D29** esiste per chiudere. Tre vincoli, tutti prerequisiti della parte 3, fra cui un buco di **V2** rilevato nei dati: i `campi_implicati` di `sottoscorta` sono incompleti. |
| 2026-07-28 | **Corpus fondativo rigenerato.** **D92 corretta**: forma normativa, espressioni temporali simboliche, riferimenti semantici con binding tecnico, raffinamenti non degeneri, stato atteso anche sui raffinamenti. Rilevato e corretto un quinto difetto che nessuno aveva misurato: **29,6% di frasi duplicate**, ora 1,0%. Il corpus passa da 876 a **948 casi verificati su 948**, e l'adattatore fra corpus e contratto è stato rimosso. Dettagli in `11` §4.6. |
| 2026-07-28 | **Parte 2 implementata.** Contratto, validazione livelli 1–2, Applicatore, forma canonica e registro delle equivalenze in `custom_addons/nli_core`. Sei questioni emerse scrivendo il codice, tutte registrate in **§13 come proposte da deliberare**: **D87** (predicato della categoria T5, senza cui il 68,8% del corpus non è rappresentabile), **D88** (come `origin` entra nello stato), **D89** (contraddizione §5.6/§12.5 contro §6.7 regola 3), **D90** (le operazioni sono 22, non 18), **D91** (due lacune nel vocabolario temporale), **D92** (difetti del generatore del corpus, poi corretti). Nessuna decisione adottata: l'implementazione dichiara la lettura raccomandata e attende delibera. |
| 2026-07-27 | **Recepito `11-corpus-fondativo.md`.** Adottate **D81–D86**. Estratti dai soli sorgenti Odoo, senza clienti: 813 entità, 12 411 attributi, 2 668 valori enumerati e **1 304 categorie aziendali già tradotte**. Generati 1 200 casi con chiave corretta per costruzione, bilanciamento **D46** rispettato, zero stati incoerenti. **D7 resta aperta per decisione esplicita (D86):** un corpus sintetico non è sigillabile, quindi **D42** e **D49** non sono soddisfatte. |

---

## 12. Giudizio complessivo

L'impianto regge, e regge per una ragione strutturale che vale la pena dichiarare: **le decisioni prese per correttezza producono, quasi ovunque, anche il comportamento più veloce e più semplice.**

Lo stato invece della cronologia (D4) è la scelta corretta contro la deriva ed è anche quella che mantiene il costo per turno costante. Il catalogo a tre fasi (D32) è la scelta corretta contro il tetto di accuratezza ed è anche quella che riduce latenza e costo. Il limite obbligatorio (D13) è una regola di contratto ed è anche la protezione della disponibilità. L'esecuzione asincrona (D20a) protegge l'ERP e rende l'attesa leggibile. Quando questo accade in modo sistematico, l'impianto non è un compromesso fra obiettivi in conflitto: è coerente.

Le tre lacune di §8 non contraddicono questo giudizio — lo confermano. Sono tutte e tre **interazioni fra documenti**, invisibili dall'interno di ciascuno: l'impronta dei permessi vive fra architettura e sicurezza, il contesto societario fra architettura ed esecuzione asincrona, la deduplicazione fra modello semantico e ritenzione. Nessuna è un errore di progettazione; tutte e tre sarebbero diventate difetti in produzione, e D40 sarebbe stata la più difficile da trovare, perché non produce errori.

Restano tre decisioni aperte, e una sola conta davvero: **D7**. Senza clienti pilota il corpus non esiste, e senza corpus il cancello di D2 non può essere aperto — il che significa che il prodotto può essere costruito ma non può crescere oltre la sola lettura. È il vincolo su cui vale la pena agire per primo, e non è un vincolo tecnico.

---

## 13. Questioni emerse dall'implementazione — parte 2

Sei questioni emerse **scrivendo il contratto**, non rileggendolo. Nessuna era visibile prima: cinque sono lacune o contraddizioni interne al corpus documentale, la sesta è un difetto del generatore del corpus. Sono qui perché toccano vocabolari chiusi e testo normativo, e per §10 modificarli richiede una decisione, non un emendamento.

**Stato: tutte deliberate il 28/07/2026** su delega dell'Architect. L'analisi di **D87** è in §14, quella di **D88–D91** in §15. **D92** non era una decisione ma un elenco di difetti del generatore, ed è corretta. Le voci che seguono restano come traccia del problema che ciascuna ha posto; la delibera è nelle sezioni indicate. Numerazione in continuità da D93.

### D87 — Il predicato della categoria (T5)

**Deliberata: ⊡ adottata con vincolo, 28/07/2026.** L'analisi che ha portato alla delibera, con l'opzione a costo zero che è stata cercata e scartata e i tre vincoli che ne discendono, è in **§14**.

### D88 — Come l'origine entra nello stato

**Origine.** §10.2 rende `origin` **obbligatorio su ogni elemento** dello stato. §6.1 dice che l'operazione trasporta la propria provenienza e confidenza agli elementi che produce. Nessuna sezione dice come `origin` venga determinato.

**Il problema.** Derivarlo dalla provenienza copre quasi tutto — un'operazione che cita le parole dell'utente produce un elemento `user` — ma non il caso che §17.1 turno 3 descrive di persona: `set_order` su un attributo testuale, dove il riferimento è dell'utente e la direzione `asc` è un'inferenza del modello, e lo stato atteso registra `origin: "inferred"`. Quell'atteso non è raggiungibile da nessuna busta esprimibile.

**Raccomandazione.** `origin` è una chiave **opzionale su ogni operazione**, che vince sulla derivazione dalla provenienza. Additiva, un solo campo.

**Limite che resta, e va dichiarato:** la granularità si ferma all'operazione. Nel caso di §17.1 turno 3 il riferimento e la direzione hanno origini diverse e la busta ne esprime una sola. Non intacca la misura dell'accuratezza — §14.3 regola 1 rimuove `origin` dalla forma canonica — ma intacca **A9**: l'interpretazione non può distinguere i due casi, e A9 è l'ipotesi su cui poggia la difesa contro R1. Una granularità per parametro è una modifica più invasiva e non è raccomandata adesso; è però il genere di cosa che §16 chiede di dichiarare in anticipo.

### D89 — Misure e vista lista: due sezioni si contraddicono

**Origine.** §5.6 e §12.5 dicono entrambe che uno stato con `measures` e vista `list` **non è valido**. §6.7 regola 3 **deriva esattamente quello stato**: misure presenti, nessun raggruppamento, vista `list`.

**Il problema.** Preso alla lettera, l'Applicatore produce uno stato che il Validatore deve respingere. Non è un caso limite: è la regola 3 su cinque della tabella di derivazione.

**Raccomandazione.** Vale §6.7 regola 3 nel caso che nomina, e il divieto si applica dove le due affermazioni non si sovrappongono: **misure con almeno un raggruppamento e vista `list`**. È il caso di cui §5.6 parla — un'aggregazione scomposta per dimensione, mostrata come elenco piatto, perde la scomposizione. Una misura senza raggruppamento è una riga aggregata, che un elenco mostra benissimo.

Se la delibera va nell'altro senso, va riscritta §6.7 regola 3, non il codice.

### D90 — Il vocabolario delle operazioni conta ventidue voci, non diciotto

**Origine.** §6.1 e il glossario di §21 dicono **diciotto**. Le cinque tabelle di §6.2–6.6 enumerano **ventidue**: 1 entità + 4 condizioni + 5 presentazione + 9 organizzazione + 3 sessione.

**Raccomandazione.** Le tabelle sono il contenuto normativo — un conteggio in prosa non può togliere un'operazione che ha una riga, una firma e una motivazione — quindi il vocabolario è di ventidue voci e i due conteggi in prosa vanno corretti. L'implementazione asserisce ventidue in un test, così la discrepanza non può essere riassorbita in silenzio.

### D91 — Due lacune nel vocabolario temporale

**Origine.** §9.2 fissa il vocabolario chiuso delle espressioni temporali. Traducendo il corpus ne emergono due assenze:

- **anno parziale.** *"Da inizio anno"* non ha simbolo: `current_year` è l'anno intero, che è un periodo diverso. È l'espressione più usata nei confronti gestionali;
- **assolute senza anno.** *"A gennaio"*, *"nel primo trimestre"*, *"a settembre"* richiedono l'istante di riferimento per essere risolte, e §5.10 lo esclude dallo stato.

**Raccomandazione.** Per la prima, una voce additiva (`year_to_date`, o `current_year_to_date`). Per la seconda, **nessuna estensione**: l'esito corretto è un chiarimento, perché *"a gennaio"* è genuinamente ambiguo fra l'anno in corso e il precedente, ed è esattamente la classe di caso per cui `clarification` è un esito di primo livello. La conseguenza pratica è sul generatore del corpus, non sul contratto.

### D92 — Difetti del generatore del corpus — ✅ **corretti il 28/07/2026**

Non sono decisioni sul contratto ma sul corpus, e stanno qui perché la misura viene da `ai/corpus/verifica_contratto.py` e perché D85 stabilisce il principio: **si corregge il generatore, non i suoi prodotti**.

| Difetto | Misura | Conseguenza |
|---|---|---|
| Le espressioni temporali sono **frasi italiane** nello stato atteso (*"nel primo trimestre"*), non simboli di §9.2 | 15 casi non mappabili; 135 condizioni temporali richiedono una tabella di traduzione | Lo stato atteso non è conforme a §9.2 sull'asse temporale |
| **Raffinamenti che non raffinano**: l'operazione attesa non cambia lo stato di partenza | 57 casi su 504 (11,3%) — `add_group` 23, `add_field` 22, `add_order` 6, `set_limit` 6 | Il caso non misura nulla: un modello che emettesse qualunque operazione idempotente lo supererebbe |
| I riferimenti sono **nomi tecnici Odoo** (`sale.order.amount_total`) usati come riferimenti semantici | Tutti i casi | Innocuo nella parte 2 — ai livelli 1–2 un riferimento è una stringa opaca — diventa un problema alla parte 3, quando il dizionario deve risolverli |
| Il filtro è una **lista piatta** senza connettivo, `order`/`verso` anziché `order_by`/`direction`, nessun `origin` sulle condizioni | Tutti i casi | Meccanico: l'adattatore lo traduce. Va comunque allineato, o l'adattatore diventa un secondo contratto da mantenere |

**Corretti alla fonte il 28/07/2026**, secondo il principio di D85: si corregge il generatore, non i suoi prodotti. Il corpus è stato rigenerato con lo stesso seme, ed è deterministico. Esito: **948 casi su 948 verificati end-to-end**, da 876. L'adattatore fra corpus e contratto è stato **rimosso** anziché mantenuto — era un secondo contratto da tenere allineato per dieci anni.

**Un quinto difetto è emerso automatizzando la verifica**, e non era in questo elenco perché nessuno lo aveva misurato: `11` §6 segnava *«nessun duplicato esatto di frase, soglia < 2%»* come **da automatizzare**. Misurato: **29,6%**. `fuori_ambito` aveva 11 frasi distinte per 72 casi, `incompreso` 5 per 48. La dimensione del corpus è ciò su cui poggia la soglia di rumore di **D48**, e 1 200 righe con 845 frasi non sono 1 200 casi. Corretto con testi composti al posto delle liste fisse e una deduplicazione che dichiara la saturazione: ora **1,0%**.

Resta aperto il solo punto che dipende da **D91**: *"da inizio anno"* è fuori dal corpus finché non esiste un simbolo per l'anno parziale.

---

## 14. Delibera di D87 — il predicato della categoria

| | |
|---|---|
| **Decisione** | Il contratto ammette il predicato `is_category`, senza valore, per nominare una **condizione nominata T5** |
| **Stato** | ⊡ **Adottata con vincolo** — tre vincoli, tutti prerequisiti della parte 3 |
| **Autorità** | Architect, delega esercitata il 28 luglio 2026 |
| **Modifica** | `03-specifica-dsl.md` §8.1 — voce additiva, MINOR per §15.2 |

### 14.1 Il problema, in una riga

`06` §3.6 definisce **T5** come *"condizione nominata"*: un termine dell'azienda che corrisponde a una condizione, non a un attributo. D30 la richiede in Fase 1. `03` §8.1 enumera i predicati **per tipo di attributo**, e una categoria non ha attributo, non ha operatore e non ha valore: non esiste riga della tabella sotto cui possa stare.

Misura di quanto pesa: **652 casi su 948** del corpus fondativo (68,8%) usano almeno una categoria.

### 14.2 L'opzione a costo zero, cercata e scartata

Prima di aggiungere un simbolo va cercata l'alternativa che non ne aggiunge nessuno, perché §7.3 e §3.9 la impongono come preferenza dichiarata: **arricchire il dizionario anziché ampliare la grammatica**. Quell'alternativa esiste, ed è la ragione per cui questa delibera non era ovvia.

> **Opzione G.** Il dizionario espone la categoria come **attributo booleano** dell'entità — `ordini_vendita.da_fatturare` di tipo booleano — e la condizione diventa `{ref, predicate: "is_true"}`. Nessun simbolo nuovo, nessun MINOR, nessuna modifica allo schema.

G regge a quattro controlli su cinque: l'interpretazione mostra ancora il termine aziendale, la propagazione di §15.6 è preservata perché la risoluzione avviene a ogni esecuzione, la verifica tipo/predicato di livello 4 è coerente, e il catalogo non cambia forma.

**Cade sul quinto, e cade in modo grave.**

**Un attributo booleano ammette `is_false`.** Che cosa significa `is_false` su `fatture_cliente.scadute`? La categoria è definita come `payment_state != paid AND invoice_date_due < oggi`. La sua negazione non è la negazione di un campo: è la negazione di una congiunzione, e comprende le fatture pagate *e* quelle non ancora scadute. Chi scrive *"le fatture non scadute"* aspettandosi le seconde ottiene anche le prime. Nessun errore, nessun avviso, un numero diverso e credibile — la forma canonica di **R1**.

Con `is_category` quel caso è **inesprimibile**: il predicato non ha polarità, e la negazione passa dal connettivo `not` dell'albero, dove la semantica è definita e ispezionabile. È il criterio **C3** — impossibilità strutturale al posto del divieto — applicato al posto giusto.

**Il secondo argomento contro G è di governo, ed è quello che chiude la questione.** D29 distingue *vocabolario* — allarga ciò che il sistema riconosce, non cambia alcun risultato esistente — da *definizione*, che cambia i risultati e richiede versionamento, tracciamento e notifica ai proprietari delle interrogazioni salvate (`06` §6.4, §15.6). `06` §3.9 classifica **T5 come definizione**. Esposta come attributo booleano, una categoria diventa indistinguibile da `clienti.attivo`, che è un campo reale e puro vocabolario. La distinzione su cui poggia l'intero meccanismo di notifica si perde **nel punto esatto in cui viene applicata**.

D29 è una delle sette decisioni portanti, e la sua motivazione è *«rende impossibile la modalità di guasto che non produce errori ma numeri diversi, tutti plausibili»*. G la riaprirebbe.

### 14.3 Le altre alternative

| Opzione | Esito |
|---|---|
| **A** — predicato `is_category`, senza valore, ammesso sui soli riferimenti di tipo categoria | **Adottata** |
| **B** — riusare `is_true` su un riferimento di categoria non dichiarato booleano | Respinta: gli stessi difetti di G, più una verifica di livello 4 priva di senso |
| **C** — espandere la categoria nelle condizioni sottostanti prima che il DSL la veda | Respinta: metterebbe una definizione dentro lo stato (contro §1.4), la soglia corretta smetterebbe di propagarsi alle interrogazioni salvate (contro §15.6), e l'interpretazione mostrerebbe la soglia anziché il termine — perdendo la ragione per cui T5 esiste |
| **E** — nuova sezione dello stato, `categories`, parallela a `filter` | Respinta: una categoria fuori dall'albero non può partecipare a `any` né a `not`, e *"ordini da fatturare o scaduti"* diventerebbe inesprimibile. Aggiunge inoltre una sezione, che è una modifica più invasiva di un predicato |
| **G** — categoria come attributo booleano del dizionario | Respinta in §14.2 |

### 14.4 Verifica contro gli otto criteri di §3

| Criterio | Esito |
|---|---|
| **C1** vocabolario chiuso | Un simbolo enumerato, ammesso su un tipo dichiarato |
| **C2** semantico mai tecnico | Migliora: senza, il modello non può nominare il termine e dovrebbe ricostruire la soglia, che è conoscenza tecnica |
| **C3** impossibilità strutturale | `is_category` non ha valore: una categoria con polarità è inesprimibile, non vietata da un controllo |
| **C4** nessuna espressione arbitraria | La condizione è un nome, non un'espressione |
| **C5** determinismo | La risoluzione è deterministica sul dizionario |
| **C6** provenienza obbligatoria | Invariata: una condizione di categoria porta origine e provenienza come ogni altra |
| **C7** estensibilità additiva | MINOR per §15.2. Un lettore 1.0 che riceve `is_category` lo **respinge** (§15.3, D14), che è il fallimento corretto |
| **C8** confrontabilità | Una sola forma per una condizione di categoria; sotto G ne esisterebbero due |

Nessun conflitto con i quattro obiettivi. Sulla **scalabilità** c'è un guadagno che vale dichiarare: una categoria sostituisce N condizioni nel contesto trasmesso al modello, quindi riduce la pressione sul budget del catalogo di **D79**.

### 14.5 I tre vincoli

Sono parte della decisione: rimuoverli è modificare la decisione, non semplificarla (§10). Tutti e tre sono prerequisiti della **parte 3**.

**V-D87-1 — Una categoria non compare nel catalogo di un utente che non può leggere i campi che la definiscono.**

Altrimenti D87 apre un percorso verso dati non autorizzati con accuratezza e latenza normali, che è la violazione di **V2** più difficile da notare. Il meccanismo esiste già: ogni voce T5 dichiara i propri `campi_implicati`, e il filtro sui permessi di `06` §5.9 precede la selezione.

**Il meccanismo è però incompleto oggi, e la verifica lo ha mostrato:** in `ai/corpus/lessico_l1.json` la categoria `sottoscorta` ha condizione `qty_available < reordering_min` e dichiara `campi_implicati: ["qty_available"]` — **`reordering_min` manca**. Un utente senza accesso a quel campo riceverebbe la categoria. Da qui la forma normativa del vincolo: **i campi implicati sono l'insieme completo dei campi che la condizione tocca, e se non è calcolabile la categoria è esclusa** — fallimento in sicurezza, come per l'impronta di D39.

**V-D87-2 — Il costo di una categoria entra nella validazione di livello 5.**

Una categoria può nascondere un costo non banale: l'esempio di `06` §3.6 è *"clienti importanti"* = `fatturato ultimi 12 mesi > 50.000`, che è un'aggregazione su un'altra entità. Senza una stima dichiarata nella voce, il costo dell'interrogazione risultante non è calcolabile a priori, che è precisamente la proprietà che **D12** esiste per garantire.

**V-D87-3 — L'Applicatore non espande mai una categoria; la risolve il Risolutore, a ogni esecuzione.**

La condizione di una categoria può dipendere dal tempo: `fatture_scadute` è `payment_state != paid AND invoice_date_due < oggi`. Espanderla in applicazione violerebbe la purezza dell'Applicatore e la riproducibilità del corpus (**D82**), e congelerebbe una definizione nello stato. Il Risolutore è l'unico componente consapevole del tempo (`04` §4.6), ed è lì che la categoria diventa un frammento di condizione.

### 14.6 Un difetto di classificazione rilevato di passaggio

`lessico_l1.json` elenca fra le categorie la voce `fatturato`, la cui condizione dichiarata è *"somma di amount_untaxed su fatture confermate"*. Non è una condizione: è una **grandezza**, quindi una voce **T4 — Metrica**, non T5. La distinzione conta perché T4 è il tipo che `06` §3.5 definisce *"il più pericoloso"* — un errore lì produce numeri credibili e sbagliati — e perché T4 non serve in Fase 1 mentre T5 sì (§6.5). Da correggere nella parte 3, insieme ai `campi_implicati` di `sottoscorta`.

---

## 15. Delibera di D88–D91

Quattro decisioni deliberate il 28 luglio 2026 su delega dell'Architect, con lo stesso metodo di §14: si cerca prima l'opzione che non modifica il contratto, e la si adotta se regge.

### D88 — Come l'origine entra nello stato

**Stato: ⊡ adottata con vincolo.**

**Il problema.** §10.2 rende `origin` obbligatorio su ogni elemento dello stato. §6.1 dice che l'operazione trasferisce provenienza e confidenza a ciò che produce. **Nessuna sezione dice come `origin` venga determinato**, e §17.1 turno 3 descrive un atteso che nessuna busta esprimibile raggiunge: `set_order` su un attributo testuale, dove il riferimento è dell'utente e la direzione `asc` è un'inferenza, e lo stato registra `origin: "inferred"`.

**Delibera.** `origin` è una chiave **opzionale su ogni operazione** e vince sulla derivazione dalla provenienza (presente → `user`, assente → `inferred`). Additiva, un campo.

**Ma la parte importante di questa delibera è il vincolo, non la chiave.** Prima di aggiungere un campo si è chiesto **chi deve decidere** la direzione. La risposta di **P4** è netta: *ogni informazione che può essere derivata deterministicamente non deve essere richiesta al modello.* Ascendente per un attributo testuale e discendente per una data **sono** derivabili — dal tipo dell'attributo, che vive nel Dizionario. Chiederla al modello viola P4 due volte: aggiunge una decisione probabilistica dove ne bastava una tabella, e la aggiunge nel punto in cui sbagliarla produce l'errore meno visibile che questo prodotto possa fare.

> *«Gli ultimi cinque ordini»* ordinati in modo ascendente restituisce **i cinque più vecchi.** Cinque record, il numero giusto, l'attributo giusto, la risposta esattamente rovesciata.

**V-D88-1 — La direzione non ha un valore predefinito.** L'Applicatore **rifiuta** `set_order` e `add_order` senza direzione anziché assumere `asc`. Chi conosce il tipo — il Risolutore — la deriva e dichiara la propria regola. È la stessa disciplina di `add_field` sui campi predefiniti: ciò che questo componente non può sapere non lo inventa.

**V-D88-2 — La regola di §17.1 turno 3 ha un nome.** `text_attribute_implies_asc`, aggiunto all'insieme chiuso degli identificativi di regola. Un'inferenza che l'interfaccia non può nominare è un'inferenza che l'utente non può contraddire, e D65 gradua la salienza proprio su questo.

**Limite residuo, dichiarato e non risolto.** La granularità di `origin` si ferma all'operazione, e tre sezioni su sette hanno elementi con **due** parametri decidibili separatamente: `order_by` (riferimento + direzione), `group_by` (riferimento + granularità), `measures` (riferimento + funzione). Con V-D88-1 il caso più frequente — la direzione — esce dal problema, perché diventa una derivazione di sistema con regola dichiarata. Resta la **granularità**: *«raggruppa per data»* → per giorno o per mese? §5.6 dichiara l'ambiguità e non dice chi la scioglie, e non è derivabile dal tipo.

Non si estende ora. Non per pigrizia, ma perché la decisione richiede un dato che non abbiamo: **D73** valida A9 per iniezione controllata, e **D53** misura la correttezza della provenienza come indicatore proprio. Se gli utenti non notano una granularità inferita, quei due strumenti lo mostrano, e allora l'estensione ha un'evidenza. Estendere adesso significherebbe scegliere fra due forme — origine per parametro, oppure un elenco di parametri inferiti con la loro regola — sulla base di un'intuizione. §3.9 dice di non farlo.

### D89 — Misure e vista lista

**Stato: ⊡ adottata con vincolo.**

**Il problema.** §5.6 e §12.5 dicono che uno stato con `measures` e vista `list` non è valido. §6.7 regola 3 **deriva** quello stato: misure presenti, nessun raggruppamento, vista `list`. Alla lettera l'Applicatore produce ciò che il Validatore deve respingere. §5.6 aggiunge una terza affermazione — *«`measures` compare solo con viste Pivot e Grafico»* — che contraddice anch'essa la regola 3.

**Le due letture possibili.**

| | Lettura 1 — **adottata** | Lettura 2 |
|---|---|---|
| Regola 3 di §6.7 | Resta: misure senza raggruppamento → `list` | Va riscritta: → `pivot` |
| Il divieto | Misure **con almeno un raggruppamento** e vista `list` | Incondizionato |
| §5.6 alla lettera | Va corretta | Resta vera |

**Perché la lettura 1.** Non perché la regola 3 sia più specifica — sarebbe un argomento formale su due enunciati normativi di pari rango. Perché **le due letture sbagliano in modi diversi**, e uno dei due modi è peggiore.

Chi chiede *«quanto abbiamo fatturato questo mese»* sotto la lettura 1 ottiene l'elenco delle fatture con il totale in fondo: la risposta c'è, più righe che non aveva chiesto, e una frase basta a passare a pivot. Sotto la lettura 2, chi chiede *«mostrami la lista con il totale»* ottiene un **rifiuto**.

E quel rifiuto colpisce un comportamento **nativo di Odoo**: la vista lista mostra le somme di colonna da sempre. Rifiutarlo contraddice il principio del prodotto additivo di `02` §4.6 — *un risultato conversazionale indistinguibile dalla prima pagina di una vista nativa*. **Una lettura che può negare una risposta perde contro una che non può.**

**V-D89-1 — Quando ci sono misure e la vista è `list`, il Presentatore mostra l'aggregato nel piede di colonna**, come fa Odoo nativamente. È ciò che rende onesta la lettura 1: senza, la misura è nello stato e invisibile nel risultato, e lo stato direbbe una cosa che la schermata non mostra — violazione diretta di **V4**. Requisito della parte 7.

**Da correggere in `03`:** la frase di §5.6 e la riga di §12.5 vanno riformulate nella forma condizionata. §6.7 regola 3 resta.

### D90 — Il vocabolario delle operazioni conta ventidue voci

**Stato: ☑ adottata.**

§6.1 e il glossario di §21 dicono **diciotto**. Le cinque tabelle di §6.2–6.6 enumerano **ventidue**: 1 + 4 + 5 + 9 + 3.

Verificato che nessuna combinazione di rimozioni dia diciotto senza cancellare righe che portano firma e motivazione propria: le tre di sessione (§6.6) porterebbero a 19, le due sulle misure a 20. Il numero è **stantio**, non una specifica.

**Delibera.** Le tabelle sono il contenuto normativo — un conteggio in prosa non può togliere un'operazione che ha una riga, una firma e una motivazione. Il vocabolario è di ventidue voci; i due conteggi in prosa vanno corretti. L'implementazione asserisce ventidue in un test, così la discrepanza non può essere riassorbita in silenzio.

Nessun vincolo: nessuna metrica e nessuna riga di codice dipendeva dal numero diciotto.

### D91 — Due lacune nel vocabolario temporale

**Stato: ⊡ adottata con vincolo.**

**Prima lacuna — l'anno parziale.** *«Da inizio anno»* non ha simbolo. `current_year` è l'anno **intero**, che è un periodo diverso.

Fare nulla non è un'opzione neutra, e vale la pena vedere perché. L'espressione è perfettamente comprensibile, quindi `clarification` sarebbe sbagliato — il sistema chiederebbe di qualcosa che ha capito. L'esito corretto sarebbe `out_of_scope`, ma `scope_note` è un insieme **chiuso** e non ha una categoria per *«periodo non esprimibile»*: fare nulla costringerebbe quindi ad aggiungere una categoria di `scope_note`, cioè a modificare comunque un vocabolario chiuso, per dire che non sappiamo dire una cosa che diremmo con un simbolo.

**Delibera: si aggiunge `year_to_date`.** Uno, non la famiglia. `month_to_date` e `quarter_to_date` sono l'estensione naturale e sono deliberatamente assenti: §3.9 aggiunge espressività quando i dati la chiedono, e i dati ne chiedono una. L'elicitazione di **D85** è lo strumento che mostrerebbe se servono le altre.

**V-D91-1 — `year_to_date` si risolve contro l'inizio dell'**esercizio fiscale**, come `current_year`.** §9.2 lo dice già per l'anno corrente e spiega perché conta: in un'azienda con esercizio non solare, restituire da gennaio produrrebbe un numero sbagliato di aspetto perfettamente credibile — la forma canonica di R1 sui dati aggregati.

**Seconda lacuna — le assolute senza anno.** *«A gennaio»*, *«nel primo trimestre»*, *«a settembre»*. Risolverle richiede l'istante di riferimento, che §5.10 esclude dallo stato, e ammettono più letture: l'anno in corso o il precedente.

**Nessuna estensione.** L'esito corretto è `clarification`, che è un esito di primo livello proprio per questo (§4.4, §11.4). Il contratto non va esteso, va usato. Il corpus fondativo le genera già come casi di chiarimento.

---

## 16. Questioni emerse dall'implementazione — parte 3

Quattro rilievi su `06-modello-semantico.md` §5.5, tutti emersi **misurando** e non rileggendo. Tre sono letture o difetti del documento; il quarto è una regola nuova, ed è proposta.

### 16.1 L'esempio del refuso non soddisfa la regola che illustra

§5.5 fissa la corrispondenza approssimata a **distanza di edit ≤ 1** e la illustra con *"mostrami le fatuere scadute"* che corrisponde a *fatture*. Le due parole sono a distanza **2** con qualunque metrica standard, trasposizione inclusa: `fatuere` → `fatture` richiede `u`→`t` e `e`→`u`, che non è uno scambio di caratteri adiacenti.

**La regola resta, l'esempio è sbagliato.** Alzare il limite a 2 farebbe corrispondere *letture* a *fatture* — due sostituzioni, una parola senza rapporto, e precisamente la corrispondenza sbagliata che nessun errore segnala e che il margine non sempre intercetta. Asserito in un test, così l'allentamento non può rientrare dalla finestra.

La **trasposizione** di caratteri adiacenti è invece inclusa, come parametro e non come decisione: è l'errore di battitura più comune, e `misura_catalogo.py` misura la quota risolta con e senza. Una scelta su intuizione è ciò che §3.9 vieta; una sulla misura è ciò che chiede.

### 16.2 Sopra 0,70 il livello approssimato è codice morto

§5.5 ammette tre livelli — esatto 1,00, forma base 0,90, approssimato 0,70 — e poi chiede *«migliore ≥ SOGLIA»*. Con una soglia superiore a 0,70 il livello approssimato non può decidere nulla: il livello che §5.5 illustra con un refuso diventa decorazione.

Ne segue una precisazione che vale più del valore: **la soglia non è la protezione, il margine lo è.** Il compito della soglia è essere alzabile — a 0,90 il percorso rapido smette di risolvere i refusi, configurazione legittima per un'installazione che preferisce chiedere. Valore iniziale **0,70**, scelto sulla misura.

### 16.3 Fase A si applica solo quando l'entità non è nota

Già in §5.5 (*"primo turno o dopo `reset`"*), e riportato qui perché la prima misura lo ha violato e il costo è stato istruttivo: applicando Fase A anche ai raffinamenti, **116 determinazioni sbagliate su 1 200**. La causa è la forma base italiana: *"ordina per cliente"* — imperativo del verbo — ha forma base `ordin`, identica al termine dell'entità *ordini*.

Un raffinamento ha già il proprio `target` nello stato. Farlo passare per il percorso rapido non è inutile: è sbagliato, e produce l'errore peggiore disponibile — un'entità diversa e plausibile su una richiesta che non chiedeva alcuna entità.

### 16.4 D93 — Un attributo batte un'entità sulla stessa porzione di frase

**Stato: ☐ proposta.**

**Il problema, misurato.** Corretto §16.3, restavano **7 determinazioni sbagliate su 696**, tutte della stessa forma: la testa del sintagma è danneggiata — la perturbazione del corpus abbrevia *"fatture cliente"* in *"fatt. cliente"* (D83) — e resta a corrispondere il solo modificatore *cliente*, che ha forma base identica all'entità *clienti*. Esito: `clienti` invece di `fatture_cliente`, con accuratezza e latenza normali.

Cinque delle sette si chiudono **arricchendo il dizionario**, come §7.3 impone: un'abbreviazione che gli utenti usano è un sinonimo, e un sinonimo è vocabolario L1. Indicizzate le forme abbreviate, la quota risolta è passata dal 78,9% all'83,3% e le sbagliate da 7 a 2 — dati, non grammatica.

Le due residue no, e la scelta era fra due rimedi. La misura:

| Rimedio | Quota risolta | Determinazioni sbagliate |
|---|---|---|
| Soglia a 1,00: si rimuove il livello forma base | 78,4% | 0 |
| **Guardia proposta** | **86,2%** | **0** |
| Nessuno dei due | 83,3% | 2 |

**Delibera proposta.** Una porzione di frase è evidenza di entità **solo se nessun termine di attributo corrisponde a quella stessa porzione almeno altrettanto bene.**

Non è una raffinatezza: è ciò che rende usabile il livello della forma base. Alzare la soglia a 1,00 elimina le determinazioni sbagliate eliminando il livello, e con esso la risoluzione di *"mostrami la fattura"* al singolare — dove non si sta indovinando nulla, perché singolare e plurale di una parola sono una parola. **Scartare l'evidenza ambigua è meglio che scartare un livello di corrispondenze corrette**, e la misura quantifica la differenza in otto punti di percorso rapido, cioè in chiamate al modello risparmiate.

La guardia è deterministica, si calcola sullo stesso indice, e non richiede nulla che il dizionario non abbia già.

**Realizzata** in `nli_semantics/catalogue/phases.py`, con il test che mostra sia il caso che chiude sia quello che non deve bloccare.

### 16.5 L'impronta dei permessi non e' leggibile dalle tabelle delle regole

**Rilievo dall'esecuzione, non dalla rilettura.** D39 elenca fra i componenti dell'impronta *"stato delle regole di accesso ai modelli"* e *"stato delle regole sui record"*. La prima realizzazione le leggeva da `ir.model.access` e `ir.rule`, e su un database reale un utente interno ordinario non puo':

> `odoo.exceptions.AccessError: You are not allowed to access 'Model Access' (ir.model.access) records.`

E `sudo` non e' disponibile: il controllo sintattico di D24 lo vieta, correttamente, perche' una lettura privilegiata qui sarebbe un percorso privilegiato dentro la catena di interrogazione (**V2**). La lacuna non era aggirabile — era da riprogettare.

**L'impronta si costruisce sugli effetti osservabili**, e la sostituzione risulta piu' corretta della formulazione originale, non un ripiego:

| Componente di D39 | Come si osserva |
|---|---|
| Accesso al modello | `has_access("read")` — la domanda stessa, anziche' la configurazione che la risponde |
| Accesso a livello di campo | L'insieme delle chiavi di `fields_get()`, che gia' esclude i campi i cui `groups` l'utente non ha |
| Gruppi, contesto societario, lingua | `env.user.groups_id`, `env.companies` (**D40**), `env.lang` |
| **Regole sui record** | **Deliberatamente assenti** |

`fields_get` e' la stessa chiamata che il catalogo usa per costruirsi: l'impronta non puo' quindi essere in disaccordo con cio' di cui e' impronta, mentre una lettura separata della tabella ACL potrebbe.

**Perche' le regole sui record non appartengono alla chiave del catalogo.** Una regola sui record cambia quali **record** vengono restituiti. Il catalogo contiene **riferimenti** — nomi di entita' e di attributi — e mai un record: A6 e V7 lo garantiscono. Una modifica a una regola sui record non puo' quindi cambiare il contenuto del catalogo, e metterla nella chiave invaliderebbe la memorizzazione a ogni evento che non puo' influenzare il risultato.

Le regole continuano ovviamente ad applicarsi, in esecuzione, dove i record ci sono. D39 le elenca perche' la sua impronta chiave anche il riuso delle **interpretazioni**; se quel riuso verra' costruito, avra' bisogno di una chiave propria, e questa nota e' il luogo in cui la differenza e' registrata.

**Nessuna modifica a D39**: le due proprieta' normative — fallimento in sicurezza e invalidazione a evento come sola ottimizzazione — valgono immutate. Cambia la materia da cui l'impronta si calcola.

### 16.6 La regola sui contesti privilegiati e' scoped, come dice §6.3

Il controllo sintattico di D24 vietava `sudo` e `with_user` in **ogni** file dei moduli `nli_*`. `04` §6.3 dice invece *"nessun uso di contesti privilegiati **nei percorsi di interrogazione**"*, e l'applicazione estesa aveva una conseguenza che si e' vista scrivendo i test: **un test che verifica che cosa un altro utente puo' vedere deve costruire l'ambiente di quell'utente.** Vietarlo rende non verificabile la proprieta' che il divieto protegge, e una proprieta' di sicurezza che nessuno puo' testare e' peggio di una che nessuno puo' aggirare.

Il controllo ora esclude `tests/` e `pure_tests/` dalla sola regola sull'elevazione di privilegio. **Nessuna esclusione per l'SQL diretto**: un cursore grezzo in un test resta un cursore grezzo, e V3 non ha percorsi. Entrambe le proprieta' sono asserite in `tools/arch/tests/`.
