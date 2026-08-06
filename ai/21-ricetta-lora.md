# LA RICETTA DEL LORA — dal dataset al profilo in servizio

Documento operativo. Scritto il 6 agosto 2026, su richiesta dell'Architect: *«stila una
ricetta per avviare il LoRA, seleziona con cura tutto il dataset che ci serve, e rendilo
super performante»*.

**Cosa NON ripete.** `ai/18-fine-tuning.md` ha già deciso *cosa* addestriamo (una sola
attività: frase italiana + catalogo → `envelope` del contratto), *come* (LoRA a 16 bit e
non QLoRA), *dove* (RunPod), *quanto costa* (~$40) e *il cancello* di **D80** (la
decisione che rifiuta di mettere in servizio un profilo non qualificato).
`ai/19-scelta-del-modello.md` ha scelto le taglie. Quei due documenti restano la
specifica.

**Cosa aggiunge questo.** Le tre cose che mancavano per premere il pulsante:

1. una **decisione nuova** che vale, da sola, il 58% del tempo di risposta (§2);
2. la **strategia di selezione del dataset** — non «genera diecimila esempi», ma
   *quali* diecimila, scelti come, e con quale prova che siano i giusti (§4);
3. la **ricetta letterale**: il file di configurazione, i comandi, e cosa si guarda
   mentre la corsa gira (§6, §7, §8).

---

## §0 — In una riga

Non stiamo insegnando al modello a capire l'italiano: lo sa già. Gli stiamo insegnando
**come si scrive un `envelope`** e **come si legge un catalogo**. Sono due abilità
strette e meccaniche, ed è il caso in cui un modello piccolo affinato batte un modello
grande generico.

L'analogia: un cuoco bravo che riceve ogni volta una dispensa diversa e una ricetta di
otto pagine. Oggi rilegge le otto pagine ogni piatto — sono due terzi del suo tempo.
Il fine tuning gli mette la ricetta **in testa**. Resta la dispensa, che cambia
davvero e va letta ogni volta.

---

## §1 — I tre cancelli prima di generare un solo esempio

Un dataset costruito su un contratto che sta per cambiare è lavoro buttato: `ai/18` §10
lo dice fra i rischi — *«si lega a una versione del contratto»*. Rigenerarlo costa poco
($11 di corsa), ma il **nostro** tempo di curatela no. Quindi:

### 1.1 Il contratto dev'essere fermo

**D141** (la decisione del 6 agosto che mette nel vocabolario i periodi che una frase
nomina: `month_of_year`, `quarter_of_year`, `half_of_year`, `year_of`) è di ieri. Se ne
arriva un'altra dopo aver generato, si rigenera.

**Il pezzo che bloccava era P0b** — la rete contro il ripiego silenzioso — e **è
chiuso**: **D144** (`00` §48), deliberato e implementato il 6 agosto. Bloccava perché
decideva **cosa il dataset deve insegnare a rifiutare**: se un periodo inesprimibile
(*«nel primo bimestre»*) va rifiutato è una famiglia di esempi, se il vocabolario si
allarga sono simboli nuovi. Sono due dataset diversi.

**La risposta è la prima**, e ora è nel codice: un'espressione temporale è rifiutata
quando il frammento che la cita nomina un periodo che quell'espressione non è. Quindi
`ai/21` §5.1 può scrivere quella famiglia senza aspettare altro.

Il fine tuning è **anche** una rete contro il ripiego, ed è bene dirlo: addestrare
«periodo che il vocabolario non sa dire → `clarification`» mette la rete nei pesi. Ma
una rete statistica non è una garanzia, e §46.7 chiedeva una garanzia. **Le due cose
convivono e nessuna sostituisce l'altra**: il livello deterministico garantisce, i pesi
fanno sì che la garanzia debba intervenire di rado.

### 1.2 La linea di partenza dev'essere fresca

`ai/18` §1 lo pretende: *«prima di addestrare va rifatta, altrimenti non sapremo cosa ha
comprato l'addestramento»*. Oggi abbiamo **due** linee, e servono entrambe:

| misura | ultimo valore | quando è stata presa | va rifatta? |
|---|---|---|---|
| corpus, 414 aperture | **74,6% complessiva, `filter` 85,0%** | **6 agosto**, `context` 8192 | **no, è fatta** (`00` §48.7) |
| batteria sul campo, 54 frasi | 39/54 (72%) | 6 agosto | **no**, è fresca — ma non copre i secondi turni (`00` §46, la lezione di §11 del 5 agosto) |

