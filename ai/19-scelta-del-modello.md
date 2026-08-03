# SCELTA DEL MODELLO — quale, e su che hardware

Documento di decisione per l'Architect. Scritto il 3 agosto 2026.

La domanda: *«`qwen3.5:9b` è la scelta migliore, o ottengo le stesse prestazioni con
qualcosa di molto più leggero? Voglio che giri su hardware privato, a basso costo, ma
che vada bene.»*

**La risposta è misurata, non ricavata da classifiche.** Ho fatto girare cinque modelli
sul MacBook con il **prompt vero** del prodotto — quello che `prompt.system_message()` e
`user_message()` producono per `crm.lead` con il catalogo intero — e ho cronometrato.
Le classifiche pubbliche servono a scegliere chi provare; a decidere serve la macchina
su cui il prodotto girerà.

---

## §1 — Il banco

**Prompt reale**, non un campione: sistema più utente, catalogo di `crm.lead` al tetto
di 60 attributi di **D31**, frase *«mostrami i lead creati quest'anno con ricavo atteso
sopra 5000»*.

    14 763 caratteri  =  4 077 gettoni

    di cui:  regole e vocabolari chiusi   8 585 caratteri  (~2 370 gettoni, il 58%)
             catalogo e frase             6 178 caratteri  (~1 707 gettoni, il 42%)

Macchina: **Apple M1 Pro, 16 GB**, `ollama` nativo, finestra forzata a 8 192 gettoni
perché altrimenti il prompt verrebbe tagliato (§39.5 del registro).

**Un avvertimento onesto sul banco**: questa misura è **senza generazione vincolata**.
In produzione **D101** e **D102** impongono al modello un insieme chiuso di riferimenti
e una griglia sul formato, quindi gli errori di JSON che vedrete qui sotto sono più
gravi di quelli veri. Il banco serve a confrontare **velocità** e **tendenza
all'errore**, non a stimare l'accuratezza del prodotto.

---

## §2 — I numeri, sulla sua macchina

| modello | peso su disco | lettura prompt | scrittura | gettoni scritti | totale | JSON | qualità del contenuto |
|---|---|---|---|---|---|---|---|
| **qwen3.5:2b** | 2,7 GB | **1 087 g/s** | **60,7 g/s** | 1 200 (non si è fermato) | 27,2 s | no | è andato a ruota libera |
| **llama3.2:3b** | 2,0 GB | 513 g/s | 46,2 g/s | 135 | 12,5-22,7 s | sì | struttura giusta, ma ha messo un risolutore di tolleranza che nessuno aveva chiesto |
| **qwen3.5:4b** | 3,4 GB | 417 g/s | 34,9 g/s | 985 | 41,4 s | sì | **valore annidato male**: `value` fuori dalla condizione |
| **granite4.1:8b** | 5,3 GB | 200 g/s | 19,4 g/s | 201 | 34,0 s | no | ha scritto **prosa dopo il JSON**, che il prompt vieta |
| **qwen3.5:9b** | 6,6 GB | 234 g/s | 21,4 g/s | 729 | 57,4 s | sì | **l'unico corretto**: annidamento e tipi giusti |

I tempi hanno una variabilità del 20-40% fra una corsa e l'altra (`llama3.2` ha fatto
12,5 s e 22,7 s sullo stesso caso): è un portatile, scalda, e non è una macchina da
misura. Gli ordini di grandezza però sono solidi.

---

## §3 — Cosa dicono davvero questi numeri

### La lettura del prompt è metà del problema

Solo per **leggere** i 4 077 gettoni del prompt servono da 3,7 secondi (il 2b) a 17,4
secondi (il 9b). Prima di scrivere un carattere.

È la ragione per cui il prodotto oggi risponde in 40-140 secondi, e **non è la
dimensione del modello**: è la lunghezza del prompt moltiplicata per la lentezza della
macchina.

### Due terzi del prompt sono regole che il modello potrebbe avere in testa

Le istruzioni e i vocabolari chiusi occupano **2 370 gettoni, il 58% del prompt**, e
sono **identici a ogni domanda**. Il catalogo — l'unica parte che cambia davvero — ne
occupa 1 707.

