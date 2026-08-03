# FINE TUNING DEL MODELLO — analisi e scelta della modalità

Documento di decisione per l'Architect. Scritto il 3 agosto 2026, su richiesta di
addestrare il modello a produrre il DSL con precisione.

Non è una proposta generica: ogni numero qui dentro è misurato su questa installazione
o verificato su fonti citate in fondo. Dove non lo è, è scritto che è una stima.

---

## §1 — Il criterio di accettazione, prima di tutto il resto

La richiesta è *«un livello dove il modello risponde esattamente a tutte le nostre
interrogazioni»*. Va tradotta in un numero, altrimenti non sapremo mai se ci siamo
arrivati.

**«Esattamente tutte» non è ottenibile come garanzia, e prometterlo sarebbe disonesto.**
Un modello è un sistema statistico: la probabilità che sbagli non arriva a zero. Quello
che *è* ottenibile, ed è quello che serve al prodotto, sono due cose insieme:

1. **una soglia alta e misurata** sulle domande che sappiamo esprimere;
2. **un rifiuto onesto** quando il modello non è sicuro — che è già l'architettura di
   oggi (**D118**, il rifiuto si guadagna; **D2**, meglio un errore che l'utente vede
   di uno che crede).

La differenza è tutta qui: un modello che sbaglia il 2% delle volte **e lo dice** è un
prodotto; uno che sbaglia lo 0,5% delle volte in silenzio non lo è.

### Le soglie che proponiamo

| misura | oggi | soglia di accettazione |
|---|---|---|
| corrispondenza esatta dello stato, su applicazioni **mai viste** | non misurata | **≥ 95%** |
| corrispondenza esatta, applicazioni viste in addestramento | 70,0% | ≥ 97% |
| sezione `filter` (la più difficile) | 79,5% | ≥ 95% |
| buste strutturalmente valide (livelli 1-2) | ~94% (6% riparate) | **100%** |
| condizioni infondate (livello 3) | 0 | **0** — non si tratta |
| rifiuti sbagliati: risponde a ciò che va rifiutato | non misurata | **0** |
| riferimenti prodotti **presenti nel catalogo di quel caso** | non misurata | **100%** |
| corrispondenza esatta su cataloghi a **termini inventati** | non misurata | ≥ 90% |
| corrispondenza esatta con **catalogo in inglese**, domanda italiana | non misurata | ≥ 90% |
| le 54 frasi della batteria sul campo | 2 su 3 provate | tutte, o rifiutate onestamente |

Due righe contano più delle altre, e per ragioni diverse.

**«Risponde a ciò che va rifiutato»** è il cancello del prodotto: se dopo l'addestramento
il modello genera un preventivo invece di rifiutare, abbiamo peggiorato il prodotto anche
se l'accuratezza è salita di venti punti.

**«Riferimenti presenti nel catalogo di quel caso»** è il termometro del mandare a
memoria: un riferimento inventato è un modello che sta **ricordando invece di leggere**,
ed è l'unico difetto che non si vede dall'accuratezza — perché sulle entità addestrate
ricordare funziona benissimo. Il perché è in §5bis.

**E serve una linea di partenza fresca.** L'ultima misura completa (70,0%) è del
2 agosto e da allora sono passate venti delibere. Prima di addestrare va rifatta,
altrimenti non sapremo cosa ha comprato l'addestramento.

---

## §2 — Cosa addestriamo, e cosa no

**Una sola attività**: da una frase italiana più un catalogo, produrre la busta del
contratto. Niente riassunti, niente consigli, niente scritture.

L'esempio di addestramento ha esattamente la forma della richiesta di produzione:

    sistema   il messaggio di `prompt.system_message()` — regole + catalogo
    utente    la frase
    risposta  la busta JSON

**Il catalogo dev'essere nell'ingresso, e variabile.** È la decisione tecnica più
importante di tutto il documento. Se il catalogo non c'è, il modello impara a
*indovinare* i riferimenti invece di leggerli, e distruggiamo la proprietà più forte
dell'architettura: **D101** e **D102** (generazione vincolata sull'insieme chiuso dei
riferimenti che quell'utente può nominare) garantiscono che nessuno possa nominare ciò
che non gli spetta. Un modello che ha imparato i riferimenti a memoria comincerebbe a
proporne di non mostrati, e il vincolo li rifiuterebbe: risposta persa, e per colpa
nostra.