La prima costa ~65 minuti di macchina e nessuna attesa umana. Si lancia e si va avanti
con altro.

### 1.3 Il catalogo servito dev'essere quello vero

Se `ollama` serve 4096 `token` di `context` mentre il profilo ne dichiara 8192
(**D133**, la decisione che impone di guardare vicine la finestra dichiarata e quella
servita), ogni misura misura il taglio — e questo vale **anche per la misura di
valutazione dopo l'addestramento**, dove sarebbe ancora più difficile da vedere perché
avremmo un colpevole comodo («il fine tuning non ha funzionato»).

    curl -s http://127.0.0.1:11434/api/ps | grep context_length

---

## §2 — D142 (proposta): il messaggio di sistema si sposta nei pesi

**È la decisione più importante di questo documento**, e `ai/18` §2 non la prende: dice
che l'esempio di addestramento ha come parte di sistema *«il messaggio di
`prompt.system_message()` — regole + catalogo»*. `ai/19` §3 invece conta il guadagno
assumendo che dopo l'addestramento **quelle regole non si mandino più**. Le due cose non
possono essere vere insieme, e la differenza vale 2 370 `token` a domanda.

### 2.1 Il fatto che la rende facile

Il nostro `prompt` è già diviso nel modo giusto, e non l'avevamo fatto per questo:

    system_message(request)  =  INSTRUCTIONS + vocabolari chiusi   COSTANTE
    user_message(request)    =  catalogo + stato + pending          VARIABILE

Misurato sul sorgente di `custom_addons/nli_engine/prompt.py`: `INSTRUCTIONS` è **8 099
caratteri ≈ 2 249 `token`**, i vocabolari chiusi portano il totale a ~2 370. Su un
`prompt` reale da 4 077 `token` (`ai/19` §1, catalogo di `crm.lead` al tetto di 60
attributi di **D31**) sono **il 58%**, e sono **identici a ogni singola domanda**.

La parte che cambia — il catalogo — sta già tutta nel messaggio dell'utente. Quindi
togliere le regole è **cancellare una funzione**, non riscrivere il `prompt`.

### 2.2 La decisione

> **Il dataset porta due forme del `prompt`, e il profilo affinato serve quella corta.**
>
> * **forma lunga** (`system_message()` intero), su una quota del dataset;
> * **forma corta**: un messaggio di sistema di poche righe che nomina il compito e la
>   versione del contratto, e nient'altro.
>
> Quota proposta: **75% corta, 25% lunga.**

**Perché due e non solo la corta.** Tre ragioni, in ordine:

1. **Il ritorno indietro resta possibile.** Se l'affinato non passa il cancello, il
   profilo torna al modello base con **D116** (la decisione che fa scegliere il modello
   dalle impostazioni) — e il modello base ha bisogno delle regole. Un adapter che
   funziona *solo* senza regole ci lega le mani.
2. **Il modello impara che le regole non contraddicono il compito.** Vedendo le due
   forme produrre la stessa risposta, impara che il testo lungo è ridondante, non che è
   assente. È robustezza, non ridondanza.
3. **Costa zero.** È lo stesso esempio con un campo diverso: nessun `token` di
   addestramento in più oltre a quelli della forma lunga, che sono comunque nel budget.

**Perché la corta domina.** Perché è quella che il prodotto servirà. Addestrare al 50/50
significa comprare metà del guadagno.

### 2.3 Cosa contiene la forma corta

Il minimo che identifica il compito e la versione, perché il giorno in cui il contratto
cambia il `prompt` deve **dirlo**, non lasciarlo indovinare:

    AIDA DSL 1.0. Answer one JSON envelope, nothing else.

Una riga. La grammatica, i vocabolari chiusi, le venti operazioni e i sette `kind` di
valore stanno nei pesi.

**Il rischio, dichiarato**: se qualcuno cambia il contratto e non cambia la stringa di
versione, il modello produce la grammatica di ieri e nessuno se ne accorge. Serve una
prova nella suite che leghi la stringa alla versione del contratto — la stessa forma di
prova di `00` §46.8, quella che fallisce se qualcuno scollega il `prompt` dal
vocabolario. È la lezione di `00` §38 (sette volte in tre giorni: codice dichiarato,
provato e non collegato) applicata prima invece che dopo.

