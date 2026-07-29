# Piano di Implementazione
## AIDA — dalla progettazione al codice

---

| Voce | Valore |
|---|---|
| **Titolo** | Piano di Implementazione — sequenza delle parti, criteri di completamento |
| **Tipo** | Documento operativo — vive fino al completamento della Fase 1 |
| **Versione** | 1.0 |
| **Data** | 27 luglio 2026 |
| **Prodotto** | **AIDA** (D6). Prefisso tecnico dei moduli: `nli_` |
| **Presuppone** | `00-registro-decisioni.md` — 85 decisioni adottate, 1 aperta (**D7**) |
| **Stato del progetto** | Progettazione chiusa. Fase 0 completa salvo ciò che dipende da D7 |

> **Punto di ripresa.** Chi riprende il progetto legge **due file**: `00-registro-decisioni.md` per sapere che cosa è stato deciso, e questo per sapere a che punto è l'esecuzione. Gli altri documenti si consultano quando servono, non si rileggono.

---

## 1. Dove siamo

### 1.1 Cosa è chiuso

| Deliverable Fase 0 | Documento | Stato |
|---|---|---|
| DSL di lettura definito e versionato | `03` | ✅ |
| Stato di Interrogazione | `03`, `04` | ✅ |
| Struttura del Dizionario Semantico | `06` | ✅ |
| Metodo di misura definito e concordato | `07` | ✅ |
| Primo corpus | `11` + `ai/corpus/` | ✅ **nella sola parte sintetica** (D86) |

Corpus documentale: `00` (registro) · `02`–`11`. Undici documenti, 85 decisioni adottate, 5 superate.

### 1.2 Cosa resta aperto

**D7 — clienti pilota.** Unica decisione aperta, e lo resta per scelta esplicita (**D86**): un corpus sintetico non è sigillabile, quindi **D42** e **D49** non sono soddisfatte e il cancello verso la scrittura resta chiuso.

Non blocca il codice. Blocca il passaggio alla Fase 2.

### 1.3 Ricognizione dello stato del repository

| Fatto | Conseguenza |
|---|---|
| `custom_addons/` contiene `lead`, `ui_brand_tokens`, `ui_premium_shell`, `ui_theme_engine` | I moduli `nli_*` vanno accanto a questi |
| ~~**Nessuna directory `tests` in alcun modulo**~~ | Risolto nella parte 1: `tests/` in tutti i cinque moduli, controlli statici in `tools/arch/` |
| `core/` contiene Odoo 18 con 380 file di traduzione italiana | Fonte di L0, già sfruttata da `ai/corpus/estrai_lessico.py` |
| `docker-compose.yml` con `.dev` e `.prod`, Odoo 18 + PostgreSQL 16 | Sufficiente: il prodotto aggiunge configurazione, non servizi (`04` §14.5) |
| `.env` con `.env.example` versionato | Convenzione da estendere per **D76** e **D77**, non da sostituire |

---

## 2. Le Parti

L'ordine non è arbitrario. Segue due criteri, in questa priorità: **ciò il cui costo cresce superlinearmente se rinviato**, poi **ciò che sblocca il resto**.

### Parte 1 — Fondamenta verificabili

> **È la sola parte il cui rinvio si paga a interessi.** Tutto il resto si può riordinare.

| Contenuto | Decisione |
|---|---|
| Scheletro dei cinque moduli `nli_*` con il grafo di dipendenze | **D18** |
| I **quattro controlli automatici** dei confini | **D24** |
| Infrastruttura di test ed esecuzione automatica | Prerequisito di D24 |

```
custom_addons/
├── nli_core/            contratto · stato · validazione · applicazione · esecuzione
├── nli_semantics/       dizionario · catalogo · risoluzione
├── nli_engine/          interprete · adattatori di fornitore
├── nli_web/             canale chat · presentazione
└── nli_observability/   registro · metriche · corpus
```

I quattro controlli:

| Controllo | Verifica |
|---|---|
| **Manifest** | Il grafo dichiarato corrisponde a `04` §6.2 |
| **Importazioni** | Nessun modulo importa oltre le proprie dipendenze; solo `nli_engine` importa librerie di fornitori |
| **Sintattico** | Nessuna connessione diretta a PostgreSQL; nessun contesto privilegiato nei percorsi di interrogazione |
| **Architetturale** | L'Applicatore è puro; il Validatore è attraversato; il Presentatore riceve stato e risultato insieme |

**Il quarto è il più prezioso e il più trascurato.** Verifica che l'Applicatore non acceda a data e ora correnti: fallisce nel momento esatto in cui qualcuno rompe la riproducibilità del corpus, cioè quando la correzione costa ancora poco.

