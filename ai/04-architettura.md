# Architettura di Sistema
## AI Agent per Odoo — Natural Language Interaction Layer

---

| Voce | Valore |
|---|---|
| **Titolo** | Architettura di Sistema – AI Agent per Odoo |
| **Versione** | 1.0 (bozza) |
| **Data** | 27 luglio 2026 |
| **Stato** | Bozza sottoposta ad approvazione dell'Architect |
| **Destinatari** | Software Architect, Team Leader, Sviluppatori backend, frontend e AI, Platform Engineer |
| **Documenti sorgente** | `02-visione-prodotto.md`, `03-specifica-dsl.md` |
| **Piattaforma di riferimento** | Odoo 18.0 Community, PostgreSQL 16, distribuzione Docker |
| **Ambito** | Componenti, responsabilità, confini, flussi, dipendenze, punti di estensione, prestazioni, degradazione, osservabilità |
| **Fuori ambito** | Schema del database, definizione del DSL *(vedi doc. 03)*, ciclo di vita del Dizionario Semantico *(documento dedicato)*, modello di sicurezza applicativa in dettaglio *(documento dedicato)*, strategia di prompting |

> **Prerequisiti.** Il documento presuppone adottate le decisioni **D9** (modello a due artefatti), **D10** (riferimenti semantici con catalogo per utente) e **D4** (Stato di Interrogazione come oggetto centrale). Sono le tre decisioni che determinano la forma dei componenti: se una venisse respinta, questo documento va riscritto.

---

## 1. Executive Summary

### 1.1 Il problema architetturale

Il documento di visione fissa una promessa che l'architettura deve rendere vera: **un componente probabilistico occupa una sola posizione del sistema, e tutto il resto è software convenzionale.**

Tradurre questa promessa in componenti significa rispondere a quattro domande:

- dove finisce esattamente la parte non deterministica, e come si impedisce che si allarghi;
- dove risiede lo Stato di Interrogazione, chi lo possiede, come sopravvive alla sessione e al canale;
- come si ottiene l'indipendenza dal canale e dal fornitore del modello senza pagarla con un'astrazione inutile;
- come si mantiene un'esperienza conversazionale su un'infrastruttura la cui componente più lenta è anche quella meno affidabile.

### 1.2 La risposta in una riga

> Un **nucleo deterministico** che possiede lo stato, il contratto e l'esecuzione; un **interprete isolato** che è l'unico componente a parlare con un modello linguistico; **adattatori** sottili ai due estremi — canali in ingresso, Odoo in uscita.

### 1.3 Le cinque decisioni architetturali portanti

**DA1 — L'interprete è l'unico componente che conosce l'esistenza di un modello linguistico.**
Nessun altro componente importa librerie di fornitori, conosce nomi di modelli o gestisce chiavi. È ciò che rende il vincolo V5 verificabile con un controllo automatico anziché con la disciplina (§8).

**DA2 — Lo Stato di Interrogazione vive nel database Odoo, non nella sessione.**
Non in memoria, non in una cache volatile, non nel client. È un record. Ne discendono ripresa a distanza di giorni, cambio di canale, condivisione, annullamento e tracciabilità — tutte proprietà che il documento di visione richiede e che una sessione in memoria non può offrire (§9).

**DA3 — Il Catalogo Semantico è un componente di primo piano, non una funzione di supporto.**
È il punto in cui si decide cosa il modello può nominare, e quindi simultaneamente il presidio del vincolo V2 e il tetto superiore dell'accuratezza (rischio RC3). Merita un componente proprio, con metriche proprie (§7).

**DA4 — L'esecuzione avviene sempre in un ambiente Odoo con l'identità dell'utente.**
Nessun servizio esterno accede ai dati. Nessuna esecuzione con privilegi elevati, in nessun percorso, nemmeno per la cache. Il vincolo V2 non è un controllo: è una proprietà di dove il codice gira (§12).

**DA5 — Il sistema è utilizzabile quando il modello non è disponibile.**
Interrogazioni salvate, riesecuzione, modifica dell'interpretazione dall'interfaccia: tutto ciò che non richiede comprensione del linguaggio continua a funzionare. È la traduzione architetturale della degradazione dignitosa (§11).

### 1.4 Struttura in cinque moduli Odoo

L'intero sistema è distribuito in `custom_addons/`, coerentemente con l'impianto esistente del repository:

| Modulo | Responsabilità | Dipende da |
|---|---|---|
| `nli_core` | Contratto, stato, validazione, applicazione, esecuzione | `base`, `web` |
| `nli_semantics` | Dizionario Semantico, Catalogo, risoluzione | `nli_core` |
| `nli_engine` | Interprete e adattatori di fornitore | `nli_core` |
| `nli_web` | Canale chat, presentazione, interpretazione ispezionabile | `nli_core`, `web` |
| `nli_observability` | Registro, metriche, corpus di valutazione | `nli_core` |

Il prefisso `nli_` è proposto in §14.2 insieme alla motivazione della suddivisione, che non è organizzativa ma di **applicazione dei confini**: in Odoo il grafo delle dipendenze fra moduli è dichiarato e verificabile, e questo lo rende lo strumento più efficace per impedire che i confini architetturali vengano attraversati.

---

## 2. Vincoli Architetturali Derivati

L'architettura non è libera. Eredita dai documenti precedenti vincoli che non sono obiettivi di progetto ma condizioni di validità: un'architettura che ne violi uno è sbagliata, non diversa.

### 2.1 Vincoli ereditati

| # | Vincolo | Origine | Conseguenza architetturale |
|---|---|---|---|
| **V1** | Nessuna operazione da output generativo non validato | Visione | La validazione è un componente attraversato obbligatoriamente, non una funzione richiamabile |
| **V2** | Esecuzione sempre con i permessi dell'utente | Visione | Nessun percorso con privilegi elevati; nessuna cache di risultati condivisa fra utenti |
| **V3** | Nessun accesso ai dati che aggiri l'ORM | Visione | Nessun componente possiede una connessione diretta a PostgreSQL |
| **V4** | Nessun risultato senza interpretazione | Visione | La presentazione riceve stato e interpretazione insieme; non esiste percorso che produca solo dati |
| **V5** | Nessuna dipendenza esclusiva da un fornitore | Visione | Un solo componente conosce i fornitori (DA1) |
| **V6** | Nessuna rottura delle interrogazioni salvate | Visione | Lo stato persiste riferimenti semantici; la risoluzione è ripetuta a ogni esecuzione |
| **V7** | Nessun contenuto di record verso il modello | Visione | Il confine dei dati coincide con il confine di un componente: solo il Catalogo alimenta l'interprete |
| **C1** | Vocabolario chiuso | DSL | Lo schema del contratto è un artefatto condiviso e versionato, non conoscenza diffusa nel codice |
| **C3** | Impossibilità strutturale al posto del divieto | DSL | I confini sono resi effettivi dal grafo delle dipendenze, non da revisioni del codice |

### 2.2 Il vincolo che determina più struttura di ogni altro

**V7** — nessun contenuto di record verso il modello.

Sembra un requisito di conformità; è in realtà il vincolo che stabilisce la forma del sistema. Impone che esista **un solo componente autorizzato a preparare ciò che raggiunge il modello**, e che quel componente non abbia accesso ai dati.

Ne discende la separazione fra `nli_semantics` — che costruisce il Catalogo a partire dai metadati e dai permessi — e `nli_engine`, che riceve il Catalogo e non ha altra fonte di informazione. L'interprete non può inviare al modello dati che non ha modo di ottenere.

È di nuovo il criterio **C3** applicato all'architettura: non un controllo che verifica cosa viene inviato, ma una struttura in cui il componente che invia non possiede ciò che non deve inviare.

### 2.3 Vincoli di piattaforma

| Vincolo | Implicazione |
|---|---|
| **Odoo 18.0 Community** | Nessuna dipendenza da funzionalità Enterprise; le viste generate usano i tipi disponibili in Community |
| **Modello a processi/thread di Odoo** | Una chiamata al modello di 1–3 secondi occupa un worker: non è accettabile (§10.3) |
| **PostgreSQL 16** | Persistenza dello stato e del registro tramite ORM; nessun accesso diretto |
| **Distribuzione Docker** | L'interprete può essere un processo separato senza cambiare l'architettura logica (§14.4) |
| **Aggiornamenti di Odoo** | I punti di contatto con l'ORM e con il sistema delle viste sono concentrati, non diffusi (§13.4) |

---

## 3. Vista d'Insieme

### 3.1 Gli strati

```
┌──────────────────────────────────────────────────────────────────┐
│  CANALI                                                           │
│  chat Odoo (R1) · voce · Teams · Slack · email · API              │
│  responsabilità: raccogliere l'intenzione, presentare l'esito     │
└──────────────────────────────────────────────────────────────────┘
                            │  intenzione + identità + id sessione
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  ORCHESTRATORE DI SESSIONE                        deterministico  │
│  possiede lo Stato · storia · annullamento · esito verso il canale│
└──────────────────────────────────────────────────────────────────┘
          │                                              ▲
          │ richiesta + stato corrente                   │ stato + interpretazione
          ▼                                              │
┌────────────────────────┐              ┌─────────────────────────────┐
│  CATALOGO SEMANTICO    │─ catalogo ──▶│  INTERPRETE   probabilistico│
│  metadati + permessi   │              │  unico contatto col modello │
│  deterministico        │              └─────────────────────────────┘
└────────────────────────┘                            │ Busta
          ▲                                           ▼
          │                              ┌─────────────────────────────┐
          │                              │  VALIDATORE   5 livelli     │
          │                              └─────────────────────────────┘
          │                                           │ Busta valida
          │                                           ▼
          │                              ┌─────────────────────────────┐
          │                              │  APPLICATORE  merge         │
          │                              └─────────────────────────────┘
          │                                           │ Stato
          │                                           ▼
          │                              ┌─────────────────────────────┐
          └──── dizionario ──────────────│  RISOLUTORE   + permessi    │
                                         └─────────────────────────────┘
                                                      │ Piano
                                                      ▼
                                         ┌─────────────────────────────┐
                                         │  ESECUTORE    ORM Odoo      │
                                         └─────────────────────────────┘
                                                      │ vista + record
                                                      ▼
                                         ┌─────────────────────────────┐
                                         │  PRESENTATORE               │
                                         │  vista nativa + interpret.  │
                                         └─────────────────────────────┘

  ─────────────────────────────────────────────────────────────────
  REGISTRO  ◀── ogni componente scrive: buste, stati, esiti, tempi
```

### 3.2 La sola linea non deterministica