Se invece il catalogo varia a ogni esempio — entità diverse, budget diversi,
sottoinsiemi diversi di attributi — l'unico modo che il modello ha di rispondere bene è
**leggerlo**. È quella l'abilità che vogliamo nei pesi.

**Cosa non entra nei pesi**: i nomi delle entità, i sinonimi di una particolare
installazione, le categorie di un cliente. Quelli stanno nel dizionario e nel catalogo,
dove si aggiornano senza riaddestrare nulla (**D108**, il registro delle voci
approvate). Un modello che sapesse a memoria le entità di questa installazione andrebbe
riaddestrato al primo cliente nuovo.

---

## §3 — LoRA o QLoRA: l'analisi

### Cosa sono, in due righe

Addestrare tutti i 9 miliardi di parametri richiederebbe centinaia di gigabyte e
produrrebbe un modello intero da conservare. **LoRA** congela il modello e aggiunge
piccole matrici a fianco dei suoi strati: si addestrano quelle, e il risultato è un
file di poche decine di megabyte. **QLoRA** fa lo stesso ma tiene il modello congelato
in 4 bit invece che in 16, il che dimezza abbondantemente la memoria al prezzo di un
po' di rumore di quantizzazione.

### I conti di memoria, per il nostro caso

Il nostro esempio medio è lungo: circa **4 200 gettoni** (§5). La memoria serve per i
pesi, per le attivazioni e per gli stati dell'ottimizzatore.

| | pesi congelati | attivazioni (4-5k gettoni, con ricalcolo) | ottimizzatore LoRA | **totale** |
|---|---|---|---|---|
| **LoRA 16 bit** | 18 GB | 4-8 GB | ~0,7 GB | **25-30 GB** |
| **QLoRA 4 bit** | 5,5 GB | 4-8 GB | ~0,7 GB | **11-15 GB** |

Conseguenza diretta: **QLoRA entra in una scheda da 24 GB, LoRA a 16 bit no** — serve
una da 48 GB.

### La scelta, e perché non è quella ovvia

Il consiglio più diffuso è *«QLoRA su una 4090»*. Per noi è un **falso risparmio**:

* una RTX 4090 (24 GB) costa **$0,34/ora**, una RTX A6000 (48 GB) **$0,49/ora**.
  Quindici centesimi l'ora di differenza;
* QLoRA è più **lento** per passo, perché a ogni moltiplicazione i pesi vanno
  dequantizzati. Il conto finale in dollari si pareggia, o va a favore dei 16 bit;
* la quantizzazione a 4 bit introduce rumore proprio sul modello congelato che il
  nostro compito usa di più — la lettura letterale di token dal catalogo. Sulla
  fedeltà a un formato è un rumore che non voglio pagare per quindici centesimi.

> **Scelta: LoRA a 16 bit, su una scheda da 48 GB o più.**
>
> QLoRA resta la strada di riserva per le prove rapide da 500 esempi, dove la scheda
> piccola costa meno e la qualità non è il punto.

**Una nota onesta**: la letteratura dice che il divario fra LoRA e QLoRA è **piccolo**,
e su un compito di aderenza a un formato probabilmente trascurabile. Non sto dicendo
che QLoRA non funzionerebbe. Sto dicendo che qui non c'è ragione di accettare quel
piccolo divario, perché non ci fa risparmiare niente.

---

## §4 — Gli iperparametri, uno per uno

Ogni riga ha un perché, perché a copiare una tabella da un tutorial ci si arriva da
soli.

