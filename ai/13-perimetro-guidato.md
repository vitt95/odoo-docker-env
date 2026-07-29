# Proposta — Il Perimetro Guidato
## Suggerire la lingua invece di indovinarla

| Voce | Valore |
|---|---|
| **Titolo** | Perimetro Guidato — vocabolario suggerito, mai imposto |
| **Tipo** | **Proposta**, non documento adottato. Richiede delibera dell'Architect |
| **Versione** | 0.1 |
| **Data** | 29 luglio 2026 |
| **Origine** | Proposta dell'Architect: *«se diamo troppa libertà di espressione non ne usciremo mai; diamo un perimetro di costruzione»* |
| **Presuppone** | `06` (dizionario semantico), `09` (esperienza utente), `03` §4.4 (esito `clarification`) |
| **Decisioni richieste** | **D104**, **D105**, **D106** — §7 |

---

## 1. Il problema, con i numeri

La misura del 29 luglio su tutte le 444 aperture del corpus, con `qwen3.5:9b`:

| Sezione | Accuratezza | Soglia D44 |
|---|---|---|
| `target` (quale entità) | 98,4% | ✅ |
| `fields` (quali colonne) | 88,1% | ✅ |
| `order_by`, `limit`, `group_by` | 93–94% | ✅ |
| **`filter` (come filtrare)** | **73,6%** | ❌ |

La diagnosi caso per caso su 80 aperture dice che **dodici fallimenti su ventuno sono lo stesso errore**: un frammento di frase che non nomina alcuna condizione nominata viene mappato su una condizione nominata.

```
'voglio vedere ordini lo scorso mese i primi 5'
  prodotto: is_category(ordini_vendita.in_bozza)  provenance: "lo scorso mese"
  atteso:   within(ordini_vendita.data_ordine, previous_month)
```

La provenienza è la confessione: il modello **isola il frammento giusto** e poi lo traduce nella condizione più economica da scrivere — un'etichetta senza valore, senza `kind`, senza espressione — invece di costruire quella corretta.

### 1.1 Perché non è un problema che si risolve limando

Tre delle sei correzioni della qualificazione del profilo (`00` §18) hanno corretto **il metro**, non il modello: la direzione dell'ordinamento fissata a discendente anche su ciò che data non è (D99), i comparativi inclusivi contati come stretti (D100), i tipi del catalogo diversi da quelli del contratto (§18.7).

E una frase del corpus è risultata **genuinamente ambigua**: *«cerca contatti con p.iva, recapito, indirizzo mail»* può significare *mostrami quelle colonne* oppure *cercami i contatti che hanno la partita iva*. Il corpus ne attende una sola, il modello ha risposto l'altra, e la lettura del modello è probabilmente la più frequente in un gestionale.

> Ogni punto strappato da qui in avanti su un corpus sintetico ha una probabilità crescente di essere **prompt adattato al generatore**. È la degradazione che **D42** descrive: la misura che si trasforma in conferma di sé stessa.

### 1.2 Il problema visto dall'utente, che è quello vero

L'utente ha davanti una casella di testo vuota e **nessun indizio** su cosa il sistema sappia fare. Deve indovinare. Se sbaglia riceve un rifiuto, e il rifiuto non gli dice cosa fare diversamente.

Nel frattempo il sistema **possiede già** l'elenco delle parole che riconosce per ogni entità — per le fatture sa che *scadute* si dice anche *insolute*, *in ritardo*, *da incassare*, *arretrate*. Quell'elenco oggi lo vede solo il modello. L'utente no.

**Teniamo nascosta a chi ne ha bisogno un'informazione che abbiamo già.**

---

## 2. La proposta in una riga

> **Il vocabolario che il sistema conosce viene mostrato all'utente mentre scrive, e riproposto come scelta quando il sistema non capisce. Suggerito sempre, imposto mai.**

---

## 3. Cosa si scarta, e perché

L'opzione conservativa — **restringere la lingua ammessa** — va cercata per prima e scartata con un argomento.

