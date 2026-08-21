Progetto AIDA — NLIL per Odoo 18. Repo ~/Learning/odoo-docker-env, branch **new-ai-agent**.

Il branch `ai-agent` è il ramo storico e si ferma al 29 luglio: `new-ai-agent` lo
riprende sopra la base UI corrente (`master`). Il lavoro continua qui.

# I prossimi passi

*(riscritto la sera del 5 agosto 2026, dopo la sessione della misura. La versione
precedente ordinava i lavori attorno a una batteria rotta e a un modello che si
credeva incapace: tutti e due riparati, vedi «Stato al 5 agosto 2026 (sera)» — e in
fondo a quello stato c'e' «Da dove si riprende», che e' la versione lunga di questa
tabella.)*

Sta qui in cima e non a meta' file perche' e' la domanda che si fa per prima. La
lista lunga, con i motivi, resta sotto in «Aperto, in ordine di quanto sblocca»: qui
c'e' solo **l'ordine**, e perche' e' quello.

## Il fatto che decide l'ordine

**La linea di partenza esiste, ed e' gia' stata mossa una volta: da 25 frasi su 54 (46%)
a 39 su 54 (72%)**, riparando l'ancora del tempo. Misure pulite tutte e due — 54 su 54
eseguite, zero saltate, i due context allineati.

Il che sposta la domanda da *«come misuriamo?»* a *«quale difetto costa di piu'?»*. Ora
la risposta non e' piu' un conteggio, e' una **gravita'**: il prodotto rispondeva *«i
lead creati nel primo trimestre»* con i dati del **terzo** trimestre, 26 record, senza
dire niente. Una risposta sbagliata con l'aria di essere giusta vale piu' di dieci
rifiuti, ed e' cio' che **D2** esiste per tenere fuori.

**Fatto il 6 agosto 2026 — vedi `00` §46 (D141).** I periodi che una frase *nomina*
— *«il primo trimestre»*, *«a gennaio»*, *«nel 2025»*, *«a marzo 2026»* — non
esistevano nel vocabolario, e il modello ripiegava sul periodo **corrente**. Ora
esistono (`month_of_year`, `quarter_of_year`, `half_of_year`, `year_of`), seguono
l'anno fiscale come `current_year`, e le quattro frasi rispondono giusto 3 giri su 3.
Quelle che gia' funzionavano non si sono mosse.

**E il rischio che D141 portava con se' e' stato chiuso lo stesso giorno — `00` §48
(D144).** Un mattone nuovo si usa anche dove non va: appena il modello ha avuto
`quarter_of_year`, ha risposto *«nel secondo semestre»* con il **secondo trimestre**,
3 giri su 3, contro una riga di prompt che lo vietava per nome. La classe di guasto non
e' il simbolo che manca — e' che **quando la parola manca il modello ripiega su quella
vicina invece di rifiutare, e non lo dice**. Ora un'espressione temporale e' rifiutata
quando il frammento che la cita nomina un periodo che quell'espressione non e': **D105
applicato al valore**, con il lessico dei periodi accanto a quello di D119.

## L'ordine

| | Cosa | Costo | Sblocca |
|---|---|---|---|
| ~~**P0**~~ | ~~La data senza anno: «primo trimestre» risposto col terzo~~ | **fatto** (D141, `00` §46) | quattro risposte sbagliate su sei diventate giuste |
| ~~**P0b**~~ | ~~La rete contro il ripiego silenzioso~~ | **fatto** (D144, `00` §48) | la **classe** e' chiusa: «bimestre» e «quadrimestre» non sono piu' ripieghi possibili, e nessun periodo nominato passa se il frammento non lo dice |
| **P1** | Finire i **pacchetti lingua**: 40 stringhe del pannello in inglese, `it.po` per cinque moduli | meccanico, mezza giornata | oggi un utente inglese vede italiano e nessun pacchetto lo corregge (§12.3) |
| **P1b** | Guardare **con gli occhi** la conversazione 207 nel pannello | ~30 min umani | chiude il punto 5 dell'interfaccia, decide il punto 6 (paginazione) |
| **P2** | `out_of_scope` su frasi legittime («il ricavo atteso piu' alto») | da capire prima di stimare | 4–5 frasi, ed e' un rifiuto **sbagliato**: il caso peggiore per la fiducia |
| **P3** | I pezzi di frase lasciati cadere («i secondi 20 lead», «non sono di milano») | da capire | una garanzia dichiarata che non e' mai esistita |
| **P3b** | Una prova nella suite di `nli_dispatch` sul cablaggio della frase | poco | il difetto di §9 e' passato proprio di li' |
| **P3c** | Una famiglia di **conversazioni** nella batteria, non solo prime domande | mezza giornata | §11: un difetto che uccideva ogni secondo turno non l'ha visto nessuna misura |
| **P4** | **D85** — avviare l'elicitazione degli enunciati | settimane, non nostre | il dataset del fine tuning |
| **P4b** | **D108** — trenta o quaranta **sinonimi scritti a mano** (`commerciale`→`Addetto vendite`, `posta`→`E-mail`, `creati`→`Data creazione`) | **mezza giornata** | l'unica cosa rimasta che sposta il risultato sulle **domande vere**, e costa meno di una corsa sbagliata. Le varianti meccaniche sono fatte (§2 dell'8 agosto); i sinonimi veri no, e nessuna regola ci arriva |
| ~~**P5**~~ | ~~Fine tuning: costruire il dataset~~ | **fatto** il 7 agosto (D142/D143 eseguite) | 10 000 esempi, ogni simbolo pieno, tre ricette e `corri.sh`: **tutto cio' che sta prima della GPU** |
| ~~**P5a**~~ | ~~Il dataset parlava una lingua sola, e citava frasi che non c'erano~~ | **fatto** l'8 agosto | provenienze scollegate **dal 13,6% a 0**, cornici da 1 a 5 per operazione, sinonimi meccanici, cataloghi meno piccoli. Vedi «Stato all'8 agosto 2026» |
| **P5b** | La **corsa**: `corri.sh fumo` (~$2), poi 4B e 2B | i tre cancelli di `ai/21` §1, poi macchina | e' l'unico passo rimasto fra il dataset e un modello addestrato — ma la **linea di partenza va rifatta prima**, quella che c'e' precede D144 |
| **P5c** | Misurare l'addestrato **due volte**: batteria sul campo **e** corpus | il corpus e' gia' scritto, e' una rimisura | se la batteria sale e il corpus no, abbiamo insegnato al modello **il nostro accento**, non la lingua. E' il risultato peggiore possibile perche' sembra un successo |
| **P6** | **1a** — copertura con i residui nascosti | macchina | **cancello D34**: sotto il 99% la regola non e' adottabile |
| **P7** | **1d** — selezione degli attributi | — | **premessa da rimisurare**: nasceva da «troppi attributi confondono il modello», che era il prompt tagliato |

**P0 prima di tutto** perche' non si misura in frasi, si misura in fiducia: finche' il
prodotto risponde col terzo trimestre a chi chiede il primo, ogni altro numero che
alziamo lo alziamo sopra una cosa che non regge.

**P4 e P5 partono in parallelo a tutto**, perche' sono lavoro sui dati e su persone,
non sulle misure, e non aspettano niente. **P5 e' chiuso il 7 agosto**: il `dataset`
esiste ed e' commesso. Quello che resta e' **P5b**, la corsa, e la sua unica dipendenza
vera non e' tecnica — e' che la linea di partenza contro cui si misurera' il modello
addestrato sia **piu' recente dell'ultima delibera che cambia le risposte**.

**Quella dipendenza e' soddisfatta dal 21 agosto**: la linea di partenza e' **47 su 59
(79,7%)**, posteriore a D144 e rifatta due volte con lo stesso risultato, su un ambiente
per la prima volta verificato a 8192 serviti. Vedi «Stato al 21 agosto 2026». E la stessa
sessione ha riordinato la lista: **P4b non e' piu' la leva piu' corta** — su 45 frasi vere
non resta un solo fallimento lessicale, mentre **8 fallimenti su 12 sono aggregazioni**.

**L'8 agosto e' entrato in mezzo un lavoro che non era in lista** (P5a), e non era una
rifinitura: il dataset insegnava a **citare frammenti che nella frase non c'erano**, nel
13,6% dei casi. Il modello avrebbe imparato a produrre esattamente cio' che D105, D119 e
D144 rifiutano — si sarebbe bocciato da solo. Riparato, con la rete che lo tiene chiuso.
Vedi «Stato all'8 agosto 2026».

**E una cosa che credevamo mancasse c'e' gia'.** L'esame indipendente — domande scritte
da qualcuno che non ha visto il generatore del dataset — non va costruito: e' il
**corpus fondativo**, 1 200 casi in `ai/corpus/`, scritti da un altro generatore con un
lessico compilato a mano. Dice *«estrai anagrafiche clienti operativi raggruppati per
comune»* dove il dataset dice *«fammi vedere contatti con Citta' uguale a Roma»*: parole
d'ufficio contro etichette Odoo. Il modello base ci fa **75,8%**, ed e' il confronto che
rende leggibile il numero dell'addestrato (P5c).

**Due voci sono uscite dalla lista.** Il corpus a `--finestra 4096` doveva separare
D113–D120 da D133: la risposta e' arrivata senza il corpus, era D133. E `1b`
(`QueueRefusal` nella batteria) e' riparato.

## P1 nel dettaglio, perche' e' il piu' corto e non e' scritto altrove

Il **contenitore** del pannello e' stato guardato nei tre temi. Il **contenuto di una
risposta** no: i turni di `nli_test` erano tutti fermi in `pending` — ora si sa perche',
quella banca dati non aveva nessun profilo attivo — quindi la vista lista incorporata,
la riga del conteggio, «Come ho letto la domanda», le opzioni di chiarimento di D121 e
la riga dei comandi **non li ha visti disegnare nessuno**.

**Il materiale ora c'e'**: su `db`, conversazione **207**, sei turni veri con due
tabelle nello stesso filo, un conteggio, due chiarimenti e un rifiuto, tutti con la
traccia diagnostica di D123. Resta solo da aprirla e guardarla.

Da guardare, in quest'ordine:

1. una risposta con tabella — l'altezza del riquadro, lo scorrimento orizzontale, e se
   440 px bastano o se il punto 6 (paginazione) diventa urgente;
2. **due tabelle nella stessa conversazione** — e' il caso in cui l'altezza sbaglia;
3. un chiarimento di D121 — le opzioni sono cliccabili solo sull'ultimo turno;
4. «Come ho letto la domanda» aperto, con una condizione dedotta (bordo tratteggiato);
5. il blocco diagnostico di D123, che e' il piu' largo di tutti dentro una colonna
   stretta.

E i passi che arrivano davvero: e' la prima volta che `nli.turn.progress` viaggia
contro un turno vero invece che contro un reporter finto.

## Cosa **non** e' il prossimo passo

Il pannello e' consegnato ma **non e' finito**: mancano il punto 5 (sopra) e il punto
6 (paginazione). Non aggiungere altra interfaccia prima di aver guardato quella che
c'e' — e' esattamente il modo in cui si sono accumulati i dieci difetti di
`ai/20-ux-pannello-aida.md` §7.

---

# Da leggere per primo

> **Prima di ogni altra cosa in questo file: la sezione «Stato al 4 agosto 2026 — la
> sessione del catalogo».** Contiene la scoperta che vale più di tutte le altre in
> lista, e in alcuni punti **contraddice** quanto scritto sotto «Stato al 29 luglio
> 2026». In una riga: il problema non è quanto è grande il `context`, è **cosa ci
> mettiamo dentro**.
>
> Poi «**Stato al 5 agosto 2026 — AIDA diventa un pannello**», che è la più recente ma
> parla d'altro: è tutta interfaccia e non tocca il motore. Leggila se lavori sul lato
> client, saltala se lavori sul catalogo. Le due cose non si contraddicono.

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
- ai/18-fine-tuning.md — l'analisi e la scelta della modalita' di addestramento
  (LoRA a 16 bit, non QLoRA), l'architettura dell'operazione, il servizio (RunPod) e i
  costi (~$40 in tutto). §1 traduce *«risponde esattamente»* in soglie misurabili,
  **§5bis** e' la sezione che risponde a *«funziona su entita' installate dopo?»* — si',
  se il catalogo varia in addestramento, e si **misura** su applicazioni intere mai
  viste. §9 e' il cancello di D80 prima del servizio, §12 l'ordine di lavoro.
- ai/19-scelta-del-modello.md — quale modello affinare e su che hardware, **misurato
  sul portatile col prompt vero**: il 9b legge il prompt in 17 s e risponde in 57, il 4b
  in meta' tempo, il 2b in un quarto. Il consiglio e' affinare **Qwen3.5-4B** con il
  **2B** in parallelo, e comprare una **RTX 3060 usata (~220 €)** per l'inferenza.
- ai/21-ricetta-lora.md — **la ricetta eseguibile** del fine tuning, scritta il 6 agosto:
  `18` decide e `19` sceglie il modello, `21` dice come si preme il pulsante. §2 e' la
  decisione che vale piu' di tutte (**D142**: il messaggio di sistema si sposta nei pesi,
  −58% sul `prompt`), §4 e' la strategia di selezione del dataset (**D143**: si
  sovra-genera 4:1 e si sceglie per copertura, non per quota), §6 il file di
  configurazione vero, §10 l'ordine di lavoro. Il costo non sono i $40: e' `genera_dataset.py`,
  2-3 giorni, ed e' li' che si decide se il modello diventa performante o solo addestrato.
  **Il 7 agosto quel costo e' stato pagato**: il generatore, le tre ricette e `corri.sh`
  sono in `tools/finetuning/`, e `data/copertura.txt` e' il rapporto che si legge **prima**
  di affittare la macchina. Vedi «Stato al 7 agosto 2026».
  **L'8 agosto il generatore e' stato riscritto dove parlava una lingua sola**, e ha
  ricevuto le sue prime prove: `tools/finetuning/tests/test_generatore.py`, 17, dentro
  `./manage.sh check`. Vedi «Stato all'8 agosto 2026».
- ai/16-controllo-architettura.md — il mandato del controllo di architettura del
  3 agosto, e ai/17-esito-controllo-architettura.md la risposta: sei reperti gravi,
  undici minori, e la raccomandazione principale, che non e' una correzione ma una
  prova. §6 e' l'ordine di lavoro; D129–D134 ne hanno chiuso la prima meta'.
- ai/15-implementazione-ui.md — la specifica dell'interfaccia. **Tre punti confliggono
  con l'architettura e sono risolti in `00` §23**: lo streaming dei gettoni non e'
  realizzabile (il modello produce una busta sola, e il turno si interpreta sul cron),
  le risposte non sono prosa ma l'interpretazione in parti, e la cronologia ha richiesto
  D115.

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

**Il 2 agosto, in una sessione sola.** Diciassette decisioni deliberate, **D109–D125**, e
il prodotto usato per la prima volta da un'interfaccia.

*L'ancoraggio del tempo* (D110–D112, proposta `14`): il catalogo dichiara dove si
attacca un periodo, un periodo non si lascia cadere, e una categoria che la frase non
nomina non e' piu' scrivibile. Rimisurato: **il movimento vero e' stato mezzo punto su
`filter`**, non i sei apparenti — il resto era cambio di popolazione, e la stima fatta
prima di misurare era bassa. Registrato in §21.7 con l'aritmetica.

*Cio' che la rimisura ha scoperto* (D113–D114, D117–D119): il predicato sinonimo che si
mangiava 2,7 punti, la via d'uscita `out_of_scope` che si apriva da sola, `create_date`
escluso dal catalogo come se fosse tecnico. Tutte cose che **non erano difetti del
modello** e che nessuno vedeva perche' erano misurate dietro un difetto piu' grande.

*L'interfaccia* (D115, D116, D120): la chat dentro Odoo con la barra di navigazione, in
chiaro e in scuro, il modello configurabile dalle impostazioni generali, la cronologia
che conserva le parole dell'utente — con il prezzo di D115 scritto per esteso.

*Una strada sola per il clic e per lo scritto* (**D121**, §30): rispondere a un
chiarimento con l'etichetta di un'opzione **esegue senza chiamare il modello** — da un
minuto d'attesa a niente — e cliccare un'opzione scrive quell'etichetta nella casella e
la invia, cosi' clic e scritto non possono divergere per costruzione. La coda di
`pipeline.run` (applicatore, livelli 3-5, risolutore, esecutore, presentatore) e' ora la
funzione `_apply_and_present`, unica per tutti e due i modi di produrre operazioni. Un
pezzo non previsto: una lettura proposta **non era applicabile com'era**, perche' si
portava dietro il frammento di prima; adesso la provenienza della condizione scelta e'
l'etichetta, che e' vera — sono le parole che l'utente ha appena detto — e il livello 3
gira e passa invece di essere aggirato.

Messo in servizio non funzionava, e non per colpa sua: `00` §30.1 elenca i **quattro
difetti gia' presenti** che ha fatto emergere, tutti della stessa forma — un fallimento
che non si dichiara. Una riga di coda che finiva senza esecuzione non chiudeva il turno;
un turno scartato copriva la domanda in sospeso; l'interfaccia diceva «non ho capito» a
un turno che nessuno aveva letto; e **il primo turno che riusciva** di ogni
conversazione moriva scrivendo lo stato, perche' `dsl_version` non c'era e nessuna prova
persisteva uno stato eseguito. Corretti tutti e quattro.