| parametro | valore | perché questo |
|---|---|---|
| **rango (r)** | **32** | 16 è lo standard per l'adattamento di stile; noi insegniamo una **grammatica** con venti operazioni e sette tipi di valore, che è più capacità. 64 lo terrei per il secondo giro, se il primo mostra che il modello non ce la fa (sotto-adattamento) |
| **alpha** | **64** (= 2r) | la regola usuale; con `rsLoRA` acceso, che rende la scala stabile ai ranghi alti |
| **dropout** | **0,05** | poco: il dataset è grande e pulito, e un dropout alto qui serve solo a rallentare |
| **moduli bersaglio** | **tutti i lineari** — `q,k,v,o,gate,up,down` | è la differenza che si misura di più. Solo attenzione costa meno e rende meno: le matrici del blocco di alimentazione sono dove il modello tiene *come si scrive* una struttura |
| **lunghezza massima** | **6 144** | copre il 99% dei nostri esempi (§5) con margine. Andare a 8k costerebbe memoria per casi che non serviamo |
| **passate (epoche)** | **2** | con 6-12 mila esempi, tre passate cominciano a mandare a memoria. Si guarda la perdita di validazione e si ferma lì |
| **passo (learning rate)** | **1e-4**, coseno, 3% di riscaldamento | 2e-4 è lo standard per LoRA; scendo per il rango alto e perché l'obiettivo è la **precisione**, non l'adattamento rapido |
| **lotto efficace** | **32** (batch 2 × accumulo 16) | lotti piccoli su esempi lunghi danno gradienti rumorosi; l'accumulo costa niente |
| **maschera della perdita** | **solo la risposta** | il prompt è per il 90% regole e catalogo identici: farci imparare sopra sarebbe spendere tutto l'addestramento a memorizzare il nostro stesso messaggio di sistema |
| **precisione** | bf16 | standard su schede moderne |
| **ricalcolo attivazioni** | acceso | è ciò che rende sostenibili i 6k gettoni |
| **DoRA** | **da provare al secondo giro** | è un miglioramento quasi gratuito di LoRA; non lo metto al primo giro perché voglio una linea di partenza pulita da confrontare |

**Il numero da guardare durante l'addestramento non è la perdita.** È la **percentuale
di buste valide** su un campione di validazione, controllata con il nostro validatore.
La perdita scende anche mentre il modello impara a scrivere JSON plausibile e sbagliato.

---

## §5 — Il dataset

### Da dove viene

L'**atlante** raccolto il 3 agosto 2026 da una banca dati con tutte e 35 le
applicazioni Odoo Community e l'italiano caricato:

    333 entita'    7 918 attributi    677 elenchi con i loro valori
    2 535 relazioni  1 439 testi  1 385 numeri  1 247 booleani  631 date

Raccolto con **la nostra introspezione**, non leggendo il sorgente: i tipi del
contratto e le regole di esposizione sono scritti una volta sola in `nli_semantics`, e
una seconda copia divergerebbe.

### Quanto grande, e perché non «il più grande possibile»

**La cura conta più del volume.** Diecimila esempi generati da dieci modelli di frase
insegnano dieci modelli di frase. Il numero che conta non è quanti esempi ci sono, ma
quante **forme diverse** contengono.

Proposta: **da 8 000 a 12 000 esempi**, così distribuiti:

| famiglia | quota | cosa insegna |
|---|---|---|
| interrogazioni semplici (una-due condizioni) | 35% | il caso comune |
| aggregazioni e raggruppamenti | 15% | somma, media, minimo, massimo, conteggio, per gruppo |
| espressioni di tempo | 15% | tutte quelle di `ai/16`, con l'ancora ambigua di **D135** |
| ordinamenti, limiti, colonne | 10% | le sezioni che oggi vanno bene e non devono peggiorare |
| raffinamenti (secondo turno) | 10% | *«e solo quelli di Roma»* — con lo stato precedente nel prompt |
| **rifiuti e chiarimenti** | **15%** | fuori ambito, ambiguità, e le frasi **miste** |

Su queste famiglie si sovrappongono **due assi indipendenti**, che non sono altre
famiglie ma proprietà che una quota degli esempi porta comunque:

| asse | quota | perché |
|---|---|---|
| **catalogo a termini inventati** | **10%** | etichette senza senso e riferimenti mescolati: lì una risposta a memoria non esiste, e l'unica strada è la lettura letterale. È il vaccino contro il mandare a memoria (§5bis) |
| **catalogo in inglese, domanda in italiano** | **15%** | è il caso reale di molte installazioni italiane su un Odoo non tradotto, ed è la porta per vendere fuori. Costa solo generarli ora; aggiungerlo dopo costa un riaddestramento |