Un solo riquadro del diagramma è probabilistico: l'**Interprete**. Ha esattamente due connessioni:

- **in ingresso**: richiesta dell'utente, stato corrente in forma semantica, catalogo;
- **in uscita**: una Busta di Interpretazione, che non raggiunge nulla senza attraversare il Validatore.

Questa è la proprietà architetturale centrale, e va conservata come tale: ogni futura evoluzione che aggiunga una seconda connessione all'Interprete — accesso ai dati, chiamata diretta all'Esecutore, scrittura sullo stato — allarga la superficie non deterministica e va valutata con lo stesso rigore di una modifica del contratto.

### 3.3 I tre confini invalicabili

| Confine | Regola | Perché è invalicabile |
|---|---|---|
| **Interprete ↔ dati** | L'Interprete non ha accesso all'ORM né a PostgreSQL | V7: non può inviare al modello ciò che non possiede |
| **Interprete → esecuzione** | Ogni output attraversa il Validatore | V1: è il confine di validazione del contratto |
| **Esecutore ↔ identità** | Ogni esecuzione avviene con l'utente richiedente | V2: nessun percorso privilegiato |

Il §6 stabilisce come questi confini vengono resi effettivi dal grafo delle dipendenze fra moduli anziché essere affidati alla revisione del codice.

### 3.4 Cosa non compare nel diagramma, e perché

**Nessuna coda di messaggi fra i componenti deterministici.** Il percorso dalla Busta al risultato è sincrono: validazione, applicazione, risoluzione ed esecuzione sono operazioni di millisecondi. Interporvi un'infrastruttura asincrona aggiungerebbe complessità operativa e modalità di guasto senza alcun beneficio. L'asincronia serve dove c'è attesa reale — la chiamata al modello — ed è trattata in §10.3.

**Nessun servizio esterno oltre al fornitore del modello.** Nessun motore di ricerca vettoriale, nessuna cache distribuita, nessun archivio separato. Ogni servizio aggiuntivo è un componente da gestire, aggiornare, mettere in sicurezza e diagnosticare per dieci anni. La selezione del catalogo (§7.4) è progettata per non richiederne, ed è una scelta deliberata: la complessità operativa è un costo permanente che il documento di visione impone di non aumentare senza un beneficio dimostrato.

---

## 4. I Componenti

Ogni componente è descritto con lo stesso schema: responsabilità, ingressi e uscite, **cosa non fa**, note di progetto. La terza voce non è ridondante: la maggior parte dell'erosione architetturale avviene per accumulo di responsabilità implicite, e dichiararle escluse rende l'accumulo visibile in revisione.

### 4.1 Orchestratore di Sessione

**Responsabilità.** Coordina il ciclo completo di un turno. Possiede lo Stato di Interrogazione e la sua storia. Decide, in base all'esito della Busta, se procedere all'esecuzione, porre un chiarimento o comunicare un limite. È il solo componente che conosce l'intero flusso.

**Ingressi.** Intenzione in linguaggio naturale, identità dell'utente, identificativo di sessione, canale di provenienza.
**Uscite.** Esito strutturato per il canale: stato, interpretazione, risultato o domanda.

**Cosa non fa.**
- Non interpreta: non conosce l'esistenza dei modelli linguistici.
- Non valida: delega al Validatore, senza replicarne alcun controllo.
- Non esegue: non conosce l'ORM.
- Non presenta: non produce viste né testo per l'utente.
- Non conosce il canale, oltre a registrarne l'identificativo.

**Note di progetto.** È il componente su cui grava il maggior rischio di accumulo: essendo l'unico ad avere la visione d'insieme, ogni funzionalità trasversale tende a essere collocata qui. La regola da applicare in revisione è netta: **l'Orchestratore contiene il flusso, mai la logica.** Se una decisione richiede di conoscere il significato di un filtro, di un permesso o di una vista, appartiene a un altro componente.

### 4.2 Catalogo Semantico

**Responsabilità.** Costruire, per una data richiesta e un dato utente, l'insieme dei riferimenti semantici che l'Interprete può nominare. Applica i permessi dell'utente e la selezione per dimensione (§7).

**Ingressi.** Identità dell'utente, stato corrente, testo della richiesta.
**Uscite.** Catalogo: entità, attributi, denominazioni, sinonimi, tipi, valori ammessi degli enumerati. **Solo metadati.**

**Cosa non fa.**
- Non legge il contenuto dei record: è la garanzia strutturale di V7.
- Non interpreta la richiesta: la selezione è deterministica (§7.4).
- Non decide quale riferimento è corretto: fornisce l'insieme, non la scelta.

**Note di progetto.** È simultaneamente il presidio di V2 — ciò che l'utente non può vedere non entra nel catalogo — e il tetto superiore dell'accuratezza: se il riferimento corretto non è nell'insieme, nessuna capacità del modello può recuperarlo. Le due proprietà convivono nello stesso componente, e per questo la sua **copertura** è una metrica di primo livello e non una statistica interna (§7.5).

### 4.3 Interprete

**Responsabilità.** Trasformare una richiesta in linguaggio naturale in una Busta di Interpretazione. È l'unico componente probabilistico e l'unico che conosce l'esistenza di un fornitore di modelli.

**Ingressi.** Richiesta, stato corrente in forma semantica, catalogo.
**Uscite.** Busta di Interpretazione, non validata.

**Cosa non fa.**
- Non accede all'ORM, al database, ai record. Non ne ha i mezzi.
- Non valida il proprio output: non è il componente che può giudicarlo.
- Non applica nulla allo stato.
- Non decide il tipo di vista quando non è espresso (§6.7 del DSL).
- Non risolve espressioni temporali né vaghezze (§9 del DSL).
- Non memorizza la conversazione: riceve lo stato, non la cronologia.

**Note di progetto.** Il vincolo *"non ha i mezzi"* è centrale e va reso vero dalla struttura: il modulo `nli_engine` non dichiara dipendenze verso i modelli di dati, e questo è verificabile automaticamente (§6.3). Un Interprete che *potrebbe* leggere i dati ma *non lo fa per convenzione* offre una garanzia qualitativamente inferiore, e in una revisione di conformità la differenza è tutta.

Internamente l'Interprete è a sua volta suddiviso (§8.2): una parte indipendente dal fornitore, che costruisce la richiesta e verifica la conformità allo schema; adattatori specifici, che parlano il protocollo di ciascun fornitore.

### 4.4 Validatore

**Responsabilità.** Applicare i cinque livelli di validazione del contratto. Respingere ogni busta non conforme e produrre un esito diagnostico utilizzabile sia dall'utente sia dal Registro.

**Ingressi.** Busta, stato corrente, catalogo, dizionario, parametri dell'installazione.
**Uscite.** Busta validata **oppure** esito di fallimento tipizzato per livello.

**Cosa non fa.**
- Non corregge, non normalizza, non completa. Una busta quasi valida è una busta non valida.
- Non decide se ritentare: la politica di ripristino appartiene all'Orchestratore.
- Non applica: la separazione fra giudizio ed effetto è deliberata.

**Note di progetto.** È il componente più importante del sistema dal punto di vista delle garanzie, e per questo deve essere **attraversato obbligatoriamente e non richiamabile facoltativamente**. In pratica: nessuna interfaccia dell'Applicatore accetta una busta che non porti l'evidenza della validazione avvenuta. È il modo per rendere V1 una proprietà dei tipi in gioco anziché una regola da ricordare.

La regola *"non corregge"* merita difesa perché è controintuitiva: correggere un errore piccolo sembra un servizio all'utente. In realtà rende il difetto invisibile alle metriche, e quindi permanente. Un errore corretto in silenzio non compare in nessun indicatore, e la sua causa non viene mai rimossa.

### 4.5 Applicatore

**Responsabilità.** Applicare le operazioni allo stato corrente producendo il nuovo stato, secondo la semantica di §4.5 del DSL: sequenzialità, atomicità, canonicalizzazione finale.

**Ingressi.** Busta validata, stato corrente.
**Uscite.** Nuovo stato in forma canonica, oppure fallimento atomico.

**Cosa non fa.**
- Non interpreta, non risolve, non esegue.
- Non conosce Odoo: opera su strutture semantiche.
- Non persiste: la persistenza è dell'Orchestratore.

**Note di progetto.** È il componente più semplice e con la più alta densità di test: funzione pura, senza effetti, senza dipendenze esterne. È anche il luogo in cui il determinismo del sistema è dimostrabile in modo diretto — stesso stato più stesse operazioni, stesso risultato — e va quindi mantenuto libero da qualunque dipendenza contestuale, incluse data e ora correnti.

### 4.6 Risolutore

**Responsabilità.** Tradurre lo stato semantico in Piano di Esecuzione: riferimenti in binding tecnici, espressioni temporali in intervalli assoluti, risolutori di vaghezza in valori, letterali di riferimento in record. Verificare i permessi su ogni elemento risolto.

**Ingressi.** Stato, dizionario, identità dell'utente, momento di riferimento, parametri di calendario dell'installazione.
**Uscite.** Piano di Esecuzione **oppure** richiesta di disambiguazione referenziale **oppure** errore di risoluzione diagnosticabile.

**Cosa non fa.**
- Non modifica lo stato: la risoluzione non è un'operazione (§11.3 del DSL).
- Non persiste il Piano: è effimero per costruzione.
- Non esegue.

**Note di progetto.** Opera a ogni esecuzione, mai una volta sola (§1.4 del DSL). È qui che il momento di riferimento entra nel sistema: l'Applicatore resta puro, il Risolutore è il solo componente consapevole del tempo. La separazione è ciò che consente di rieseguire il corpus di valutazione con un istante fissato senza artifici (§13.3).

È anche l'unico componente in cui il **fuso orario, il primo giorno della settimana e l'inizio dell'esercizio fiscale** hanno effetto. Concentrarli in un punto solo evita la classe di difetti più insidiosa dei sistemi di reportistica: due parti del sistema che calcolano *"questo mese"* in modo leggermente diverso.

### 4.7 Esecutore

**Responsabilità.** Eseguire il Piano tramite l'ORM di Odoo con l'identità dell'utente richiedente, e produrre l'azione di apertura della vista.

**Ingressi.** Piano di Esecuzione, identità dell'utente.
**Uscite.** Risultato: azione di vista, insieme di record, conteggi.

**Cosa non fa.**
- Non usa SQL diretto, in nessun percorso, nemmeno per conteggi o ottimizzazioni.
- Non eleva i privilegi, in nessun percorso, nemmeno per la cache o le statistiche.
- Non modifica dati: nel profilo di sola lettura non esiste percorso di scrittura.
- Non interpreta: riceve un Piano completamente determinato.

