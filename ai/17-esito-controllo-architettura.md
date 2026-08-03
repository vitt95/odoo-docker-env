# ESITO DEL CONTROLLO DI ARCHITETTURA — 3 agosto 2026

Risposta al mandato di `ai/16-controllo-architettura.md`. L'audit ha guardato tutta la
catena, non solo il codice toccato di recente: contratto, prompt, fasi del catalogo,
dizionario, validazione a cinque livelli, applicatore, risolutore, esecutore,
presentatore, coda, e lo strato web fino al componente OWL che disegna la tabella.

**La base di partenza è verde**: 464 test in zona pura, 5 controlli dei confini
puliti. Nessuno dei reperti qui sotto rompe una prova esistente. È il punto.

---

## §0 — Il verdetto in una riga

Il motore **non** è al livello enterprise che `16` chiede, e la distanza non è dove il
progetto pensava che fosse.

Le sette occorrenze del difetto di `00` §38 (codice dichiarato, provato e non
collegato, con la prova verde sempre un passo prima del punto che serviva) **non erano
sette. Ne ho trovate altre undici**, e tre di queste tolgono al prodotto capacità che
`16` elenca come obiettivo:

* le **aggregazioni non vengono mai calcolate** — `SUM`, `AVG`, `MIN`, `MAX` non
  arrivano da nessuna parte;
* i **join non esistono**, in nessuna forma: nessun riferimento attraversa mai una
  relazione;
* l'**ordinamento e le colonne scelte non arrivano alla tabella** che l'utente guarda.

E tre reperti sono di classe diversa — non codice scollegato, ma comportamento
sbagliato che nessuno vede:

* un **fuso orario mancante** su ogni condizione temporale che tocca un campo
  `datetime`, cioè su *«i lead creati oggi»*;
* **nessun tetto** al numero di record richiesti, in nessun punto della catena viva;
* il **catalogo tagliato a 17 attributi** con il profilo in servizio, il che rende
  falsa la proprietà su cui **D32** (la strategia a tre fasi del catalogo) fonda la
  chiusura di **RC3**.

Sotto: i sei reperti gravi per esteso nel formato che `16` chiede, poi gli undici
minori in tabella, poi cosa il prodotto **non** sa fare rispetto alla lista di `16`.

---

## §1 — Reperti gravi

### R1 — Le aggregazioni non vengono mai calcolate

| | |
|---|---|
| **Gravità** | Critica |
| **Probabilità** | Certa: succede a ogni domanda con una misura |
| **Componente** | `nli_dispatch/runtime/pipeline.py`, `nli_core/execution/executor.py`, `nli_web/models/nli_chat.py` |
| **Priorità** | 1 |

**Descrizione tecnica.** `executor.py` ha due funzioni: `execute`, che fa
`search_count` più `search`, e `aggregate`, che fa `_read_group` — l'aggregazione vera
dell'ORM. **`aggregate` non è chiamata da nessuna parte.** Cercata in tutto il
repository: zero chiamanti, e nessun test che la eserciti (`test_execution.py` chiama
solo `execute`, cinque volte).

Il pipeline (`_apply_and_present`) chiama sempre e solo `execute`. Quindi lo stato può
portare `measures: [{"function": "avg", "ref": "crm_lead.expected_revenue"}]`, il piano
la porta avanti fedelmente, il presentatore la elenca nell'interpretazione — e nessuno
la calcola mai. E `_aida_query`, cioè quello che la chat manda al client, **non porta
`measures` affatto**.

**Impatto sul prodotto.** Metà della lista di `16` non ha risposta:

* *«qual è il fatturato medio dei lead»* → il piano ha `avg`, la vista derivata è
  `list` (regola di §6.7: misure senza raggruppamento → lista), e l'utente riceve
  **l'elenco dei 39 lead**. Nessun numero. L'interpretazione sopra dice «media di
  fatturato», il che rende la cosa peggiore che se non avesse detto niente;
* *«qual è il fatturato medio per stato»* → misure più un raggruppamento → vista
  `graph`. La vista di Odoo arriva senza misure dichiarate e ne usa una sua di
  riserva: **il conteggio**. L'utente legge «media di fatturato» sopra e guarda un
  grafico di **quantità** sotto. È la forma pura del rischio che **D2** (il cancello
  che vieta qualunque scrittura sui dati finché la Fase 2 non è misurata e superata)
  porta come argomento: una risposta sbagliata con l'aria di essere giusta.