Un modello affinato quelle regole le ha nei pesi. Il prompt scende da 4 077 a circa
**1 700 gettoni**, cioè **il 58% in meno**, e la lettura scende in proporzione. Questo è
un guadagno che il fine tuning porta **oltre** all'accuratezza, e da solo vale la
corsa.

### Sono tutti troppo prolissi

Una busta corretta per questa frase sta in **150-250 gettoni**. Ne hanno scritti 729
(il 9b), 985 (il 4b), 1 200 senza fermarsi (il 2b): JSON con rientri, spazi e a volte
commenti. Ogni gettone di troppo è tempo di risposta.

Addestrando su buste **compatte** la scrittura si accorcia di tre-quattro volte. È il
secondo guadagno gratuito del fine tuning.

### Il modello grande vince sulla **struttura**, non sulla comprensione

Tutti e cinque hanno capito la frase. Solo il 9b ha scritto la condizione con
l'annidamento giusto (`"value": {"kind": "number", "value": 5000}`). Il 4b ha messo il
valore fuori dalla condizione; il granite ha aggiunto una spiegazione in prosa dopo il
JSON.

**Sono errori di forma, non di senso.** Ed è esattamente la classe di errore che il fine
tuning corregge meglio: non stiamo insegnando a capire l'italiano — quello lo sanno già
tutti — stiamo insegnando **come si scrive una busta**.

Questo è il fatto centrale del documento: la distanza fra il 4b e il 9b è quasi tutta
distanza di formato, e il formato è ciò che una LoRA sistema in una corsa da undici
dollari.

---

## §4 — Il panorama: chi sono i candidati

| famiglia | taglie piccole | licenza | note |
|---|---|---|---|
| **Qwen 3.5** | 0,8B · 2B · 4B · 9B | Apache-2.0 | finestra 262k, ragionamento **spento** di serie sulle taglie piccole, pesi già pronti su Hugging Face |
| **Llama 3.2** | 1B · 3B | Llama Community | ha 18 mesi e sul banco tiene testa a modelli nuovi. Licenza con vincoli |
| **Granite 4.1** | 3B · 8B | Apache-2.0 | pensata per l'impresa e le chiamate a strumento; sul banco ha aggiunto prosa dopo il JSON |
| **Ministral / Gemma / Phi** | 3-4B | varie | non provate qui; nessuna ragione forte per preferirle a Qwen sul nostro compito |

Sul nostro compito il criterio di scelta **non è l'intelligenza generale**. È: sa
copiare alla lettera dei riferimenti da un elenco lungo, sa fermarsi, e ha una licenza
che non ci lega le mani. La classifica BFCL — quella delle chiamate a strumento — mette
i modelli piccoli intorno al 60%, ma è una misura su schemi generici, e la stessa fonte
avverte che il posto in classifica non predice il comportamento nel proprio impianto.

**Nota sul «ragionamento»**: su un compito di estrazione strutturata i modelli che
pensano ad alta voce **non vanno meglio**, e pagano il tempo dei gettoni di
ragionamento. Le taglie piccole di Qwen 3.5 lo hanno spento di serie, che per noi è la
configurazione giusta.

---

## §5 — I candidati veri, pro e contro

### Qwen3.5-4B — **il candidato principale**

**Pro**
* sul banco legge il prompt **quasi il doppio** del 9b (417 contro 234 g/s) e scrive il
  60% più veloce;
* pesa 3,4 GB contro 6,6: sta comodo in 8 GB di memoria, e lascia spazio alla cache;
* **stessa famiglia del 9b**: stesso tokenizzatore e stesso schema di conversazione,
  quindi cambiare profilo è una riga in `nli.profile` e nient'altro;
* Apache-2.0, nessun vincolo d'uso;
* il suo errore misurato è **di annidamento**: la cosa che una LoRA corregge meglio.

**Contro**
* zero-shot è **meno preciso** del 9b sulla struttura: senza fine tuning non lo metterei
  in servizio;
* è prolisso quanto gli altri, quindi il guadagno di velocità reale arriva solo dopo
  l'addestramento sulle buste compatte.

### Qwen3.5-2B — **l'obiettivo ambizioso**

