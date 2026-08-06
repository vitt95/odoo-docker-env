# Registro delle Decisioni Architetturali

## AI Agent per Odoo — Natural Language Interaction Layer

| | |
|---|---|
| **Documento** | `00-registro-decisioni.md` |
| **Natura** | Documento di governo — vive per tutta la durata del progetto |
| **Copre** | D1–D96, con l'articolazione D20a–D20f |
| **Fonti** | `02-visione-prodotto.md` §19 · `03-specifica-dsl.md` §20 · `04-architettura.md` §17 · `05-esecuzione-asincrona.md` §10 · `06-modello-semantico.md` §13 · `07-piano-valutazione-qualita.md` §17 · `08-sicurezza-conformita.md` §13 |
| **Autorità decisionale** | Architect — delega esercitata in questa sede |
| **Delibera** | 27 luglio 2026 |
| **Stato complessivo** | **94 decisioni adottate** (di cui 20 con vincolo), **5 superate**, **1 aperta** — **D7**, che resta aperta per volontà esplicita: nessun corpus sintetico la soddisfa |

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
| **D54** | **Pseudonimizzazione degli enunciati all'ingresso**, mappatura separata e cifrata | ☑ Adottata | La pseudonimizzazione retroattiva non esiste: ogni giorno senza produce dati in chiaro che nessuna decisione successiva ripulisce. Cancellare una riga di mappatura è esatto e dimostrabile; cercare un nome in dodici mesi di testo non lo è | · ⊘ **Il meccanismo per la cronologia è superato da D115** (§23): l'enunciato resta sul turno in chiaro. Il resto di D54 vale ancora.
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
| **D93** | Guardia attributo/entità in Fase A: una porzione di frase è evidenza di entità solo se nessun termine non di entità la copre altrettanto bene | ⊡ Adottata con vincolo | §16.4. Deliberata su delega dell'Architect il 28/07/2026. **Non tocca il contratto**: è una regola di risoluzione, non di DSL. Misurata: 86,2% di percorso rapido contro 78,4% dell'alternativa, a pari zero determinazioni sbagliate. **V-D93-1** in §16.4 |
| **D94** | `nli_dispatch`, il modulo che compone la catena | ⊡ Adottata con vincolo | §17.1. Scartate `nli_web` (P5) e il nucleo con composizione tardiva: quell'arco il controllo di D24 non lo vedrebbe. **V-D94-1** |
| **D95** | Due deroghe a V3 ristrette per file, chiamata e forma dell'enunciato | ⊡ Adottata con vincolo | §17.2. `FOR UPDATE SKIP LOCKED` sulla coda e un cursore per thread. Scartate la claim ORM (insicura al secondo dispatcher) e lo sharding per `id % N` (una partizione senza esecutore, in silenzio). **V-D95-1** |
| **D96** | L'enunciato in coda è transitorio e cifrato, mai in chiaro | ⊡ Adottata con vincolo | §17.3. Non è pseudonimizzazione e non pretende di esserlo: nulla è conservato. Fallimento chiuso senza chiave, come D77. **V-D96-1** |
| **D97** | Adattatore sintetico per il solo banco di carico, dietro variabile d'ambiente | ⊡ Adottata con vincolo | §18.1. Non è un profilo, non è in `PROTOCOLS`, non passa da D75 né da D80. Fallimento chiuso senza la variabile, busta costante, `warning` a ogni ciclo. **V-D97-1** |
| **D98** | Il profilo dichiara lo **sforzo di ragionamento**, e la chiave viaggia solo se nominata | ☑ Adottata | §18.2. Misurato: ragionamento acceso, 2397 gettoni contro una finestra di 4096 e **busta vuota**; a `none`, 179 gettoni e busta valida. `reasoning_effort` è campo standard del protocollo: D75 non si allarga |
| **D99** | La **direzione dell'ordinamento** è derivata dal tipo prima dell'applicazione, mai chiesta al modello | ☑ Adottata — **adempie D88** | §18.3. D88 aveva assegnato la derivazione al Risolutore, che non l'ha mai fatta. La regola è dichiarata dallo stato e derivata dalla direzione inferita, perché §15.3 vieta chiavi ignote in un'operazione |
| **D100** | I comparativi **inclusivi** sono distinti da quelli stretti nel lessico e nel generatore | ☑ Adottata | §18.4. *«almeno»*, *«da … in su»*, *«non più di»*, *«entro i»* comprendono l'estremo. L'atteso chiedeva `greater_than` dove la frase diceva `greater_or_equal`: il metro penalizzava la lettura corretta |
| **D101** | I **riferimenti** sono un insieme chiuso nello schema del turno | ☑ Adottata | §18.5. C1 da prosa a struttura. Misurato: riparazioni dal 25% al 5%, rese da 2 a 0, `order_by` da 70% a 97,5%. Senza catalogo lo schema resta quello generale, che è ciò che `emit_schema.py` scrive |
| **D102** | I riferimenti hanno **tre generi** — entità, attributi, categorie — e ogni operazione ammette solo il proprio | ☑ Adottata | §18.5. D101 aveva chiuso l'insieme lasciandolo piatto, e il modello ha chiesto un'entità come colonna. Una categoria è solo la condizione: dietro non c'è un campo da mostrare |
| **D103** | Il **predicato** e' vincolato dal tipo dell'attributo gia' nello schema del turno | ☑ Adottata | §18.7. §8.1 accoppiava tipo e predicati e solo il livello 3 lo leggeva: *«clienti sopra i 1000»* era scrivibile. Misurato: +5 casi su `filter`, riparazioni dal 3,6% al 2,9%. Un tipo non dichiarato conserva l'insieme intero |
| **D104** | Il vocabolario del catalogo e' **mostrato all'utente**, suggerito e mai imposto | ☑ Adottata | §19.5. Scartato il perimetro obbligatorio con tre argomenti (`13` §3). La struttura la deriva la zona pura dal catalogo dell'utente che chiede, le parole del prodotto le mette lo strato che ha una lingua |
| **D105** | Una **condizione nominata** non fondata nel proprio frammento e' rifiutata al livello 3 | ☑ Adottata | §19.1. Misurato su 80 aperture: **11 filtri sbagliati diventati rifiuti, 0 filtri corretti rifiutati**. Il confronto e' con la provenienza, non con l'enunciato, perche' un raffinamento porta avanti le condizioni dei turni precedenti. Riconoscitore condiviso con la Fase A |
| **D106** | Il rifiuto di D105 **propone**: `clarification` con letture derivate dal catalogo | ☑ Adottata | §19.2. Le opzioni sono derivate, mai chieste al modello (P4): chi ha appena inventato una condizione e' l'ultimo a cui chiedere le alternative. Meno di due letture, nessuna domanda |
| **D108** | Le voci di dizionario **approvate** hanno un registro, e la condizione tipizzata si traduce in dominio | ☑ Adottata | §19.4. Senza, il dizionario vivo era **solo L0**: le proposte di D35 restavano nella coda L3 e nessuna installazione aveva una condizione nominata. La traduzione va dalla condizione tipizzata al dominio — meccanica — mai al contrario, che sarebbe una supposizione (`06` §7) |
| **D109** | La mappa dei tipi di campo (`char`→`text`, `monetary`→`number`) è una **zona pura**, fuori dall'introspezione | ☑ Adottata | §20.1. Dodici coppie uguali in ogni installazione: un fatto, non una domanda a un sistema vivo. Chiusa dentro il file che importa l'ORM di Odoo, impediva di costruire il catalogo fuori dalla piattaforma — e il comando che misura l'accuratezza non partiva affatto |
| **D128** | **Una domanda che facciamo deve avere risposte che funzionano** | ☑ Adottata | §37. Il modello ha offerto quattro opzioni con un `within` senza periodo: il clic applicava fedelmente qualcosa di inapplicabile. Le opzioni si validano quando la domanda si **memorizza**, non quando qualcuno clicca; sotto due utilizzabili non e' un chiarimento. Fin li' avevamo contato **quante** opzioni c'erano e mai **se funzionavano** |
| **D129** | **Il livello 5 gira intero**: tetto ai record, salti di relazione e costo delle categorie sullo stesso percorso | ☑ Adottata | §39.1. `coherence.validate_cost` non era chiamata da nessuno e `category_costs` non lo passava nessuno: il massimo assoluto di 500 di **D13** era scritto e inapplicato. Provato — `set_limit` a un milione passava struttura, stato e livelli 3-5 e arrivava all'Esecutore. Un utente ordinario poteva togliere disponibilita' a tutti scrivendolo in italiano |
| **D130** | **L'Esecutore ha una porta sola**, e le aggregazioni si calcolano | ☑ Adottata | §39.2. `executor.aggregate` esisteva, era provata e **non aveva chiamanti**: `SUM`, `AVG`, `MIN` e `MAX` erano nel contratto, nel piano e nell'interpretazione mostrata all'utente, e nessuno li calcolava. *«Qual e' il fatturato medio dei lead»* restituiva l'elenco dei lead. Due funzioni pubbliche erano la scelta che il chiamante sbagliava: adesso `run` decide dal piano |
| **D131** | **Gli estremi di un periodo si convertono in UTC** quando la colonna e' un istante | ☑ Adottata | §39.3. Odoo conserva i `datetime` in UTC, il calendario ragiona nei giorni dell'utente, e nessuno convertiva: *«i lead creati oggi»* escludeva quelli di stanotte e includeva quelli di ieri sera. Due ore su una finestra di un giorno sono l'8% delle righe, e il campo colpito e' `create_date`, che **D117** ha appena rimesso nel catalogo. Il fuso viaggia come **nome** e non come scostamento, perche' l'ora legale lo cambia |
| **D132** | **Il piano arriva intero alla tabella**: ordinamento, raggruppamenti e misure | ☑ Adottata | §39.4. `_aida_query` calcolava `order` e `fields` e il componente OWL non li usava: la vista rileggeva il solo dominio. *«I 10 lead col fatturato piu' alto»* mostrava dieci righe ordinate da tutt'altro, sotto un'interpretazione che dichiarava l'ordinamento giusto. Le misure non partivano affatto, e pivot e grafico ricadevano sul conteggio |
| **D133** | **La finestra dichiarata e quella servita sono due numeri, e si guardano vicini** | ☑ Adottata | §39.5. Misurato su `ollama`: dodicimila gettoni mandati, **2050 letti**, nessun errore. L'adattatore non manda la finestra al fornitore — il protocollo non ha un campo per dirla — quindi divergono in silenzio. E il contatore dei rifiuti per budget di **D79** esisteva da sempre senza lettori: con 4096 il budget vale **17** attributi contro il tetto di 60, il che toglie a **D32** la proprieta' con cui chiude **RC3** |
| **D134** | **Una risposta si prova sul suo contenuto**, non sul suo esito | ☑ Adottata | §39.6. La regola di §38 non bastava: sette degli undici scollegamenti trovati dall'audit erano nello stesso tratto — fra il piano e lo schermo — e passavano perche' **nessuna prova andava da uno stato a un numero**. Il banco delle risposte confronta i nomi in ordine, la media col suo valore, il conteggio per gruppo. Rimesse a mano le regressioni, diventa rosso su quattro casi |
| **D127** | **Chi nomina la propria entita' fa una domanda nuova**, chi non la nomina raffina | ☑ Adottata | §36. Lo stato si accumulava e non c'era modo di ricominciare parlando: un filtro sulla mail rispondeva a una domanda che non lo nominava. La fase A gira sempre — cinque centesimi di secondo, il dizionario e non il modello — e chi porta il proprio soggetto riparte da vuoto. Chiude anche il cambio di entita', che era impossibile |
| **D126** | **Un'entita' si chiama come la chiama la gente**: etichetta, pezzi, menu | ☑ Adottata | §35. Ogni entita' aveva un termine solo, l'etichetta grezza `Lead/Opportunità`, che nessuna frase contiene: fase A a **0 su 8** sul database vero, 6 su 8 dopo. Le parole si raccolgono dall'installazione, non si generano — il plurale e' gia' scritto nel menu che l'utente preme. §35.1: il guardiano vale contro le prove morfologiche, non contro quelle esatte. §35.2: il registro dichiarava T1 approvabile e ne rifiutava ognuno |
| **D125** | **Un periodo nuovo prende il posto del precedente** sullo stesso attributo | ☑ Adottata | §34. La regola di §33.2 rifiutava invece di riparare: al terzo turno sulla stessa data la conversazione era **bloccata senza via d'uscita**, e ogni tentativo di rimediare peggiorava lo stato. Ora l'Applicatore sostituisce, e uno stato gia' rovinato si ripara parlando. Il rifiuto e' giusto solo se chi lo riceve ha una mossa |
| **D124** | **Una strada sola verso lo schermo**; due periodi sullo stesso attributo sono un rifiuto | ☑ Adottata | §33. Il Presentatore produce una struttura, `in_words` la fa parole, e non lo chiamava nessuno: **nessuna risposta riuscita e' mai stata disegnata**. §33.2: due periodi sullo stesso asse si intersecano invece di raffinare, e il conteggio non cambia — 39 e 39 — quindi non si vede. §33.3: il livello 4 girava a meta', `coherence` non era sul percorso. §33.4: le tabelle di `15` sono la vista lista di Odoo incorporata |
| **D123** | **La modalita' diagnostica viaggia con il turno**: DSL, stato, query e tempi | ☑ Adottata | §32. Quando un turno va storto conta una domanda sola — nel modello o dopo? — e la risposta stava in dati che il sistema aveva e buttava via. Sul turno e non nei log, perche' D60 vieta frasi e cataloghi li' dentro; visibile solo a un amministratore, perche' l'interruttore dice se la traccia esiste, non chi puo' vederla. §32.1: al primo giro ha misurato la fase B a 113 s contro 33 dell'interpretazione |
| **D122** | **Il tempo concesso al modello lo dichiara il profilo**, non una costante dell'adattatore | ☑ Adottata | §31. Il modello in servizio impiegava 60,1 s per chiamata e l'adattatore ne concedeva 60 fissi: **nessuna domanda poteva riuscire**. Non esiste il numero giusto — un modello locale impiega minuti, uno ospitato secondi — quindi si dichiara, come la finestra di D78. §31.1: il guasto arrivava all'utente come «non ho capito», che invita a riformulare una frase che era già giusta |
| **D121** | **Una strada sola per il clic e per lo scritto**: l'opzione si sceglie dicendone l'etichetta | ☑ Adottata | §30. Le operazioni di ogni lettura sono gia' nella busta (D106): riconoscerne una costa niente, interpretarla costa un minuto di modello e puo' riscoprire la lista diversa. Il clic scrive l'etichetta nella casella e la invia, quindi non esiste una seconda strada da tenere allineata. La provenienza della condizione scelta e' l'etichetta, ed e' vera: sono le parole che l'utente ha appena detto |
| **D120** | Una frase che **risponde a una domanda** porta con se' lo scambio precedente | ☑ Adottata | §29. Una richiesta di chiarimento non produce operazioni, quindi non scrive stato: il contesto spariva esattamente nel punto in cui serviva di piu'. Due stringhe, non la trascrizione: un prompt che cresce con la durata della chat consuma la finestra che serve alla risposta |
| **D119** | Il frammento citato da un rifiuto deve **contenere le parole** che chiedono quella cosa | ☑ Adottata | §28. D118 rendeva obbligatorio citarne uno, non che dicesse qualcosa: restava possibile rifiutare citando un pezzo qualunque della frase. Il lessico sta in `nli_semantics` e arriva iniettato, perche' e' di lingua e `nli_core` non ne ha |
| **D118** | Un **rifiuto per portata deve citare il frammento** che chiede la cosa impossibile | ☑ Adottata | §27. `out_of_scope` costava quanto una risposta ed era l'uscita che il modello prendeva ogni volta che faticava: nove rifiuti su 414 con nota `previsione`, e «mostrami i lead di quest'anno» classificato come cancellazione di record. Ora il rifiuto si guadagna con la stessa prova di qualunque altra risposta |
| **D117** | `create_date` **non e' un campo di sistema**: e' esposto come gli altri | ☑ Adottata | §26. *«Quando e' stato creato»* e' una domanda di lavoro, non un dettaglio tecnico. Misurato sul campo: a «i lead di quest'anno» l'ancora del tempo offriva chiusura, conversione, scadenza e assegnazione — quattro date, e non quella che una persona intende |
| **D116** | La superficie della piattaforma di `nli_web` si allarga a **`base_setup`**, per la sezione AIDA nelle impostazioni generali | ☑ Adottata | §24. Il modello si configura dal pannello, come vuole **D75**. La vista delle impostazioni generali sta in `base_setup` e non c'e' altro aggancio. Il pannello **configura e non attiva**: D80 continua a rifiutare un profilo non qualificato |
| **D115** | L'**enunciato dell'utente resta sul turno, in chiaro** — supera D54 per la sola cronologia | ☑ Adottata — **dall'Architect** | §23. Una chat la cui cronologia non puo' rimostrare all'utente le proprie parole e' un altro prodotto. Cio' a cui si rinuncia e' scritto e non attenuato: **un dump del database contiene le frasi digitate**. A proteggerle resta la regola di record del turno, non piu' la cifratura |
| **D113** | Su una data l'intervallo si dice **`within`**, e `between` resta l'intervallo numerico | ☑ Adottata | §22.1. Il contratto ammetteva due parole per lo stesso fatto e il corpus ne accetta una. Non emergeva finché il modello sbagliava il campo: con l'ancora di D110 è rimasta l'unica differenza su **11 casi di 414**, cioè 2,7 punti contati come errori mentre erano legali |
| **D114** | Un **periodo che seleziona record esistenti non è fuori portata**, e il prompt lo dice | ☑ Adottata | §22.2. Nove rifiuti su 414 uscivano con `scope_note: "previsione"`, fra cui *«ordini lo scorso mese»*. L'elenco delle cose fuori portata nominava «una previsione» e «un calcolo nel tempo», e un'espressione temporale ci finiva per somiglianza |
| **D110** | Il catalogo dichiara **l'ancora del tempo**: una data se ne espone una sola, l'insieme delle scelte se sono due o più, nulla se non ce ne sono | ☑ Adottata | §21.1. Un'espressione di tempo non nomina mai il proprio campo, né nel corpus né in italiano: si dice *«ordini del mese scorso»*. Nessuna euristica su quale data conti di più — sceglierne una fra due plausibili è indovinare. L'ancora si calcola dagli attributi già filtrati dai diritti e dal budget |
| **D111** | Un'espressione di tempo **non può essere lasciata cadere**: se non si colloca, si chiede | ☑ Adottata | §21.2. Oggi lasciar cadere un pezzo di frase non costa niente al modello, perché la busta senza quella condizione resta valida. La regola toglie l'uscita di sicurezza che D110 da sola lasciava aperta |
| **D112** | Le categorie ammesse dalla generazione vincolata sono quelle **nominate dalla frase**, non tutte quelle del catalogo | ☑ Adottata | §21.3. `is_category` è l'unica condizione senza appiglio lessicale, e per questo era la discarica di ogni frammento non collocabile. La frase si conosce prima dello schema, quindi la categoria infondata diventa inesprimibile invece che rifiutata dopo. Stesso riconoscitore di D105, passato come argomento |
| **D107** | Modello di riferimento: **`qwen3.5:9b`** | ☑ Adottata — **dall'Architect** | §18.8. Deliberata il 29/07/2026 su basi architetturali, con il confronto empirico contro `granite4.1:8b` **interrotto prima di produrre un numero**. Le ragioni sono in §18.8, e cosi' e' il limite della delibera |

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
| ~~Gli enunciati non sono mai persistiti in chiaro~~ — **non vale più**: **D115** (§23) tiene l'enunciato sul turno in chiaro, e a proteggerlo è la regola di record, non la cifratura. Resta vero per la **coda**, che continua a sigillarlo e a cancellarlo (**D96**) | **D54** ⊘ **D115** | Prova P-7, da riscrivere su ciò che è ancora vero |
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

**Per aggiungere una decisione**: numerazione in continuità da **D129**. **D128** è deliberata in §37. **D127** è deliberata in §36. **D126** è deliberata in §35. **D125** è deliberata in §34. **D124** è deliberata in §33. **D123** è deliberata in §32. **D122** è deliberata in §31. **D121** è deliberata in §30. **D120** è deliberata in §29. **D119** è deliberata in §28. **D118** è deliberata in §27. **D117** è deliberata in §26. **D116** è deliberata in §24. **D115** è deliberata in §23. **D113** e **D114** sono deliberate in §22, dalla rimisura di §21.7. **D110**, **D111** e **D112** sono deliberate in §21, dalla proposta `14-ancoraggio-del-tempo.md`. **D109** è deliberata in §20. **D104**, **D105** e **D106** sono deliberate in §19, insieme a **D108** che ne era il presupposto mancante. D87–D91 sono deliberate (§14, §15); D92 è corretta; **D93** è deliberata (§16.4.1); **D94–D96** sono deliberate in §17; **D97–D103** e **D107** in §18.

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
| 2026-07-28 | **Parte 6 completa — esecuzione asincrona.** Tre delibere in §17, tutte con l'opzione conservativa cercata per prima e scartata con argomento: **D94** (il modulo `nli_dispatch` che compone la catena — il nucleo con composizione tardiva avrebbe comprato il grafo rendendolo non verificabile), **D95** (due deroghe a V3 ristrette per file, chiamata e **forma dell'enunciato**, con sei test che le mostrano ammettere e rifiutare), **D96** (l'enunciato in coda transitorio e cifrato, con la coda separata dal turno perche' non abbia un campo in cui una domanda possa finire — C3). Due irrigidimenti dei controlli trovati scrivendo D95: `cursor` da solo (una chiamata in mezzo alla catena evadeva la regola) e l'uid letterale in `Environment(cr, 1, {})`, che e' `sudo` scritto diversamente. Due rilievi: l'impronta dei permessi era **per utente** contro la lettera di D39 (§17.4), e i tipi di `fields_get` non sono i tipi di §8.1 (§17.5). **D27 non e' superata e lo strumento lo dichiara**: 20 utenti conversazionali, ERP P95 da 21,8 a 14,7 ms — cioe' rumore — su uno stack senza `--workers`, senza profilo attivo e con 37 partner. Il numero informativo e' l'accettazione a **P95 205 ms** contro i 50 ms di §6.1. |
| 2026-07-28 | **Prima qualificazione di un profilo, e cinque delibere in §18.** Fornitore spostato su `ollama` nativo con Metal (il container non ha GPU) e modello di riferimento **`qwen3.5:9b`** — Apache 2.0, denso, 256K, la taglia piu' capace che entra in 16 GB. Tre guasti di configurazione trovati misurando, nessuno dei pesi: finestra servita a 4096 contro 262144 dichiarati, ragionamento acceso che spende il contesto prima di rispondere (**D98**), `presence_penalty 1.5` cotto nel tag che lavora contro una busta ripetitiva. Poi **tre difetti del metro**, non del modello: la direzione dell'ordinamento fissata a `desc` anche su cio' che data non e' (**D99**, che adempie l'obbligazione lasciata aperta da D88), i comparativi inclusivi contati come stretti (**D100**), e soprattutto `ref` come stringa libera nello schema (**D101**): C1 era prosa, ora e' struttura, e con essa le riparazioni passano dal 25% al 5% e `order_by` da 70% a 97,5%. **D97** registra l'adattatore sintetico del banco di carico. **Misura finale su tutte le 444 aperture**: accuratezza complessiva **63,5%** (era 15% su 20 casi), `target` 98,0%, `fields` **87,2%**, `group_by` 93,0%, `order_by` 93,0%, `limit` 93,5%, `measures` e `presentation` 98,0%. **Sette sezioni su otto sopra la soglia di D44**; resta sotto `filter` a **72,5%**, che e' il prossimo bersaglio e ha gia' la sua leva strutturale — i predicati vincolati dal tipo dell'attributo, la stessa mossa di D101 e D102. Il profilo resta quindi `draft` e **D80 continua a rifiutarne l'attivazione**, che e' il comportamento voluto. Riparazioni 3,6%, latenza media 8511 ms contro i ~2,5 s che D5 lascia all'interpretazione: **la latenza non si qualifica su questo portatile**, come D27. Due misure in §18.6 che non sono decisioni ma cambiano cosa si puo' affermare: la **confidenza dichiarata dal modello discrimina** — ma solo dopo aver tolto dal prompt il `0.9` che il modello copiava: 0 esatti su 5 sotto 0,95 contro 23 su 33 sopra, cioe' la proposta dell'Architect e' sostenuta dalla misura corretta e smentita da quella viziata e la **soglia di rumore di D48 e' zero** (sigma 0,0% su cinque esecuzioni identiche), il che rende esatti i confronti sullo stesso campione e lascia intatta l'incerteza campionaria di +/-13 punti su 40 casi. |
| 2026-07-28 | **D93 deliberata su delega dell'Architect: ⊡ adottata con vincolo** (§16.4.1). Cercata e scartata l'opzione che non aggiunge alcuna regola — tenere il livello della forma base e accettare **2 determinazioni sbagliate su 696** — perche' una determinazione sbagliata di entita' non e' un errore ma un elenco di record veri in risposta a un'altra domanda, cioe' **R1**. La portata e' **piu' larga della proposta**: il confronto e' contro ogni termine **non di entita'**, categorie T5 comprese, perche' l'argomento non e' che gli attributi siano speciali ma che una porzione di frase gia' spiegata non e' evidenza di entita'. **V-D93-1**: il confronto e' sulla stessa porzione, mai globale — una guardia globale perderebbe l'entita' in *«ordini di vendita raggruppati per cliente»*. Quando scatta, Fase A rende `no_candidate` e il turno passa al modello: la regola non puo' produrre un'entita' sbagliata, al massimo rinuncia a una giusta. |
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

**Stato: ⊡ adottata con vincolo, 28/07/2026**, su delega dell'Architect. La delibera è in §16.4.1; quanto segue è l'analisi che l'ha prodotta.

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

### 16.4.1 Delibera di D93

**Adottata con vincolo.** Prima di adottarla è stata cercata l'opzione che non aggiunge una regola, come impone il metodo di §14 e §15: qui è la riga *«nessuno dei due»* della tabella sopra — si tiene il livello della forma base e si accettano **2 determinazioni sbagliate su 696**. È stata scartata, e la ragione non è la percentuale.

Una determinazione sbagliata di entità non produce un errore: produce `clienti` al posto di `fatture_cliente`, cioè un elenco di record veri, con accuratezza e latenza normali, in risposta a una domanda diversa. È la forma canonica di **R1**, la stessa modalità di guasto per cui sono state deliberate **D29**, **D40** e il vincolo **V-D88-1**. Un prodotto che l'ammette per non aggiungere una regola deterministica di sei righe sta pagando la propria semplicità con la valuta sbagliata. L'altra alternativa — soglia a 1,00 — la elimina, ma eliminando il livello che risolve *«mostrami la fattura»*, dove non si indovina nulla: costa **otto punti** di percorso rapido, cioè chiamate al modello, cioè latenza e budget, per una proprietà ottenibile senza perderli.

**La regola vale, e la sua portata è più larga della formulazione proposta.** La proposta di §16.4 dice *«nessun termine di attributo»*; la realizzazione confronta contro **ogni termine non di entità**, quindi anche le categorie **T5**. È la lettura corretta e va scritta così: l'argomento non è che gli attributi siano speciali, è che una porzione di frase già spiegata da un altro riferimento non è evidenza di entità. Una categoria che copre la stessa porzione è controprova almeno quanto un attributo — anzi di più, perché una categoria è una **definizione** (D29) e nominarla è un atto più deliberato che nominare un campo.

**V-D93-1 — Il confronto è sulla stessa porzione di frase, mai globale.** La guardia scarta un candidato di entità solo se un termine non di entità corrisponde **allo stesso intervallo** (inizio e lunghezza) con punteggio pari o superiore. Una guardia che confrontasse i punteggi migliori a livello di frase — *«c'è un attributo che ha corrisposto meglio da qualche parte»* — sopprimerebbe entità legittime ogni volta che la frase nomina un campo, che è il caso ordinario: *«ordini di vendita raggruppati per cliente»* perderebbe l'entità. La forma per intervallo è ciò che rende la regola una **disambiguazione** anziché una soppressione, ed è la sola misurata. Asserita in `pure_tests/test_catalogue.py` da due test: quello che mostra la guardia scattare e quello che mostra che non blocca un'entità legittima quando l'attributo copre la stessa porzione solo per forma base.

**Direzione del fallimento.** Quando la guardia scatta, l'esito di Fase A è `no_candidate`: il turno prosegue in Fase B o C, cioè con il modello. La regola non può quindi produrre un'entità sbagliata — al massimo rinuncia a una giusta, e la rinuncia costa una chiamata, non un numero credibile e falso. È l'orientamento di **D33**: il margine distingue una corrispondenza da un'ipotesi, e un'ipotesi si scarta.

**Nessuna modifica al contratto**, a `03` né allo schema: D93 vive interamente dentro `06` §5.5, che descrive la risoluzione. `06` §5.5 va integrata con la regola.

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

---

## 17. Questioni emerse dall'implementazione — parte 6

L'esecuzione asincrona non ha aggiunto una funzione al prodotto: ha fatto girare per la prima volta la catena **fuori da una richiesta HTTP**, ed e' li' che le tre questioni che seguono sono diventate visibili. Tutte e tre sono state deliberate cercando prima l'opzione che non modifica nulla, come §14.2, e tutte e tre sono state scartate con un argomento.

### 17.1 D94 — Il modulo che compone la catena

**⊡ Adottata con vincolo, 28/07/2026.**

Il ciclo di `05` §3.3 e' *catalogo → interprete → validatore → applicatore → risolutore → esecutore*: ha bisogno del modulo che costruisce il catalogo (`nli_semantics`) e di quello che parla al modello (`nli_engine`), e `04` §6.3 vieta a ciascuno dei due di dipendere dall'altro — e' la separazione fra chi conosce i dati e chi conosce il fornitore, e regge V5. Fino alla parte 5 la catena non era mai stata composta: nella parte 4 i pezzi erano assemblati a mano dentro un test.

**L'opzione che non aggiunge un modulo, cercata per prima.** Il grafo di §6.2 gia' contiene un modulo che sta sopra tutti, `nli_web`. Metterci il dispatcher non richiederebbe alcuna decisione. E' stata scartata per **P5**: l'interpretazione e' indipendente dal canale che l'ha richiesta, e un'installazione che usasse solo un'API dovrebbe installare il canale di chat per poter eseguire un turno. La responsabilita' dichiarata di `nli_web` in §6.2 e' *«canale chat, presentazione»*, e un pool di thread con controllo di carico non e' nessuna delle due.

**La seconda opzione, piu' tentante, e' quella che si e' dovuto argomentare.** Il dispatcher poteva stare in `nli_core`, che gia' possiede il turno, con interprete e dizionario risolti a tempo di esecuzione attraverso il registro dei modelli di Odoo (`env["nli.semantics"]`, `env["nli.interpreter"]`) invece che per import. Nessun modulo nuovo, grafo invariato, e la composizione tardiva e' il meccanismo idiomatico della piattaforma.

E' stata scartata per una ragione sola, e vale la pena scriverla: **quell'arco il controllo di D24 non lo vede.** Il primo controllo legge i manifest e gli import; una dipendenza espressa come stringa dentro `env[...]` non e' ne' l'uno ne' l'altro. Si sarebbe comprata la proprieta' «le dipendenze puntano verso il nucleo» rendendola non verificabile — cioe' esattamente il modo in cui, in questo progetto, una regola smette di funzionare senza dirlo. Un modulo dichiarato costa una riga in `spec.py` e mantiene l'arco sotto controllo.

**`nli_dispatch`**, responsabilita' *«accettazione, coda, dispatcher, controllo di carico, notifica»*, dipende da `nli_semantics`, `nli_engine` e dalla piattaforma `bus`. `nli_web` dipende ora da `nli_dispatch` anziche' da `nli_semantics`: il canale chiede l'accettazione, non costruisce cataloghi.

**V-D94-1 — Il nucleo non sa di essere dispatchato.** `nli_core → nli_dispatch` entra fra le non-dipendenze nominate: e' la regola della parte 2 (*«la catena non presuppone mai di girare dentro una richiesta HTTP»*) vista dall'altro lato, ed e' cio' che ha permesso a questa parte di essere un involucro invece di una riscrittura. Verificata dal primo controllo.

### 17.2 D95 — Le due deroghe a V3, ristrette per file e per forma

**⊡ Adottata con vincolo, 28/07/2026.**

`05` §3.3 specifica l'acquisizione del lotto come `SELECT … FOR UPDATE SKIP LOCKED`, e su di essa poggia il percorso di scala di D20f (*«la capacita' si aggiunge con N record dispatcher»*): due dispatcher possono estrarre insieme solo perche' una riga bloccata viene **saltata** anziche' attesa. L'ORM di Odoo non sa esprimerlo, e Odoo stesso scrive quella riga a mano (`ir_cron.py:140`). Servono inoltre **un cursore per thread**: il fallimento di un turno non deve annullare gli altri del lotto (§3.4), quindi il cursore del cron non e' riusabile.