**Note di progetto.** È il componente più esposto agli aggiornamenti di Odoo, perché tocca ORM e sistema delle viste. Va mantenuto sottile e concentrato: la superficie di contatto con la piattaforma è il costo di manutenzione ricorrente del prodotto sull'orizzonte decennale (§13.4).

La regola *"nessuna elevazione di privilegi in nessun percorso"* è formulata in modo assoluto deliberatamente. Le violazioni di V2 non nascono mai da una decisione esplicita: nascono da un percorso secondario — un conteggio, una statistica, un precaricamento — in cui l'elevazione sembra innocua perché il risultato non viene mostrato.

### 4.8 Presentatore

**Responsabilità.** Produrre ciò che l'utente vede: la vista Odoo nativa e l'**interpretazione ispezionabile** in linguaggio non tecnico, con la provenienza e l'origine di ogni elemento.

**Ingressi.** Stato, risultato dell'esecuzione, dizionario per le denominazioni.
**Uscite.** Vista nativa e interpretazione, insieme.

**Cosa non fa.**
- Non produce una tabella propria: la vista è quella di Odoo, con tutte le sue funzioni.
- Non nasconde gli elementi inferiti: sono precisamente quelli che l'utente deve vedere.
- Non mostra nomi tecnici, in nessuna circostanza, incluse le condizioni di errore.

**Note di progetto.** Realizza V4, e la sua interfaccia lo rende strutturale: **non esiste modo di ottenere il risultato senza l'interpretazione**, perché sono la stessa uscita. Un'interfaccia che le restituisse separatamente aprirebbe la strada a un chiamante che usa solo la prima.

La regola *"nessun nome tecnico, incluse le condizioni di errore"* è quella che nella pratica viene violata per prima: i messaggi diagnostici sono il percorso naturale attraverso cui i nomi interni raggiungono l'utente, ed è anche il momento in cui l'utente è già in difficoltà.

### 4.9 Registro

**Responsabilità.** Conservare, per ogni interazione, l'evidenza completa: richiesta, catalogo fornito, busta, esito di validazione, stato risultante, tempi, costo, esito. Alimentare le metriche e il corpus di valutazione.

**Ingressi.** Eventi da tutti i componenti.
**Uscite.** Tracciabilità, metriche, candidati per il corpus e per l'arricchimento del dizionario.

**Cosa non fa.**
- Non conserva il contenuto dei record restituiti: conserva la domanda, non la risposta.
- Non influenza il flusso: la sua indisponibilità non blocca l'uso.

**Note di progetto.** La prima esclusione è una decisione di conformità con conseguenze pratiche: il registro può essere conservato a lungo e consultato ampiamente proprio perché non contiene dati aziendali. Conservare i risultati renderebbe il registro un archivio parallelo di dati riservati, con obblighi propri.

La seconda ha un'implicazione operativa: la scrittura sul registro non deve poter far fallire un'interazione. Un difetto nell'osservabilità non deve diventare un'interruzione del servizio — inversione di priorità frequente e sempre costosa.

---

## 5. Flussi

### 5.1 Flusso nominale

Utente: *"solo quelli confermati"*, su uno stato esistente.

```
 1. Canale          → Orchestratore    richiesta + identità + sessione
 2. Orchestratore   → Catalogo         stato + richiesta + identità
 3. Catalogo        → Orchestratore    catalogo (metadati, filtrato per permessi)
 4. Orchestratore   → Interprete       richiesta + stato + catalogo
 5. Interprete      → Orchestratore    Busta  [ unico passo probabilistico ]
 6. Orchestratore   → Validatore       busta + stato + catalogo
 7. Validatore      → Orchestratore    busta validata
 8. Orchestratore   → Applicatore      busta validata + stato
 9. Applicatore     → Orchestratore    nuovo stato canonico
10. Orchestratore   → [persiste lo stato]
11. Orchestratore   → Risolutore       stato + identità + istante
12. Risolutore      → Orchestratore    Piano
13. Orchestratore   → Esecutore        piano + identità
14. Esecutore       → Orchestratore    risultato
15. Orchestratore   → Presentatore     stato + risultato
16. Presentatore    → Canale           vista nativa + interpretazione
     ogni passo →   Registro
```

**Osservazione.** Dei sedici passi, uno solo è probabilistico. Gli altri quindici sono verificabili con test convenzionali e producono, a parità di ingressi, sempre lo stesso risultato. È la promessa del documento di visione resa struttura.

**Osservazione sui costi.** I passi 2–5 sono l'unica parte con latenza significativa (§10). I passi 6–16 si misurano in millisecondi. È la ragione per cui l'ottimizzazione ha un solo bersaglio sensato.

### 5.2 Flusso di chiarimento interpretativo

Diverge al passo 6: la Busta ha esito `clarification`.

```
 6. Validatore      → Orchestratore    busta valida, esito = clarification
 7. Orchestratore   → Presentatore     domanda + opzioni
 8. Presentatore    → Canale           domanda a scelta chiusa
 9. Utente sceglie un'opzione
10. Canale          → Orchestratore    opzione selezionata
11. Orchestratore   → Applicatore      operazioni pre-associate all'opzione
```

**Nessuna seconda interpretazione.** Le operazioni erano già nella busta e già validate (§11.2 del DSL). La scelta dell'utente è un evento deterministico: nessun costo aggiuntivo, nessuna latenza, nessuna possibilità che la risposta al chiarimento venga a sua volta fraintesa.

Lo stato non viene modificato finché l'utente non sceglie: un chiarimento senza risposta non lascia tracce nell'interrogazione.

### 5.3 Flusso di disambiguazione referenziale

Diverge al passo 12: il Risolutore trova più record corrispondenti al letterale.

```
12. Risolutore      → Orchestratore    disambiguazione referenziale + candidati
13. Orchestratore   → Presentatore     elenco candidati (solo quelli visibili all'utente)
14. Utente sceglie
15. Orchestratore   → Risolutore       stato + scelta di sessione
16. … prosegue dal passo 12 del flusso nominale
```

Due proprietà, entrambe conseguenze di §11.3 del DSL:

- **il modello non è coinvolto.** È un problema con risposta esatta e viene risolto in modo esatto;
- **lo stato non viene modificato.** La scelta vive nella sessione, non nell'interrogazione: un'interrogazione condivisa si risolve secondo i permessi di chi la esegue, non di chi l'ha creata.

### 5.4 Flusso di riesecuzione — senza modello

Interrogazione salvata, eseguita da un collega o dallo stesso utente giorni dopo.

```
 1. Canale          → Orchestratore    identificativo dello stato salvato
 2. Orchestratore   → [carica lo stato]
 3. Orchestratore   → Risolutore       stato + identità di CHI ESEGUE ORA + istante ATTUALE
 4. Risolutore      → Orchestratore    Piano
 5. … prosegue dal passo 13 del flusso nominale
```

**Nessun passo probabilistico. Nessun costo di modello. Nessuna latenza di rete.**

Questo flusso è il più importante dal punto di vista economico e da quello dell'affidabilità, e giustifica da solo diverse scelte prese altrove:

- è il motivo per cui il riuso delle interrogazioni salvate è un indicatore di sostenibilità (§17.4 del documento di visione): ogni riesecuzione è un'interazione a costo variabile nullo;
- è il motivo per cui il sistema resta utile quando il modello non è disponibile (§11);
- è il motivo per cui la risoluzione avviene a ogni esecuzione: *"questo mese"* significa il mese di adesso, e i permessi sono quelli di adesso.

### 5.5 Flusso di annullamento

```
 5. Interprete      → Orchestratore    Busta con operazione revert_last
 8. Orchestratore   → [ripristina lo stato precedente dalla storia]
 9. … prosegue dall'11
```

L'annullamento non ricalcola nulla: la storia degli stati è persistita e il ripristino è una selezione. È possibile perché lo stato è un oggetto e non una cronologia di messaggi — la verifica pratica della decisione D4.

### 5.6 Flusso di fallimento della validazione

```
 7. Validatore      → Orchestratore    fallimento tipizzato (livello, dettaglio)
 8. Orchestratore   → decide secondo il livello:
      livelli 1, 2, 4  → un solo ripristino: torna al passo 4 con l'errore strutturato
      livello 3        → esito verso l'utente con proposte dal catalogo
      livello 5        → esito verso l'utente con proposta di restringimento
 9. Se il ripristino fallisce → esito "non ho capito"
     sempre → Registro con classificazione del fallimento
```

**Il conteggio dei ripristini è a livello di turno, non di sessione**, e il limite è uno (§12.7 del DSL). Un fallimento dopo il ripristino non viene ritentato: viene registrato come difetto di sistema e comunicato all'utente in linguaggio comprensibile.

---

## 6. Confini e Regole di Dipendenza

### 6.1 Perché i confini vanno resi effettivi

Un'architettura descritta in un documento è una convenzione. Le convenzioni si erodono: sotto pressione, un componente importa ciò che gli serve e il confine scompare senza che nessuno lo decida.

Il criterio **C3** del DSL — *impossibilità strutturale al posto del divieto* — vale anche qui. Odoo offre lo strumento adatto: il grafo delle dipendenze fra moduli è **dichiarato** nei manifest e **verificabile automaticamente**. Un modulo che non dichiara una dipendenza non può usare ciò che quella dipendenza fornirebbe.

### 6.2 Il grafo delle dipendenze

```
                      ┌───────────┐
                      │ nli_core  │   contratto · stato · validazione
                      │           │   applicazione · esecuzione
                      └───────────┘
                       ▲    ▲    ▲
          ┌────────────┘    │    └──────────────┐
   ┌─────────────┐   ┌────────────┐    ┌──────────────────┐
   │nli_semantics│   │ nli_engine │    │ nli_observability│
   │ dizionario  │   │ interprete │    │ registro·metriche│
   │ catalogo    │   │ fornitori  │    └──────────────────┘
   └─────────────┘   └────────────┘
          ▲                  
          │           ┌────────────┐
          └───────────│  nli_web   │  chat · presentazione
                      └────────────┘
```

Regola generale: **le dipendenze puntano verso il nucleo, mai fra i moduli periferici.**

### 6.3 Regole di non dipendenza

Sono la parte normativa. Ciascuna riga è una proprietà da verificare automaticamente, non un'indicazione di stile.