### 2.4 Cosa ci aspettiamo, scritto prima di misurare

Proiezione di `ai/19` §6, con i numeri veri del portatile:

| | `prompt` letto | risposta scritta | totale |
|---|---|---|---|
| 4B oggi | 4 077 `token` @ 417 g/s = 9,8 s | 985 `token` @ 34,9 g/s = 28,2 s | **~41 s** |
| 4B affinato, forma corta | ~1 700 @ 417 = 4,1 s | ~200 @ 34,9 = 5,7 s | **~10 s** |

Sono **proiezioni**. Se dopo la prova di fumo il `prompt` non scende sotto i 2 000
`token` o la risposta non sta sotto i 250, la previsione era sbagliata e va detto.

---

## §3 — Le tre leve della velocità, in ordine di resa

«Super performante» ha due significati e vanno tenuti separati: **giusto più spesso** e
**pronto prima**. Il fine tuning compra tutti e due, ma con leve diverse.

| leva | quanto rende | dove si attiva |
|---|---|---|
| **1. `prompt` corto** (§2) | −58% sul tempo di lettura, che è metà del problema | dataset + profilo |
| **2. `envelope` compatto** | da 985 a ~200 `token` scritti: **−80% sul tempo di scrittura** | serializzazione del dataset (§3.1) |
| **3. taglia più piccola** | 4B legge quasi il doppio del 9B | `ai/19`, scelta già fatta |

Moltiplicate, sono la differenza fra 41 secondi e 10.

### 3.1 L'`envelope` compatto non è una preferenza estetica

Il modello scrive **esattamente come gli abbiamo insegnato**. Se nel dataset le risposte
hanno rientri, spazi dopo i due punti e chiavi in ordine casuale, il modello li
riprodurrà — e ogni spazio è un `token`, e ogni `token` è tempo.

> **Regola: nel dataset l'`envelope` è serializzato in forma canonica, byte per byte.**
>
>     json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
>
> Chiavi nell'ordine dello schema, nessun rientro, nessuno spazio, `confidence` con al
> massimo due decimali.

E dev'essere **la stessa forma canonica che il nostro validatore produce**, altrimenti
stiamo insegnando una serializzazione e verificandone un'altra. Il punto di verità è
`ai/corpus/verifica_contratto.py` (`_stabilita_canonica`).

**Il secondo guadagno, meno ovvio.** In servizio la generazione vincolata di **D101** e
**D102** (l'insieme chiuso dei riferimenti che quell'utente può nominare) rifiuta i
`token` fuori grammatica e ne fa riscrivere altri. Un modello addestrato a produrre
*già* la forma grammaticale fa intervenire il vincolo quasi mai: meno riscritture, meno
tempo. Il vincolo resta acceso — non è ridondanza, è la garanzia — ma smette di essere
sul percorso caldo.

---

## §4 — La strategia del dataset: si sceglie, non si genera

`ai/18` §5 dice la cosa giusta — *«la cura conta più del volume»* — e si ferma alle
quote per famiglia. Questa sezione la rende eseguibile.

**Il principio.** Non generiamo 10 000 esempi. Ne generiamo **40 000 e ne scegliamo
10 000**, e il criterio di scelta è la **copertura delle forme**, non il caso.
Generare è gratis (CPU, nessun modello); scegliere male costa una corsa e — molto
peggio — un modello che sembra buono e ha imparato dieci modelli di frase.

### 4.1 La firma di un esempio: l'unità di diversità

Ogni esempio generato porta una **firma**, cioè la lista di ciò che quell'esempio
*insegna*. Due esempi con la stessa firma insegnano la stessa cosa, per quanto le parole
siano diverse.

| asse della firma | valori |
|---|---|
| **entità** | il `ref` (`crm_lead`, `stock_picking`, …) e l'applicazione che la porta |
| **forma del catalogo** | fascia di attributi (4-9 / 10-19 / 20-39 / 40-60), ha date sì/no, ha elenchi sì/no, ha relazioni sì/no |
| **lingua del catalogo** | italiano / inglese / **termini inventati** |
| **forma dell'intento** | insieme delle operazioni, predicati usati, `kind` dei valori, simbolo temporale, aggregazione, presenza di gruppo / ordine / limite |
| **forma linguistica** | modello di verbalizzazione + perturbazione applicata (`Verbalizzatore` e `Perturbatore` di `ai/corpus/genera_corpus.py`) |
| **turno** | apertura / raffinamento (con stato precedente nel `prompt`) |
| **esito** | `operations` / `clarification` / `out_of_scope` + motivo |