`COUNT` sopravvive per caso: `record_count` viene da `search_count`, che c'è per
**D68** (conteggio prima del recupero, per poter dire *«i primi 80 di 1 243»*).
`GROUP BY` sopravvive per caso pure lui: `group_by` passa nel contesto della vista
lista di Odoo, che sa raggruppare da sola.

**Root cause.** La stessa di `00` §38. `aggregate` è stata scritta quando il piano ha
imparato a portare le misure, ed è rimasta scollegata perché **nessuna prova la
richiede**: la catena di `_apply_and_present` è provata contro l'esito (`operations`,
39 record), non contro il numero che l'esito dovrebbe contenere.

**Soluzione consigliata.** Il pipeline sceglie il ramo dalla forma del piano, non
dalla vista: `if plan.measures or plan.group_by: executor.aggregate(...)`, e il
risultato dell'aggregazione entra nel `Result` insieme al totale. Il presentatore lo
mostra; `_aida_query` porta le misure nel contesto della vista pivot/graph
(`context.pivot_measures` / `graph_measure`), così la vista di Odoo mostra la misura
che l'interpretazione ha dichiarato.

**Patch suggerita** (forma, non testo finale):

```python
# executor.py — un solo punto d'ingresso, come per l'esecuzione semplice
def run(env, plan: Plan) -> Result:
    if plan.measures or plan.group_by:
        return Result(records=(), total=..., plan=plan,
                      groups=aggregate(env, plan))
    return execute(env, plan)
```

**Test che verifica la correzione.** Due, e servono tutti e due secondo la regola di
`ai/restart.md` (*«una funzione è finita quando esiste una prova che fallisce se
qualcuno la scollega»*):

1. test Odoo: uno stato con `avg` su un campo numerico e un raggruppamento produce un
   `Result` i cui gruppi contengono la media, e il numero è quello che `_read_group`
   dà sugli stessi record;
2. test Odoo: `_aida_query` di un turno con misure porta le misure. Senza questo, il
   ramo si può ricollegare al server e restare scollegato allo schermo — che è
   esattamente com'è finita `in_words`.

---

### R2 — L'ordinamento e le colonne non arrivano alla tabella

| | |
|---|---|
| **Gravità** | Critica |
| **Probabilità** | Certa su ogni domanda con «i primi N» o «ordinati per» |
| **Componente** | `nli_web/static/src/chat/aida_records.js` |
| **Priorità** | 1 |

**Descrizione tecnica.** `_aida_query` costruisce e manda al client sette chiavi:
`model`, `domain`, `fields`, `group_by`, `order`, `limit`, `view`. Il componente
`AidaRecords.viewProps` ne usa **quattro**: `view`, `model`, `domain`, e `limit` (come
`list_view_limit`), più `group_by` nel contesto.

**`order` e `fields` sono ignorati.**

**Impatto sul prodotto.** La tabella che l'utente guarda **non è il risultato del
piano**: è una rilettura del solo dominio, ordinata come Odoo ordina quel modello per
conto suo (`_order` del modello). Per una domanda con un ordinamento, i record mostrati
sono quelli sbagliati.

**Esempio reale.** *«i 10 lead con il fatturato più alto»*. Il piano è corretto:
`order = "expected_revenue desc"`, `limit = 10`. L'esecutore li legge giusti. Poi la
vista rilegge con il solo dominio, ordina per `_order` di `crm.lead` e mostra **i primi
10 di un ordinamento che nessuno ha chiesto**, con il limite giusto. L'interpretazione
sopra dice «ordinati per fatturato, decrescente». Dieci righe plausibili, l'ordinamento
sbagliato, nessun errore da nessuna parte.

Stesso meccanismo su `fields`: *«mostrami i lead con email e telefono»* risolve
`set_fields` correttamente, e la vista mostra le sue colonne di sempre.

**Root cause.** `00` §33.4 ha deciso di incorporare la vista lista di Odoo per non
riscrivere ricerca, colonne e paginazione. La decisione è giusta. Quello che non è
stato fatto è **passarle il resto del piano**: sono state passate le due chiavi che
servivano a far comparire la tabella, e le prove si fermano al server — `_aida_query`
è provata, `viewProps` no. È il difetto di §38 nel codice più nuovo del progetto, e
conferma il punto 2 degli aperti di `restart.md` (*«non esiste nessuna prova del lato
client»*).