**Le due opzioni che non toccano V3, cercate e scartate.** La prima: acquisire con l'ORM (`search` poi `write`). E' sicura **oggi**, perche' V-A da' a un record `ir.cron` una sola esecuzione concorrente in tutto il cluster; smette di esserlo il giorno in cui qualcuno aggiunge il secondo dispatcher, cioe' quando nessuno sta guardando, e D20f dichiara quel passaggio *senza modifiche al codice*. La seconda: partizionare la coda per `id % N`, che non richiede alcun blocco. Scartata perche' introduce un guasto silenzioso: se N smette di corrispondere al numero di dispatcher, un'intera partizione resta senza esecutore — turni che nessuno prende, nessun errore da nessuna parte. Fra un enunciato SQL ristretto e una configurazione che esegue silenziosamente nulla, il rischio minore e' l'enunciato.

**V-D95-1 — La deroga e' per file, per chiamata e per forma dell'enunciato.** Una deroga che ammettesse un *file* ammetterebbe ogni enunciato che qualcuno vi scrivera' poi leggendo l'esenzione e non l'argomento. `spec.py` dichiara quindi: in `nli_dispatch/runtime/claim.py` e' ammesso `cr.execute` **solo** con un enunciato che contiene `SELECT id FROM nli_queue_item` e `FOR UPDATE SKIP LOCKED` e non contiene join, scritture o punti e virgola; in `nli_dispatch/runtime/worker.py` e' ammessa **solo** l'apertura del cursore, e nessun `execute`. Un enunciato costruito a tempo di esecuzione non e' ammesso: e' il modo ovvio di aggirare una forma. Sei test in `tools/arch/tests/` mostrano la deroga ammettere e rifiutare.

**Due irrigidimenti trovati mentre la si scriveva**, entrambi difetti preesistenti del controllo:

- `odoo.registry(db).cursor()` ha una **chiamata in mezzo alla catena**, quindi il controllo leggeva solo la coda `cursor` e la regola, scritta su `registry.cursor`, non scattava. Una regola che un paio di parentesi evade non e' una regola: ora `cursor` e' vietato da solo;
- **V2 aveva una seconda forma non coperta.** `Environment(cr, 1, {})` e' `sudo` scritto diversamente, e non contiene ne' `sudo` ne' `SUPERUSER_ID`. La regola nuova non riguarda il costruttore ma **l'uid**: dev'essere un valore letto dal turno, mai un letterale. Un uid scritto a mano non puo' venire dalla richiesta che dovrebbe rappresentare.

### 17.3 D96 — L'enunciato attraversa un confine di processo, e non in chiaro

**⊡ Adottata con vincolo, 28/07/2026.**

L'accettazione gira su un worker HTTP, l'interpretazione su un processo cron, e l'unico canale fra i due e' la banca dati: la parte 6 e' il primo punto del prodotto in cui la frase dell'utente deve **sopravvivere alla richiesta che l'ha portata**. Fino a qui non aveva mai toccato lo storage — la parte 4 arriva a rimuovere `provenance` dallo stato proprio per questo. La regola vincolante e' una riga di §9: *«nessun enunciato persistito in chiaro»* (**D54**), e il meccanismo di D54 — pseudonimizzazione all'ingresso con mappa cifrata separata — non esiste ancora.

**L'opzione che non decide nulla e' impraticabile, non scomoda.** Non c'e' un modo di passare la frase al processo cron che non sia la banca dati; il bus non e' un canale di dati e il cron non eredita nulla. Restava scrivere in chiaro per trenta secondi, che e' esattamente cio' che D54 dice non essere riparabile dopo: *«ogni giorno senza produce dati in chiaro che nessuna decisione successiva ripulisce»*.

**Quello che D96 stabilisce e' piu' stretto e disponibile ora.** L'enunciato e' **transitorio, non conservato**: vive nella riga di coda fra accettazione e interpretazione, limitato da L4 a trenta secondi, ed e' **cancellato nella stessa scrittura** che porta il turno a uno stato finale — riuscito, fallito, scaduto o sostituito. Finche' e' li' e' **cifrato con una chiave che sta nell'ambiente** (`NLI_UTTERANCE_KEY`), quindi una copia della banca dati non contiene frasi: e' l'argomento di D76 applicato a un altro segreto. Senza la chiave l'accettazione **rifiuta**, come `NLI_ALLOWED_HOSTS` sotto D77 — una protezione che degrada in silenzio a nulla e' peggio di una mai promessa.

**Non e' pseudonimizzazione e non da' la cancellazione per interessato.** Non ne ha bisogno: non conserva niente. Quando D54 arriva, la mappa sostituisce questo e la questione della ritenzione si sposta con lei, nello stesso cambiamento.