| Vincolo | Regola | Vincolo di prodotto protetto |
|---|---|---|
| `nli_engine` → dati | **Non dipende** da modelli di dati Odoo oltre al contratto | **V7**: l'Interprete non può inviare dati che non possiede |
| `nli_engine` → `nli_semantics` | **Non dipende**: riceve il catalogo, non lo costruisce | Separazione fra chi conosce i dati e chi parla col modello |
| `nli_core` → `nli_engine` | **Non dipende**: il nucleo ignora l'esistenza dei modelli | **V5**: sostituibilità del fornitore |
| `nli_core` → `nli_web` | **Non dipende**: il nucleo ignora i canali | **P5**: indipendenza dal canale |
| Chiunque → librerie di fornitori | Solo `nli_engine` le importa | **V5**: verificabile con un controllo automatico |
| Chiunque → SQL diretto | Nessun modulo apre connessioni a PostgreSQL | **V3**: nessun aggiramento dell'ORM |
| Chiunque → elevazione privilegi | Nessun uso di contesti privilegiati nei percorsi di interrogazione | **V2**: nessun percorso privilegiato |
| Applicatore → tempo | Non accede a data e ora correnti | Determinismo e riproducibilità del corpus |

### 6.4 Come si verificano

Quattro controlli automatici, da inserire nella pipeline fin dal primo giorno. Sono economici da scrivere all'inizio e proibitivi da introdurre dopo, quando le violazioni esistono già e vanno prima sanate.

| Controllo | Cosa verifica |
|---|---|
| **Manifest** | Il grafo dichiarato in `__manifest__.py` corrisponde a §6.2 |
| **Importazioni** | Nessun modulo importa oltre le proprie dipendenze; solo `nli_engine` importa librerie di fornitori |
| **Sintattico** | Nessuna occorrenza di connessioni dirette a PostgreSQL o di contesti privilegiati nei percorsi di interrogazione |
| **Architetturale** | Test che verificano che i confini reggano: l'Applicatore è puro, il Validatore è attraversato, il Presentatore riceve sempre stato e risultato insieme |

**L'ultimo controllo è il più prezioso e il più trascurato.** Un test che verifica che l'Applicatore produca lo stesso risultato a distanza di tempo con gli stessi ingressi è un test dell'architettura, non della funzionalità: fallisce nel momento esatto in cui qualcuno introduce una dipendenza dal tempo, cioè quando la correzione costa ancora poco.

### 6.5 Confine con Odoo

I punti di contatto con la piattaforma sono concentrati in due componenti soltanto:

| Componente | Superficie |
|---|---|
| **Esecutore** | ORM: ricerca, lettura, aggregazione; sistema delle azioni e delle viste |
| **Catalogo** | Introspezione dei metadati: modelli, campi, tipi, permessi |

Nessun altro componente conosce Odoo. Il Validatore, l'Applicatore e l'Interprete opererebbero identicamente su un'altra piattaforma.

**È la superficie di aggiornamento del prodotto.** Ogni versione maggiore di Odoo richiede di verificare due componenti, non nove. Sull'orizzonte decennale dichiarato dal documento di visione, questa concentrazione è la principale difesa contro il costo ricorrente di manutenzione — e la ragione per cui i due componenti vanno mantenuti sottili anche quando sarebbe comodo arricchirli.

---

## 7. Il Catalogo Semantico

### 7.1 Perché è il componente più critico

Il documento sul DSL identifica in **RC3** il rischio che nessun miglioramento del modello può compensare: se il riferimento corretto non è nel catalogo fornito all'Interprete, l'interpretazione giusta è irraggiungibile.

Un'installazione Odoo 18 con i moduli applicativi principali espone centinaia di modelli e diverse migliaia di campi. Trasmetterli integralmente non è praticabile: né per dimensione, né per costo, né per qualità — un catalogo enorme peggiora l'interpretazione anche quando entra nel contesto.

Occorre quindi selezionare. **E la selezione è, di per sé, un secondo punto di potenziale non determinismo**: è la ragione per cui questo componente ha una sezione propria e metriche proprie.

### 7.2 La proprietà del contratto che rende il problema trattabile

Il DSL ammette **una sola entità per interrogazione** (§5.3 del DSL). Questa restrizione, adottata per contenere l'espressività, produce qui il suo beneficio maggiore: il problema della selezione si scompone in due problemi molto più piccoli.

| Sotto-problema | Dimensione | Difficoltà |
|---|---|---|
| **Quale entità** | Ordine delle centinaia | Piccolo: i nomi di entità sono pochi e distintivi |
| **Quali attributi** | Ordine delle decine, **una volta nota l'entità** | Piccolo: gli attributi di una singola entità entrano interamente nel contesto |

Il problema difficile — scegliere fra migliaia di campi — **non si presenta mai**, purché l'entità sia determinata per prima.

È un esempio di come un vincolo del contratto produca semplificazione architetturale a valle. Se il DSL avesse ammesso interrogazioni su più entità, questa scomposizione sarebbe impossibile e la selezione richiederebbe un componente di recupero semantico, con tutto ciò che comporta: un servizio in più, un indice da mantenere allineato, e un secondo componente probabilistico non misurato.

### 7.3 Strategia in due fasi

**Caso ordinario — l'entità è già nota** (lo stato ha un `target`, cioè dal secondo turno in poi):

il catalogo contiene tutti gli attributi dell'entità corrente, gli attributi raggiungibili con un salto di relazione limitati a quelli dichiarati nel dizionario, e l'elenco dei nomi di entità per consentire un cambio di argomento. **Nessuna selezione probabilistica, nessuna perdita di copertura.**

**Caso di apertura — l'entità non è nota** (primo turno o dopo un `reset`):

```
 A. Corrispondenza lessicale deterministica
    la richiesta viene confrontata con denominazioni e sinonimi del dizionario
    │
    ├─ corrispondenza univoca  → entità determinata, nessuna chiamata al modello
    │                            [percorso rapido: la maggioranza dei casi]
    │
    └─ nessuna o multipla      → B
 B. Interpretazione di sola entità
    catalogo ridotto ai soli nomi di entità (piccolo)
    │
    └─ entità determinata → C
 C. Interpretazione completa
    catalogo completo degli attributi dell'entità determinata
```

**Costo.** Un turno di apertura ambiguo richiede due chiamate al modello; tutti gli altri turni ne richiedono una. Il percorso rapido di A elimina la prima chiamata nella maggior parte dei casi di apertura, perché *"mostrami i clienti"* contiene la parola che il dizionario associa all'entità.

**Perché due fasi anziché un catalogo speculativo.** L'alternativa sarebbe includere gli attributi delle entità più probabili in un'unica chiamata. Costa una chiamata sola, ma reintroduce la selezione probabilistica sugli attributi e con essa il tetto di accuratezza non misurabile. La scelta a due fasi rende la selezione degli attributi **esatta per costruzione**: nota l'entità, il catalogo dei suoi attributi è completo.

Resta un punto di perdita possibile — la determinazione dell'entità in fase A/B — ma è un problema piccolo, isolato e misurabile separatamente.

### 7.4 Filtro per permessi

Prima di ogni altra considerazione, il catalogo viene filtrato sui permessi dell'utente: modelli non leggibili esclusi, campi non leggibili esclusi, campi resi invisibili da regole di accesso esclusi.

Il filtro precede la selezione, non la segue. L'ordine è normativo: un catalogo selezionato e poi filtrato potrebbe risultare più povero del previsto senza che nulla lo segnali, perché la selezione avrebbe speso il proprio budget su elementi poi rimossi.

### 7.5 Misura della copertura

**Metrica obbligatoria di primo livello**, da riportare sempre accanto all'accuratezza interpretativa:

> **Copertura del catalogo** = percentuale di casi in cui tutti i riferimenti necessari all'interpretazione corretta erano presenti nel catalogo fornito.

Il documento sul DSL lo argomenta in RC3 e vale la pena ripeterlo qui perché è una trappola diagnostica: un'accuratezza dell'87% con copertura del 92% e un'accuratezza dell'87% con copertura del 99,5% descrivono due situazioni completamente diverse. Nella prima, il margine di miglioramento non è nel modello e ogni lavoro sull'interpretazione è sprecato.

La misura è possibile perché il Registro conserva il catalogo fornito a ogni interazione (§4.9): dato un caso del corpus con la sua interpretazione attesa, verificare se i riferimenti necessari erano presenti è un controllo deterministico.

**Soglia di riferimento proposta: ≥ 99%.** La copertura deve essere quasi perfetta, perché è un limite superiore: ogni punto perduto qui è un punto che l'accuratezza non potrà mai recuperare.

### 7.6 Memorizzazione

Il catalogo è costoso da costruire — introspezione dei metadati e valutazione dei permessi — e cambia raramente. Va memorizzato con chiave composta da: identità dell'utente, entità, versione del dizionario, versione dei permessi.

**L'identità nella chiave non è negoziabile.** Un catalogo memorizzato per gruppo o per installazione tornerebbe a esporre riferimenti che un singolo utente non deve poter nominare. Sarebbe l'ottimizzazione che riapre V2, e appartiene alla stessa famiglia dei percorsi secondari citati in §4.7.

L'invalidazione avviene su tre eventi: modifica del dizionario, modifica dei permessi o dei gruppi dell'utente, aggiornamento dei moduli.

---

## 8. Indipendenza dal Fornitore del Modello

### 8.1 Il vincolo e la sua verifica

Il vincolo **V5** vieta che una capacità di prodotto dipenda in modo esclusivo da un singolo fornitore. L'obiettivo strategico **OS5** lo rende misurabile: sostituire il modello e conoscerne l'impatto in meno di una settimana.

L'architettura lo realizza con DA1: **un solo componente conosce l'esistenza dei fornitori**, e il controllo automatico sulle importazioni (§6.4) lo verifica a ogni build. La differenza fra un'indipendenza dichiarata e una verificata è precisamente questo controllo.

### 8.2 Struttura interna dell'Interprete

```
┌──────────────────── nli_engine ────────────────────┐
│                                                     │
│  Compositore              indipendente dal fornitore│
│  costruisce la richiesta a partire da               │
│  catalogo + stato + testo utente                    │
│                     │                               │
│                     ▼                               │
│  Adattatore di Fornitore        specifico           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │Fornitore │ │Fornitore │ │ Modello in        │   │
│  │    A     │ │    B     │ │ ambiente proprio  │   │
│  └──────────┘ └──────────┘ └──────────────────┘    │
│                     │                               │
│                     ▼                               │
│  Verificatore di Forma    indipendente dal fornitore│
│  conformità allo schema del contratto               │
│                                                     │
└─────────────────────────────────────────────────────┘
                      │  Busta
                      ▼  → Validatore (nli_core)
```

