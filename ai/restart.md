Progetto AIDA — NLIL per Odoo 18. Repo ~/Learning/odoo-docker-env, branch **new-ai-agent**.

Il branch `ai-agent` è il ramo storico e si ferma al 29 luglio: `new-ai-agent` lo
riprende sopra la base UI corrente (`master`). Il lavoro continua qui.

# Da leggere per primo

- ai/00-registro-decisioni.md — cosa è deciso. Il changelog in fondo è la cronologia
  reale; §18 sono le sette delibere della qualificazione del profilo (D97–D103), §19
  le cinque del perimetro guidato (D104–D108), §20 la delibera della ripresa (D109) più
  il vincolo che non esisteva in nessun database, e §21 le tre dell'ancoraggio del tempo
  (D110–D112). §18.6 contiene due misure che non sono
  decisioni ma cambiano cosa si può affermare.
- ai/12-piano-implementazione.md — §2 le parti, §3 il percorso critico, §5 la tabella
  di avanzamento, §5.1 come si verifica.
- ai/13-perimetro-guidato.md — la proposta da cui nascono D104–D106, deliberate.
- ai/14-ancoraggio-del-tempo.md — la proposta da cui nascono D110–D112, deliberate.

Poi: `./manage.sh check` deve essere verde prima di toccare qualunque cosa.

# Stato al 29 luglio 2026

Parti 1–6 complete. Parte 8 (perimetro guidato) completa lato motore. Parte 7
(`nli_web`) **avviata**: fatta l'interpretazione scritta per una persona, resta il
resto.

Misura del profilo `qwen3.5:9b` su tutte le 444 aperture del corpus:

    complessiva 64,0%   target 98,4%   fields 88,1%   group_by 93,2%
    measures 98,4%      order_by 93,9%  limit 94,4%    presentation 98,4%
    filter 73,6%  <-- unica sezione sotto la soglia di D44 (85%)

Il profilo resta `draft` e D80 ne rifiuta l'attivazione: è il comportamento voluto,
non un residuo da sistemare in fretta.

Verifiche: 395 test in zona pura, 114 test Odoo, confini e contratto (948/948) verdi.

**Ripresa del 1 agosto 2026.** Il lavoro è stato riportato su `new-ai-agent` sopra la
base UI corrente. Niente è cambiato nel motore: `./manage.sh check` verde (948/948,
copertura 100%, 0 determinazioni sbagliate) e `./manage.sh test nli_test` verde. Sono
cambiati due fatti d'ambiente, entrambi descritti sotto: il modello si raggiunge via
host gateway, e `nli_test` ha già i sei moduli installati con i 50 004 partner del
popolatore.

La verifica della ripresa ha trovato due cose, deliberate in `00` §20 (il registro
delle decisioni, sezione della ripresa).

**D109** — la tabella che traduce i tipi di campo di Odoo nei tipi del contratto
(`char` → `text`, e altre undici righe) è ora la zona pura
`nli_semantics/platform_types.py`. Prima stava dentro `introspection/runtime.py`, che
importa l'ORM: chi la leggeva si tirava dietro l'ORM, e sul portatile l'ORM non c'è di
proposito. Conseguenza: il comando che misura l'accuratezza non partiva affatto.

**§20.2** — il `CHECK (context_window > 0)` di `nli_profile` aveva una virgola dentro
la stringa SQL. PostgreSQL rifiutava il comando, Odoo scriveva `ERROR` e proseguiva, e
il vincolo **non è mai esistito in nessun database**. Corretto, con i due test che lo
mostrano rifiutare e accettare. Test Odoo ora **116**.

Misura di controllo dopo lo spostamento: **65,0% su 40 aperture**, contro il 64,0%
misurato a luglio su 444. Stessa fotografia — 40 casi portano ±13 punti di incertezza,
quindi il numero conferma che nulla si è rotto, non che qualcosa sia migliorato.