**V-D96-1 — La coda non ha un campo che possa contenere una domanda.** L3 (profondita' della coda) va valutata **all'accettazione**, con l'identita' di chi chiede, e quindi contando le righe **di tutti**; ma `nli.turn` porta `state_json`, che e' la domanda, ed e' protetto da una regola di record che lo limita al proprietario. La via d'uscita non e' allargare quella regola ma separare la coda dal turno: `nli.queue.item` porta una corsia, uno stato, due date e l'enunciato **cifrato**, e non ha alcun campo in cui una domanda possa finire. E' il criterio **C3** — impossibilita' strutturale invece di divieto da ricordare. Le righe sono quindi leggibili da ogni utente interno e scrivibili solo dal proprietario, e senza questa asimmetria L3 coinciderebbe con L1 e non esisterebbe.

### 17.4 L'impronta dei permessi era per utente, e D39 dice il contrario

Rilievo, non decisione: la delibera di **D39** enuncia la proprieta' che l'impronta compra — *«due utenti condividono l'impronta del catalogo solo se hanno gli stessi permessi, quindi il riutilizzo fra utenti non viola V2»* — e la realizzazione della parte 3 includeva nel materiale anche `env.user.id`. Con l'uid dentro, **due utenti non condividono mai un'impronta**: il dizionario e il catalogo si ricostruiscono per ogni collega che fa lo stesso genere di domanda, e su un'installazione da duecento utenti sono duecento costruzioni della stessa cosa. Fino alla parte 6 la cosa non si vedeva, perche' nessuno riusava niente.

L'uid non dice nulla su cio' che un utente puo' **nominare**: lo decidono i gruppi, le societa' attive, la lingua e lo stato di accesso osservabile — e due utenti identici in tutti e quattro possono nominare esattamente gli stessi riferimenti, che sono l'intero contenuto del catalogo. L'uid e' stato rimosso e la proprieta' e' ora asserita da un test.

### 17.5 I tipi di Odoo non sono i tipi del contratto

`fields_get` dice `char`, `many2one`, `monetary`; `03` §8.1 enumera i predicati su `text`, `relation`, `number`. I due non si erano mai incontrati: il pacchetto lessicale del corpus parla gia' la lingua del contratto, e il dizionario introspettivo e' arrivato solo qui. Un catalogo che pubblicizza `char` fa emettere al modello predicati che il livello 4 poi rifiuta, per una ragione che nessuna diagnostica nomina.

La mappa vive in `nli_semantics/introspection/runtime.py` — e' conoscenza di piattaforma — ed e' **passata** alla zona pura come argomento (`type_map`), assente il quale i tipi passano invariati. La regola di §5.9 non cambia: la zona che decide l'esposizione non acquisisce conoscenza della piattaforma.

### 17.6 Il criterio di completamento della parte 6, misurato per quello che e'

D27 chiede la prova di isolamento: con N utenti conversazionali continui, la latenza di Odoo per un utente ordinario non peggiora in modo misurabile. Lo **strumento** esiste (`tools/load/prova_isolamento.py`) e misura tre distribuzioni via HTTP: utente ordinario a vuoto, utente ordinario sotto carico, e percorso di accettazione.

**La prova non e' superata, ed e' una constatazione, non una cautela.** L'esecuzione del 28/07/2026 su questo portatile, con 20 utenti conversazionali a ritmo di una frase ogni tre secondi:

| Misura | P50 | P95 |
|---|---|---|
| Utente ordinario, a vuoto | 9,9 ms | 21,8 ms |
| Utente ordinario, sotto carico | 6,6 ms | 14,7 ms |
| Accettazione (§3.2) | 127,6 ms | **205,2 ms** |

Tre ragioni per cui la prima riga di questa tabella non e' la prova di D27, tutte dichiarate dallo strumento a ogni esecuzione: lo stack di sviluppo gira **senza `--workers`**, quindi il pool prefork la cui saturazione *e'* RA3 non esiste; non c'e' profilo attivo, quindi la fase che domina il tempo — l'interpretazione — non viene esercitata affatto; e la banca dati ha 37 partner. Il degrado misurato dell'ERP e' negativo, cioe' rumore.

**Il numero che invece e' informativo e' il terzo, e non e' buono.** §6.1 fissa l'accettazione a **P95 ≤ 50 ms**; qui e' 205 ms. L'accettazione fa oggi sei viaggi verso la banca dati — tre conteggi per i limiti, due creazioni, la riga di trigger del cron — sotto un server di sviluppo con log a livello debug. E' il primo bersaglio della taratura della parte 7, ed e' registrato qui perche' un numero misurato e brutto vale piu' di un numero asserito e bello.

---

## 18. Le delibere della qualificazione del profilo (28–29 luglio 2026)

Otto decisioni nate misurando un modello vero invece di ragionare su come si sarebbe comportato. Tre di esse correggono un difetto **nostro** che la misura attribuiva al modello, ed e' la ragione per cui questa sezione esiste: la prima misura di un fornitore non misura solo il fornitore.

### 18.1 D97 — Un fornitore finto con latenza vera, e perche' non e' una porta di servizio

La prova di isolamento di **D27** misura l'effetto del prodotto su chi non lo sta usando. Cio' che produce quell'effetto non e' l'accuratezza: e' il fatto che ogni turno tiene occupato un thread del pool e una connessione per un tempo dominato dall'attesa di rete. Senza un fornitore che risponda in quel tempo, la coda si svuota istantaneamente e la prova misura una coda vuota.

**L'opzione conservativa era usare il modello locale, e l'ho scartata con un argomento.** D80 rifiuta l'attivazione di un profilo non qualificato, e la regola e' giusta: un profilo lento dimezza la capacita' del dispatcher e la conseguenza cade sull'ERP. Aggirarla per fare una misura significherebbe rompere il presidio proprio nel momento in cui lo si sta verificando.

**V-D97-1 — Tre proprieta', tutte verificabili leggendo un file.** L'adattatore **non e' un profilo**: non e' in `PROTOCOLS`, non e' costruibile da una riga di `nli.profile`, non passa dalla macchina a stati. Vive dietro `NLI_LOAD_HARNESS` e **fallisce chiuso** senza di essa, come `NLI_ALLOWED_HOSTS` sotto D77. **Non amplia nulla**: la busta e' una costante del file, sempre valida secondo il contratto; non legge dati, non chiama nessuno, non ha credenziali — chi puo' impostare una variabile d'ambiente sul processo Odoo possiede gia' il processo. **Non passa inosservato**: ogni ciclo che lo usa emette un `warning` e ogni turno lo dichiara nel proprio esito. Un banco di prova dimenticato acceso si riconosce dai log, non dal comportamento.

### 18.2 D98 — Un modello che ragiona non e' un modello piu' lento

`qwen3.5:9b`, prima misura, prompt reale con il catalogo di `sale.order`:

| | prompt | completamento | contenuto |
|---|---|---|---|
| Ragionamento acceso (default del tag) | 1699 | 2397 | **vuoto** |
| `reasoning_effort: "none"` | 1701 | 179 | busta valida, 20,6 s |

`1699 + 2397 = 4096`, cioe' la finestra esatta. **Il modello ha speso l'intero contesto dentro il pensiero e non e' mai arrivato a rispondere.** Non e' latenza: e' assenza di risposta, e il turno sarebbe scaduto sul `timeout` di 60 s senza che nessuna metrica dicesse perche'.

**Cercata prima l'opzione che non tocca il contratto, e c'era.** Le alternative scartate: l'API nativa di ollama (`think: false`) funziona ma introdurrebbe un secondo protocollo, e **D75** chiude l'insieme; `chat_template_kwargs` e' stato **ignorato** dal server (misurato: 95,9 s e 7603 caratteri di pensiero); cuocere il parametro in un modello derivato sposterebbe una dichiarazione rilevante per la qualificazione in un artefatto fuori dal repository. `reasoning_effort` e' un campo **standard del protocollo OpenAI**: il profilo lo dichiara, e la chiave viaggia **solo se nominata**, perche' un fornitore che non la conosce risponde 400. E' la stessa forma di D78.

**Un secondo difetto trovato leggendo il Modelfile del tag**, e registrato perche' vale per ogni profilo locale: `PARAMETER presence_penalty 1.5`. La penalita' scoraggia i gettoni gia' usati, e la busta ripete `"ref"`, `"provenance"`, `"op"` a ogni operazione. E' un parametro che lavora **contro** il compito, e l'adattatore ne sovrascrive uno solo, `temperature`.

### 18.3 D99 — Un'obbligazione che D88 aveva assegnato e nessuno aveva adempiuto

**D88** rifiuta una direzione assente invece di metterla a `asc`, perche' crescente su una data trasforma *«gli ultimi cinque ordini»* nei cinque piu' vecchi — una risposta che sembra giusta ed e' esattamente rovesciata. E assegna la derivazione a chi conosce il tipo, il Risolutore. Il Risolutore legge `entry["direction"]` e non ne ha mai scritta una: **la direzione la dava il modello**, cioe' proprio cio' che P4 vieta e che §5.9 argomenta per la vista.

Il corpus, dal canto suo, fissava `desc` e `latest_implies_desc_by_date` su **ogni** attributo, `stato` e `team` compresi — una regola che nel nome dice *«per data»*, applicata a cio' che data non e'. Erano due delle sei perdite di `order_by` nella misura del 28/07.

**Il vocabolario chiuso conteneva gia' `text_attribute_implies_asc`**, aggiunto da D88 e mai emesso da nessuno. La verifica del contratto ha respinto al primo tentativo l'identificativo che avevo inventato — ed e' la dimostrazione che l'insieme chiuso funziona come presidio e non come formalita'.

Due vincoli di forma, entrambi imposti dal contratto e non scelti: l'operazione **non porta** `rule`, perche' §15.3 respinge le chiavi ignote in un'operazione e un'operazione e' una richiesta, non una spiegazione; lo stato **deve** portarla, perche' §10.2 vuole che un'inferenza dichiari cio' che l'ha prodotta, altrimenti l'utente non puo' contraddirla. L'Applicatore la deriva quindi dalla direzione inferita: stessa informazione, detta una volta sola.

### 18.4 D100 — Il metro premiava la lettura sbagliata

Il lessico aveva un gruppo per verso: `confronto_sopra` conteneva *«sopra i»*, *«oltre»*, *«piu' di»* insieme ad *«almeno»* e *«da … in su»*, tutti mappati a `greater_than`. Ma *«almeno 100»* e *«da 100 in su»* **comprendono** il 100, e i predicati `greater_or_equal` e `less_or_equal` erano gia' nel vocabolario numerico.

Misurato su F00648, *«budget da 100 in su»*: il modello ha risposto `greater_or_equal` ed e' stato contato **sbagliato**. Quattro gruppi ora, con scelta congiunta di frase e predicato, perche' nessuna combinazione possa dissociarli.

### 18.5 D101 — C1 smette di essere una frase nel prompt

`prompt.py` dichiara *«il modello sceglie, non inventa mai»*. Fino a questa decisione lo dichiarava soltanto: nello schema `ref` era `{"type":"string","minLength":1}`, quindi la generazione vincolata **non poteva** rifiutare un riferimento inventato, e i livelli 1–2 nemmeno — conoscono la forma di un riferimento, non il catalogo. Su quaranta casi il modello ha emesso `oppurtunita.fase`, `oppurtunaita.cliente` e un `importo_totale` senza entita': tutti passati, tutti finiti nello stato.

Dato il catalogo del turno, i riferimenti ammessi sono un insieme chiuso. Un riferimento fuori da quell'insieme **smette di essere esprimibile** invece di essere rimproverato: e' il criterio **C3**, quello che il progetto preferisce a ogni regola da ricordare.

Effetti misurati sugli stessi 40 casi, una variabile per volta:

| | prima | dopo |
|---|---|---|
| Riparazioni (D15) | 25% | **5%** |
| Rese (`out_of_scope` su frasi interpretabili) | 2 | **0** |
| `order_by` | 70% | **97,5%** |
| `limit` | 80% | **95%** |
| Latenza media | 11 049 ms | **9 472 ms** |

La latenza **scende** malgrado lo schema piu' grande (da 13 470 a 15 126 caratteri con 7 riferimenti), perche' il modello smette di sbagliare e di riparare.


**D102 — e cio' che D101 aveva lasciato aperto.** Chiuso l'insieme, restava piatto: il catalogo elenca anche **le altre entita'**, perche' la Fase A ne ha bisogno per risolvere il soggetto, e un insieme unico non distingue una colonna da un'entita'. Misurato: `set_fields` con `["fatture_cliente", ...]` due volte su quaranta, cioe' un'entita' chiesta come colonna — ammessa dallo schema, priva di senso nel contratto.

I riferimenti hanno quindi **tre generi**, e ogni operazione ammette solo il proprio: `set_target` prende un'entita'; `set_fields`, `add_group`, `add_order`, `add_measure` prendono un attributo; una condizione prende un attributo **o una categoria** (T5, D87). Scritto come dato — una tabella verbo → genere — e non come sequenza di rami, perche' la decisione e' la tabella.

Due direzioni, entrambe con un test: un'entita' non e' una colonna, e **un attributo non e' il bersaglio** — un'interrogazione il cui soggetto e' una colonna ha perso il soggetto. E una terza proprieta' trovata scrivendo la tabella invece che misurando: **una categoria non e' mai una colonna**, perche' dietro non c'e' un campo da mostrare.

L'entita' in corso viaggia insieme alle altre fra quelle ammesse: `set_target` deve poter cambiare soggetto, e un catalogo che ammettesse solo l'entita' corrente renderebbe il cambio inesprimibile.

Tre limiti dichiarati. L'identificativo di condizione (`c1`) resta libero: non e' un riferimento, e chiuderlo renderebbe `remove_condition` inesprimibile. Senza `refs` lo schema e' quello generale — un file su disco non puo' portare l'enumerazione di un turno, e `emit_schema.py` continua a scrivere quello. E un profilo **senza** generazione vincolata non ne beneficia affatto: per lui restano i livelli 3–5, che e' esattamente la degradazione prevista da `10` §5.1.

### 18.6 Due misure che non sono decisioni, e vanno registrate lo stesso

**La confidenza dichiarata dal modello discrimina, ma solo dopo che abbiamo smesso di dettargliela.** La prima misura diceva il contrario: su 40 casi `qwen3.5:9b` ha dichiarato `0.9` **quaranta volte su quaranta**, con 22 stati esatti e 18 sbagliati — nessuna soglia separa alcunche'. La causa era nostra: la forma della busta nel prompt conteneva `"confidence":0.9` come esempio, e il modello **copiava la costante**. Sostituita con un segnaposto, la stessa misura sugli stessi 40 casi:

| Fascia | Casi | Esatti |
|---|---|---|
| `[0,95 – 1,00]` | 33 | 23 = **70%** |
| `[0,90 – 0,95)` | 5 | 0 = **0%** |

Zero su cinque nella fascia bassa. Il numero porta informazione, e la proposta di un cancello sulla confidenza — avanzata dall'Architect e respinta dalla prima misura — **e' sostenuta dalla seconda**. Con due riserve che ne governano l'uso: cinque casi sono pochi per fissare una soglia, e il 70% nella fascia alta dice che `>= 0,95` **non garantisce** la correttezza. Un cancello li' trasformerebbe in richiesta di riformulazione circa il 12% dei turni, evitando altrettante risposte sbagliate e lasciandone passare comunque delle errate. La cautela di §10.5 — *«un segnale di ordinamento, non una probabilita'»* — resta esatta: e' ordinabile, non calibrata. La taratura e' il lavoro di **RC6**, e va fatta sulle 444 aperture prima che qualunque cancello di prodotto vi poggi sopra.

**La lezione di metodo, che vale piu' del risultato:** la prima misura non misurava il modello, misurava un nostro difetto. E' la terza volta in questa sezione — dopo D99 e D100 — e giustifica una regola: *prima di attribuire un esito al fornitore, verificare che non sia stato il prompt a dettarlo*.

**La soglia di rumore di D48 vale zero.** Cinque esecuzioni identiche sugli stessi 40 casi, temperatura 0 e generazione vincolata: `sigma = 0,0%` su **tutte** le sezioni, complessiva compresa. La stabilita' K=5 di D48 e' quindi al **100%**, non al 98%, e un confronto fra due versioni del prompt sullo stesso campione e' esatto: una differenza di un caso e' un risultato, non rumore.

Il limite di questa misura va detto con la stessa precisione, perche' e' quello che si confonde: `sigma = 0` misura la **ripetibilita'**, non la rappresentativita'. Quaranta casi su 444 aperture portano un'incertezza campionaria di circa **±13 punti** al 95%, e **nessuna soglia di D44 puo' essere dichiarata raggiunta su quaranta casi**.

### 18.7 D103 — Il predicato segue il tipo, e la tabella esisteva gia'

`03` §8.1 accoppia da sempre ogni tipo con i confronti che su di esso significano qualcosa, e il livello 3 la legge. Lo **schema** no: la condizione ammetteva qualunque predicato su qualunque riferimento, quindi un profilo con generazione vincolata poteva scrivere `less_than` su un nome o `contains` su un importo. Il rifiuto arrivava un livello dopo — come riparazione quando la coppia era impossibile, come **risposta sbagliata** quando era soltanto errata.

Con il catalogo la condizione diventa un ramo per tipo: i riferimenti di quel tipo, e solo i predicati che §8.1 gli concede. *«clienti sopra i 1000»* smette di essere scrivibile — un cliente non sta su una scala. E' la mossa di D101 e D102 applicata a cio' che si dice **a proposito** del riferimento invece che al riferimento.

Un attributo di tipo non dichiarato conserva l'insieme intero: indovinare quali confronti convengano a un tipo ignoto significherebbe inventare la tabella che §8.1 possiede.

**Guadagno misurato, e piu' piccolo del previsto**: `filter` da 72,5% a 73,6% su 444 aperture, cioe' cinque casi; riparazioni dal 3,6% al 2,9%. La previsione era «la stessa mossa di D101 e D102», che ne avevano spostati venti. L'errore di previsione ha una spiegazione utile: D101 e D102 rimuovevano l'**impossibile** — un riferimento inesistente, un'entita' chiesta come colonna — e quella era la classe dominante. I fallimenti residui di `filter` sono predicati **possibili e sbagliati**, che nessuna grammatica distingue.

**Un difetto di misura chiuso di conseguenza.** §17.5 aveva rilevato che i tipi di `fields_get` non sono i tipi di §8.1, e `build()` accetta per questo un `type_map`; lo strumento di misura del corpus non lo passava, quindi esercitava un catalogo con i tipi di Odoo (`many2one`, `selection`) che nessuna installazione produce. Finche' i tipi servivano solo a scrivere il catalogo era cosmetico; con D103, che ne deriva i predicati, diventa sostanziale. Ora `misura_accuratezza.py` passa `CONTRACT_TYPE_BY_ODOO_TYPE`, la stessa mappa dell'introspezione.

### 18.8 D107 — Il modello di riferimento, e cosa non sappiamo di lui

**Deliberata dall'Architect il 29/07/2026: `qwen3.5:9b`.** La registro con il suo limite in evidenza, perche' e' l'unica forma onesta.

**Cosa e' misurato.** Su tutte le 444 aperture del corpus, `qwen3.5:9b` con generazione vincolata e ragionamento spento porta sette sezioni su otto sopra la soglia di D44: `target` 98,4%, `fields` 88,1%, `group_by` e `order_by` 93%, `limit` 94,4%, `measures` e `presentation` 98,4%. Resta `filter` a 73,6%.

**Cosa non e' misurato, e va detto per primo.** Il confronto testa a testa con `granite4.1:8b` — Apache 2.0, 8,8 miliardi di parametri, 5,3 GB — e' stato **avviato e interrotto** su decisione dell'Architect prima di produrre un numero. Esiste una sola sonda su un caso: su `F00145` (*«voglio vedere ordini lo scorso mese i primi 5 ordinati per data documento»*), dove `qwen3.5:9b` produce una condizione nominata senza rapporto con la frase, `granite4.1:8b` produce la condizione temporale corretta nella forma sbagliata (`last_n_months` con `n=1` invece di `previous_month`) e prende anche il limite, che qwen perde. **Un caso non e' una misura**, e questa riga esiste perche' fra sei mesi nessuno possa credere che il confronto sia stato fatto.

**Le ragioni architetturali della scelta, che non dipendono dalla misura mancante.**

| | |
|---|---|
| **Multimodalita' nativa** | `qwen3.5:9b` dichiara `vision` fra le proprie capacita': testo e immagini nello stesso modello. `granite4.1:8b` e' solo testo, e IBM tratta le immagini con un modello separato della stessa famiglia |
| **Un modello invece di due** | La **Fase 6** di `02` §15 (voce e comprensione documentale) con granite richiederebbe un secondo modello, quindi un secondo protocollo di qualificazione **D51** — otto passi, prova di isolamento inclusa — per sempre, a ogni aggiornamento |
| **Copertura linguistica** | Oltre 200 lingue dichiarate contro la dozzina di granite. Ogni enunciato e ogni termine del dizionario sono italiani |
| **Licenza** | Apache 2.0 entrambi: nessuna differenza, e nessun vincolo su **D8** (tutte le modalita' di erogazione supportate) |

**Un rilievo a favore di granite, registrato perche' e' vero e perche' ha gia' fatto danno una volta.** Il pacchetto di `granite4.1:8b` **non porta parametri precotti**; quello di `qwen3.5:9b` ne porta tre, fra cui `presence_penalty 1.5`, che scoraggia i gettoni gia' emessi mentre la busta del contratto ripete `"op"`, `"ref"` e `"provenance"` a ogni operazione. E' un parametro che lavora contro il compito, l'adattatore ne sovrascrive uno solo (`temperature`), ed e' uno dei tre guasti di configurazione trovati in §18.2. **Chi mantiene questo profilo deve saperlo.**

**Cosa rimane aperto.** Se `filter` non salira' con le decisioni del perimetro guidato (D104–D106, proposte in `13`), la domanda *«e' del compito o del modello?»* tornera' senza risposta, e l'unico modo di risponderle e' rifare la misura interrotta. Il modello e' scaricato, il comando e' quello di §5.1 con `--profilo granite4.1:8b`, e la riga di comando e' identica: verificato che `reasoning_effort` su un modello senza modalita' di ragionamento e' inerte, risposta identica con e senza.


---

## 19. Le delibere del perimetro guidato (29 luglio 2026)

Proposte in `13-perimetro-guidato.md` su iniziativa dell'Architect. Deliberate una per volta, misurando.

### 19.1 D105 — La condizione nominata dev'essere fondata

**Il difetto, misurato.** Diagnosi su 80 aperture con `qwen3.5:9b`: dodici fallimenti su ventuno di `filter` erano lo stesso — un frammento che non nomina alcuna condizione trasformato in condizione nominata, perche' e' la piu' economica da scrivere: nessun valore, nessun `kind`, nessuna espressione.

```
'voglio vedere ordini lo scorso mese i primi 5'
  -> is_category(ordini_vendita.in_bozza)  provenance: "lo scorso mese"
```

La provenienza e' la confessione. §10.3 la definisce come *il frammento della frase che ha prodotto l'operazione*, quindi una condizione nominata il cui frammento non contiene alcuno dei suoi termini e' infondata **per la definizione stessa del contratto** — e accorgersene richiede di confrontare due elenchi, non di capire l'italiano.

**Tre scelte di costruzione, ognuna con la sua ragione.**

Il confronto e' con la **provenienza** e non con l'enunciato: un turno di raffinamento porta avanti le condizioni dei turni precedenti, i cui frammenti appartengono a frasi che nessuno sta piu' dicendo. Confrontarle con l'enunciato corrente rifiuterebbe l'intera conversazione al secondo turno.

Il riconoscitore e' **quello della Fase A**, iniettato come funzione perche' `nli_core` non dipende da nulla (`tools/arch/spec.py`). Il corpus perturba le proprie frasi con refusi, accenti mancanti, abbreviazioni e minuscole di proposito (D83), e gli utenti fanno lo stesso senza che nessuno glielo chieda: un confronto letterale rifiuterebbe risposte corrette, trasformando una protezione in un difetto. Due nozioni diverse di *stessa parola* sarebbero un guasto peggiore di quello che si corregge.

Sono giudicate **solo le condizioni nominate**. Un confronto porta un valore che l'utente ha detto: non esiste un vocabolario contro cui verificarlo, e inventarne uno rifiuterebbe filtri legittimi.

**Misura sul campo, 80 aperture:**

| | filtro sbagliato | filtro corretto |
|---|---|---|
| **il controllo scatta** | **11** | **0** |
| il controllo non scatta | 9 | 59 |

Undici risposte sbagliate diventate rifiuti, **zero risposte corrette rifiutate**. Fra i casi presi, `F00752` — *«voglio vedere prelievi»*, una frase senza alcun filtro a cui il modello ne attaccava uno.

**Il limite dello zero, dichiarato.** Il denominatore non e' 80: il controllo puo' sbagliare solo dove una condizione nominata c'e' e il filtro era corretto, che e' una frazione dei 59. Su un numero piccolo uno zero significa *raro*, non *impossibile*, e la misura va rifatta sulle 444.

**Il segno dell'effetto.** L'accuratezza **non sale**: quelle undici passano da sbagliate a rifiutate e restano fuori dalla colonna degli esatti. Era previsto in `12` §Parte 8a prima di misurare, ed e' il compromesso che **D2** chiede — un filtro inventato mostra *meno* record con sicurezza, e chi guarda non ha modo di accorgersene. Un rifiuto e' un errore che si vede.

**Cosa non copre.** I nove fallimenti residui sono di altre famiglie — una condizione dimenticata, un predicato possibile e sbagliato, un valore preso male — e nessun controllo di fondatezza li tocca.

### 19.2 D106 — Un rifiuto che propone

D105 trasforma un filtro inventato in un rifiuto, che e' gia' il compromesso chiesto da **D2**. Ma un *«non ho capito»* nudo lascia l'utente dov'era, senza sapere cosa scrivere di diverso. Le opzioni sono anche il punto in cui il perimetro di `13` **insegna**: si imparano tre modi di dire una cosa scegliendone uno.

**Derivate, mai chieste al modello.** §5.9 fissa il principio per la vista — *«chiedere al modello di scegliere la vista violerebbe C2/P4: e' una decisione derivabile»* — e qui vale identico. Stabilito che una condizione nominata non e' fondata, le letture plausibili sono derivabili: o la condizione non e' stata chiesta, o l'utente intendeva una delle condizioni nominate che quell'entita' possiede. **Un modello che ha appena inventato una condizione e' l'ultimo a cui chiedere le sue alternative.**

Quattro vincoli, ognuno con il suo argomento:

* **una domanda per volta.** Con due condizioni infondate la domanda porterebbe due assi insieme e un'opzione dovrebbe combinare una scelta su ciascuno; §4.4 ammette una lista da due a quattro, non una matrice;
* **la prima lettura e' sempre *senza la condizione***, ed e' l'unica sempre disponibile: se l'utente non ha detto nulla che nomini una condizione, non filtrare e' una lettura fedele;
* **non si propone una condizione che la frase gia' porta**: offrire all'utente un filtro sotto cui e' gia' non e' una scelta;
* **meno di due letture, nessuna domanda.** Un'opzione sola non e' una domanda, e un rifiuto che finge di offrire una scelta e' peggio di uno che ammette di non averla. In quel caso l'esito resta `not_understood`.

**La divisione del lavoro fra le zone.** Le operazioni di ogni lettura sono costruite nella zona pura, che non ha lingua; le parole della domanda e delle etichette nella catena, che ha quella dell'utente. Un modulo puro che producesse testo per l'utente sarebbe un modulo puro con dentro una lingua.

**Un limite che vale per entrambe le decisioni, e non e' piccolo.** In un'installazione viva le condizioni nominate nascono dai filtri salvati di Odoo ed entrano nella **coda L3**, che `store.py` ignora finche' qualcuno non le approva. Oggi quindi un'installazione reale **non ha alcuna condizione nominata attiva**: il modello non puo' emettere `is_category`, D105 non ha nulla da controllare e D106 nulla da proporre. Il corpus le ha (L1), quindi la misura esercita lo stato **futuro** del prodotto — quello in cui i filtri sono stati approvati. Le due decisioni sono corrette e necessarie; il loro effetto sul campo comincia con la prima approvazione.

### 19.3 Un difetto trovato eseguendo la suite, che non era del codice

Tre test Odoo sono falliti dopo D106, e nessuno per causa sua: `nli_test` contiene **50 004 partner**, di cui 49 943 seminati dal popolatore del banco di carico (D97). I tre test asserivano conteggi esatti su `res.partner` e usavano *«Milano»* come citta' di prova — la stessa che il popolatore distribuisce.

**Un test che passa solo su una banca dati vuota non e' un test**, ed e' esattamente la situazione che ogni cliente reale presenta il primo giorno. Corretto alla radice: le prove usano ora una citta' che nessun popolatore produce, e restano deterministiche su qualunque volume. Tutti gli 83 test Odoo passano su una base con cinquantamila record.

### 19.4 D108 — Il percorso di approvazione, e il buco che ha chiuso

**Il buco, trovato verificando D106.** In un'installazione viva il dizionario era **solo L0**: quello che l'introspezione legge dalla piattaforma. Le proposte di categoria di **D35** entravano nella coda **L3**, che `store.py` ignora e che `validate_entry` rifiuta a priori — e non esisteva alcun luogo in cui approvarle. Conseguenza misurabile: nessuna installazione reale aveva una sola condizione nominata, il modello non poteva emettere `is_category`, e **D105 e D106 non avevano nulla su cui agire**. Erano corrette e inerti.

**Tre pezzi mancanti, non uno.** Il registro delle voci approvate (`nli.dictionary.entry`); la traduzione dalla condizione tipizzata al **dominio** che la esegue (`dictionary/domains.py`); e il collegamento nel runtime, che le carica accanto a L0 e costruisce per ogni categoria il proprio `Binding` con il dominio dentro. Nessuno dei tre esisteva, e l'assenza del terzo spiega perche' l'unico `kind="category"` del progetto vivesse in un test puro.

**La direzione della traduzione e' la decisione.** `06` §7 vieta di tradurre automaticamente il **dominio di un filtro salvato in una condizione tipizzata**: significherebbe analizzare un'espressione Odoo arbitraria e sbagliarla di poco, producendo una categoria che vuol dire qualcosa di *vicino* a cio' che si intendeva — il guasto che una categoria esiste per togliere. Quel divieto resta intatto. La traduzione **inversa** — dalla condizione tipizzata al dominio — e' meccanica: una condizione validata ha una lettura sola e non c'e' nulla da indovinare. La persona scrive la condizione in approvazione, la macchina la esegue sempre allo stesso modo.

**Il tempo entra come argomento.** *«Scadute»* e' *scadenza prima di oggi*, e un dominio congelato all'approvazione sarebbe sbagliato il mattino dopo: `compare_now` si risolve a ogni costruzione contro l'istante passato, che e' la ragione per cui **V-D87-3** vieta all'Applicatore di espandere una categoria.

**Cio' che non si puo' scrivere.** Il vincolo esegue il validatore del dizionario **al momento della scrittura**: una voce che `Dictionary.build` scarterebbe viene rifiutata prima di esistere. Una definizione presente in una tabella e assente dal dizionario e' una divergenza che nessuno nota finche' un risultato non cambia. Un aggregato viene invece **memorizzato e lasciato senza binding**: e' materia del livello 5 (**V-D87-2**), e lasciarlo irrisolto fa sì che il livello 3 lo rifiuti per nome invece di farlo fallire tardi in esecuzione.

**Chi legge e chi scrive.** Lettura a ogni utente interno, scrittura al solo amministratore. La lettura non e' una cortesia: il percorso di interrogazione ha il divieto di elevare i privilegi (§6.3), quindi il runtime legge queste righe con i diritti di chi chiede. Cio' che protegge il catalogo non e' l'invisibilita' della riga — e' il filtro che tiene solo le voci la cui entita' quell'utente puo' leggere, e c'e' un test che lo mostra.

**13 test puri** sulla traduzione e **13 test Odoo** sull'approvazione, fra cui quello che conta piu' di tutti: un filtro salvato **non diventa una categoria da solo** (D28). 94 test Odoo verdi.

### 19.5 D104 — Il vocabolario visibile, e chi possiede quali parole

**Il difetto non e' del modello.** `13` §1.2: l'utente ha davanti una casella vuota e nessun indizio su cosa il sistema sappia fare, deve indovinare, e quando sbaglia il rifiuto non gli dice cosa scrivere di diverso. Nel frattempo il sistema **possiede gia'** l'elenco delle parole che riconosce, e lo mostra soltanto al modello.

**Suggerito, mai imposto.** L'opzione del perimetro obbligatorio e' stata cercata per prima e scartata con tre argomenti (`13` §3): il prodotto sparirebbe — sarebbe un modulo a tendine con una casella davanti, e Odoo le tendine le ha gia'; i numeri diventerebbero falsi, perche' l'accuratezza salirebbe togliendo i casi difficili; e le persone non parlano per sostantivi, scrivono *«chi mi deve dei soldi»*.

**Due generi di parola, e uno solo e' nostro.** I termini del cliente — *«scadute»*, il nome di una colonna — vengono dal catalogo e si mostrano **come li ha scritti il cliente**: tradurli sostituirebbe il vocabolario dell'azienda con quello del fornitore, che e' l'opposto di cio' per cui un dizionario si costruisce dall'installazione. Le formulazioni del prodotto — i periodi, la forma di un confronto — sono nostre, chiuse, uguali per ogni installazione, e passano dalla traduzione come ogni altra stringa.

Da qui la divisione: la **struttura** la deriva la zona pura di `catalogue/perimeter.py`, che e' una funzione dei suoi argomenti e non ha lingua; le **parole** le mette `nli_web`, che ha un utente. I periodi viaggiano con il proprio simbolo accanto alla parola, perche' una parola e' cio' che l'utente dice e un simbolo e' cio' che il contratto ammette.

**Tre esclusioni, ognuna con la sua ragione.** Un periodo che richiede un argomento — *«ultimi N giorni»* — non e' un suggerimento: offrirlo senza la N produce una frase che l'utente deve finire. Le date assolute sono dell'utente. Un confronto si offre solo su cio' su cui significa qualcosa: proporlo su un cliente o su uno stato insegnerebbe l'errore che **D103** ha reso inesprimibile.

**La garanzia che rende sicuro un suggerimento**: il perimetro nasce dallo **stesso catalogo che vede il modello**, costruito con i diritti di chi chiede. Le regole di esposizione e il budget di D31/D79 sono gia' stati applicati, quindi un utente che non puo' leggere gli importi non se li vede proporre, e nessun suggerimento puo' contenere qualcosa che il sistema non sa fare. Un perimetro assemblato altrove sarebbe una seconda via alla stessa informazione, senza le stesse guardie.

**Resta all'interfaccia** la parte visiva: dove compaiono i suggerimenti, come si scelgono, come si compongono con il testo gia' scritto. E' parte 7, e questa decisione le consegna i dati gia' filtrati.

7 test puri sulla struttura, 9 Odoo sulle parole e sulla derivazione. 101 test Odoo verdi.

---


## 20. Le delibere della ripresa (1 agosto 2026)

Il lavoro è stato spostato dal ramo `ai-agent` al ramo `new-ai-agent`, sopra la base
dell'interfaccia corrente. Nel trasporto il motore non è cambiato: i controlli dei
confini sono verdi (948 casi, 0 errori) e i test Odoo passano prima e dopo.

Le due voci che seguono non nascono da una richiesta. Sono venute fuori **verificando
che la ripresa funzionasse**: una è una decisione, l'altra è un difetto che una regola
del progetto avrebbe dovuto intercettare e che nessuno stava guardando.

### 20.1 D109 — La mappa dei tipi è un fatto, non una lettura

**Cosa non funzionava.** Il comando che misura quanto il modello capisce — quello di
`12` §5.1 (il documento del piano, paragrafo con i comandi di verifica) — non partiva
più:

    ImportError: cannot import name 'fields' from 'odoo'

Non era rotto il modello e non era rotto il corpus. Lo strumento aveva bisogno di una
tabellina, `CONTRACT_TYPE_BY_ODOO_TYPE`, che traduce i tipi di campo di Odoo nei tipi
del nostro contratto: `char` diventa `text`, `monetary` diventa `number`, e così per
dodici righe. Quella tabellina stava dentro `introspection/runtime.py`, un file che
importa l'ORM di Odoo.

Lo strumento di misura, però, gira **fuori da Odoo**, sul portatile, senza database. E
lì l'ORM non c'è di proposito: `tools/pure/bootstrap.py` è scritto apposta perché
`from odoo import fields` fallisca. Quel fallimento è la garanzia che tiene in piedi
tutte le zone pure — se passasse, non sapremmo più quali pezzi funzionano davvero
senza piattaforma.

**La domanda giusta.** Non era *«come faccio ad avere l'ORM anche sul portatile»*. Era
*«perché una tabella di dodici coppie è chiusa dietro l'ORM»*.

Il resto dell'introspezione interroga un sistema vivo: quali modelli esistono, quali
campi hanno, cosa può vedere questo utente, che ore sono. Senza Odoo non ha senso.
Questa tabella invece non interroga niente. `char` è `text` in ogni installazione, su
ogni database, a ogni ora. È un **fatto**, e un fatto non ha bisogno di una piattaforma
accesa per essere vero.

**La decisione.** La tabella si sposta in `nli_semantics/platform_types.py`, dichiarato
zona pura in `tools/arch/spec.py` con scritto il perché. Il vecchio file la importa e
continua a offrirla con lo stesso nome: sotto Odoo non cambia una riga per nessuno.
Quello che cambia è che ora il catalogo si può costruire fuori dalla piattaforma — ed è
il presupposto di qualsiasi misura fatta sul corpus.

**L'alternativa scartata, e perché.** Rendere l'ORM importabile sul portatile era la
strada che non toccava l'architettura, quindi è stata cercata per prima, come vuole il
metodo. Scartata con un argomento: avrebbe messo l'ORM sul percorso di uno strumento
puro solo per leggere una costante. Cioè avrebbe piegato **D24** (la decisione per cui
ogni zona dichiara cosa può importare, e un controllo automatico lo verifica) pur di
non spostare dodici righe.

Verifica: 54 file nelle zone pure, 0 violazioni. La misura riparte e produce un numero
— 65,0% su 40 aperture, contro il 64,0% misurato a luglio su 444: stessa fotografia,
dentro l'incertezza del campione.

### 20.2 Un vincolo che non è mai esistito in nessun database

Il profilo del modello dichiara `CHECK (context_window > 0)`: la finestra di contesto
non può essere zero o negativa. Serve a difendere **D78** (il profilo deve dichiarare
quanto testo il modello regge), che a sua volta è il numero da cui **D79** (il budget
del catalogo si ricava dalla finestra dichiarata) fa una divisione. Con una finestra a
zero, il catalogo calcolerebbe un budget partendo dal nulla.

La riga era scritta così:

    ("context_window_positive", "CHECK (context_window > 0),", ...)

Con la **virgola dentro la stringa SQL**. Ecco cosa succedeva, in ordine: Odoo manda a
PostgreSQL il comando che crea il vincolo; PostgreSQL lo rifiuta perché quella virgola
finale non è sintassi valida; Odoo scrive un `ERROR` nel giornale e tira dritto; il
modulo si installa lo stesso e i test passano lo stesso.

Risultato: **il vincolo non esisteva in nessun database.** Verificato guardando
direttamente la tabella di sistema `pg_constraint` su `nli_test`: non ce n'era traccia.

Nessuna suite se n'era accorta perché non c'era un test che lo mostrasse rifiutare
qualcosa. Ed è esattamente la regola che il progetto si è dato: *nessun controllo può
passare a vuoto, e ogni controllo ha un test che lo mostra scattare e uno che lo mostra
non scattare*. La regola era scritta, e disattesa proprio dove serviva.

Corretta la virgola, aggiunti i due test, il vincolo ora esiste e rifiuta davvero. Il
test riconosce l'errore **dal nome del vincolo**, non da un messaggio generico: così, se
un domani il vincolo sparisse di nuovo, un rifiuto qualsiasi non potrebbe passare per
quello giusto. 116 test Odoo verdi, erano 114.

---


## 21. Le delibere dell'ancoraggio del tempo (2 agosto 2026)

Proposte in `14-ancoraggio-del-tempo.md`. Nascono da una diagnosi su 80 aperture del
corpus fondativo con `qwen3.5:9b`, il modello che **D107** (la decisione che fissa il
modello di riferimento) ha scelto.

**Il difetto, e perché era uno solo.** Su 80 aperture, 21 fallivano. Il modello non
sbagliava a scrivere: 80 buste valide su 80, zero errori di forma, zero rifiuti
dell'applicatore. Sbagliava **cosa** diceva. Dodici fallimenti erano sul tempo, nove
erano categorie inventate. Sembrano due famiglie. Sono la stessa.

Nel DSL una condizione si aggancia alla frase in due modi soltanto. O la frase **nomina
il campo** — *«con importo oltre 500»* — oppure la condizione è nominata, e allora la
frase nomina solo la categoria. Un'espressione di tempo **non nomina mai il campo**.
Nessuno dice *«ordini con data ordine nel mese scorso»*: si dice *«ordini del mese
scorso»*. Non è un difetto del corpus, è come si parla. E nel catalogo che mandiamo al
modello non esisteva il concetto di *«la data»* dell'entità.

Il modello si trovava quindi un frammento da collocare e nessun posto dove metterlo.
Faceva una di due cose: lo lasciava cadere, oppure lo appoggiava sull'unica condizione
che non chiede un appiglio, cioè una categoria. **`is_category` era la discarica.** Ci
finiva *«lo scorso mese»*, ci finiva *«prelievi»* — che è il nome dell'entità stessa —
trasformato in *«in bozza»*.

Le tre decisioni chiudono le tre uscite. Al tempo si dà un appiglio (**D110**),
lasciarlo cadere diventa vietato (**D111**), e alla categoria si toglie la discarica
(**D112**).

### 21.1 D110 — L'ancora del tempo è un fatto di struttura

**La regola.** Il catalogo conta le date che espone. Una sola → è quella, e un periodo
senza campo si attacca lì. Due o più → nessuna è principale, e la risposta giusta è una
domanda. Zero → su questa entità il tempo non è esprimibile, e va detto.

**Perché si contano e non si scelgono.** L'alternativa era un'euristica: prendere la
data dell'ordinamento predefinito, o quella obbligatoria, o quella che sta nelle viste.
È stata cercata per prima e scartata con un argomento solo. Sceglierne una fra due
plausibili **è indovinare**, che è esattamente ciò che stiamo togliendo. §19.1 lo
argomenta deliberando **D105** (la decisione per cui una condizione nominata non fondata
nel proprio frammento è rifiutata al livello 3): un filtro inventato mostra *meno*
record con sicurezza, e chi guarda non ha modo di accorgersene. È il compromesso che
**D2** (il cancello che vieta qualunque scrittura sui dati finché la Fase 2 non è
misurata e superata) rende obbligatorio: un sistema che dovrà scrivere non può
permettersi errori invisibili.

Se un domani si vorrà dichiarare che per le fatture la data principale è la scadenza,
quella è una voce di dizionario che qualcuno approva. La strada esiste già: è **D108**
(la decisione che dà un registro alle voci di dizionario approvate e traduce la
condizione tipizzata in dominio). Non si costruisce adesso, e non si indovina nel
frattempo.

**Dove nasce l'ancora, e perché lì.** Si calcola dagli attributi **sopravvissuti al
filtro dei permessi e al budget**, mai da quelli in ingresso. Un'ancora che nominasse
una data che l'utente non può leggere sarebbe una seconda via alla stessa informazione,
senza le stesse guardie — e le guardie sono quelle di **D31** (le regole di esposizione,
con il budget fissato a 60 attributi per entità) e di **D79** (il budget del catalogo
derivato dalla finestra di contesto dichiarata). Vale la stessa garanzia di **D104** (il
vocabolario del catalogo è mostrato all'utente, suggerito e mai imposto): il
suggerimento nasce dallo stesso catalogo che vede il modello, costruito con i diritti di
chi chiede. C'è un test che toglie un attributo dai riferimenti leggibili e verifica che
sparisca dall'ancora: se qualcuno spostasse il calcolo prima del filtro, quel test
fallirebbe.

**Essere strutturale è ciò che la rende verificabile.** L'ancora è una funzione della
lista di attributi. Non serve un database, non serve il modello, e i suoi test sono test
puri. È lo stesso schema di **D109** (la mappa dei tipi di campo di Odoo vive in una zona
pura, fuori dall'introspezione): un fatto non ha bisogno di una piattaforma accesa per
essere vero. Le zone pure passano da 54 a **55 file**, 0 violazioni.

**Il terzo caso resta aperto.** L'ancora nulla — nessuna data esposta — è il più
silenzioso dei tre. Oggi *«clienti del mese scorso»* perde il tempo e nessuno se ne
accorge, perché sui clienti non c'è una data da esporre. Con D110 l'ancora nulla
**dichiara** che l'entità non espone alcuna data: quel fatto ora si vede. Cosa
l'interfaccia debba fare con quel fatto **non è ancora deciso**. Il prompt (§21.2) dice
di rispondere con un chiarimento, ma un chiarimento richiede 2-4 opzioni e ogni opzione
porta almeno un'operazione (`nli_core/contract/schema.py`): senza una data non c'è
operazione da offrire, quindi non c'è un chiarimento da costruire. Il caso resta senza
una risposta definita — voce aperta in `ai/restart.md`.

### 21.2 D111 — Un periodo non si lascia cadere

D110 dà l'appiglio. Da solo non basta, perché lascia aperta l'altra uscita.

**Oggi lasciar cadere un pezzo di frase non costa niente al modello.** Nessuna regola
glielo vieta, e una busta senza quella condizione è comunque valida: passa i livelli,
passa la coerenza, l'applicatore la accetta. Cinque dei dodici fallimenti temporali
erano esattamente questo — il periodo spariva e la risposta sembrava a posto.

La regola nel prompt dice due cose, e la seconda è quella che conta. La prima: dove va
un periodo che non nomina un campo. La seconda: **un periodo non si può lasciare
fuori**. Se non si colloca, si chiede. Una frase che nomina un periodo e una risposta
che non lo nomina è una risposta **sbagliata**, non una risposta più corta.

**Perché una regola nel prompt qui, quando il progetto diffida delle regole nel
prompt.** La leva del prompt è la più debole che abbiamo, e le prove ci sono: le regole
scritte vengono violate. Ma D110 e D111 sono di natura diversa dalle altre. Non dicono
*come si dice una cosa in italiano* — dicono **dove va**, e il dove è dichiarato dal
catalogo, che è dato e non opinione. Il vincolo forte, quello che il modello non può
violare, arriva con D112 e agisce sullo schema, non sulla prosa.

### 21.3 D112 — La categoria che la frase non nomina è inesprimibile

**Il difetto.** Una condizione nominata è la sola il cui riferimento la frase non deve
scrivere: nessun campo, nessun valore, nessun tipo. È la più economica da produrre, e
per questo raccoglieva tutto. Il caso più istruttivo dei nove: *«commesse con importo
oltre 500 raggruppati per stato»* diventava una categoria *«da consegnare»* — il modello
prendeva tutto il resto della frase come giustificazione, e nel farlo **perdeva il
`> 500`**, che era l'unica condizione vera.

**La leva era già in mano.** Lo schema che vincola la generazione si costruisce già per
catalogo: è **D101** (i riferimenti sono un insieme chiuso nello schema del turno) e
**D103** (il predicato è vincolato dal tipo dell'attributo già nello schema del turno).
La cosa che mancava non era un meccanismo: era accorgersi che **la frase la conosciamo
prima di costruire lo schema**. Fra le categorie del catalogo si ammettono solo quelle i
cui termini compaiono nella frase.

Il risultato per *«voglio vedere prelievi»*: il modello **non ha più in bocca**
`in_bozza`. Non è una regola che può violare. È un simbolo che, per quella frase, non
esiste nel suo alfabeto.

**Sparisce il ramo, non resta vuoto.** Con l'insieme delle categorie vuoto, il ramo
`is_category` **non viene proprio aggiunto** allo schema. Un ramo con una lista di
riferimenti vuota sarebbe una forma che il modello vede e non può riempire; assente, la
condizione nominata semplicemente non è una delle forme che quel turno ammette. È il
predicato di **D87** (`is_category` per la condizione nominata T5) che si toglie dal
tavolo insieme al proprio riferimento.

**Solo le categorie.** Un attributo si nomina da sé nella frase, e restringerlo
toglierebbe colonne e raggruppamenti, che la frase nomina altrove. Il restringimento si
ferma dove l'appiglio lessicale c'è già.

**Il riconoscitore si passa, non si importa.** È lo stesso di D105 — quello che sa di
accenti mancanti, abbreviazioni e refusi — e arriva come argomento perché `nli_engine`
non può dipendere da `nli_semantics` (`04` §6.3, il confine fra il motore e la
semantica). Come per D105, **se non viene passato il restringimento non si applica**:
così i test puri del motore continuano a girare senza dizionario.

**Quando il riconoscitore sbaglia**, cioè l'utente ha scritto la categoria in un modo
che non riconosce, il fallimento degrada a **una domanda** e non a un filtro sbagliato.
È la direzione di §19.1, di nuovo: un errore che si vede è preferibile a uno che non si
vede. E **D106** (il rifiuto di D105 propone: `clarification` con letture derivate dal
catalogo) è già il posto in cui quella domanda prende forma.

**D105 resta dov'è.** Non è ridondanza. D112 impedisce, D105 verifica, e verifica ciò
che arriva da altre strade: una query salvata, un'interpretazione modificata a mano, un
secondo esecutore. Il riconoscitore si costruisce **una volta sola** nella conduttura e
serve a entrambe: costruirne due significherebbe due indici dei termini nel percorso di
una singola richiesta, per la stessa risposta.

**Dove il restringimento non è stato collegato, di proposito.** La conduttura chiama
l'interprete due volte. La seconda chiamata — quella di Fase B, che serve solo a capire
di quale entità si parla — **non** riceve il riconoscitore. Il catalogo di Fase B porta
solo i nomi delle entità e ha l'insieme delle categorie sempre vuoto: lì il
restringimento sarebbe codice che non fa niente. Verificato sul codice, non assunto.

Il collegamento nella conduttura vale **1 test Odoo**, e serve: il restringimento vive
nella costruzione dello schema, quindi non compare nella risposta. Senza quel test
sarebbe codice mai eseguito e nessuno se ne accorgerebbe. Test Odoo da 116 a **117**.

### 21.4 Il metro chiedeva cose che la frase non diceva

Questa parte non è una decisione. È un difetto **della misura**, trovato mentre si
costruivano le tre. Il metodo del progetto chiede di controllarlo sempre per primo:
prima di attribuire un esito al modello, verificare che non sia stato il metro a
dettarlo. Non è una precauzione teorica — tre delle sette delibere di §18 (la
qualificazione del profilo) correggono il metro e non il modello.

Il generatore del corpus, per un'entità con più date, ne pescava **una a caso** e nella
frase scriveva solo *«lo scorso mese»*. Sulle fatture cliente le date esposte sono due —
data fattura e scadenza. Casi reali: *«sta settimana»* → data fattura, *«lo scorso
mese»* → scadenza, *«quest'anno»* → scadenza, *«nel 2025»* → data fattura. Stessa
entità, stessa forma di frase, attese diverse.

Su quei casi **nessuno poteva fare meglio del 50%**, né un modello né una persona: la
frase non contiene l'informazione che l'attesa pretendeva. Era un tetto strutturale, e
una parte dei dodici fallimenti temporali era colpa del metro.

Correzione: quando l'entità espone più di una data e la frase non nomina il campo, il
caso **si aspetta un chiarimento**. Il generatore sapeva già produrre casi di
chiarimento con temporale ambiguo; erano le aperture normali a pescare comunque a caso.

**La regola sta in un posto solo.** Quante date espone un'entità lo decide `time_anchor`
— la stessa funzione del prodotto, importata, non copiata — e la lista delle date per
entità vive in un unico file, letto sia dal generatore sia dal verificatore. Una misura
che contasse le date con una regola diversa da quella del prodotto misurerebbe un altro
prodotto. È lo stesso argomento di D109.

**Cosa è cambiato nel corpus.** I casi totali restano **1200**. Le aperture che
attendono un'operazione passano da 444 a **414**: le 30 spostate sono tutte su
`account.move.out_invoice`, l'unica entità del corpus che espone due date. I loro
**testi non sono cambiati** — è cambiata l'attesa. I casi verificati contro il contratto
passano quindi da 948 a **918** (414 aperture + 504 raffinamenti), 0 errori, copertura
100%.

Un numero che scende e non è un peggioramento va detto per quello che è: si sono tolte
30 domande a cui non esisteva una risposta giusta.

**E il livello 3 ora gira dentro lo strumento di misura.** `interpret()` esegue i livelli
1-2 e la coerenza, mai il livello 3 — che è dove vive il controllo di fondatezza di D105.
Lo strumento di misura non aveva quindi **mai** eseguito quel controllo. È il motivo per
cui si diceva che D105 «rende i fallimenti visibili senza spostare il punteggio»: il
punteggio non li aveva mai visti. Ora il numero riflette D105.

**Il contatore non deve restare a zero con D112, e non è un segno di disaccordo se non
lo è.** D112 (§21.3) restringe guardando **tutta la frase** — è `mentions(riferimento,
frase)` in `nli_engine/prompt.py`. D105 verifica guardando **solo il frammento** della
condizione, la sua provenienza — è `mentions(riferimento, frammento)` in
`nli_core/validation/contextual.py`. Stesso riconoscitore, testo diverso. Un modello può
nominare una categoria che la frase contiene davvero, ma giustificarla con il frammento
sbagliato: passa D112, che ha visto tutta la frase, e fallisce D105, che vede solo quel
frammento. Il numero diverso da zero dice questo — il livello 3 vede ora ciò che prima
non vedeva mai — non che i due riconoscitori si contraddicono.

### 21.5 Cosa questo lavoro non fa

**Non alza l'accuratezza, e può abbassarla.** Le risposte sbagliate diventano domande.
È il verso giusto — un errore visibile al posto di uno invisibile — ma il corpus conta
una domanda come un fallimento di `operations`. Il numero da guardare è un altro: quanti
filtri sbagliati escono con l'aria di essere giusti. I suoi indicatori sono le condizioni
infondate contate dal metro e i chiarimenti prodotti, e vanno letti con la copertura
accanto, come chiede `07` §5.4 (il piano di valutazione, il paragrafo su come si leggono
i due numeri insieme).

**La rimisura non è stata fatta.** È il passo 5 dell'ordine di costruzione di `14` §8, e
va dopo, non a metà: misurare a metà strada produce un numero che non descrive né il
prima né il dopo. Finché non è fatta, di questo lavoro sappiamo che è costruito e
verificato, non quanto è servito.

**Non risolve `filter` da solo.** Delle famiglie diagnosticate sulle 80 aperture restano
quelle che non c'entrano con il tempo né con le categorie inventate: il predicato
possibile ma sbagliato, il valore preso male, le due condizioni fuse in una.

**Non tocca `within`/`between`.** Su una data il contratto ammette entrambi i predicati,
il corpus si aspetta sempre `within`, e un modello che scrive `between` produce una cosa
**legale** contata come sbagliata. Deliberato di lasciarlo com'è: nel campione pesa due
casi, che sbagliavano anche altro. Resta scritto qui perché chi rivedrà quei due casi non
ci perda tempo.

**Non lima il prompt contro il corpus sintetico.** Le due regole del prompt sono
strutturali: dicono dove va una cosa, non come si dice in italiano. Ogni punto strappato
al generatore rischia di essere prompt adattato al generatore. È la degradazione che
**D42** (le tre popolazioni di corpus, con il corpus sigillato protetto da
autorizzazione) esiste per impedire, e sul corpus fondativo il sigillo **non c'è**: lo
dichiara **D86** (il corpus fondativo non soddisfa D42 e non chiude D49, perché chi
scrive un generatore ne conosce la distribuzione).

### 21.6 Le verifiche

| | prima | dopo |
|---|---|---|
| test in zona pura | 395 | **412** |
| test Odoo | 116 | **117** |
| file nelle zone pure | 54 | **55**, 0 violazioni |
| casi verificati contro il contratto | 948 | **918**, 0 errori |
| aperture che attendono un chiarimento | 0 | **30**, tutte su `account.move.out_invoice` |
| casi totali nel corpus | 1200 | **1200** |

I punti costruiti sono verificabili **senza interrogare il modello nemmeno una volta**:
sono test puri e test Odoo. La misura serve alla fine, a dire quanto è servito.

### 21.7 La rimisura, e cosa dice davvero

Eseguita il 2 agosto 2026 su tutte le **414 aperture** che attendono un'operazione, con
`qwen3.5:9b`, generazione vincolata, ragionamento spento, finestra 4096.

| | luglio, 444 casi | ora, 414 casi |
|---|---|---|
| complessiva | 64,0% | **70,0%** (290/414) |
| `filter` | 73,6% | **79,5%** |
| `fields` | 88,1% | 85,3% |
| `target` | 98,4% | 95,7% |
| riparazioni (**D15**, la decisione che concede un solo tentativo di correzione) | 2,9% | **6,3%** |
| condizioni infondate (**D105**) | mai misurate | **0** |

**Il confronto fra quelle due colonne non vale, e va detto prima di leggerle.** La
popolazione è cambiata: le 30 aperture uscite sono quelle in cui l'attesa era testa o
croce, e non erano un campione qualunque. Nel campione di 80 usato per la diagnosi
**prima** delle modifiche ce n'erano 8, ed **erano fallimenti tutte e 8**. Otto su otto.

Se le 30 uscite erano fallimenti — e la prova dice di sì — la riga di luglio ricalcolata
**sugli stessi 414 casi** vale circa **68,6%** complessiva e **79,0%** su `filter`.

Il confronto onesto è quindi questo:

    complessiva   68,6%  ->  70,0%     (+1,4 punti)
    filter        79,0%  ->  79,5%     (+0,5 punti)

**Su `filter`, che era il bersaglio, il movimento è mezzo punto. Cioè niente.**

Era stato previsto in §21.5 che l'accuratezza potesse non salire. Non era stato previsto
che il guadagno apparente venisse quasi tutto dal cambio di popolazione: la stima fatta
prima di misurare parlava di *«circa 3 punti di contabilità»*, e i punti erano **4,6**.
La stima era bassa perché nessuno aveva contato quanti dei casi rimossi fossero già
fallimenti. Adesso è contato.

**Le tre famiglie del tempo, e sono uguali.** Dei 414 casi, 33 contengono
un'espressione di tempo, e falliscono **tutti e 33** (sui casi senza tempo si fallisce
nel 23,9%). Guardati uno per uno, si dividono in tre gruppi da undici:

| famiglia | casi | |
|---|---|---|
| **solo il predicato** | 11 | campo giusto, periodo giusto, `between` invece di `within` |
| **rifiuto** | 11 | 9 `out_of_scope`, 2 `clarification`: il modello si ferma |
| **altro** | 11 | fallimenti veri, su `filter` e su `fields` |

**D110 funziona.** Nella prima famiglia il modello attacca il periodo alla data
dichiarata dall'ancora — che è precisamente ciò che prima non sapeva fare. Esempio:
*«ordini di vendita con totale almeno 100 quest'anno»* produce `data_ordine` con
`current_year`, e l'unica differenza dall'atteso è `between` al posto di `within`.

**E qui una valutazione precedente si rivela sbagliata.** §1.3 della proposta `14`
aveva classificato la coppia `within`/`between` come minore — *«due casi, che
sbagliavano anche altro»* — e su quella base era stato deciso di lasciarla stare. La
valutazione era corretta con i dati di allora e non lo è più: il predicato non poteva
emergere come causa isolata **finché il modello sbagliava il campo**. Era misurato
dietro un difetto più grande. Oggi vale **11 casi su 414, cioè 2,7 punti**, e risolverlo
porterebbe la complessiva a ~72,7% e `filter` a ~82,1% — ancora sotto la soglia di
**D44** (la decisione per cui l'accuratezza si misura per sezione, con soglia 85% su
ciascuna), ma è la leva più corta disponibile.

**D112 funziona, e si vede da due numeri.** Zero condizioni infondate su 414: la
categoria che la frase non nomina non è più scrivibile, quindi il livello 3 non ha nulla
da rifiutare. Il costo sta nelle riparazioni, più che raddoppiate: il modello prova a
dire cose che lo schema non ammette più.

**La seconda famiglia non era prevista.** Undici rifiuti, quasi tutti su `sale.order`,
dove l'ancora è **una sola data e non c'è ambiguità**: il modello ha l'informazione per
rispondere e si ferma lo stesso. Non sappiamo perché, ed è la prossima cosa da
diagnosticare — non un'altra decisione da prendere.

**Il bilancio, in una riga.** Il lavoro fa quello che aveva promesso — l'ancora regge,
le categorie inventate sono sparite, gli errori invisibili sono diventati visibili — e
sul numero non ha spostato quasi nulla. Le due cose stanno insieme, e sono entrambe
vere.

**Diagnosi della seconda famiglia, fatta subito dopo.** Gli undici rifiuti escono quasi
tutti con la stessa etichetta: `scope_note: "previsione"`. Il modello classifica una
richiesta che contiene un periodo come una **previsione**, e la previsione è fra le cose
che il prompt dichiara fuori portata:

    out_of_scope [...] Answer it only when the request needs something these
    operations cannot do — a forecast, a write, a computation over time.

*«ordini lo scorso mese»* non è una previsione: è un filtro su una data passata. Ma
l'elenco delle cose fuori portata nomina *«una previsione»* e *«un calcolo nel tempo»*,
e un'espressione temporale ci finisce dentro per somiglianza.

Due osservazioni che aiutano chi ci lavorerà:

* Quasi tutti quei casi hanno **una riparazione** (D15): il primo tentativo non passa la
  validazione, e la seconda risposta è la fuga in `out_of_scope`. È anche la spiegazione
  delle riparazioni raddoppiate.
* I due `clarification` non sono errori grossolani: il modello chiede *«per "nel 2025"
  intendi la data ordine in quell'anno, o gli ordini aperti a fine 2024 da evadere nel
  2025?»*. È una domanda sensata su una frase che il corpus considera chiara.

Il sospetto è che **D111 abbia alzato l'attenzione sul periodo senza dire cosa non è**:
al modello è stato vietato di lasciarlo cadere, gli è stato detto dove attaccarlo, e non
gli è stato detto che un periodo passato non è una previsione. Con la via d'uscita
aperta e più saliente di prima, la prende.

Non si delibera niente su questa base: è una diagnosi, e il rimedio — restringere cosa
conta come previsione — è una modifica al prompt, che va fatta sapendo che limare il
prompt contro un corpus sintetico è la degradazione contro cui **D42** (la decisione
delle tre popolazioni di corpus, con quello sigillato protetto da un'autorizzazione)
mette in guardia. Qui però non si tratta di guadagnare punti aggiustando parole: si
tratta di una regola dimostrabilmente letta male, con il meccanismo identificato.

**Insieme, le prime due famiglie valgono 22 casi su 414, cioè 5,3 punti**, e nessuna
delle due è un difetto del modello.

---

## 22. Le delibere della rimisura (2 agosto 2026)

Le due decisioni che seguono non nascono da una proposta, ma dalla misura di §21.7.
Sono lo stesso genere di cosa: **due terzi dei fallimenti sul tempo non erano difetti
del modello**, ed è stato possibile vederlo solo dopo che l'ancora di D110 aveva tolto
di mezzo il difetto più grande.

C'è una lezione di metodo, e vale più delle due decisioni: **un difetto misurato dietro
un difetto più grande è misurato male**. Entrambe queste cause erano già presenti a
luglio, e nessuna delle due era visibile finché il modello sbagliava il campo a cui
attaccare il periodo.

### 22.1 D113 — Un solo modo di dire un intervallo di tempo

Il contratto ammetteva `within` e `between`, **entrambi con un valore temporale**, su
una data. Dicono la stessa cosa. Il corpus si aspetta sempre `within`, quindi un modello
che scriveva `between` produceva qualcosa di **legale** e veniva contato sbagliato.

**Perché non se n'era fatto niente prima.** La proposta `14` §1.3 aveva guardato questa
coppia e l'aveva classificata come minore: *«nel campione pesa due casi, che sbagliavano
anche altro»*. La valutazione era **corretta con i dati di allora**. Il punto è che quei
dati erano stati raccolti mentre il modello sbagliava il campo del periodo: il predicato
non poteva emergere come causa isolata, perché arrivava sempre insieme a un errore più
grosso. Era misurato dietro un altro difetto.

Con l'ancora di **D110** (il catalogo dichiara dove si attacca un'espressione temporale
che non nomina un campo) il campo è giusto, e il predicato è rimasto solo. Misurato:
**11 casi su 414**, che sono **2,7 punti** di accuratezza persi su una differenza che
non è un errore.

**La decisione.** Su un attributo di tipo data o data-e-ora, i predicati ammessi
diventano `on`, `before`, `after`, `within`. `between` esce.

Esce in **due posti**, e la distinzione conta:

* dai predicati ammessi per il tipo, così la generazione vincolata non lo offre affatto
  (**D103**, la decisione per cui il predicato è vincolato dal tipo dell'attributo già
  nello schema del turno). Il periodo scritto con la parola sbagliata diventa
  **inesprimibile**, non rifiutato un livello dopo: è la stessa scelta di **D112** (le
  categorie ammesse sono quelle che la frase nomina);
* dai tipi di valore che `between` accetta, che restano il solo `range`. Questa è la
  rete per le condizioni che arrivano da altre strade — una query salvata, un'
  interpretazione modificata a mano — dove lo schema della generazione non passa. Uno
  impedisce, l'altro verifica.

**`between` non sparisce**: resta l'intervallo numerico, e lì non è il doppione di
niente. `equivalence.py` fonde in quella forma un `>= X` e un `<= Y` sullo stesso
riferimento, che è una regola di forma canonica e continua a valere.

Un test asseriva la ridondanza — *«between accetta sia un intervallo sia un periodo»* —
ed è stato riscritto con la decisione. Un test che fissa un contratto cambia quando il
contratto cambia; aggirarlo sarebbe stato il modo di non accorgersi di niente.

### 22.2 D114 — Un periodo non è una previsione

Nove dei rifiuti misurati in §21.7 uscivano con la stessa etichetta:
`scope_note: "previsione"`. Fra questi *«ordini lo scorso mese»*, *«ordini di vendita
quest'anno raggruppati per anagrafica»*, *«commesse il mese scorso in bozza»*. Nessuna
di quelle frasi chiede una previsione: chiedono un filtro su una data passata.

**Il meccanismo.** Il prompt elencava le cose fuori portata così: *«una previsione, una
scrittura, un calcolo nel tempo»*. Un'espressione temporale ci finisce dentro per
somiglianza — e con **D111** (un periodo non si lascia cadere: se non si colloca, si
chiede) il periodo è diventato più saliente di prima, senza che gli fosse detto **cosa
un periodo non è**. Gli è stato vietato di ignorarlo, gli è stato detto dove attaccarlo,
e la via d'uscita è rimasta aperta e più visibile.

**La decisione.** La regola dice adesso cosa esclude *e* cosa non esclude: la previsione
riguarda ciò che accadrà, il calcolo nel tempo è un andamento o un tasso di crescita, e
**un periodo che seleziona record già esistenti non è nessuna delle due cose**.

La forma non è nuova: la stessa regola conteneva già *«una parola che non riconosci non
è fuori portata»*, con la ragione accanto. Qui si aggiunge il caso gemello.

**Perché questa non è limatura del prompt.** `ai/restart.md` avverte di non limare il
prompt contro il corpus sintetico, e l'avvertimento è giusto: ogni punto strappato
aggiustando parole rischia di essere prompt adattato al generatore, che è la
degradazione contro cui **D42** (le tre popolazioni di corpus, con quello sigillato
protetto da un'autorizzazione) mette in guardia. La differenza qui è che non si cercava
un punteggio: si è osservato un esito, se n'è letta l'etichetta, e l'etichetta diceva
che il modello classificava un filtro come una previsione. È una regola dimostrabilmente
letta male, con il meccanismo identificato e scritto. Se la misura successiva non
muoverà quei nove casi, l'ipotesi era sbagliata e va detto.

### 22.3 Cosa ci si aspetta, scritto prima di misurare

Le due decisioni valgono insieme **22 casi su 414**, cioè **5,3 punti**. Se entrambe
funzionano, l'accuratezza complessiva passa da 70,0% a circa **75,3%** e `filter` da
79,5% a circa **84,8%** — che resta **sotto** la soglia dell'85% di **D44** (l'accuratezza
si misura per sezione, con soglia su ciascuna).

Questa previsione è scritta qui **prima** della misura, e serve a poter essere
smentita. Le due decisioni agiscono su cause diverse: se il numero si muove di 2,7 e non
di 5,3, dirà quale delle due ipotesi era giusta.

Resta fuori la terza famiglia — gli undici fallimenti veri, su `filter` e su `fields` —
che nessuna di queste due decisioni tocca.

**Verifiche:** 417 test in zona pura (erano 412), 117 test Odoo, confini 131 file e 55
in zone pure con 0 violazioni, contratto e corpus 918/918 con 0 errori e copertura al
100%. Gli schemi JSON derivati risultano già allineati: la tabella dei predicati per
tipo non vi compare.

---

## 23. D115 — La cronologia conserva le parole dell'utente

Deliberata **dall'Architect** il 2 agosto 2026, davanti alla specifica dell'interfaccia
(`15-implementazione-ui.md`), che chiede una chat con uno storico in stile ChatGPT.

### Il conflitto, posto prima della scelta

`nli.turn` conservava il **contesto** e lo **stato prodotto**, mai la frase. La frase
viveva cifrata nella coda e veniva **cancellata** al primo stato finale: **D96**
(l'enunciato in coda è transitorio e cifrato) sopra **D54** (pseudonimizzazione degli
enunciati all'ingresso, con mappatura separata).

Quindi *«riaprendo una sessione l'utente ritrova la cronologia come l'aveva lasciata»*
era **impossibile**. Si poteva ricostruire cosa il sistema aveva capito, non cosa
l'utente aveva detto.

Sono state poste tre strade, con il costo di ciascuna:

1. conservare l'enunciato **cifrato a riposo**, decifrato solo per chi l'ha scritto, con
   scadenza — conserva *«un dump non contiene frasi»*, costa una delibera su D54;
2. mostrare **l'interpretazione** invece della frase — nessun cambio di contratto, ma
   l'utente non rilegge le proprie parole;
3. conservarlo **in chiaro**, come farebbe ChatGPT — la più fedele alla specifica, e
   rinuncia esplicitamente alla proprietà di D54.

### La decisione, e cosa costa

**Scelta la terza.** L'enunciato è un campo di testo sul turno.

Cio' a cui si rinuncia si scrive per intero, perche' una decisione il cui prezzo non è
scritto è una decisione che qualcuno ripeterà senza saperlo: **un dump di questo
database contiene le frasi che le persone hanno digitato.** A proteggerle resta la
regola di record di `nli.turn` — un utente vede i propri turni e non quelli dei
colleghi — e **non più la cifratura**. Chi ha accesso al database ha accesso alle
domande.

Restano invece veri, e non sono stati toccati:

* la **coda** continua a sigillare l'enunciato e a cancellarlo (**D96**): quella copia
  serve ad attraversare il processo cron, non a essere riletta;
* **D60** (enunciati e cataloghi non finiscono nei registri diagnostici) vale ancora, ed
  è un'altra cosa dal database;
* la cancellazione è nelle mani dell'utente: eliminare una conversazione elimina i suoi
  turni, e con essi le frasi. È l'unico modo che ha di ritirare le proprie parole,
  quindi non è un dettaglio dell'interfaccia.

**Cosa resta aperto e non è stato deliberato qui:** la **conservazione**. Non c'è una
scadenza, non c'è cancellazione automatica, e `08-sicurezza-conformita.md` andrà
riletto con questa decisione in mano — perché il documento della conformità descrive un
sistema che non conservava le frasi, e ora le conserva.

### Cosa è stato costruito sopra

`nli.turn` acquista `utterance` (in chiaro), `outcome` e `interpretation_json`. Gli
ultimi due non c'entrano con la privacy e c'entrano con la reattività: la risposta già
impaginata dal Presentatore si **conserva** invece di essere riderivata. Riderivarla
vorrebbe dire ricostruire catalogo, diritti e istante di quel momento, e riaprire una
conversazione costerebbe quanto eseguirla — che è esattamente ciò che la specifica
vieta quando chiede che non ci sia mai attrito nella chat.

---

## 24. D116 — Il modello si sceglie dal pannello

**D75** (i profili di modello sono gestiti dall'amministrazione, con il protocollo preso
da un insieme chiuso e uno solo attivo) aveva gia' messo la scelta del modello nelle
mani di chi amministra. Mancava il pannello: fino a oggi un profilo si poteva scrivere
solo da codice, il che rendeva D75 vera sulla carta e falsa in mano a un
amministratore.

**Cosa costa.** La vista delle impostazioni generali vive in `base_setup`, e non c'e'
un altro aggancio: una sezione che compaia accanto alle altre deve estendere quella
vista. Quindi `nli_web` acquista una dipendenza di piattaforma, e **D18** (allargare la
superficie della piattaforma e' una decisione, non un import) vuole che la si scriva.
E' dichiarata in `tools/arch/spec.py`, dove il controllo dei confini la vede — ed e' il
controllo che me l'ha fermata prima che passasse in silenzio.

**Dove sta, e perche' non nel motore.** `nli_engine` possiede il profilo, ma la sua
responsabilita' dichiarata e' *interprete e adattatori* e non dichiara nessuna
dipendenza dalla piattaforma: ci arriva attraverso il nucleo. Un pannello e'
interfaccia, e l'interfaccia sta in `nli_web`. Cosi' il motore resta esercitabile senza
Odoo davanti, che e' la ragione per cui i suoi test girano in millisecondi.

**Il punto che valeva la pena non sbagliare.** Il pannello **configura, non mette in
servizio**. Scrive i parametri su una bozza e mostra i due passaggi veri — la
qualificazione di **D51** e l'attivazione — che restano quelli di sempre: **D80** (un
profilo mai qualificato non puo' essere attivato) continua a rifiutare, e il rifiuto
arriva come messaggio invece che come silenzio.

Una sezione delle impostazioni che avesse scritto `state = "active"` avrebbe reso il
cancello una formalita' aggirabile con due clic. Il cancello esiste perche' un modello
non qualificato puo' rallentare l'ERP **per tutti**, non solo per chi lo ha scelto.

**Un difetto trovato costruendolo, che vale per chiunque tocchi le impostazioni.** I
campi erano stati scritti come calcolati con inverso. `res.config.settings` costruisce
il proprio record con `default_get`, che **non esegue i calcoli**: `create({})`
restituiva i valori giusti mentre la pagina mostrava caselle vuote. Riscritti come
campi normali riempiti in `default_get` e riscritti in `set_values`, che e' il modo in
cui la piattaforma lo fa per se stessa e non dipende da quando girano i calcoli.

---

## 25. Il profilo e' in servizio, e la qualificazione non e' stata eseguita

Il 2 agosto 2026 l'Architect ha dato istruzione di qualificare e attivare il profilo
`qwen3.5:9b` per poter usare AIDA in sviluppo. E' stato fatto. **Il protocollo di D51 —
le otto verifiche, fra cui la prova di isolamento di D27 — non e' stato eseguito.**

Questa sezione esiste perche' quel fatto non resti solo in un campo di testo che nessuno
apre. Chi guarda il sistema vede un profilo `active`, e da `active` si deduce
normalmente che sia stato verificato: qui non lo e'.

**Cosa e' stato scritto dove.** La nota di qualificazione sul profilo dice per esteso
che la qualificazione non e' avvenuta, con la data e il motivo. **D80** (un profilo mai
qualificato non puo' essere attivato) non e' stata aggirata ne' allentata: la sua
condizione — passare da `qualified` — e' stata soddisfatta nel modo previsto, ed e' la
*dichiarazione* di qualificazione a essere, deliberatamente, una dichiarazione vuota.
La differenza conta: il meccanismo regge, la sostanza manca, e la seconda e' scritta
dove si vede.

**Cosa questo NON autorizza.** Non e' un precedente per le installazioni dei clienti,
dove un modello non qualificato puo' rallentare l'ERP per tutti. Prima del primo utente
vero, D51 va eseguita davvero e questa sezione va aggiornata con l'esito.

**Cosa ha permesso di verificare, subito.** Con il profilo in servizio, una domanda
posta dall'interfaccia ha attraversato tutta la catena — coda cifrata, cron, catalogo
costruito dai metadati Odoo veri, modello sull'host, validazione, bus — e ha prodotto
una risposta. La risposta e' stata **un chiarimento**: alla domanda *«mostrami i
contatti di Tracy»* AIDA non ha inventato un filtro, ha chiesto quale attributo
contenga il nome e ha proposto tre letture. E' **D106** (un rifiuto che propone le
letture plausibili) che funziona su dati veri, non sul corpus.

---

## 26. D117 — La data di creazione non e' un campo tecnico

**Il difetto, visto da un utente.** Alla domanda *«mostrami i lead di quest'anno»* AIDA
chiedeva quale data filtrare e proponeva: chiusura, conversione, scadenza,
assegnazione. Quattro date, e **non quella che una persona intende**. Il chiarimento
sembrava incompetente proprio dove doveva aiutare.

**La causa.** La regola 2 di `06` §5.3 esclude dal catalogo i nomi che Odoo mette su
ogni modello. Li trattava come un gruppo solo, ma non lo sono: `id`, `create_uid`,
`write_uid`, `display_name` non significano niente per chi lavora, mentre *«quando e'
stato creato»* e' la prima cosa che si intende quando si dice «di quest'anno».

**La decisione.** `create_date` esce dall'elenco dei campi di sistema ed e' esposto come
qualunque altro attributo. `write_date` resta fuori: *«quando e' stato modificato
l'ultima volta»* e' una domanda tecnica, non di lavoro.

L'alternativa che non toccava la regola era dichiararlo a livello L2 nel dizionario —
la regola 1 vince su tutte — ed e' stata scartata perche' avrebbe richiesto di farlo
entita' per entita', installazione per installazione, e fino ad allora ogni chiarimento
temporale avrebbe continuato a mancare l'opzione ovvia.

**Un secondo difetto trovato scrivendo il test, ed e' lo stesso di D109.** L'elenco dei
campi di sistema viveva in `introspection/l0.py`, che sta dietro un `__init__` che
importa l'ORM: un test puro non poteva leggerlo. E' un **fatto** — gli stessi nomi in
ogni installazione — non la lettura di un registro vivo. Spostato in
`nli_semantics/platform_types.py`, la zona pura che gia' ospita la mappa dei tipi, con
`l0` che lo importa. Due volte lo stesso difetto in due settimane dice che la regola
merita di essere guardata quando si scrive: **un fatto della piattaforma non va messo
dietro l'ORM.**

**Cosa NON ha risolto, e va detto.** Dopo la modifica la stessa domanda non produce piu'
un chiarimento: produce `out_of_scope` con nota `cancellazione_record`. Il modello ha
classificato *«mostrami i lead di quest'anno»* come una **cancellazione di record**.

Non e' una regressione di questa decisione: e' la stessa via d'uscita generica gia'
diagnosticata in §21.7 — nove rifiuti su 414 uscivano con `previsione` — che **D114** ha
ristretto per un solo verso. Il `scope_note` e' un insieme chiuso di cinque valori, tutti
legali, e il modello ne sceglie uno qualunque quando fatica. Restringere una parola alla
volta non chiude una porta che si apre da sola: e' il prossimo problema da affrontare, ed
e' fra gli aperti.

---

## 27. D118 — Il rifiuto si guadagna

**Il difetto, misurato due volte.** Nella rimisura di §21.7, nove rifiuti su 414
uscivano con `scope_note: "previsione"` — fra cui *«ordini lo scorso mese»*, che e' un
filtro su una data passata. **D114** ha ristretto quel verso, e la porta si e' aperta da
un'altra parte: sul campo, *«mostrami i lead di quest'anno»* e' uscito come
**`cancellazione_record`**.

**La causa non era la parola, era la porta.** `scope_note` e' un insieme chiuso di
cinque valori, tutti legali. Il modello ne sceglieva uno qualunque quando faticava,
perche' `out_of_scope` **non costava niente**: era facile quanto una risposta.
Restringere una parola alla volta non chiude un'uscita che si apre da sola.

**La decisione.** Un rifiuto per portata deve portare `scope_provenance`: **il pezzo di
frase che chiede la cosa impossibile**. E' la forma di **D105** (una condizione nominata
dev'essere fondata nel frammento che la giustifica) applicata al rifiuto invece che al
filtro: si chiede una prova verificabile al posto di una parola libera.

Il controllo e' **strutturale**, non contestuale, e la scelta conta: vive nel livello 1,
che `interpret()` esegue gia'. Quindi un rifiuto infondato viene respinto **dentro
l'interprete**, la riparazione singola di **D15** scatta, e il modello riceve l'errore e
risponde invece di uscire. Se il controllo fosse stato al livello 3 il turno sarebbe
finito, e il rifiuto sarebbe arrivato all'utente.

**Cosa e' costato.** L'esempio §17.5 della specifica del DSL non era piu' valido: il
contratto e' cambiato, quindi anche il documento e i suoi esempi vanno aggiornati, ed e'
il genere di cosa che si scopre solo se i test eseguono gli esempi del documento —
questi li eseguono. Rigenerati anche gli artefatti JSON derivati.

**Verificato sul campo.** Alla stessa domanda che produceva `cancellazione_record`, AIDA
risponde ora con un chiarimento: *«Il termine "lead" non e' presente nel catalogo
disponibile. Cosa intendi mostrare?»* con due letture. Non e' ancora la risposta
migliore possibile — `crm_lead` **e'** nel catalogo — ma e' un «non sono sicuro» onesto
al posto di un rifiuto senza senso, ed e' il verso che **D2** rende necessario.

**Cosa resta aperto.** Il controllo verifica che il frammento **ci sia**, non che
**giustifichi** la nota dichiarata: un modello puo' ancora citare un pezzo qualunque
della frase. La meta' lessicale — il frammento deve contenere le parole che chiedono
quell'azione — vuole un riconoscitore iniettato come quello di D112, perche' il lessico
e' di lingua e `nli_core` non ha lingua. E' il prossimo passo, e la misura dira' se
serve.

---

## 28. D119 — Il frammento deve dirlo davvero

**Cosa mancava a D118.** Il rifiuto per portata doveva citare un frammento, e il
controllo verificava che il frammento **ci fosse**. Non che dicesse qualcosa: restava
possibile rifiutare citando un pezzo qualunque della frase. Per la domanda che aveva
scoperto il difetto — *«mostrami i lead di quest'anno»*, uscita come cancellazione di
record — sarebbe bastato citare *«mostrami i lead»* e il rifiuto sarebbe passato.

**La decisione.** Il frammento citato deve contenere le parole con cui quella cosa si
chiede. Un lessico per categoria: *«cancell»*, *«elimin»*, *«rimuov»* per la
cancellazione; *«invia»*, *«manda»*, *«mail»* per l'invio; e cosi' per le altre tre.

**Radici e non parole intere.** *«cancell»* copre cancella, cancellare, cancellazione,
cancellale. Un elenco di forme flesse sarebbe sempre incompleto di una, e la forma
mancante sarebbe un rifiuto che passa.

**Dove sta, e perche' non nel nucleo.** Il lessico e' di lingua, e `nli_core` non ne ha
**per costruzione**: e' la ragione per cui il controllo di fondatezza di **D105** riceve
il riconoscitore come argomento invece di importarlo. Mettere parole italiane nel nucleo
per comodita' avrebbe rotto quella proprieta'. Sta in `nli_semantics/scope_lexicon.py`,
dichiarata zona pura — il file diceva di esserlo e non lo era, finche' non e' stato
scritto in `tools/arch/spec.py`, che e' l'unico posto in cui quell'affermazione diventa
verificabile.

**Una categoria sconosciuta passa.** Se `SCOPE_NOTES` cresce e il lessico non la segue,
quella categoria torna com'era prima di D119 invece di bloccarsi. Un vocabolario
incompleto non deve trasformarsi in un rifiuto di rifiutare.

**Cosa questo controllo non e'.** Non riconosce intenzioni: non decide se l'utente
voglia cancellare qualcosa. Decide se **il frammento che il modello ha citato** contiene
le parole con cui quella cosa si chiede. La prima domanda e' aperta, la seconda si
risponde confrontando due elenchi — ed e' l'unica che un controllo puo' porre
onestamente.

**Verifica.** 431 test in zona pura (erano 423), 56 file in zone pure, 117 test Odoo.
Sul campo la risposta alla domanda che aveva scoperto il difetto e' rimasta un
chiarimento: D118 aveva gia' chiuso quella strada, e D119 chiude quella che restava
aperta accanto — un rifiuto citato a caso. La misura dira' quanti erano.

---

## 29. D120 — Chi risponde a una domanda non riparte da zero

**Il difetto, segnalato dal campo.** AIDA chiede *«per "quest'anno" quale periodo
intendi?»*, l'utente risponde *«anno corrente»*, e AIDA riparte da capo come se quella
frase fosse una domanda nuova. E' il modo piu' rapido di far sembrare stupido un sistema
che aveva capito.

**La causa.** Il contesto di una conversazione viveva **solo nello stato**, e lo stato
lo scrive soltanto un turno che ha prodotto operazioni. Una richiesta di chiarimento non
ne produce: non scrive niente, e il turno dopo comincia da un foglio bianco. Il contesto
spariva esattamente nel punto in cui serviva di piu' — subito dopo una domanda.

**La decisione.** Quando il turno precedente si e' chiuso con una domanda, la richiesta
al modello porta due stringhe: la frase di allora e la domanda posta. Il modello e'
istruito a **comporle** invece di richiedere la stessa cosa.

**Due stringhe e non la conversazione.** Mandare la cronologia intera a ogni turno
farebbe crescere il prompt con la durata della chat, e la finestra e' gia' occupata a
meta' dal catalogo: **D79** ricava da li' il budget degli attributi, quindi una
cronologia che cresce si mangia il catalogo, cioe' proprio cio' che serve per capire.

**Solo il turno immediatamente precedente.** Una domanda a cui l'utente non ha risposto
subito non e' piu' in sospeso: ha cambiato argomento, e trascinarsela dietro sarebbe
peggio che dimenticarla.

**L'esito, riportato com'e'.** Il contesto adesso arriva al modello: la risposta al
seguito non riparte piu' da zero e parla del periodo invece che di nulla. **Ma la
composizione non e' ancora buona**: nella prova la seconda risposta ha perso l'entita' e
ha chiesto su quale attributo temporale filtrare. Due chiarimenti deboli in fila si
sommano, e il primo era gia' impreciso — diceva che «lead» non e' nel catalogo mentre
`crm_lead` c'e'.

Quindi: il canale del contesto e' aperto e verificato, la qualita' della composizione
no. La strada che chiude davvero il caso resta quella gia' registrata fra gli aperti —
**far scegliere le letture con un clic** (D106), dove le operazioni sono gia' nella
busta e non c'e' niente da ricomporre.

---

## 30. D121 — Una strada sola per il clic e per lo scritto

**Da dove viene.** L'ha decisa l'Architect il 2 agosto 2026, ed era il primo
dell'elenco degli aperti. Chiude il caso che **D120** (la decisione per cui chi
risponde a una domanda non riparte da zero: al modello arrivano la frase di prima e la
domanda posta) aveva aperto il canale ma non risolto.

**Il difetto.** **D106** (la decisione per cui un rifiuto propone: quando una condizione
nominata non e' fondata nel suo frammento, invece di fermarsi AIDA offre da due a
quattro letture prese dal catalogo) mette nella busta le operazioni di ogni opzione.
Poi le buttava via. Chi voleva scegliere una lettura doveva riscrivere la domanda a
mano, e la frase riscritta ripartiva dal modello: un minuto d'attesa per riscoprire una
lista che avevamo scritto noi — e per riscoprirla, magari, diversa.

**La decisione, in due parti che si tengono.**

*Primo: la frase che risponde a una domanda si confronta prima con le opzioni.* Se
corrisponde a una, si applicano le sue operazioni **senza passare dal modello**. Se non
corrisponde, si interpreta come una frase qualunque, con il contesto di D120.

*Secondo: il clic non ha un percorso proprio.* Cliccare un'opzione **scrive la sua
etichetta nella casella e la invia**. Da li' in poi e' una frase come tutte le altre.

**Perche' la seconda parte non e' una comodita' dell'interfaccia.** Se il clic mandasse
al server le operazioni, ci sarebbero due modi di far partire un turno: uno che passa
per la validazione delle frasi e uno che no. Resterebbero allineati finche' qualcuno se
ne ricorda, e il giorno in cui divergono lo fanno in silenzio — una richiesta che salta
un livello di controllo non fallisce, **risponde**. Cosi' invece la strada e' una per
costruzione: non c'e' una seconda strada da tenere allineata.

**La conseguenza che non era prevista, e che e' il pezzo interessante.** Una lettura
proposta non era applicabile com'era. L'opzione *«con partita iva»* sostituisce il
riferimento della condizione ma si porta dietro il frammento di prima — *«quelle
strane»* — e quel frammento non nomina **questa** condizione: applicata, la lettura
falliva di nuovo il livello 3, e per la ragione giusta. Era una scelta che non si poteva
prendere.

La riparazione non e' un'eccezione al controllo: e' che **il frammento adesso e' vero**.
Chi sceglie l'opzione dice quelle parole — le scrive o le fa scrivere dal clic — quindi
la provenienza della condizione e' l'etichetta, che e' esattamente cio' che §10.3 chiede
(il frammento della frase dell'utente che ha prodotto l'elemento). La condizione smette
di essere una cosa che il modello ha asserito e diventa una cosa che l'utente ha detto,
che e' precisamente la differenza che D105 (il livello 3 rifiuta una condizione nominata
non fondata nel proprio frammento) esiste per riconoscere. Nessun livello viene saltato:
il livello 3 gira e passa.

**Il riconoscimento e' sull'etichetta, non sulle operazioni.** L'etichetta e' l'unica
cosa che l'utente ha visto. Maiuscole, spazi doppi, virgolette e il punto finale non
sono scelte sue e non contano; **gli accenti si'** — due condizioni nominate che
differiscono per un accento sono due condizioni, e sceglierne una a caso in silenzio
sarebbe peggio che richiedere. Due opzioni che si leggono uguali non sono una scelta: la
frase passa alla strada ordinaria, che chiede.

**Solo il turno immediatamente precedente**, come D120. L'etichetta di una domanda
sorpassata non sceglie piu' niente: chi ha cambiato argomento e poi ha scritto per caso
quelle parole non sta rispondendo a nulla.

**La guardia sul doppio invio si e' spostata.** Stava nella casella di scrittura; ora
sta nel punto di partenza unico. E' la stessa regola applicata a se stessa: una guardia
che protegge una sola delle due strade protegge quella che nessuno usa per sbaglio, e un
doppio clic su una lettura manderebbe due turni identici.

**Cosa e' stato estratto, e perche' e' la parte rischiosa.** La coda di `pipeline.run` —
applicatore, livelli 3-5, risolutore, esecutore, presentatore — e' ora la funzione
`_apply_and_present`. Ci passano tutti e due i modi di produrre operazioni. E' un
percorso critico e coperto: il motivo per cui e' una funzione sola e' lo stesso della
seconda parte della decisione, cioe' che due copie andrebbero d'accordo il giorno in cui
sono scritte e non il giorno dopo.

**Verificato.** Sei prove Odoo sulla catena vera: la risposta con l'etichetta esegue e
**il modello non viene chiamato affatto** (l'adattatore registra zero richieste),
l'opzione che toglie il filtro non lascia condizioni, maiuscole e spazi non vanno
riprodotti, una frase che non e' un'opzione torna al modello **con** il contesto di
D120, e l'etichetta di un turno sorpassato non sceglie. Quattordici prove pure su
riconoscimento e fondazione. Il turno di chiarimento viene eseguito e **scritto** come
lo scrive il lavoratore, perche' e' nella persistenza che questa strada si sarebbe rotta
in silenzio.

**Quali chiarimenti copre davvero, e quali no.** Le letture di **D106** sono richieste
intere, perche' sono costruite da una: ognuna porta il proprio `set_target`. Ma non
tutti i chiarimenti nascono cosi' — quello che chiede *«per "quest'anno" quale periodo
intendi?»* lo scrive **il modello**, e le sue opzioni sono complete quanto il modello le
ha fatte. Un'opzione che porta la sola operazione che disambigua, senza entita', non si
applica a niente. Quando la conversazione non ha gia' un bersaglio, un'opzione cosi'
**non viene presa**: la frase torna alla strada ordinaria, che puo' ancora risponderle.
Applicarla e fallire trasformerebbe la risposta parziale del modello in un *«non ho
capito»* con il nostro nome sopra.

Conseguenza da dichiarare: **per i chiarimenti scritti dal modello, D121 aiuta solo
quando le opzioni sono complete.** Chiudere anche quel caso vuol dire costruire il
chiarimento temporale come si costruisce quello di D106 — da noi, dal catalogo, con le
operazioni intere — invece di chiederlo al modello. Non e' fatto ed e' fra gli aperti.

**Cosa non e' misurato.** L'effetto sull'accuratezza: questa strada non cambia cosa il
modello capisce, cambia cosa costa correggerlo. E l'interfaccia non ha prove
automatiche — il progetto non ne ha per il lato client — quindi il clic e' verificato
per costruzione (scrive nella casella e chiama la stessa funzione dell'invio) e non da
un test.

### 30.1 Cosa e' emerso mettendolo in servizio

Messo in servizio, D121 non funzionava. Non per un difetto suo: per tre difetti che
c'erano gia' e che nessuno poteva vedere finche' non c'era qualcosa che dipendesse dal
turno precedente. Vale la pena elencarli perche' hanno tutti la stessa forma — **un
fallimento che non si dichiara**.

**Uno: una riga di coda che finiva senza esecuzione non chiudeva il turno.** Scadenza
(L4), sostituzione, fallimento registrato dal cron: tutte passavano da `_finish`, che
scriveva sulla riga e non sul turno. Il turno restava senza esito, cioe' *in corso per
sempre*. E' esattamente il difetto che `worker._fail` era stato scritto per chiudere —
chiuso pero' per il solo percorso del lavoratore. Ora lo chiude `_finish`, e solo se il
turno e' ancora vuoto: un turno completato porta gia' la risposta del pipeline, e
sovrascriverla col nome dello stato della coda cancellerebbe la risposta.

**Due: un turno scartato copriva la domanda in sospeso.** D120 e D121 guardano il turno
immediatamente precedente. Quella regola serve a riconoscere che l'utente **ha cambiato
argomento** — ma un turno scaduto in coda non dice niente sull'utente, dice che la sua
frase e' andata persa da noi. Contarlo faceva sparire la domanda: la risposta a un
chiarimento tornava dal modello anche quando l'etichetta corrispondeva parola per
parola. Ora i turni che il sistema ha buttato via (`expired`, `superseded`, `failed`)
non contano come turni.

**Tre: l'interfaccia diceva «non ho capito» a un turno che nessuno aveva letto.** Il
ramo finale del filo dei messaggi raccoglieva ogni esito non previsto, e quindi anche
l'assenza di esito. E' la stessa bugia che §11 di `04` aveva gia' rifiutato per il
fornitore irraggiungibile: *«non ho capito»* invita a riformulare, e riformulare non
serve a niente quando la frase era giusta e non e' mai arrivata a nessuno. Ora scaduto,
sostituito e senza-esito hanno ciascuno la propria frase.

**E un quarto, che non c'entra con la coda.** Il primo turno che **riusciva** di ogni
conversazione moriva scrivendo lo stato: `dsl_version` e' obbligatoria nello schema
dello stato, una conversazione nuova parte da `{}`, e nessuno la metteva. Le altre tre
chiavi obbligatorie le riempiono l'applicatore e la normalizzazione; la versione no,
perche' non si deduce dalle operazioni — la dichiara l'interrogazione, ed e' un suo
campo. Non lo vedeva nessun test **perche' nessuna prova persisteva uno stato
eseguito**: si fermavano tutte all'esito. Il buco di copertura era piu' interessante del
difetto, ed e' ora coperto.

**Misurato sul database vero, con il modello vero.** *«mostrami i lead di quest'anno»* →
chiarimento in **96,0 s**. Risposta con l'etichetta della prima opzione → **operations
in 0,08 s, zero richieste al modello, 39 record**. E' la misura che dice cosa fa D121:
non cambia cosa il modello capisce, cambia cosa costa correggerlo.

**Un difetto trovato per strada, non risolto qui.** L'impronta che fa da chiave alla
cache della semantica (**D39**) guarda gruppi, societa', lingua e stato d'accesso dei
modelli, **non le voci approvate del dizionario**. Approvare una condizione nominata
(D108) non invalida la cache: la voce nuova non si vede finche' la cache non decade da
sola. Nelle prove si aggira svuotandola a mano. E' un aperto vero e sta nell'elenco.

---

## 31. D122 — Il tempo concesso al modello lo dichiara il profilo

**Da dove viene.** Dall'analisi del flusso chiesta dall'Architect il 2 agosto 2026,
dopo che ogni domanda dell'interfaccia rispondeva *«non ho capito la domanda, puoi
riformularla?»*.

**Il difetto, misurato.** Il modello in servizio — `qwen3.5:9b` su ollama, sul
processore della macchina che ospita Odoo — impiegava **60,1 secondi** per una singola
chiamata. L'adattatore ne concedeva **60, scritti in una costante**. Tre turni di fila
nella coda vera, ognuno finito dopo esattamente 61 secondi con
`failure_reason = provider_unavailable`. Non era una domanda difficile: nessuna domanda
poteva riuscire.

**La decisione.** Il tempo concesso per una risposta e' un **campo del profilo**, come
la finestra di contesto (D78), con un `CHECK` che ne rifiuta lo zero e un valore
predefinito di 180 secondi. Si modifica dal pannello dei modelli insieme agli altri.

**Perche' non una costante piu' grande.** Perche' non esiste il numero giusto. Un
modello da nove miliardi di parametri sul processore di un portatile impiega minuti; lo
stesso modello ospitato altrove impiega secondi. Una costante che va bene a uno
trasforma ogni turno dell'altro in un guasto — ed e' la stessa forma di D78, dove la
finestra e' dichiarata e non indovinata. Il valore predefinito e' generoso di proposito:
quello che ci si prende senza scegliere non dev'essere quello che rompe il caso su cui
si sviluppa.

### 31.1 La bugia che lo copriva

Il difetto sarebbe stato ovvio dal primo turno se l'interfaccia avesse detto cosa
succedeva. Diceva *«non ho capito la domanda»*.

`04` §11 stabilisce che il fornitore irraggiungibile e' un modo di fallire
**dichiarato**, e che deve arrivare all'utente come tale — «non ho capito» invita a
riformulare, e riformulare non serve a niente se la frase era giusta e non l'ha letta
nessuno. `worker.execute` lo rispettava: quando a mancare era **il profilo**, l'esito
era `unavailable`. Il pipeline no: quando a mancare era **la risposta**, teneva l'esito
`not_understood` che l'interprete gli restituiva — e quello e' il percorso che si
percorre sempre.

Due posti, la stessa condizione, due nomi, e quello sbagliato sul percorso normale. E'
la stessa forma di divergenza che **D121** ha chiuso per il clic e lo scritto, e la
correzione e' la stessa: un punto solo — `_provider_failure` — da cui passano tutti e
due i rami del pipeline.

L'interprete continua a restituire una busta `not_understood`, perche' e' l'unica che il
contratto gli permette di costruire senza modello. Il vocabolario dell'**esito del
turno** e' nostro, non del DSL: puo' dire cio' che serve all'interfaccia senza allargare
quello della busta.

**Verificato.** Tre prove Odoo: un fornitore muto produce `unavailable` e non
`not_understood`, raggiunge comunque il circuito, e la riga di coda lo registra come
guasto del fornitore con il turno che lo dice. Tre prove sul profilo: l'adattatore nasce
con il tempo dichiarato, il valore predefinito regge un modello locale, lo zero e'
rifiutato per nome del vincolo.

**Misurato dopo, sul database vero.** *«mostrami i lead creati quest'anno»* →
**operations in 103,1 secondi, 39 record**. E' il turno che con il limite di 60 moriva.

**Cosa resta da guardare, e non e' una decisione.** Il profilo in servizio dichiara una
finestra di contesto di **4096 gettoni**. D79 ne ricava il budget del catalogo, quindi
un valore basso non e' innocuo: taglia il catalogo che il modello vede. `qwen3.5:9b` ne
regge molti di piu'. Va guardato prima della prossima misura di accuratezza, perche'
misurare con un catalogo tagliato misura il taglio.

---

## 32. D123 — La modalità diagnostica viaggia con il turno

**Da dove viene.** Richiesta dall'Architect il 2 agosto 2026: *«ho bisogno di una
modalita' debug dove ad ogni prompt ottengo anche il DSL e la query che formula»*.

**Il problema, detto per bene.** Quando un turno va storto c'e' una sola domanda che
conta: **e' andato storto nel modello o dopo?** Fino a ieri non c'era modo di
rispondere senza aprire una shell. Le due giornate appena passate lo mostrano: il
chiarimento temporale sembrava un difetto di D121 ed era una riga di coda scaduta; il
«non ho capito» sembrava il modello che non capiva ed era un tempo scaduto. In tutti e
due i casi la risposta stava in dati che il sistema aveva e buttava via.

**La decisione.** Con la modalita' accesa, ogni turno conserva **come e' stato
costruito** e lo mostra sotto la risposta: la busta DSL uscita dal modello, lo stato che
ne e' derivato, **la query** con cui Odoo e' stato interrogato, e il tempo di ogni fase.

**Dove sta, e perche' non nei log.** Sul turno, in `debug_json`. **D60** vieta frasi
dell'utente e cataloghi nei registri diagnostici, e la busta contiene le une e l'altro:
un file di log e' esattamente il posto in cui non puo' andare. Sul turno invece e'
protetta dalle stesse cose che proteggono la frase — la regola di record di `nli.turn` e
la cancellazione a cascata con la conversazione — che e' la protezione che **D115** ha
gia' scelto per `utterance`. Non e' un archivio nuovo da gestire per dieci anni: e' un
campo in piu' sul record che c'era gia'.

**Due condizioni per vederla, non una.** Che la traccia *esista* dipende
dall'interruttore quando il turno e' corso; che si *veda* e' un'altra domanda, e la
risposta e' *solo un amministratore*. Se bastasse l'interruttore, spegnerlo non
nasconderebbe niente di cio' che era gia' stato raccolto — e un utente ordinario
davanti al dominio Odoo non ci ricava nulla, se non l'impressione che il prodotto gli
stia parlando addosso.

**L'interruttore e' un parametro di sistema, non un campo del profilo.** Non e' una
proprieta' del modello: e' una scelta di chi sta guardando. Spento di default, e da
spento **non si costruisce niente e non si conserva niente** — che e' precisamente cio'
che gli permette di portare la busta per intero quando e' acceso.

**Come e' agganciata al pipeline.** `run` e' diventata un guscio sottile attorno a
`_run`, e la traccia si attacca **li'**. Il corpo ha una decina di punti d'uscita:
attaccarla a ognuno avrebbe voluto dire che il primo dimenticato e' un esito che non si
sa spiegare, cioe' esattamente quello che si sta guardando quando la modalita' serve.
Dentro, una sola funzione `trace(collector, ...)` che non fa nulla quando il raccoglitore
e' `None` — una funzione muta e' piu' difficile da sbagliare di dieci `if debug` che
devono ricordarsi di essere tutti uguali.

**Nessun `sudo`.** Il primo tentativo leggeva il parametro con `sudo()` e il controllo
dei confini (**V2**, nessuna elevazione di privilegi sul percorso di interrogazione) lo
ha rifiutato. Aveva ragione e non serviva: i due soli chiamanti hanno gia' i diritti —
il ciclo del dispatcher, che gira nell'ambiente del cron, e il pannello, che apre solo
un amministratore.

**Verificato.** Sei prove Odoo sul pipeline (spenta non raccoglie niente; la traccia
porta la busta del modello; porta la query e non una sua descrizione; porta le fasi con
il loro costo; si scrive sul turno solo quando e' stata raccolta) e quattro
sull'esposizione (un utente ordinario non la riceve, un amministratore si', un turno
senza traccia non porta la chiave, una traccia illeggibile non porta giu' la
conversazione).

### 32.1 Cosa ha detto al primo giro

Acceso sul database vero, il primo turno ha risposto a una domanda aperta da giorni.
*«mostrami i lead creati quest'anno»*, 147,6 secondi in tutto:

    fase A — dizionario                     0,054 s
    fase B — modello: quale entita'       113,439 s
    fase C — catalogo                       0,249 s
    modello: la busta                      33,576 s
    esecuzione su Odoo                      0,031 s

**La fase B costa piu' del triplo dell'interpretazione vera.** E la fase B risponde a
una domanda sola — *di quale entita' si parla* — che e' il compito piu' piccolo dei due.
L'esecuzione su Odoo, cioe' la parte che tutti immaginano lenta, e' tre centesimi di
secondo.

Questo cambia l'aperto sulla latenza: non e' *«il modello e' lento»*, e' **«la fase B e'
la parte cara e chiede la cosa piu' facile»**. Le strade da pesare diventano concrete —
allargare la fase A perche' la fase B serva piu' di rado, oppure un modello piccolo per
la sola fase B. Il numero che sceglie fra le due adesso c'e', e prima non c'era.

---

## 33. D124 — Una strada sola verso lo schermo, e le regole che nessuno chiamava

**Da dove viene.** Dall'analisi di un'interazione, il 2 agosto 2026: *«mostrami i lead
creati da 6 mesi ad oggi»* rispondeva *«questa domanda non e' arrivata a una risposta»*.
Il turno era **riuscito**: `operations`, 39 record, query eseguita in 0,031 s.

### 33.1 Nessuna risposta riuscita e' mai stata disegnata

Il Presentatore produce una **struttura** — bersaglio, condizioni, periodi risolti.
Trasformarla in frasi e' `09` §3, e lo fa `nli.interpretation.in_words`: esiste,
e' documentato, ha quattordici prove verdi. **Non lo chiamava nessuno.** Il turno
memorizzava la struttura, il template cercava `parts`, e ogni `operations` finiva nel
ramo di scarto.

Due strade portavano al medesimo schermo: l'avviso sul bus, costruito in
`nli_dispatch`, e `_aida_payload`, costruito in `nli_web`. Nessuna delle due chiamava
la conversione. **Decisione: l'avviso dice solo che il turno e' finito**; cio' che si
disegna lo costruisce `_aida_payload`, e una volta sola. E' l'argomento di **D121**
applicato al percorso opposto — dal server allo schermo invece che dallo schermo al
server — e qui le due strade non rischiavano di divergere: erano gia' divergute.

Le parole si costruiscono **alla lettura**, perche' i termini vengono dal catalogo di
chi legge: due persone con permessi diversi vedono lo stesso turno con vocabolari
diversi, per la stessa ragione per cui il catalogo non si condivide fra utenti (D39).

### 33.2 Due periodi sullo stesso attributo si intersecano

Lo stato del turno portava `create_date within current_year` (dal turno prima) **e**
`create_date within last_n_months(6)`, in AND. L'utente aveva chiesto un periodo
nuovo e ha ottenuto l'intersezione.

Il raffinamento additivo di §17.1 e' giusto — e' cio' che fa funzionare *«solo quelli
attivi»* al secondo turno. Ma una frase che nomina **lo stesso asse** non ne aggiunge
uno: lo riscrive, e il DSL ha gia' `replace_condition`. Nuova regola di livello 4:
due predicati di periodo sullo stesso riferimento sono un rifiuto.

**Perche' strutturale e non un'istruzione al prompt.** Perche' il fallimento e'
**invisibile**: i due turni hanno restituito lo stesso numero di record — 39 e 39 —
perche' i sei mesi cadevano dentro l'anno. Niente da notare, nemmeno guardando. Forma
pura del rischio di **D2**.

### 33.3 E il livello 4 girava a meta'

Aggiunta la regola, **non scattava**. `contextual.validate` — la catena che il pipeline
esegue — chiama livello 3, poi `validate_types`, poi il costo. **Non ha mai chiamato
`coherence.validate_coherence`.** Profondita' del filtro, numero di raggruppamenti,
misure contro vista, coerenza fra predicato e valore: regole scritte, provate in zona
pura, e mai eseguite sul prodotto.

E' il terzo caso in due giorni della stessa forma — `in_words`, `coherence`, e prima
`_finish` che non chiudeva il turno: **codice corretto, provato, e non collegato**. La
prova verde stava sempre un passo prima del punto in cui la cosa serviva. Ora la catena
esegue tutte e due le meta' del livello 4.

### 33.4 Le viste di risposta

`15` chiede, per le tabelle: ricerca, ordinamento, filtri, selezione multipla, gestione
e ridimensionamento colonne, preferenze salvate, paginazione con totali. E' l'elenco di
cio' che la **vista lista di Odoo fa gia'**, con i diritti e le preferenze di chi
guarda. `00` §23 aveva deciso di incorporarla; ora e' fatto: il turno conserva il piano
risolto (`plan_json`), il payload ne espone il dominio, e un componente monta la vista
nativa dentro la risposta.

**Esce il dominio, non i record.** La vista li rilegge da sola: un dominio che tornasse
indietro da un utente a cui e' stato tolto un permesso non gli mostrerebbe niente di
piu' di quanto vedrebbe aprendo il menu — stessa regola di record, stessa vista.

**Cosa resta scoperto, dichiarato invece che aggirato.** La paginazione di Odoo si
governa scrivendo l'intervallo, non da una tendina 10/25/50/100. Una barra nostra
riporterebbe dentro la duplicazione appena evitata.

**Verificato sul database vero.** *«mostrami i lead creati quest'anno»* → `operations`
in 112 s, **39 record, 4 parti disegnabili**, dominio
`[("create_date",">=","2026-01-01"),("create_date","<","2027-01-01")]`.

**Un difetto minore, visto e non risolto.** Il Presentatore associa i periodi risolti
alle condizioni **per riferimento**: con due condizioni sullo stesso attributo mostrava
due righe identiche. Con §33.2 quello stato non arriva piu' all'esecuzione, ma
l'accoppiamento resta fragile e va guardato quando si toccheranno i periodi.

### 33.5 Il difetto che ha rotto la chat, e il quinto controllo

Distribuito D124, **le opzioni di disambiguazione sono sparite**. Non erano sparite le
opzioni: era sparito il filo dei messaggi. Una riga aggiunta a colpi di sostituzione
aveva messo `AidaRecords` fra i `static components` di `AidaThread` **senza importarlo**.
Il modulo fallisce quando viene valutato, il componente non si registra, e tutto cio'
che il suo template disegna scompare — **senza un solo errore lato server**.

I 147 test Odoo erano verdi mentre la chat non si apriva. Non e' una prova che mancava:
**non esiste nessuna prova del lato client in questo progetto**, ed e' il rischio piu'
grande che resta aperto ora che l'interfaccia e' la parte che si tocca di piu'.

Nell'attesa, un controllo statico: **il quinto dei confini di D24** verifica che ogni
nome dentro `static components` sia importato o definito nello stesso file. Non e' un
analizzatore JavaScript e non finge di esserlo — prende il caso in cui il nome non c'e'
proprio, che e' quello capitato. Verificato togliendo di nuovo l'import: il controllo
fallisce e nomina file, riga e componente.

Il numero dei controlli e' asserito nelle prove, perche' un controllo che sparisce
dall'elenco non fallisce: smette di guardare, e l'elenco resta verde.

### 33.6 La tabella e' una tabella, non un secondo modo di chiedere

Deciso dall'Architect subito dopo: la vista incorporata **non porta la barra sopra** —
niente pulsante *Nuovo*, niente barra di ricerca, niente titolo.

*Nuovo* aprirebbe un modulo di creazione dentro la risposta a una domanda, e **D2**
(finche' la Fase 2 non e' misurata e superata non si scrive sui dati) dice che da qui
non si scrive: un pulsante che non deve essere premuto e' peggio di un pulsante assente.
La barra di ricerca sarebbe una **seconda strada per dire cosa si vuole**, accanto alla
domanda in italiano che e' il prodotto — e una che non passa dall'interpretazione,
quindi non comparirebbe in cio' che AIDA dichiara di aver capito. Il numero mostrato
smetterebbe di corrispondere alla spiegazione sopra di esso. E' l'argomento di D121 su un
altro pezzo.

Restano ordinamento per colonna e ridimensionamento: sono lettura, non riformulazione
della domanda.

**Il prezzo, dichiarato.** Spegnere il pannello di controllo porta via anche la
**paginazione**, che `15` chiede. Oggi si vedono i record fino al limite deciso
dall'interpretazione e non oltre. Rimetterla vuol dire riaccendere il pannello tenendo
spente le sue parti di sinistra e di destra, che e' una riga sola ma dipende da nomi
interni di Odoo che cambiano fra versioni. Sta fra gli aperti.

---

## 34. D125 — Un periodo nuovo prende il posto del precedente

**Da dove viene.** Da un caso portato dall'Architect il 2 agosto 2026, con la modalita'
diagnostica accesa: *«la prima richiesta e' andata a buon fine, la stessa richiesta poi
non la comprende»*.

**Cosa succedeva.** Tre turni sulla stessa data:

    «i lead creati quest'anno»        -> operations, stato: 1 periodo
    «creati da 6 mesi ad oggi»        -> operations, stato: 2 periodi in AND
    «i lead creati quest'anno»        -> 3 periodi -> livello 4 rifiuta
    «i lead creati quest'anno»        -> 3 periodi -> rifiuta ancora

**La conversazione era bloccata, e senza via d'uscita.** Ogni tentativo di rimediare
aggiungeva un periodo in piu' e falliva allo stesso modo. Non c'era modo di uscirne
parlando, che e' l'unico modo che l'utente ha.

**Cosa avevo sbagliato in §33.2.** La regola di livello 4 riconosceva la cosa giusta e
faceva la cosa sbagliata: **rifiutava invece di riparare**. Un rifiuto e' l'esito giusto
quando l'utente puo' agire; qui non poteva. E il difetto era peggiore di quello che la
regola sostituiva — prima si otteneva una risposta silenziosamente stretta, dopo non si
otteneva piu' niente e per sempre.

**La decisione.** Nell'Applicatore: un `add_condition` con un predicato di periodo, sotto
`all`, **toglie i periodi che c'erano su quell'attributo** e mette il proprio.

**Perche' sostituire e non chiedere.** §17.1 e' giusto per un asse nuovo — *«solo quelli
confermati»* si somma — ma una frase che nomina di nuovo lo stesso asse non ne aggiunge
uno: lo riscrive. Nessuno chiede l'intersezione fra due periodi dicendo due periodi; se
la volesse la direbbe come un periodo solo. E' la forma di **D89** e **D99**: quando la
forma dello stato impone cio' che l'utente intendeva, si deriva invece di domandare
(C2/P4).

**Perche' toglie tutti i periodi e non il primo.** Cosi' uno stato gia' rovinato **si
ripara da solo** al primo turno che nomina di nuovo quell'asse. Le conversazioni guaste
da prima di questa regola guariscono parlando, che e' l'unico rimedio che si puo'
chiedere a un utente.

**Solo sotto `all`.** Sotto `any` due periodi sono un'unione, e *«di marzo o di
settembre»* e' una cosa che si puo' voler dire davvero.

**La regola di livello 4 resta**, e cambia mestiere: da rimedio a **rete di sicurezza**.
Dopo la sostituzione due periodi sullo stesso attributo non possono piu' nascere per la
strada normale; se ne compaiono, e' un difetto nostro e va detto, non subito.

**Verificato.** Cinque prove pure: il secondo periodo sostituisce il primo; uno stato
gia' rovinato si ripara; un periodo su un altro attributo si somma ancora (§17.1 regge);
una condizione che non e' un periodo si somma; sotto `any` i due periodi sopravvivono.

**Cosa insegna, oltre al caso.** Una regola che rifiuta va sempre guardata due volte:
**il rifiuto e' giusto solo se chi lo riceve ha una mossa**. Qui non l'aveva, e una
protezione senza uscita e' un guasto con una spiegazione migliore.

---

## 35. D126 — Un'entità si chiama come la chiama la gente

**Da dove viene.** Dal problema portato dall'Architect il 2 agosto 2026: lo stato di una
conversazione si accumulava e non c'era modo di distinguere una domanda nuova da un
raffinamento. Il segnale naturale — *la frase nomina la propria entità?* — non era
misurabile, perché **la fase A non riconosceva nessuna entità**.

**La causa, misurata.** Ogni entità aveva **un termine solo: l'etichetta Odoo grezza**.
`crm.lead` si chiamava `Lead/Opportunità`. Il normalizzatore la riduce ai gettoni `lead
opportunita`, e come termine unico pretende di trovarli tutti e due di fila: nessuna
frase italiana lo fa. Su otto frasi di prova, **zero risolte** — nemmeno
*«opportunità»*, che è metà del nome del modello.

Non era un difetto del metodo: il corpus misura la fase A all'**86,2% con zero
determinazioni sbagliate**. Era vocabolario che non esisteva.

**La decisione: raccogliere, non generare.** Le parole che l'utente usa sono già scritte
nell'installazione, in tre posti, e sono tutte vere:

* l'etichetta **e i suoi pezzi** — `Lead/Opportunità` sono due nomi, non uno;
* i nomi delle **azioni** che aprono quel modello **da un menu**;
* i nomi delle **voci di menu** che ci portano.

**Il plurale si legge, non si costruisce.** Il modello si chiama *Contatto*, il menu
*Contatti*, e la gente dice il secondo. Leggerlo evita di scrivere regole di morfologia
italiana che sbaglierebbero su *«Registrazioni contabili»* e sulle parole straniere, si
traduce da solo, e segue il cliente che rinomina un menu.

**Perché non chiedere i sinonimi al modello.** P4. Un nome di entità inventato è
esattamente il fallimento che D14 e D105 esistono per impedire, sarebbe da rifare a ogni
installazione, e non ci sarebbe modo di verificarlo. Il modello non decide cosa esiste.

**Perché non un file di sinonimi come fondamento.** Non scala a 741 voci, invecchia al
primo aggiornamento di Odoo, ed è per cliente. Il registro delle voci approvate (D108,
livello L2) resta la strada per il **gergo** — *«pratiche»*, *«trattative»* — e il
vocabolario si somma fra i livelli, come `06` §2.2 aveva già stabilito: un sinonimo
aggiunto non cancella quelli di base.

### 35.1 Il guardiano che buttava via le prove esatte

Arricchiti i nomi, due frasi su otto continuavano a non risolvere — e non per ambiguità:
i candidati erano **zero** anche se il termine c'era.

    === le fatture non pagate
       ENTITA' span=(1,1) score=1.00 account_move
       campo   span=(1,1) score=1.00 res_partner.invoice_ids
       campo   span=(1,1) score=1.00 sale_order.invoice_ids

**V-D93-1** dice che un pezzo di frase è prova di un'entità solo se nessun termine che
entità non è lo copre altrettanto bene. Il campo *Fatture* su un partner si chiama come
l'entità *Fatture*: tre prove esatte identiche, e il guardiano le buttava tutte.

Il caso per cui il guardiano è stato scritto è **diverso**, e il codice lo raccontava
già: *«fatt. cliente … raggruppati per cliente»* risolveva a `clienti` perché
l'attributo *cliente* e l'entità *clienti* hanno la stessa **forma base**. Lì l'entità
arrivava dal livello morfologico — un'evidenza *più debole* di quella che le si
opponeva — e scartarla era giusto.

**La decisione: il guardiano vale contro le prove morfologiche, non contro quelle
esatte.** Se l'utente ha detto *«fatture»* e le fatture sono un'entità, le fatture sono
un candidato; se ce ne sono due, decide il margine, che è lì apposta (D33).

### 35.2 Il registro dichiarava T1 approvabile e non ne accettava nessuno

Scrivendo le prove ho provato a dare a un'entità un nome con una voce approvata — la
strada che D108 offre. **Rifiutata.** `nli.dictionary.entry` elenca T1 fra i tipi
approvabili, ha `entity_ref` obbligatorio, e `to_entry` lo metteva sempre nella voce; ma
per un T1 `entity` non è una chiave ammessa, e il validatore la rifiutava. Il registro
prometteva una porta che non si apriva.

Un T1 non ha bisogno di dichiarare l'entità: ce l'ha nel proprio riferimento —
`res_partner` la nomina, `res_partner.city` la contiene.

**Verificato.** Undici prove Odoo sul meccanismo — non sui dati dell'installazione, che
cambiano con i moduli e con la lingua: l'etichetta composta diventa più nomi, l'intera
resta, il nome del menu diventa un termine, un'azione che nessun menu raggiunge no, un
nome troppo corto no, e i campi tengono la loro etichetta sola. Tre prove pure sul
confine del guardiano, fra cui quella che **protegge il caso per cui esiste**: un'entità
che arriva dalla forma base viene ancora scartata.

**Misurato sul database vero, da 0/8 a 6/8.** I due che restano non risolti sono quelli
che devono restare — *«quelli che hanno per mail…»*, *«solo quelli confermati»* — perché
non nominano un'entità: è esattamente il segnale che serviva a D127.

**Cosa non è misurato.** Il corpus gira su un pacchetto di dizionario scritto a mano,
non sull'introspezione L0: i suoi «0 determinazioni sbagliate» restano veri e **non
coprono** questo cambiamento. Il rischio che un nome di menu tiri a sé una frase che non
gli appartiene — *«Flusso»* verso i lead — lo sorveglia solo il margine della fase A, e
va misurato su un'installazione vera.

---

## 36. D127 — Chi nomina la propria entità fa una domanda nuova

**Da dove viene.** *«mostrami quelli che hanno per mail md@…»*, poi *«MOSTRAMI DI NUOVO
I LEAD DI quest anno»*: la seconda frase non c'entrava niente con la mail e rispondeva
sul residuo della prima. Lo stato si accumulava e **non c'era modo di ricominciare
parlando**.

**La decisione.** Una frase che nomina la propria entità è una domanda nuova e lo stato
riparte da lì; una che non la nomina è un raffinamento e continua.

Riparte **da vuoto**, non da «vuoto tranne il bersaglio»: le operazioni del turno
ricostruiscono tutto, perché il modello emette sempre `set_target` per primo. E al
modello si passa `state=None`, che gli toglie di dosso un contesto che non c'entra più.

**La fase A gira sempre**, anche con un bersaglio nello stato. Prima si fermava lì, e
con lei spariva il solo segnale che distingue i due casi. Costa cinque centesimi di
secondo ed è il dizionario, non il modello: nessuna decisione probabilistica dove la
forma della frase decide già (C2/P4).

**Chiude un secondo difetto che nessuno aveva ancora incontrato.** Con un bersaglio nello
stato, **cambiare entità era impossibile**: *«adesso mostrami le fatture»* saltava la
fase A, il modello riceveva lo stato dei lead e ci restava. La stessa regola lo risolve
senza aggiungere niente.

**Nell'incertezza si continua, non si riparte.** I due errori non sono uguali: la fase A
che non riconosce tratta una domanda nuova come raffinamento — silenzioso e cumulativo;
la fase A che riconosce a sproposito tratta un raffinamento come domanda nuova — la
risposta resta **corretta per quello che è stato detto**, il conteggio che cambia lo
rende visibile, e si rimedia ripetendo la frase. Ma §17.1 — *«solo quelli confermati»* al
secondo turno — è ciò che regge la conversazione, e romperlo per prudenza sarebbe uno
scambio pessimo.

**La precisione della regola è la precisione della fase A**, ed è per questo che D126
viene prima: con la fase A che non riconosce niente, questa regola sarebbe un `if` che
non scatta mai.

**Un secondo segnale, no.** I marcatori del discorso — *«quelli»*, *«solo»* contro *«di
nuovo»*, *«adesso invece»* — non sarebbero estranei all'architettura (`scope_lexicon` è
già questo genere di cosa). Ma due segnali insieme vogliono dire non sapere quale ha
lavorato. Uno, misurato, e poi si vede.

**Come se ne accorge l'utente.** Da **quanto ha trovato**, che è il numero che gli
interessa. Non da un'etichetta *«nuova domanda»*, che in una schermata che vogliamo
pulita sarebbe rumore. E se qualcosa non torna, *«Come ho letto la domanda»* porta i
criteri per intero: è il motivo per cui quel riepilogo è ripiegato e non tolto, e senza
di esso questa regola sarebbe più rischiosa di quanto valga.

**Verificato.** Sei prove: riparte, non chiede al modello quale entità, non gli passa lo
stato vecchio, il raffinamento continua **e** riceve lo stato, e la traccia dice quando
ha ripartito.

---

## 37. D128 — Una domanda che facciamo deve avere risposte che funzionano

**Da dove viene.** Dal campo, il 3 agosto 2026, con la modalità diagnostica accesa. AIDA
ha chiesto per quale data filtrare e ha offerto quattro opzioni. Dietro *«Filtra per Data
creazione»*:

    {"op": "add_condition", "condition": {"ref": "crm_lead.create_date",
                                          "predicate": "within"}}
    {"op": "add_condition", "condition": {"ref": "crm_lead.date_closed",
                                          "predicate": "within"}}

Un `within` **senza periodo**, e una condizione sulla data di chiusura dentro l'opzione
della data di creazione. L'utente ha cliccato, D121 ha riconosciuto l'etichetta e ha
applicato fedelmente qualcosa che non era applicabile: *«non ho capito»*, dopo un clic e
due minuti.

**Dove stava il buco.** D121 poggia su *«le operazioni di ogni opzione sono già nella
busta»*. È vero per le letture di **D106**, che costruiamo noi dal catalogo e sono valide
per costruzione. Non è vero per un chiarimento che scrive **il modello**: veniva
memorizzato com'era, e le operazioni dentro le opzioni non passavano da nessuna
validazione. Restavano lì, invalide, finché qualcuno non cliccava — e allora il difetto
usciva dalla parte sbagliata della conversazione, come un fallimento dell'utente invece
che del modello. Fin lì avevamo controllato **quante** opzioni c'erano e mai **se
funzionavano**.

**La decisione.** Ogni opzione si valida con la catena strutturale e con la coerenza —
la stessa che valida una risposta — **nel momento in cui la domanda si memorizza**.
Quelle che non passano non si mostrano. Se non ne restano almeno due non è un
chiarimento (`01` §11.2: una sola opzione è una conferma travestita) e il turno diventa
un onesto *«non ho capito»* **subito**, mentre l'utente sta ancora leggendo la propria
frase.

Servono tutti e due i controlli: lo strutturale prende la busta malformata, la coerenza
prende il caso vero — un `within` senza periodo è strutturalmente una condizione a
posto, ed è il livello 4 a sapere che quel predicato un valore lo vuole. È lo stesso
`coherence` che fino al giorno prima non era nemmeno sul percorso (§33.3).

**E le due strade, di nuovo.** Messa la validazione, le prove hanno continuato a
fallire: un chiarimento può nascere in **fase B** — *«di quale entità parli?»* — oppure
in **fase C**, e le due impacchettavano l'esito terminale ognuna per conto suo. Ne avevo
protetta una. Ora c'è `_terminal_outcome`, e ci passano entrambe.

**Verificato.** Cinque prove: l'opzione inapplicabile non si offre, una domanda senza
risposte utilizzabili non è una domanda, un solo superstite è una conferma travestita, un
chiarimento sano passa intatto, e la traccia dice **quale** opzione è stata rifiutata e
perché.

**Cosa non risolve, e va detto.** La guardia impedisce di offrire opzioni rotte; non fa
funzionare la domanda. Su `crm.lead`, che espone quattro date, ogni frase che nomina un
periodo senza dire quale data finisce in un rifiuto onesto invece che in una risposta.
La strada è **costruire il chiarimento temporale come quello di D106** — le opzioni le
facciamo noi dall'ancora del tempo, complete — e richiede che il modello ci dica il
periodo invece di provare a scrivere le opzioni: è una delibera di contratto, ed è il
primo degli aperti.

---

## 38. Il difetto che si ripete: dichiarato, provato, non collegato

Non è una decisione. È un'osservazione che questa sessione ha guadagnato il diritto di
fare, e che vale più di ognuna delle correzioni che l'hanno prodotta.

**Sette volte in tre giorni**, sempre la stessa forma:

| dove | cosa era vero | cosa non era vero |
|---|---|---|
| `_finish` | chiudeva la riga di coda | non chiudeva il turno (§33.5 lo mostra a valle) |
| `in_words` | esisteva, documentato, quattordici prove verdi | **non lo chiamava nessuno** (§33.1) |
| `coherence.validate_coherence` | scritto, provato in zona pura | **non era sul percorso** del pipeline (§33.3) |
| T1 nel registro | dichiarato approvabile | **rifiutato a ogni scrittura** (§35.2) |
| il fallimento del fornitore | dichiarato `unavailable` in `worker` | detto `not_understood` nel pipeline (§31.1) |
| i due rami terminali | validati in fase C | non validati in fase B (§37) |
| la fase A | misurata all'86,2% | **non girava** con un bersaglio nello stato (§36) |

In tutti e sette i casi il codice era corretto e le prove erano verdi. Erano verdi **un
passo prima** del punto in cui la cosa serviva: si asseriva l'esito e non ciò che
l'utente vedeva, il componente e non il suo collegamento, la regola e non la catena che
la esegue.

**Cosa cambia da adesso.** Una funzione nuova non è finita quando è provata: è finita
quando esiste una prova che **fallisce se qualcuno la scollega**. Le prove aggiunte in
questi giorni sono scritte così di proposito — un turno riuscito deve produrre qualcosa
che la chat sappia disegnare, una riga di coda che finisce deve chiudere il turno, il
numero dei controlli dei confini è asserito perché un controllo che sparisce dall'elenco
non fallisce, smette di guardare.

Il quinto controllo di D24 nasce da qui: dopo che un componente OWL dichiarato e non
importato ha fatto sparire l'intera chat con 147 prove verdi, un controllo statico non
sostituisce le prove che mancano, ma prende senza far girare niente la classe di errore
che nessuno stava guardando.

**Il rischio più grande che resta aperto** è quello che ha prodotto due dei sette: **non
esiste nessuna prova del lato client**, e l'interfaccia è ormai la parte che si tocca di
più.

### §38.1 — Il controllo di architettura del 3 agosto: non erano sette

L'audit completo chiesto da `ai/16-controllo-architettura.md` è in
`ai/17-esito-controllo-architettura.md`. Ha trovato **altre undici occorrenze della
stessa forma**, tutte precedenti alla regola di §38, e sei reperti gravi.

Tre tolgono al prodotto capacità che `16` elenca come obiettivo: **le aggregazioni non
vengono mai calcolate** (`executor.aggregate` non ha chiamanti — `SUM`, `AVG`, `MIN`,
`MAX` non arrivano da nessuna parte), **i join non esistono** (nessun riferimento
attraversa mai una relazione, e il `Binding` documenta un percorso puntato che nessuno
emette), **l'ordinamento e le colonne non arrivano alla tabella** che l'utente guarda
(`AidaRecords.viewProps` ignora `order` e `fields`, quindi *«i 10 lead con fatturato
più alto»* mostra dieci righe ordinate come Odoo ordina di suo).

Tre sono comportamento sbagliato che nessuno vede: **nessun tetto ai record** sul
percorso vivo — `coherence.validate_cost`, dove sta il massimo di 500 di **D13**, non è
chiamata da nessuno, e la riga si può chiedere in italiano; il **fuso orario** manca su
ogni condizione temporale che tocca un `datetime`, cioè su `create_date`, che **D117**
ha appena rimesso nel catalogo; e il **catalogo è tagliato a 17 attributi** con la
finestra di 4096 del profilo in servizio, il che rende falsa oggi la proprietà con cui
**D32** chiude **RC3** (*«in fase C non c'è selezione»*).

**La lezione che l'audit aggiunge a §38.** Sette degli undici casi sono lo stesso pezzo
di catena — fra il piano risolto e lo schermo — e tutti sono provati **a monte** del
punto in cui servivano. La causa comune è che **non esiste una sola prova che parta da
una frase e arrivi a un numero**: le 1 549 prove verdi guardano l'esito e il conteggio,
mai l'ordinamento, le colonne o le misure. La regola di §38 è necessaria e non
sufficiente; quello che manca è il banco punta-a-punta descritto in `17` §5.

---

## §39 — Le sei delibere del controllo di architettura (D129–D134)

Deliberate su delega dell'Architect il 3 agosto 2026, tutte nate dai reperti di `17`.
Sei correzioni, e nessuna aggiunge una capacità: rimettono in servizio cose che il
progetto credeva di avere.

### §39.1 — D129: il livello 5 girava a metà, come il livello 4 prima di §33.3

`00` §33.3 ha scoperto che `coherence.validate_coherence` non era sul percorso e l'ha
collegata. **Ha lasciato indietro la sua vicina di modulo.** `coherence.validate_cost`
— che porta il massimo assoluto di 500 record di **D13** (la decisione che fissa il
limite predefinito a 80 e il massimo a 500) e il limite di due salti di relazione di
**D12** (i limiti strutturali che rendono il costo calcolabile a priori) — non era
chiamata da nessuno.

`contextual.validate` chiamava la **propria** `validate_cost`, che è un'altra funzione
e guarda solo il costo delle categorie. E anche quella girava a vuoto: il pipeline non
passava `category_costs`, che valeva `{}`.

**Provato, eseguendo la zona pura**: `set_limit` a un milione passava la validazione
strutturale, passava lo stato, passava i livelli 3-5 senza un rifiuto e arrivava
all'Esecutore, che chiedeva un milione di record a Odoo su un processo cron condiviso.
Nessun privilegio da scalare: bastava scriverlo in italiano. È l'unico reperto
dell'audit con una faccia di sicurezza, ed è di disponibilità — non di chi chiede, ma
di tutti gli altri.

**Le due metà si sommano invece di fermarsi alla prima**, perché sono lo stesso
livello: un'interrogazione può essere insostenibile per due ragioni insieme, e dirne
una sola costringerebbe l'utente a due giri per scoprire la seconda.

Il costo delle categorie lo costruisce ora `nli_semantics`, e **anche per le condizioni
che non si legano**: un aggregato è esattamente il caso che resta senza binding, ed è
l'unico che il livello 5 deve poter contare. Leggerlo solo dalle condizioni legate
avrebbe costruito una tabella dei costi con dentro tutto tranne ciò che costa.

### §39.2 — D130: le aggregazioni esistevano e nessuno le calcolava

`executor.py` aveva due funzioni: `execute`, che fa il conteggio e la ricerca, e
`aggregate`, che fa `_read_group` — l'aggregazione vera dell'ORM. **`aggregate` non
aveva chiamanti**, in nessun punto del repository, e nessun test la esercitava.

Quindi lo stato poteva portare `avg` su un importo, il piano la portava avanti
fedelmente, il Presentatore la elencava nell'interpretazione mostrata sopra la
risposta — e il numero non lo calcolava nessuno:

* *«qual è il fatturato medio dei lead»* → l'elenco dei lead. Nessun numero, sotto la
  scritta «media di fatturato»;
* *«il fatturato medio per stato»* → un grafico di **quantità**, perché la vista di
  Odoo senza misure dichiarate ricade sul conteggio.

`COUNT` e `GROUP BY` sopravvivevano per caso: il primo da `search_count`, che c'è per
**D68** (il conteggio prima del recupero, per poter dire *«i primi 80 di 1 243»*); il
secondo perché il raggruppamento arrivava alla vista lista di Odoo, che sa raggruppare
da sola.

**Una porta sola.** Due funzioni pubbliche erano la scelta che il chiamante sbagliava:
ora `executor.run` guarda il piano e decide il ramo, ed è lo stesso rimedio di
`_apply_and_present` (**D121**, l'unica strada per il clic e per lo scritto) applicato
un gradino più in basso.

**Le righe si leggono sempre**, anche quando ci sono misure, perché **D89** (la
delibera che risolve la contraddizione fra §5.6 e §6.7: una misura senza raggruppamento
resta una lista) dice che quella è una lista, e una lista senza righe non è niente.

### §39.3 — D131: due ore che nessuno vedeva

Odoo conserva i `datetime` in **UTC**. Il calendario ragiona nei **giorni dell'utente**,
perché *«questo mese»* deve voler dire il suo mese (§9.2). I due non si incontravano:
gli estremi di un periodo uscivano come date nude — `('create_date', '>=',
'2026-08-03')` — e finivano confrontati con una colonna in un'altra unità di misura.

Su un'installazione italiana d'estate lo scarto è di due ore: *«i lead creati oggi»*
**escludeva** quelli inseriti fra mezzanotte e le due e **includeva** quelli di ieri
sera dopo le 22. Un numero plausibile, vicino a quello giusto, e sbagliato. Su
*«quest'anno»* due ore su 365 giorni non si vedono; su *«oggi»* sono l'8% delle righe.

Il campo colpito è `create_date`, cioè proprio quello che **D117** (la decisione che lo
toglie dai campi tecnici, perché *«quando è stato creato»* è la prima cosa che si
intende con «i lead di quest'anno») ha appena rimesso nel catalogo.

**Il fuso viaggia come nome, non come scostamento.** Un numero di ore sarebbe sbagliato
metà anno: l'ora legale lo cambia, quindi *«il mese scorso»* chiesto a novembre e
chiesto a giugno non si convertono allo stesso modo. Il nome porta con sé la regola.

**Su un campo `date` non si converte niente**, e serve dirlo quanto l'altra metà:
convertire anche le date pure sposterebbe *«scaduto oggi»* di due ore su un campo che
di ore non ne ha, che è lo stesso difetto col segno invertito.

**Un fuso sconosciuto non fa fallire un'interrogazione**: si torna a UTC, cioè al
comportamento di prima. Una risposta col fuso sbagliato è un difetto; una conversazione
che si rifiuta di rispondere perché un `tz` è scritto male è un difetto peggiore.

### §39.4 — D132: la tabella non era il risultato del piano

`00` §33.4 ha deciso di incorporare la vista lista di Odoo invece di riscrivere
ricerca, colonne e paginazione. La decisione è giusta. Quello che non è stato fatto è
**passarle il resto del piano**: sono arrivate le due chiavi che facevano comparire la
tabella, e le altre no.

`_aida_query` calcolava e mandava al client sette chiavi. Il componente `AidaRecords`
ne usava quattro. **`order` e `fields` erano ignorati**, e le misure non partivano
affatto.

Quindi la tabella non era il risultato dell'interrogazione: era una rilettura del solo
dominio, ordinata come Odoo ordina quel modello per conto suo. *«I 10 lead con il
fatturato più alto»* mostrava dieci righe plausibili, con il limite giusto e
l'ordinamento sbagliato, sotto un'interpretazione che dichiarava l'ordinamento giusto.
Nessun errore da nessuna parte — la forma di **D2** (la decisione che fa della Fase 2
un cancello obbligatorio prima di qualunque scrittura) applicata alla tabella.

Ora l'ordinamento e i raggruppamenti passano come **proprietà** della vista, non come
contesto, e le misure entrano nel contesto che pivot e grafico leggono.

**Resta aperto `fields`**, e va deciso e non aggirato: per rispettare le colonne che
l'utente ha chiesto bisogna generare noi la struttura della tabella, e nel farlo si
perdono le sue preferenze di colonna — che erano il motivo per cui §33.4 ha scelto la
vista nativa. Non si possono avere tutt'e due.

### §39.5 — D133: la finestra dichiarata non è quella servita

**Misurato il 3 agosto 2026 su `ollama` nativo.** Un prompt da circa dodicimila gettoni
è tornato con `prompt_eval_count` a **2050**, e il modello non sapeva più cosa ci fosse
scritto all'inizio. Nessun errore: HTTP 200, una risposta plausibile costruita su ciò
che era rimasto. Il modello regge 262 144 gettoni; il **server** ne serve 4096, e oltre
quella soglia taglia.

**L'adattatore non manda la finestra al fornitore**, e non per distrazione: il
protocollo OpenAI non ha un campo per dirla. Quindi `context_window` è ciò che il
profilo *dichiara*, e con cui **D79** (il budget del catalogo derivato dalla finestra)
dimensiona il catalogo, mentre ciò che il server serve è un'altra cosa che nessuno
guarda. Due numeri che possono divergere in silenzio.

**E il contatore c'era già.** `refused_for_budget` conta gli attributi che il budget
butta via, e non lo leggeva nessuno. Con la finestra di 4096:

    disponibili = 4096 × 0,25 − 600 = 424 gettoni
    budget      = 424 ÷ 24 = 17 attributi per entità

Diciassette, contro il tetto di 60 di **D31**. Questo toglie a **D32** (la strategia a
tre fasi) la proprietà con cui chiude **RC3**, e il registro la riporta testualmente:
*«in Fase C non c'è selezione: la copertura sugli attributi è esatta per costruzione»*.
Con un budget di 17 la selezione c'è, ed è grossa.

**La delibera è che i due numeri stiano vicini.** La traccia diagnostica di **D123**
porta ora, sullo stesso turno, quanto il budget ha buttato e quanto il server dice di
aver letto contro quanto il profilo dichiara. Non risolve la configurazione — alzare
`OLLAMA_CONTEXT_LENGTH` è dell'ambiente, e costa memoria e latenza — ma toglie la
condizione che rendeva il guasto invisibile, che è esattamente ciò per cui D79 esiste.

**Nota d'ordine.** Alzare la finestra dichiarata dal profilo **senza** alzare quella del
server sarebbe peggio di lasciarla com'è: D79 consegnerebbe un catalogo più grande e il
server lo taglierebbe. Le due metà si muovono insieme o non si muovono.

### §39.6 — D134: una prova che va da uno stato a un numero

La regola di §38 — *«una funzione è finita quando esiste una prova che fallisce se
qualcuno la scollega»* — è giusta e non basta. **Sette degli undici scollegamenti
trovati dall'audit sono lo stesso tratto di catena**: fra il piano risolto e lo schermo.
Tutti provati un passo a monte del punto in cui servivano.

La ragione è che nessuna prova guardava il **contenuto** di una risposta. Le prove del
contratto guardano la forma della busta, le pure guardano una funzione alla volta,
quelle Odoo guardano l'esito — `operations`, e quanti record. Nessuna guardava *quali*
record, in *quale* ordine, con *quale* media.

Il banco delle risposte (`nli_core/tests/test_answers.py`) parte da uno stato, percorre
risolutore, esecutore e presentatore veri, e confronta la risposta per intero su dati
che il caso stesso crea. Rimesse a mano le regressioni di D130 e D131, diventa rosso su
quattro casi che oggi nessun'altra prova prendeva.

**Non presume un database vuoto**: ogni caso lavora dietro una condizione su una città
che nessun popolatore produce, come `ai/restart.md` richiede.

**Verifiche dopo §39**: 468 test in zona pura (erano 464), **180 test Odoo** (erano
167), cinque controlli dei confini puliti. Il controllo sintattico di **D24** ha preso
al primo giro un accesso diretto a PostgreSQL che avevo scritto nel banco, ed è la
prova che quel controllo lavora.

### §39.7 — Il difetto che ho introdotto io, e perché la mia prova non l'ha visto

**Messo in servizio, D133 ha rotto ogni turno.** *«Mostrami i lead creati negli ultimi
3 mesi»* rispondeva *«qualcosa non ha funzionato»* in un decimo di secondo, prima ancora
di arrivare al modello.

La causa: `Catalogue.refused_for_budget` **è già un numero**, e io ci avevo messo un
`len()` intorno. Un `TypeError` alla costruzione della traccia.

**E la traccia si costruiva anche a diagnostica spenta.** `trace()` esce subito quando
il raccoglitore è `None`, ma il dizionario che gli si passa è un *argomento*, e Python
valuta gli argomenti prima della chiamata. L'interruttore di D123 non protegge da un
errore nel valore che gli viene passato — solo dal costo di conservarlo.

**Perché la prova non l'ha preso, che è la parte che conta.** Il test girava con la
finestra larga degli altri, dove il budget non scarta niente: `refused_for_budget`
valeva **zero**, e zero è l'unico valore su cui il difetto non scatta — `0 or ()`
diventa una tupla vuota, mentre `49 or ()` resta `49`. La prova asseriva che la chiave
ci fosse, la chiave c'era, e ogni turno vero moriva.

È §38 un giro più stretto. Non codice scollegato: una **prova che esercita il caso in
cui il difetto non si vede**. La regola si allarga di conseguenza — *un contatore si
prova dove conta qualcosa, non dove vale zero* — e il test ora gira con la finestra
stretta di 4096. Rimesso il `len()`, diventa rosso.

**Cosa ha rallentato la diagnosi, e cosa è cambiato.** Il log diceva `AIDA turn 80
failed: TypeError` e nient'altro. `worker._fail` dichiarava che il dettaglio *«resta
nell'eccezione, che la piattaforma registra con la traccia»*: **falso**, perché
l'eccezione la catturiamo noi e non la rilanciamo. Ora si scrive la pila delle chiamate
con `format_tb` — i soli fotogrammi, file e riga — e **mai il messaggio**, che è il
pezzo che potrebbe citare una frase dell'utente. È la distinzione che rende la cosa
compatibile con **D60** (il divieto di frasi e cataloghi nei registri diagnostici).

### §39.8 — I numeri veri, misurati sul database vero dopo la correzione

*«Mostrami i lead creati negli ultimi 3 mesi»*, modello vero, `db`:

    esito        operations        record   39        tempo   101,0 s
    dominio      ['&', ['create_date', '>=', '2026-05-02 22:00:00'],
                       ['create_date', '<',  '2026-08-03 22:00:00']]
    fase C       17 attributi tenuti, **49 rifiutati per budget**
    prompt       3 655 gettoni letti / 4 096 dichiarati

Tre cose che prima non si potevano dire.

**D131 si vede nel dominio.** `2026-05-02 22:00:00` è la mezzanotte di Roma scritta in
UTC. Prima c'era `2026-05-03` e mancavano due ore in testa e in coda.

**Il catalogo perde il 74% di sé.** Diciassette attributi tenuti, quarantanove
scartati. Non è una stima: è il contatore di D79, letto per la prima volta. La
proprietà con cui **D32** chiude **RC3** — *«in fase C non c'è selezione»* — oggi è
falsa di tre quarti.

**E il margine non c'è.** Il prompt occupa 3 655 gettoni degli 4 096 che il server
serve: l'89%. Aggiungere attributi senza alzare la finestra del **server** manderebbe
il prompt oltre la soglia, e lì `ollama` taglia in silenzio — misurato, dodicimila
gettoni mandati e 2 050 letti. Conferma con i numeri la nota d'ordine di §39.5: le due
metà si muovono insieme o non si muovono.

---

## §40 — D135: la domanda su quale data la facciamo noi

Deliberata su delega dell'Architect il 3 agosto 2026. Nasce dal punto 1 degli aperti di
`ai/restart.md`, che era il primo per quanto sblocca.

### §40.1 — Il fallimento, con i numeri

Batteria sul campo del 3 agosto 2026, modello vero e banca dati vera:

    mostrami i lead creati quest'anno              not_understood   145 s
    mostrami gli ordini di vendita di questo mese  not_understood   119 s

Sono le due entità che espongono **più di una data**, cioè le prime due domande che
chiunque farebbe. E *«creati quest'anno»* aveva dato 39 record la mattina dello stesso
giorno: **il modello non è deterministico su questo**, quindi non era una frase da
sistemare, era una strada da togliergli.

La latenza è tutta lì. Senza espressione di tempo: 15-40 s. Con: 84-145 s. Lo stesso
pezzo, non due problemi.

### §40.2 — La causa non era il modello, era il compito

**D110** (la decisione per cui il catalogo dichiara dove si attacca un periodo: una
data se ne espone una sola, l'insieme delle scelte se sono due o più, nulla se non ce
ne sono) mette nel catalogo un campo `time_anchor`. Il prompt lo leggeva così: se
dichiara `choices`, *«answer with a clarification whose options are those dates»*.

Cioè al modello si chiedeva di scrivere lui una domanda con da due a quattro opzioni,
ognuna **completa e applicabile**: un `set_target`, la condizione, il periodo dentro.
È la cosa più difficile di tutto il prompt, ed è la stessa che **D128** (la delibera
per cui le opzioni di una domanda si validano quando la domanda si memorizza) ha già
dovuto sorvegliare, perché quelle opzioni arrivavano rotte — un `within` senza periodo
dietro un'etichetta che diceva *«Filtra per Data creazione»*.

**Il principio era già scritto altrove.** `03` §5.9 dice che chiedere al modello di
scegliere la vista violerebbe C2/P4, perché è una decisione derivabile dalla forma
dello stato. Le opzioni di questa domanda sono derivabili allo stesso modo: sono le
date dell'ancora, una ciascuna, col periodo che il modello ha già collocato bene.

### §40.3 — La regola: è D105 con una data al posto di una categoria

**D105** (la decisione per cui una condizione nominata che il proprio frammento non
nomina è rifiutata al livello 3) confronta due liste: i termini della condizione e le
parole del frammento che l'ha prodotta. §10.3 definisce la provenienza come *il
frammento della frase che ha prodotto questa operazione*, quindi una condizione che il
proprio frammento non nomina **non è stata chiesta**, per definizione del contratto.

Un periodo non nomina mai il proprio campo — si dice *«ordini del mese scorso»*, non
*«ordini con data ordine nel mese scorso»*. Quindi:

> Se l'entità espone due o più date (l'ancora dichiara `choices`) e il frammento che ha
> prodotto la condizione temporale non nomina nessuna di quelle date, **la data l'ha
> scelta il modello e non l'utente**. Livello 3, codice `unanchored_period`.

**Con una data sola non si chiede niente**, ed è la differenza che fa leggere l'ancora
invece del tipo: il tipo dice *questa è una data*, l'ancora dice *questo utente aveva
una scelta*. Sulle entità con una data sola il periodo va lì per costruzione, e una
domanda con una risposta sola non è una domanda.

**Serve un secondo riconoscitore.** `mentions_of` indicizza solo le condizioni nominate
(T5) e di un attributo non sa niente: chiedergli se *«con data di creazione»* nomina
`create_date` avrebbe risposto sempre no, e la regola avrebbe rifiutato **anche** i
periodi che l'utente aveva ancorato da sé. Quindi `names_of` sui nomi (T1), tenuto
separato invece di fondere i due indici: un indice solo farebbe passare a ciascuna
regola i casi dell'altra, che è il guasto di ogni riconoscitore condiviso.

### §40.4 — Il rifiuto propone, e ogni opzione tiene il periodo

`alternatives.for_unanchored` costruisce una lettura per data, sostituendo il `ref`
della condizione e **lasciando dentro il periodo**. Due differenze da **D106** (la
decisione per cui il rifiuto propone letture derivate dal catalogo), e tutt'e due hanno
un motivo:

* **la data che il modello aveva scelto si offre lo stesso.** In D106 la condizione
  rifiutata era inventata, e riproporla sarebbe stato riproporre uno sbaglio. Qui è una
  delle date che l'entità espone davvero, e toglierla metterebbe fuori portata la
  risposta giusta tutte le volte che l'ipotesi era azzeccata;
* **nessuna lettura toglie il periodo.** In D106 la prima opzione è *«senza quel
  filtro»*; qui non può esistere, perché **D111** (la decisione per cui un'espressione
  di tempo non si lascia cadere: se non si colloca, si chiede) lo vieta. La frase il
  periodo lo dice; quello che non dice è dove va.

L'etichetta di ogni opzione è il termine della data, e sceglierla la fonda: cliccare
scrive l'etichetta nella casella e la invia (**D121**, l'unica strada per il clic e per
lo scritto), quindi al secondo giro il frammento è davvero quelle parole e il livello 3
la trova ancorata. **Esegue senza chiamare il modello**, come già fa per le categorie.

**Il tetto delle quattro opzioni** di §4.4 resta. Un'entità con cinque date esposte ne
vede offerte quattro, in ordine stabile: chi non trova la propria la può ancora
nominare scrivendola, e la strada ordinaria risponde.

### §40.5 — Il prezzo, e dove non si paga

L'ancora sta nel catalogo, e il catalogo di un turno che risponde a una domanda non era
costruito affatto (D121). Adesso serve per validare, ma **solo se il turno porta un
periodo**: `contextual.carries_period` guarda i predicati dello stato prima che si
costruisca qualcosa. Un turno senza periodo non paga niente; uno con un periodo paga la
fase C, misurata a **0,249 s** in `00` §32.1 — niente accanto ai 96 secondi del modello,
tutto accanto a un turno che risponde senza chiamarlo.

### §40.6 — Il prompt perde la riga difficile

La riga ora dice di mettere la condizione sulla scelta che la frase nomina, sulla prima
quando non ne nomina nessuna, e **di non scrivere quella domanda**. Un modello lasciato
libero di scriverla comunque rimetterebbe in circolo le opzioni rotte che D128 ha
dovuto imparare a rifiutare.

### §40.7 — Le prove, nella forma che §38 chiede

§38 (*«una funzione è finita quando esiste una prova che fallisce se qualcuno la
scollega»*) qui è verificata, non asserita: staccando `names` e `time_anchor` dalla
chiamata della conduttura, **tre prove su sei diventano rosse** — provato, non dedotto.

Il banco Odoo gira su `res.users`, e non è un dettaglio: `res.partner` espone **una**
sola data (`create_date`), quindi non ha nessuna scelta da offrire e una prova scritta
lì sarebbe passata senza esercitare niente. `res.users` ne espone due — creazione e
ultimo accesso — ed è installata ovunque, quindi il banco non dipende da un modulo
applicativo. La prima prova della classe **asserisce che l'ancora dichiari `choices`**,
perché nessun controllo può passare a vuoto.

E la coppia che la regola richiede c'è: una prova che la mostra **scattare** (il
periodo che non nomina la data diventa una domanda) e una che la mostra **non
scattare** (*«con data di creazione di quest'anno»* riceve una risposta, perché la
scelta l'ha fatta l'utente e richiedergliela sarebbe non averlo ascoltato).

**Verifiche dopo §40**: 487 test in zona pura (erano 468), **186 test Odoo** (erano
180), cinque controlli dei confini puliti, contratto e corpus 918/918.

### §40.8 — Cosa questa delibera non fa

**Non è stata misurata sul campo.** Il numero che conta — la stessa batteria di frasi
sulle stesse entità, col modello vero — non c'è ancora, e finché non c'è questa sezione
descrive un meccanismo, non un miglioramento. L'attesa scritta prima di misurare, così
che una previsione sbagliata si veda: *«creati quest'anno»* e *«ordini di questo mese»*
finiscono in una domanda con due-quattro date invece che in `not_understood`, e la
risposta al clic arriva in un decimo di secondo invece che in due minuti.

**Non tocca il ramo dell'ancora nulla.** Un'entità che non espone nessuna data resta il
punto 11 degli aperti: il prompt chiede un chiarimento e un chiarimento vuole almeno
due opzioni con un'operazione ciascuna, che lì non esistono. Serve una delibera a parte.

**E resta dipendente dal dizionario.** La regola misura se il frammento nomina la data
con i termini che il dizionario ha (T1). Una data i cui termini non contengono la parola
che l'utente usa davvero — *«creati»* per `create_date` — produrrà una domanda che
l'utente troverà inutile, perché la data l'aveva già detta. Non è un difetto della
regola: è **materiale prezioso** nel senso di §12.4, cioè una voce mancante che si
aggiunge con **D108** (il registro delle voci di dizionario approvate). Da guardare
alla prossima batteria, perché è l'unico modo in cui questa delibera può peggiorare le
cose invece di migliorarle.

---

## §41 — Il primo turno vero di D135, e i tre difetti che ha scoperto (D136–D138)

Il 3 agosto 2026, subito dopo §40, l'Architect ha scritto *«mostrami i lead di
quest'anno»* sull'installazione vera. **La domanda è arrivata**: quattro date —
creazione, chiusura, conversione, chiusura attesa — costruite dall'ancora, e il clic su
*«Data creazione»* ha eseguito senza chiamare il modello. D135 fa quello che dice.

**La risposta è stata «nessun record trovato».** Il turno numero 87 sul database `db`,
letto per intero, dice perché — e sono tre cose diverse, non una.

### §41.1 — Cosa è successo, nell'ordine

Il modello ha tradotto *«di quest'anno»* con **`after`**, non con `within`:

    condizione   crm_lead.create_date  after  current_year
    dominio      ['create_date', '>=', '2026-12-31 23:00:00']
    record       0

`after` su un periodo prende **il lato destro** della finestra, cioè *dopo la fine del
2026*: una data futura, e quindi nessun record. Il risolutore ha fatto la cosa giusta
con uno stato sbagliato.

D135 ha portato avanti il predicato fedelmente, ed è il comportamento voluto: le opzioni
spostano **la data**, non toccano il resto della frase. Un'opzione che avesse anche
corretto il predicato avrebbe corretto il modello di nascosto.

### §41.2 — D136: l'interpretazione mostrava una finestra che nessuno aveva interrogato

Questo è il difetto peggiore dei tre, ed è nostro.

Sopra la risposta, l'interpretazione diceva:

    crm_lead.create_date:  2026-01-01 - 2026-12-31

cioè **l'anno intero**, mentre l'insieme interrogato era *dopo il 31 dicembre*. Il
motivo: `calendar.describe` riceveva l'espressione e l'istante, e **non il predicato**,
quindi descriveva la finestra di `current_year` qualunque cosa il dominio ne facesse.

L'utente leggeva l'anno intero e riceveva zero record, senza nessun modo di capire
perché. **L'interpretazione esiste per rendere una risposta verificabile** (§10): questa
la rendeva inspiegabile. È la forma di **D2** (il cancello che vieta le scritture finché
la Fase 2 non è misurata e superata) con un'aggravante — non solo una risposta sbagliata
con l'aria di essere giusta, ma il pezzo che avrebbe dovuto smascherarla che la copriva.

Ora il predicato entra nella descrizione: `> 2026-12-31` per `after`, `< 2026-01-01` per
`before`, la finestra per `on` e `within`. La forma resta simbolica e non tradotta,
perché la zona è pura e non ha lingua — ed era già così.

### §41.3 — D137: chi sceglie un'opzione ripartiva dallo stato che la domanda aveva buttato via

Nello stesso turno, l'ordinamento portava **due** voci: una sulla data, e una su
`automated_probability` con provenienza vuota. Veniva dal turno 85, *«mostrami i lead
più promettenti»*, due domande prima.

Il meccanismo: la frase *«mostrami i lead di quest'anno»* nomina il proprio soggetto,
quindi **D127** (chi nomina la propria entità ricomincia) l'aveva dichiarata domanda
nuova e aveva buttato via lo stato. Ma quel turno è finito in una domanda, e **un turno
che chiede non scrive stato** — quindi il vecchio era ancora lì, e le operazioni
dell'opzione ci sono finite sopra.

Qui è costato un ordinamento di troppo. Il caso che conta è un altro: se il turno di
prima filtrava per una città, la risposta alla domanda esce **ristretta a quella
città**, senza che niente lo dica.

**La regola non è nuova, è D127 applicata dove non arrivava.** Un'opzione che si porta
il proprio `set_target` è una richiesta intera — **D106** le costruisce da una — quindi
riparte. Una che non ce l'ha è un raffinamento e continua sullo stato che c'è: è la
stessa distinzione che `alternatives.chosen` fa già, pretendendo che l'entità sia nota
quando l'opzione non porta un bersaglio.

Non c'è nessun contrasto con **D120** (chi risponde a una domanda non riparte da zero):
D120 tiene viva la domanda in sospeso, che senza di lei sparirebbe nel punto in cui
serve di più. Quello che riparte è lo **stato dei dati**, e riparte perché l'opzione lo
ricostruisce tutto.

### §41.4 — D138: un periodo si prende intero, salvo che la frase dica altro

Il prompt non diceva niente sul predicato di un'espressione di tempo, e `after` costa
zero da scrivere quanto `within`. Ora lo dice: **il predicato di un periodo è `within`**;
`before` e `after` si guadagnano con delle parole — *«prima di»*, *«dopo»*, *«entro»* —
e prendono un lato della finestra, non la finestra.

È la stessa forma di **D118** (il rifiuto si guadagna) e di **D113** (su una data
l'intervallo si dice `within`, e basta): una via d'uscita che si apriva da sola perché
nessuna riga la chiudeva.

**Non è una garanzia.** Il prompt è una richiesta, non un vincolo: se il modello scrive
`after` lo stesso, la catena lo esegue e D136 lo **mostra**. Le due cose lavorano su
piani diversi, ed è il motivo per cui servono tutte e due.

### §41.5 — Le prove

* D136: due prove pure su `describe`, una per lato, più quella che mostra `on` e
  `within` invariati.
* D137: una prova Odoo che fa tre turni — una condizione eseguita, una domanda nuova che
  finisce in chiarimento, la scelta — e verifica che **la condizione del primo turno non
  sopravviva**. Diventa rossa se qualcuno rimette lo stato vecchio sotto le operazioni
  dell'opzione.
* D138: la riga del prompt è asserita nel test che già sorveglia le istruzioni sul tempo.

**Verifiche dopo §41**: 489 test in zona pura, 187 test Odoo, cinque controlli dei
confini puliti, contratto e corpus 918/918.

### §41.6 — Quello che questo turno insegna su §40

D135 ha funzionato al primo colpo e **ha reso visibili tre difetti che stavano sotto**.
Non è un caso: finché la domanda finiva in `not_understood` dopo due minuti, nessuno di
questi tre poteva nemmeno essere osservato. È l'argomento di §5 dell'audit (`ai/17`) da
un'altra direzione — non «una prova che va dalla frase al numero», ma **un turno che
arriva in fondo** — e vale la pena ricordarlo la prossima volta che una correzione
sembra non aver migliorato niente.

---

## §42 — Il banco delle capacità, e la prova che passava a vuoto

Richiesto dall'Architect il 3 agosto 2026: *«fai un test per tutte le operazioni
espresse nel controllo-architettura, tranne per le join. Devo poter effettuare
attraverso i predicati umani, tutte le operazioni»*.

`nli_core/tests/test_capabilities.py`, **60 prove** su quattro classi. `ai/17` §3 aveva
risposto **a tavolino** quali operazioni di `16` esistono e quali no; questo banco
risponde **eseguendole**.

### §42.1 — Cosa copre

| classe | prove | cosa |
|---|---|---|
| `TestGliIntenti` | 18 | SELECT, colonne, SEARCH, FILTER, COUNT, SUM, AVG, MIN, MAX, DISTINCT, GROUP BY (semplice, multiplo, con misura), ORDER BY (semplice, multiplo), LIMIT, PAGINATION, EXISTS, NOT EXISTS |
| `TestGliOperatori` | 15 | `=`, `>`, `<`, `>=`, `<=`, BETWEEN, CONTAINS/LIKE, ILIKE, STARTS WITH, IN, NOT IN, IS NULL, IS NOT NULL, vero/falso, i connettivi *e*/*o* |
| `TestLeDate` | 18 | oggi, ieri, domani, questa settimana, settimana scorsa, questo mese, mese scorso, ultimi 7/30/90 giorni, quest'anno, anno scorso, questo trimestre, trimestre scorso, da inizio anno, una data precisa, un intervallo preciso, `before`/`after` |
| `TestQuelloCheNonSiPuoDire` | 9 | HAVING, OFFSET, EXPORT, `!=`, ENDS WITH, la negazione, i trimestri e i mesi nominati, le aggregazioni annidate, i join |

**Ogni prova porta nel proprio nome la frase italiana** che rappresenta, perché è quello
il metro: non *«il contratto ammette `starts_with`»* ma *«i partner che iniziano per
Del»* restituisce **Delta e nessun altro**.

**L'ultima classe conta quanto le altre.** Un buco che nessuno misura torna a farsi
credere una svista. La prima volta che qualcuno scriverà `HAVING` in una specifica,
serve poter dire *«è fuori portata per costruzione, ecco la riga che lo dice»* invece di
*«mi pare di no»*. Ognuna di quelle nove è provata sul vocabolario, che è l'unico posto
dove una cosa che **non** esiste si può asserire.

**I join sono fuori per scelta dell'Architect**, e il banco lo dichiara invece di
tacerlo: nessun riferimento del catalogo attraversa una relazione (reperto R5), la
relazione si prende solo come un tutto — `is_set`, `is_not_set` — ed è provato.

### §42.2 — Il banco non chiama il modello, e va detto

Parte dallo **stato**, non dalla frase, e percorre risolutore, esecutore e presentatore
veri. Che il modello traduca *«i primi 10 per fatturato»* in quello stato è un'altra
domanda e ha un altro strumento: la misura di accuratezza sul corpus. Mescolarle
renderebbe il banco non deterministico — il modello sbaglia a caso, e una prova che
sbaglia a caso non è una prova.

Quindi qui si legge: **dato che la frase è stata capita, il prodotto sa rispondere?**

### §42.3 — `create_date` non è scrivibile, e una prova ci era appoggiata sopra

Scrivendo le date del banco è venuto fuori che **Odoo 18 non lascia scrivere
`create_date`**: né in `create` né in `write`. Provato in una sessione di shell — il
valore passato viene ignorato e il record prende l'ora corrente. Su `res.partner` non
c'è nessun altro campo data memorizzato e scrivibile.

**La conseguenza sta in `test_answers.py`.** Il caso del fuso orario (D131) creava un
partner *«dell'una di notte»* passando `create_date`, e poi verificava di trovarlo con
*«creati oggi»*. Il partner prendeva invece l'ora in cui la prova girava, cioè *adesso*,
e *«creati oggi»* lo trovava **sempre**: verde qualunque cosa facesse la conversione. E
dal giorno dopo sarebbe diventato rosso senza che nulla si rompesse, perché l'istante
del banco è fisso al 3 agosto e *adesso* non lo è.

Una riga che non distingue niente è peggio di una riga che manca. È **§39.7 un giro più
stretto** — *un contatore si prova dove conta qualcosa, non dove vale zero* — e la
stessa regola in versione generale: **una prova si scrive dove il difetto si vede**. Per
la conversione del fuso quel posto è il **dominio**, e non serve nessun record: ora si
asserisce che gli estremi siano `2026-08-02 22:00:00` e `2026-08-03 22:00:00`, cioè la
mezzanotte di Roma scritta in UTC da tutt'e due i lati. Se le due ore mancano, cade.

L'altra metà — le date su righe vere — sta nel banco nuovo, su un'entità che una data
scrivibile ce l'ha: i **cambi di valuta**, dove il giorno è un campo proprio
(`res.currency.rate.name`), su una valuta inventata dal banco che non dà fastidio a
nessuno. È un `date` puro, senza ore: il fuso vive su un `datetime` e resta dove è
provato.

**Verifiche dopo §42**: 489 test in zona pura, **247 test Odoo** (erano 187), cinque
controlli dei confini puliti, contratto e corpus 918/918.

### §42.4 — Cosa il banco dice del prodotto

Tutto quello che `16` chiede **e che esiste, esiste davvero**: 51 prove verdi che
eseguono, non che ispezionano. Le nove che restano dichiarano i buchi con precisione, e
sono la stessa lista di `ai/17` §3 — con la differenza che adesso è verificata a ogni
giro invece che scritta una volta.

---

## §43 — La batteria sul campo: le stesse operazioni, dette da una persona

Richiesta dall'Architect il 3 agosto 2026, subito dopo §42: *«ovviamente Intenti,
Operatori tutto mappato in richieste prompt da chat»*.

`tools/campo/frasi.py` porta **54 frasi** italiane — le stesse operazioni di `ai/16` del
banco delle capacità, dette come le direbbe qualcuno in chat — e `tools/campo/batteria.py`
le esegue attraverso il prodotto vero. Si lancia con `./manage.sh campo <db> [famiglia]`.

### §43.1 — Perché è uno strumento e non una prova

Il banco di §42 è deterministico: parte da uno stato, gira in un secondo, sta nella
suite. Questa batteria parte da una **frase** e passa dal modello, che non è
deterministico — la stessa frase, il 3 agosto, ha dato 39 record la mattina e
`not_understood` il pomeriggio.

Quindi è fuori da `check` e da `test`, di proposito: una suite che dipendesse dal modello
direbbe cose diverse a ogni giro, e chi la guarda smetterebbe di crederle. È una
**misura**, e il risultato di un giro è una fotografia da confrontare con altri giri.

Le due cose insieme rispondono a due domande diverse, ed è per questo che sono due:

* il banco — *il prodotto **sa fare** questa operazione?*
* la batteria — *una persona riesce a **chiederla**?*

### §43.2 — Le attese non nominano i riferimenti

Un'attesa dice *«deve uscirne una misura di conteggio e un raggruppamento»*, mai
*«`crm_lead.stage_id`»*. I riferimenti dipendono dall'installazione, e una batteria che
li fissasse misurerebbe questa banca dati invece del prodotto.

### §43.3 — I saltati, che sono la parte che insegna di più

Ogni frase dichiara le parole che il catalogo deve contenere perché sia rispondibile. Se
mancano, il caso è **saltato** invece che contato come sbagliato. Addossare al modello un
attributo che nessuno gli ha mostrato falserebbe la misura nella direzione peggiore:
quella che fa lavorare sul pezzo giusto per il motivo sbagliato.

**E al primo giro ha parlato subito.** Con la finestra a 4096, il catalogo di `crm.lead`
tiene **17 attributi e ne rifiuta 49**, e quelli tenuti sono:

    attivo, azienda, campagna, chiusura attesa, città, data assegnazione,
    data chiusura, data conversione, data creazione, e-mail, e-mail in cc,
    giorni da assegnare, giorni per chiudere, nazione, nome contatto,
    probabilità automatica, qualità e-mail

Non ci sono **lo stato, il ricavo atteso, il commerciale, il telefono**. Cioè: metà delle
domande che una persona farebbe per prime non è *sbagliata*, è **non rispondibile** — il
modello non ha mai visto quegli attributi.

Questo conferma con l'elenco alla mano ciò che **D133** (la finestra dichiarata non è
quella servita) aveva calcolato con l'aritmetica, e chiude il punto: **la batteria intera
va eseguita dopo aver alzato la finestra**, non prima. Prima misurerebbe il taglio.

### §43.4 — Prova di funzionamento

Tre frasi, per verificare lo strumento e non il prodotto:

    mostrami i lead                          ok       37,7 s   39 record
    mostrami i lead con nome e telefono      saltato           (telefono non esposto)
    cerca i lead che hanno milano nel nome   ok       67,0 s    0 record

### §43.5 — Cosa la batteria non tocca

Non scrive niente: la transazione viene annullata al termine, salvo `CAMPO_SCRIVI=1`. Una
misura non deve lasciare cinquanta turni in una banca dati di lavoro.

E percorre la strada del prodotto senza copiarla: perimetro, finestra e adattatore
vengono dai metodi del **dispatcher**, gli stessi che il cron chiama; ogni frase entra da
`accept`, che è l'unica porta d'ingresso. Non passa dal pool di thread — quello è un
fatto di concorrenza, provato da D27, e qui darebbe solo rumore.

---

## §44 — D139: il limite non arrivava alla tabella, e la chiave non esisteva

Visto sul campo il 3 agosto 2026. *«I primi 5 lead ordinati per data di creazione»*: il
piano diceva `limit 5`, il server leggeva cinque record — e la tabella ne mostrava
**trentanove**.

### §44.1 — La causa, in una parola

Il limite viaggiava verso la vista come `list_view_limit` **nel contesto**. Quella chiave
**non esiste in Odoo 18**: zero occorrenze in tutto `web/static/src`. Nessuno la leggeva,
e la lista teneva il proprio valore predefinito.

La chiave vera è una **proprietà**, non una voce di contesto:

    list_controller.js:225   limit: this.archInfo.limit || this.props.limit

### §44.2 — È R2 per la seconda volta, nello stesso componente

Il reperto R2 dell'audit diceva: *«`order` e `fields` sono ignorati»*, e **D132** ha
passato l'ordinamento come proprietà. Il limite è rimasto dov'era, e per la stessa
ragione per cui c'era finito: **una chiave passata a chi non la legge non fallisce**. Non
c'è errore, non c'è avviso, non c'è prova rossa. C'è una tabella che mostra il numero
sbagliato di righe sotto un'interpretazione che dichiara il numero giusto.

E la ragione per cui torna è sempre la stessa, ed è il punto 3 degli aperti: **dal lato
client non esiste nessuna prova**.

### §44.3 — Il controllo che la prende senza far girare niente

Uno statico non sostituisce le prove che mancano, ma questa classe di guasto è
verificabile leggendo: *questa parola, Odoo la conosce?*

`tools/arch/check_owl.py` ha ora una seconda regola. Confronta le chiavi che i nostri
componenti mettono in un `context: { ... }` con tutto il sorgente JavaScript di
`web/static/src`; una parola che lì non compare mai non la legge nessuno.

**Al primo giro ha trovato altre cinque chiavi morte**, e sono più interessanti del
limite: `create`, `edit`, `delete`, `duplicate` e `import_enabled`. Erano lì per **D2**
(nessuna scrittura sui dati finché la Fase 2 non è misurata e superata), con un commento
che diceva *«la vista lo legge dal contesto, e senza, «Nuovo» ricompare»*. **Falso in
Odoo 18**, verificato in tre punti: `getActiveActions` legge dagli attributi dell'arch;
il server li abbassa da sé secondo i diritti (`ir_ui_view._postprocess_access_rights`);
e nel client non c'è nessuna lettura di `context.create`. `import_enabled` non compare
nemmeno una volta in tutto il sorgente di Odoo.

Cioè: **cinque parole che sembravano una garanzia e non lo erano**. Toglierle non toglie
niente, perché non davano niente. Ciò che tiene in piedi D2 è altrove ed è più solido —
il pannello di controllo spento (i pulsanti non esistono), `editable: false` che è una
proprietà vera, e soprattutto una catena che non scrive mai, che è architettura e non un
suggerimento all'interfaccia.

**Un controllo che passa perché non ha guardato è peggio di un controllo che manca**:
senza il sorgente di Odoo la regola tace invece di dichiararsi verde. E i commenti si
tolgono prima di cercare le chiavi — al primo giro segnalava una voce chiamata `D2`,
presa da una nota, e un controllo che segnala le proprie note è un controllo che si
impara a ignorare.

### §44.4 — Il limite dichiarato di questo controllo

Prende le parole **distintive**: `list_view_limit`, `import_enabled`. Non può prendere
`create` o `edit`, che nel sorgente di Odoo compaiono ovunque per altre ragioni — quelle
sono state trovate a mano, seguendo la stessa domanda. E non dice il contrario: una
chiave che *esiste* può essere passata nel posto sbagliato, e il controllo non se ne
accorge.

Resta che le due chiavi morte che hanno prodotto un difetto visibile sarebbero state
prese tutte e due, prima di arrivare sullo schermo.

**Verifiche dopo §44**: 489 test in zona pura, 247 test Odoo, **51 test dei confini**
(erano 47), cinque controlli puliti, contratto e corpus 918/918.

### §44.5 — D140: la frase di D68 era calcolata e nessuno la mostrava

Stesso turno, riga sopra la tabella: **«39 record trovati»** con cinque righe sotto.

Il numero è giusto — è il totale, e l'Esecutore lo conta prima di recuperare. Ma è
**metà della frase**, e l'altra metà esiste da sempre: `Result.describe()` produce
*«i primi 5 di 39»*, il Presentatore la mette in `interpretation.records`, il payload la
porta al client. **Nessuno la disegna.** La chat scriveva il totale e basta.

Ed è il motivo per cui **D68** esiste, scritto nella delibera: *«ottanta record senza
contesto si leggono come **tutti quanti**. È un fraintendimento plausibile prodotto
dall'interfaccia, non dal modello»*. La riga faceva esattamente quello.

**Terza volta in un turno solo**, e sempre la stessa forma: il limite che non arrivava
alla vista (§44), le cinque chiavi inerti (§44.3), e ora una frase calcolata sul server e
mai disegnata. Tutte fra il piano e lo schermo, tutte nel pezzo che **non ha prove**.

**La correzione sta dove c'è la lingua.** Il client ha già i due numeri — `record_count`
è il totale, `query.limit` quante righe si leggono — e se il primo supera il secondo la
risposta è troncata: lo stesso conto di `Result.truncated`, fatto dove si può scrivere in
italiano. Sopra la tabella ora c'è *«I primi 5 di 39 record.»*

**Le prove.** Due, sul lato Python, e dichiarano cosa non coprono: che la query porti il
limite (senza, la tabella non sa quante righe mostrare **e** la frase non si può
comporre) e che il payload porti totale e limite **insieme** — con uno solo dei due la
chat può solo dire *«39 record trovati»* sopra cinque righe, che è vero e fuorviante.
Il banco di componente OWL resta il punto 3 degli aperti.

**Verifiche dopo §44.5**: 489 test in zona pura, **249 test Odoo**, 51 test dei confini,
cinque controlli puliti.

---

## §45 — La finestra alzata, e cosa rende di nuovo misurabile

4 agosto 2026. Eseguito il punto 1 degli aperti, cioè la nota d'ordine di **D133** (la
finestra dichiarata non è quella servita): le due metà si muovono insieme o non si
muovono.

    server   OLLAMA_CONTEXT_LENGTH=8192   (launchctl setenv + riavvio dell'applicazione)
    profilo  context_window = 8192        (il profilo in servizio, su `db`)

**Verificato su tutti e due i lati**, che è la parte che conta:

* il server legge **4 061 gettoni** di un prompt da 4 077 senza specificare nulla nella
  richiesta. Prima, con dodicimila gettoni mandati, ne leggeva 2 050 e tagliava in
  silenzio;
* il catalogo di `crm.lead` tiene ora **60 attributi su 66** — il tetto di **D31** — con
  **sei** rifiuti per budget invece di quarantanove.

Il catalogo passa dal 26% al 91% di sé stesso.

### §45.1 — Cosa questo invalida

Tutto ciò che è stato misurato prima di oggi è stato misurato attraverso un catalogo
tagliato a un quarto, e **va rifatto**: il 70,0% di accuratezza, le frasi saltate della
batteria sul campo, e il banco dei tre candidati di `ai/19` §2.

Non è una perdita: è la ragione per cui la nota d'ordine di §39.5 diceva di alzare la
finestra **prima** di qualunque misura. Il costo di averla ignorata sarebbe stato
scoprire fra un mese che stavamo ottimizzando il pezzo giusto per il motivo sbagliato.

### §45.2 — Il prompt cresce, ed è previsto

Con 60 attributi il prompt di `crm.lead` passa da 11 057 a **14 763 caratteri**, cioè da
3 655 a **4 077 gettoni**: metà della finestra, con metà di margine. È dentro il conto di
**D79** (il budget del catalogo derivato dalla finestra) per costruzione — un quarto
della finestra per il catalogo — e lascia spazio alla risposta.

`ai/19` misura quanto costa in tempo: leggere quei 4 077 gettoni sono 17 secondi sul 9b
e 3,7 sul 2b, e sono la ragione vera dei tempi di risposta di oggi.

---

## §46 — D141: i periodi nominati entrano nel vocabolario

6 agosto 2026. È il punto P0 di `restart.md`, e la sonda che segue dice che era il punto
giusto.

### §46.1 — Cosa fa oggi il prodotto

Sei frasi, sul database `db`, col modello vero, `context` 8192 su tutti e due i lati.
Ogni riga è il periodo che Odoo ha **davvero** interrogato:

| la frase | il periodo interrogato | l'esito |
|---|---|---|
| *«i lead creati nel primo trimestre»* | 1 lug – 30 set | il **terzo** trimestre, 26 record |
| *«i lead creati a gennaio»* | 1 – 31 ago | **agosto**, 0 record |
| *«i lead creati nel 2025»* | tutto il **2026** | 39 record |
| *«i lead creati a marzo 2026»* | 1 – 31 ago | **agosto**, 0 record |
| *«i lead creati nel secondo semestre»* | — | `not_understood` |
| *«i lead creati questo trimestre»* | 1 lug – 30 set | giusto |

**Quattro risposte sbagliate su sei, e nessuna lo dichiara.** È la forma di guasto che
**D2** (il cancello che vieta qualunque scrittura sui dati finché la Fase 2 non è
misurata e superata) esiste per tenere fuori: non un errore, un numero plausibile e
sbagliato. Chi legge *«26 record»* non ha modo di sapere che ha davanti il terzo
trimestre.

*«A marzo 2026»* è la peggiore delle quattro, perché l'utente aveva detto **anche
l'anno**: nessuna ambiguità da risolvere, e il prodotto ha risposto agosto.

### §46.2 — La causa, e non è il modello

Il vocabolario temporale (§9.2) ha `current_quarter` e `previous_quarter`, che dicono
*«questo»* e *«scorso»*. Non ha modo di dire *«il primo»*. Non ha i mesi nominati né gli
anni nominati. L'unico mattone che li direbbe è `absolute_range`, che vuole i due
estremi — e il prompt vieta al modello di calcolarli (*«never resolve a date»*).

**È la contraddizione che `ai/17` §3 aveva già trovato e lasciato da deliberare**: o
entrano le espressioni nominate, o la regola del prompt fa un'eccezione dichiarata. La
prova pura `test_capabilities.test_i_trimestri_nominati_e_i_mesi_nominati_non_esistono`
la teneva scritta e verde.

Messo davanti a una cosa che non può dire, il modello dice quella di forma più vicina:
`current_month` per *«gennaio»*, `current_quarter` per *«il primo trimestre»*,
`current_year` per *«nel 2025»*. Non è una caduta del modello, è un vocabolario che non
contiene la parola.

### §46.3 — La decisione

**D141 — i periodi nominati sono simboli del contratto.** Entrano tre espressioni:

| espressione | parametri | dice |
|---|---|---|
| `month_of_year` | `n` 1–12, `year` facoltativo | *«a gennaio»*, *«a marzo 2026»* |
| `quarter_of_year` | `n` 1–4, `year` facoltativo | *«nel primo trimestre»*, *«nel Q1 2025»* |
| `year_of` | `n` l'anno, quattro cifre | *«nel 2025»* |

**Perché non l'eccezione al prompt.** Risolvere una data non è un calcolo che si fa a
mente: dipende dal fuso dell'utente, dal primo giorno della settimana e dall'inizio
dell'esercizio fiscale — i tre parametri d'installazione di §9.2, che il modello non
conosce e non deve conoscere. Un modello che scrive `2026-01-01` sta indovinando che
l'anno dell'azienda cominci a gennaio. Con `month_of_year(1)` il modello dice **quale
mese**, che è ciò che ha capito dalla frase, e chi conosce i parametri calcola. La
divisione del lavoro resta quella di tutto il resto del sistema.

**L'anno che la frase non dice è l'anno fiscale corrente.** *«A gennaio»* detto oggi è
gennaio dell'esercizio in corso, come `current_year` e `year_to_date` (**D91**). In
un'azienda il cui esercizio parte a luglio, *«il primo trimestre»* è luglio–settembre:
è ciò che intende chi ci lavora, ed è l'unica scelta coerente con le espressioni che
già ci sono. Resta **simbolico** come tutto il resto (§9.2): la stessa domanda salvata
e rieseguita l'anno prossimo risponde per l'anno prossimo.

**L'ambiguità che resta è dichiarata, non nascosta.** *«A gennaio»* detto a dicembre può
voler dire il gennaio passato o quello che viene; la regola sceglie l'esercizio in
corso, sempre, e l'interpretazione mostra gli estremi risolti (**D67**, **D136**), quindi
chi legge vede *«2026-01-01 – 2026-01-31»* e può correggere. Una regola prevedibile che
si vede è meglio di una regola intelligente che indovina.

### §46.4 — Cosa questo **non** copre, e perché va bene

*«Nel secondo semestre»* resta fuori: i semestri non entrano, perché nessuna misura li
ha mai chiesti e §3.9 aggiunge espressività quando i dati la chiedono. Oggi quella frase
risponde `not_understood`, che è il comportamento giusto — un rifiuto, non un numero
sbagliato.

**La rete contro il ripiego silenzioso non è in questa decisione.** Si potrebbe
pretendere che l'espressione scelta dal modello sia *fondata* nel frammento — **D105**
applicato al valore invece che al riferimento — e rifiutare o riparare quando il
frammento nomina un periodo che l'espressione non è. Serve un lessico deterministico dei
mesi e dei trimestri, cioè lingua nel codice, subito dopo che i pacchetti lingua l'hanno
tolta di mezzo. **Si misura prima**: il ripiego di oggi nasce dalla parola che manca, e
se D141 la mette a disposizione il ripiego non ha più ragione di esistere. Se dopo la
misura resta, la rete si delibera con i numeri in mano.

### §46.5 — Il rischio che D141 introduce

Un mattone nuovo si può usare male: il modello potrebbe scrivere `month_of_year(8)` dove
la frase dice *«questo mese»*, che oggi è giusto e diventerebbe sbagliato al primo
settembre. È la ragione per cui la sonda delle sei frasi si rifà **dopo**, insieme alle
frasi che oggi funzionano — una misura che guarda solo i casi riparati non è una misura.

### §46.6 — La misura dopo, e la riga di prompt che spostava tutto

Stesse sei frasi, stesso database, `context` 8192, **tre giri per cella** dove il
risultato contava:

| la frase | prima | dopo |
|---|---|---|
| *«nel primo trimestre»* | 1 lug – 30 set (26 rec) | **1 gen – 31 mar**, 3/3 |
| *«a gennaio»* | 1 – 31 ago | **1 – 31 gen**, 3/3 |
| *«nel 2025»* | tutto il 2026 | **tutto il 2025**, 3/3 |
| *«a marzo 2026»* | 1 – 31 ago | **1 – 31 mar 2026**, 3/3 |
| *«questo trimestre»* | 1 lug – 30 set (giusto) | **invariato**, 3/3 |
| *«nel secondo semestre»* | `not_understood` | `not_understood` |

**Quattro risposte sbagliate diventano quattro risposte giuste, e nessuna di quelle
che funzionavano si è mossa.** I tempi sono 5–7 secondi a turno.

**Ma la prima stesura della riga di prompt ha rotto qualcos'altro, e la prova
controfattuale è il pezzo che vale.** Con quella riga, *«i lead creati questo
trimestre»* — che rispondeva 26 record — ha cominciato a chiedere *«quale data
intendi?»*, 3 giri su 3: il modello metteva il periodo su `date_open` invece che su
`create_date`. Rimesso il prompt vecchio e rimisurato: 3/3 su `create_date`. **Non era
il modello, era il prompt**, esattamente come impone di verificare la regola di lavoro
nata da §18.

La causa: la riga stava fra la regola *«never resolve a date»* e la regola dell'ancora
del tempo, e nominava *«questo»*, *«corrente»*, *«in corso»* — cioè parlava anche di
**dove** va la condizione, dentro una regola che doveva parlare solo di **quale**
periodo. Spostata dopo la regola dell'ancora, tolta ogni parola sull'attributo e
aggiunta la frase *«this chooses WHICH period, never which attribute carries it»*:
tutte e tre le celle tornano giuste.

**Lezione, oltre al caso:** una riga aggiunta a un prompt non aggiunge soltanto. Un
prompt è un testo che il modello legge intero, e una regola nuova compete con quelle
vicine. Un'aggiunta al prompt si misura **anche sulle frasi che già funzionavano**.

### §46.7 — Il semestre: il rischio di §46.5, misurato il giorno stesso

*«Nel secondo semestre»* era `not_understood` prima di D141 — un rifiuto onesto. Appena
il modello ha avuto `quarter_of_year`, l'ha risposta con il **secondo trimestre**: tre
mesi dei dati sbagliati, 3 giri su 3. È il rischio scritto in §46.5 due ore prima,
verificatosi subito: **un mattone nuovo si usa anche dove non va**.

Una riga di prompt che lo vietava per nome (*«un periodo che nessuna espressione sa
dire è un chiarimento, mai il più vicino»*) **non ha retto**: 3/3 ancora sul trimestre.

Quindi `half_of_year` entra nel vocabolario, con `n` fra 1 e 2 e un semestre che è due
trimestri esatti — proprietà provata, perché due simboli che descrivono lo stesso
periodo e divergono darebbero due risposte diverse alla stessa domanda detta in due
modi. Dopo: *«nel secondo semestre»* torna `not_understood`, cioè al comportamento
onesto di partenza. Il modello non usa ancora il simbolo nuovo su quella frase, e non è
un difetto da inseguire oggi: è un rifiuto, non un numero sbagliato.

**Cosa resta aperto, e va deliberato con questi numeri in mano.** Bimestri,
quadrimestri, decenni: la stessa forma. Aggiungere simboli finché non ne mancano più
non è una strategia — il ripiego silenzioso è la classe di guasto, e la classe si
chiude con una **rete**, non con un elenco. La rete è quella descritta in §46.4:
pretendere che l'espressione scelta sia fondata nel frammento, **D105** applicato al
valore. Serve un lessico dei periodi, cioè lingua, e va messa dove sta la lingua di
questo prodotto — il dizionario e i suoi livelli (**D108**), non il sorgente. Costo e
forma da valutare; l'argomento per farlo ora c'è, ed è questo paragrafo.

### §46.8 — Le verifiche

* **534 test in zona pura** (erano 516): il risolutore dei quattro periodi nominati,
  l'anno fiscale, il semestre uguale a due trimestri, gli intervalli dei parametri al
  livello 2, e la prova che il prompt **mostra la forma** di ogni periodo nominato —
  quella che fallisce se qualcuno lo scollega (§38).
* **258 test Odoo**, `check` verde, corpus 918/918, copertura 100%.
* Schemi JSON rigenerati da `tools/dsl/emit_schema.py`: il contratto resta la fonte.
* La batteria sul campo ha ora sei frasi nuove nella famiglia `date`, e l'attesa dice
  **quale** periodo: un'attesa che si accontentasse di *«c'è un periodo»* avrebbe
  contato giuste tutte e quattro le risposte sbagliate di §46.1.