**Soluzione consigliata.** `viewProps` passa `orderBy` (derivato da `plan.order`) e le
colonne. Odoo 18 accetta `orderBy: [{name, asc}]` sulla `View`; le colonne richiedono
o un `arch` generato o il contesto delle colonne opzionali. Se una delle due non è
ottenibile pulitamente, **va dichiarato**: una tabella che non rispetta l'ordinamento
dichiarato sopra di sé è peggio di una tabella che dice di non poterlo fare.

**Test che verifica la correzione.** Una prova di componente OWL (il banco che il punto
2 di `restart.md` chiede e che non esiste) che monta `AidaRecords` con un `query`
contenente `order` e verifica che le `viewProps` lo portino. **Fallisce se qualcuno
riscollega la vista dimenticando l'ordinamento**, che è la condizione della regola di
§38.

---

### R3 — Nessun tetto al numero di record, in nessun punto della catena viva

| | |
|---|---|
| **Gravità** | Alta — è anche il solo reperto con una faccia di sicurezza |
| **Probabilità** | Alta |
| **Componente** | `nli_core/validation/coherence.py`, `nli_dispatch/runtime/pipeline.py` |
| **Priorità** | 1 |

**Descrizione tecnica.** **D13** fissa il limite predefinito a 80 e il **massimo
assoluto a 500**. Il tetto è scritto in `coherence.validate_cost`, che produce
`limit_above_maximum`. Quella funzione **non è chiamata da nessuna parte in
produzione**: `contextual.validate` — l'unica cosa che il pipeline invoca per i livelli
3-5 — chiama la sua `validate_cost`, che è un'altra funzione e guarda solo il costo
delle categorie.

L'applicatore, per parte sua, **non taglia di proposito** (commento in `_set_limit`:
*«il tetto è una faccenda del livello 5»*), e il livello 5 non gira. La validazione
strutturale controlla che `limit.value` sia un intero positivo, senza massimo. Lo
schema JSON ha `maximum`, ma lo schema serve alla generazione vincolata e all'ispezione
— non è la strada della validazione.

**Provato**, eseguendo la zona pura:

```
1. set_limit oltre il massimo assoluto (D13 = 500)
   struttura busta : NESSUN RIFIUTO
   limite nello stato: 1000000
   struttura stato : NESSUN RIFIUTO
   livelli 3-5 come li chiama il pipeline: NESSUN RIFIUTO
   coherence.validate_cost (MAI CHIAMATA in produzione): ['limit_above_maximum']
```

**Impatto sul prodotto.** *«mostrami i primi 200000 lead»* è una frase ordinaria che il
modello traduce in `set_limit: 200000`, e la catena la esegue: `search` con quel limite,
su un processo cron condiviso, con la connessione al database occupata. Non è un
problema di prestazioni di chi ha chiesto: è disponibilità tolta a tutti gli altri, che
è precisamente l'argomento con cui `coherence.validate_cost` si giustifica nel proprio
docstring.

Nessun privilegio da scalare, nessuna iniezione: basta scriverlo in italiano.

**Root cause.** Il livello 5 è nato diviso in due metà — quella che non ha bisogno del
dizionario (`coherence`) e quella che ce l'ha (`contextual`) — e il pipeline ne ha
collegata una sola. È la stessa forma di `00` §33.3, dove `coherence.validate_coherence`
non era sul percorso: **è stata corretta quella funzione e non la sua vicina di
modulo**.

**Soluzione consigliata.** Una riga in `contextual.validate`, accanto a quella che già
aggiunge `coherence.validate_coherence`:

```python
return (validate_cost(state, category_costs=category_costs or {}, limits=limits)
        + coherence.validate_cost(state, limits=limits))
```

**Test.** Uno che mostra il rifiuto a 501 e uno che mostra il passaggio a 500, come
chiede `restart.md` (*«ogni controllo ha un test che lo mostra scattare e uno che lo
mostra non scattare»*), scritti **contro `contextual.validate`** e non contro
`coherence.validate_cost` — la prova deve fallire se qualcuno scollega di nuovo.