**L'ancoraggio del tempo, 2 agosto 2026.** Tre decisioni deliberate in `00` §21, dalla
proposta `14`. **D110**: il catalogo dichiara l'ancora del tempo — una data se ne espone
una sola, l'insieme delle scelte se sono due o più, nulla se non ce ne sono. **D111**:
un'espressione di tempo non si lascia cadere; se non si colloca, si chiede. **D112**: le
categorie ammesse dalla generazione vincolata sono solo quelle che la frase nomina,
quindi una categoria infondata non è più scrivibile invece di essere rifiutata dopo.

Il corpus ha smesso di chiedere ciò che la frase non dice: 30 aperture su
`account.move.out_invoice` — l'unica entità con due date esposte — attendevano
un'operazione dove nessuno poteva indovinare quale delle due date. I testi sono gli
stessi, è cambiata l'attesa. Casi verificati **918** (erano 948), casi totali **1200**
invariati. Test puri **412** (erano 395), test Odoo **117** (erano 116), file in zona
pura **55** (erano 54).

**La rimisura è stata fatta, ed è in `00` §21.7.** Su tutte le 414 aperture:
complessiva **70,0%**, `filter` **79,5%**, zero condizioni infondate, riparazioni dal
2,9% al 6,3%.

Il confronto con il 64,0% di luglio **non vale**: la popolazione è cambiata di 30 casi
che erano fallimenti tutti e trenta. Ricalcolata sugli stessi 414, la riga di luglio
vale ~68,6% complessiva e ~79,0% su `filter`. Il movimento vero è **+1,4 punti
complessivi e +0,5 su `filter`**, cioè quasi niente.

Dei 414 casi, 33 contengono un'espressione di tempo e falliscono tutti. Si dividono in
tre gruppi da undici: **solo il predicato** (`between` invece di `within`, tutto il
resto giusto — l'ancora funziona), **rifiuto** (il modello si ferma su entità dove la
data è una sola), **altro** (fallimenti veri).

# Come lavoriamo

- sei il Senior Staff Engineer, io l'Architect. Ti ho delegato l'autorità decisionale
  caso per caso: quando trovi una lacuna o una contraddizione nei documenti,
  analizzala, delibera e registrala in ai/00 con la sua argomentazione. Niente domande
  bloccanti; decidi e vai, tranne per le azioni distruttive.
- **spiegami le cose in un linguaggio poco tecnico, con esempi concreti, e quando citi
  una sigla o un punto della documentazione metti fra parentesi di cosa tratta.** Non
  «D2 lo impedisce» ma «D2 (il cancello che vieta qualunque scrittura sui dati finché la
  Fase 2 non è misurata e superata) lo impedisce». **La glossa si verifica aprendo la
  riga del registro, non si ricorda**: una glossa sbagliata è peggio di nessuna glossa,
  perché chi legge si fida e non controlla. L'esempio qui sopra è nato proprio così —
  diceva che D2 vieta «risposte sbagliate con l'aria di essere giuste», che è un
  argomento che il registro porta *accanto* a D2, non ciò che D2 stabilisce. Dal
  1 agosto 2026 la regola vale **ovunque**: chat, documenti di `ai/`, commenti del
  codice, messaggi di commit (`ai/CLAUDE.md`, sezione «Documenti e sigle»).
- cerca sempre prima l'opzione che NON modifica il contratto, e scartala solo con un
  argomento. Così sono nate D87, D98, D101 e D106.
- **prima di attribuire un esito al fornitore, verifica che non sia stato il prompt a
  dettarlo.** Tre delle sette delibere di §18 correggono il metro e non il modello, e
  la misura sulla confidenza diceva l'opposto della verità finché il prompt conteneva
  il valore d'esempio che il modello copiava.
- nessun controllo può passare a vuoto: ogni verifica dichiara quanto ha ispezionato e
  l'ispezione vuota è un fallimento. Ogni controllo ha un test che lo mostra scattare
  **e** uno che lo mostra non scattare.