Il Compositore e il Verificatore non conoscono i fornitori. L'Adattatore non conosce il dominio: traduce una richiesta astratta nel protocollo di un fornitore e ne riporta l'output in forma normalizzata.

### 8.3 Cosa si può usare di un fornitore, e cosa no

| Utilizzabile | Non ammesso |
|---|---|
| Generazione vincolata a uno schema — è **raccomandata**, riduce i fallimenti di validazione ai livelli 1–2 | Che la validità del contratto **dipenda** da quel meccanismo |
| Memorizzazione del contesto lato fornitore, per costo e latenza | Che il funzionamento dipenda dalla sua disponibilità |
| Modalità di elaborazione differita per il ricalcolo del corpus | Che il percorso interattivo la richieda |

La distinzione operativa: **sfruttare una capacità è legittimo, dipenderne non lo è.** La prova pratica è un test che esegue l'intero percorso con l'adattatore più povero disponibile — nessuna generazione vincolata, nessuna memorizzazione — e verifica che il sistema resti corretto, pagando solo in qualità e costo.

### 8.4 Procedura di sostituzione del modello

È una procedura operativa, non un progetto:

1. il nuovo modello viene configurato come adattatore alternativo;
2. il corpus di valutazione viene eseguito su entrambi, con lo stesso istante di riferimento e lo stesso dizionario;
3. si confrontano accuratezza complessiva, accuratezza per sezione, tasso di chiarimento, tasso di fallimento della validazione, latenza e costo;
4. si ricalibrano le soglie di confidenza sul nuovo modello (§10.5 del DSL): **non sono trasferibili**;
5. si decide sulla base dei dati.

Il passo 4 è quello che viene dimenticato più spesso. La confidenza dichiarata da modelli diversi non è comparabile, e riutilizzare soglie tarate su un modello precedente produce o troppi chiarimenti o troppo pochi — in entrambi i casi un peggioramento che sembra dovuto al modello e non lo è.

### 8.5 Modello in ambiente controllato

L'architettura ammette un adattatore verso un modello eseguito nell'infrastruttura del cliente, senza alcuna modifica agli altri componenti: è la decisione **D8** del documento di visione, ed è l'accesso ai segmenti regolamentati.

Vale la pena notare che l'assunzione **A6** rende questa opzione più praticabile di quanto sarebbe altrimenti: poiché il modello riceve solo metadati e la frase dell'utente, il compito richiesto è la traduzione in un contratto strutturato a vocabolario chiuso — un compito alla portata di modelli sensibilmente più piccoli di quelli necessari a ragionare sui dati.

---

## 9. Stato e Sessione

### 9.1 Dove vive lo stato

**In Odoo, come record.** Non nella sessione web, non in memoria, non in una cache, non nel client.

| Alternativa | Perché scartata |
|---|---|
| Sessione web | Perso alla scadenza; non condivisibile; non riprendibile da altro canale; non tracciabile |
| Cache in memoria | Perso al riavvio; non condivisibile fra i processi worker di Odoo |
| Stato nel client | Non condivisibile; manipolabile; assente sui canali senza interfaccia (email, API) |
| Archivio dedicato | Un componente in più da gestire per dieci anni, senza benefici rispetto al database già presente |

La persistenza come record è ciò che rende possibili, senza alcun meccanismo aggiuntivo, cinque proprietà richieste dal documento di visione: ripresa a distanza di tempo, cambio di canale, condivisione, annullamento, tracciabilità.

### 9.2 Le entità concettuali

Descritte per responsabilità, non come schema — la modellazione dei dati appartiene alla fase di realizzazione.

| Entità | Ruolo | Ciclo di vita |
|---|---|---|
| **Sessione** | Contesto conversazionale: utente, canale, stato corrente | Chiusa per inattività |
| **Stato** | Un'interrogazione in un dato momento, in forma semantica | Immutabile una volta creato |
| **Turno** | Richiesta, busta, esito di validazione, stato prodotto | Conservato per il periodo di ritenzione |
| **Interrogazione salvata** | Uno stato promosso a oggetto riutilizzabile, con nome e proprietario | Finché il proprietario la conserva |

**Gli stati sono immutabili.** Un'operazione non modifica lo stato: ne produce uno nuovo che riferisce il precedente. Ne discendono l'annullamento come selezione anziché come ricalcolo, la storia completa senza strutture aggiuntive, e la tracciabilità esatta di cosa l'utente stava guardando in ogni momento.

Il costo è la crescita del numero di record, governata dalla ritenzione (§9.3). È un costo accettabile: uno stato è un oggetto piccolo, e la proprietà che compra — nessuna modifica distruttiva, mai — è precisamente ciò che rende il sistema diagnosticabile a posteriori.

### 9.3 Ritenzione

| Entità | Ritenzione proposta | Motivazione |
|---|---|---|
| Stati intermedi | 30 giorni | Coprono l'annullamento e la ripresa; oltre, non hanno uso |
| Turni | 12 mesi | Alimentano metriche, analisi dei fraintendimenti e corpus |
| Interrogazioni salvate | Illimitata | Sono oggetti dell'utente |
| Registro senza contenuti | 24 mesi | Tracciabilità e analisi delle tendenze |

La ritenzione lunga è sostenibile **perché nulla di tutto ciò contiene dati aziendali**: sono domande, non risposte (§4.9). Se il registro conservasse i risultati, ogni riga di questa tabella diventerebbe una decisione di conformità anziché una scelta di dimensionamento.

### 9.4 Ripresa e cambio di canale

Poiché lo stato è un record e non contiene nulla di specifico del canale, la ripresa è banale: un'altra sessione carica lo stesso stato.

*"Mandami su Teams l'interrogazione di ieri"* non richiede alcun meccanismo dedicato: richiede un identificativo di stato e un adattatore di canale. **È la verifica architetturale dell'indipendenza dal canale**, ed è il motivo per cui il documento di visione raccomanda di attivare un secondo canale già in Fase 2: è la prova che si può fare.

### 9.5 Condivisione

Un'interrogazione condivisa è un riferimento a uno stato, non una copia dei risultati.

Chi la esegue ottiene ciò che **i propri** permessi consentono, al momento in cui la esegue, con le date risolte **adesso**. Due utenti che aprono la stessa interrogazione salvata possono legittimamente vedere risultati diversi: è il comportamento corretto, e va comunicato come tale nell'interfaccia — un utente che confronta il proprio schermo con quello di un collega deve poter capire perché differiscono.

### 9.6 Concorrenza

Due canali attivi sulla stessa sessione — chat aperta sul desktop e applicazione mobile — possono produrre turni concorrenti.

Regola: **l'applicazione delle operazioni è serializzata sulla sessione.** Una busta si applica allo stato che era corrente al momento in cui è stata richiesta l'interpretazione; se nel frattempo lo stato è cambiato, la busta viene respinta e reinterpretata sullo stato aggiornato.

Il costo è una reinterpretazione in un caso raro. L'alternativa — applicare operazioni pensate per uno stato diverso da quello effettivo — produrrebbe un'interrogazione che nessuno ha chiesto: la forma più difficile da diagnosticare del rischio R1, perché non è riconducibile ad alcuna singola richiesta dell'utente.

---

## 10. Prestazioni

### 10.1 Il budget

Il documento di visione fissa una latenza percepita al 95° percentile di **3 secondi**. Ripartizione stimata di un turno nominale:

| Passo | Tempo atteso | Quota |
|---|---|---|
| Costruzione del catalogo (memorizzato) | 5–20 ms | trascurabile |
| **Interpretazione (modello)** | **600–2500 ms** | **dominante** |
| Validazione | < 5 ms | trascurabile |
| Applicazione | < 5 ms | trascurabile |
| Risoluzione | 10–50 ms | marginale |
| Esecuzione ORM | 50–500 ms | secondaria |
| Presentazione | < 50 ms | trascurabile |

**Il modello è dal 70% al 90% del tempo totale.** Ogni ottimizzazione altrove è irrilevante finché questa proporzione regge, e ogni discussione sulle prestazioni che non riguardi l'interpretazione o l'esecuzione ORM è tempo mal speso.

### 10.2 Le tre leve efficaci

**Leva 1 — Evitare del tutto la chiamata.** È l'unica ottimizzazione di un ordine di grandezza. Tre percorsi la realizzano: la riesecuzione di interrogazioni salvate (§5.4), il percorso rapido lessicale nella determinazione dell'entità (§7.3), e la modifica dell'interpretazione dall'interfaccia (§11.3). Nessuno dei tre richiede il modello.

**Leva 2 — Contesto compatto.** Lo stato invece della cronologia (decisione D4) mantiene la richiesta di dimensione costante anche nelle conversazioni lunghe. Senza di essa, latenza e costo crescerebbero a ogni turno: la ventesima domanda di una sessione costerebbe molte volte la prima.

**Leva 3 — Catalogo compatto.** La strategia a due fasi (§7.3) trasmette gli attributi di una sola entità anziché uno schema esteso. Riduce simultaneamente latenza, costo e — cosa più rilevante — migliora l'accuratezza: un catalogo più piccolo e pertinente produce interpretazioni migliori.

Le tre leve sono conseguenze di decisioni prese per ragioni di correttezza. È un buon segnale: quando le scelte fatte per l'affidabilità migliorano anche le prestazioni, l'impianto è coerente.

### 10.3 Il problema dei worker

Una chiamata al modello dura secondi. Nel modello di esecuzione di Odoo, una richiesta HTTP occupa un worker per tutta la sua durata: con la configurazione predefinita, poche conversazioni contemporanee saturerebbero il server e degraderebbero **l'intero ERP**, non solo il livello conversazionale.

È un rischio operativo di prima grandezza e va affrontato nell'architettura, non nel dimensionamento.

**Decisione: l'interpretazione non blocca un worker.**

```
richiesta utente
   │
   ▼  il worker registra il turno e si libera immediatamente
[coda]
   │
   ▼  elaborazione fuori dal ciclo di richiesta
Interprete → Validatore → … → risultato persistito
   │
   ▼  notifica al client tramite il bus di Odoo
interfaccia aggiorna
```

Tre benefici, uno dei quali non evidente:

- **la saturazione dei worker è esclusa per costruzione**: il livello conversazionale non può compromettere la disponibilità dell'ERP;
- **nessun limite di durata da aggirare**: le scadenze delle richieste HTTP non si applicano;
- **l'attesa diventa leggibile**: il sistema può comunicare a che punto è, come richiede §10.5 del documento di visione. Un'attesa spiegata è percepita come sensibilmente più breve di un'attesa muta di pari durata.