Con la stessa riga rientra anche `too_many_relation_hops` (§7.3, il limite di due salti
di relazione di **D12**), che oggi è morto per la stessa ragione.

---

### R4 — Il fuso orario manca su ogni condizione temporale che tocca un `datetime`

| | |
|---|---|
| **Gravità** | Alta |
| **Probabilità** | Certa, su ogni installazione non in UTC |
| **Componente** | `nli_core/resolution/resolver.py`, `nli_dispatch/runtime/pipeline.py` |
| **Priorità** | 1 |

**Descrizione tecnica.** `pipeline._instant` legge l'ora **nel fuso dell'utente** —
`context_timestamp` — e la passa al calendario, che lavora su date. Il risolutore
trasforma il periodo in due estremi e li scrive nel dominio come stringhe di data:

```
dominio prodotto: ['&', ('create_date', '>=', '2026-08-03'), ('create_date', '<', '2026-08-04')]
```

Ma **Odoo conserva i `datetime` in UTC**. La colonna è in UTC, gli estremi sono l'ora
locale, e nessuno converte. `_temporal_domain` non riceve nemmeno il tipo
dell'attributo, quindi non potrebbe distinguere un `date` (dove il confronto è giusto)
da un `datetime` (dove non lo è).

**Impatto sul prodotto.** Su un'installazione italiana (UTC+2 d'estate) la finestra è
spostata di due ore: *«i lead creati oggi»* **esclude** quelli inseriti fra mezzanotte
e le due di stanotte e **include** quelli inseriti fra le 22 e mezzanotte di ieri. Il
numero è plausibile, vicino a quello giusto, e sbagliato. D'inverno lo scarto è un'ora;
su un'installazione a Tokyo o a Los Angeles è mezza giornata.

Il campo colpito è `create_date`, cioè **quello che D117 ha appena rimesso nel catalogo
proprio perché *«quando è stato creato»* è la prima cosa che si intende con «i lead di
quest'anno»**. E colpisce di più le finestre corte: su *«quest'anno»* due ore su
365 giorni non si vedono, su *«oggi»* sono l'8%.

**Root cause.** Il calendario è dichiarato zona deterministica e ragiona in **date**,
il che è giusto per la sua aritmetica. Il salto mancante è alla frontiera: chi scrive
il dominio deve sapere se la colonna è un istante o un giorno, e il risolutore lo sa
(`binding.type`) ma non lo passa a `_temporal_domain`.

**Soluzione consigliata.** `_temporal_domain` riceve `binding.type`. Per `date`, il
comportamento resta identico. Per `datetime`, gli estremi si convertono da ora locale a
UTC prima di essere scritti. La conversione è dato di piattaforma, quindi la fa chi ha
la piattaforma: `Instant` porta già il fuso (o lo porta il pipeline), e la funzione di
conversione arriva come argomento — la stessa forma con cui `mentions` e
`scope_justifies` entrano nelle zone pure.

**Test.** Un test puro con un istante alle 00:30 locali in un fuso a +02:00 che verifica
che il dominio parti da `2026-08-02 22:00:00` e non da `2026-08-03`. E un test Odoo che
crea due lead a cavallo della mezzanotte locale e chiede *«creati oggi»*: la prova
fallisce oggi.

---

### R5 — I join non esistono

| | |
|---|---|
| **Gravità** | Alta (limite di capacità, non difetto di correttezza) |
| **Probabilità** | Certa |
| **Componente** | `nli_semantics/introspection/l0.py`, `introspection/runtime.py` |
| **Priorità** | 2 |

**Descrizione tecnica.** `Binding.field` è documentato come *«il percorso tecnico del
campo, per esempio `partner_id.city`»*. Quel percorso **non è mai prodotto**:

```python
def reference_of_field(model_name: str, field_name: str) -> str:
    return f"{reference_of_model(model_name)}.{field_name}"
```

Un solo punto, e il pezzo dopo è un nome di campo diretto. `runtime.semantics` lega
`bindings[ref] = Binding(field=name, ...)` iterando `fields_get()` del solo modello
bersaglio. Nessuna relazione viene attraversata, in nessun punto. Il limite di due
salti di **D12** sorveglia un percorso che non esiste.

**Impatto sul prodotto.** Tutta la sezione JOIN di `16` è fuori portata, e con lei una
buona parte delle QUERY COMPLESSE:

* *«quali città hanno più lead»* — la città sta su `partner_id`;
* *«il massimo fatturato per regione»*;
* *«quali aziende non hanno referenti»*;
* *«mostrami i contatti di Roma»* — misurato sul campo il 3 agosto: **0 record**, e il
  registro lo attribuisce a un dominio corretto su dati assenti. Va riguardato con
  questo reperto in mano.

Quello che **funziona** è la relazione presa come un tutto: `partner_id` è un attributo
di tipo `relation`, quindi `is_set` / `is_not_set` / `is_one_of` ci lavorano —
*«i lead senza cliente»* si dice. Quello che non si dice è **un attributo dell'entità
in fondo alla relazione**.

**Root cause.** Non è un difetto: è una parte non costruita, con la documentazione
scritta come se lo fosse. Il `Binding` promette un percorso puntato e nessuno lo emette.
Questo è il modo più costoso di avere un buco, perché chi legge il codice crede che ci
sia.

**Soluzione consigliata.** Non improvvisarla. È una decisione numerata, e ha almeno tre
questioni aperte che vanno deliberate prima di scrivere: (a) **quali** relazioni
esporre, perché esporle tutte moltiplica il catalogo per il numero dei campi
relazionali, e il budget è già stretto (vedi R6); (b) come si chiama il riferimento
promosso — `06` ha già il tipo **T7** per questo; (c) chi paga il costo, visto che un
dominio con un punto in Odoo è una sotto-interrogazione.

**Nel frattempo va scritto nella documentazione**, dove oggi il `Binding` dice il
contrario, e vanno tolte le tre affermazioni di `04` che descrivono i salti di
relazione come esistenti.

---

### R6 — Il catalogo è tagliato a 17 attributi, e questo rende falsa la promessa di D32

| | |
|---|---|
| **Gravità** | Alta |
| **Probabilità** | Certa con il profilo in servizio |
| **Componente** | `nli_semantics/catalogue/exposure.py` + configurazione del profilo |
| **Priorità** | 1 (prima della prossima misura di accuratezza) |

**Descrizione tecnica.** **D79** deriva il budget del catalogo dalla finestra di
contesto dichiarata dal profilo. Con i valori scritti in `exposure.py` e la finestra di
**4096** che il profilo in servizio dichiara:

```
disponibili = 4096 × 0,25 − 600 = 424 gettoni
budget      = 424 ÷ 24 = 17 attributi per entità
```

Diciassette, contro il tetto di 60 di **D31**. `crm.lead` di attributi nominabili ne ha
molti di più.

**Impatto sul prodotto.** **D32** (la strategia a tre fasi) chiude **RC3** con questo
argomento, che il registro riporta testualmente: *«In Fase C non c'è selezione: la
copertura sugli attributi è esatta per costruzione, e il punto di perdita si riduce
alla sola determinazione dell'entità»*. Con un budget di 17 la selezione **c'è**, ed è
grossa: quaranta e più attributi non arrivano al modello. La copertura non è esatta per
costruzione, e il punto di perdita non è solo la fase A.

`restart.md` segnala già la finestra da sistemare. Quello che aggiungo è **l'aritmetica
e la conseguenza sull'architettura**: non è solo che la prossima misura misurerebbe il
taglio — è che una proprietà su cui si regge la chiusura di un requisito non vale oggi.

**Root cause.** Il profilo dichiara 4096 perché è quanto il server serve di default;
`qwen3.5:9b` regge molto di più. È configurazione, non codice — ma **D79 è nata proprio
per rendere visibile questo caso** (*«copertura alta, accuratezza bassa, causa fuori da
ogni tabella diagnostica»*) e il meccanismo ha funzionato: `refused_for_budget` conta i
tagli. **Non lo guarda nessuno.**

**Soluzione consigliata.** Due cose, e la seconda conta più della prima:

1. alzare la finestra dichiarata dal profilo a quella vera, e rimisurare;
2. **far parlare `refused_for_budget`**. Un catalogo che ha buttato 40 attributi su 57
   è un fatto che deve arrivare a qualcuno: nella traccia diagnostica di **D123**
   sempre, e come avviso sullo stato del profilo quando il budget scende sotto una
   soglia. Un contatore che nessuno legge è la stessa cosa di un contatore che non
   c'è.