**Completamento:** i quattro controlli girano automaticamente e passano su uno scheletro vuoto.

**Realizzato il 27/07/2026.** I controlli vivono in `tools/arch/`, con tutte le regole in un solo file (`spec.py`) confrontabile a diff con `04` §6.2–6.3. Documentazione operativa: `tools/arch/README.md`. Due proprietà aggiunte in sede di realizzazione, entrambe difese contro il modo in cui questo genere di strumenti smette di funzionare senza dirlo:

- **nessun controllo può passare a vuoto.** Ogni controllo dichiara quanto ha ispezionato e l'ispezione vuota è un fallimento. Un controllo che non trova più i file da esaminare riporterebbe successo per sempre, con la pipeline verde;
- **i controlli hanno i propri test** (`tools/arch/tests/`, 33 casi): ciascuno è mostrato scattare su una fixture che viola la regola. Un controllo mai visto fallire è indistinguibile da un controllo che non può fallire.

Zone pure dichiarate e verificate da subito: `nli_core/contract`, `nli_core/application`, `nli_core/validation/structural.py`, e — dalla parte 2 — `nli_core/validation/coherence.py` e `nli_core/pure_tests`. L'ultima non è pedanteria: un test che importa la piattaforma non può dimostrare che il codice sotto non la importi. La metà comportamentale del quarto controllo — Applicatore puro su ingressi reali, Validatore attraversato, Presentatore con stato e risultato insieme — entra con i componenti: la prima è arrivata nella parte 2, le altre due nella parte 4.

---

### Parte 2 — Il contratto, senza Odoo e senza modello

| Contenuto | Decisione |
|---|---|
| Schema JSON della Busta e dello Stato | **D11** |
| Validazione livelli 1–2 (struttura, vocabolario) | `03` §12.3 |
| Applicatore: semantica di applicazione delle operazioni | **D9**, `03` §4.5 |
| Forma canonica | `03` §14.3 |
| Registro delle equivalenze semantiche | **D43** |

**Qui si incassa l'investimento fatto sul corpus.** I 1 200 casi di `ai/corpus/corpus_fondativo.jsonl` portano ciascuno lo stato atteso in forma esatta: sono **già** la suite di test dell'Applicatore, della canonicalizzazione e del registro delle equivalenze — senza un solo modello linguistico, senza rete, senza ORM.

È la porzione del prodotto che deve essere impeccabile, ed è interamente deterministica e testabile.

> **Vincolo di progetto da rispettare in questa parte.** La catena non presuppone mai di girare dentro una richiesta HTTP. Ingresso un turno, uscita un turno. Rispettandolo, l'esecuzione asincrona della parte 6 entra come involucro anziché come riscrittura.

**Completamento:** i casi `operations` del corpus fondativo producono lo stato atteso; i casi incoerenti sono respinti; la forma canonica è stabile su permutazioni.

**Realizzato il 28/07/2026.** Tutto in zona pura: nessun import di `odoo`, nessun orologio, 152 test che girano in 11 ms con `python3 tools/pure/run.py`.

| Componente | Dove |
|---|---|
| Vocabolari chiusi | `nli_core/contract/vocabulary.py` — unica fonte, diffabile con `03` §6, §8, §9 |
| Busta e firme delle operazioni | `contract/envelope.py` |
| Stato, albero dei filtri, identificativi | `contract/state.py` |
| Schema JSON formale (D11), generato | `contract/schema.py` → `contract/schema/dsl-1.0-*.json` |
| Validazione livelli 1–2 | `validation/structural.py` |
| Livelli 4–5, la metà senza dizionario | `validation/coherence.py` |
| Applicatore, 22 operazioni, derivazione della vista | `application/applicator.py` |
| Forma canonica, 7 regole | `contract/canonical.py` |
| Registro delle equivalenze (D43) | `contract/equivalence.py` |
| Esecuzione del corpus | `ai/corpus/verifica_contratto.py` |

**I tre criteri, misurati.**

| Criterio | Esito |
|---|---|
| I casi `operations` producono lo stato atteso | **948 / 948.** 444 aperture per round-trip stato → operazioni → stato; 504 raffinamenti confrontando l'Applicatore con la trasformazione dell'intento del generatore — due implementazioni indipendenti della stessa semantica |
| I casi incoerenti sono respinti | **Tutti.** Il corpus non ne contiene — il generatore li evita per costruzione — quindi il criterio è verificato iniettando l'incoerenza in uno stato valido: 10 mutazioni, 10 rifiuti |
| Forma canonica stabile su permutazioni | **360 permutazioni**, nessuna deriva. Più l'idempotenza, asserita come proprietà |