La lunghezza segue la distribuzione **vera** dei nostri cataloghi, non una scelta a
tavolino: con il tetto di 60 attributi di **D31** e 24 gettoni per attributo, un prompt
va da ~3 500 gettoni (entità piccola, mediana 12 attributi) a ~4 700 (entità al tetto).
Addestrare a 1k o a 16k vorrebbe dire spendere l'addestramento su forme che il prodotto
non serve mai.

### La famiglia che vale doppio: i rifiuti

Il 15% di rifiuti **non è riempitivo**. È ciò che protegge la proprietà su cui regge
tutto. Dentro ci vanno:

* le scritture — *«genera un preventivo»*, *«crea un'attività di follow-up»* →
  `out_of_scope`, con il frammento citato;
* le previsioni — *«quali opportunità sono a rischio»*;
* **le frasi miste**, che sono le più difficili e le più realistiche:
  *«mostrami i clienti inattivi da oltre 90 giorni con fatturato sopra 10 000 e proponi
  una campagna di riattivazione»* — la prima metà è esprimibile, la seconda no;
* **la lettura dei documenti**, che l'evolutiva prevede: *«cosa dice il contratto di
  Rossi»* → un rifiuto con un motivo che nomina la cosa. Costa niente addestrarlo ora e
  un riaddestramento aggiungerlo dopo. **Richiede una delibera**: il vocabolario dei
  motivi di fuori ambito oggi ne ha cinque e questo sarebbe il sesto.

### Le divisioni

* **addestramento**: ~28 applicazioni;
* **validazione**: un campione delle stesse, per fermarsi al momento giusto;
* **prova, tenuta fuori**: **applicazioni intere mai viste** — manutenzione, eventi,
  ristorazione, corsi — più le **54 frasi della batteria**, scritte a mano.

Questa è la parte più importante di tutta la sezione. Se misuriamo sulle stesse
applicazioni su cui addestriamo, il numero salirà e il prodotto no — ed è lo stesso
difetto di forma che abbiamo trovato due volte nel codice questa settimana: *una prova
che esercita il caso in cui il difetto non si vede*.

### La garanzia di correttezza

Ogni esempio nasce **dall'intento e poi si verbalizza**, mai dal testo indovinando lo
stato. E prima di entrare nel dataset passa dal **nostro validatore**: se i livelli 1-2
rifiutano la busta, o l'applicatore non la sa applicare, non è un esempio — è un errore
che stavamo per insegnare.


---

## §5bis — Le entità che al momento dell'addestramento non esistono

Domanda dell'Architect, ed è la più importante di tutto il documento: **un modello
addestrato oggi risponde su un'applicazione installata domani?**

**Sì, e non per fortuna: è la proprietà che stiamo comprando.** Ma solo se il dataset
è costruito per insegnarla, e va misurata invece che sperata.

### Perché può funzionare

Il catalogo dell'entità è **nel prompt**, a ogni domanda. Se durante l'addestramento
quel catalogo cambia a ogni esempio — 333 entità, 35 applicazioni, budget diversi,
sottoinsiemi diversi di attributi — l'unica strategia che porta a una risposta giusta è
**leggerlo**. Il modello non impara *«crm.lead ha questi campi»*: impara *«l'entità è
quella in cima, gli attributi sono quelli elencati, i riferimenti si copiano
esattamente, le parole dell'utente si agganciano ai termini mostrati»*.

Quella è un'operazione, non una nozione. E un'operazione si applica a un catalogo che
non esisteva quando è stata imparata.

**E il vincolo tiene comunque.** Anche se il modello volesse inventare un riferimento,
la generazione vincolata (**D101**, **D102**) glielo impedisce: l'insieme ammesso è
costruito dal catalogo di quell'utente in quel momento. Il fine tuning migliora la
probabilità di scegliere bene *dentro* quell'insieme; non può allargarlo.

### Le tre cose che rendono vera questa proprietà