**Primo argomento: il prodotto sparisce.** Se l'utente può usare solo le parole che gli diamo, abbiamo costruito un modulo a tendine con una casella di testo davanti, e Odoo i filtri a tendina li ha già. La ragione per cui questo prodotto esiste è la persona che **non sa** dove sta il filtro, non conosce il nome del campo e sa soltanto cosa vuole sapere. A quella persona il recinto toglie esattamente ciò per cui era venuta.

**Secondo argomento: i numeri diventerebbero falsi.** Restringere il linguaggio ammesso alza l'accuratezza perché **rimuove i casi difficili**, non perché il sistema migliori. È lo stesso difetto di §1.1 con un'altra faccia: si otterrebbe un 95% che non significa nulla, e — peggio — che nessuno saprebbe più leggere come sospetto.

**Terzo argomento: le persone non parlano per sostantivi.** L'utente non scrive un filtro, scrive un obiettivo: *«chi mi deve dei soldi»*, *«come stiamo andando questo mese»*. Nessun perimetro di sostantivi produce quelle frasi, e sono quelle che l'elicitazione (**D85**) andrà a raccogliere.

---

## 4. I tre momenti

### 4.1 Mentre scrive — il vocabolario visibile

L'utente scrive *«fatture»*. Sotto la casella compaiono le voci che il catalogo di quell'entità contiene, raggruppate per genere:

```
  condizioni pronte   scadute · da incassare · in bozza · partite aperte
  periodi             questo mese · mese scorso · quest'anno · ultimi 30 giorni
  confronti           importo sopra … · importo sotto … · importo almeno …
  colonne             cliente · data · importo · scadenza · stato pagamento
```

Cliccabili, e ignorabili. **L'effetto che conta non è il clic: è che alla seconda interrogazione l'utente scrive meglio da solo.** Impara la lingua della casa guardandola, senza corsi e senza manuale.

### 4.2 Quando il sistema non capisce — il perimetro come scelta

È il momento in cui la proposta vale di più, perché è il punto in cui oggi l'utente resta fermo.

`03` §4.4 prevede già l'esito `clarification`: una domanda più da 2 a 4 opzioni, ciascuna con le operazioni che produrrebbe. È implementato. **Il modello non lo emette quasi mai**: su 444 aperture ha preferito indovinare.

Con il perimetro, un frammento non riconosciuto produce:

> **Non sono sicuro di aver capito «lo scorso mese».** Intendevi:
> 1. ordini **con data nel mese precedente**
> 2. ordini **ancora in bozza**
> 3. ordini **da consegnare**

L'utente sceglie e ottiene la risposta giusta. E ha appena imparato tre modi di dire senza che nessuno gliel'abbia spiegato.

**Questa è anche la risposta alla domanda lasciata aperta dal controllo di §5**: un rifiuto che propone è un prodotto; un rifiuto che tace è solo un errore in più.

### 4.3 Dopo la risposta — il perimetro come raffinamento

Sotto il risultato, le condizioni che **si possono aggiungere a questa interrogazione**, prese dallo stesso catalogo. È il caso conversazionale già previsto da `03` §17.1 (la sequenza di turni in cui ogni frase modifica lo stato precedente), con la differenza che l'utente non deve indovinare cosa sia lecito dire.

---

## 5. Il controllo che rende il perimetro necessario

Separato ma inscindibile: **una condizione nominata deve essere fondata nella frase.**

Il catalogo porta i **termini** di ogni condizione nominata. `in_bozza` ha *in bozza, da confermare, provvisori, non confermati, provvisorie, non confermate*. Il frammento *«lo scorso mese»* non contiene nessuno di quei termini, quindi la condizione è infondata **per costruzione** — e accorgersene non richiede di capire l'italiano, richiede di confrontare due liste.

