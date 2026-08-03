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

1. **Rimisurare tutto, adesso che il catalogo e' intero.** E' il primo perche' senza di
   questo non sappiamo dove siamo: ogni numero che il progetto porta e' stato preso con
   17 attributi su 66. Tre misure, tutte automatizzate, mezza giornata di macchina:

   * **la linea di partenza sul corpus** (`ai/corpus/misura_accuratezza.py`): l'ultima
     e' 70,0% complessiva e 79,5% su `filter`, ed e' di venti delibere fa;
   * **la batteria sul campo per intero** (`./manage.sh campo db`): 54 frasi. Con 60
     attributi le domande su *stato*, *ricavo atteso* e *commerciale* smettono di essere
     saltate;
   * **gli stessi tre candidati di `19`** — `qwen3.5:2b`, `:4b`, `:9b` — con la
     generazione vincolata accesa, che il banco di `19` §2 non aveva.

   **L'attesa scritta prima di misurare**, cosi' che una previsione sbagliata si veda:
   D135 (`00` §40.8) dice che *«mostrami i lead creati quest'anno»* deve finire in una
   domanda con le date invece che in `not_understood`, e il clic deve rispondere in un
   decimo di secondo. E il catalogo intero dovrebbe alzare `filter`, che e' la sezione
   dove mancavano gli attributi.

   **Il modo in cui D135 puo' peggiorare le cose**, da guardare per primo: la regola
   misura se il frammento nomina la data con i termini che il dizionario ha (T1). Se
   `create_date` non ha fra i suoi termini la parola che l'utente usa — *«creati»* —
   allora *«i lead creati quest'anno»* diventa una domanda inutile, perche' la data
   l'utente l'aveva gia' detta. Non e' un difetto della regola: e' una voce mancante, e
   la strada e' **D108**.

2. **Il fine tuning, deciso dall'Architect il 3 agosto.** I due documenti sono scritti e
   sono la specifica: `ai/18` per la modalita' (LoRA a 16 bit, RunPod, ~$40) e `ai/19`
   per il modello (Qwen3.5-4B principale, 2B in parallelo, 9B riserva). Manca il lavoro,
   ed e' in quest'ordine:

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

4. **Non esiste nessuna prova del lato client.** E' il rischio piu' grande aperto, ed e'
   quello che ha prodotto due dei sette difetti di `00` §38: un componente OWL dichiarato
   e non importato ha fatto sparire l'intera chat con 147 prove verdi. Il quinto
   controllo dei confini prende quella sola classe di errore. Serve un banco vero — tour
   Odoo o prove di componente.

5. **La chat non e' mai stata guardata in un browser da chi l'ha scritta.** Le viste di
   risposta (vista lista di Odoo incorporata), il blocco diagnostico, «Come ho letto la
   domanda»: tutto verificato lato server, niente visto girare. Da guardare per primi
   l'altezza del contenitore e due tabelle nella stessa conversazione.

6. **La tabella non ha la paginazione.** Il pannello di controllo e' spento perche'
   `Nuovo` e la barra di ricerca non devono stare in una risposta (`00` §33.6), e con lui
   se n'e' andato il selettore di pagina che `15` chiede. Si riaccende tenendo spente le
   parti di sinistra e destra: una riga, ma dipende da nomi interni di Odoo.

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

   **La misura dopo D113–D120 non e' stata fatta.** L'attesa scritta prima di misurare
   e' in `00` §22.3: complessiva ~75,3%, `filter` ~84,8%, ancora sotto la soglia di
   D44. Se il numero si muove meno, dira' quale ipotesi era sbagliata.

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
ai/12-piano-implementazione.md, verifica con ./manage.sh check, poi vai con il punto 1
degli aperti — **rimisurare tutto adesso che la finestra e' a 8192 e il catalogo e'
intero**: la linea di partenza sul corpus, la batteria sul campo per intero, e i tre
candidati di `19` con la generazione vincolata accesa — oppure con quello che ti indico.

Il punto 2 e' il fine tuning, gia' specificato in `ai/18` e `ai/19`: li' manca il
lavoro, non le decisioni. E leggi `00` §38 prima di
dichiarare finita qualunque cosa. Stesse regole di prima: deliberi tu le questioni che emergono e le
registri in ai/00, e mi spieghi le cose in modo non tecnico.