**Il generatore del corpus è stato allineato (D92).** I criteri sopra sono misurati su un corpus rigenerato il 28/07/2026: forma normativa, espressioni temporali simboliche, riferimenti semantici con binding tecnico a parte, raffinamenti che raffinano, e stato atteso anche sui raffinamenti. Dettagli in `11` §4.6.

Due conseguenze pratiche. L'adattatore fra corpus e contratto è **stato rimosso** anziché mantenuto: era un secondo contratto da tenere allineato per dieci anni, e il primo che sarebbe divergito in silenzio. E la quota di frasi duplicate — mai misurata prima, marcata *«da automatizzare»* in `11` §6 — è scesa dal **29,6% all'1,0%**: il corpus precedente aveva 1 200 righe e 845 frasi, e la soglia di rumore di D48 poggia sulla seconda cifra.

**Due letture della specifica fissate qui, perché cambiano il codice.**

La prima: §4.5 regola 4 dice che lo stato risultante viene *"portato in forma canonica"* al termine della sequenza. Alla lettera, con §14.3 regola 1, questo cancellerebbe `origin`, `provenance` e gli identificativi — e con essi D64, tutto §10 e la possibilità dell'utente di riconoscere un fraintendimento. §14.2 risolve: le forme sono due, e quella che si persiste è la **forma d'esercizio**. Al termine dell'applicazione avviene quindi la sola normalizzazione comune alle due (regole 4, 5, 7); la forma canonica si calcola su richiesta, per il confronto.

La seconda: §17.1 turno 2 scrive `is_true` **con** un valore booleano, mentre un predicato che è l'intera condizione non ne porta. Un esempio lavorato che non passa la validazione significa che la lettura è sbagliata, quindi il valore è ammesso e la canonicalizzazione lo scarta — due buste che differiscono per un valore ridondante sono la stessa condizione, e C8 esige che abbiano una sola forma canonica.

**Il vincolo di progetto è rispettato.** La catena non presuppone mai di girare dentro una richiesta HTTP: l'Applicatore è una funzione da (stato, operazioni) a stato, `revert_last` **riporta** la richiesta anziché risolverla — la storia appartiene al sistema, non a una funzione pura — e `open_record` restituisce una navigazione lasciando l'interrogazione intatta. L'involucro asincrono della parte 6 entra intorno a questo, non dentro.

---

### Parte 3 — `nli_semantics`

| Contenuto | Decisione |
|---|---|
| Dizionario a quattro livelli, L3 non attivo | **D28** |
| Sette tipi di voce, vocabolario chiuso | **D30**, **D59** |
| Distinzione vocabolario / definizione | **D29**, **D38** |
| Generazione di L0 per introspezione dei metadati | **D84** |
| Regole di esposizione e budget | **D31**, **D79** |
| Catalogo a tre fasi A / B / C | **D32**, **D33** |
| Filtro sui permessi **prima** della selezione | `06` §5.9 |
| Impronta dei permessi | **D39** |
| Copertura scomposta | **D34** |

`ai/corpus/estrai_lessico.py` ha già dimostrato l'approccio sui file di traduzione; qui la stessa logica si applica ai metadati vivi. `ai/corpus/lessico_l1.json` è il primo pacchetto base L1.

**Prerequisiti da D87** (deliberata il 28/07/2026, `00` §14). I tre vincoli della decisione sono lavoro di questa parte, non note a margine:

| Vincolo | Che cosa impone |
|---|---|
| **V-D87-1** | Una categoria non compare nel catalogo di un utente che non può leggere i campi che la definiscono. I `campi_implicati` devono essere l'insieme **completo**, e se non è calcolabile la categoria è esclusa — fallimento in sicurezza, come per l'impronta di D39 |
| **V-D87-2** | Il costo di una categoria entra nella validazione di livello 5. Una categoria può nascondere un'aggregazione su un'altra entità, e D12 esiste perché il costo sia calcolabile a priori |
| **V-D87-3** | L'Applicatore non espande mai una categoria: la risolve il Risolutore, a ogni esecuzione, perché la condizione può dipendere dall'orologio (`scadenza < oggi`) |
| **V-D88-1** | La **direzione di ordinamento** si deriva dal tipo dell'attributo — ascendente per il testo, discendente per le date — e il Risolutore la dichiara con la propria regola. L'Applicatore la rifiuta se assente: `asc` su una data restituirebbe i cinque più vecchi per *«gli ultimi cinque»* |
| **V-D91-1** | `year_to_date` si risolve contro l'inizio dell'**esercizio fiscale**, come `current_year`. Da gennaio in un'azienda con esercizio non solare è un numero sbagliato di aspetto credibile |