**Misurato sul database vero, con il modello vero:** *«mostrami i lead di quest'anno»*
→ chiarimento in **96,0 s**; risposta con l'etichetta → **operations in 0,08 s, zero
richieste al modello, 39 record**.

*Il tempo concesso al modello* (**D122**, §31): l'interfaccia rispondeva *«non ho capito
la domanda»* a **ogni** domanda. Il modello in servizio impiegava **60,1 s** per
chiamata e l'adattatore ne concedeva **60, in una costante**: nessuna domanda poteva
riuscire. Ora e' un campo del profilo, come la finestra di D78, con predefinito 180 s.
E §31.1: il guasto arrivava all'utente come «non ho capito» invece che come «il modello
non ha risposto» — `worker.execute` lo diceva giusto per il profilo mancante, il
pipeline lo diceva sbagliato per la risposta mancante, che e' il percorso che si
percorre sempre. Stessa forma di divergenza che D121 ha chiuso, stessa correzione: un
punto solo. Dopo: *«mostrami i lead creati quest'anno»* → **operations in 103,1 s, 39
record**.

**Da guardare, non e' una decisione.** Il profilo in servizio dichiara una finestra di
**4096 gettoni** e D79 ne ricava il budget del catalogo: il modello vede un catalogo
tagliato. `qwen3.5:9b` regge molto di piu'. Va sistemato **prima** della prossima misura
di accuratezza, altrimenti quella misura misura il taglio.

*La modalita' diagnostica* (**D123**, §32): accesa, ogni turno mostra sotto la
risposta **come e' stato costruito** — la busta DSL uscita dal modello, lo stato, **la
query** con cui Odoo e' stato interrogato, e il tempo di ogni fase. Sta sul turno e non
nei log, perche' D60 vieta frasi e cataloghi li' dentro; la vede solo un amministratore.
Spenta di default e da spenta non costa e non conserva niente.

**§32.1 — cosa ha detto al primo giro.** *«mostrami i lead creati quest'anno»*, 147,6 s:
fase A 0,054 s, **fase B 113,4 s**, fase C 0,249 s, interpretazione 33,6 s, esecuzione su
Odoo **0,031 s**. La fase B costa **piu' del triplo** dell'interpretazione vera e chiede
la cosa piu' facile — di quale entita' si parla. L'aperto sulla latenza non e' piu' «il
modello e' lento»: e' «la fase B e' la parte cara».

*Le viste di risposta, e tre regole che non erano collegate* (**D124**, §33): il
Presentatore produceva una struttura, `in_words` la faceva parole, e **non lo chiamava
nessuno** — nessuna risposta riuscita e' mai stata disegnata, da sempre. Ora l'avviso sul
bus dice solo *che* il turno e' finito e cio' che si disegna lo costruisce
`_aida_payload`, una volta sola (§33.1). §33.2: due periodi sullo stesso attributo si
intersecano invece di raffinare — regola nuova di livello 4, perche' il conteggio non
cambia (39 e 39) e quindi non si vede. §33.3: **il livello 4 girava a meta'**,
`coherence.validate_coherence` non era sul percorso del pipeline; profondita' del filtro,
raggruppamenti e misure-contro-vista erano regole provate e mai eseguite. §33.4: le
tabelle di `15` sono la **vista lista di Odoo incorporata** — ricerca, ordinamento,
filtri, colonne e paginazione arrivano da li'.

**Tre difetti in due giorni della stessa forma**: `_finish` che non chiudeva il turno,
`in_words` che nessuno chiamava, `coherence` che non era sul percorso. Codice corretto,
provato, e **non collegato** — con la prova verde sempre un passo prima del punto in cui
serviva.

*Un periodo nuovo prende il posto del precedente* (**D125**, §34): la regola di §33.2
rifiutava invece di riparare, e al terzo turno sulla stessa data la conversazione era
**bloccata senza via d'uscita** — ogni tentativo di rimediare aggiungeva un periodo e
falliva uguale. Ora l'Applicatore sostituisce, e uno stato gia' rovinato guarisce al
primo turno che nomina di nuovo quell'asse. La regola di livello 4 resta come rete di
sicurezza. **Lezione, oltre al caso:** un rifiuto e' giusto solo se chi lo riceve ha una
mossa.

**Il 3 agosto: tre decisioni, e un difetto che si ripete.** **D109–D128**.

*I nomi delle entita'* (**D126**, §35): ogni entita' aveva **un termine solo**,
l'etichetta Odoo grezza — `Lead/Opportunità`, che nessuna frase italiana contiene. La
fase A sul database vero risolveva **0 su 8**; adesso 6 su 8. Le parole si **raccolgono**
dall'installazione (etichetta, i suoi pezzi, azioni e voci di menu) invece di generarle:
il plurale che l'utente dice e' gia' scritto nel menu che preme. §35.1: il guardiano di
V-D93-1 buttava via anche le prove **esatte**, e ora vale solo contro quelle
morfologiche. §35.2: il registro delle voci approvate dichiarava T1 e ne rifiutava
ognuno.

*Domanda nuova o raffinamento* (**D127**, §36): chi nomina la propria entita' ricomincia,
chi non la nomina continua. La fase A gira **sempre**, anche con un bersaglio nello
stato — prima si fermava li', e con lei spariva il solo segnale che distingue i due casi.
Chiude anche il cambio di entita', che era **impossibile**.

*Le opzioni di una domanda* (**D128**, §37): il modello offriva quattro letture con un
`within` senza periodo, e il clic applicava fedelmente qualcosa di inapplicabile. Ora si
validano quando la domanda si **memorizza**. E ancora due strade — fase B e fase C
impacchettavano l'esito terminale ognuna per conto suo.

**§38 — il difetto che si ripete.** Sette volte in tre giorni la stessa forma: codice
**dichiarato, provato e non collegato**, con la prova verde sempre un passo prima del
punto che serviva. `_finish`, `in_words`, `coherence`, T1 nel registro, il fallimento del
fornitore, i due rami terminali, la fase A. Da adesso: una funzione e' finita quando
esiste una prova che **fallisce se qualcuno la scollega**.

**Batteria sul campo, 3 agosto, modello vero e database vero.**

*Fase A, 36 frasi sulle 8 entita' installate:* **32 giuste, 4 mancate, zero falsi
positivi.** Tutti e sette i raffinamenti non risolvono, come devono — e' il segnale di
D127 che regge. Le 4 mancate: `registrazioni contabili`, `movimenti contabili`, `righe
ordine di vendita` (quest'ultima finita su `sale_order` invece che su `sale_order_line`)
e il refuso `leed`. Le prime tre hanno **la stessa causa**: etichetta di due parole al
singolare contro frase al plurale, match al livello morfologico (0,90), e li' il
guardiano di V-D93-1 la scarta perche' un **campo che punta a quella stessa entita'** si
chiama uguale. La stretta di §35.1 era giusta e non basta.

*Giro completo, 13 turni:* **6 hanno prodotto una risposta**, con i domini corretti e i
periodi risolti bene.

    mostrami i prodotti                          operations  36 rec   15s
    i primi 5 ordini di vendita                  operations  20 rec   15s
    mostrami i contatti di Roma                  operations   0 rec   32s
    mostrami i lead creati questo mese           operations   0 rec   31s
    mostrami i lead creati negli ultimi 3 mesi   operations  39 rec   84s
    mostrami i lead creati quest'anno            not_understood      145s
    mostrami gli ordini di vendita di questo mese not_understood     119s

**Il fallimento dominante e' uno solo: l'ancora del tempo.** Colpisce `crm_lead` **e**
`sale_order`, cioe' le due entita' della prima domanda che chiunque farebbe. E
*«creati quest'anno»* ha fallito tre volte su tre la sera dopo aver dato 39 record la
mattina: **il modello non e' deterministico su questo**, quindi non e' una frase da
sistemare, e' una strada da togliergli.

**La latenza e' tutta li'.** Senza espressione temporale: **15-40 s**. Con: **84-145 s**.
Sono lo stesso pezzo, non due problemi.

**Due cose minori trovate dalla batteria.** *«quanti lead avremo il mese prossimo»* ha
risposto `not_understood` invece di `out_of_scope`: e' una previsione, e D118 chiede che
il rifiuto citi il frammento — primo caso di misura sul campo per D114/D118. E un turno
fallito ne fa fallire due: il raffinamento dopo non ha niente su cui appoggiarsi.

**Il controllo di architettura, e le sei correzioni che ne sono nate.** `ai/16` e' il
mandato, `ai/17` l'esito: gli scollegamenti di §38 non erano sette, ce n'erano **altri
undici**, e sette erano lo stesso tratto di catena — fra il piano risolto e lo schermo.
**D129–D134** (`00` §39) li rimettono in servizio: il tetto ai record di **D13**, che non
era chiamato da nessuno e lasciava passare *«i primi 200000 lead»*; le **aggregazioni**,
che nessuno calcolava (`avg` mostrava l'elenco sotto la scritta «media»); il **fuso
orario**, che spostava di due ore ogni condizione su un `datetime`; l'**ordinamento e le
colonne**, che non arrivavano alla tabella; la **finestra del profilo**, che dichiara 4096
mentre il modello ne regge 262 144, e con essa il catalogo tagliato al 26%; e il **banco
delle risposte** (`nli_core/tests/test_answers.py`), che parte da uno stato e arriva a un
numero — la prova che mancava, ed e' la raccomandazione principale dell'audit.

**Il chiarimento temporale, 3 agosto** (**D135**, `00` §40): la domanda su *quale data*
la costruiamo noi dall'ancora di D110 invece di chiederla al modello. E' D105 con una
data al posto di una categoria — se l'entita' espone due date e il frammento non ne
nomina nessuna, la data l'ha scelta il modello — e ogni opzione tiene il periodo, perche'
D111 vieta di lasciarlo cadere. Sceglierne una esegue in un decimo di secondo (D121).
**Non e' ancora misurata sul campo**: l'attesa scritta prima di misurare e' in `00` §40.8.

**Il primo turno vero di D135, e i tre difetti che ha scoperto** (**D136–D138**, `00`
§41). La domanda e' arrivata — quattro date, costruite dall'ancora — e il clic ha
eseguito senza chiamare il modello. La risposta pero' e' stata *«nessun record trovato»*,
e il turno letto per intero dice perche': il modello aveva tradotto *«di quest'anno»* con
**`after`** invece che `within`, cioe' *dopo la fine del 2026*. Sotto c'erano due difetti
nostri che nessuno poteva vedere finche' la domanda moriva in `not_understood`:
l'interpretazione mostrava **la finestra dell'espressione** (*«2026-01-01 - 2026-12-31»*)
invece dell'insieme davvero interrogato, quindi zero record era inspiegabile; e chi
sceglieva un'opzione ripartiva **dallo stato che la domanda aveva gia' buttato via**, che
qui e' costato un ordinamento di troppo e domani sarebbe una risposta ristretta a una
citta' che nessuno ha piu' nominato.

**Il banco delle capacita'** (`00` §42): `nli_core/tests/test_capabilities.py`, **60
prove** che eseguono ogni operazione di `ai/16` tranne i join — intenti, operatori, date
— piu' nove che **dichiarano i buchi** (HAVING, OFFSET, EXPORT, `!=`, ENDS WITH, la
negazione, i trimestri e i mesi nominati, le aggregazioni annidate). Ogni prova porta
nel nome la frase italiana che rappresenta. Ha anche scoperto che **`create_date` non e'
scrivibile in Odoo 18**, e che una riga della prova del fuso orario ci era appoggiata
sopra e passava a vuoto: corretta.

**La batteria sul campo** (`00` §43): `./manage.sh campo <db> [famiglia]` esegue **54
frasi italiane** — le stesse operazioni del banco, dette come le direbbe qualcuno in chat
— attraverso il prodotto vero. E' una **misura**, non una prova, ed e' fuori da `check` e
da `test` di proposito: il modello non e' deterministico. Al primo giro ha detto subito la
cosa che conta: con la finestra a 4096 il catalogo di `crm.lead` tiene 17 attributi e ne
rifiuta 49, e fra i mancanti ci sono **lo stato, il ricavo atteso, il commerciale, il
telefono**. Meta' delle domande che una persona farebbe per prime non e' sbagliata: e'
**non rispondibile**. La batteria intera va quindi eseguita **dopo** aver alzato la
finestra, non prima.

**Il limite non arrivava alla tabella** (**D139**, `00` §44): *«i primi 5 lead»* ne
mostrava trentanove. Il limite viaggiava come `list_view_limit` nel contesto della vista,
e **quella chiave non esiste in Odoo 18** — la vera e' la proprieta' `limit`. E' il
reperto R2 per la seconda volta nello stesso componente, per la stessa ragione: una
chiave passata a chi non la legge non fallisce. `check_owl.py` ha ora una regola che
confronta le chiavi di contesto col sorgente di Odoo, e al primo giro ne ha trovate altre
cinque morte (`create`, `edit`, `delete`, `duplicate`, `import_enabled`): erano li' per
D2 e **non garantivano niente**.

**E la frase di D68 non arrivava allo schermo** (**D140**, `00` §44.5): sopra una tabella
di cinque righe c'era scritto *«39 record trovati»*. Il totale e' giusto, ma e' meta'
della frase: `Result.describe()` produce *«i primi 5 di 39»* da sempre, il payload la
porta al client, e nessuno la disegnava — cioe' proprio il fraintendimento per cui D68
esiste. Terza volta in un turno solo, e sempre fra il piano e lo schermo.

**La finestra e' stata alzata, il 4 agosto 2026.** Le due meta' insieme, come **D133**
richiede: `OLLAMA_CONTEXT_LENGTH=8192` sul servizio `ollama` dell'host (con
`launchctl setenv` piu' riavvio dell'applicazione) e `context_window = 8192` sul profilo
in servizio. **Verificato su tutti e due i lati**: il server legge 4 061 gettoni di un
prompt da 4 077 invece di fermarsi a 2 050, e il catalogo di `crm.lead` tiene ora
**60 attributi su 66** invece di 17 — sei rifiutati per budget invece di quarantanove.

**Da qui in poi le misure valgono.** Tutto quello che e' stato misurato prima del
4 agosto — il 70,0% di accuratezza, le frasi saltate della batteria, i tre candidati di
`19` — e' stato misurato attraverso un catalogo tagliato a un quarto, e **va rifatto**.
E' il punto 1 degli aperti.

**Verifiche al 3 agosto:** 489 test in zona pura, 249 test Odoo, 51 test dei confini,
57 file in zone pure,
contratto e corpus 918/918 con copertura al 100%, **cinque** controlli dei confini puliti.

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
- **dal 4 agosto 2026, obbligo: spiegare come a un ragazzino sveglio ma inesperto.**
  Frasi corte. Un'analogia concreta quando il meccanismo non e' ovvio — il catalogo da
  60 attributi si spiega come un menu' da 60 piatti di cui 43 non sono piatti. Prima il
  «perche'», poi il dettaglio. Vale in chat **e nei documenti**, e vale anche quando
  l'argomento e' profondo: si allunga la spiegazione, non si alza il registro.
  **Le parole chiave tecniche restano in inglese e non si traducono**: `envelope` (non
  «busta»), `context` (non «finestra»), `token` (non «gettoni»). Il termine esatto e'
  un'ancora; tradurlo la toglie.
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

**Il context servito, che e' il primo da controllare.** `ollama` carica il modello con
il context che ha **lui**, non con quello che il profilo dichiara: il protocollo
compatibile OpenAI non ha un campo per dirlo (D133). Il 5 agosto 2026 serviva **4096**
mentre noi dichiaravamo 8192, il prompt arrivava tagliato dentro il catalogo e il
prodotto rispondeva `not_understood` a quasi tutto — deterministicamente, e senza che
niente lo segnalasse.

    curl -s http://127.0.0.1:11434/api/ps | grep context_length

`/api/ps` risponde vuoto se nessun modello e' caricato: basta una domanda qualunque per
caricarlo.

**Se dice 4096 — e il rimedio che era scritto qui non funziona.** Il 21 agosto 2026 la
riga precedente diceva di riavviare l'applicazione dopo un `launchctl setenv`. E'
sbagliata, ed e' costata una diagnosi: **Ollama.app avvia `ollama serve` con un ambiente
suo e non eredita `launchctl`**. Verificato leggendo l'ambiente del processo vero
(`ps eww`): dentro c'erano `OLLAMA_MODELS` e `OLLAMA_NO_CLOUD`, non
`OLLAMA_CONTEXT_LENGTH`. E l'impostazione `settings.context_length` nel database
dell'applicazione (`~/Library/Application Support/Ollama/db.sqlite`) **vale per la sua
chat, non per il server**: portata a 8192, `/api/ps` continuava a dire 4096.

L'unico modo verificato e' avviare il server a mano, con la variabile nel suo ambiente:

    osascript -e 'quit app "Ollama"'; pkill -f "ollama serve"
    OLLAMA_CONTEXT_LENGTH=8192 nohup /usr/local/bin/ollama serve > /tmp/ollama-serve.log 2>&1 &

Poi si **verifica**, non si presume: `/api/ps` deve dire `8192`. Cosi' gira oggi. Muore
al riavvio del Mac e l'applicazione puo' riprendersi la porta: il `LaunchAgent` resta
aperto, ed e' l'unica forma che chiude il buco.