La firma è il pezzo di ingegneria che rende «cura» una parola con un numero dietro.

### 4.2 Il forno: sovra-generare 4:1

Sorgente unica: **l'atlante** (`tools/finetuning/atlante.json`) — 333 entità, 7 918
attributi, raccolto con la nostra introspezione e non leggendo il sorgente, così i tipi
del contratto e le regole di esposizione restano scritti una volta sola.

Il generatore riusa la catena che esiste già in `ai/corpus/genera_corpus.py`: intento →
stato normativo → verbalizzazione → perturbazione. **Mai il contrario**: un esempio non
nasce mai da un testo di cui si indovina lo stato (`ai/18` §5).

Due cose vanno aggiunte, e sono lavoro vero:

* **il catalogo variabile**. Oggi il generatore lavora su un pacchetto di otto entità
  scritto a mano. Qui il catalogo si costruisce per ogni esempio dall'atlante, con
  **budget variabile**: a volte 8 attributi, a volte 60. È la cosa che insegna a
  *leggere* invece di ricordare (`ai/18` §5bis) e non è un dettaglio di
  configurazione — è il cuore;
* **i cataloghi a termini inventati**. Etichette senza senso e `ref` mescolati, sullo
  stesso intento. Su quegli esempi una risposta a memoria non esiste.

### 4.3 I quattro filtri, in quest'ordine

| filtro | cosa toglie | perché è lì |
|---|---|---|
| **1. validatore** | ogni `envelope` che i livelli 1-2 rifiutano, o che l'applicatore non sa applicare | un esempio non valido è un difetto che stavamo per mettere nei pesi |
| **2. doppioni esatti** | stessa frase + stesso catalogo | inutili per definizione |
| **3. doppioni vicini** | Jaccard sui 5-grammi > 0,9 **dentro la stessa firma** | due modi di dire la stessa cosa sulla stessa forma non insegnano due cose |
| **4. tetto per modello di frase** | oltre N occorrenze della stessa coppia (modello di verbalizzazione × entità) | è l'unico argine al *«diecimila esempi da dieci modelli di frase»* |

**Il numero da guardare al filtro 1 non è quanti ne restano: è quanti ne sono caduti.**
Se il validatore scarta più del 2%, il generatore sta producendo qualcosa che il
prodotto non accetta, e va capito **prima** — è un difetto del generatore o una regola
che non conoscevamo.

### 4.4 La selezione per copertura

Sopravvissuti ai filtri: ~30 000. Bersaglio: 10 000. La selezione è **avida sulla
copertura**:

    celle_coperte = {}
    scelti = []
    finché len(scelti) < bersaglio:
        prendi l'esempio che copre il maggior numero di celle di firma
            ancora scoperte, fra quelli che non violano una quota
        aggiornagli le celle, mettilo in scelti

Detto in italiano: **a ogni giro si prende l'esempio che insegna la cosa più nuova.**
Quando non c'è più niente di nuovo da insegnare, il resto si riempie a caso rispettando
le quote — e quel punto, *quando* la copertura satura, è un'informazione da riportare:
se satura a 4 000 esempi, gli altri 6 000 sono volume e non cura, e il dataset
può essere più piccolo e la corsa più corta.

### 4.5 Le quote e i minimi assoluti

Le quote per famiglia restano quelle di `ai/18` §5 (35% interrogazioni semplici, 15%
aggregazioni, 15% tempo, 10% ordinamenti/limiti/colonne, 10% raffinamenti, 15% rifiuti;
più i due assi indipendenti: 10% termini inventati, 15% catalogo inglese).

Si aggiungono i **minimi assoluti**, che le quote non garantiscono:

> **Ogni simbolo del vocabolario chiuso compare almeno 50 volte.**

Vale per: le ~20 operazioni, i predicati di ogni tipo, i 7 `kind` di valore, **ogni**
espressione temporale — comprese le quattro nuove di **D141** — le 6 aggregazioni, le
viste, e i **5 motivi di fuori ambito** di `SCOPE_NOTES`.