**Due difetti nei dati da correggere qui**, rilevati deliberando D87:

- `lessico_l1.json`, categoria `sottoscorta`: condizione `qty_available < reordering_min`, ma `campi_implicati` dichiara solo `qty_available`. **`reordering_min` manca**, ed è un buco di V2 sotto V-D87-1;
- la voce `fatturato` è elencata fra le categorie ed è una **metrica T4** (*"somma di amount_untaxed su fatture confermate"*). T4 è il tipo che `06` §3.5 definisce «il più pericoloso», e non serve in Fase 1 mentre T5 sì.

**Realizzato il 28/07/2026 — la metà pura.** Dizionario e catalogo in `custom_addons/nli_semantics`, tutto in zona pura: 236 test con `python3 tools/pure/run.py`. La misura è in `ai/corpus/misura_catalogo.py`, dentro `./manage.sh check`.

| Componente | Dove |
|---|---|
| Sette tipi di voce, classi vocabolario/definizione | `dictionary/entries.py` |
| Linguaggio tipizzato delle condizioni T5/T4 | `dictionary/conditions.py` |
| Livelli, precedenza L2 › L1 › L0, L3 come coda | `dictionary/store.py` |
| Indice dei termini unico e multilingua | `dictionary/index.py` |
| Nove regole di esposizione, budget dalla finestra | `catalogue/exposure.py` |
| Fasi A / B / C, soglia **e** margine | `catalogue/phases.py` |
| Assemblaggio: permessi, poi selezione, poi budget | `catalogue/build.py` |
| Copertura scomposta | `catalogue/coverage.py` |

**I tre criteri, misurati sul corpus.**

| Criterio | Esito |
|---|---|
| Copertura misurabile | **100%** complessiva, entità e attributi, su 948 casi. Il 100% sugli attributi non è fortuna: in Fase C non c'è selezione (D32), quindi è esatto per costruzione — ed è la proprietà che rende RC3 un problema piccolo e isolato anziché un tetto invisibile |
| Percorso rapido di Fase A | **86,2%** dei 696 casi in cui l'entità non è nota, **zero determinazioni sbagliate**. Tolleranza dichiarata 1%, da ritarare |
| Budget dalla finestra | Derivato: 128k → 60 (tetto D31); 6k → dalla finestra; 2k → pavimento, con il motivo dichiarato. Dimensione media del catalogo 6,5 voci, zero rifiuti per budget |

**Il pezzo di progetto che conta: la condizione di una categoria è una struttura tipizzata.** Da lì i tre vincoli di D87 si derivano invece di essere dichiarati — i campi implicati sono l'insieme completo per costruzione (V-D87-1), la dipendenza dall'orologio è una proprietà del nodo (V-D87-3), la classe di costo distingue una clausola da un roll-up su un'altra entità (V-D87-2). Il buco di `sottoscorta` non è più correggibile per dimenticanza: non c'è nulla da dichiarare.

**Due difetti nei dati, corretti** (`00` §14.6): `lessico_l1.json` porta ora `condizione_tipizzata` e non più `campi_implicati`; `fatturato` è passata da categoria a metrica T4.

**La metà che richiede Odoo, completata lo stesso giorno.** In `nli_semantics/introspection/`, che non è zona pura ed è il punto in cui la piattaforma è ammessa esistere — così `dictionary/` e `catalogue/` non devono.

| Componente | Dove | Decisione |
|---|---|---|
| L0 per introspezione dei metadati, rigenerabile identico | `introspection/l0.py` | **D84** |
| Riferimenti leggibili e impronta dei permessi | `introspection/permissions.py` | **D39**, **D40** |
| Filtri salvati come proposte di categoria, inerti in coda L3 | `introspection/filters.py` | **D35**, **D28** |

**Due rilievi dall'esecuzione**, entrambi in `00` §16:

- **l'impronta non è leggibile dalle tabelle delle regole** (§16.5). Un utente interno ordinario non può leggere `ir.model.access`, e `sudo` è vietato dal controllo di D24 — correttamente, perché sarebbe un percorso privilegiato dentro la catena. L'impronta si costruisce sugli **effetti osservabili**: `has_access`, le chiavi di `fields_get`, gruppi, società attive, lingua. Le regole sui record sono **deliberatamente escluse**: filtrano record, e il catalogo contiene riferimenti, mai record;
- **il divieto sui contesti privilegiati è ora scoped ai percorsi di interrogazione** (§16.6), come `04` §6.3 dice fin dall'inizio. Applicato anche ai test rendeva non verificabile la proprietà che protegge. Nessuna eccezione per l'SQL diretto.