- niente deroghe inline: allentare una regola richiede una decisione numerata in ai/00.
- riporta gli esiti come sono, con i numeri. Un numero brutto misurato vale più di un
  numero bello asserito. Se una previsione si rivela sbagliata, dillo esplicitamente.

# Fatti d'ambiente che una sessione fredda perde per primi

**Il modello.** Gira su `ollama` **nativo dell'host**, 127.0.0.1:11434, con Metal. Il
container `ollama` è spento e non va riacceso: dentro Docker non c'è GPU e si va dieci
volte più piano. `granite4.1:8b` è scaricato ma il confronto con qwen non è mai stato
completato (D107 lo dichiara).

**Come lo si raggiunge, e perché è cambiato.** Dall'host: `http://127.0.0.1:11434/v1`.
Dal container: `http://host.docker.internal:11434/v1`, risolto dalla voce `extra_hosts`
di `docker-compose.dev.yml`. La vecchia via — il nome di container `ollama` sulla rete
esterna `qwen25_default` — è caduta insieme al container: quella rete la creava il
compose del modello, e con `ollama` nativo non esiste più. Di conseguenza
`NLI_ALLOWED_HOSTS` vale `host.docker.internal:11434,localhost:11434` in `.env` (è ciò
che vede il container), mentre lo script di misura gira **sull'host** e vuole
`127.0.0.1:11434` come nella riga di comando qui sopra: sono due punti di vista sulla
stessa porta, non due configurazioni in conflitto.

**Il comando della misura**, con i flag senza i quali il numero non vale niente:

    NLI_ALLOWED_HOSTS=127.0.0.1:11434 python3 ai/corpus/misura_accuratezza.py \
      --endpoint http://127.0.0.1:11434/v1 --profilo qwen3.5:9b \
      --vincolata --ragionamento none --finestra 4096 --casi 444