Il perché è semplice: un simbolo visto tre volte è un simbolo non imparato, e sarà
proprio quello che il modello sbaglierà in servizio. Con 20 operazioni × 50 il costo del
minimo è ~1 000 esempi su 10 000: il 10% del dataset per coprire il 100% della
grammatica.

E un tetto, dall'altra parte:

> **Nessuna entità supera l'1,5% del dataset** (150 esempi su 10 000).

Senza, `res.partner` e `account.move` — che hanno più attributi e più forme — si
prendono un quarto del dataset e il modello impara quelle.

### 4.6 Le divisioni: per applicazione intera, non a caso

È la parte più importante e la più facile da sbagliare.

| divisione | cosa contiene | a che serve |
|---|---|---|
| **addestramento** | ~28 applicazioni | i pesi |
| **validazione** | un campione delle **stesse** applicazioni | fermarsi al momento giusto |
| **prova, tenuta fuori** | **applicazioni intere mai viste** — manutenzione, eventi, ristorazione, corsi — + le 54 frasi della batteria, scritte a mano | rispondere alla domanda vera |

Dividere a caso — l'80/20 che fa chiunque — produce un numero alto e falso, perché ogni
entità di prova avrebbe decine di fratelli in addestramento. È **lo stesso difetto di
forma trovato due volte nel codice questa settimana**: una prova che esercita il caso in
cui il difetto non si vede.

### 4.7 Il rapporto di copertura, che si commette insieme al dataset

Il dataset è un artefatto grande e opaco. Accanto ci va un file leggibile che dice cosa
c'è dentro:

    entità: 291 su 333 (42 sotto ATTRIBUTI_MINIMI o senza forme utili)
    applicazioni in addestramento: 28    tenute fuori: 7
    operazioni: 20/20    minimo 50: rispettato
    espressioni temporali: 24/24    minimo 50: rispettato
    predicati: 31/31     kind di valore: 7/7
    motivi di fuori ambito: 5/5
    fasce di catalogo: 4/4    lingua: it 75% / en 15% / inventata 10%
    copertura satura a: 6 340 esempi
    scartati dal validatore: 214 (0,7%)

**Se una riga dice zero, il dataset non è adottabile.** È lo stesso ruolo che il
rapporto di `verifica_contratto.py` ha per il corpus: un numero che si legge prima di
spendere, non dopo.

---

## §5 — Le famiglie difficili, scritte per esteso

Tre famiglie decidono se il prodotto migliora o solo il numero. Vanno scritte a mano
nella specifica del generatore, perché nessuna cade fuori da sola.

### 5.1 I rifiuti (15%) — la famiglia che protegge tutto il resto

Non è riempitivo. Se dopo l'addestramento il modello genera un preventivo invece di
rifiutare, **abbiamo peggiorato il prodotto anche con venti punti di accuratezza in
più**. Dentro:

* **le scritture** — *«genera un preventivo»*, *«crea un'attività di follow-up»* →
  `out_of_scope` con il frammento citato. **D2** (la decisione che vieta qualunque
  scrittura sui dati finché la Fase 2 non è misurata e superata) è in piedi: una busta
  che scrive non è un esempio, è un difetto in arrivo;
* **le previsioni** — *«quali opportunità sono a rischio»*, *«quanti lead avremo il mese
  prossimo»*;
* **le frasi miste**, le più realistiche: *«mostrami i clienti inattivi da oltre 90
  giorni con fatturato sopra 10 000 e proponi una campagna di riattivazione»*. Prima
  metà esprimibile, seconda no. Sono anche le più difficili da generare, e sono quelle
  che un utente vero scrive;
* **i periodi inesprimibili** — *«nel primo bimestre»*, *«nel quadrimestre»*: la rete di
  §46.7 messa nei pesi accanto a quella deterministica (§1.1);
* **i pezzi di frase che il vocabolario chiuso non sa dire** — *«i secondi 20 lead»*,
  *«i lead che non sono di Milano»*. Oggi il prodotto li **lascia cadere in silenzio**
  ed è un difetto aperto (`restart.md`, P3). Nel dataset diventano rifiuti espliciti:
  è la stessa classe di P0b, e insegnarla è gratis.

### 5.2 I raffinamenti (10%) — la famiglia che nessuna misura vede