**Completamento:** copertura misurabile sul corpus fondativo; percorso rapido di Fase A funzionante; budget derivato dalla finestra di contesto.

---

### Parte 4 — Esecuzione deterministica

| Contenuto | Decisione |
|---|---|
| Risolutore — unico componente consapevole del tempo | `04` §4.6 |
| Validazione livelli 3–5 | `03` §12.4–12.6 |
| Esecutore — ORM, conteggio prima del recupero | **D68**, `04` §10.5 |
| Presentatore — viste native | **V4** |
| Stato persistito come record | **D19** |
| Contesto societario sul turno | **D40** |

**Realizzato il 28/07/2026.**

| Componente | Dove | Note |
|---|---|---|
| Risolutore | `nli_core/resolution/` | **Zona deterministica**, non pura |
| Espressioni temporali contro l'esercizio fiscale | `resolution/calendar.py` | §9.2, V-D91-1 |
| Piano di Esecuzione, tecnico ed effimero | `resolution/plan.py` | Mai persistito |
| Validazione livelli 3–5 con il dizionario | `validation/contextual.py` | Zona pura |
| Esecutore ORM, conteggio prima del recupero | `execution/executor.py` | **D68** |
| Presentatore, viste native | `presentation/presenter.py` | **V4**, **D64** |
| Stato come record, turni con contesto societario | `models/nli_interrogation.py` | **D19**, **D40** |

**Una distinzione nuova nei controlli: la zona deterministica.** `04` §4.6 dice che il Risolutore è *«il solo componente consapevole del tempo»*, e essere consapevoli del tempo non è leggerlo: l'istante è un **argomento**. Senza questa distinzione la scelta era fra un Risolutore che non sa fare aritmetica sulle date e un Risolutore che nessuno controlla. Una zona deterministica vieta le stesse **chiamate** di una zona pura — `now`, `today`, `utcnow` — e ammette le librerie di data. È anche la classificazione corretta per le suite di test: un test deve poter **costruire** un istante e non deve poterlo **leggere**, altrimenti passa oggi e fallisce fra undici mesi.

**Due scelte che vale la pena dichiarare.**

La prima: **la provenienza non viene persistita**. I frammenti di §10.3 sono le parole dell'utente, e D54 richiede la pseudonimizzazione all'ingresso con mappatura separata e cifrata — che non esiste ancora. Persistirli adesso significherebbe scrivere testo dell'utente in chiaro per i dodici mesi di D26, e l'argomento di D54 si applica alla lettera: *«la pseudonimizzazione retroattiva non esiste»*. Vengono quindi rimossi in scrittura; l'evidenziazione incrociata continua a funzionare dentro il turno vivo, dove la busta è in memoria. Quando D54 arriva, si persistono pseudonimizzati **nello stesso cambiamento**, non prima.

La seconda: **il Presentatore non ha un costruttore che accetti il solo risultato.** V4 e D64 sono la stessa affermazione vista da due lati, e il modo di renderla strutturale anziché sperata è un tipo di ritorno che non può portare l'uno senza l'altra. Il test lo verifica costruendo la presentazione senza stato e pretendendo un errore.

**Completamento:** prima interrogazione end-to-end da uno stato scritto a mano, senza modello. È il punto in cui il prodotto esiste come motore deterministico.

---

### Parte 5 — `nli_engine`

| Contenuto | Decisione |
|---|---|
| Adattatore di fornitore | `04` §8 |
| Profili di modello dall'amministrazione | **D75**, **D80** |
| Segreti non leggibili da un salvataggio | **D76** |
| Elenco host ammessi nell'ambiente | **D77** |
| Dichiarazione delle capacità del profilo | **D78** |
| Generazione vincolata allo schema | `03` §12.3 |
| Ripristino con un solo tentativo | **D15** |

**Completamento:** prima interpretazione reale; accuratezza misurata sul corpus fondativo; profilo locale e profilo remoto entrambi funzionanti.

---

### Parte 6 — Esecuzione asincrona

> **Obbligatoria prima di qualunque utente reale.** È l'unico rischio del progetto il cui danno ricade fuori dal perimetro del prodotto.