**1. Il catalogo varia, e varia molto.** Non solo entità diverse: anche forme diverse —
entità con quattro attributi e entità al tetto di sessanta, entità senza nessuna data,
entità di soli elenchi, entità con etichette lunghe e con etichette di una parola.
L'atlante le contiene tutte perché le contiene Odoo.

**2. Una quota di cataloghi con parole che il modello non può conoscere.** È il
trucco più forte e va scritto: in una parte degli esempi i termini sono **inventati** —
etichette senza senso, riferimenti mescolati. Su quegli esempi *non c'è* una risposta
raggiungibile a memoria: l'unica strada è la lettura letterale. È un vaccino contro il
mandare a memoria, e costa solo generarli.

**3. L'insieme di prova è fatto di applicazioni intere mai viste.** È l'unica misura
che risponde davvero alla domanda. Se l'affinato fa ≥95% su manutenzione, eventi,
ristorazione e corsi — che in addestramento non ha visto — allora l'applicazione che il
cliente installerà il mese prossimo si comporterà come quelle. Se invece va bene solo
sulle applicazioni addestrate, **ha imparato a memoria**, e lo sappiamo prima di
metterlo in servizio invece che dopo.

### I due limiti veri, detti chiaramente

**Il gergo nuovo non lo risolve il modello, lo risolve il dizionario.** Se un modulo
verticale porta la parola *«ddt»* e l'etichetta di Odoo dice *«Documento di
trasporto»*, l'aggancio fra le due avviene nel **nostro** indice dei termini (fase A e
il riconoscitore del livello 3), non nei pesi. La strada è **D108** (il registro delle
voci approvate), e funziona senza riaddestrare niente. Questo è un bene: la parte che
cambia da cliente a cliente sta dove si aggiorna in un minuto.

**Un cambio del contratto invece invalida i pesi.** Se aggiungiamo un'operazione al
vocabolario, un tipo di valore, o cambiamo il significato di un predicato — come ha
fatto **D113** togliendo `between` sulle date — il modello ha imparato la grammatica
*di ieri*. Lì si riaddestra. Il costo è contenuto e va detto: il dataset si **rigenera**
da atlante più generatore, la corsa costa ~$11, e la ricetta è un file YAML nel
repository. Riaddestrare è mezza giornata, non un progetto.

### La lingua: decisa

Le domande sono **in italiano**, perché il prodotto lo è. I **cataloghi no**: il 15%
degli esempi porta un catalogo con le etichette **in inglese** e la domanda in italiano.

Il motivo non è l'estero, o non solo. Un'installazione Odoo può girare in inglese e le
etichette del catalogo sono in quella lingua: succede spessissimo anche in Italia, su
installazioni mai tradotte. Un modello addestrato solo su cataloghi italiani se la
caverebbe peggio proprio lì — non per la frase dell'utente, che resta italiana, ma per i
termini a cui deve agganciarla.

Ed è il caso più difficile e più istruttivo che ci sia: *«mostrami gli ordini di questo
mese»* con un catalogo che dice `Order Date`, `Customer`, `Untaxed Amount`. Se il modello
lo risolve, ha imparato ad **agganciare significati**, non parole — che è esattamente
l'abilità che serve a un'entità mai vista.

Costa solo generarli: l'atlante si raccoglie una seconda volta su una banca dati senza
l'italiano caricato, e le due versioni si allineano per riferimento. Aggiungerlo dopo
costerebbe un riaddestramento.

### La misura che mettiamo nel cancello

Alle soglie di §1 se ne aggiunge una, ed è quella che risponde a questa domanda:

| misura | soglia |
|---|---|
| corrispondenza esatta su **applicazioni mai viste** | **≥ 95%** |
| riferimenti prodotti che sono **presenti nel catalogo di quel caso** | **100%** |
| corrispondenza esatta su cataloghi con **termini inventati** | **≥ 90%** |
| corrispondenza esatta con **catalogo in inglese**, domanda italiana | **≥ 90%** |

La seconda riga è il termometro del mandare a memoria: un riferimento inventato è un
modello che sta ricordando invece di leggere, e va visto **prima** del servizio.

---

