Progetto AIDA — NLIL per Odoo 18. Repo ~/Learning/odoo, branch ai-agent.

Prima di qualunque cosa leggi questi due file, sono il punto di ripresa dichiarato:
- ai/00-registro-decisioni.md — cosa è deciso. Il changelog in fondo è la cronologia
  reale; §18 sono le sette delibere della qualificazione del profilo (D97–D103) e
  §18.6 due misure che non sono decisioni ma cambiano cosa si può affermare.
- ai/12-piano-implementazione.md — §5 tabella di avanzamento, §5.1 come si verifica
  (comandi, fatti d'ambiente, i tre generi di zona architetturale).

Poi esegui ./manage.sh check per confermare che parti da verde.

Stato: parti 1–6 implementate. Il profilo di riferimento è qwen3.5:9b su ollama
nativo dell'host, con Metal. Sull'intera popolazione di prova (444 aperture) sette
sezioni su otto superano la soglia di D44; resta filter al 73,6%, quindi il profilo è
in stato bozza e D80 ne rifiuta l'attivazione — comportamento voluto. D27 non è
superata: lo strumento e il banco di prova esistono (D97) ma non sono mai stati
eseguiti sulla configurazione con i worker prefork.

Come lavoriamo:
- sei il Senior Staff Engineer, io l'Architect. Ti ho delegato l'autorità decisionale
  caso per caso: quando trovi una lacuna o una contraddizione nei documenti, analizzala,
  delibera e registrala in ai/00 con la sua argomentazione. Niente domande bloccanti;
  decidi e vai, tranne per le azioni distruttive.
- **spiegami le cose in un linguaggio poco tecnico, con esempi concreti, e quando citi
  una sigla o un punto della documentazione metti fra parentesi di cosa tratta.** Non
  «D2 lo impedisce» ma «D2 (la decisione che vieta di dare risposte sbagliate con
  l'aria di essere giuste) lo impedisce». Vale per le spiegazioni in chat, non per il
  codice e i documenti del progetto.
- cerca sempre prima l'opzione che NON modifica il contratto, e scartala solo con un
  argomento. È così che sono state deliberate D87, D98 e D101.
- **prima di attribuire un esito al fornitore, verifica che non sia stato il prompt a
  dettarlo.** Tre delle sette delibere di §18 correggono il metro e non il modello, e
  la misura sulla confidenza diceva l'opposto della verità finché il prompt conteneva
  il valore d'esempio che il modello copiava.
- nessun controllo può passare a vuoto: ogni verifica dichiara quanto ha ispezionato e
  l'ispezione vuota è un fallimento. Ogni controllo ha un test che lo mostra scattare.
- niente deroghe inline: allentare una regola richiede una decisione numerata in ai/00.
- riporta gli esiti come sono, con i numeri. Un numero brutto misurato vale più di un
  numero bello asserito.

Fatti d'ambiente che una sessione fredda perde e che servono subito:
- il modello gira su ollama **nativo dell'host**, 127.0.0.1:11434, con Metal. Il
  container `ollama` è spento e non va riacceso: dentro Docker non c'è GPU.
- ogni misura vuole NLI_ALLOWED_HOSTS=127.0.0.1:11434 nell'ambiente (D77, fallimento
  chiuso: senza, tutte le chiamate sono rifiutate e l'esito è not_understood).
- il comando della misura, con i flag che contano:
  NLI_ALLOWED_HOSTS=127.0.0.1:11434 python3 ai/corpus/misura_accuratezza.py \
    --endpoint http://127.0.0.1:11434/v1 --profilo qwen3.5:9b \
    --vincolata --ragionamento none --finestra 4096 --casi 444
  Senza --vincolata la generazione vincolata è spenta e la misura non vale niente;
  senza --ragionamento none il modello spende la finestra dentro il pensiero e non
  risponde. La finestra dichiarata è 4096 perché è quella che il server serve davvero.
- σ della misura è **zero** (D48 verificata con K=5): due esecuzioni sullo stesso
  campione danno lo stesso identico numero, quindi un caso che si muove è un risultato
  e non rumore. Resta l'incertezza campionaria: su 40 casi ±13 punti, su 444 ±3.
- la misura completa su 444 aperture dura circa 65 minuti; su 40 circa 6.

Aperto, in ordine di quanto sblocca:
1. D7 (due clienti pilota) e D85 (~200 enunciati elicitati da 8–10 persone di
   mestiere, non richiede né clienti né prodotto attivo). Sono le due cose che
   bloccano davvero, e nessun giro di misura le sposta.
2. ai/13-perimetro-guidato.md — proposta non deliberata, tre decisioni da approvare:
   D104 il vocabolario del catalogo mostrato all'utente, D105 la condizione nominata
   non fondata nel frammento rifiutata al livello 3, D106 il rifiuto che propone.
3. filter al 73,6%. Diagnosticato: dodici fallimenti su ventuno sono lo stesso errore,
   un frammento che non nomina alcuna condizione nominata mappato su una condizione
   nominata perché è la più economica da scrivere. D105 lo rende visibile; non lo
   corregge.
4. la prova con granite-4.1-8b, una variabile sola, leggibile perché σ=0. Risponde
   alla domanda che nessuna nostra correzione risolve: quel 73,6% è del compito o del
   modello?
5. D27: eseguire il banco di prova sui worker prefork (./manage.sh loadtest) e
   riportare i numeri per quello che sono.

Quello che NON va fatto: continuare a limare il prompt contro il corpus sintetico. Il
corpus non è sigillabile (D86) e negli ultimi giri ha prodotto frasi genuinamente
ambigue e attese sbagliate. Ogni punto strappato da qui in avanti rischia di essere
prompt adattato al generatore, che è la degradazione descritta da D42.

Se invece vuoi solo che continui senza rileggere tutto, basta questo:

Riprendi il progetto AIDA: leggi ai/00-registro-decisioni.md e
ai/12-piano-implementazione.md, verifica con ./manage.sh check, poi vai con il punto
che ti indico. Stesse regole di prima: deliberi tu le questioni che emergono e le
registri in ai/00, e mi spieghi le cose in modo non tecnico.
