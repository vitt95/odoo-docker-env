# Proposta — L'ancoraggio del tempo

## Dare un appiglio alle espressioni temporali, e togliere la discarica alle categorie

Documento del 2 agosto 2026. Nasce da una diagnosi fatta su 80 aperture del corpus
fondativo con `qwen3.5:9b`, e propone tre decisioni.

Le sigle citate portano fra parentesi di cosa trattano, come chiede `ai/CLAUDE.md`.

---

## 1. Il problema, con i numeri

Su 80 aperture, 21 falliscono. Il modello **non sbaglia a scrivere il DSL**: 80 buste
valide su 80, zero errori di forma, zero rifiuti dell'applicatore, un solo
`out_of_scope`. Sa scrivere la lingua. Sbaglia cosa dice.

I 21 fallimenti si dividono in due famiglie che sembrano diverse e non lo sono.

**Il tempo — 12 casi su 21.** In tutte e dodici le frasi che contengono
un'espressione di tempo, è il tempo la cosa che va storta. Sparisce (5), diventa una
categoria che non c'entra (4), viene scritto con il valore sbagliato (1), o il caso
fallisce per altro mentre il tempo regge (2). Nessuna eccezione: dove c'è un periodo,
il periodo è il problema.

**Le categorie inventate — 9 casi su 21.** Il modello produce una condizione nominata
che nella frase non c'è:

| frase | atteso | prodotto |
|---|---|---|
| ordini **lo scorso mese** | data ordine nel mese scorso | **in bozza** |
| fatture **sta settimana** con valore fino a 1000 | data fattura questa settimana, importo ≤ 1000 | **partite aperte**, importo ≤ 1000 |
| voglio vedere **prelievi** | nessun filtro | **in bozza** |
| commesse con importo oltre 500 raggruppati per stato | importo > 500 | **da consegnare** |

L'ultimo è il più istruttivo: il modello prende *tutto il resto della frase* come
giustificazione di una categoria, e nel farlo perde il `> 500` che era l'unica
condizione vera.

### 1.1 Le due famiglie sono la stessa

Nel DSL una condizione si àncora alla frase in due modi soltanto:

| forma | dove trova l'appiglio |
|---|---|
| condizione su un attributo | la frase **nomina il campo**: *«con importo oltre 500»* |
| condizione nominata (`is_category`) | la frase nomina **solo la categoria**, nessun campo |

Un'espressione di tempo **non nomina mai il campo a cui si attacca**. Non è un difetto
del corpus: è così che si parla. Nessuno dice *«ordini con data ordine nel mese
scorso»*, si dice *«ordini del mese scorso»*.

Verificato nel generatore del corpus, `ai/corpus/genera_corpus.py` riga 248: una
condizione numerica si scrive `"con {attributo} {operatore} {valore}"` — il campo c'è
— mentre una condizione temporale si scrive `c["frase"]`, cioè **solo *«lo scorso
mese»***.

E nel catalogo che mandiamo al modello **non esiste il concetto di "la data"
dell'entità**. Ogni attributo porta riferimento, termini e tipo, e basta. Il prompt ha
una sola regola sulle date — *«non risolvere mai una data»* — e **nessuna** che dica
dove si attacca un periodo che non nomina un campo.

Il modello si trova quindi un pezzo di frase che deve diventare una condizione, e
nessun posto dove metterlo. Fa una di due cose: lo lascia cadere, oppure lo appoggia
sull'unica forma di condizione che non richiede un appiglio, cioè una categoria.

**`is_category` è la discarica.** Non chiede un campo, non chiede un valore, non chiede
un tipo. Ogni frammento che il modello non sa collocare finisce lì. Vale per *«lo
scorso mese»*, vale per *«di vendita»* → partite aperte, vale per *«prelievi»* → in
bozza, dove *«prelievi»* è **il nome dell'entità stessa**.

Da qui la proposta: dare al tempo un appiglio, e togliere alle categorie la discarica.

### 1.2 Un pezzo del problema non è del prodotto: la misura fa domande senza risposta

`genera_corpus.py` riga 569:

```python
campo = self.rng.choice(spec["temporali"])
```

Per le fatture, `"temporali": ["invoice_date", "invoice_date_due"]` — data fattura
**e** scadenza. Il generatore ne pesca una a caso, e nella frase scrive solo *«lo
scorso mese»*.

Verificato sui casi reali: stessa entità, stessa forma di frase, attese diverse.
*«sta settimana»* → data fattura. *«lo scorso mese»* → scadenza. *«quest'anno»* →
scadenza. *«nel 2025»* → data fattura.

Su quei casi **nessuno può fare meglio del 50%**, né un modello né una persona: la
frase non contiene l'informazione che l'attesa pretende. Una parte dei 12 fallimenti
temporali è quindi un difetto del metro, non del prodotto.

Questo è il punto che `ai/restart.md` («Come lavoriamo») chiede di controllare sempre
per primo: prima di attribuire un esito al fornitore, verificare che non sia stato il
metro a dettarlo.

### 1.3 Due difetti minori, trovati per strada