| Contenuto | Decisione |
|---|---|
| Accettazione + `ir.cron._trigger()` + notifica su bus | **D20a** |
| Dispatcher con pool di thread, `CICLO_MAX` 15 s | **D20b** |
| I cinque limiti di carico | **D20c** |
| Dispatcher separato per il carico differito | **D20d** |
| `--max-cron-threads` a 4, entro il tetto di connessioni | **D20e** |
| Recupero dei turni orfani, idempotenza | `05` §5.3–5.4 |
| **Prova di isolamento** | **D27** |

**Completamento:** la prova di isolamento passa — con N utenti conversazionali continui, la latenza di Odoo per un utente ordinario non peggiora in modo misurabile.

---

### Parte 7 — `nli_web`

| Contenuto | Decisione |
|---|---|
| Canale chat dentro Odoo | `04` §14.6 |
| Interpretazione sempre visibile sopra il risultato | **D64** |
| Salienza graduata per origine | **D65** |
| Ogni elemento azionabile | **D66** |
| Periodo risolto, non l'espressione | **D67** |
| Messaggi di rifiuto per carico | **D69** |
| Token di `ui_brand_tokens` con degradazione | **D25** |
| Accessibilità | **D71** |
| Aggregato nel piede di colonna quando la vista è lista | **D89** (V-D89-1) |
| Stati dell'attesa | `09` §5.2 |

**Completamento:** gli otto criteri di `02` §8.5.

---

### Parte 8 — Il perimetro guidato

Proposta in `13-perimetro-guidato.md`, **non ancora deliberata**. Tre decisioni, e l'ordine di esecuzione non segue la numerazione: **8a precede la parte 7**, perche' protegge l'utente su qualunque canale e non richiede interfaccia.

#### 8a — La condizione nominata dev'essere fondata (**D105**)

| Contenuto | Nota |
|---|---|
| Il livello 3 riceve i **termini** di ogni condizione nominata, oltre a tipi e riferimenti | oggi riceve solo `types` e `known_refs` |
| Una condizione nominata la cui provenienza non contiene alcun termine della categoria e' **rifiutata** | `03` §10.3: la provenienza *e'* il frammento che l'ha prodotta |
| Il confronto usa **lo stesso riconoscitore di termini della Fase A**, non una nuova implementazione | refusi, abbreviazioni, accenti mancanti e maiuscole sono nel corpus di proposito |
| Un test che lo mostra **scattare** e uno che lo mostra **tollerare** una frase perturbata | D24: nessun controllo passa a vuoto |

**Misurato prima e dopo**: riparazioni (D15), rese, e le tre classi di `00` §18 sul filtro. **Attenzione al segno**: questo controllo *alza* i rifiuti e *abbassa* le risposte sbagliate. Se le riparazioni non salgono, il controllo non sta scattando; se sale l'accuratezza, e' un effetto collaterale e non l'obiettivo.

#### 8b — Il rifiuto propone (**D106**)

| Contenuto | Nota |
|---|---|
| Quando 8a rifiuta, o quando la Fase A e' sotto margine, l'esito e' `clarification` con da 2 a 4 opzioni | `03` §4.4, gia' nel contratto e oggi quasi mai emesso |
| Le opzioni sono **derivate dal catalogo**, non chieste al modello | **P4**: e' informazione deterministica, come la vista di §5.9 |
| Ogni opzione porta le operazioni che produrrebbe, quindi e' eseguibile con un clic | gia' previsto dalla forma della busta |

**Completamento 8a+8b:** una frase che oggi produce un filtro inventato produce invece una domanda con le letture plausibili, e il caso e' nel corpus di regressione.

#### 8c — Il vocabolario visibile (**D104**)

Vive dentro la parte 7 perche' e' interfaccia. Le voci escono dal catalogo — condizioni nominate con i loro termini, periodi dal vocabolario temporale, confronti dagli attributi numerici, colonne dagli attributi esposti entro il budget di **D31/D79**. **Nessuna lista scritta a mano**: un cliente con campi personalizzati ottiene il proprio perimetro senza che nessuno scriva nulla.

**Completamento:** il perimetro non contiene nulla che il sistema non sappia fare, perche' nasce dalla stessa fonte che il modello riceve.

---

## 3. Il Percorso Critico

```
1 fondamenta ──▶ 2 contratto ──▶ 3 semantica ──▶ 4 esecuzione ──▶ 5 engine
                                                                      │
                                          6 asincrono ◀───────────────┘
                                               │
                                               ▼
                            8a fondatezza ──▶ 8b il rifiuto propone
                                               │
                                               ▼
                                  7 web  (+ 8c vocabolario visibile) ──▶ Fase 1
```