**Test.** Un test puro che, dato `context_window=4096`, asserisca il budget di 17 —
così il numero è scritto e un cambio ai coefficienti si vede. E un test che verifichi
che la traccia diagnostica riporti il numero dei rifiutati.

---

## §2 — Reperti minori, in tabella

Tutti verificati. Nessuno è un'ipotesi.

| # | Reperto | Gravità | Componente | Perché conta |
|---|---|---|---|---|
| M1 | **`revert_last` e `open_record` non fanno niente.** L'applicatore li gestisce e mette l'esito in `Result.revert_requested` e `Result.navigations`; il pipeline **non legge né l'uno né l'altro**. Due delle ventidue operazioni del vocabolario sono no-op silenziosi | Media | `pipeline.py` | *«torna indietro»* rilancia la stessa query e sembra riuscito. *«apri il terzo»* ridà l'elenco. Difetto di §38 |
| M2 | **Il livello 5 sulle categorie non gira.** Il pipeline chiama `contextual.validate` senza `category_costs`, che vale `{}`: `too_many_aggregate_categories` (V-D87-2) non può mai scattare | Media | `pipeline.py:292` | La regola che **D12** cita come ragione della propria esistenza è provata e non collegata |
| M3 | **Il margine della fase A non chiede mai niente.** `PhaseA.needs_clarification` e l'esito `BELOW_MARGIN` non sono letti da nessuno: due entità troppo vicine cadono nella fase B invece di produrre la domanda che **D33** prescrive | Media | `pipeline._determine_entity` | D33 dice che il margine *«è ciò che distingue una corrispondenza da un'ipotesi»*. Oggi distingue solo quanto si spende |
| M4 | **`_persist` sta fuori dal `try`.** `worker.execute` promette nel docstring di non sollevare mai; l'eccezione è catturata solo intorno a `pipeline.run`. Se `write_state` fallisce — e ha già fallito una volta, per `dsl_version` mancante (`00` §30.1) — il thread muore, la riga resta in `running` e l'utente guarda l'attesa per cinque minuti, fino al cron di recupero | Media | `worker.py:76-91` | La prova che quel guasto è già successo è nel registro |
| M5 | **`Presentation.action()` non è chiamata.** L'azione Odoo nativa che **V4** descrive non è mai costruita: la chat incorpora la vista per conto suo (`00` §33.4) | Bassa | `presenter.py` | O si collega o si toglie. Un metodo che realizza un vincolo e non gira è una garanzia che non c'è |
| M6 | **`CHECK (true)` su `nli.turn`.** Il vincolo SQL si chiama `companies_required` e verifica letteralmente `true`. La garanzia vera è il `@api.constrains` in Python | Bassa | `nli_interrogation.py:197` | È **la stessa forma** di `00` §20.2 (il `CHECK` di `nli_profile` che PostgreSQL rifiutava e che non è mai esistito). Un vincolo che dichiara e non verifica |
| M7 | **La negazione non è producibile.** Lo stato ammette il connettivo `not`, il risolutore lo traduce, e **nessuna operazione lo può creare**: `add_condition` accetta `combine` solo fra `all` e `any` | Media | `contract/vocabulary.py`, `contract/envelope.py` | *«i lead che non sono di Roma»* non è esprimibile. Terzo caso di simbolo dichiarato e irraggiungibile, stavolta **nel contratto** |
| M8 | **`not_equals` e `ends_with` non esistono.** `16` li chiede entrambi. `is_not_one_of` c'è ma solo su `enum` e `relation`, non su testo e numeri | Media | `contract/vocabulary.py` | *«diverso da»* è una delle prime cose che una persona dice |
| M9 | **`_check_one_period_per_attribute` non guarda `on`.** Due `on` sullo stesso attributo data sono una contraddizione (una data non può essere due giorni) e passano | Bassa | `validation/coherence.py:228` | Stessa famiglia di **D125**, un predicato dimenticato |
| M10 | **Un `not` su un figlio vuoto sparisce.** In `_filter_domain`, se i figli si riducono a niente si restituisce `[]`: un `not` di niente diventa *nessun filtro*, cioè l'opposto. Raggiungibile con una categoria il cui dominio è vuoto | Bassa | `resolver.py:154-158` | Allarga la risposta invece di restringerla, in silenzio |
| M11 | **Sette funzioni pubbliche senza chiamanti** oltre a quelle già citate: `permissions.readable_entities`, `filters.propose_categories`, `conditions.implied_entities`, `failure.first_failing_level`, `envelope.operations_of`, `scope_lexicon.justifies_of`, e `Plan.as_search_arguments` | Bassa | varie | Non fanno danno. Sono la misura di quanto sia facile, qui, scrivere una cosa e non collegarla |