Il costo è una latenza aggiuntiva di decine di millisecondi per l'accodamento e la notifica: trascurabile rispetto ai secondi dell'interpretazione, e ampiamente ripagato dalla protezione della disponibilità.

> **Il meccanismo completo è specificato in `05-esecuzione-asincrona.md`**, verificato sui sorgenti di Odoo 18: dispatcher su `ir.cron` con pool di thread interno, risveglio via `pg_notify`, notifica su bus servito dal processo gevent, e i cinque limiti di carico senza i quali la coda si limiterebbe a spostare la saturazione. La decisione D20 è lì articolata in D20a–D20f.

### 10.4 Memorizzazione delle interpretazioni

Un'interpretazione può essere riusata quando **testo della richiesta, impronta del catalogo e forma canonica dello stato di partenza** coincidono.

La chiave ha una proprietà di sicurezza che vale la pena rendere esplicita: poiché il catalogo è costruito sui permessi dell'utente (§7.4), **due utenti condividono un'impronta di catalogo solo se hanno gli stessi permessi sull'entità**. Il riuso fra utenti diversi è quindi possibile senza violare V2 — non perché venga controllato, ma perché la chiave lo esclude.

Attenzione a ciò che si memorizza: **l'interpretazione, mai il risultato.** I risultati dipendono dai dati e dai permessi al momento dell'esecuzione, e una loro memorizzazione condivisa sarebbe la violazione di V2 che §4.7 indica come tipica.

### 10.5 Esecuzione

Il limite obbligatorio nel contratto (§5.8 del DSL) elimina la classe di problemi più grave: nessuna interrogazione può tentare di recuperare un numero illimitato di record.

Due accortezze restano a carico dell'Esecutore: conteggio prima del recupero, per poter avvisare l'utente che la richiesta produce troppi risultati prima di produrli; e lettura dei soli attributi presenti nello stato, che è possibile proprio perché lo stato li elenca esplicitamente.

---

## 11. Degradazione

### 11.1 Modalità di guasto e comportamento richiesto

| Guasto | Comportamento | Il sistema resta usabile? |
|---|---|---|
| Modello lento | Attesa leggibile; oltre una soglia, avviso esplicito | Sì |
| Modello non disponibile | Messaggio chiaro; interrogazioni salvate e modifica dell'interpretazione restano disponibili | **Sì, parzialmente** |
| Quota o limite di frequenza superati | Come sopra, con indicazione della natura temporanea | **Sì, parzialmente** |
| Output non conforme allo schema | Un ripristino, poi *"non ho capito"* | Sì |
| Dizionario incompleto | Chiarimento o proposta di alternative dal catalogo | Sì |
| Odoo lento | Il livello conversazionale non peggiora la situazione (§10.3) | Come Odoo |
| Registro non disponibile | Interazione completata, evidenza persa | Sì |

### 11.2 Cosa continua a funzionare senza il modello

È l'elenco che rende concreta la decisione DA5:

- **eseguire e rieseguire interrogazioni salvate**: percorso interamente deterministico (§5.4);
- **modificare l'interpretazione dall'interfaccia**: rimuovere un filtro, cambiare vista, aggiungere una colonna;
- **usare Odoo normalmente**: il livello conversazionale è additivo e la sua assenza non toglie nulla.

Il messaggio corretto all'utente non è *"il servizio non è disponibile"* ma *"in questo momento non riesco a capire le richieste scritte; le tue interrogazioni salvate funzionano"*. È una differenza di comunicazione che riflette una differenza reale di capacità.

### 11.3 L'interpretazione modificabile

L'interpretazione ispezionabile (V4) non serve solo a mostrare: ogni suo elemento è **azionabile**. Rimuovere una condizione, cambiare l'ordinamento, cambiare vista, togliere una colonna sono operazioni che l'interfaccia costruisce direttamente, senza passare dall'Interprete.

Nasce come requisito di esperienza — §10.3 del documento di visione: il fraintendimento deve costare due secondi — e si rivela un percorso di resilienza: **la parte deterministica del prodotto è utilizzabile per intero anche quando la parte probabilistica non risponde.**

È anche, in condizioni normali, la Leva 1 di §10.2: la correzione fatta dall'interfaccia è istantanea e a costo nullo.

### 11.4 Protezione dal guasto persistente

Un circuito di protezione sull'adattatore del fornitore evita di accumulare richieste verso un servizio che non risponde: superata una soglia di fallimenti, il sistema smette di tentare, comunica lo stato e riprende gradualmente.

Senza questo meccanismo, un guasto del fornitore si traduce in code crescenti, attese lunghe e infine timeout a cascata: l'utente attende trenta secondi per ricevere un errore che era prevedibile al primo tentativo.

---

## 12. Sicurezza

### 12.1 Identità ed esecuzione

Ogni esecuzione avviene nell'ambiente Odoo con l'identità dell'utente richiedente. Nessun percorso eleva i privilegi. Nessun servizio esterno accede ai dati.

Ne consegue che **regole di accesso, permessi sui campi e regole sui record continuano a valere senza che il prodotto debba conoscerli**. Il livello conversazionale non reimplementa il modello di sicurezza di Odoo: lo attraversa.

**Verifica architetturale.** Il controllo sintattico di §6.4 cerca l'uso di contesti privilegiati nei percorsi di interrogazione. Il valore del controllo non sta nel primo giorno — quando nessuno li userebbe — ma nel trentesimo mese, quando qualcuno risolverà un problema di prestazioni nel modo più rapido.

### 12.2 Il catalogo come frontiera di autorizzazione

Ciò che l'utente non può vedere non entra nel catalogo, quindi non entra nello spazio delle interpretazioni possibili (§7.4).

È una difesa qualitativamente diversa dal filtraggio dei risultati: agisce prima dell'interpretazione anziché dopo l'esecuzione, e non produce trasferimento di informazione per negazione — l'utente non riceve un rifiuto che gli rivelerebbe l'esistenza di ciò che non deve conoscere.

Resta il controllo in fase di risoluzione (§4.6): due difese indipendenti, come deve essere per una proprietà di questa importanza.

### 12.3 Cosa esce effettivamente dal perimetro

Verso il fornitore del modello viaggiano due cose, e due soltanto:

1. la **frase dell'utente**;
2. il **catalogo**: metadati di struttura e denominazioni.

Non i record, non i risultati, non i conteggi, non gli identificativi (assunzione A6, vincolo V7).

**Un punto da non nascondere.** La frase dell'utente è scritta dall'utente e può contenere informazioni riservate: un nome, un importo, un riferimento a una trattativa. È inevitabile — è la richiesta stessa — ma va gestito come un fatto e non ignorato:

- condizioni contrattuali con il fornitore che escludano la conservazione e l'uso per addestramento;
- opzione di modello in ambiente controllato per i clienti che non accettano il trasferimento (§8.5);
- dichiarazione esplicita nella documentazione destinata ai clienti.

Presentare il sistema come se nulla uscisse dal perimetro sarebbe inesatto e verrebbe smentito alla prima valutazione fornitori seria.

### 12.4 Iniezione tramite contenuti

Nel profilo di sola lettura il vettore è chiuso alla radice: i contenuti dei record non raggiungono il modello (§13.4 del DSL).

Due punti restano sotto sorveglianza architetturale.

**Il dizionario è un ingresso verso il modello.** Denominazioni e sinonimi arrivano all'Interprete attraverso il catalogo. Sono contenuti curati, ma l'arricchimento automatico previsto dalla Fase 2 crea un percorso dal linguaggio degli utenti al contesto del modello. L'arricchimento automatico richiede quindi validazione dei contenuti e, per le voci che definiscono metriche, approvazione umana.

**La difesa strutturale regge comunque.** Qualunque cosa il modello produca è una Busta, che attraversa i cinque livelli e può nominare solo il catalogo di *quell'* utente. Un'iniezione riuscita non può produrre più di un'interrogazione valida su dati che l'utente può già vedere. È la proprietà da preservare quando la Fase 6 introdurrà la comprensione documentale, ed è la ragione per cui nessuna evoluzione deve consentire all'Interprete di produrre qualcosa che non sia una Busta validata.

### 12.5 Segreti

Le credenziali dei fornitori risiedono nella configurazione dell'ambiente, non nel database e non nel codice. Non compaiono nel registro, nei messaggi di errore né nelle risposte. La rotazione non richiede modifiche al codice.

Il repository usa già `.env` con `.env.example` versionato: la convenzione esiste e va estesa, non sostituita.

### 12.6 Tracciabilità

Il Registro conserva, per ogni interazione: chi, quando, da quale canale, cosa ha chiesto, quale catalogo ha ricevuto, come è stato interpretato, cosa è stato validato, quale stato è stato prodotto, cosa è stato eseguito, quanto è costato.

Non conserva i risultati (§4.9), il che rende la conservazione prolungata sostenibile e la consultazione ampia.

Con la provenienza (§10.3 del DSL), la ricostruzione a posteriori arriva al livello utile: non solo *cosa* è stato frainteso, ma **quali parole** lo hanno causato.

---

## 13. Osservabilità e Valutazione

### 13.1 Perché è parte dell'architettura

Il documento di visione fa della misura continua il cancello verso ogni ampliamento d'ambito. Una misura che dipende da strumenti costruiti a posteriori non è continua: è un'attività periodica che viene rinviata.

**L'osservabilità è quindi un componente**, presente dal primo giorno, non uno strato aggiunto quando servirà dimostrare qualcosa.

### 13.2 Cosa si misura

| Famiglia | Indicatori | Origine |
|---|---|---|
| **Interpretazione** | Accuratezza complessiva e per sezione; risoluzione al primo tentativo; tasso di chiarimento; tasso di fallimento per livello di validazione; tasso di ripristino | Corpus + Registro |
| **Catalogo** | **Copertura** (§7.5); dimensione media; tasso di uso del percorso rapido | Registro |
| **Esperienza** | Passi per risultato; tasso di correzione dell'interpretazione; abbandono; risultati vuoti | Registro |
| **Operative** | Latenza per passo; costo per interazione; disponibilità; profondità della coda | Registro |
| **Adozione** | Utenti attivi; interrogazioni per utente; riuso delle salvate | Registro |

**Accuratezza e copertura vanno sempre riportate insieme** (§7.5). Una dashboard che mostri l'accuratezza da sola induce sistematicamente la diagnosi sbagliata.

### 13.3 Dal registro al corpus