## §6 — L'architettura dell'operazione

    pesi base            Qwen/Qwen3.5-9B  (Apache-2.0, da Hugging Face)
        │
        ├── dataset JSONL  ──►  addestramento LoRA 16 bit  ──►  adapter.safetensors
        │                        (una GPU affittata, ~5 ore)         ~150 MB
        │
        ▼
    convert_lora_to_gguf.py  (llama.cpp)  ──►  adapter.gguf
        │
        ▼
    Modelfile:  FROM qwen3.5:9b
                ADAPTER ./adapter.gguf
        │
        ▼
    ollama create aida-dsl  ──►  profilo nuovo in `nli.profile`  ──►  cancello D80

**L'adattatore non si fonde nel modello base**, ed è una decisione, non un dettaglio.
`ollama` sa caricare un adattatore GGUF accanto al modello con la direttiva `ADAPTER`,
e `llama.cpp` sotto permette di applicarne, scalarne e cambiarne più d'uno senza
toccare i pesi. Tenerli separati significa:

* la lettura dei documenti, quando arriverà, usa il **base** e non un modello
  specializzato a emettere sempre una busta;
* si può misurare base e affinato **fianco a fianco**, sullo stesso `ollama`;
* si torna indietro togliendo una riga.

Fondere resta la via di riserva se emergessero incompatibilità di formato
(`llama-export-lora` unisce i due GGUF), ma si perde tutto quanto sopra.

**Il quadro (framework) di addestramento.** Tre candidati seri: **Axolotl** (ricette
YAML, molto usato in produzione), **Unsloth** (più veloce e con meno memoria, pubblica
i pesi di Qwen3.5 già pronti), **torchtune** (ufficiale PyTorch, più verboso). Andrei
con **Axolotl** per la riproducibilità della ricetta — un file YAML che finisce nel
repository accanto al dataset è un pezzo di documentazione, non una sessione di
terminale che nessuno ricorda.

**Il modello base**: **non è più deciso qui.** `ai/19-scelta-del-modello.md` lo ha
misurato sul portatile col prompt vero e propone di affinare **Qwen3.5-4B** come
candidato principale e **Qwen3.5-2B** in parallelo, tenendo il 9B come riferimento e
riserva. Tutta la ricetta di questo documento vale identica per le tre taglie: cambia
una riga del file di configurazione, non il piano. Tutte e tre sono Apache-2.0.

**Attenzione**: l'adattatore va addestrato sui pesi della **stessa variante** che
`ollama` serve, altrimenti il comportamento è indefinito.

**E una conferma indipendente della scelta di §3**: chi pubblica i pesi di Qwen 3.5
**sconsiglia QLoRA a 4 bit** su questa famiglia per problemi di precisione, e raccomanda
LoRA a 16 bit. Ci eravamo arrivati con i conti di memoria e di costo; è utile sapere che
il consiglio arriva anche da chi ha addestrato questi modelli.

---

## §7 — Il servizio: confronto

| servizio | scheda | $/ora | note |
|---|---|---|---|
| **Vast.ai** | RTX 4090 24 GB | **0,29-0,39** | il più economico. Mercato fra privati: affidabilità e disponibilità variabili. 24 GB obbliga a QLoRA |
| **RunPod** | RTX A6000 48 GB | **0,49** | fatturazione **al secondo**, ambiente standard, regioni UE. 48 GB = LoRA a 16 bit |
| **RunPod** | A100 80 GB | **1,39** | margine per lotti più grandi e sequenze lunghe |
| **RunPod** | H100 PCIe 80 GB | **2,89** | la più veloce a nostra portata |
| **Lambda** | A100 40 GB | **1,99** | **niente spot**, e le SXM si vendono solo a gruppi di otto. Fattura anche le istanze ferme |
| **Lambda** | H100 PCIe | **3,29** | come sopra |

### La scelta

> **RunPod, RTX A6000 48 GB ($0,49/ora) per le prove; A100 80 GB ($1,39/ora) per le
> corse vere.**

Le ragioni, in ordine:

1. **48 GB è la soglia** che ci fa fare LoRA a 16 bit invece di QLoRA;
2. la **fatturazione al secondo** premia la disciplina giusta: prepari tutto in locale,
   carichi, corri, scarichi, spegni;