**Il metro non vede D105** (la decisione per cui una condizione nominata dev'essere
fondata nel frammento che la giustifica). `interpret()` esegue i livelli 1-2
(struttura) e la coerenza, ma **non il livello 3**, che è dove quel controllo vive. Ecco
perché D105 «rende i fallimenti visibili senza spostare il punteggio»: il punteggio non
li ha mai visti.

**Due predicati per la stessa cosa.** Su una data il contratto ammette sia `within` sia
`between`, entrambi con valore temporale. Il corpus si aspetta sempre `within`. Un
modello che scrive `between` produce una cosa **legale** e viene contato sbagliato.
Deliberato di **lasciarlo com'è**: nel campione pesa due casi, che sbagliavano anche
altro. Resta scritto qui perché la prossima persona che vede quei due casi non ci
perda tempo.

---

## 2. La proposta in una riga

**Il catalogo dichiara dove si attacca il tempo, e una categoria che la frase non
nomina smette di essere scrivibile.**

---

## 3. Cosa si scarta, e perché

**Indovinare la data principale con un'euristica.** Si poteva ordinare le date per
qualche criterio — quella che compare nell'ordinamento predefinito del modello Odoo,
quella obbligatoria, quella che sta nelle viste — e prendere la prima. Scartata:
sceglierne una fra due plausibili è indovinare, che è esattamente ciò che stiamo
togliendo.

Il registro lo argomenta in §19.1 deliberando **D105**: un filtro inventato mostra
*meno* record con sicurezza, e chi guarda non ha modo di accorgersene, mentre un
rifiuto è un errore che si vede. È il compromesso che **D2** (la decisione che vieta
qualunque scrittura sui dati finché la Fase 2 non è misurata e superata) rende
necessario: un sistema che dovrà scrivere non può permettersi errori invisibili.

**Chiedere sempre, anche quando la data è una sola.** Onesto ma inutilmente faticoso:
*«ordini del mese scorso»* ha una data sola e nessuna ambiguità vera. Trasformarlo in
una domanda insegnerebbe all'utente che il sistema non capisce nemmeno le cose facili.

**Aggiungere solo una regola nel prompt.** È la leva più debole, e il progetto ha già
le prove: le regole nel prompt ci sono e vengono violate. Una regola in più su una
finestra di contesto da 4096 gettoni, già occupata per metà dal prompt, è un costo
certo con un beneficio incerto.

---

## 4. Le tre parti

### 4.1 Il catalogo dichiara l'ancora del tempo

Una chiave nuova nel catalogo, calcolata nella **zona pura** che lo costruisce. Tre
forme, per i tre casi reali:

```
"time_anchor": {"ref": "ordini_vendita.data_ordine"}         una sola data esposta
"time_anchor": {"choices": ["fatture_cliente.data_fattura",
                            "fatture_cliente.scadenza"]}      due o più: si chiede
"time_anchor": null                                           nessuna data esposta
```

La regola che la deriva è **strutturale, non semantica**: conta le date che
l'esposizione ha reso visibili **a questo utente**. Una → è quella. Due o più → nessuna
è principale. Zero → il tempo non è esprimibile su questa entità.

Che sia strutturale è ciò che la rende verificabile senza database e senza modello: è
una funzione della lista di attributi, e i suoi test sono test puri.