---

## §3 — Cosa `16` chiede e il prodotto non sa fare

Non sono difetti: sono la distanza fra l'obiettivo dichiarato e il contratto attuale.
La metto perché `16` chiede di segnalare i mapping incompleti.

**Intenti.** `SELECT`, `COUNT`, `GROUP BY`, `ORDER BY`, `LIMIT`, `FILTER`, `SEARCH`
esistono. `SUM`, `AVG`, `MIN`, `MAX`, `DISTINCT` esistono nel contratto e **non sono
calcolati** (R1). `HAVING`, `OFFSET`, `JOIN`, `EXISTS`, `NOT EXISTS`, `EXPORT` non
esistono nel vocabolario.

* `HAVING` — *«le aziende con più di 10 lead»* — richiede una condizione su un
  aggregato. Il dizionario ha il tipo **T4** per questo, ma `domains.py` rifiuta
  esplicitamente di tradurre un aggregato in un dominio, e il livello 5 lo respinge. È
  una scelta dichiarata (**V-D87-2**), non un buco: va detto che quelle domande sono
  **fuori portata per costruzione**, non «da sistemare».
* `OFFSET` — non c'è. La paginazione è quella della vista incorporata, il che è una
  risposta ragionevole ma diversa da quella che `16` immagina.
* `EXISTS` / `NOT EXISTS` — coperti solo nel caso semplice, `is_set` / `is_not_set` su
  una relazione. *«i lead che non hanno attività»* funziona; *«i lead che hanno almeno
  un'opportunità vinta»* no, perché la condizione sta sull'entità in fondo (R5).

**Operatori.** Mancano `!=` (M8), `ENDS WITH` (M8) e `NOT IN` su testo e numeri.
`BETWEEN` su date è stato tolto di proposito da **D113** in favore di `within`, ed è
giusto così.

**Date.** Il vocabolario copre tutto quello che `16` elenca **tranne i trimestri
nominati** (`Q1`…`Q4`) e **i mesi nominati** (*«gennaio»*, *«marzo»*). Ci sono
`current_quarter` e `previous_quarter`, che sono un'altra cosa: *«nel primo trimestre»*
non si dice. Un mese nominato si può dire con `absolute_range`, ma solo se il modello
sa calcolarne gli estremi — cioè esattamente quello che il prompt gli vieta (*«never
resolve a date»*). **È una contraddizione fra il prompt e il vocabolario**, e va
deliberata: o entrano le espressioni nominate, o la regola del prompt fa un'eccezione
dichiarata.

**Sinonimi di entità e di campo.** L'impianto è quello giusto — **D126** raccoglie le
parole dall'installazione invece di generarle, e il registro delle voci approvate di
**D108** è la strada per aggiungerne. Ma la lista di `16` (*prospect*, *trattativa*,
*deal*, *referente*, *posta elettronica*, *cellulare*, *commerciale*) **non è nei
menu di Odoo**, quindi oggi non è riconosciuta. Ottenerla è lavoro di dizionario, non
di motore: la strada c'è ed è **D108**. Va solo percorsa, e il punto 5 degli aperti di
`restart.md` dice già che i nomi non sono misurati su un'installazione vera.

---

## §4 — Sicurezza: cosa ho guardato e cosa ho trovato

Poco, ed è un buon segno.

**Iniezione di prompt.** L'enunciato entra nel messaggio all'utente in fondo, senza
delimitatore, quindi si può scrivere una frase che finge di essere una sezione del
prompt. **Il danno è quasi nullo**, e la ragione è architetturale: con la generazione
vincolata i `ref` ammessi sono un insieme chiuso costruito dal catalogo **di chi
chiede** (**D101**, **D102**). Un utente che convince il modello a scrivere qualunque
cosa può solo far male interpretare la propria domanda. Non c'è modo di nominare
un'entità o un attributo che non gli spetta, perché non è scrivibile. Questa è la
proprietà più forte dell'intera architettura e regge.