3. **regioni UE** disponibili — conta il giorno in cui nel dataset entrano gli enunciati
   veri di **D85**, che sono parole di utenti (**D54**, **D115**);
4. Lambda costa il triplo per la stessa cosa, non ha spot, vende le schede migliori solo
   a gruppi di otto e **fattura anche quando l'istanza è ferma**: per un lavoro
   discontinuo come il nostro è la scelta peggiore delle tre;
5. Vast.ai è il più economico e lo terrei per le prove rapide, ma con 24 GB si torna a
   QLoRA e con un mercato fra privati si torna a controllare che la macchina ci sia.

---

## §8 — I costi

Il conto si fa in gettoni processati. Con **10 000 esempi da ~4 200 gettoni** e **2
passate**, sono **84 milioni di gettoni**.

| scheda | $/ora | velocità stimata | una corsa | **costo** |
|---|---|---|---|---|
| RTX A6000 48 GB | 0,49 | ~1 200 gettoni/s | ~19 h | **~$9** |
| A100 80 GB | 1,39 | ~3 000 gettoni/s | ~8 h | **~$11** |
| H100 PCIe | 2,89 | ~6 000 gettoni/s | ~4 h | **~$12** |

**Il costo è quasi lo stesso ovunque** — le schede veloci costano in proporzione — e si
sceglie sul **tempo di attesa**, non sul prezzo. Con l'A100 una corsa sta in mezza
giornata di lavoro.

Preventivo dell'operazione intera:

| voce | stima |
|---|---|
| 2-3 prove di fumo da 500 esempi (A6000) | $2 |
| 3 corse vere (A100 80 GB) | $33 |
| valutazione dell'affinato sull'insieme tenuto fuori | $3 |
| spazio disco e traffico | $2 |
| **totale** | **~$40** |

Con un margine per due corse in più: **sotto i $70**.

> **Il costo non è un fattore di decisione.** Quaranta dollari non decidono niente: la
> cosa cara di questa operazione è il **dataset** e il nostro tempo. Il che significa
> anche che possiamo permetterci di sbagliare due corse, e va bene così.

Le velocità in tabella sono **stime**, non misure: la prima corsa di fumo ci darà il
numero vero, e a quel punto il preventivo si aggiorna con un dato invece che con
un'ipotesi.

---

## §9 — Il cancello: come entra in servizio

**D80** rifiuta di attivare un profilo non qualificato, e questa è la ragione per cui
quella regola esiste. L'affinato non sostituisce niente finché non ha passato:

1. la misura sul corpus con il contratto di oggi, **≥ 95%** sulle applicazioni mai
   viste;
2. **zero** risposte a ciò che va rifiutato;
3. **100%** di buste strutturalmente valide;
4. **100%** dei riferimenti prodotti presenti nel catalogo di quel caso — il
   termometro del mandare a memoria (§5bis);
5. **≥ 90%** sui cataloghi a termini inventati e **≥ 90%** con catalogo in inglese: le
   due prove che dicono se ha imparato a leggere o a ricordare;
6. la batteria sul campo, tutte le 54 frasi;
7. un confronto **fianco a fianco** con il modello base sullo stesso `ollama`: se
   l'affinato vince su meno di tre sezioni su otto, non vale il debito di
   manutenzione.

Se passa, diventa un profilo accanto agli altri, e **D116** lo fa scegliere dalle
impostazioni: si torna indietro con un menu a tendina, non con un ripristino.

---

## §10 — I rischi, e come li vediamo prima di pagarli