Che parta dagli attributi **già filtrati dai diritti** è ciò che la rende sicura: un
utente che non può vedere la scadenza non se la vede proporre, perché la scadenza non è
nel suo catalogo. Vale la stessa garanzia di **D104** (la decisione per cui il
vocabolario del catalogo si mostra all'utente, suggerito e mai imposto): i suggerimenti
nascono dallo stesso catalogo che vede il modello, costruito con i diritti di chi
chiede.

Il terzo caso è un guadagno che non era stato previsto: oggi *«clienti del mese
scorso»* perde il tempo **in silenzio**, perché sui clienti non c'è nessuna data
esposta. Con l'ancora nulla, la risposta diventa una domanda.

Se un domani si vorrà dire *«per le fatture la data principale è la scadenza»*, quella
è una voce di dizionario che qualcuno approva, e la strada esiste già: è **D108** (il
percorso di approvazione delle voci di dizionario). Non si costruisce adesso.

### 4.2 Due regole nel prompt, e la seconda è quella che conta

```
- a time expression that names no attribute is a condition on the catalogue's
  "time_anchor": use its "ref" if it has one; if it has "choices", answer with a
  clarification offering those dates; if it is null, answer with a clarification;
- NEVER drop a time expression. If you cannot place it, ask. A sentence that mentions
  a period and an answer that does not is a wrong answer.
```

La prima dà l'appiglio. La seconda toglie l'uscita di sicurezza: oggi lasciar cadere un
pezzo di frase **non costa niente** al modello, perché nessuna regola glielo vieta e
una busta senza quella condizione è comunque valida.

### 4.3 La categoria infondata diventa inesprimibile

Lo schema che vincola la generazione si costruisce già **per catalogo**: è **D101** (i
riferimenti ammessi sono un insieme chiuso, preso dal catalogo). L'aggiunta è piccola e
sfrutta una cosa che abbiamo già in mano: **la frase la conosciamo prima di costruire
lo schema**.

Fra le categorie si ammettono solo quelle **i cui termini compaiono nella frase**, con
lo stesso riconoscitore che D105 usa dopo — quello che sa di accenti, abbreviazioni e
refusi.

Il riconoscitore si passa come argomento, non si importa: `nli_engine` non può dipendere
da `nli_semantics` (§6.3 di `04`, il confine fra il motore e la semantica). È la stessa
forma con cui `validate_grounding` riceve `mentions` oggi, e come oggi, **se non viene
passato il restringimento non si applica** — così i test puri del motore continuano a
girare senza dizionario.

Il risultato: per *«voglio vedere prelievi»* il modello **non ha più in bocca**
`in_bozza`. Non è una regola che può violare: è un simbolo che, per quella frase, non
esiste nel suo alfabeto.

E quando il riconoscitore sbaglia — l'utente ha scritto la categoria in un modo che non
riconosce — il fallimento degrada a **una domanda**, non a un filtro sbagliato. È la
direzione argomentata in §19.1: un errore che si vede è preferibile a uno che non si
vede.

D105 resta dov'è, come rete per le condizioni che arrivano da altre strade: una query
salvata, un'interpretazione modificata a mano, un secondo esecutore. Uno impedisce,
l'altro verifica.

---

## 5. La misura smette di fare domande senza risposta

Il generatore **sa già** produrre casi di chiarimento con temporale ambiguo: c'è
`temporale_ambiguo` dentro `caso_chiarimento`. Il difetto è che le aperture normali
pescano lo stesso una data a caso su entità che ne hanno due.

Correzione: quando l'entità espone più di una data e la frase non nomina il campo, il
caso **si aspetta un chiarimento**, non un'operazione.

La regola *«quante date espone questa entità»* deve stare **in un posto solo**, letto
sia dal prodotto sia dal generatore. Altrimenti divergono, e una misura che usa una
regola diversa da quella del prodotto misura un altro prodotto. È lo stesso schema di
**D109** (la mappa dei tipi che vive in una zona pura e la legge chiunque serva).

E il livello 3 va eseguito **dentro lo strumento di misura**, così il numero riflette
D105. Non nel prodotto: lì il livello 3 gira già al posto suo.

---

## 6. Decisioni richieste

| | |
|---|---|
| **D110** | Il catalogo dichiara l'ancora del tempo: una data se ne espone una sola, l'insieme delle scelte se sono due o più, nulla se non ce ne sono. Un'espressione temporale che non nomina un campo si attacca lì, e se l'ancora non è unica la risposta è un chiarimento |
| **D111** | Un'espressione temporale non può essere lasciata cadere: se non si colloca, si chiede |
| **D112** | Le categorie ammesse dalla generazione vincolata sono quelle **nominate dalla frase**, non tutte quelle del catalogo. Una categoria infondata diventa inesprimibile invece che rifiutata dopo |

---

## 7. Cosa non fa

**Non alza il punteggio di accuratezza, e potrebbe abbassarlo.** Le risposte sbagliate
diventano domande: è il verso giusto — un errore visibile al posto di uno invisibile —
ma il corpus conta una domanda come un fallimento di `operations`. Il numero da guardare è un altro — quanti filtri sbagliati
escono con l'aria di essere giusti — e va guardato con la copertura accanto, come dice
`07` §5.4 (il piano di valutazione, paragrafo su come si leggono i due numeri insieme).

**Non risolve `filter` da solo.** Restano le famiglie che non c'entrano con il tempo né
con le categorie inventate: il predicato possibile ma sbagliato, il valore preso male,
le due condizioni fuse in una.

**Non tocca `within`/`between`**, come deliberato in §1.3.

**Non lima il prompt contro il corpus sintetico.** Le due regole di §4.2 sono
strutturali — dicono dove va una cosa, non come si dice in italiano. Ogni punto
strappato al generatore rischia di essere prompt adattato al generatore. È la
degradazione che **D42** (la decisione delle tre popolazioni di corpus, con quello
sigillato protetto da un'autorizzazione) esiste per impedire: senza sigillo la misura
degrada in conferma nel giro di pochi trimestri, e il procedimento che la degrada è il
procedimento corretto di miglioramento. Sul corpus fondativo il sigillo **non c'è**, e
lo dichiara **D86** (la decisione che riconosce il corpus sintetico come non
sigillabile, perché chi scrive il generatore ne conosce la distribuzione).

---

## 8. Ordine di costruzione

1. **`time_anchor` nella zona pura**, con i suoi test puri. Non serve il modello.
2. **Regola nel prompt e restringimento dello schema**, con i test puri e Odoo.
3. **Generatore del corpus**: i temporali ambigui si aspettano un chiarimento. Corpus
   rigenerato.
4. **Livello 3 dentro lo strumento di misura.**
5. **Rimisura** — dopo, e solo dopo.

I punti 1-4 sono verificabili **senza interrogare il modello nemmeno una volta**: sono
test puri e test Odoo. La misura serve alla fine, a dire quanto è servito, e non prima:
misurare a metà strada produce un numero che non descrive né il prima né il dopo.