```
interazioni reali
   │
   ├─ chiarimenti risolti        ─┐
   ├─ correzioni dell'utente      │
   ├─ fallimenti di livello 3     ├─▶ candidati ─▶ annotazione ─▶ CORPUS
   ├─ riformulazioni immediate    │                  umana
   └─ esiti out_of_scope         ─┘                              │
                                                                  ▼
                                              esecuzione a ogni rilascio
                                              istante fissato · dizionario fissato
```

**Tre parametri vanno congelati** perché il confronto fra esecuzioni abbia significato: l'istante di riferimento — altrimenti `current_month` cambia esito con il calendario; la versione del dizionario — altrimenti un arricchimento si confonde con un miglioramento del modello; la versione del contratto.

Questa riproducibilità è possibile per una ragione architetturale precisa: **il Risolutore è il solo componente consapevole del tempo** (§4.6). Fissare l'istante è un parametro di quel componente, non un artificio che attraversa il sistema.

**L'annotazione umana è indispensabile.** Un caso entra nel corpus con l'interpretazione **corretta**, che solo una persona che conosce il dominio può stabilire. Un corpus popolato automaticamente con ciò che il sistema ha prodotto misurerebbe la stabilità, non la correttezza — e mostrerebbe risultati eccellenti mentre il prodotto sbaglia in modo costante.

### 13.4 La regressione come cancello

Il documento di visione non ammette regressioni fra rilasci. Perché sia applicabile e non solo dichiarato:

- il corpus si esegue automaticamente a ogni modifica di prompt, modello, dizionario o contratto;
- l'esito è un confronto con la misurazione precedente, non un valore assoluto;
- una regressione **blocca il rilascio**, come un test fallito;
- il confronto è per sezione: una regressione sui raggruppamenti compensata da un miglioramento sui filtri resta una regressione.

L'ultimo punto è quello che distingue una verifica seria da una formale. Le metriche aggregate nascondono i peggioramenti localizzati, ed è proprio nei peggioramenti localizzati che si annidano i fraintendimenti plausibili.

### 13.5 Analisi dei fraintendimenti

Il confronto per sezione (§14.5 del DSL) indica dove intervenire; la provenienza indica su cosa.

L'analisi combina i due: raggruppare i fraintendimenti per sezione e per frammento di testo produce l'elenco ordinato delle espressioni che il sistema comprende peggio — l'ingresso diretto del lavoro sul Dizionario Semantico previsto dalla Fase 2.

---

## 14. Struttura dei Moduli e Distribuzione

### 14.1 Collocazione nel repository

```
custom_addons/
├── lead/                    esistente
├── ui_brand_tokens/         esistente — token di design
├── ui_theme_engine/         esistente — motore dei temi
├── ui_premium_shell/        esistente — shell dell'interfaccia
├── nli_core/                contratto · stato · validazione · applicazione · esecuzione
├── nli_semantics/           dizionario · catalogo · risoluzione
├── nli_engine/              interprete · adattatori di fornitore
├── nli_web/                 canale chat · presentazione
└── nli_observability/       registro · metriche · corpus
```

### 14.2 Perché cinque moduli

La suddivisione non è organizzativa: **è il meccanismo con cui i confini di §6.3 diventano verificabili.** In Odoo il grafo delle dipendenze è dichiarato e controllabile automaticamente; separare i moduli è ciò che rende impossibile — non sconsigliato — che l'Interprete acceda ai dati.

Tre benefici secondari, tutti reali:

- **installazione selettiva**: un cliente che voglia solo l'esecuzione di interrogazioni salvate non installa `nli_engine`, e ottiene un sistema senza alcuna dipendenza esterna;
- **sostituibilità**: `nli_engine` è rimpiazzabile per intero senza toccare il resto;
- **conformità dimostrabile**: mostrare a un cliente che il modulo che parla col fornitore non dichiara alcuna dipendenza verso i dati è un argomento verificabile, non una rassicurazione.

Il costo è la disciplina nel mantenere le interfacce fra moduli. È un costo che va pagato deliberatamente: cinque moduli mal separati sono peggio di uno solo, perché aggiungono attrito senza aggiungere garanzie.

### 14.3 Convenzione di denominazione

Il prefisso `nli_` è coerente con l'impianto esistente — `ui_` per la famiglia dell'interfaccia — e rende immediatamente leggibile l'appartenenza.

È inoltre l'occasione per accogliere la raccomandazione §18.6 del documento di visione: `nli` sta per *Natural Language Interaction*, e descrive il prodotto per ciò che è, evitando il termine *agent* che ne descrive l'opposto. Se la denominazione commerciale cambierà, il prefisso tecnico resta appropriato.

### 14.4 L'Interprete: nello stesso processo o servizio separato

La domanda si pone perché `nli_engine` è l'unico componente con dipendenze esterne e con un profilo di carico diverso dagli altri.

| Opzione | Valutazione |
|---|---|
| **Nel processo Odoo, dietro l'adattatore** | **Scelta per la prima release.** Nessuna infrastruttura aggiuntiva; distribuzione, configurazione e diagnostica invariate |
| Servizio separato | Rinviata: aggiunge un servizio da gestire, un protocollo, una modalità di guasto e un salto di rete, per benefici che oggi non servono |

**La decisione è reversibile a basso costo**, e questo è ciò che la rende accettabile: l'accodamento di §10.3 disaccoppia già l'interpretazione dal ciclo di richiesta, e l'Adattatore è già un confine. Estrarre l'Interprete in un servizio separato, se un giorno servirà — scalabilità indipendente, isolamento più stretto, esecuzione di un modello proprio — significa cambiare l'implementazione di un'interfaccia esistente, non ridisegnare il sistema.

È l'applicazione del principio di non distribuire prematuramente: la distribuzione è un costo operativo permanente, e va pagata quando produce un beneficio, non quando sembra più moderna.

### 14.5 Ambienti

La distribuzione esistente — `docker-compose.yml`, `.dev`, `.prod` con Odoo 18.0 e PostgreSQL 16 — è sufficiente. Il livello conversazionale aggiunge configurazione, non servizi:

| Parametro | Ambito |
|---|---|
| Fornitore e modello attivo | Ambiente |
| Credenziali | Ambiente, mai nel database |
| Soglie di confidenza | Installazione, calibrate sul modello attivo |
| Limite predefinito e massimo dei record | Installazione |
| Budget di complessità | Installazione |
| Ritenzione | Installazione |

**Nessun servizio nuovo nella prima release.** È una proprietà da difendere: ogni servizio aggiunto è un elemento da gestire, aggiornare, mettere in sicurezza e diagnosticare per l'intero orizzonte del prodotto.

### 14.6 Integrazione con l'interfaccia esistente

`nli_web` introduce il canale chat dentro l'interfaccia Odoo. Il repository contiene già `ui_brand_tokens`, `ui_theme_engine` e `ui_premium_shell`: la chat e l'interpretazione ispezionabile **usano quei token e quel motore dei temi**, non uno stile proprio.

Non è una questione estetica. Il documento di visione richiede che il prodotto sia additivo e incorporato nel flusso di lavoro (§4.6): un livello conversazionale che appaia visivamente estraneo all'interfaccia viene percepito come uno strumento separato, ed è precisamente il fallimento descritto dal rischio R3.

**Dipendenza da dichiarare:** `nli_web` dipende da `ui_brand_tokens` se la famiglia `ui_*` è installata, e degrada agli stili standard di Odoo altrimenti. Il livello conversazionale deve poter essere installato anche senza l'interfaccia premium.

---

## 15. Alternative Valutate e Scartate

### 15.1 Interprete con accesso ai dati

L'approccio più diffuso: il modello accede ai record per comprendere meglio il contesto — vedere i valori esistenti di un campo, i nomi dei clienti, gli stati effettivamente usati.

**Scartata.** Viola V7 e A6; espone dati riservati a un servizio esterno; riapre il vettore di iniezione tramite contenuti (§12.4); introduce obblighi di conformità che precludono interi segmenti di mercato.

Il beneficio che prometterebbe — conoscere i valori realmente presenti — si ottiene senza dati: **il catalogo contiene i valori ammessi degli attributi enumerati** (§4.2), che sono metadati di schema, non contenuto. Per gli attributi liberi la risoluzione referenziale (§5.3) risolve il problema in modo esatto e deterministico, senza mostrare nulla al modello.

### 15.2 Un componente per servizio

Ogni componente come servizio autonomo, comunicazione via rete.

**Scartata.** Ogni salto di rete aggiunge latenza a un budget già dominato dal modello; ogni servizio aggiunge una modalità di guasto e un costo operativo permanente; nessuno dei componenti deterministici ha un profilo di carico che giustifichi una scalabilità indipendente — sono operazioni di millisecondi.

I confini si ottengono con la struttura dei moduli (§6.3), che li rende verificabili senza pagare il costo della distribuzione. È l'errore opposto a quello di non separare affatto, e ugualmente costoso.

### 15.3 Motore di ricerca vettoriale per il catalogo

Un indice semantico degli attributi per selezionare i più pertinenti alla richiesta.

**Scartata**, e vale la pena spiegare perché la tentazione è forte: è la soluzione standard al problema della selezione. Ma il problema, nella forma in cui si presenta qui, non esiste: il vincolo di entità singola del DSL lo scompone in due problemi piccoli (§7.2), e una volta nota l'entità **i suoi attributi entrano interamente nel contesto**.

Adottare un indice vettoriale significherebbe aggiungere un servizio da mantenere allineato ai metadati, e reintrodurre un secondo componente probabilistico — non misurato — nel percorso critico. Costo alto, rischio nuovo, beneficio nullo.

È l'esempio più chiaro di come una restrizione del contratto produca semplificazione architetturale: la decisione di ammettere una sola entità, presa per contenere l'espressività, elimina qui un intero sottosistema.

### 15.4 Viste proprietarie invece delle viste native

Rendere i risultati in una tabella costruita dal prodotto.

**Scartata.** Contraddice §4.6 del documento di visione: il risultato deve essere una vista Odoo autentica, con esportazione, filtri, azioni e apertura del record. Una tabella propria costringerebbe a reimplementare per anni funzionalità già esistenti, e trasformerebbe il prodotto da additivo a sostitutivo — l'ingresso diretto nel rischio R3.

### 15.5 Memorizzazione dei risultati

Riusare i risultati di interrogazioni identiche.

**Scartata.** I risultati dipendono dai permessi e dai dati al momento dell'esecuzione. Una cache condivisa violerebbe V2; una cache per utente e a validità brevissima avrebbe un tasso di riuso trascurabile, dato che gli utenti raramente ripetono la stessa interrogazione entro pochi secondi.