**Pro**
* legge il prompt a **1 087 g/s**: quattro volte e mezza il 9b. Con il prompt accorciato
  dal fine tuning, la lettura scende sotto i **due secondi**;
* 2,7 GB: gira su qualunque cosa, anche su un mini-PC senza scheda video.

**Contro**
* sul banco **non si è fermato**: ha scritto 1 200 gettoni di seguito. È il difetto
  tipico delle taglie piccolissime, e in produzione la generazione vincolata lo
  taglierebbe — ma resta il segnale che la presa sul formato è debole;
* è la taglia dove il fine tuning può **non bastare**. Non lo escludo: lo metto alla
  prova, perché costa undici dollari saperlo invece di discuterne.

### Qwen3.5-9B — **il riferimento, e la riserva**

**Pro**
* l'unico che sul banco ha prodotto una busta **corretta** senza addestramento;
* è quello in servizio oggi: se il fine tuning delle taglie piccole non passasse il
  cancello, restiamo qui senza aver perso niente.

**Contro**
* 57 secondi per una risposta su questa macchina. Con il prompt accorciato scenderebbe
  a ~27, che è ancora il triplo di un 4b affinato;
* 6,6 GB in memoria, e con Docker acceso su 16 GB si comincia a stare stretti.

### Granite 4.1 8B e Llama 3.2 3B — **scartati, con motivo**

Granite ha aggiunto **prosa dopo il JSON**, che è il difetto peggiore per noi: è la
forma di errore che un parser non riconosce come errore. Ed è il più lento del gruppo a
leggere.

Llama 3.2 3B è una **sorpresa positiva** — 18 mesi di età e tiene testa ai nuovi, con
la busta più compatta del gruppo (135 gettoni) — ma ha una licenza con vincoli d'uso e
appartiene a una famiglia diversa da quella in servizio, il che significa un secondo
schema di conversazione da mantenere. Lo terrei come piano di riserva se Qwen desse
problemi.

---

## §6 — Cosa succede dopo il fine tuning: la proiezione

Con le due economie di §3 — prompt più corto del 58% e uscita compatta a ~200 gettoni —
sulla **stessa macchina**:

| modello | lettura (1 700 gettoni) | scrittura (200 gettoni) | **risposta** | oggi |
|---|---|---|---|---|
| qwen3.5:2b | 1,6 s | 3,3 s | **~5 s** | 27 s |
| qwen3.5:4b | 4,1 s | 5,7 s | **~10 s** | 41 s |
| qwen3.5:9b | 7,3 s | 9,3 s | **~17 s** | 57 s |

**Sono proiezioni**, non misure: assumono che la velocità resti quella misurata e che
l'addestramento porti davvero le due economie. Il numero vero arriva dalla prova di
fumo.

Ma l'ordine di grandezza è quello, e dice una cosa netta: **un 4B affinato risponde in
un decimo del tempo del 9B di oggi**. Da «l'utente aspetta e va a prendere un caffè» a
«l'utente aspetta».

---

## §7 — L'hardware, e quanto costa

Un modello affinato da 4B in quantizzazione a 4 bit occupa **~3,5 GB**, più la cache
delle chiavi: con una finestra da 8k, **meno di 5 GB in tutto**.

| soluzione | costo | risposta stimata (4B affinato) | note |
|---|---|---|---|
| **il MacBook che ha già** | 0 € | ~10 s | va bene per lo sviluppo e per un utente solo |
| **mini-PC 32 GB**, solo CPU | 400-600 € | 20-30 s | funziona, ma la CPU sulla lettura del prompt è lenta |
| **usato: RTX 3060 12 GB** | 200-250 € | **1-2 s** | il salto vero. 12 GB tengono comodamente un 4B, e volendo anche il 9B |
| **nuovo: RTX 4060 Ti 16 GB** | 450-500 € | **~1 s** | margine per il 9B e per i documenti di domani |
| **Mac mini M4 16 GB** | 700 € | ~8 s | silenzioso, poco consumo, ma la memoria unificata non regge il 9B con altro acceso |

> **Il consiglio sull'hardware**: una **RTX 3060 12 GB usata, intorno ai 220 €**, in un
> PC che probabilmente ha già. È la differenza fra dieci secondi e due, costa meno di
> un mese di una macchina in affitto, e regge anche il 9B se un domani servisse.