**Perche' e' il primo controllo di ogni sessione.** Quando il servito e' 4096 il prodotto
non e' rotto in modo visibile: risponde `not_understood`, che assomiglia a un limite del
modello. Il 21 agosto una domanda e' stata diagnosticata come guasto di entita' mentre il
server serviva 4096 — la diagnosi reggeva lo stesso, ma la misura sotto era inutilizzabile
e nessuno se n'era accorto. **Il valore dichiarato dal profilo non e' una prova di niente:
la prova e' `/api/ps`.**

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
      --vincolata --ragionamento none --finestra 8192 --casi 444 --attesa 300

Senza `--vincolata` la generazione vincolata è spenta e si misura il vuoto; senza
`--ragionamento none` il modello spende la finestra dentro il pensiero e non risponde;
`NLI_ALLOWED_HOSTS` è obbligatoria (D77, fallimento chiuso: senza, ogni chiamata è
rifiutata e l'esito è `not_understood`). La finestra dichiarata è **8192** perché è
quella che il server serve davvero da D133 (la decisione che alza la finestra sulle due
metà insieme, server e profilo): scriverne 4096 rimette il catalogo tagliato dentro la
misura. `--attesa 300` sostituisce il default di 60 s, che è il valore d'esercizio di
D5 e non un limite della misura: con la finestra piena una chiamata può superarlo, e un
tempo scaduto contato come errore misura il portatile, non il modello.

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

# Stato al 4 agosto 2026 — la sessione del catalogo

Questa sezione e' la piu' recente e va letta **prima** di quelle datate 28-29 luglio,
che in alcuni punti contraddice. Quattro cose, in ordine di quanto contano.

## 1. Il prodotto era rotto per intero, e non lo sapeva nessuno

Il profilo in servizio portava `reasoning_effort = 'high'`, **scritto il 3 agosto alle
22:48**, cioe' dentro la stessa modifica che alzava il `context` per D133 (la decisione
che impone di alzare il `context` sulle due meta' insieme, server e profilo).

**D98** (la decisione per cui il profilo dichiara lo sforzo di ragionamento, e la chiave
viaggia solo se nominata) era stata adottata misurando esattamente il contrario: col
ragionamento acceso il modello spende il `context` dentro il pensiero e l'`envelope`
torna **vuoto** — 2 397 token e nessuna risposta; con `none`, 179 token e `envelope`
valido.

Misurato sul prodotto vero, non dedotto:

| frase | `high` | `none` |
|---|---|---|
| *«mostrami i lead»* | `not_understood`, **41,2 s** | **ok, 4,9 s** |

**Corretto**: `reasoning_effort` riportato a `none` sul profilo attivo del database `db`.

**La lezione, che vale piu' della correzione.** Il profilo e' **dato**, non codice:
nessun diff lo mostra, e il commit `80ec214` dice il vero e nasconde questo. D133 esiste
perche' il `context` ha due meta' che vanno mosse insieme; il guasto e' della stessa
famiglia, con una terza meta' che nessuno stava guardando. **Serve un controllo che
confronti il profilo in servizio con i valori qualificati**, invece di fidarsi.

## 2. La misura sul corpus, e perche' non dice quello che sembra

Fatta, 414 aperture, `context` 8192, generazione vincolata, ragionamento `none`:
complessiva **75,8%** (era 70,0%), `filter` **85,0%** (era 79,5%), le altre sette sezioni
fra 88,6% e 98,6%. **D44** (la soglia dell'85% richiesta su ciascuna sezione, non sulla
complessiva) e' superata su tutte e otto **per la prima volta**, e `filter` la tocca
esatta: nessun margine.

**Il numero non e' attribuibile.** La linea del 70,0% precede sia D113-D120 sia D133,
quindi due cause stanno dentro una misura sola, e la coincidenza con la previsione di
`00` §22.3 (~75,3% e ~84,8%, scritta per D113-D120 **a `context` invariato**) non la
conferma. Si separa rifacendo le stesse 414 con il codice di oggi e `--finestra 4096`.
**Non ancora fatto.**

**E soprattutto: il corpus non descrive il prodotto.** Il corpus misura il modello contro
un catalogo **sintetico**, scritto da noi, pulito. Il prodotto gli mostra il catalogo
**Odoo vero**. Lo scarto misurato il 4 agosto e' enorme: 75,8% in palestra, **2 casi su
49** sul campo. D86 (la decisione che dichiara il corpus sintetico e percio' non
sigillabile) lo diceva; adesso sappiamo di quanto.

## 3. Il catalogo intero affoga il modello — e il catalogo tagliato mentiva

Prima misura del prodotto vero, otto frasi, unica variabile la larghezza del catalogo:

| catalogo | attributi | prompt | `operations` | qualita' delle risposte |
|---|---|---|---|---|
| `context` 4096 | 17 | 2 940 token | 8/8 | **inventate** |
| `context` 8192 | 60 | 4 041 token | 2/8 | — |
| segnale forte | **27** | **3 156 token** | 6/8 | corrette |

Il caso che decide tutto:

    «i lead con ricavo atteso sopra 1000»
      con 17 attributi  ->  [["campaign_id", "!=", false]]      inventato
      con 27 attributi  ->  [["expected_revenue", ">", 1000]]   giusto

**Quindi D133 non ha peggiorato il prodotto: ha reso visibile un guasto che c'era gia'
ed era nascosto.** A 4096 il modello non capiva meglio, mentiva meglio — e' **D29** (una
delle sette decisioni portanti, che esiste per rendere impossibile «la modalita' di
guasto che non produce errori ma numeri diversi, tutti plausibili»).

**Perche' i 17 di 4096 erano quelli sbagliati.** Le prime 50 voci entrano tutte con la
stessa regola (`in_default_views`) e la stessa priorita'; a parita' di priorita' il
criterio di spareggio e' **il nome tecnico in ordine alfabetico**. I 17 sopravvissuti
erano i primi 17 dell'alfabeto, da `active` a `email_state`. Fuori restavano `name`,
`partner_id`, `user_id`, `stage_id`, `expected_revenue`: le cinque cose che uno chiede
per prime.