**La numerazione delle parti non e' l'ordine di esecuzione.** 8a e 8b precedono la parte 7 perche' non richiedono interfaccia e proteggono l'utente su qualunque canale; 8c e' interfaccia e vive dentro la parte 7.

**Le parti 2 e 3 sono parzialmente parallelizzabili**: il contratto non dipende dal dizionario. Le altre no.

**La parte 6 non può essere ultima.** Va completata prima che il prodotto veda un utente reale, e la tentazione di rinviarla sarà forte perché non blocca nulla di visibile.

---

## 4. In Parallelo, Senza Codice

| Attività | Decisione | Costo |
|---|---|---|
| **Elicitazione** di ~200 enunciati presso 8–10 persone di mestiere | **D85** | ~30 min a persona |
| Ricerca marchio su «AIDA» prima di comunicarlo all'esterno | **D6** | Poche ore |
| Verifica dei requisiti **F-1…F-7** sul fornitore scelto | **D56** | Poche ore |
| Individuazione dei clienti pilota | **D7** | Commerciale |
| Misura iniziale sull'interfaccia nativa | **D52** | Poche ore, **finestra che si chiude** |

**D85 è quella con il miglior rapporto valore/costo dell'intero elenco.** Non richiede clienti, prodotto attivo né codice: corregge il generatore del corpus anziché i suoi prodotti.

**D52 è l'unica con una scadenza che non dipende da noi**: va eseguita prima di attivare il primo utente, e dopo non è più ottenibile.

---

## 5. Stato di Avanzamento

Da aggiornare a ogni parte completata. È l'unica sezione di questo documento destinata a cambiare.

| Parte | Stato | Note |
|---|---|---|
| 1 — Fondamenta verificabili | ✅ **Completa** (27/07/2026) | Cinque moduli `nli_*`, quattro controlli in `tools/arch/`, 33 test dei controlli, suite Odoo in `nli_core/tests/`. Esecuzione automatica su tre punti: `pre-push`, GitHub Actions, `./manage.sh test` |
| 2 — Contratto | ✅ **Completa** (28/07/2026) | Contratto, livelli 1–2 e metà di 4–5, Applicatore, forma canonica, registro equivalenze. 152 test puri senza Odoo; **948/948** casi del corpus verificati. Cinque questioni aperte in `00` §13 (**D87–D91**); **D92 corretta** |
| 3 — `nli_semantics` | ✅ **Completa** (28/07/2026) | Dizionario, catalogo, tre fasi, copertura (236 test puri) più L0 per introspezione, `ir.filters`, impronta dei permessi (27 test Odoo). I tre criteri misurati: copertura 100%, Fase A 86,2% con zero errori, budget derivato |
| 4 — Esecuzione deterministica | ✅ **Completa** (28/07/2026) | Risolutore (zona deterministica), livelli 3–5, Esecutore con conteggio prima del recupero, Presentatore, stato come record, contesto societario sul turno. 40 test Odoo, 269 puri. Prima interrogazione end-to-end da stato scritto a mano |
| 5 — `nli_engine` | ◐ **Implementata, profilo non qualificato** (29/07/2026) | Adattatore, profili con D76/D77/D80, generazione vincolata, ripristino singolo. 52 test Odoo, 347 puri. Profilo di riferimento **`qwen3.5:9b`** su `ollama` nativo (Metal). Misura su **tutte le 444 aperture**: complessiva 63,5%, `target` 98,0%, `fields` 87,2%, `group_by` e `order_by` 93,0%, `limit` 93,5%, `measures` e `presentation` 98,0% — **sette sezioni su otto sopra D44**. Resta `filter` a **72,5%**: D80 rifiuta ancora l'attivazione, ed è il comportamento voluto. Cinque delibere in `00` §18 (**D97–D102**), di cui tre correggono il **metro** e non il modello |
| 6 — Asincrono | ◐ **Implementata, D27 non superata** (28/07/2026) | Sesto modulo `nli_dispatch` (**D94**): accettazione, coda, dispatcher con pool derivato da `db_maxconn`, corsia differita separata, recupero degli orfani, interruttore, notifica su bus. La catena composta per la prima volta e girata su metadati introspettivi. 79 test Odoo, 314 puri, 47 dei controlli. **D27 non e' superata**: lo strumento esiste e dichiara su che cosa ha misurato — vedi `00` §17.6 |
| 8a — Fondatezza della condizione nominata (**D105**) | ☐ | **Prossima**, e precede la parte 7: non richiede interfaccia. Alza i rifiuti e abbassa le risposte sbagliate; l'accuratezza non e' l'obiettivo |
| 8b — Il rifiuto propone (**D106**) | ☐ | `clarification` con opzioni derivate dal catalogo, non chieste al modello (P4). La funzione esiste nel contratto e oggi non viene usata |
| 7 — `nli_web` (+ **D104**, vocabolario visibile) | ☐ | Primo bersaglio di taratura: l'accettazione a P95 205 ms contro i 50 ms di `00` §6.1 |