Il controllo appartiene al **livello 3** (la validazione che conosce il dizionario dell'utente che ha chiesto), non allo schema: è una domanda sul catalogo, non sulla forma della busta.

**Va detto con precisione cosa produce**: non fa dare la risposta giusta, fa **rifiutare** quella sbagliata. Sul metro può valere zero. Sul prodotto vale la ragione per cui esiste **D2** (nessuna risposta sbagliata presentata con l'aria di essere giusta): un filtro inventato non sbaglia in modo visibile — mostra *meno* record, con sicurezza, e l'utente decide su dati sbagliati credendoli giusti.

> Un «non ho capito» è un errore che si vede. Un filtro inventato è un errore che si crede.

**Rischio dichiarato.** Il confronto fra frammento e termini deve tollerare refusi, abbreviazioni, accenti mancanti e maiuscole — che il corpus inietta di proposito e che gli utenti veri producono di continuo. Un confronto letterale rifiuterebbe risposte corrette. Il confronto deve quindi usare **lo stesso apparato di riconoscimento dei termini della Fase A** (la fase deterministica che risolve l'entità con punteggio e margine, misurata all'86,2% con zero determinazioni sbagliate), non una nuova implementazione. Due riconoscitori di termini che divergono sarebbero un guasto peggiore del problema.

---

## 6. Da dove escono le parole

**Dal catalogo, che esiste.** Nessuna lista scritta a mano:

| Genere | Fonte | Esempio |
|---|---|---|
| Condizioni nominate | categorie del catalogo, con i loro termini | *scadute, insolute, in ritardo* |
| Periodi | vocabolario temporale del contratto, verbalizzato | *questo mese → current_month* |
| Confronti | attributi numerici + comparativi del lessico | *importo sopra …* |
| Colonne | attributi esposti, entro il budget di **D31/D79** | *cliente, data, importo* |

Due conseguenze che valgono da sole:

1. **Un cliente con campi personalizzati ottiene il proprio perimetro senza che nessuno scriva nulla.** Se lo compilassimo a mano andrebbe riscritto per ogni installazione e invecchierebbe il giorno dopo.
2. **Il perimetro non può contenere ciò che il sistema non sa fare**, perché nasce dalla stessa fonte che il modello riceve. Un suggerimento che non funziona sarebbe peggio del silenzio.

---

## 7. Decisioni richieste

| | Proposta | Nota |
|---|---|---|
| **D104** | Il vocabolario del catalogo è **mostrato all'utente**, suggerito e mai imposto | Scartato il perimetro obbligatorio con i tre argomenti di §3 |
| **D105** | Una condizione nominata **non fondata** nel frammento è rifiutata al livello 3, con lo stesso riconoscitore di termini della Fase A | Alza i rifiuti, abbassa le risposte sbagliate. Coerente con **D2** |
| **D106** | Il rifiuto **propone**: `clarification` con le opzioni prese dal perimetro | Riempie una funzione del contratto che il modello oggi non usa |

---

## 8. Cosa non fa

**Non alza l'accuratezza misurata.** Le 444 frasi di prova sono già scritte: nessun suggerimento le cambia. `filter` resta al 73,6% su quel corpus.

**Cambia però cosa si misura, e in meglio.** Oggi misuriamo *quanto il sistema indovina su frasi scritte alla cieca*. Servirà misurare anche *quanto ci azzecca su frasi scritte da chi vede i suggerimenti*, che è la situazione reale del prodotto. Sono due popolazioni distinte, ed è già previsto che ce ne sia più d'una (**D42**).

**Non sostituisce l'elicitazione.** **D85** — circa 200 enunciati raccolti da 8–10 persone di mestiere, che non richiede né clienti né prodotto attivo — resta il prerequisito: serve a scoprire **quali parole la gente usa davvero**, cioè a riempire il perimetro con la lingua giusta invece che con quella che immaginiamo noi. Le stesse interviste producono entrambe le cose.

---

## 9. Ordine di costruzione consigliato

1. **D105**, il controllo di fondatezza — è il pezzo che protegge l'utente, e il solo che abbia effetto anche senza interfaccia;
2. **D106**, il rifiuto che propone — trasforma il controllo in prodotto;
3. **D104**, il vocabolario visibile mentre si scrive — è la parte con più interfaccia e meno rischio;
4. la seconda popolazione di prova, dopo **D85**.

**Nessuno dei tre è urgente nel senso di rischioso**: il filtro sotto soglia tiene il profilo bloccato in stato bozza e **D80** (il divieto strutturale di attivare in produzione un profilo non qualificato) rifiuta l'attivazione. Nulla di sbagliato sta raggiungendo nessuno. Ciò che blocca davvero il progetto resta **D7** (due clienti pilota) e **D85**.