Da notare: **serve solo per l'inferenza**. L'addestramento resta su GPU affittata
(`ai/18` §7), perché lì servono 48 GB e comprarli non ha senso per tre corse.

---

## §8 — La raccomandazione

> **Affinare Qwen3.5-4B come candidato principale, e Qwen3.5-2B in parallelo.
> Tenere il 9B come riferimento e come riserva. Decide il cancello, non il dibattito.**

Le ragioni, in ordine:

1. **La distanza fra il 4B e il 9B è distanza di formato**, ed è la cosa che una LoRA
   corregge meglio. Non stiamo chiedendo al modello di capire meglio l'italiano: gliene
   stiamo chiedendo di scrivere meglio una busta;
2. **due corse costano ventidue dollari.** Discutere se il 2B ce la fa costa più tempo
   di quanto costi scoprirlo. Il dataset è lo stesso, la ricetta è la stessa, cambia una
   riga nel file di configurazione;
3. **il cancello di `ai/18` §9 decide da solo**: se il 4B affinato passa le sette
   condizioni, va in servizio; se non le passa, si guarda il 2B; se non passa nessuno
   dei due, si affina il 9B e si è comunque guadagnato il prompt più corto;
4. **il rischio è nullo**: l'adattatore non si fonde nel modello base, e **D116** fa
   scegliere il profilo dalle impostazioni. Si torna indietro con un menu a tendina.

### La regola generale che ne esce

**Non è «quale modello è il più intelligente», è «qual è il più piccolo che passa il
cancello».** Ed è una domanda a cui si risponde solo misurando, perché dipende dal
compito: il nostro è stretto, ripetitivo e strutturato, cioè il caso in cui i modelli
piccoli affinati vanno meglio del loro peso.

---

## §9 — Il piano di prova

1. **Rimisurare la linea di partenza** dei tre candidati sul corpus, senza fine tuning,
   con la generazione vincolata accesa — quindi la misura vera e non quella di §2.
   Serve a sapere da dove parte ciascuno.
2. **Prova di fumo** su 500 esempi, sul 4B: verifica la catena intera — addestramento,
   conversione in GGUF, `ollama`, misura — e dà la velocità vera dell'addestramento.
3. **Due corse vere**, 4B e 2B, stesso dataset, stessa ricetta.
4. **Cancello** di `ai/18` §9 su entrambi, più le due misure di questo documento: gettoni
   del prompt e tempo di risposta.
5. Se passa il **2B**, si compra anche il vantaggio di girare ovunque. Se passa solo il
   **4B**, è comunque il quadruplo della velocità di oggi. Se non passa nessuno, il 9B
   affinato resta meglio del 9B di adesso.

---

## §10 — Cosa cambia in `ai/18`

Due cose, e le annoto perché quel documento va letto insieme a questo:

* **il modello da affinare non è più deciso in partenza**: sono due candidati e un
  riferimento. Cambia una riga della ricetta, non il piano;
* **una nota che vale per tutti**: chi pubblica i pesi di Qwen 3.5 **sconsiglia QLoRA a
  4 bit** su questa famiglia per problemi di precisione, e raccomanda LoRA a 16 bit. È
  una conferma indipendente della scelta già fatta in `ai/18` §3, con un motivo in più
  che vale la pena avere scritto.

---

## Fonti

* [Qwen3.5 small models — Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models)
* [Qwen 3.5: Architecture, Benchmarks, Model Selection](https://blog.overshoot.ai/blog/qwen3.5-on-overshoot)
* [Qwen/Qwen3.5-9B-Base — Hugging Face](https://huggingface.co/Qwen/Qwen3.5-9B-Base)
* [I Tested 13 Local LLMs on Tool Calling — 2026 Eval Results](https://www.jdhodges.com/blog/local-llms-on-tool-calling-2026-pt1-local-lm/)
* [Function Calling Benchmarks Leaderboard 2026](https://awesomeagents.ai/leaderboards/function-calling-benchmarks-leaderboard/)
* [AI Agent Tool Calling Benchmarks: BFCL v4, tau-Bench, latency](https://www.spheron.network/blog/tool-calling-benchmarks-bfcl-tau-bench-latency-optimization/)