Senza `--vincolata` la generazione vincolata è spenta e si misura il vuoto; senza
`--ragionamento none` il modello spende la finestra dentro il pensiero e non risponde;
`NLI_ALLOWED_HOSTS` è obbligatoria (D77, fallimento chiuso: senza, ogni chiamata è
rifiutata e l'esito è `not_understood`). La finestra dichiarata è 4096 perché è quella
che il server serve davvero.

**Durate e affidabilità.** 444 aperture ≈ 65 minuti, 80 ≈ 12, 40 ≈ 6. σ della misura è
**zero** (D48 verificata con K=5): due esecuzioni sullo stesso campione danno lo stesso
identico numero, quindi un caso che si muove è un risultato. Resta l'incertezza
campionaria: ±13 punti su 40 casi, ±3 su 444.

**La banca dati di prova.** `nli_test` contiene **50 004 partner**, seminati dal
popolatore del banco di carico. I test non devono presumere una base vuota: usano una
città che nessun popolatore produce. Un test che passa solo su un database vuoto non è
un test.

**Trappole trovate sul campo.** `_fields` e `_order` sono attributi riservati di ogni
modello Odoo: definirli come metodi rompe l'ORM al caricamento. Le zone pure di
`nli_semantics/catalogue` e `nli_semantics/dictionary` non possono importare **nemmeno**
da `nli_core`: sono funzioni dei loro argomenti, e ciò che serve si passa.

# Cosa è stato deciso il 28–29 luglio

| | |
|---|---|
| D97 | Adattatore sintetico per il solo banco di carico, dietro variabile d'ambiente |
| D98 | Il profilo dichiara lo sforzo di ragionamento; senza, il modello non risponde |
| D99 | La direzione dell'ordinamento è derivata dal tipo, non chiesta al modello |
| D100 | I comparativi inclusivi distinti da quelli stretti nel lessico e nel corpus |
| D101 | I riferimenti sono un insieme chiuso nello schema del turno |
| D102 | I riferimenti hanno tre generi: entità, attributi, categorie |
| D103 | Il predicato è vincolato dal tipo dell'attributo |
| D104 | Il vocabolario del catalogo è mostrato all'utente, suggerito e mai imposto |
| D105 | Una condizione nominata non fondata nel proprio frammento è rifiutata |
| D106 | Il rifiuto propone: `clarification` con letture derivate dal catalogo |
| D107 | Modello di riferimento `qwen3.5:9b`, con il confronto interrotto dichiarato |
| D108 | Registro delle voci approvate + traduzione condizione tipizzata → dominio |

# Aperto, in ordine di quanto sblocca

1. **D7** (due clienti pilota) e **D85** (~200 enunciati elicitati da 8–10 persone di
   mestiere, non richiede né clienti né prodotto attivo). Sono le due cose che bloccano
   davvero, e nessun giro di misura le sposta. **D52** — la misura di quanto costa oggi
   la stessa informazione sull'interfaccia nativa — ha una scadenza che non dipende da
   noi: va fatta prima di attivare il primo utente, dopo non è più ottenibile.
2. **Parte 7**, il resto: il canale di chat, gli stati dell'attesa (`09` §5.2), i
   messaggi di rifiuto per carico (D69), i token di `ui_brand_tokens` con degradazione
   (D25), l'accessibilità (D71), l'aggregato nel piede di colonna (D89), e la resa
   visiva dei suggerimenti di 8c. Primo bersaglio di taratura: l'accettazione a **P95
   205 ms** contro i 50 ms di `00` §6.1.

   **Da decidere per primo, perché tocca ogni frase che scriveremo dopo.** Le parole
   che l'utente legge — «contenente Milano», «sopra 1000» — passano dalla funzione di
   traduzione di Odoo, `_()`. Quella funzione capisce in che lingua tradurre
   **guardando chi l'ha chiamata**: risale la pila delle chiamate e cerca la richiesta
   web in corso, o in mancanza di quella l'utente collegato.

   In `nli_web` viene chiamata da due posti dove non trova né l'una né l'altro: le
   lambda scritte a livello di modulo in `nli_interpretation.py` (21 righe delle 33 che
   usano `_()` in quel file) e la funzione annidata `rendered` in `nli_perimeter.py`
   riga 99. Dentro una richiesta web funziona lo stesso, perché la richiesta la trova.
   Ma **la frase dell'utente si interpreta sul cron** — è la parte 6, l'esecuzione
   asincrona: chi scrive accetta e se ne va, l'interpretazione la fa un processo
   separato più tardi. Lì la richiesta web non c'è. Esito: la frase esce **non
   tradotta**, in silenzio, lasciando solo un avviso nei log.

   Oggi non fa danno perché `in_words` non ha ancora chiamanti fuori dai test; lo farà
   appena il canale di chat la collega. Le tre strade: `self.env._()` (dice
   esplicitamente in che lingua, ma bisogna portare `self` dentro le lambda);
   `LazyGettext` (`odoo.tools.translate._lt`, che rimanda la traduzione al momento in
   cui la stringa si usa davvero); oppure costruire le formule dentro il metodo, dove
   il contesto c'è già. Va deliberata e registrata in `ai/00`: è la forma dello strato
   delle parole, non un ritocco.
3. **`filter` al 79,5%, e le due cose che lo tengono lì.** Rimisurato su tutte le 414
   aperture (`00` §21.7). Le due famiglie diagnosticate a luglio — il tempo e le
   categorie inventate — sono state affrontate da D110–D112 (`00` §21), e **hanno fatto
   quello che promettevano**: l'ancora regge, zero condizioni infondate su 414. Sul
   numero però non è cambiato quasi niente.

   I 33 casi con un'espressione di tempo falliscono tutti, in tre gruppi da undici:

   **a) Undici erano solo il predicato** — `between` invece di `within`, campo e
   periodo giusti. **Risolto da D113** (`00` §22.1): su una data l'intervallo si dice
   `within`, e `between` resta l'intervallo numerico.

   **b) Undici erano rifiuti**, quasi tutti su `sale.order` dove l'ancora è una sola
   data. Diagnosticati: nove uscivano con `scope_note: "previsione"` — il modello
   leggeva un periodo passato come una previsione, che il prompt dichiarava fuori
   portata. **Risolto da D114** (`00` §22.2): la regola dice adesso che un periodo che
   seleziona record esistenti non è una previsione.

   **c) Undici sono fallimenti veri**, e **restano**: il predicato possibile ma
   sbagliato, il valore preso male, le due condizioni fuse in una. Nessuna delle due
   decisioni li tocca.

   **La misura dopo D113 e D114 non è ancora stata fatta.** L'attesa, scritta in `00`
   §22.3 prima di misurare: complessiva ~75,3%, `filter` ~84,8% — ancora sotto la
   soglia di D44. Se il numero si muove di 2,7 punti invece di 5,3, dirà quale delle
   due decisioni ha funzionato e quale no.

   Il numero da guardare non è solo l'accuratezza: sono le condizioni infondate contate
   dal metro (zero) e i rifiuti prodotti. Le risposte sbagliate sono diventate rifiuti,
   che è il verso giusto ma non alza il punteggio.