Si memorizza l'interpretazione (§10.4), che non dipende dai dati.

### 15.6 Alternative argomentate altrove

| Alternativa | Sezione |
|---|---|
| Stato in sessione, in memoria o nel client | §9.1 |
| Coda di messaggi fra i componenti deterministici | §3.4 |
| Interprete come servizio separato fin da subito | §14.4 |
| Catalogo speculativo in una sola chiamata | §7.3 |
| Modulo unico anziché cinque | §14.2 |

---

## 16. Rischi Architetturali

### RA1 — L'Orchestratore accumula logica

**Descrizione.** Essendo l'unico componente con la visione d'insieme, attrae ogni funzionalità trasversale finché non contiene la maggior parte delle decisioni del sistema.
**Impatto.** Alto sul lungo periodo: i confini restano dichiarati ma svuotati; la testabilità dei singoli componenti diventa illusoria.
**Mitigazione.** La regola *"il flusso, mai la logica"* (§4.1) applicata in revisione; test architetturali che verificano la purezza dei componenti a valle.
**Segnale anticipatore.** L'Orchestratore cresce più rapidamente degli altri componenti; le sue prove richiedono simulacri di tutto il sistema.

### RA2 — I confini non vengono resi effettivi

**Descrizione.** I controlli automatici di §6.4 vengono rinviati; i confini restano una convenzione documentale.
**Impatto. Critico.** È il meccanismo attraverso cui V2, V5 e V7 decadono senza che nessuno lo decida. Una violazione scoperta al ventiquattresimo mese costa una riprogettazione.
**Mitigazione.** I quattro controlli fanno parte della prima consegna, prima di qualunque funzionalità. Sono economici quando non ci sono violazioni da sanare.
**Segnale anticipatore.** Il primo controllo disattivato "temporaneamente".

### RA3 — Saturazione dei worker

**Descrizione.** L'interpretazione viene realizzata in modo sincrono nel ciclo di richiesta.
**Impatto. Critico**, e non confinato al prodotto: poche conversazioni contemporanee degradano l'intero ERP, inclusi gli utenti che non usano il livello conversazionale.
**Mitigazione.** §10.3 e, per il meccanismo completo, `05-esecuzione-asincrona.md` — dispatcher su cron, controllo del carico, prova di isolamento come criterio di accettazione. Dalla prima release: non è un'ottimizzazione da rinviare, è una proprietà di isolamento.
**Segnale anticipatore.** Prove di carico non eseguite; latenza che cresce con la concorrenza anziché restare stabile.

### RA4 — La copertura del catalogo non viene misurata

**Descrizione.** Si misura l'accuratezza e non la copertura.
**Impatto.** Alto: l'accuratezza si stabilizza sotto l'obiettivo e il lavoro si concentra sul modello, mentre la causa è a monte e non appare in nessun indicatore.
**Mitigazione.** §7.5, con la copertura riportata sempre accanto all'accuratezza.
**Segnale anticipatore.** Miglioramenti al prompt o al modello che non producono effetti misurabili.

### RA5 — L'accoppiamento con Odoo si diffonde

**Descrizione.** Chiamate all'ORM o al sistema delle viste compaiono fuori da Esecutore e Catalogo.
**Impatto.** Alto sull'orizzonte decennale: ogni aggiornamento maggiore di Odoo diventa un progetto anziché una verifica.
**Mitigazione.** Controllo automatico sulle importazioni; revisione dedicata a ogni aggiunta di superficie verso la piattaforma.
**Segnale anticipatore.** Il Validatore o l'Applicatore importano qualcosa da Odoo.

### RA6 — L'osservabilità viene rinviata

**Descrizione.** Registro e corpus vengono realizzati dopo le funzionalità, "quando serviranno".
**Impatto. Critico per il governo del prodotto:** senza misura non esiste il cancello della Fase 2, e senza quel cancello la decisione sulla scrittura si prende per impressioni.
**Mitigazione.** `nli_observability` fa parte della prima consegna; nessuna capacità è considerata completa senza il corrispondente caso di valutazione.
**Segnale anticipatore.** Discussioni sulla qualità condotte per aneddoti.

### RA7 — Distribuzione prematura o troppo tardiva

**Descrizione.** L'Interprete viene estratto in un servizio separato prima che serva, o non viene estratto quando servirebbe.
**Impatto.** Medio in entrambe le direzioni.
**Mitigazione.** L'Adattatore è già il confine di estrazione (§14.4); la decisione si prende sui dati — carico, necessità di isolamento, richiesta di modello proprio — non sulle preferenze.
**Segnale anticipatore.** Nel primo caso, un servizio in più senza un carico che lo giustifichi; nel secondo, l'impossibilità di soddisfare un cliente che richieda un modello nella propria infrastruttura.

### RA8 — Dizionario e Catalogo confusi in un unico componente

**Descrizione.** La distinzione fra il dizionario — dato curato, permanente, per installazione — e il catalogo — selezione effimera, per utente e per richiesta — si perde.
**Impatto.** Medio-alto: la selezione finisce per essere memorizzata come se fosse dato permanente, oppure i permessi vengono applicati al dizionario anziché al catalogo, con il rischio di renderli persistenti e disallineati.
**Mitigazione.** Responsabilità separate all'interno di `nli_semantics`, con la regola: il dizionario non conosce l'utente, il catalogo non è mai persistito oltre la propria memorizzazione a chiave.
**Segnale anticipatore.** Voci di dizionario con riferimenti a utenti o gruppi.

---

## 17. Decisioni Richieste

Numerazione in continuità con i documenti precedenti (D1–D17).

| # | Decisione | Raccomandazione | Conseguenza se rinviata |
|---|---|---|---|
| **D18** | Struttura in cinque moduli `nli_*` con il grafo di §6.2 | **Adottare** | I confini restano convenzioni; RA2 senza presidio |
| **D19** | Stato di Interrogazione persistito come record Odoo (DA2) | **Adottare** | Niente ripresa, cambio di canale, condivisione, annullamento, tracciabilità |
| **D20** | Interpretazione fuori dal ciclo di richiesta, con notifica via bus (§10.3) — **articolata in D20a–D20f in `05-esecuzione-asincrona.md`** | **Adottare** | RA3: rischio di degradare l'intero ERP; è la decisione più urgente |
| **D21** | Catalogo a due fasi con percorso rapido lessicale (§7.3) | **Adottare** | Selezione probabilistica non misurata; tetto di accuratezza invisibile |
| **D22** | Copertura del catalogo come metrica di primo livello, soglia ≥ 99% (§7.5) | **Adottare** | RA4: diagnosi sistematicamente errata sulle cause dell'accuratezza |
| **D23** | Interprete nello stesso processo, dietro l'Adattatore, estrazione rinviata (§14.4) | **Adottare** | Costo operativo pagato senza beneficio, oppure estrazione impossibile in seguito |
| **D24** | I quattro controlli automatici dei confini nella prima consegna (§6.4) | **Adottare** | RA2 e RA5 senza presidio; costo crescente con il codice scritto |
| **D25** | `nli_web` usa i token di `ui_brand_tokens` con degradazione agli stili standard (§14.6) | **Adottare** | Livello conversazionale percepito come estraneo: rischio R3 |
| **D26** | Politica di ritenzione di §9.3 | Confermare o ricalibrare | Crescita non governata dei record di stato |

**D19, D20 e D21 sono le decisioni bloccanti.** D20 è la più urgente in senso proprio: è l'unica il cui rinvio produce un danno **fuori** dal perimetro del prodotto, degradando Odoo per utenti che non lo stanno nemmeno usando.

---

## 18. Glossario Architetturale

| Termine | Definizione |
|---|---|
| **Orchestratore di Sessione** | Coordina il turno; possiede lo Stato e la sua storia; contiene il flusso, non la logica |
| **Catalogo Semantico** | Insieme dei riferimenti nominabili dall'Interprete per un utente e una richiesta; solo metadati |
| **Interprete** | Unico componente probabilistico; unico a conoscere l'esistenza di un fornitore di modelli |
| **Compositore** | Parte dell'Interprete indipendente dal fornitore, che costruisce la richiesta |
| **Adattatore di Fornitore** | Parte dell'Interprete specifica di un fornitore; confine di estrazione futura |
| **Validatore** | Applica i cinque livelli; attraversato obbligatoriamente; non corregge mai |
| **Applicatore** | Funzione pura che produce il nuovo stato; nessuna dipendenza dal tempo |
| **Risolutore** | Traduce lo stato in Piano; unico componente consapevole del tempo e dei permessi in risoluzione |
| **Esecutore** | Esegue tramite ORM con l'identità dell'utente; superficie di contatto con Odoo |
| **Presentatore** | Produce vista nativa e interpretazione, insieme e inseparabilmente |
| **Registro** | Evidenza completa di ogni interazione; conserva la domanda, mai la risposta |
| **Percorso rapido** | Determinazione lessicale deterministica dell'entità, senza chiamata al modello |
| **Copertura del catalogo** | Percentuale di casi in cui i riferimenti necessari erano nel catalogo fornito |

---

## Chiusura

L'architettura ha un solo obiettivo strutturale: **rendere impossibile ciò che i documenti precedenti hanno dichiarato inammissibile.**

L'Interprete non invia dati al modello perché non ha modo di ottenerli. L'esecuzione non supera i permessi perché avviene con l'identità dell'utente. Il modello non nomina ciò che l'utente non può vedere perché non è nel suo catalogo. L'output generativo non raggiunge l'esecuzione perché nessuna interfaccia lo accetta senza l'evidenza della validazione.

Nessuna di queste proprietà dipende dalla disciplina di chi scriverà il codice fra due anni. Dipendono dal grafo delle dipendenze, dalla forma delle interfacce e da quattro controlli automatici — ed è per questo che §6.4 e la decisione **D24** contano quanto le scelte di componente.

**Documenti successivi**, in ordine di dipendenza:

1. **Modello Semantico** — struttura e ciclo di vita del Dizionario, strategia di catalogo, arricchimento dall'uso *(dipende da D10, D16, D17, D21)*
2. **Piano di Valutazione della Qualità** — corpus, metodo, soglie, copertura, criteri di regressione *(dipende da §13, D22)*
3. **Modello di Sicurezza e Conformità** — identità, autorizzazioni, tracciabilità, trattamento dei dati verso il fornitore *(dipende da §12)*
4. **Linee guida di Esperienza Utente** — interpretazione ispezionabile, stati non ideali, disambiguazione *(dipende da §4.8, §11.3)*

---

*Fine del documento.*