**Il segnale migliore, e generalizza.** Odoo non ha «le viste predefinite»: ne ha quattro
tipi e dicono cose diverse. La **vista di ricerca** e' «ecco cosa la gente cerca»; i
**filtri di raggruppamento** sono «ecco per cosa raggruppa»; la **vista elenco** sono le
colonne che si vedono ogni giorno; la **vista scheda** mostra tutto di un record, ed e'
da li' che entra il rumore (`probabilita' automatica`, `giorni per chiudere`, `e-mail in
cc`). Oggi la regola 8 le unisce tutte e quattro in un mucchio solo, e la regola 9
(`residual`, «tutto il resto — esposto con priorita' bassa») non e' una selezione: e' una
resa.

| entita' | esposti oggi | segnale forte |
|---|---|---|
| `res.partner` | 93 | 16 |
| `sale.order` | 52 | 17 |
| `sale.order.line` | 54 | 11 |
| `account.move` | 100 | 34 |
| `account.move.line` | 69 | 36 |
| `product.template` | 45 | 13 |
| `crm.lead` | 66 | 27 |
| `hr.employee` | 82 | 17 |

Da ~70 in media a ~21. `res.partner`, `account.move` e `hr.employee` sfondano gia' il
tetto di 60 di **D31** (il massimo di attributi per entita'), quindi li' il taglio
alfabetico sta gia' buttando via cose importanti a caso. Con `crm.lead` a 27 attributi:
**0 rifiutati per budget**.

**Regola proposta** — sostituire la regola 8 con tre regole graduate e capovolgere la 9:

| segnale | priorita' |
|---|---|
| vista di ricerca | 1 |
| filtri di raggruppamento | 1 |
| vista elenco | 2 |
| solo vista scheda | 3 |
| nessuna vista | **nascosto** |

**Verifica sulla batteria**, stessi primi 20 casi, stesso modello, cambia solo il
catalogo:

| catalogo | ok | diversi | saltati |
|---|---|---|---|
| 60 attributi | **2** | 14 | 4 |
| 27 attributi | **10** | 6 | 4 |

Otto frasi passate da sbagliate a giuste, **nessuna peggiorata**. Dal 12,5% al 62,5% sui
casi eseguiti, **senza toccare il modello e senza una riga di codice nuova**. I 27
termini di `crm.lead`: `addetto vendite, attivo, azienda, campagna, chiusura attesa,
citta', cliente, data chiusura, data creazione, e-mail, etichette, fase, mezzo, motivo
perdita, nazione, nome contatto, opportunita', origine, priorita', probabilita',
proprieta', ricavo atteso, segnalato da, stato, team di vendita, telefono,
telefono/cellulare`.

**Il rischio da misurare prima di adottare**: nascondere i residui puo' far scendere la
**copertura**, che oggi e' al 100% e che **D34** vuole almeno al 99%.

**I 6 casi ancora sbagliati non c'entrano con gli attributi**: sono le domande con una
**misura** (*«somma il ricavo atteso»*, *«qual e' il piu' alto»*, *«il ricavo medio per
stato»*). Il modello trova l'attributo giusto e poi non costruisce l'aggregazione. Fronte
diverso, adesso isolato invece che sepolto sotto il rumore.

## 4. Lo strumento di misura mente in tutte e due le direzioni

**La batteria sul campo non era mai stata eseguita per intero.** Il 4 agosto e' il primo
giro completo, ed e' quindi la linea di partenza, non una regressione.

**Difetto 1 — salta casi che funzionano.** `_manca` (`tools/campo/batteria.py:59`)
confronta per contenimento delle stringhe che `frasi.py` dichiara a mano contro le
etichette Odoo vere:

| la batteria cerca | l'etichetta vera | si incontrano? |
|---|---|---|
| `data di creazione` | `Data creazione` | no — un «di» di troppo |
| `email` | `E-mail` | no — manca il trattino |
| `commerciale` | `Addetto vendite` | no |

**Ventuno frasi su 54 non sono mai state eseguite, a nessun `context`, in nessun giro** —
e sono tutte le domande sulle date. Il commento della funzione afferma che «il catalogo
dice *Data di creazione*»: e' falso, e lo e' sempre stato.

**E il salto nasconde successi veri**: il prodotto risponde **giusto** a quelle frasi.

    «i lead senza commerciale»        ->  [["user_id", "=", false]]           giusto
    «i lead che hanno un commerciale» ->  [["user_id", "!=", false]]          giusto
    «i lead senza email»              ->  [["email_from", "in", [false, ""]]] giusto

Il modello legge `Addetto vendite` e `E-mail` nel catalogo, sente `commerciale` e
`email`, e capisce da solo. **Il 10 su 20 e' quindi pessimista.**

**Difetto 2 — la coda ferma la batteria.** `QueueRefusal: «In questo momento ci sono
molte richieste in corso»`. La protezione e' giusta per utenti veri, ma la batteria e'
uno strumento che parla col proprio prodotto: si e' fermata al caso 50 il primo giro e al
caso 21 il secondo.

## 5. L'indice dei termini e la robustezza a trattini e parole di servizio

Chiesto dall'Architect. Stato di fatto misurato sull'indice vero (`dictionary/index.py`):

| la frase dice | il sistema trova |
|---|---|
| `e-mail`, `e mail` | ✅ `email_from` |
| **`email`** | ❌ **niente** |
| `data creazione` | ✅ `create_date` |
| **`data di creazione`** | ❌ **niente** |
| `addetto vendite` | ✅ `user_id` |
| **`commerciale`**, **`creati`** | ❌ niente |

**Oggi funziona solo se dici l'etichetta esattamente come l'ha scritta Odoo.** La causa:
il normalizzatore trasforma la punteggiatura in **spazi** (`index.py:44`), quindi
`E-mail` diventa due token e `email` uno solo; e il confronto vuole finestre contigue
della **stessa larghezza**, quindi un «di» in mezzo spezza tutto.

**Dove fa male davvero, e dove no.** Il modello decide quale attributo nomina la frase, e
li' i trattini non contano — l'ha dimostrato su `commerciale`. Lo strato deterministico
e' l'unica autorita' su tre cose: la **Fase A** (quale entita', corsia veloce, 86,2%),
**D105** (se un frammento nomina una condizione del dizionario) e **D135** (se l'utente
la data l'ha gia' detta). **E' D135 che ci costa oggi**:

    «i lead creati oggi»                    ->  clarification
    «i lead con data di creazione di oggi»  ->  clarification

Due domande *«quale data intendi?»* a chi l'ha appena detta. Non e' una risposta
sbagliata: e' una domanda inutile, che fa sembrare il prodotto ottuso.

**Tre problemi distinti, tre rimedi diversi:**

1. **Punteggiatura** (`email` / `e-mail`) → **indicizzare anche la forma attaccata**,
   cosi' `E-mail` produce sia `["e","mail"]` sia `["email"]`. E' un'**aggiunta**, non un
   allentamento: non puo' creare corrispondenze che un termine vero non avrebbe gia'
   creato. Costo zero token, rischio zero.
2. **Parole di servizio** (`data di creazione`) → permettere di **saltare** dentro la
   corrispondenza una lista chiusa e cortissima (`di, del, della, dei, delle, da, a, al,
   in, per, con`). Questo **allarga** il confronto, e `03` §3.9 vieta gli allargamenti
   scelti a intuito: si implementa, si rimisura la Fase A sul corpus, e passa solo se la
   risoluzione non peggiora.
3. **Sinonimi veri** (`creati` / `Data creazione`, `commerciale` / `Addetto vendite`) →
   nessuna regola meccanica ci arriva, `creat` e `creazion` sono radici diverse. Serve il
   livello L1, cioe' **D108** (il registro delle voci approvate del dizionario). La lista
   e' corta, e con 27 attributi invece di 60 si riduce di due terzi.

**Non delegare al modello.** La ragione e' scritta in cima al modulo: la corsia veloce
dev'essere deterministica, o diventa «una seconda componente probabilistica davanti
all'interprete, e RC3 peggiora invece di migliorare». Il modello e' gia' dove serve — sui
sinonimi veri, l'unico dei tre che richiede di capire il significato.

## Cosa e' cambiato su disco, e cosa no

- **Modificato**: `ai/restart.md` (questo file). **Nient'altro nel repository.**
- **Cambiato nel database `db`**: `reasoning_effort` da `high` a `none` sul profilo
  attivo. Correzione, non scelta: allinea il prodotto a D98.
- **Non toccato**: il `context` resta 8192 su server e profilo. Rimetterlo a 4096
  sarebbe una decisione, non una correzione, e i dati dicono che il bersaglio non e' la
  larghezza del `context` ma **quali** attributi entrano.
- **L'esperimento del catalogo forte e' una sostituzione fatta a runtime** dentro una
  shell, con la transazione annullata. Nessuna regola di esposizione e' stata cambiata.
- `aida.debug` acceso per le sonde e **rispento**.

---

# Stato al 5 agosto 2026 — AIDA diventa un pannello

Sessione di sola interfaccia. **Il motore non è stato toccato**: nessuna regola di
esposizione, nessun prompt, nessuna soglia. Quello che è cambiato è dove AIDA vive e
cosa racconta mentre pensa.

Il documento completo è **`ai/20-ux-pannello-aida.md`** — analisi del riferimento con
le misure, decisioni e alternative scartate, protocollo degli avanzamenti, sistema dei
token, budget di prestazioni, accessibilità, debito residuo. Qui c'è solo quello che
serve a una sessione fredda per non ripartire da zero.

## 1. Le due decisioni

**AIDA non è più una pagina, è una colonna a destra.** Un'azione client sostituisce
quello che si stava guardando, ma la domanda tipica di AIDA è *«quali di questi sono
scaduti?»* e ha senso solo se **questi** sono ancora sullo schermo. Larghezza di
partenza 440 px (la misura reale del riferimento Jira Rovo, ricavata dai pixel del
video), ridimensionabile fra 360 e metà finestra.

**Il turno dice a che punto è, con passi veri.** Sette passi che corrispondono alle
fasi che il pipeline percorre davvero. Inventarne di decorativi sarebbe stato mostrare
qualcosa che ha l'aria di essere vero e non lo è — lo stesso principio di **D2** (la
decisione che vieta qualunque scrittura sui dati finché la Fase 2 non è misurata e
superata), applicato all'interfaccia.

## 2. Il vincolo che ha deciso tutto il backend

`core/addons/bus/models/bus.py:106` — `bus.bus._sendone` **non manda niente subito**:
accoda su `cr.precommit` e sveglia il processo del bus su `cr.postcommit`. Parte tutto
al `commit`. E `runtime/worker.py` fa girare l'intero turno **dentro una sola
transazione**, con un `commit` alla fine.

Quindi un avanzamento mandato sul cursore del lavoratore arriverebbe **insieme alla
risposta**: un'animazione che racconta un'attesa già finita.

**L'unica soluzione che funziona è un cursore proprio per ogni evento**, aperto,
scritto e committato subito. È tutto ciò che `runtime/progress.py` fa, e l'unica
ragione per cui quel file esiste.

Tre proprietà blindate, provate senza base dati in `pure_tests/test_progress.py`: non
solleva mai, strozzato a 250 ms, tetto di 12 eventi per turno. **Deroga architetturale
dichiarata** in `tools/arch/spec.py` — il controllo statico l'aveva intercettata al
primo tentativo.

## 3. Le due scoperte che valgono per chiunque tocchi lo SCSS

Sono la stessa famiglia di guasto vista tre volte in questo progetto — *un nome che
sembra collegato e non lo è* — e nessuna delle due dava un errore da nessuna parte.

**`--o-view-background-color` non esiste.** Era il gradino intermedio del fallback in
tutto lo SCSS di AIDA. `$o-view-background-color` è una variabile **SCSS**, risolta a
compilazione: come variabile CSS non arriva mai al browser. In tutto `web/static/src`
ci sono 38 variabili CSS con prefisso `--o-` e nessuna è quella.

**E `--bs-body-bg` non esiste neanche.** Era la correzione ovvia, ed era sbagliata pure
lei: `web/static/src/scss/bootstrap_overridden.scss:51` imposta `$variable-prefix: ''`,
quindi Bootstrap emette **`--body-bg`**, `--primary`, `--border-color`, senza prefisso.
Verificato contando nel pacchetto servito: occorrenze di `--bs-`, **zero**.

È il modo di fallire di un fallback: non c'è nessun errore, perché il gradino
successivo funziona sempre. **L'unica prova possibile è guardare il browser.**

**Corollario da ricordare**: Odoo 18 Community **non ha un tema scuro vero**.
`web.assets_web_dark` aggiunge tre file di componente e lascia la tavolozza dov'è
(nessun `*.dark.scss` fra gli SCSS principali; con il cookie `color_scheme=dark` i
valori a `:root` sono identici). Con la skin Classic AIDA è chiara perché *Odoo* è
chiaro. `enterprise/` è vuota su questa macchina.

## 4. La lezione di metodo

Dieci difetti trovati in una giornata. **Cinque sono passati indenni sotto 256 prove
verdi**, e sono usciti solo compilando gli asset e aprendo un browser:

- `min(300px, 88%)` in SCSS: Sass ha un `min()` suo, provava a calcolarlo, e l'errore
  di unità **fermava la compilazione di tutto `web.assets_backend`** — lo stile
  dell'intera piattaforma, non solo il nostro;
- lo shimmer **cancellava** le prime lettere di «Sto pensando…» (un gradiente ritagliato
  fuori intervallo non sbiadisce il testo: con `color: transparent` lo rende invisibile);
- il segno animato diventava magenta acceso in tema scuro;
- il pulsante era grigio scuro su barra viola;
- la scorciatoia non chiudeva il pannello, perché il fuoco è nella casella.

Per questo esiste **`tools/ui/verify_panel.py`**: il guardare, reso ripetibile. 47
asserzioni — i token risolti nei tre temi, i confini del ridimensionamento, la barra
che non si muove, la bozza che sopravvive alla chiusura, e **ogni** errore JavaScript
della pagina. Non è nella suite (serve Playwright), va lanciato a mano:

```bash
python3 tools/ui/verify_panel.py --db nli_test --password <password>
```

## 5. Cosa è cambiato su disco

**Nuovi**
- `ai/20-ux-pannello-aida.md` — il documento dell'interfaccia
- `custom_addons/nli_dispatch/runtime/progress.py` + `pure_tests/test_progress.py`
- `custom_addons/nli_web/static/src/aida_tokens.scss` — i tre gradini, in un posto solo
- `custom_addons/nli_web/static/src/panel/` — servizio, pannello, pulsante nel systray
- `custom_addons/nli_web/static/src/chat/`: `aida_steps.{js,xml,scss}`,
  `aida_welcome.js`, `aida_history.js` (sostituisce `aida_sidebar.js`, rimosso),
  `aida_thread.xml` e `aida_action.xml` (scorporati da `aida_chat.xml`)
- `tools/ui/verify_panel.py`
- `ai/screenvideo/screen-capture.webm` — il riferimento, 9,4 MB. **Untracked**: se non
  lo vuoi nel repository va in `.gitignore` prima del commit, ma senza di lui le
  misure del documento non sono più riproducibili

**Modificati**
- `runtime/pipeline.py` (sette punti di emissione), `runtime/worker.py`
- `tests/test_dispatch.py` — `TestTheProgressSteps`, 7 prove
- `tools/arch/spec.py` — la deroga per il cursore di `progress.py`
- `tools/pure/bootstrap.py` — pacchetti sintetici per le sotto-cartelle, così le tre
  proprietà si provano senza base dati
- `nli_web/__manifest__.py` — elenco esplicito, non più un glob: i token devono
  caricarsi **per primi**, e con `**/*` l'ordine lo decideva l'alfabeto

**Non toccato**: motore, prompt, regole di esposizione, soglie, profilo.

**Nel database `nli_test`**: la password di `admin` è stata cambiata in `aidatest123`
per poter guidare il browser. L'originale non la conosceva nessuno in sessione.

## 6. Stato delle verifiche

| Verifica | Esito |
|---|---|
| Controlli architetturali | **5 / 5** |
| Prove pure | **504**, 0 fallite |
| Prove Odoo | **256**, 0 fallite (`nli_dispatch` da 101 a 108) |
| `verify_panel.py` | **47 asserzioni** verdi |
| Compilazione pacchetti | backend, Premium, dark — tutti e tre |
| Errori JavaScript nei tre temi | nessuno |

**Niente è stato committato**: tutto è nel working tree del branch `new-ai-agent`.

## 7. Cosa resta aperto sull'interfaccia

1. **Nessuna prova automatica del lato client nella suite.** `verify_panel.py` va
   lanciato a mano e dipende da chi se lo ricorda — e le verifiche che dipendono dalla
   memoria spariscono. Un `tour` Odoo che apra il pannello, mandi una frase e controlli
   che i passi arrivino girerebbe con tutto il resto.
2. **Il ritardo dei passi non è misurato.** Sappiamo che arrivano; non quanto dopo
   l'istante in cui il turno li raggiunge. Una misura fra `report()` e la comparsa
   direbbe se lo strozzamento a 250 ms è il numero giusto.
3. **La cronologia non ha ricerca.** Con quindici conversazioni non serve; con
   trecento sì.
4. **Fuori scope per scelta**: streaming del testo (non esiste), pollice su/giù
   (nessun modello dati), cambio agente (ce n'è uno), bottone di stop (il turno non è
   annullabile).

---

# Stato al 5 agosto 2026 (sera) — il context che non c'era

*Sessione partita per fare P0 (guardare una risposta vera nel pannello) e P1 (riparare
la batteria). Tutti e due fatti. Per strada e' venuto fuori che il prodotto era mezzo
spento da giorni, e nessuno lo sapeva.*

## 1. Il fatto, in una riga

**Ollama serviva 4096 token di context mentre noi ne dichiaravamo 8192.** Il prompt
arrivava tagliato a meta', e il modello — che riceveva un catalogo interrotto a meta'
frase — rispondeva `not_understood`. Non era il modello. Non erano le frasi. Era un
foglio tagliato.

    curl /api/ps  ->  qwen3.5:9b  context_length 4096
    launchctl getenv OLLAMA_CONTEXT_LENGTH  ->  8192

La variabile era impostata, ma il processo di `ollama` era partito prima e non l'aveva
mai vista. Riavviato, serve 8192 (5,8 GB di memoria contro 5,6: mezzo giga in piu').

## 2. La misura, prima e dopo

Tre frasi di difficolta' crescente, tre giri per cella, sulla banca dati `db` col
modello vero. Ogni cella e' **deterministica**: tre volte lo stesso esito.

| frase | 4096 serviti | 8192 serviti |
|---|---|---|
| «mostrami i lead» (solo entita') | 3/3 operations | 3/3 operations |
| «quanti lead ci sono» (conteggio) | **0/3** — `not_understood` | **3/3 operations** |
| «i lead senza commerciale» (condizione) | **0/3** — `not_understood` | **3/3 operations** |

Con 8192 dichiarati **e** serviti, il piano e' anche giusto: `[['user_id', '=',
False]]`, 13 lead su 39, identico nei tre giri. E i tempi sono crollati: **~10 secondi
a turno** contro i 15–145 documentati il 3 agosto.

La traccia diagnostica di **D123** (la decisione che conserva la busta del modello
quando la modalita' diagnostica e' accesa) e' cio' che ha reso leggibile la cosa:

    turno 233  finestra 4096  17 attributi  2940 token  ->  add_measure count   giusto
    turno 235  finestra 8192  60 attributi  4041 token  ->  {"not_understood"}  tagliato

Fra le due celle non cambia altro. 4041 token piu' il messaggio di sistema non stanno
in 4096, e il taglio cade dentro il catalogo.

## 3. Cosa questo obbliga a rileggere

**Il reperto §3 del 4 agosto — *«il catalogo intero affoga il modello»* — e' stato
misurato su un prompt tagliato.** Non e' detto che sia falso, ma non e' piu' provato:
con i due numeri allineati il catalogo da 60 attributi non affoga niente, ed e' l'unico
che permette di rispondere alla frase con la condizione — a 4096 il budget di **D79**
(la decisione che ricava dalla finestra quanti attributi mostrare) non espone
`crm_lead.user_id`, quindi «senza commerciale» non e' fondato in nessun attributo e
**D121** (la decisione che fa proporre letture invece di indovinare) chiede, giustamente.

Ricadute sull'ordine dei lavori:

* **P5 (`1d`, la selezione degli attributi)** nasceva da *«troppi attributi confondono
  il modello»*. Quella premessa va rimisurata prima di spendere il lavoro. Sfoltire
  resta utile per il costo del prompt, ma non e' piu' un'emergenza.
* **P6 (il corpus a `--finestra 4096`, ~70 minuti macchina)** doveva separare D113–D120
  da **D133** (la decisione che impone di guardare vicine la finestra dichiarata e
  quella servita). La risposta e' arrivata da qui, senza il corpus: era D133.
* **`19` (la scelta del modello)** e' da rileggere con i tempi nuovi: le misure del
  3 agosto sono state prese con lo stesso taglio.

**La lezione di metodo**: D133 aveva gia' scritto il fenomeno — *«dodicimila token
mandati, 2050 letti»* — e nessuno aveva ricollegato i `not_understood` a quello. Una
misura scritta nel registro e non collegata ai sintomi e' una misura che non lavora.

## 4. P1 — la batteria non salta piu' ventuno frasi

`_manca` (`tools/campo/batteria.py`) confrontava per contenimento le stringhe scritte a
mano in `frasi.py` con le etichette Odoo vere. Non si incontravano: `email` contro
`E-mail`, `commerciale` contro `Addetto vendite`, `citta'` contro `Citta'`.

Ora `serve` dichiara i **riferimenti** del catalogo — `crm_lead.user_id` — e il
confronto e' per appartenenza. Il `ref` e' cio' che il catalogo pubblica, non una
traduzione che qualcuno ha scritto in un altro file.

| finestra | attributi esposti | frasi saltate |
|---|---|---|
| 4096 | 17 | 25 / 54 |
| 8192 | 60 | **0 / 54** (prima: 21, sempre le stesse) |

Il filtro non e' stato annacquato: a 4096 morde ancora, ed e' li' che si vede che il
budget non espone nemmeno `crm_lead.name`, il nome del lead.

Aggiunta una **guardia**: su una banca dati che non espone `crm_lead` la batteria si
ferma e lo dice. Prima ripiegava su `scope[0]` e su `nli_test` chiedeva «mostrami i
lead» al catalogo dei contatti, chiamando sbagliato il modello per aver risposto sui
contatti. Un ripiego silenzioso in uno strumento di misura e' un terzo modo di mentire.

Lasciato aperto, in un commento dentro `frasi.py`: **«per stato» e' una trappola.** Sul
catalogo vero `Stato` e' `state_id`, la provincia; la fase di vendita si chiama `Fase`
(`stage_id`). Chi ha scritto le frasi intendeva la fase, ma l'attesa conta *quanti*
raggruppamenti e non su cosa, quindi un raggruppamento per provincia passerebbe lo
stesso. Due decisioni da prendere: se la frase va detta «per fase», e se almeno qui
l'attesa debba nominare il riferimento del raggruppamento.

## 5. P0 — c'e' finalmente una risposta vera da guardare

Su `db`, **conversazione 207**, a 8192 dichiarati e serviti:

| turno | esito | cosa mostra |
|---|---|---|
| 277 | operations, 39 record | la prima tabella |
| 278 | operations, 39 record | **tabella a quattro colonne** — lo scorrimento orizzontale |
| 279 | operations | la riga del conteggio |
| 280 | clarification | «i lead creati negli ultimi 30 giorni» — chiede, e va capito perche' |
| 281 | clarification | «i lead di oggi» — D135, l'esito giusto |
| 282 | out_of_scope | il rifiuto onesto |

Due tabelle nello stesso filo: e' il caso del punto 2 di P0, quello in cui l'altezza
sbaglia. Tutti e sei hanno la traccia diagnostica, quindi anche il blocco di D123 e'
visibile. Resta da **guardarla con gli occhi**: il pannello del browser non e'
raggiungibile dalla sessione, quindi il punto 5 di P0 e' consegnato ma non chiuso.

La conversazione **188** e' lo stesso filo a 4096, tenuta per confronto. La **161** e'
la conversazione delle diciotto risposte tagliate: da tenere, e' la prova del difetto.

## 6. Cosa e' cambiato su disco, e cosa no

**Nel repository**, solo lo strumento di misura — nessuna riga di prodotto:

* `tools/campo/batteria.py` — `_catalogo_riferimenti`, `_manca` sui `ref`, la guardia.
* `tools/campo/frasi.py` — `serve` in riferimenti, la nota sulla trappola di «per stato».

`./manage.sh check` verde.

**Nelle banche dati**, che non sono nel repository e vanno sapute:

* `db`: profilo attivo con `context_window` **8192**, `aida.debug` **acceso** (spegnerlo
  quando non serve piu': conserva la frase dell'utente in chiaro), conversazioni 161,
  188, 207.
* `nli_test`: profilo `qwen3.5:9b (P0)` creato e attivo, che prima non c'era — e' il
  motivo per cui i turni erano tutti fermi in `pending`. Il perimetro li' e'
  `res.partner` e le etichette sono in inglese: non e' una banca dati su cui misurare.
* I tre cron di AIDA vengono spenti per la durata della batteria e riaccesi dopo — la
  batteria pilota `pipeline.run` nella shell e il cron lavorerebbe sugli stessi elementi
  di coda (`expired`, `could not serialize access`).

## 7. La prima misura completa che sia mai esistita

54 frasi su 54 eseguite, **zero saltate**, con lo strumento riparato e i due context
allineati. Sette minuti di macchina, non un'ora: i turni ora costano 5–10 secondi.

| famiglia | come atteso |
|---|---|
| operatori | 11/12 — 92% |
| intenti | 10/18 — 56% |
| limiti | 3/6 — 50% |
| **date** | **1/18 — 6%** |
| **totale** | **25/54 — 46%** |

Questa e' **la linea di partenza** che `18` §12 (l'ordine di lavoro del fine tuning)
pretende prima di addestrare. Prima non esisteva: il giro del 4 agosto aveva 21 frasi
mai eseguite, un prompt tagliato a meta' e si fermava al caso 25 su 54.

**Perche' si fermava al 25**, ed e' il difetto 2 di §4 finalmente capito: la batteria
chiama `pipeline.run`, che interpreta il turno e non tocca la coda. Nel prodotto e'
`worker._persist` a chiamare `complete()`; qui non lo chiamava nessuno, ogni frase
lasciava la sua riga in `pending`, e al venticinquesimo si superava **L3** (la
profondita' della coda: pool 8 x 3 = 24). Riparato chiudendo l'elemento come fa il
worker — non alzando il limite, che avrebbe nascosto il difetto invece di toglierlo.

## 8. Il difetto singolo che vale 17 fallimenti su 29

**Le date non sono diciassette difetti: sono uno, ripetuto.** Tutte e diciotto le
frasi dicono `clarification` invece di rispondere, e il modello non c'entra — risponde
giusto:

    la busta del modello   crm_lead.create_date  within  last_n_days 30   corretta
    il prodotto rifiuta    L3 [unanchored_period]

Il messaggio del rifiuto: *«il periodo su `crm_lead.create_date` viene da un frammento
che non nomina nessuna data (“negli ultimi 30 giorni”); questa entita' ne espone 7 e
D110 non ne dichiara nessuna principale, quindi l'attributo l'ha scelto il modello»*.

Il controllo guarda il **frammento**, e il frammento davvero non nomina date. Ma la
frase intera dice *«i lead **creati** negli ultimi 30 giorni»*: la parola che ancora
c'e', sta solo fuori dal pezzo di frase che il modello ha dichiarato come provenienza.

**E questo tocca la premessa di D110**, che e' scritta a chiare lettere: *«un'espressione
di tempo non nomina mai il proprio campo, ne' nel corpus ne' in italiano: si dice
“ordini del mese scorso”»*. Per il corpus sara' vero. Per l'italiano che una persona
scrive in chat **non lo e'**: diciotto frasi su diciotto nominano la data.

Tre strade, e la scelta e' dell'Architect perche' tocca una decisione adottata:

1. **Il riconoscitore passa sulla frase intera, non sul solo frammento**, e l'ancora
   vale solo se il termine trovato porta **allo stesso attributo** che il modello ha
   scelto. Non allarga la garanzia di D111 (un'espressione di tempo che non si colloca
   si chiede): la sposta da «nominata nel frammento» a «nominata nella frase e
   concorde». Costo piccolo. Da verificare che il dizionario leghi *«creati»* a
   `create_date`, che si chiama `Data creazione`: sono due forme diverse della stessa
   parola, e §5 del 4 agosto dice che l'indice dei termini e' robusto a trattini e
   parole di servizio, non alle desinenze.
2. **Il prompt chiede che la provenienza copra la parola che ancora.** Non tocca
   nessuna regola, ma dipende dall'obbedienza del modello e va misurato.
3. **Dichiarare una data principale per entita'** (oggi D110 dice esplicitamente che
   nessuna lo e'). E' la strada che indovina, ed e' quella che D110 ha gia' scartato.

La 1 e' stata deliberata e fatta, la sera stessa. Vedi §9.

**Gli altri diversi**, per completezza: `out_of_scope` su frasi legittime («qual e' il
ricavo atteso piu' alto», «il ricavo atteso medio per stato») — il prodotto dichiara
fuori perimetro cose che sa fare; e due limiti dichiarati che **non** vengono piu'
rifiutati («i secondi 20 lead», «i lead che non sono di milano» rispondono invece di
chiedere), che va guardato perche' e' una garanzia che si e' allentata.

**Rumore nei log**: `pipeline.py:93` chiama `_()` senza una lingua nel context, e Odoo
stampa una traccia di stack a ogni chiarimento. Non cambia il comportamento, sporca
ogni misura.

## 9. L'ancora del tempo, riparata — e serviva riparare due cose

**Pezzo uno: le parole.** Il riconoscitore conosceva l'etichetta Odoo `Data creazione`
e non la forma verbale «creati», e fra le due c'e' una desinenza che nessuno fa. Sono
venti voci **T1** nel registro delle voci approvate di **D108**, livello L1 (il
dominio: che «creati» sia il participio di «creazione» e' un fatto della lingua, non di
questa installazione). Le voci T1 **si fondono** fra i livelli (`06` §2.2), quindi il
sinonimo non toglie l'etichetta: la data si chiama in tutti e due i modi.

Stanno in `tools/dizionario/sinonimi_date.py`, con `./manage.sh dizionario <db>` e la
sua prova a vuoto. Sono dati e non codice, e non sono nel modulo: chi installa in
inglese non li vuole, chi aggiunge un'entita' al perimetro li rivuole.

**Le date di ordini e fatture sono state lasciate fuori apposta.** Per
`sale_order.date_order` verrebbe naturale «ordinati», che in italiano vuol dire anche
*messi in ordine*: *«gli ordini di questo mese ordinati per totale»* nominerebbe una
data che nessuno ha nominato. Meglio nessun sinonimo che uno che indovina.

**Pezzo due: dove si guarda.** `validate_anchoring` accetta ora l'ancora presa dalla
**frase intera**, e non solo dal frammento — ma solo quando la frase nomina **una sola**
data fra quelle in scelta, e quella e' la data su cui il periodo e' caduto. Con due
nominate decide il frammento come prima, perche' li' la scelta torna a essere del
modello.

E' una via d'uscita **in accettazione**: nessun turno che prima passava puo' iniziare a
fallire. E' cio' che la rende compatibile con la ragione — scritta nel codice — per cui
il livello 3 guarda il frammento: un turno di raffinamento porta condizioni di frasi
che nessuno sta piu' dicendo, e verificarle contro la frase corrente le rifiuterebbe
tutte.

Cinque prove nuove in `test_anchoring.py`. Tolta la riga aggiunta, due diventano rosse.

**Serviva davvero tutt'e due?** Si', e i numeri lo dicono: con i soli sinonimi la
famiglia `date` e' passata da 1/18 a **13/18** — nelle frasi corte il modello mette
«creati» dentro il frammento da solo — e le tre che restavano erano tutte della forma
*«negli ultimi N giorni»*, dove il frammento dichiarato porta solo il tempo. Con la
frase intera anche quelle rispondono: *«i lead creati negli ultimi 30 giorni»* → 25
record, zero fallimenti.

**Un difetto mio, per memoria di chi tocchera' questa catena.** La prima stesura
aggiungeva il parametro a `_apply_and_present` e ai suoi due chiamanti, e si fermava
li': dentro, la chiamata a `contextual.validate` non lo passava. Il valore arrivava e
moriva. Le prove pure erano verdi lo stesso — provavano la regola, non il cablaggio.

`test_the_chain_carries_the_sentence_through` copre un pezzo del cablaggio: se
`contextual.validate` smette di passare la frase a `validate_anchoring`, diventa rossa.
**Il pezzo che si e' rotto davvero — `pipeline` verso `validate` — non e' coperto**, e
non puo' esserlo da una prova pura: la pipeline vuole Odoo. Va scritta una prova nella
suite di `nli_dispatch`, ed e' aperta. A trovare il difetto e' stata la misura sul
campo, il che dice quanto e' costato non averla.

## 10. La misura dopo: 39 su 54, e una maschera caduta

| famiglia | prima | dopo |
|---|---|---|
| date | 1/18 — 6% | **17/18 — 94%** |
| operatori | 11/12 | 11/12 |
| intenti | 10/18 | 10/18 |
| limiti | 3/6 | **1/6** |
| **totale** | **25/54 — 46%** | **39/54 — 72%** |

**I limiti sono scesi, e non e' una regressione: e' una maschera caduta.** Le due frasi
che hanno smesso di passare sono *«i lead creati nel primo trimestre»* e *«i lead creati
a gennaio»*. Passavano perche' rispondevano `clarification`, che e' quello che l'attesa
chiede — ma lo rispondevano **per il motivo sbagliato**: non stavano rifiutando l'anno
ambiguo, stavano chiedendo *quale data*. Riparata l'ancora, la domanda non c'e' piu' e
si vede cosa il prodotto fa davvero:

    «i lead creati nel primo trimestre»
      la busta del modello   within current_quarter
      il piano risolto       create_date >= 2026-07-01  <  2026-09-30
      la risposta            26 record, presentati come giusti

**Il primo trimestre risposto col terzo.** `ai/17` dichiara che una data senza anno non
si puo' dire e va rifiutata; il rifiuto non esiste, e al suo posto c'e' una risposta
sbagliata con l'aria di essere giusta — la classe di fallimento peggiore che questo
prodotto possa produrre, e quella che **D2** esiste per tenere fuori.

Il difetto e' vecchio: la busta con `current_quarter` il modello la produceva anche
prima. E' cambiato solo che ora si vede. Una misura che sale scoprendo un difetto piu'
grave di quello che ha risolto sta facendo il suo mestiere.

Gli altri quindici diversi restano quelli gia' descritti in §8: il rifiuto sbagliato su
frasi legittime, i pezzi di frase lasciati cadere («i secondi 20 lead», «i lead che non
sono di milano»), e qualche caduta del modello.

## 11. Il raffinamento era morto, e la batteria non poteva vederlo

**Trovato al primo uso vero del pannello**, subito dopo aver riparato le date. Sequenza:
*«i lead creati nel primo trimestre»* → risposta; *«ordinameli per email»* → **«Non ho
capito»**. E il rifiuto non parlava dell'ordinamento:

    L3 [unanchored_period] crm_lead.create_date: carries no provenance

Parlava del **filtro del turno prima**. Il meccanismo, per intero:

1. Ogni turno rivalida lo stato **completo**, non solo cio' che la frase ha aggiunto.
2. Lo stato salvato **non ha i frammenti**: `strip_provenance` li toglie di proposito,
   e resteranno tolti finche' **D54** non li pseudonimizza.
3. Il livello 3 delle date pretende il frammento. La condizione ereditata non ce l'ha
   e non potra' mai averlo: rifiuto garantito, ogni turno, per sempre.

Quindi **dopo un filtro sulle date qualunque raffinamento moriva** — l'ordinamento, una
colonna in piu', un altro filtro. Non era una regressione di oggi: c'era da quando D135
esiste. Prima non si vedeva perche' il primo turno con una data non rispondeva mai.

**La correzione**: il livello 3 giudica solo le condizioni che **questo turno ha appena
introdotto**. Gli identificativi di quelle gia' presenti arrivano dallo stato di
partenza (`state_module.condition_ids`), e si saltano. E' cio' che D135 dice gia' a
parole — si giudica la data che *il modello ha appena scelto* — e una condizione
accettata in un turno passato e' stata giudicata allora, con le prove che allora
c'erano.

Provato sul prodotto, tre turni in fila:

    i lead creati quest'anno        operations   39 record
    ordinameli per email            operations   39 record   ordine email_from asc
    solo quelli senza commerciale   operations   13 record   + user_id = false

**La lezione, e vale piu' della correzione.** La batteria apre **una conversazione
nuova per ogni frase**, di proposito, perche' D120 e D127 (il turno prima fa da
contesto) falserebbero la misura. Conseguenza: nessun secondo turno viene mai provato,
e un difetto che uccideva ogni conversazione a partire dalla seconda battuta ha
attraversato tutte le misure senza lasciare traccia. Le 54 frasi misurano **la prima
domanda**. Serve una famiglia che misuri **le conversazioni** — ed e' aperta.

## 12. Le parole che AIDA mostra: etichette, lingua, pacchetti

Nato da una prova tua nel pannello: *«mostrami i lead di questo trimestre»* ha risposto
**`Which date do you mean by “di questo trimestre”?`** con le opzioni `creazione`,
`Ultima azione`, `chiusura`, `conversione`. Due difetti in una schermata.

### 12.1 Le etichette — un difetto introdotto la sera stessa

Le opzioni mostravano `creazione` invece di `Data creazione`: erano **i sinonimi
scritti da me poche ore prima** (§9). Il codice mostrava `terms[0]`, e la fusione fra
livelli mette per primo il livello piu' alto — da quel momento L1, cioe' il mio.

`store._merge` dice a chiare lettere che l'ordine dei termini e' *«quello con cui
l'interpretazione mostra il riferimento all'utente, cosi' la parola del cliente viene
prima di quella del fornitore»*. La regola era giusta; erano i miei sinonimi a non
avere titolo per quel posto: `creati`, `chiusi`, `assegnati` sono **flessioni**, parole
per riconoscere, non nomi.

**La regola nuova, da mettere a registro**: si mostra il nome che qualcuno ha **scelto**
per quella cosa — quello del cliente (L2) se c'e', altrimenti quello della piattaforma
(L0), che per giunta Odoo traduce gia' da se'. **L1 non nomina mai.**

In pratica: il dizionario espone `display_of(ref)` accanto a `terms_of(ref)`, il
catalogo porta `label` accanto a `terms`, e la domanda di chiarimento usa `label`.
Quattro prove nuove in `test_dictionary.py`.

    prima   creazione     Ultima azione   chiusura        conversione
    dopo    Data creazione Ultima azione  Data chiusura   Data conversione

### 12.2 La lingua non era mancante: non arrivava

La domanda usciva in inglese benche' l'utente sia `it_IT`, e a ogni chiarimento il log
stampava una traccia di stack — *«no translation language detected»*. Le due cose erano
la stessa cosa.

`_()` di modulo ricava la lingua **dal chiamante**, cercandogli in casa un `self` o un
`env`. `_anchor_clarification(failures, operations, catalogue)` non aveva ne' l'uno ne'
l'altro, quindi Odoo rinunciava. Il contesto giusto c'era gia' — `context_for_execution()`
porta `lang` e `tz` del turno fin dentro il worker: nessuno glielo chiedeva.

Sostituito con `env._()`, che la lingua la prende dal contesto invece che dallo stack.
Sparita anche la traccia nei log, che sporcava ogni misura.

### 12.3 I pacchetti lingua

Deciso: **sorgente inglese, un pacchetto per lingua, ripiego sulla sorgente.** E' il
funzionamento nativo di Odoo — lingua dell'utente, e se la traduzione manca esce
l'inglese — quindi non serve scrivere codice, serve mettere in ordine le stringhe.

Estratti i cataloghi di tutti e sei i moduli in `custom_addons/nli_*/i18n/*.pot`:
**264 stringhe**. Scritto `nli_dispatch/i18n/it.po` con le frasi che AIDA dice in un
turno. Provato sul prodotto: *«Quale data intendi con «di questo trimestre»?»*.

**Cosa manca, ed e' il punto da cui si riprende.** Quaranta stringhe del pannello sono
scritte **in italiano nel sorgente** — `Chiedi ad AIDA`, `Come ho letto la domanda`,
`Ci sto ancora pensando…`. Finche' stanno li', un utente inglese vede italiano e
**nessun pacchetto lo puo' correggere**: non esiste una sorgente da cui tradurre. Vanno
ribaltate in inglese, e l'italiano va nel `it.po`.

I template OWL **sono gia' estraibili**: Odoo li legge da se', e le 134 stringhe di
`nli_web` nel `.pot` lo dimostrano. Il lavoro e' meccanico: 40 stringhe da ribaltare,
piu' i `it.po` degli altri cinque moduli (etichette di campi e di menu, che vede
soprattutto un amministratore).

---

# Da dove si riprende

In ordine, e il primo e' il piu' grave:

1. **La data senza anno** (§10). *«nel primo trimestre»* risponde col **terzo**, 26
   record, senza dire niente. `ai/17` dichiara che va rifiutata; il rifiuto non esiste.
   E' la stessa forma di *«i secondi 20 lead»* e *«i lead che non sono di milano»*: un
   pezzo di frase che il vocabolario chiuso non sa dire e che viene lasciato cadere in
   silenzio. Una regola sola li copre tutti e tre, ed e' la delibera da prendere:
   allargare il vocabolario, oppure rifiutare — che e' cio' che gia' promettiamo.
2. **Finire i pacchetti lingua** (§12.3): 40 stringhe del pannello da ribaltare in
   inglese, `it.po` per i cinque moduli restanti.
3. **Guardare il pannello con gli occhi**: conversazione **207** su `db`, sei turni
   veri. Il punto 5 e il punto 6 dell'interfaccia sono ancora aperti.
4. **Le due prove che mancano**: il cablaggio `pipeline` → `validate` (§9) e una
   famiglia di **conversazioni** nella batteria (§11).
5. `out_of_scope` su frasi legittime (§8), che oggi vale 4–5 casi.

**Prima di misurare qualunque cosa, si controlla che Ollama serva 8192**:

    curl -s http://127.0.0.1:11434/api/ps | grep context_length

`OLLAMA_CONTEXT_LENGTH=8192` sta in `launchctl setenv`, che **non sopravvive al riavvio
del Mac**. Se dice 4096, tutto torna a rispondere `not_understood` e nessuno lo segnala:
si riavvia Ollama, e prima o poi si scrive un `LaunchAgent` che la renda permanente.

---

# Aperto, in ordine di quanto sblocca

1. **La selezione degli attributi.** E' il primo perche' vale piu' di qualunque altra
   cosa in lista: otto frasi su venti passate da sbagliate a giuste, **senza toccare il
   modello e senza una riga di codice nuova**. La proposta e la sua prova stanno qui
   sopra, in «Stato al 4 agosto 2026» §3. Quattro passi, in quest'ordine.

   **1a. Misurare la copertura con i residui nascosti.** E' un **cancello**: se scende
   sotto il 99% che **D34** pretende, la regola non e' adottabile cosi' com'e' e va
   ammorbidita. Sto per togliere 16 attributi a `crm.lead` e 33 a `res.partner`, e sono
   quasi certo che siano rumore — ma «quasi certo» non e' un numero, e il guadagno lo
   vedrei mentre il danno resterebbe invisibile.

   **1b. Togliere il blocco della coda** che ferma la batteria (`QueueRefusal`). La
   protezione e' giusta per utenti veri; la batteria e' uno strumento che parla col
   proprio prodotto. Senza questo, il numero riguarda solo le prime venti frasi — tutte
   della stessa famiglia, e le altre trentaquattro (date, operatori, limiti) sono le
   difficili.

   **1c. Riparare le attese della batteria** (`_manca` e le stringhe di `frasi.py`).
   Non e' manutenzione: lo strumento **inventa fallimenti e nasconde successi**, ed e'
   la ragione per cui 21 frasi su 54 non sono mai partite. Vedi §4 qui sopra.

   **1d. Deliberare**, con i numeri in mano. Serve perche' fra sei mesi chi trovera' i
   residui nascosti li rimettera' dentro alla prima frase che non funziona — e perche'
   il 4 agosto abbiamo avuto la prova di cosa costa una scelta non scritta: il
   `reasoning_effort` a `high` e' stato trovato **solo** perche' D98 stava nel registro.

   **In parallelo, perche' tocca solo la zona pura** (nessun database, nessun modello,
   prove deterministiche): la robustezza dell'indice dei termini a trattini e parole di
   servizio, §5 qui sopra. Chiesta dall'Architect il 4 agosto.

   **Restano da fare, dalla vecchia lista:**

   * **il controllo del corpus a `--finestra 4096`** con il codice di oggi, per separare
     il contributo di D113-D120 da quello di D133. ~70 minuti di macchina, nessuna
     attesa umana;
   * **la batteria per intero**, dopo 1b e 1c;
   * **i tre candidati di `19`** — `qwen3.5:2b`, `:4b`, `:9b` — con la generazione
     vincolata accesa, che il banco di `19` §2 non aveva. **Da rifare col catalogo
     selezionato**, non con quello da 60: misurarli sul catalogo rumoroso direbbe che
     sono tutti scarsi, e non e' quello che vogliamo sapere.

   **Attese scritte prima di misurare**, cosi' che una previsione sbagliata si veda:

   * il 10 su 20 della batteria e' **pessimista**, perche' fra i 4 casi «saltati» ce ne
     sono che il prodotto risponde giusto (misurato: `commerciale`, `email`);
   * i **6 casi ancora sbagliati** sono tutti di aggregazione (*somma*, *media*, *piu'
     alto*) e **non** si muoveranno con la selezione degli attributi: se si muovono,
     l'ipotesi «fronte separato» era sbagliata;
   * la copertura di 1a **non** dovrebbe scendere sotto il 99%. Se scende, i residui
     coprivano qualcosa che nessuno aveva notato, ed e' un risultato piu' interessante
     del passaggio del cancello.

2. **Il fine tuning, deciso dall'Architect il 3 agosto.** I due documenti sono scritti e
   sono la specifica: `ai/18` per la modalita' (LoRA a 16 bit, RunPod, ~$40) e `ai/19`
   per il modello (Qwen3.5-4B principale, 2B in parallelo, 9B riserva). Manca il lavoro.

   **Dove siamo nell'ordine di `18` §12**: il passo 1 (alzare la finestra a 8 192) e'
   **fatto**, ed e' D133. Il passo 2 — rimisurare la linea di partenza col contratto di
   oggi — **non e' fatto, ed e' bloccato dal punto 1c di questa lista**: la batteria
   inventa fallimenti e nasconde successi, quindi qualunque numero produca oggi non e'
   utilizzabile come linea di partenza. `18` §12 lo dice a modo suo — *«i passi 1 e 2
   vanno fatti comunque, anche se il fine tuning non si facesse mai»* — e la
   conseguenza e' che **il punto 1 e il punto 2 di questa lista condividono lo stesso
   primo ostacolo**. Riparare la batteria li sblocca tutti e due.

   Senza la linea di partenza il cancello di `18` §9 non e' verificabile: le dieci
   soglie di `18` §1 si leggono contro un «oggi» che dev'essere un numero fresco, e
   quattro di quelle righe dicono gia' *«non misurata»*.

   **Cosa si puo' fare in parallelo, senza aspettare la batteria** — sono lavori sui
   dati e non sulle misure:

   * la pulizia dell'atlante e la seconda raccolta senza italiano (i primi due punti
     qui sotto);
   * lo strato dei sinonimi;
   * e soprattutto **D85**, che dipende da persone e ha i tempi piu' lunghi di tutto.

   Il resto — generatore, prova di fumo, corse — arriva dopo, ed e' in quest'ordine:

   * **pulire l'atlante**: `tools/finetuning/atlante.json` porta 333 entita' e 7 918
     attributi, ma i termini delle entita' contengono le **voci di menu filtrate**
     (`sale_order` risulta nominabile come *«carrelli abbandonati»*, che e' una
     condizione, non un nome). Le scartate non si buttano: diventano candidate
     categorie T5;
   * **raccogliere l'atlante una seconda volta senza l'italiano**, per la quota di
     cataloghi in inglese di `18` §5bis. Stesso comando, banca dati senza la lingua;
   * **lo strato dei sinonimi** sulle famiglie nuove — magazzino, produzione, personale,
     progetti, contabilita'. Gli attributi hanno **un termine solo**: la mediana e' 1, e
     tutto il gergo e' lavoro nostro. `ai/corpus/lessico_l1.json` ne ha gia' ventuno,
     scritti per il corpus e riusabili;
   * **il generatore**: intento -> frase, catalogo vero con budget variabile, prompt vero
     da `prompt.system_message()`, e ogni esempio validato dal nostro validatore prima di
     entrare nel dataset;
   * **la prova di fumo** da 500 esempi su una A6000 affittata ($2), che verifica la
     catena intera e da' la velocita' vera;
   * **le due corse** e il cancello di `18` §9.

   **La banca dati `atlante`** con tutte e 35 le applicazioni piu' i nostri sei moduli e'
   gia' installata e serve solo a questo: non e' una banca dati di lavoro.

   **E la cosa che dipende da persone e ha i tempi piu' lunghi**: gli enunciati veri di
   **D85**. Senza, il dataset resta fatto delle frasi che ci scriviamo da soli, e la
   misura migliorerebbe piu' del prodotto. Va avviata in parallelo a tutto il resto.

3. **Quello che il controllo di architettura ha lasciato aperto.** `ai/17` §6 e' l'ordine
   di lavoro; D129–D134 ne hanno chiuso la prima meta'. Resta:

   * **R5 — i join non esistono.** `Binding.field` promette un percorso puntato
     (`partner_id.city`) che **nessuno emette mai**: nessun riferimento attraversa una
     relazione. *«le citta' con piu' lead»*, *«i contatti di Roma»* — quest'ultima ha
     dato 0 record il 3 agosto e va riguardata con questo reperto in mano. Non si
     improvvisa: e' una delibera, con tre questioni da decidere prima di scrivere
     (quali relazioni esporre, come si chiama il riferimento promosso, chi paga il
     costo). **Nel frattempo la documentazione dice il contrario e va corretta.**
   * **M1–M4, i quattro scollegamenti minori**: `revert_last` e `open_record` che non
     fanno niente (*«torna indietro»* rilancia la stessa query e sembra riuscito), il
     margine della fase A che non chiede mai niente (D33), `_persist` fuori dal `try`
     del lavoratore.
   * **M7/M8** — la negazione non e' producibile (*«i lead che non sono di Roma»*) e
     mancano `not_equals` e `ends_with`. Sono contratto: vanno numerate prima di
     scrivere codice.

4. **Non esiste nessuna prova del lato client nella suite.** *(ridotto il 5 agosto,
   non chiuso.)* E' il rischio che ha prodotto due dei sette difetti di `00` §38: un
   componente OWL dichiarato e non importato ha fatto sparire l'intera chat con 147
   prove verdi. Il quinto controllo dei confini prende quella sola classe di errore.

   Dal 5 agosto c'e' **`tools/ui/verify_panel.py`**: 47 asserzioni in un browser vero —
   token risolti nei tre temi, confini del ridimensionamento, la barra che non si
   muove, la bozza che sopravvive alla chiusura, e ogni errore JavaScript della pagina.
   Ha gia' preso cinque difetti che 256 prove verdi non vedevano.

   **Ma sta fuori dalla suite** (serve Playwright) e va lanciato a mano, quindi dipende
   da chi se lo ricorda — e le verifiche che dipendono dalla memoria spariscono. Serve
   ancora un banco vero: un `tour` Odoo che apra il pannello, mandi una frase e
   controlli che i passi arrivino girerebbe con tutto il resto.

5. **Una risposta riuscita non e' mai stata vista disegnata.** *(riformulato il 5
   agosto: la meta' che restava e' piu' importante di quella chiusa.)*

   Il **contenitore** adesso e' stato guardato: pannello, intestazione, casella,
   cronologia, schermata iniziale, attesa e passi, nei tre temi, con dieci difetti
   trovati (`ai/20-ux-pannello-aida.md` §7).

   Il **contenuto di una risposta** no. I turni di `nli_test` erano tutti fermi in
   `pending` dalle batterie di carico, quindi la vista lista incorporata, la riga del
   conteggio, «Come ho letto la domanda», le opzioni di chiarimento di D121 e la riga
   dei comandi **non li ha visti disegnare nessuno, nemmeno una volta**. Lo stile c'e',
   la prova che regga no — ed e' proprio la parte che il pannello stretto mette alla
   prova piu' della pagina intera.

   Costa mezz'ora: modello acceso, una banca dati con dati veri, una frase, e si
   guarda. Va fatto **prima** di dichiarare finita l'interfaccia, e prima del punto 6,
   che dipende da cosa si vede qui.

6. **La tabella non ha la paginazione, e adesso conta di piu'.** Il pannello di
   controllo e' spento perche' `Nuovo` e la barra di ricerca non devono stare in una
   risposta (`00` §33.6), e con lui se n'e' andato il selettore di pagina che `15`
   chiede. Si riaccende tenendo spente le parti di sinistra e destra: una riga, ma
   dipende da nomi interni di Odoo.

   **Il pannello alza la posta**: in una colonna da 440 px una lista senza selettore di
   pagina si consulta peggio che a tutta pagina. C'e' un'attenuante nuova — «Apri a
   tutta pagina» lancia l'azione Odoo con lo stesso dominio, dove la paginazione c'e' —
   ma e' un rimedio, non la risposta. Da decidere dopo il punto 5.

7. **I nomi delle entita' non sono misurati su un'installazione vera.** Il corpus gira su
   un pacchetto scritto a mano: i suoi «0 determinazioni sbagliate» **non coprono**
   **D126**. Il rischio che un nome di menu tiri a se' una frase che non gli appartiene —
   *«Flusso»* verso i lead — lo sorveglia solo il margine della fase A.

8. **D7** (due clienti pilota) e **D85** (~200 enunciati elicitati da 8–10 persone di
   mestiere, non richiede ne' clienti ne' prodotto attivo). Sono le due cose che bloccano
   davvero, e nessun giro di misura le sposta. **D52** — quanto costa oggi la stessa
   informazione sull'interfaccia nativa — ha una scadenza che non dipende da noi: va
   fatta prima di attivare il primo utente, dopo non e' piu' ottenibile.

9. **`filter` al 79,5%, e la famiglia che resta.** Rimisurato su tutte le 414 aperture
   (`00` §21.7). Delle tre famiglie da undici, due sono state affrontate — il predicato
   sinonimo con **D113**, i rifiuti con **D114**, **D118** e **D119**. Resta la terza:
   il predicato possibile ma sbagliato, il valore preso male, le due condizioni fuse in
   una.

   ~~**La misura dopo D113–D120 non e' stata fatta.**~~ **Fatta il 4 agosto 2026**, ma
   **non e' attribuibile**: contiene anche D133, perche' la linea del 70,0% precede tutte
   e due. Misurato 75,8% e `filter` 85,0% contro un'attesa di ~75,3% e ~84,8% scritta in
   `00` §22.3 **per D113-D120 soli, a `context` invariato**. Sembra un centro perfetto e
   non lo e': due cause dentro una misura sola. Si separa col controllo a
   `--finestra 4096`, che resta da fare. Vedi «Stato al 4 agosto 2026» §2.

10. **Il secondo tentativo non puo' esistere.** Il cron di recupero rimette in coda un
   turno rimasto orfano perche' ci riprovi (`MAX_ATTEMPTS`), e **L4 garantisce che il
   secondo tentativo non parta mai**: appena torna `pending` ha gia' piu' di trenta
   secondi di vita, quindi il giro successivo lo scarta. Due regole che si annullano, e
   il contatore dei tentativi e' codice che non gira. Va deciso quale delle due cede:
   L4 misura da quando l'utente ha chiesto (e allora scartare e' giusto, ma il recupero
   e' inutile), oppure misura l'attesa in coda (e allora un turno ripreso riparte da
   zero). **L4 e' un limite numerato di `05`: non lo tocco senza delibera.** Legato:
   il modello impiega ~96 secondi e L4 ne concede 30 — funziona solo perche' il turno
   viene preso subito e l'attesa si conta da `pending`, il che rende ogni intoppo un
   turno perso.

11. **Approvare una condizione nominata non la fa comparire.** Trovato scrivendo le prove
   di D121. L'impronta che fa da chiave alla cache della semantica (**D39**, la chiave
   che permette di riusare un catalogo solo fra utenti con gli stessi permessi) guarda
   gruppi, societa', lingua e stato d'accesso dei modelli — **non le voci approvate del
   dizionario** (**D108**). Chi approva una categoria non la vede finche' la cache non
   decade da sola, e non c'e' niente che glielo dica. Nelle prove si aggira svuotando la
   cache a mano, che e' esattamente il segno che il prodotto non lo fa. Va deliberata la
   forma: mettere le voci nell'impronta, oppure svuotare la cache quando una voce viene
   scritta.

12. **La fase B e' la parte cara, e chiede la cosa piu' facile.** Misurato con
   **D123** (`00` §32.1) su un turno vero: fase A 0,054 s, **fase B 113,4 s**,
   fase C 0,249 s, interpretazione 33,6 s, esecuzione su Odoo 0,031 s. La fase B
   chiede *di quale entita' si parla* e costa piu' del triplo dell'interpretazione
   completa. Due strade, e adesso c'e' il numero per scegliere: **allargare la
   fase A** perche' la B serva piu' di rado (il dizionario non ha riconosciuto
   «lead»: e' una voce mancante, non un limite del metodo), oppure **un modello
   piccolo per la sola fase B**, che e' un compito da modello piccolo. Legata al
   punto 5: finche' L4 concede 30 secondi e una risposta ne richiede 150, il
   margine sta tutto nel fatto che il turno viene preso subito.

13. **Il ramo dell'ancora nulla non ha una risposta.** **D110** (`00` §21.1) dice che
   quando un'entita' non espone nessuna data il fatto si dichiara. Il prompt dice di
   rispondere con un chiarimento, ma un chiarimento vuole 2-4 opzioni e ognuna almeno
   un'operazione (`nli_core/contract/schema.py`), e senza date non ce ne sono. Serve una
   decisione numerata: probabilmente una voce nel vocabolario degli scope, che e'
   contratto.

   **Niente lo esercita**: il generatore costruisce condizioni temporali solo per
   entita' che hanno campi data, quindi le entita' senza date non ricevono mai un
   periodo.

14. **Le parole di `nli_web` non si traducono sul cron.** `_()` capisce la lingua
   guardando chi l'ha chiamata: dentro una richiesta web funziona, ma **il turno si
   interpreta sul cron** e li' la richiesta non c'e'. La frase esce non tradotta, in
   silenzio. Le lambda di modulo in `nli_interpretation.py` (21 righe su 33) e la
   funzione annidata in `nli_perimeter.py`. Tre strade: `self.env._()`, `LazyGettext`,
   o costruire le formule dentro il metodo. Va deliberata: e' la forma dello strato
   delle parole.

15. **D27**: eseguire il banco di prova sui worker prefork (`./manage.sh loadtest <db>`,
   **non su `nli_test`**) e riportare i numeri per quello che sono.

16. **La conservazione delle frasi.** **D115** (`00` §23) tiene l'enunciato in chiaro sul
   turno: non c'e' scadenza ne' cancellazione automatica, e
   `08-sicurezza-conformita.md` descrive un sistema che non le conservava. Va riletto
   con questa decisione in mano.

17. **Il profilo e' in servizio senza qualificazione** (`00` §25). Prima del primo utente
    vero, **D51** va eseguita davvero e la sezione aggiornata con l'esito.

18. Il confronto con `granite4.1:8b`, se serve rispondere a *«il resto e' del compito o
    del modello?»*. Riga di comando identica, cambia solo `--profilo`.

# Cosa NON va fatto

Continuare a limare il prompt contro il corpus sintetico. Il corpus non è sigillabile
(D86) e negli ultimi giri ha prodotto frasi genuinamente ambigue e attese sbagliate.
Ogni punto strappato da qui in avanti rischia di essere prompt adattato al generatore,
che è la degradazione descritta da D42.

# Se vuoi solo ripartire senza rileggere tutto

Riprendi il progetto AIDA: leggi ai/00-registro-decisioni.md e
ai/12-piano-implementazione.md, **poi le sezioni «Stato al 5 agosto 2026 (sera)»,
«Stato al 7 agosto 2026» e «Stato all'8 agosto 2026» qui sopra: sono le piu' recenti e
contraddicono in piu' punti tutte quelle prima**. Verifica
con ./manage.sh check, poi vai con «Da dove si riprende», in fondo a quella sezione —
oppure con quello che ti indico.

**Prima di misurare qualunque cosa**, controlla che Ollama serva 8192 token di context:
`curl -s http://127.0.0.1:11434/api/ps | grep context_length`. Se dice 4096, il prompt
arriva tagliato e il prodotto risponde `not_understood` a quasi tutto, senza che niente
lo segnali. Si riavvia Ollama.

**In una riga: la misura c'e', e dice 39 frasi su 54.** Quel numero e' arrivato in una
sera da 25, riparando due cose che non erano il modello — un context servito piu'
stretto di quello dichiarato, e un controllo sulle date che chiedeva la parola giusta
nel posto sbagliato.

**Due frasi di luglio e del 4 agosto sono da considerare superate**: che *«il catalogo
intero da 60 attributi affoga il modello»* — misurato su un prompt tagliato, e con i due
numeri allineati il catalogo intero e' l'unico che permette di rispondere alle frasi con
condizioni; e che la selezione degli attributi sia il primo lavoro in lista. Puo' restare
utile per il costo del prompt, ma la premessa da cui nasceva va rimisurata.

**Il fine tuning non e' piu' solo specificato: il `dataset` esiste.** `ai/18` decide la
modalita', `ai/19` sceglie il modello, `ai/21` e' la ricetta, e dal 7 agosto
`tools/finetuning/` contiene il generatore, 10 000 esempi riproducibili, le tre ricette e
`corri.sh`. Manca **solo la corsa**, e prima di lanciarla vanno riletti i tre cancelli di
`ai/21` §1 — in particolare la linea di partenza: quella che c'e' (39/54) e' del 6 agosto
e **precede D144**, quindi misurerebbe il modello addestrato contro un prodotto che nel
frattempo e' cambiato.

**L'8 agosto il dataset e' stato rifatto, e non per rifinirlo.** Insegnava a citare
frammenti che nella frase non c'erano (13,6%), parlava con una cornice sola per
operazione, dava a ogni attributo un termine solo e serviva cataloghi grandi la meta' di
quelli veri. Tutto misurato, tutto riparato, tutto verificato da 17 prove nuove dentro
`./manage.sh check`. **Il dataset in `data/` va rigenerato prima di usarlo** se qualcuno
ha una copia precedente all'8 agosto:
`python3 tools/finetuning/genera_dataset.py --genera 40000 --bersaglio 10000`.

E **misura l'addestrato due volte**, non una: la batteria sul campo (54 frasi nostre) e
il corpus (1 200 domande scritte da un altro generatore, base al 75,8%). Se sale la prima
e non la seconda, il modello ha imparato il nostro modo di dire le cose, non il mestiere.

E leggi `00` §38 prima di
dichiarare finita qualunque cosa. Stesse regole di prima: deliberi tu le questioni che emergono e le
registri in ai/00, e mi spieghi le cose in modo semplice — come a un ragazzino sveglio ma
inesperto, con le parole chiave tecniche in inglese (`envelope`, `context`, `token`).

---

# Stato al 6 agosto 2026 — i periodi che una frase nomina

*Sessione partita per committare il lavoro della sera prima e fare P0. Fatti tutti e
due, piu' cinque prove che leggevano il database invece di costruirlo.*

## 1. La suite era verde su una base e rossa sull'altra

`./manage.sh test db` diceva **2 falliti e 3 errori**; su `nli_test`, zero. Non era il
codice: erano cinque prove che davano per buono lo stato del database.

* due presumevano *«nessun profilo attivo su questa base»* — vero su una base di prova,
  falso su quella dove il prodotto gira, che un profilo attivo ce l'ha per definizione;
* tre facevano leggere a un amministratore il turno di **un altro utente**. La regola
  dei record lo vieta — un turno lo legge chi l'ha fatto, e vale anche per chi
  amministra — e passavano solo dove `base.group_system` non si porta dietro
  `base.group_user`, che dipende dai moduli installati.

Corrette costruendosi lo stato invece di leggerlo, piu' **la prova che mancava**: un
amministratore che legge il turno di un altro riceve `AccessError`. **258 test Odoo,
verdi su tutte e due le basi.**

## 2. P0 — i periodi nominati (D141, `00` §46)

Sonda di sei frasi sul prodotto vero, prima di toccare niente:

    «nel primo trimestre»  -> 1 lug - 30 set   il TERZO trimestre, 26 record
    «a gennaio»            -> 1 - 31 ago       agosto, 0 record
    «nel 2025»             -> tutto il 2026    39 record
    «a marzo 2026»         -> 1 - 31 ago       agosto, e l'anno l'aveva detto l'utente
    «nel secondo semestre» -> not_understood   l'unica onesta
    «questo trimestre»     -> 1 lug - 30 set   giusta

**Quattro risposte sbagliate su sei.** La causa non era il modello: il vocabolario non
aveva modo di dire *«il primo»*, e il prompt vieta al modello di calcolare date. Entrano
quattro simboli — `month_of_year`, `quarter_of_year`, `half_of_year`, `year_of` — tutti
sull'anno **fiscale** come `current_year`. Dopo: le quattro frasi giuste **3 giri su 3**,
le altre due invariate.

## 3. Le due cose che questa sessione insegna

**Una riga aggiunta a un prompt non aggiunge soltanto.** La prima stesura ha fatto
smettere di funzionare *«i lead creati questo trimestre»*, che rispondeva da sempre: il
modello ha iniziato a mettere il periodo su `Data apertura`. Prova controfattuale col
prompt vecchio, 3/3 su `Data creazione` — **era il prompt, non il modello**. Un prompt e'
un testo che il modello legge intero, e una regola nuova compete con quelle vicine: si
misura **anche sulle frasi che gia' funzionavano**.

**Un mattone nuovo si usa anche dove non va.** *«Nel secondo semestre»* era un rifiuto
onesto; appena il modello ha avuto i trimestri, l'ha risposta col secondo **trimestre**,
3/3, malgrado una riga di prompt che glielo vietava per nome. Per questo `half_of_year`
e' entrato lo stesso giorno. Bimestri e quadrimestri restano la stessa forma di rischio:
e' **P0b**, la rete di `00` §46.7.

## 4. Cosa e' cambiato su disco

Sei commit: l'ancora del tempo, le etichette del dizionario, il comando `dizionario`, la
batteria riparata, i pacchetti lingua, le cinque prove, e D141. **Verifiche: 534 test in
zona pura, 258 Odoo, 51 dei confini, corpus 918/918 con copertura al 100%.**

---

# Stato al 7 agosto 2026 — il dataset esiste, e non e' ancora costato un dollaro

*Sessione partita dalla ricetta scritta la sera prima (`ai/21`) e arrivata al `dataset`
vero: 10 000 esempi, le tre ricette per la macchina affittata, e lo script che le
esegue. **Tutto quello che sta prima della GPU e' fatto. La GPU non e' ancora stata
accesa.***

## 1. Cosa c'e' su disco che ieri non c'era

| file | cos'e' |
|---|---|
| `tools/finetuning/genera_dataset.py` | il generatore: **D143** (la decisione per cui il dataset si sovra-genera 4:1 e poi si sceglie per copertura, non per quota) tradotta in codice |
| `data/copertura.txt` | il rapporto che dice **cosa manca**, e che si legge prima di spendere |
| `tools/finetuning/ricette/aida-{2b,4b,9b}-lora.yml` | le tre configurazioni Axolotl, una per candidato |
| `tools/finetuning/corri.sh` | la corsa intera sulla macchina affittata: `fumo`, `4b`, `2b`, `9b` |

**Un solo `dataset` per tutti e tre i candidati.** Niente in un esempio dipende dalla
taglia del modello — il catalogo, la frase, l'`envelope` e le due forme del `prompt` di
**D142** (la decisione per cui il messaggio di sistema si sposta dentro i pesi, e il
`prompt` cala del 58%) sono le stesse — e le tre Qwen 3.5 condividono il tokenizzatore e
lo schema di conversazione (`ai/19` §5). E' la ragione per cui **provare 2B e 4B non
raddoppia il lavoro: raddoppia solo il conto della macchina**.

## 2. I numeri del dataset

    generati            40 000
    scelti              10 000   (addestramento + validazione)
    tenuti fuori         2 518   applicazioni intere mai viste
    copertura satura a     295   esempi

    simboli del vocabolario chiuso, minimo 50 per simbolo
      op 22/22   tempo 22/22   kind 6/6   aggregazione 6/6   nota_portata 5/5

    ampiezza   287 entita' su 328,  57 applicazioni (6 tenute fuori)

**«Satura a 295» non e' un tetto, e' un pavimento.** E' il punto oltre il quale nessun
esempio porta una **forma** nuova — una combinazione di entita', simbolo, lingua e
famiglia mai vista. Sotto quel numero il dataset ha buchi ed e' un difetto. Sopra, gli
esempi comprano varieta' di **superficie** — quante condizioni, con che parole — che e'
cio' di cui un modello di lingua vive e che quel numero non misura apposta.

**La saturazione ora conta anche le coppie** (simbolo × lingua, simbolo × famiglia).
Con le sole celle singole saturava intorno al numero delle entita' qualunque cosa il
dataset contenesse: un numero che sembrava dire una cosa e ne diceva un'altra.

## 3. La famiglia che nessuna misura vede: il secondo turno

Il rapporto al primo giro diceva **op 7 su 22**: mancavano *tutte* le operazioni del
raffinamento. E' la stessa cecita' di §11 — la batteria apre una conversazione nuova per
ogni frase, e il 5 agosto un difetto che uccideva ogni conversazione **dalla seconda
battuta in poi** ha attraversato tutte le misure senza lasciare traccia. Ora **22 su 22**.

**La trappola, ed e' istruttiva.** Lo stato che la conduttura manda al modello **non ha i
frammenti**: `strip_provenance` li toglie quando lo stato si salva, finche' **D54** (la
decisione che pseudonimizzera' le parole dell'utente prima di conservarle) non e' fatta.
Un esempio con le provenienze dentro insegnerebbe a lavorare con un'informazione che in
servizio **non arriva mai**. Verificato invece che sperato: 538 esempi di secondo turno,
**zero** stati con i frammenti.

`strip_provenance` si e' spostata da `nli_core/models/nli_interrogation.py` a
`nli_core/contract/state.py`: e' una funzione pura su uno stato, e il posto delle
funzioni sullo stato e' il contratto. C'e' voluto un **secondo** chiamante in zona pura
per accorgersene. Riesportata da dov'era — spostare una funzione non deve rompere chi la
usava.

E tre difetti trovati **misurando invece che indovinando**: `add_field` su uno stato
senza colonne e' rifiutato dall'applicatore e ha ragione (chi sceglie da zero dice
`set_fields`); `reset` da solo lascia uno stato senza bersaglio; e il frammento di un
confronto ometteva il verso — *«importo 5000»* invece di *«importo sotto 5000»*. Quel
terzo e' il piu' grave: **il frammento e' la provenienza**, e D105/D119/D144 ci
verificano sopra. Insegnare a citare male sarebbe insegnare cio' che le reti poi fermano.

## 4. Quattro difetti che si vedono solo alla scala vera

Il generatore girava bene su 4 000 esempi. A 40 000 ha mostrato quattro cose:

1. **Il 25% degli esempi aveva un SEGNAPOSTO al posto del messaggio di sistema.** Ora la
   forma lunga di D142 e' quella che `prompt.system_message()` produce, **presa dal
   prodotto**: una copia scritta a mano divergerebbe alla prima delibera che tocca il
   vocabolario, e insegnerebbe a leggere un messaggio che nessuno manda.
2. **Il minimo di cinquanta esempi per simbolo era misurato e non fatto rispettare.** Il
   rapporto si limitava a dire «sotto 50: `add_field`, `clear_fields`, …» giro dopo giro.
   D143 lo chiama una garanzia: ora la selezione **ripiana i simboli scoperti** prima di
   riempire a volume. L'avidita' da sola non bastava — la copertura si accontenta della
   **prima** volta che vede un simbolo, e coprire non e' imparare.
3. **Esempi oltre la finestra**: il massimo era 15 799 `token` contro un `sequence_len`
   di 6 144. Ora si scartano e si contano, perche' un esempio troncato non insegna una
   risposta piu' corta: insegna **una risposta che finisce a meta'**.
4. **La selezione avida scandiva tutto il serbatoio anche dopo la saturazione**: ore per
   prendere lo stesso esempio che prenderebbe il primo che passa. Ora quaranta mila
   generati e selezionati in **quindici secondi**.

## 5. Due numeri che correggono `ai/18` §8

**La lunghezza vera di un esempio**: mediana **3 044 `token`**, 90° percentile 3 690,
99° **4 658**, massimo 6 075 — non i ~4 200 di media che `18` assumeva.

**Il costo di una passata**: **12,4 milioni di `token`** con la quota corta di D142,
contro i 42 milioni preventivati. **La corsa costa circa un terzo di quanto scritto.**

## 6. La ricetta del 9B, e l'unica differenza che non e' una riga di comodo

`ai/18` §3 conta 25-30 GB per una LoRA a 16 bit sul 9B, ma quel conto assume 4-5 mila
`token`. A **6 144** con due esempi per lotto le attivazioni crescono e una A6000 da
48 GB va stretta. **Un esempio per lotto e il doppio di accumulo** tengono il lotto
efficace a 32 — che e' cio' che conta per il gradiente — e si paga in **tempo**, non in
qualita'.

E `corri.sh` stampava `FROM qwen3.5:4b` anche per il 2B e il 9B. La base ora la dichiara
la ricetta: **un adapter attaccato alla taglia sbagliata e' un guasto che non si
annuncia** — il modello parte, risponde, e sbaglia in modo plausibile.

## 7. Cosa NON e' stato fatto, ed e' il prossimo passo vero

- **Nessuna corsa e' stata eseguita.** Zero dollari spesi. Il primo passo e'
  `corri.sh fumo`: 500 esempi su A6000, ~$2, e non misura la copertura — verifica che la
  catena intera giri (dataset → Axolotl → adapter → GGUF → `ollama`).
- **I tre cancelli di `ai/21` §1 vanno riletti prima**, non dopo: il contratto dev'essere
  fermo, la **linea di partenza dev'essere fresca** (oggi e' 39/54 del 6 agosto, ed e'
  precedente a D144), e il catalogo servito dev'essere quello vero.
- Il rapporto di copertura **si legge prima di spendere**, ed e' `corri.sh` stesso a
  stamparlo per primo.

## 8. Cosa e' cambiato su disco

Quattro commit: il generatore, la famiglia dei raffinamenti, il dataset vero con le
ricette e la corsa, la ricetta del 9B. **Nessuna decisione nuova nel registro**: la
sessione e' l'esecuzione di D142 e D143, gia' deliberate in `00` §47.

**Verifiche: 572 test in zona pura** (erano 568), **263 Odoo**, `./manage.sh check`
verde.

---

# Stato all'8 agosto 2026 — il dataset citava frasi che non aveva detto

*Sessione partita da una domanda semplice — «questo dataset basta per arrivare al 95%?»
— e finita con un difetto che nessuno cercava. La risposta alla domanda e' **no**, ed e'
scritta in §1. Il difetto e' in §2, e vale piu' della risposta.*

## 1. La risposta alla domanda: no, e perche'

Il `dataset` del 7 agosto insegnava la **grammatica** del contratto, non la **lingua**
degli utenti. Analogia: e' un cameriere che conosce tutti i piatti e sa scrivere una
comanda, ma ha sentito i clienti ordinare sempre con le stesse sette frasi. Il primo che
dice *«mi porti i cinque piu' cari»* invece di *«fammi vedere X ordinati per prezzo solo
i primi 5»* lo spiazza.

Quattro misure, tutte sul dataset vero:

| | 7 agosto |
|---|---|
| cornici per operazione (modi di dire la stessa cosa) | `add_order` **2** su 1 081 esempi, `add_field` **1** su 50, `remove_group` **1** su 50 |
| quota delle 4 aperture piu' comuni | **51%** |
| termini per attributo | **1**, su tutti e 123 363 |
| mediana degli attributi per catalogo | **9**, contro i 27-60 che il prodotto serve |

L'ordine delle parole era **fisso**: entita' -> condizioni -> misure -> gruppi ->
ordinamento -> campi -> limite, in tutti e 9 500 gli esempi. Mai un'inversione, mai
un'ellissi, mai un preambolo.

**Il generatore lo diceva gia' di se'**, nel docstring di `verbalizza`: *«una frase un
po' piu' piatta... La ricchezza la portano le 918 frasi del corpus e — soprattutto — gli
enunciati veri di D85, che nessun generatore sostituisce»*. Era vero, ed e' rimasto vero.

## 2. Il difetto che la domanda ha fatto emergere

**Il 13,56% delle provenienze citava parole che nella frase non c'erano** — 2 484 su
18 316.

    [set_target]  provenienza='dipendenti'           frase='vorrei vedere dipendente ...'
    [set_fields]  provenienza='mostrami anche X e Y' frase='... con X e Y'

Causa: `envelope_di` e `verbalizza` chiamavano `_detto()` **due volte in modo
indipendente**. Due sorteggi sullo stesso elenco di sinonimi, due parole diverse.

**Perche' conta piu' di tutto il resto.** §10.3 definisce la provenienza come *il
frammento della frase che ha prodotto l'operazione*, e **D105** (una condizione nominata
non fondata nel proprio frammento e' rifiutata), **D119** e **D144** ci verificano sopra
in servizio. Un dataset con provenienze inventate insegna al modello a produrre
esattamente cio' che le tre reti bocciano: **il prodotto rifiuterebbe la risposta che
l'addestramento gli ha insegnato a dare**.

**Perche' era invisibile.** Finche' ogni attributo aveva **un termine solo**, due
sorteggi dallo stesso elenco davano sempre la stessa parola. Il difetto era gia' scritto
e aspettava i sinonimi per manifestarsi — cioe' proprio il lavoro che stavamo per fare.
Aggiungere i sinonimi senza accorgersene lo avrebbe portato dal 13% a oltre il 40%.

E' la stessa famiglia di §38 (codice dichiarato, provato e non collegato) e di §46: **una
cosa che funziona per un motivo che non e' quello per cui dovrebbe funzionare**.

## 3. Cosa e' cambiato, e di quanto

| | 7 agosto | 8 agosto |
|---|---|---|
| **provenienze scollegate** | **2 484 / 18 316 = 13,6%** | **0 / 18 526** |
| mediana attributi per catalogo | 9 | **13** |
| esempi con >= 27 attributi | 11% | **21%** |
| esempi con <= 10 attributi | 61% | **42%** |
| termini per attributo | `{1: 123363}` | `{1: 134008, 2: 25969, 3: 2183, 4: 1139}` |
| parole distinte nelle frasi | 3 016 | 3 235 |
| quota delle 4 aperture piu' comuni | 51% | **20%** |
| cornici per operazione, la piu' povera | 1 | **5** |

Ampiezza tenuta: **287 entita' su 328**, entita' piu' rappresentata allo **0,76%** contro
il tetto dell'1,5% di **D143** (il dataset si sovra-genera 4:1 e si sceglie per copertura).
Copertura invariata: op 22/22, tempo 22/22, kind 6/6, aggregazione 6/6, nota_portata 5/5.

### Le quattro riparazioni

**La `Dizione`** — le parole di un esempio si scelgono **una volta sola**, e la frase e
l'envelope le leggono. Il frammento **e'** il pezzo di frase: non gli somiglia, e' lo
stesso oggetto. E una rete in §6, `provenienze_scollegate`, rifiuta l'esempio se una
provenienza non e' contenuta nella frase — perche' e' la riparazione a poter tornare
indietro, non il difetto.

**Le cornici** — da una a cinque o piu' per operazione, piu' l'ordine delle parole libero
nel 40% degli esempi e il limite in testa nel 25% (*«mostrami i primi 5 clienti ordinati
per fatturato»*, che prima era impossibile). Costa **zero**: nessun esempio in piu',
nessun `token` in piu' per passata. Si moltiplicano i modi di dire, non le cose dette.

**I sinonimi meccanici** — le due trasformazioni che non inventano niente: la
punteggiatura (`E-mail` -> `email`, `e mail`) e la parola di servizio (`Data creazione`
-> `data di creazione`). Con una guardia contro le collisioni: una variante che coincide
col termine di un altro attributo dello stesso catalogo non e' un sinonimo, e' un'
ambiguita'. Nel 50% dei casi la variante entra **anche** nel catalogo mostrato, nell'altro
50% resta solo nella frase — e li' il modello deve fare il ponte da solo, che e' il
compito vero.

**La taglia del catalogo** — quattro fasce pesate invece del sorteggio uniforme, piu' il
peso sulla taglia dell'entita' (radice quadrata: rapporto 3 a 1 fra la piu' grande e la
piu' piccola).

## 4. Cio' che non e' arrivato dove doveva, detto com'e'

**La mediana degli attributi e' 13, non i 25-30 che avevo indicato.** Il tetto non e' il
campionatore, e' l'atlante: solo il **26%** delle entita' Odoo ha almeno 27 attributi, e
la mediana per entita' e' 12. Per fare cataloghi grandi avrei dovuto usare sempre le
stesse otto tabelle grosse, e allora il modello avrebbe imparato **quelle otto** invece
del mestiere — cioe' rotto l'ampiezza che D143 protegge.

Meglio un libro un po' facile ma vario che uno difficile e ripetitivo. Ma **21% contro i
27-60 che il prodotto serve resta un divario reale**, e per chiuderlo serve un atlante
diverso, non un campionatore diverso.

**E i sinonimi veri non ci sono.** Le regole meccaniche arrivano da `E-mail` a `email`,
non da `E-mail` a `posta` — `creat` e `creazion` sono radici diverse, e nessuna regola ci
arriva. Quelli sono **D108** (il registro delle voci approvate del dizionario), sono
mezza giornata di lavoro a mano, e sono **P4b**: la cosa rimasta che sposta di piu' il
risultato sulle domande vere.

## 5. Le prove, che non esistevano

`genera_dataset.py` non aveva **nessuna verifica automatica**. Ora ha
`tools/finetuning/tests/test_generatore.py`: **17 prove**, dentro `./manage.sh check`.
Ogni controllo ne ha una che lo mostra **scattare** e una che lo mostra **non scattare** —
un controllo visto solo passare non e' un controllo, e' una decorazione.

**E hanno subito preso due cose che l'occhio non aveva visto:**

1. **Il mio controllo passava a vuoto.** Confrontavo per sottostringa senza spazi di
   guardia, quindi `mail` risultava contenuto in `email`: il controllo mentiva proprio
   sui casi che doveva prendere.
2. **Enum impronunciabili.** Tre esempi su 40 000 avevano per valore l'operatore `<` o
   `>`, e producevano *«cerca regole prezzo di consegna >»*. Corretto **alla fonte**
   secondo **D85** (si corregge il generatore, non i suoi prodotti), non lasciato allo
   scarto.

E la prima prova a volume ridotto ha mostrato due difetti di lingua che nessuna misura
avrebbe preso: *«transazione della di pagamento»* (preposizione doppia su un'etichetta
che ne aveva gia' una) e *«Work of Order»* (la regola italiana applicata all'inglese).
Ora `di` e' l'unica preposizione italiana ammessa — le altre chiedono genere e numero,
che su 333 entita' non sappiamo — e l'inglese non ne prende nessuna.

## 6. La cosa che credevamo mancasse, e c'e' gia'

Avevo scritto che manca **un esame scritto da qualcun altro**, e che senza quello il 95%
non e' verificabile. La prima meta' e' sbagliata: **l'esame esiste**.

E' il **corpus fondativo** — 1 200 casi in `ai/corpus/`, scritti da un generatore
**diverso**, con un lessico compilato a mano. Parla un'altra lingua:

| il dataset dice | il corpus dice |
|---|---|
| *«fammi vedere contatti con Citta' uguale a Roma»* | *«estrai anagrafiche clienti operativi raggruppati per comune»* |
| *«mostrami prodotti con quantita' sopra 5000»* | *«dammi articoli con giacenza almeno 5000 attivi»* |
| *«voglio vedere ordini»* | *«tirami fuori prelievi da consegnare»* |

`anagrafiche clienti`, `giacenza`, `prelievi`, `comune`: parole d'ufficio, non etichette
Odoo. Ci sono perfino i refusi voluti (`cleinti`). E il modello base ci fa **75,8%**
(misura del 4 agosto), quindi il confronto e' gia' apparecchiato.

Resta vero che il corpus e' **sintetico** — **D86** lo dichiara e per questo non e'
sigillabile — e che copre 8 entita' contro le 287 del dataset. Non sostituisce D85. Ma
come secondo esame, indipendente dal generatore che ha scritto il libro di studio, e'
molto meglio di niente ed e' **gia' pagato**.

## 7. Il 95%, e cosa mi aspetto davvero

Il numero non ha una misura sotto: e' un desiderio, non una previsione. I fatti sono
39/54 (72%) sulla batteria, **prima di D144**, e 75,8% sul corpus col modello base.

Previsione, da misurare e non da credere:

| esame | previsione | vale? |
|---|---|---|
| `aida_test_mai_viste` (applicazioni nuove, frasi nostre) | 90-96% | **no** — misura lo schema, non la lingua |
| batteria sul campo, 54 frasi | 45-48 su 54 (83-89%) | in parte |
| corpus, 1 200 casi con parole d'ufficio | **e' quello che risponde alla domanda** | si' |

**Il 95% su domande di un cliente vero non lo vedo**, e preferisco scriverlo prima di
spendere invece che dopo.

## 8. Cosa e' cambiato su disco

- `tools/finetuning/genera_dataset.py` — `Dizione`, `CORNICI`, `RAFFINAMENTI_DETTI`,
  `varianti_meccaniche`, `FASCE_CATALOGO`, peso sulla taglia dell'entita', e la rete
  `provenienze_scollegate` in §6
- `tools/finetuning/tests/` — **nuovo**, 17 prove
- `manage.sh` — le prove del generatore entrano in `check`
- `data/*.jsonl` e `data/copertura.txt` — rigenerati (i `.jsonl` non sono in git: si
  rigenerano con `--genera 40000 --bersaglio 10000`)

**Nessuna decisione nuova nel registro.** Le riparazioni applicano D105, D143 e D85 a
codice che gia' avrebbe dovuto rispettarli; la sola cosa che potrebbe meritare una
delibera e' la quota 50/50 fra varianti dentro e fuori dal catalogo, e per ora e' una
costante dichiarata nel generatore con la sua argomentazione.

**Verifiche: 51 + 17 + 572 test, `./manage.sh check` verde.**

## 9. Da dove si riprende

1. **Committare**: il codice e il dataset rigenerato non sono ancora commessi.
2. **Rifare la linea di partenza** — `./manage.sh campo db`. Senza, dopo la corsa non si
   sapra' se il movimento viene dal fine tuning o da D144. E' pesarsi dopo la dieta
   usando la foto dell'anno scorso.
3. **`corri.sh fumo`** (~$2): non misura niente, verifica che i tubi siano collegati.
4. **P4b, D108** — mezza giornata di sinonimi a mano, prima delle corse vere. E' l'unica
   cosa rimasta che sposta il risultato sulle domande vere, e costa meno di una corsa
   sbagliata.
5. Poi **4B e 2B**, e le **due** misure di P5c.

# Stato al 21 agosto 2026 — l'entita' che nessuno aveva nominato

*Sessione partita da una domanda dell'Architect — «perche' questa frase non funziona?»
— con una traccia incollata in chat. La risposta e' in §2. Ma la prima cosa trovata non
era nel prodotto: era sotto, ed e' §1.*

## 1. Il context servito era 4096, e il rimedio scritto qui era sbagliato

Primo controllo della sessione, quello che `restart` dice di fare per primo:

    curl -s http://127.0.0.1:11434/api/ps | grep context_length   ->  4096

La riga che stava qui diceva di riavviare l'applicazione dopo un `launchctl setenv`.
**Non funziona**, e l'ho verificato leggendo l'ambiente del processo vero (`ps eww`):
Ollama.app avvia `ollama serve` con un ambiente suo, dentro c'erano `OLLAMA_MODELS` e
`OLLAMA_NO_CLOUD` e **non** `OLLAMA_CONTEXT_LENGTH`. Ho provato anche l'impostazione nel
database dell'applicazione (`settings.context_length`, portata a 8192): vale per la sua
chat, `/api/ps` continuava a dire 4096. L'unico modo verificato e' avviare il server a
mano con la variabile nel suo ambiente. La sezione dei fatti d'ambiente e' corretta.

**Quanto costava.** Il turno che l'Architect ha portato riportava `prompt_tokens: 2050`,
che non e' la misura del prompt: e' **la firma del taglio**, documentata da tre settimane
in `pipeline.py:360`. La stessa domanda, con il server a 8192, ne riporta **4388**. Il
prompt arrivava al modello tagliato a meta' del catalogo, e nessun controllo diceva
niente — il prodotto rispondeva `not_understood`, che assomiglia a un limite del modello.
**Il valore dichiarato dal profilo non e' una prova di niente: la prova e' `/api/ps`.**

## 2. La frase, e i due difetti sotto

    dammi il numero di lead creati quest'anno        -> operations, 39 record
    mostrami le vendite con totale superiore a 2000  -> not_understood, 67,7 s

La seconda **nomina il proprio soggetto**, e ha ricevuto il catalogo dei lead. Traccia:

    phase_a  {"resolved": false, "entity": null, "known": "crm_lead"}
    phase_c  {"entity": "crm_lead", "attributes": 60}

*Vendite* non era fra i nomi di `sale_order`, e la raccolta di **D126** non poteva
trovarla: il menu radice *Vendite* non ha azione e sotto porta a quattro modelli diversi.
Guardando l'installazione quella parola non ha **una** risposta; una persona invece lo sa.

Ma il difetto vero non era la parola: era che **la fase B, che esiste apposta per questo
caso, era irraggiungibile** appena una conversazione aveva un bersaglio. Tutto in
`00` §49: **D145** (un raffinamento che non si capisce si ricrede, una volta sola),
**V-D93-2** (una parola dentro il nome di un attributo non nomina un'entita' — l'ha presa
una prova prima del prodotto, quando *«i lead per addetto vendite»* ha smesso di
risolvere), **D146** (l'entita' ereditata si dichiara dedotta).

**§49.4 e' la parte che conta di piu'.** D145 si attacca a `not_understood`, cioe' a un
fallimento visibile. Misurato lo stesso giorno: *«mostrami le anagrafiche di Roma»*, dopo
una domanda sui lead, risponde **un record di lead** — il modello ce l'ha fatta a leggere
la frase sul catalogo sbagliato, i lead una citta' ce l'hanno, e non c'e' nessun rifiuto a
cui attaccare una seconda lettura. E' **D29**, ed e' la meta' pericolosa della classe. D146
non la ripara: la rende **leggibile**, ed e' il massimo che si possa fare per una parola
che il dizionario non ha ancora.

## 3. La linea di partenza, e cosa dice davvero

**47 su 59 (79,7%)**, zero saltati, ambiente verificato a 8192. Rifatta dopo le tre
delibere: **identica**, famiglia per famiglia. Con un modello non deterministico due giri
uguali sono di per se' un segnale.

| famiglia | |
|---|---|
| intenti | 11/18 — 61,1% |
| operatori | 11/12 — 91,7% |
| date | 23/24 — 95,8% |
| limiti | 2/5 — 40,0% |

**Non confrontabile con il 39/54 del 6 agosto**: la popolazione e' cambiata (59 casi
contro 54). Questa e' la linea buona — e' posteriore a D144, e serve due volte: per il
fine tuning (P5b) e come metro del lavoro sulle aggregazioni.

**I 12 fallimenti, per causa** — ed e' il numero che riordina la lista:

| causa | quanti |
|---|---|
| **aggregazioni non costruite** | **8** |
| rifiuti mancati (risponde a cio' che non sa esprimere) | 2 |
| buchi gia' dichiarati (`inizia per`, HAVING) | 2 |
| **lessicali** | **0** |

I due rifiuti mancati sono i piu' gravi perche' non si vedono: *«i secondi 20 lead»*
risponde **39 record** invece di rifiutare, *«i lead che non sono di milano»* risponde
invece di rifiutare. Un buco dichiarato che non rifiuta e' una risposta sbagliata con
l'aria di essere giusta.

## 4. I sinonimi: il meccanismo si', le parole no

Avevo scritto che i sinonimi erano la leva piu' corta (P4b). **La misura dice di no**, e
la lista va riordinata.

Passate alla fase A le **45 frasi distinte** che il prodotto ha davvero ricevuto: 36
riconosciute, e le altre 9 — *«solo quelli vinti»*, *«ordinameli per email»*, *«Data
creazione»* — non nominano nessuna entita', cioe' sono raffinamenti, dove la fase A muta
e' il comportamento voluto. **Dopo *vendite*, nessuna frase vera resta senza entita' per
colpa di una parola mancante.**

Quindi: `tools/dizionario/pacchetti.py` (zona pura, 9 prove) organizza le voci per modulo
Odoo, solo L1, caricate se il modulo e' installato, con il **rilevatore di collisioni** —
provato sul percorso vero: *ordini* e *vendite* chiesti per `crm_lead` vengono bloccati e
nominati. E dentro c'e' **una parola sola**, perche' riempirli adesso vorrebbe dire
inventare. Una prova obbliga chi ne aggiunge a portare la propria misura.

**E non si copiano dal corpus fondativo**, per quanto sia allettante: e' l'unico esame
indipendente che abbiamo, e un modello misurato su parole che gli abbiamo insegnato
apposta non e' piu' misurato.

Le stesse voci alimentano il generatore del dataset: entrano nel **catalogo** dell'esempio
italiano, mai nei pesi da sole (`ai/18` §2).

## 4bis. Le aggregazioni: 47 -> 51, e la causa era una riga mancante

`add_measure` **non compariva nella forma della busta del prompt**. Sette operazioni
hanno la loro riga — `set_target`, `add_condition` due volte, `add_group`, `set_fields`,
`add_order`, `set_limit` — e lei no: esisteva solo come parola nell'elenco dei vocabolari
chiusi. Il modello ne conosceva il **nome** e non la **forma**.

Si vedeva nelle buste: su *«quanti lead per stato e per commerciale»* emetteva i due
gruppi e saltava la misura; su *«qual e' il ricavo atteso piu' alto»* restituiva una busta
**vuota**, che diventa `out_of_scope`. Non rifiutava: non sapeva scrivere.

E' la firma di famiglia di questo progetto, la quarta volta in tre settimane: **capacita'
dichiarata nel contratto, ammessa dal validatore, coperta dal generatore del dataset, e
mai insegnata nell'unico posto che il modello legge.** Come `coherence` che non era sul
percorso, come la fase B irraggiungibile.

Riparato con tre cose: la riga della forma, le regole che legano *quanti / somma / media /
piu' alto / piu' basso* alle funzioni, e un secondo esempio svolto dove misura e gruppo
compaiono insieme — perche' il caso che sbagliava di piu' era proprio quello in cui vanno
emesse tutt'e due.

| | prima | dopo |
|---|---|---|
| **totale** | 47/59 — 79,7% | **51/59 — 86,4%** |
| intenti | 11/18 | **14/18** |
| operatori | 11/12 | 11/12 |
| date | 23/24 | **24/24** |
| limiti | 2/5 | 2/5 |

**Nessuna regressione**, e le date sono andate a posto da sole: il prompt non le nomina,
quindi il guadagno viene dal non dover piu' indovinare una forma.

**I quattro che restano in `intenti` non sono quattro difetti.** Due —
*«qual e' il ricavo atteso piu' basso»* e *«il ricavo atteso medio per stato»* — muoiono a
**180,1 s**, cioe' sul tetto di D122: e' latenza, non comprensione, e le domande con misura
sono le piu' lente (*«piu' alto»* passa in 33,4 s, *«per stato e per commerciale»* in 15,0).
Gli altri due chiedono un chiarimento perche' *«di oggi»* non nomina una data e `crm_lead`
ne espone sette senza che D110 ne dichiari una principale: **e' D135 che funziona**, e
probabilmente e' l'attesa della batteria a essere vecchia. Va deciso, non aggiustato di
nascosto.

## 5. Da dove si riprende

1. **Le due domande che vanno in timeout** — 180 s sul tetto di D122, su frasi che il
   modello capisce. E' la latenza delle misure, ed e' cio' che il fine tuning promette
   di togliere (`ai/21` §2.4);
2. **I due rifiuti mancati** — pochi, invisibili, e sono D29;
3. **Le conversazioni nella batteria** (P3c) — oggi tutte e 59 le frasi parlano di
   `crm_lead` e sono tutte prime domande. E' il motivo per cui questa misura non ha
   potuto vedere ne' D145 ne' i sinonimi: non e' piu' «sarebbe utile», ci ha nascosto
   due difetti;
4. **Il controllo sul context servito** — `prompt_tokens` accanto a `context_window` sono
   gia' nella diagnostica e **nessuno fallisce** quando divergono. E' la raccomandazione
   rimasta aperta dal 5 agosto, e oggi ha il suo secondo caso;
5. **Il `LaunchAgent`** per il context: oggi il server gira avviato a mano e muore al
   riavvio del Mac.

**Verifiche della sessione**: pure 574, Odoo 269 (erano 267), generatore 20, pacchetti 9,
corpus 600/696 sulla fase A con **determinazioni sbagliate 0**, copertura 100%.