La batteria apre **una conversazione nuova per ogni frase**, di proposito. Conseguenza,
scoperta il 5 agosto: un difetto che uccideva ogni conversazione dalla seconda battuta
in poi ha attraversato **tutte** le misure senza lasciare traccia.

Nel dataset il raffinamento porta lo **stato precedente** nel `prompt`, come in
produzione. E porta la sua trappola specifica: lo stato salvato **non ha i frammenti**
(`strip_provenance` li toglie finché **D54** non li pseudonimizza), quindi gli esempi di
raffinamento devono avere esattamente quella forma monca — o insegneremo al modello a
lavorare con un'informazione che in servizio non arriva mai.

### 5.3 Il catalogo in inglese (15%) — il caso più istruttivo che abbiamo

*«mostrami gli ordini di questo mese»* con un catalogo che dice `Order Date`,
`Customer`, `Untaxed Amount`. Se il modello lo risolve ha imparato ad **agganciare
significati**, non parole — che è precisamente l'abilità che serve su un'entità mai
vista.

**Costa meno di quanto `ai/18` §5bis prevedesse, ed è già fatto.** Quel documento
chiedeva una **seconda banca dati senza l'italiano caricato**. Non serve: l'inglese è la
lingua **sorgente** di Odoo e l'italiano è una traduzione che ci sta sopra, quindi le
etichette inglesi sono già nella stessa banca dati. Basta leggere con un'altra lingua nel
contesto:

    ./manage.sh atlante atlante            # 333 entità, etichette italiane
    ./manage.sh atlante atlante en_US      # le stesse 333, etichette inglesi

E le due versioni sono allineate per `ref` **per costruzione** — è lo stesso riferimento
a portare due nomi — invece che da un passo di allineamento che potrebbe sbagliare. Una
banca dati in meno da costruire e da tenere allineata.

**Verificato, non dichiarato**, raccolte le due nello stesso momento:

    entità             333 / 333, stesse chiavi
    attributi          7 918 it / 7 917 en
    etichette diverse  96,6%   (il 3,4% identico è «Email», «Partner»: uguali davvero)
    ref disallineati   1 attributo su 7 918

L'unico disallineamento è `hr_leave_accrual_level.sequence`, che in italiano ha
un'etichetta (*«sequenza»*) e in inglese non ne ha alcuna, quindi cade. Lo 0,013%: il
generatore lavora sull'**intersezione** dei riferimenti e la cosa finisce lì.

---

## §6 — La ricetta di addestramento

Quadro: **Axolotl**, perché la ricetta è un file YAML che finisce nel repository accanto
al dataset — cioè documentazione, non una sessione di terminale che nessuno ricorda.

File proposto: `tools/finetuning/ricette/aida-4b-lora.yml`.

```yaml
# AIDA — LoRA 16 bit su Qwen3.5-4B.
# I valori e il perché di ognuno stanno in ai/18 §4. Qui c'è solo la forma.
base_model: Qwen/Qwen3.5-4B-Instruct
model_type: AutoModelForCausalLM
tokenizer_type: AutoTokenizer

# --- LoRA (ai/18 §3, §4) ---------------------------------------------------
adapter: lora
lora_r: 32                  # grammatica, non stile: 16 non basta
lora_alpha: 64              # = 2r
lora_dropout: 0.05          # dataset grande e pulito
lora_target_linear: true    # q,k,v,o,gate,up,down — non solo attenzione
peft_use_rslora: true       # scala stabile ai ranghi alti
load_in_8bit: false
load_in_4bit: false         # 16 bit: la nota di Qwen su QLoRA, ai/19 §10

# --- Dati -------------------------------------------------------------------
datasets:
  - path: data/aida_train.jsonl
    type: chat_template
    field_messages: messages
chat_template: qwen3
test_datasets:
  - path: data/aida_val.jsonl
    type: chat_template
    field_messages: messages
    split: train

train_on_inputs: false      # perdita SOLO sulla risposta: il prompt è nostro
sequence_len: 6144          # copre il 99% degli esempi (ai/18 §5)
sample_packing: false       # vedi §6.1
pad_to_sequence_len: false

# --- Corsa ------------------------------------------------------------------
num_epochs: 2               # a 3 comincia a mandare a memoria
micro_batch_size: 2
gradient_accumulation_steps: 16   # lotto efficace 32
learning_rate: 0.0001       # 1e-4: rango alto, obiettivo precisione
lr_scheduler: cosine
warmup_ratio: 0.03
optimizer: adamw_torch_fused
weight_decay: 0.01
max_grad_norm: 1.0
bf16: auto
gradient_checkpointing: true      # è ciò che rende sostenibili i 6k token
flash_attention: true

# --- Cosa salviamo e quando -------------------------------------------------
output_dir: ./out/aida-4b-lora
saves_per_epoch: 4          # 8 punti di controllo: si valuta ognuno (§8)
evals_per_epoch: 4
logging_steps: 10
save_total_limit: 8
seed: 20260806              # una corsa che non si ripete non è una misura
```