| Attività parallela | Stato |
|---|---|
| D85 — elicitazione | ☐ |
| D6 — ricerca marchio | ☐ |
| D56 — verifica fornitore | ☐ |
| D7 — clienti pilota | ☐ **aperta** |
| D52 — misura iniziale | ☐ **finestra che si chiude** |

---

## 5.1 Come si verifica

Tutto quello che segue gira senza Odoo tranne l'ultima riga di ciascun blocco. È anche ciò che il **pre-push** esegue (`./scripts/install-hooks.sh`, `core.hooksPath=scripts/hooks`) e ciò che gira in CI (`.github/workflows/boundaries.yml`).

```bash
./manage.sh check              # tutto il verificabile senza database, in un comando
./manage.sh test <db>          # quanto sopra, poi la suite Odoo su <db>

python3 tools/arch/run.py                  # i quattro controlli dei confini (D24)
python3 -m unittest discover -s tools/arch/tests -t .   # i test dei controlli
python3 tools/pure/run.py [filtro]         # zona pura, ~290 test, ~20 ms
python3 tools/dsl/emit_schema.py --write   # rigenera lo schema JSON derivato (D11)

python3 ai/corpus/genera_corpus.py         # rigenera il corpus (deterministico, seme 42)
python3 ai/corpus/verifica_contratto.py    # criteri della parte 2
python3 ai/corpus/misura_catalogo.py [--taratura]   # criteri della parte 3
NLI_ALLOWED_HOSTS=localhost:11434 \
  python3 ai/corpus/misura_accuratezza.py --casi 20  # criterio della parte 5

./manage.sh start                                  # lo stack, per le prove di carico
python3 tools/load/prova_isolamento.py \
  --db nli_test --utenti 20 --secondi 20           # strumento di D27 (parte 6)
```

**Fatti dell'ambiente che servono e non sono deducibili dal codice.**

| | |
|---|---|
| Database di prova | `nli_test` (esiste già; `./manage.sh test nli_test`) |
| Modello locale | `ollama` con `qwen2.5:latest`, container `ollama`, rete `qwen25_default` |
| Endpoint del modello | `http://localhost:11434/v1` dall'host, `http://ollama:11434/v1` dal container |
| Variabili obbligatorie | `NLI_ALLOWED_HOSTS` — senza, **nessun** host è ammesso (D77). `NLI_UTTERANCE_KEY` — senza, **nessuna richiesta è accettata** (D96). Entrambe fallimenti chiusi, entrambe passate al container da `docker-compose.yml` e definite in `.env` |
| Chiave degli enunciati | `python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` |
| Prove di carico | Lo stack `dev` gira **senza `--workers`**: il pool prefork la cui saturazione è RA3 non esiste, e nessuna misura fatta lì è la prova di D27 |
| Importabilità fuori Odoo | `tools/pure/bootstrap.py` registra pacchetti sintetici `nli_*` e l'alias `odoo.addons`, senza eseguire gli `__init__.py` degli addon |

**Tre generi di zona**, dichiarati in `tools/arch/spec.py` e verificati dal quarto controllo:

| Zona | Può | Non può |
|---|---|---|
| **pura** | solo i propri argomenti | `odoo`, date, orologio, caso, ambiente |
| **deterministica** | calcolare con le date | **leggere** l'orologio (`now`, `today`), `odoo` |
| nessuna | la piattaforma | SQL diretto, `sudo` (`tests/` escluse dalla sola regola sui privilegi) |

---

## 6. Regole di Esecuzione

Valgono per tutte le parti, e discendono da decisioni già adottate.

| Regola | Origine |
|---|---|
| I quattro controlli dei confini girano da subito e non si disattivano | **D24** |
| Nessuna capacità è completa senza il corrispondente caso di valutazione | `02` §12.4 |
| Non si modificano dizionario e modello nello stesso rilascio | `06` §4.4 |
| Una regressione per sezione blocca il rilascio | **D50** |
| Nessun enunciato persistito in chiaro | **D54** |
| Nessun percorso privilegiato, nemmeno nel dispatcher | **V2**, `08` §2.3 |
| La catena non presuppone di girare in una richiesta HTTP | Parte 2 |

---

*Documento operativo. Si aggiorna; non si riscrive.*