| rischio | come si manifesta | come lo vediamo prima |
|---|---|---|
| **impara i nostri modelli di frase** | la misura sale, il campo no | l'insieme di prova è fatto di applicazioni **mai viste** e delle 54 frasi scritte a mano |
| **impara i riferimenti a memoria** | inventa `ref` non mostrati, il vincolo li rifiuta, la risposta si perde | catalogo variabile a ogni esempio; e nella prova si misura la percentuale di riferimenti **presenti nel catalogo di quel caso** |
| **dimentica di rifiutare** | genera un preventivo invece di dire di no | il 15% di rifiuti nel dataset, e la riga «zero risposte a ciò che va rifiutato» è un cancello, non un indicatore |
| **perde la lingua generale** | inutile per la lettura dei documenti di domani | adattatore **non fuso**: il base resta intatto |
| **si lega a una versione del contratto** | ogni delibera che tocca il DSL invalida i pesi | il dataset si **rigenera** da atlante + generatore: riaddestrare costa $11, non un progetto |
| **la finestra tagliata falsa tutto** | addestriamo su cataloghi da 17 attributi | **prima** si alza la finestra a 8 192 (**D133**) e si rimisura |
| **installazione non tradotta** | il cliente ha Odoo in inglese, il modello aggancia peggio | il 15% degli esempi ha il catalogo in inglese, ed è una riga del cancello (§9) |
| **entità installate dopo** | il cliente aggiunge un'applicazione e il modello peggiora | l'insieme di prova è fatto di **applicazioni intere mai viste** (§5bis) |

---

## §11 — Cosa non facciamo, e perché

**Niente SQL fra gli strumenti del modello.** **V3** vieta di raggiungere PostgreSQL
senza passare dall'ORM, e c'è un controllo statico che lo verifica a ogni giro. Non è
pignoleria: l'ORM applica le regole di record, SQL grezzo no. Un modello che scrive SQL
scavalca i permessi di chi chiede.

**Niente recupero a similarità al posto del catalogo.** Le fasi A, B e C *sono* già il
recupero, e il nostro è **esatto**: l'insieme dei riferimenti ammessi è chiuso e la
generazione vincolata lo impone. Sostituirlo con una ricerca approssimata sarebbe
scendere proprio dove abbiamo la garanzia più forte.

**Niente scritture nel dataset.** Finché **D2** è in piedi, una busta che scrive non è
un esempio: è un difetto che stiamo per mettere nei pesi.

---

## §12 — L'ordine di lavoro proposto

1. **Alzare la finestra a 8 192** (server e profilo insieme, D133). Mezz'ora, gratis,
   e senza questo tutto il resto misura il taglio.
2. **Rimisurare la linea di partenza** sul corpus col contratto di oggi.
3. **Pulire l'atlante**: separare i nomi delle entità dalle voci di menu filtrate — le
   seconde diventano candidate categorie. E **raccoglierlo una seconda volta senza
   l'italiano**, per la quota di cataloghi in inglese di §5bis: è lo stesso comando su
   una banca dati senza la lingua caricata, e le due versioni si allineano per
   riferimento.
4. **Strato dei sinonimi** sulle famiglie nuove: magazzino, produzione, personale,
   progetti, contabilità.
5. **Generatore + dataset**, con le divisioni di §5.
6. **Prova di fumo** da 500 esempi su A6000: verifica la catena intera — addestramento,
   conversione, `ollama`, misura — e dà la velocità vera.
7. **Corsa vera** su A100, e misura sull'insieme tenuto fuori.
8. **Cancello di §9**, e solo allora il profilo va in servizio.

I passi 1 e 2 vanno fatti comunque, anche se il fine tuning non si facesse mai.

---

## Fonti

* [Qwen/Qwen3.5-9B-Base — Hugging Face](https://huggingface.co/Qwen/Qwen3.5-9B-Base)
* [Importing a model — Ollama (direttiva `ADAPTER`)](https://docs.ollama.com/import)
* [Does llama.cpp support LoRA adapters in GGUF](https://github.com/ggml-org/llama.cpp/discussions/7785)
* [Cloud GPU Instances — RunPod](https://www.runpod.io/product/cloud-gpus)
* [How Much Does RunPod Cost? The Real 2026 GPU Price](https://hackceleration.com/labs/runpod-pricing)
* [Vast.ai RTX 4090 Price (Apr 2026)](https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing)
* [Lambda Labs GPU Cloud Pricing 2026](https://gpuvec.com/providers/lambda)
* [LoRA vs. QLoRA — Red Hat](https://www.redhat.com/en/topics/ai/lora-vs-qlora)
* [LoRA Learns Less and Forgets Less (arXiv)](https://arxiv.org/pdf/2405.09673)