Per il **2B** cambia una riga: `base_model: Qwen/Qwen3.5-2B-Instruct`. Per il **9B** di
riserva, `sequence_len` e `micro_batch_size` vanno rivisti alla memoria della scheda.

> **Onestà su questo file**: i nomi dei campi sono quelli di Axolotl come li conosco, e
> vanno verificati contro la versione che si installa il giorno della corsa — `axolotl`
> li ha rinominati più volte. Il primo comando di §7 è `preprocess` proprio per questo:
> fallisce in trenta secondi invece che dopo un'ora di corsa.

### 6.1 Perché `sample_packing: false`

L'impacchettamento cuce più esempi corti in una sequenza per non sprecare posti. I
nostri esempi sono lunghi ~4 200 `token` su un limite di 6 144: **ne entra uno e
basta**, quindi il guadagno è quasi zero. In cambio, se la maschera di attenzione
sbaglia anche solo su un caso limite, due cataloghi diversi finiscono nella stessa
finestra e il modello impara a leggere il catalogo sbagliato — che è **esattamente** il
difetto che stiamo spendendo tutto questo lavoro per evitare.

Prima corsa: spento. Se il tempo diventa un problema, si riaccende e si misura.

### 6.2 Il numero da guardare non è la perdita

`ai/18` §4 lo dice e vale la pena ripeterlo: **la perdita scende anche mentre il modello
impara a scrivere JSON plausibile e sbagliato.** Il numero vero è la **percentuale di
`envelope` validi** su un campione di validazione, controllata con il nostro validatore.
Come si ottiene in pratica: §8.

---

## §7 — I comandi, dall'inizio alla fine

### In locale, prima di affittare qualunque cosa

```bash
# 1. l'atlante, due volte — stessa banca dati, due lingue di lettura (§5.3)
./manage.sh atlante atlante           # -> tools/finetuning/atlante.json
./manage.sh atlante atlante en_US     # -> tools/finetuning/atlante_en.json

# 2. genera in eccesso, filtra, seleziona, e scrivi il rapporto
python3 tools/finetuning/genera_dataset.py \
    --atlante tools/finetuning/atlante.json \
    --atlante-en tools/finetuning/atlante_en.json \
    --genera 40000 --bersaglio 10000 \
    --tieni-fuori maintenance,event,pos_restaurant,website_slides \
    --out data/ --rapporto data/copertura.txt

# 3. il rapporto si legge PRIMA di spendere un dollaro
cat data/copertura.txt
```

Lo strumento `genera_dataset.py` **non esiste ancora**: è il lavoro di §11 passo 3, ed è
il pezzo più grosso di tutta l'operazione.

### Sulla macchina affittata

```bash
# RunPod, RTX A6000 48 GB per la prova di fumo — $0,49/ora, fattura al secondo
pip install -U axolotl
axolotl preprocess tools/finetuning/ricette/aida-4b-lora.yml   # fallisce subito se sbaglio
axolotl train      tools/finetuning/ricette/aida-4b-lora.yml
```

### Il ritorno a casa

```bash
# adapter -> GGUF -> ollama
python3 llama.cpp/convert_lora_to_gguf.py \
    --base Qwen/Qwen3.5-4B-Instruct out/aida-4b-lora --outfile adapter.gguf

printf 'FROM qwen3.5:4b\nADAPTER ./adapter.gguf\n' > Modelfile
ollama create aida-dsl-4b -f Modelfile
```

L'adapter **non si fonde** nel modello base (`ai/18` §6): si misura base e affinato
fianco a fianco sullo stesso `ollama`, e si torna indietro togliendo una riga.

---

## §8 — Come si guarda una corsa mentre gira

Otto punti di controllo (§6, `saves_per_epoch: 4` × 2 passate). Su ognuno, **offline e
non dentro Axolotl**, si fa girare la misura che conta:

1. si converte il punto di controllo in GGUF e lo si carica su `ollama`;
2. si eseguono **200 esempi di validazione** con `misura_accuratezza.py`, generazione
   vincolata accesa;
3. si registrano tre numeri: **% `envelope` validi**, **% `ref` presenti nel catalogo di
   quel caso**, **corrispondenza esatta**.

Il secondo è il **termometro del mandare a memoria**: un `ref` inventato è un modello che
sta ricordando invece di leggere, ed è l'unico difetto che l'accuratezza non mostra —
perché sulle entità addestrate ricordare funziona benissimo.

**La curva che vogliamo vedere**: validi e `ref` salgono presto e restano piatti;
l'esattezza sale piano. **La curva che ci ferma**: l'esattezza sale e i `ref` scendono →
sta imparando a memoria, si ferma alla passata prima.

---

## §9 — Il cancello

Invariato: `ai/18` §9, sette condizioni, e **D80** rifiuta l'attivazione finché non sono
passate. Si aggiungono le due misure di velocità che questo documento promette, perché
una promessa non misurata è una promessa:

| misura | soglia |
|---|---|
| `token` del `prompt` in servizio, forma corta | **< 2 000** |
| `token` scritti, mediana su 200 casi | **< 250** |
| tempo di risposta mediano, stessa macchina, stesso caso | **meno di un quarto di oggi** |

---

## §10 — L'ordine di lavoro, con i tempi

| # | cosa | costo | dipende da |
|---|---|---|---|
| 1 | ~~**P0b deliberata**~~ — **fatto**, D144 (`00` §48) | — | — |
| 2 | ~~**linea di partenza fresca**~~ — **fatto**: 74,6% (309/414), `00` §48.7 | — | — |
| 3 | ~~**atlante, raccolto due volte**~~ — **fatto**: 333 entità × 2 lingue, verificate allineate (§5.3) | — | — |
| 4 | **`genera_dataset.py`**: catalogo variabile, termini inventati, firma, filtri, selezione, rapporto | **2-3 giorni** — è il pezzo grosso | 1, 3 |
| 5 | **il rapporto di copertura si legge** (§4.7) | mezz'ora | 4 |
| 6 | **prova di fumo**, 500 esempi su A6000 | ~$2, mezza giornata | 4 |
| 7 | **due corse vere**, 4B e 2B, stesso dataset | ~$22, un giorno | 6 |
| 8 | **cancello** (§9) | mezza giornata | 7 |

**Il costo vero non sono i $40**: è il passo 4. Ed è lì che si decide se il modello
diventa performante o solo addestrato.

**Cosa parte in parallelo, oggi, senza aspettare niente**: **D85** — gli enunciati veri
elicitati da 8-10 persone di mestiere. Ha i tempi più lunghi di tutto e non dipende né
da clienti né dal prodotto attivo. Senza, il dataset resta fatto delle frasi che ci
scriviamo da soli, e la misura migliorerebbe più del prodotto.

---

## §11 — Cosa questa ricetta NON fa

* **Non tocca il dizionario.** Il gergo di un cliente (*«ddt»* per *«Documento di
  trasporto»*) si aggancia in **D108** (il registro delle voci approvate), non nei pesi,
  e si aggiorna in un minuto senza riaddestrare. È un bene: la parte che cambia da
  cliente a cliente sta dove si cambia in fretta.
* **Non mette SQL fra gli strumenti del modello.** **V3** vieta di raggiungere
  PostgreSQL senza passare dall'ORM, e un controllo statico lo verifica a ogni giro:
  l'ORM applica le regole di record, SQL grezzo no.
* **Non sostituisce il catalogo con un recupero a similarità.** Le fasi A, B e C *sono*
  già il recupero, e il nostro è **esatto**.
* **Non addestra scritture.** Finché D2 è in piedi, una busta che scrive è un difetto in
  arrivo, non un esempio.
* **Non allarga il vocabolario dei motivi di fuori ambito.** La lettura dei documenti
  (*«cosa dice il contratto di Rossi»*) sarebbe il sesto motivo e **richiede una
  delibera**: `SCOPE_NOTES` oggi ne ha cinque. Costerebbe niente addestrarla ora e un
  riaddestramento aggiungerla dopo — ma prima si numera.