**Iniezione SQL.** Nessuna superficie: si passano domini all'ORM, mai stringhe. L'unica
stringa costruita è l'ordinamento, e i suoi due pezzi vengono dal dizionario e da un
`enum` chiuso.

**Scalata di privilegi.** Nessun `sudo` nella catena, e il controllo sintattico di
**D24** lo verifica a ogni giro. L'identità e le società attive sono ricostruite dal
turno (**D40**). L'impronta dei permessi (**D39**) include gruppi, società e lingua.

**Il buco reale è R3**, ed è di disponibilità: un utente ordinario può chiedere un
milione di record scrivendolo in italiano.

**Un rischio da conoscere, non un difetto:** `nli.turn` è scrivibile dal proprio
proprietario, e le operazioni di un'opzione scelta (**D121**) non ripassano dalla
validazione strutturale prima di essere applicate. Chi si costruisce a mano un turno
falso può far sollevare l'applicatore. L'esito è un turno `failed` suo, e i riferimenti
restano quelli che gli spettano (il livello 3 li ricontrolla) — quindi il costo è per
lui. Ma è un punto in cui **D121** poggia su *«le operazioni sono già nella busta e
quindi sono valide»*, che è la stessa assunzione che **D128** ha appena dovuto
smentire per i chiarimenti scritti dal modello.

---

## §5 — La conclusione che vale più dei singoli reperti

`00` §38 dice: *«una funzione è finita quando esiste una prova che fallisce se qualcuno
la scollega»*. La regola è giusta ed è arrivata dopo sette occorrenze. Ne ho trovate
altre undici, **tutte scritte prima che la regola esistesse**, e questo va detto: la
regola non ha fallito, non era ancora in vigore.

Ma la regola da sola non basta, e i reperti dicono perché. **Sette degli undici casi
sono lo stesso pezzo di catena: la coda finale del turno.** `aggregate`,
`coherence.validate_cost`, `category_costs`, `revert_requested`, `navigations`,
`Presentation.action`, `order` e `fields` nella vista. Tutti fra il piano risolto e lo
schermo. Tutti provati **a monte** del punto in cui servivano.

La ragione è strutturale: **non esiste una sola prova che parta da una frase e arrivi a
un numero.** Ci sono prove del contratto (918 casi), prove pure (464), prove Odoo
(167), e la batteria manuale sul campo. Nessuna di queste attraversa la catena intera
verificando il **contenuto** della risposta: quelle sul campo guardano l'esito
(`operations`) e il conteggio, non l'ordinamento, non le colonne, non le misure.

**La raccomandazione principale di questo audit non è una patch. È una prova.** Un
banco che, su un database noto, prenda una decina di frasi con risposta calcolabile a
mano — *«i 3 lead con fatturato più alto»*, *«la media del fatturato»*, *«quanti lead
per stato»*, *«i lead creati oggi»* — e verifichi **i record e i numeri**, non l'esito.
Sei degli undici reperti qui sopra sarebbero rossi al primo giro, e nessuno di loro è
visibile a nessuna delle 1 549 prove che oggi passano.

---

## §6 — Ordine di lavoro proposto

1. **R3** (tetto ai record) — una riga, chiude un rischio di disponibilità.
2. **R6** (finestra del profilo) — configurazione, e va fatto **prima** di qualunque
   misura di accuratezza, altrimenti quella misura misura il taglio.
3. **La prova punta-a-punta di §5** — prima delle correzioni che seguono, così le
   correzioni nascono già coperte.
4. **R4** (fuso orario) e **R2** (ordinamento e colonne alla tabella) — i due che
   producono numeri sbagliati con l'aria di essere giusti.
5. **R1** (aggregazioni) — è la capacità più grande che manca, ed è lavoro vero.
6. **M1, M2, M3, M4** — i quattro scollegamenti minori.
7. **R5** (join) e **M7/M8** (negazione e operatori mancanti) — sono decisioni da
   deliberare, non correzioni. Vanno numerate in `ai/00` prima di scrivere codice.

Il punto 1 degli aperti di `restart.md` — il chiarimento temporale costruito da noi
invece che dal modello — **resta il primo per quanto sblocca**, e non è in
concorrenza con questa lista: è nella parte di catena che funziona.
