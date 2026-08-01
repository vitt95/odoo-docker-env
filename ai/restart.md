Progetto AIDA — NLIL per Odoo 18. Repo ~/Learning/odoo-docker-env, branch **new-ai-agent**.

Il branch `ai-agent` è il ramo storico e si ferma al 29 luglio: `new-ai-agent` lo
riprende sopra la base UI corrente (`master`). Il lavoro continua qui.

# Da leggere per primo

- ai/00-registro-decisioni.md — cosa è deciso. Il changelog in fondo è la cronologia
  reale; §18 sono le sette delibere della qualificazione del profilo (D97–D103) e §19
  le cinque del perimetro guidato (D104–D108). §18.6 contiene due misure che non sono
  decisioni ma cambiano cosa si può affermare.
- ai/12-piano-implementazione.md — §2 le parti, §3 il percorso critico, §5 la tabella
  di avanzamento, §5.1 come si verifica.
- ai/13-perimetro-guidato.md — la proposta da cui nascono D104–D106, deliberate.

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
copertura 100%, 0 determinazioni sbagliate) e `./manage.sh test nli_test` verde (114 su
114). Sono cambiati solo due fatti d'ambiente, entrambi descritti sotto: il modello si
raggiunge via host gateway, e `nli_test` ha già i sei moduli installati con i 50 004
partner del popolatore.

# Come lavoriamo

- sei il Senior Staff Engineer, io l'Architect. Ti ho delegato l'autorità decisionale
  caso per caso: quando trovi una lacuna o una contraddizione nei documenti,
  analizzala, delibera e registrala in ai/00 con la sua argomentazione. Niente domande
  bloccanti; decidi e vai, tranne per le azioni distruttive.
- **spiegami le cose in un linguaggio poco tecnico, con esempi concreti, e quando citi
  una sigla o un punto della documentazione metti fra parentesi di cosa tratta.** Non
  «D2 lo impedisce» ma «D2 (la decisione che vieta di dare risposte sbagliate con
  l'aria di essere giuste) lo impedisce». Vale per le spiegazioni in chat, non per il
  codice e i documenti del progetto.
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

   **Da decidere per primo, perché tocca ogni stringa che scriveremo dopo.** Le parole
   di `nli_web` passano da `_()` chiamata in due posti dove Odoo 18 non riesce a
   dedurre la lingua: le lambda a livello di modulo di `nli_interpretation.py` (21
   delle 33 righe con `_()` del file) e la funzione annidata `rendered` di
   `nli_perimeter.py` §99. `_()` deduce la lingua ispezionando lo stack: dentro una
   richiesta HTTP trova `request.env.lang` e funziona, ma **il turno si interpreta sul
   cron** (parte 6), e lì non c'è richiesta — restano `cr` e `uid` letti dal frame
   chiamante, che in una lambda di modulo non ci sono. Esito: la stringa esce **non
   tradotta**, in silenzio, con uno stack trace di avviso nei log. Oggi non fa danno
   perché `in_words` non ha ancora chiamanti fuori dai test; lo farà appena il canale
   di chat la collega. Le opzioni sono `self.env._()` (esplicita, ma va portato `self`
   dentro le lambda), `LazyGettext` (`odoo.tools.translate._lt`, risolta al momento
   dell'uso) o un dizionario di forme costruito nel metodo. La scelta va deliberata e
   registrata in `ai/00`: è la forma dello strato delle parole, non un ritocco.
3. **`filter` al 73,6%.** Diagnosticato su 80 aperture: dodici fallimenti su ventuno
   erano un frammento senza condizione nominata mappato su una condizione nominata.
   D105 li rende visibili, non li corregge. I nove restanti sono di altre famiglie —
   condizione dimenticata, predicato possibile e sbagliato, valore preso male.
4. **D27**: eseguire il banco di prova sui worker prefork (`./manage.sh loadtest <db>`,
   **non su `nli_test`**) e riportare i numeri per quello che sono.
5. Il confronto con `granite4.1:8b`, se serve rispondere a *«il 73,6% è del compito o
   del modello?»*. Riga di comando identica, cambia solo `--profilo`.

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