4. **D27**: eseguire il banco di prova sui worker prefork (`./manage.sh loadtest <db>`,
   **non su `nli_test`**) e riportare i numeri per quello che sono.
5. Il confronto con `granite4.1:8b`, se serve rispondere a *«il 73,6% è del compito o
   del modello?»*. Riga di comando identica, cambia solo `--profilo`.
7. **La chat mostra le letture di un chiarimento ma non le fa scegliere.** **D106**
   (un rifiuto propone le letture plausibili) vuole che la soluzione sia derivabile dal
   catalogo, **senza tornare dal modello**: le operazioni della lettura sono gia' nella
   busta. Manca il percorso server che le applichi — applicatore, livelli 3-5,
   risolutore, esecutore, presentatore — cioe' la coda di `pipeline.run` senza la
   chiamata al modello. Finche' non c'e', le letture si mostrano e si riscrivono a mano:
   meno comodo, ma non finge. Un bottone che ripartisse dal modello contraddirebbe
   D106, che esiste proprio per non chiedere le alternative a chi ha appena sbagliato.

8. **La chat non mostra ancora i dati.** L'interpretazione si vede, i record no. La
   strada e' incorporare la vista lista di Odoo, che porta con se' ricerca,
   ordinamento, filtri, gestione colonne e paginazione — tutto cio' che `15` chiede per
   le tabelle — invece di riscriverle.

6. **Il ramo dell'ancora nulla non ha ancora una risposta.** D110 (`00` §21.1) dice che
   quando un'entità non espone nessuna data, il fatto si dichiara. Il prompt (§21.2)
   dice di rispondere con un chiarimento, ma un chiarimento richiede 2-4 opzioni e ogni
   opzione porta almeno un'operazione (`nli_core/contract/schema.py`): senza una data
   non c'è operazione da offrire. Serve una decisione dell'Architect su cosa fare in
   questo caso — il contratto non si tocca senza una decisione numerata. Nel corpus
   fondativo il ramo non è mai esercitato: il generatore costruisce condizioni
   temporali solo per le entità che hanno campi data, quindi le quattro entità senza
   data non ricevono mai un periodo.

# Cosa NON va fatto

Continuare a limare il prompt contro il corpus sintetico. Il corpus non è sigillabile
(D86) e negli ultimi giri ha prodotto frasi genuinamente ambigue e attese sbagliate.
Ogni punto strappato da qui in avanti rischia di essere prompt adattato al generatore,
che è la degradazione descritta da D42.

# Se vuoi solo ripartire senza rileggere tutto

Riprendi il progetto AIDA: leggi ai/00-registro-decisioni.md e
ai/12-piano-implementazione.md, verifica con ./manage.sh check, poi vai con il punto
che ti indico. Stesse regole di prima: deliberi tu le questioni che emergono e le
registri in ai/00, e mi spieghi le cose in modo non tecnico.
