# L'ancoraggio del tempo — piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dare a un'espressione temporale un posto dichiarato dove attaccarsi, e togliere a `is_category` il ruolo di discarica per i frammenti che il modello non sa collocare.

**Architecture:** Tre cambiamenti, in ordine di dipendenza. (1) Una regola pura calcola *l'ancora del tempo* dagli attributi del catalogo già filtrati dai diritti, e il catalogo la porta con sé fino al modello. (2) Il prompt dice dove si attacca un periodo e vieta di lasciarlo cadere. (3) Lo schema che vincola la generazione ammette solo le categorie i cui termini compaiono nella frase, usando lo stesso riconoscitore del controllo di fondatezza. Nessun cambiamento richiede di interrogare il modello per essere verificato.

**Tech Stack:** Python 3.12, Odoo 18, `unittest`. Zone pure verificate da `tools/arch`, test puri da `tools/pure/run.py`, test Odoo da `./manage.sh test nli_test`.

**Spec:** `ai/14-ancoraggio-del-tempo.md`. Le decisioni che ne nascono sono **D110**, **D111**, **D112**.

## Global Constraints

- **Le zone pure non importano la piattaforma.** `nli_semantics/catalogue` è zona pura dichiarata in `tools/arch/spec.py`: niente `odoo`, niente `os`, niente `datetime.now`. Un file nuovo dentro una zona già dichiarata è coperto automaticamente — non serve toccare `spec.py`.
- **`nli_engine` non importa `nli_semantics`** (§6.3 di `04`, il confine fra motore e semantica). Ciò che serve dalla semantica si riceve come argomento.
- **Nessun controllo può passare a vuoto.** Ogni controllo ha un test che lo mostra scattare **e** uno che lo mostra non scattare. Un'ispezione vuota è un fallimento.
- **Niente deroghe inline.** Allentare una regola richiede una decisione numerata in `ai/00-registro-decisioni.md`.
- **Ogni sigla porta fra parentesi cosa tratta**, nel codice, nei commenti e nei messaggi di commit. **La glossa si verifica sul registro, non si ricorda.**
- **Verifica prima di ogni commit:** `./manage.sh check` deve essere verde. Dopo i task che toccano moduli Odoo: `./manage.sh test nli_test`.
- **Nessuna misura contro il modello** fino al termine del piano. I task 1-7 si verificano senza interrogare `ollama` nemmeno una volta.
- **Stato di partenza:** 116 test Odoo verdi, 948/948 contratto e corpus, 54 file in zone pure con 0 violazioni.

## Struttura dei file

| file | responsabilità |
|---|---|
| `custom_addons/nli_semantics/catalogue/anchor.py` | **nuovo.** La regola dell'ancora: quali attributi sono date, e cosa ne consegue. Pura, senza dipendenze. |
| `custom_addons/nli_semantics/pure_tests/test_anchor.py` | **nuovo.** I test della regola, scattante e non scattante. |
| `custom_addons/nli_semantics/catalogue/build.py` | il catalogo acquista il campo `time_anchor`, calcolato dopo diritti e budget. |
| `custom_addons/nli_semantics/pure_tests/test_catalogue.py` | i test che l'ancora nasce dagli attributi sopravvissuti ai diritti. |
| `custom_addons/nli_engine/prompt.py` | il payload porta l'ancora; le istruzioni acquistano le due regole di D110 e D111; `catalogue_references` restringe le categorie (D112). |
| `custom_addons/nli_engine/interpreter.py` | `interpret()` riceve il riconoscitore e lo passa alla costruzione dello schema. |
| `custom_addons/nli_engine/pure_tests/test_interpreter.py` | i test del payload, delle regole e del restringimento. |
| `custom_addons/nli_dispatch/runtime/pipeline.py` | la conduttura passa a `interpret()` il riconoscitore che già costruisce per il livello 3. |
| `custom_addons/nli_dispatch/tests/test_dispatch.py` | il test che la conduttura lo passa davvero. |
| `ai/corpus/genera_corpus.py` | un'apertura con temporale ambiguo si aspetta un chiarimento, non un'operazione. |
| `ai/corpus/misura_accuratezza.py` | lo strumento esegue il livello 3, così il numero riflette D105. |
| `ai/00-registro-decisioni.md` | §21 con D110, D111, D112 e le loro argomentazioni. |

---

## Task 1: La regola dell'ancora, in zona pura

**Files:**
- Create: `custom_addons/nli_semantics/catalogue/anchor.py`
- Test: `custom_addons/nli_semantics/pure_tests/test_anchor.py`

**Interfaces:**
- Consumes: niente. È il fondo della catena.
- Produces: `DATE_TYPES: frozenset[str]`, `date_refs(attributes) -> tuple[str, ...]`, `time_anchor(refs) -> dict | None`. `attributes` è qualunque iterabile di oggetti con `.ref: str` e `.type: str`. Il ritorno di `time_anchor` è `{"ref": str}`, `{"choices": list[str]}` oppure `None`.

- [ ] **Step 1: Scrivere il test che fallisce**

Creare `custom_addons/nli_semantics/pure_tests/test_anchor.py`:

```python
"""Dove si attacca un'espressione temporale che non nomina un campo (D110).

D110 e' la decisione per cui il catalogo dichiara l'ancora del tempo: una data se ne
espone una sola, l'insieme delle scelte se sono due o piu', nulla se non ce ne sono.
"""

from __future__ import annotations

import unittest

from ..catalogue import anchor


class Attributo:
    """Il minimo che la regola legge: un riferimento e un tipo."""

    def __init__(self, ref: str, tipo: str):
        self.ref, self.type = ref, tipo


class TestDateRefs(unittest.TestCase):

    def test_only_the_two_time_types_count(self):
        attributi = [
            Attributo("fatture.data_fattura", "date"),
            Attributo("fatture.creato_il", "datetime"),
            Attributo("fatture.importo_totale", "number"),
            Attributo("fatture.cliente", "relation"),
            Attributo("fatture.note", "text"),
        ]
        self.assertEqual(
            anchor.date_refs(attributi),
            ("fatture.creato_il", "fatture.data_fattura"))

    def test_a_catalogue_without_dates_yields_nothing(self):
        """Il controllo non deve passare a vuoto: senza date la lista e' vuota,
        e l'ancora nulla che ne deriva e' un caso reale — i clienti non hanno date."""
        attributi = [Attributo("clienti.citta", "text")]
        self.assertEqual(anchor.date_refs(attributi), ())


class TestTimeAnchor(unittest.TestCase):

    def test_one_date_is_the_anchor(self):
        self.assertEqual(
            anchor.time_anchor(("ordini.data_ordine",)),
            {"ref": "ordini.data_ordine"})

    def test_two_dates_are_a_question_not_a_choice_we_make(self):
        """Sceglierne una fra due plausibili sarebbe indovinare: l'ancora porta
        entrambe e la risposta diventa un chiarimento."""
        self.assertEqual(
            anchor.time_anchor(("fatture.scadenza", "fatture.data_fattura")),
            {"choices": ["fatture.data_fattura", "fatture.scadenza"]})

    def test_no_date_is_no_anchor(self):
        self.assertIsNone(anchor.time_anchor(()))

    def test_the_order_is_stable(self):
        """Due catalogui uguali devono produrre lo stesso payload: un ordine che
        cambia fa cambiare il prompt a parita' di installazione."""
        uno = anchor.time_anchor(["b.due", "a.uno"])
        due = anchor.time_anchor(["a.uno", "b.due"])
        self.assertEqual(uno, due)
        self.assertEqual(uno, {"choices": ["a.uno", "b.due"]})
```

- [ ] **Step 2: Eseguirlo e vederlo fallire**

Run: `python3 tools/pure/run.py`
Expected: FAIL con `ImportError: cannot import name 'anchor'`

- [ ] **Step 3: Scrivere l'implementazione minima**

Creare `custom_addons/nli_semantics/catalogue/anchor.py`:

```python
"""Dove si attacca un'espressione temporale che non nomina un campo (D110).

**Zona pura.**

## Il problema che questa regola risolve

Nel DSL una condizione si ancora alla frase nominando il proprio campo: *«con importo
oltre 500»* porta l'attributo, l'operatore e il valore. Un'espressione di tempo non lo
fa mai — si dice *«ordini del mese scorso»*, non *«ordini con data ordine nel mese
scorso»* — e fino a qui il catalogo non aveva alcun concetto di *«la data»*
dell'entita'. Il modello si trovava un frammento da collocare e nessun posto dove
metterlo: o lo lasciava cadere, o lo appoggiava sull'unica forma di condizione che non
richiede un appiglio, cioe' una condizione nominata.

## La regola e' strutturale, non semantica

Si contano le date **esposte**, e basta. Nessuna euristica su quale data «conta di
piu'»: sceglierne una fra due plausibili sarebbe indovinare, e un sistema che dovra'
scrivere sui dati non puo' permettersi errori invisibili (`00` §19.3). Se un domani si
vorra' dichiarare che per le fatture la data principale e' la scadenza, quella e' una
voce di dizionario che qualcuno approva, e la strada esiste gia': **D108** (la
decisione che da' un registro alle voci di dizionario approvate).

Essere strutturale e' anche cio' che la rende verificabile senza database e senza
modello: e' una funzione della lista di attributi, e i suoi test sono test puri.
"""

from __future__ import annotations

#: I due tipi di `03` §8.1 (il paragrafo che elenca il vocabolario dei tipi) che
#: portano un punto nel tempo. `monetary` e `float` collassano in `number` altrove per
#: la stessa ragione per cui questi due restano distinti: qui la distinzione non serve
#: a nulla, e un periodo si applica a entrambi allo stesso modo.
DATE_TYPES = frozenset({"date", "datetime"})


def date_refs(attributes) -> tuple[str, ...]:
    """I riferimenti degli attributi che portano una data, in ordine stabile.

    `attributes` e' qualunque iterabile di oggetti con `.ref` e `.type` — il catalogo
    ne passa i propri, e un test puo' passare un oggetto minimo. La zona non conosce
    la classe che li porta, e non deve.
    """
    return tuple(sorted(
        attribute.ref for attribute in attributes if attribute.type in DATE_TYPES))


def time_anchor(refs) -> dict | None:
    """L'ancora del tempo per un catalogo, dalle sue date esposte (**D110**).

    Tre forme, per i tre casi reali:

    * `{"ref": "..."}` — una sola data esposta: un periodo senza campo va li';
    * `{"choices": [...]}` — due o piu': nessuna e' principale, e la risposta giusta
      e' una domanda;
    * `None` — nessuna data esposta: su questa entita' un periodo non e' esprimibile,
      e va detto invece che lasciato cadere in silenzio.

    Le date arrivano gia' filtrate dai diritti di chi chiede, perche' il catalogo
    applica il filtro dei permessi **prima** dell'esposizione (§5.9). Un utente che non
    puo' leggere la scadenza non se la vede proporre, per la stessa garanzia di **D104**
    (la decisione per cui il vocabolario del catalogo si mostra all'utente, suggerito e
    mai imposto).
    """
    dates = tuple(sorted(refs))
    if not dates:
        return None
    if len(dates) == 1:
        return {"ref": dates[0]}
    return {"choices": list(dates)}
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `python3 tools/pure/run.py`
Expected: PASS, e il conteggio dei test puri sale di 6 (da 395 a 401).

- [ ] **Step 5: Verificare i confini**

Run: `python3 tools/arch/run.py`
Expected: `PASS Architectural (pure zones)` con **55** file in zone pure (era 54), 0 violazioni.

- [ ] **Step 6: Commit**

```bash
git add custom_addons/nli_semantics/catalogue/anchor.py \
        custom_addons/nli_semantics/pure_tests/test_anchor.py
git commit -m "D110 (1/3): la regola dell'ancora del tempo, in zona pura

Conta le date esposte e ne deriva dove si attacca un periodo che non nomina
un campo: una sola data e' l'ancora, due o piu' sono una domanda, nessuna
e' un periodo inesprimibile su questa entita'.

Strutturale e non semantica di proposito: sceglierne una fra due plausibili
sarebbe indovinare, e 00 §19.3 argomenta perche' un errore invisibile e'
peggio di una domanda. Se servira' dichiarare una data principale, la strada
e' D108 (il registro delle voci di dizionario approvate), non un'euristica.

6 test puri, fra cui quello che mostra la lista vuota e quello che mostra
l'ordine stabile."
```

---

## Task 2: Il catalogo porta l'ancora

**Files:**
- Modify: `custom_addons/nli_semantics/catalogue/build.py`
- Test: `custom_addons/nli_semantics/pure_tests/test_catalogue.py`

**Interfaces:**
- Consumes: `anchor.date_refs`, `anchor.time_anchor` dal Task 1.
- Produces: `Catalogue.time_anchor: dict | None`, popolato da `build()`. I consumatori successivi lo leggono come attributo diretto.

- [ ] **Step 1: Scrivere il test che fallisce**

Aggiungere in fondo a `custom_addons/nli_semantics/pure_tests/test_catalogue.py`:

```python
class TestTimeAnchor(unittest.TestCase):
    """L'ancora nasce dagli attributi che sono sopravvissuti ai diritti (D110)."""

    def _dictionary(self):
        return Dictionary.build([
            naming("ordini_vendita.data_ordine", ["data ordine", "data"]),
            naming("ordini_vendita.data_consegna", ["data consegna"]),
            naming("ordini_vendita.importo_totale", ["totale", "importo"]),
        ])

    def _attributes(self):
        return [
            Attribute(name="data_ordine", label="Data ordine", type="date",
                      in_default_views=True),
            Attribute(name="data_consegna", label="Data consegna", type="date",
                      in_default_views=True),
            Attribute(name="importo_totale", label="Totale", type="number",
                      in_default_views=True),
        ]

    def test_two_dates_make_the_anchor_a_question(self):
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=self._attributes(),
            readable_refs=frozenset({"ordini_vendita.data_ordine",
                                     "ordini_vendita.data_consegna",
                                     "ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertEqual(
            catalogue.time_anchor,
            {"choices": ["ordini_vendita.data_consegna",
                         "ordini_vendita.data_ordine"]})

    def test_a_date_the_user_cannot_read_is_not_offered(self):
        """La garanzia che rende sicuro il suggerimento: l'ancora nasce dopo il
        filtro dei permessi (§5.9), quindi non puo' nominare cio' che l'utente non
        vede. Senza questo test la regola potrebbe leggere gli attributi in ingresso
        invece di quelli sopravvissuti, e nessuno se ne accorgerebbe."""
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=self._attributes(),
            readable_refs=frozenset({"ordini_vendita.data_ordine",
                                     "ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertEqual(catalogue.time_anchor,
                         {"ref": "ordini_vendita.data_ordine"})

    def test_no_date_exposed_is_no_anchor(self):
        catalogue = build.build(
            self._dictionary(), entity="ordini_vendita",
            attributes=[Attribute(name="importo_totale", label="Totale",
                                  type="number", in_default_views=True)],
            readable_refs=frozenset({"ordini_vendita.importo_totale"}),
            context_window=32_000)
        self.assertIsNone(catalogue.time_anchor)
```

- [ ] **Step 2: Eseguirlo e vederlo fallire**

Run: `python3 tools/pure/run.py`
Expected: FAIL con `AttributeError: 'Catalogue' object has no attribute 'time_anchor'`

- [ ] **Step 3: Implementare**

In `custom_addons/nli_semantics/catalogue/build.py`, aggiungere l'import accanto agli altri:

```python
from . import anchor as anchor_module
from .exposure import Attribute, Budget, Decision, attribute_budget, exposed, within_budget
```

Aggiungere il campo in fondo alla dataclass `Catalogue`, dopo `exposure_rules`:

```python
    #: Dove si attacca un'espressione temporale che non nomina un campo (**D110**).
    #: Calcolata dagli attributi sopravvissuti a diritti e budget, mai da quelli in
    #: ingresso: un'ancora che nominasse una data non leggibile sarebbe una seconda
    #: via alla stessa informazione, senza le stesse guardie.
    time_anchor: dict | None = None
```

In `build()`, dopo il blocco che costruisce `catalogue_attributes` e prima di `# --- 3. categories`:

```python
    # --- 2b. l'ancora del tempo, dagli attributi rimasti (D110) -------------
    time_anchor = anchor_module.time_anchor(
        anchor_module.date_refs(catalogue_attributes))
```

E nel `return Catalogue(...)`, aggiungere l'argomento dopo `exposure_rules=...`:

```python
        time_anchor=time_anchor,
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `python3 tools/pure/run.py`
Expected: PASS. I test puri salgono di 3 (401 → 404).

- [ ] **Step 5: Verifica completa**

Run: `./manage.sh check`
Expected: tutto verde, contratto e corpus 948/948 invariati.

- [ ] **Step 6: Commit**

```bash
git add custom_addons/nli_semantics/catalogue/build.py \
        custom_addons/nli_semantics/pure_tests/test_catalogue.py
git commit -m "D110 (2/3): il catalogo porta l'ancora del tempo

Calcolata dopo il filtro dei permessi e il budget, mai dagli attributi in
ingresso: un'ancora che nominasse una data non leggibile sarebbe una seconda
via alla stessa informazione senza le stesse guardie. Il test che lo mostra
toglie un attributo dai readable_refs e verifica che sparisca dall'ancora.

3 test puri."
```

---

## Task 3: Il payload e le due regole del prompt (D110, D111)

**Files:**
- Modify: `custom_addons/nli_engine/prompt.py`
- Test: `custom_addons/nli_engine/pure_tests/test_interpreter.py`

**Interfaces:**
- Consumes: `catalogue.time_anchor` dal Task 2.
- Produces: la chiave `"time_anchor"` nel payload restituito da `catalogue_payload(catalogue)`.

- [ ] **Step 1: Scrivere il test che fallisce**

In `custom_addons/nli_engine/pure_tests/test_interpreter.py`, aggiungere `time_anchor` allo stub `Catalogue` esistente:

```python
class Catalogue:
    entity = "clienti"
    attributes = (Attribute("clienti.citta", ("città", "comune")),)
    categories = (Category("clienti.attivi", ("attivi", "operativi")),)
    entity_names = (("clienti", ("clienti", "anagrafiche")),)
    time_anchor = None
```

E aggiungere questa classe di test:

```python
class TestTimeAnchorInThePrompt(unittest.TestCase):
    """Il modello deve sapere dove si attacca un periodo (D110) e che non puo'
    lasciarlo cadere (D111)."""

    def test_the_payload_carries_the_anchor(self):
        catalogo = Catalogue()
        catalogo.time_anchor = {"ref": "clienti.creato_il"}
        self.assertEqual(catalogue_payload(catalogo)["time_anchor"],
                         {"ref": "clienti.creato_il"})

    def test_an_absent_anchor_travels_as_null_not_as_a_missing_key(self):
        """Una chiave assente e una chiave nulla sono due cose diverse per chi
        legge: la prima si puo' scambiare per una versione vecchia del catalogo,
        la seconda dice esplicitamente che date non ce ne sono."""
        payload = catalogue_payload(Catalogue())
        self.assertIn("time_anchor", payload)
        self.assertIsNone(payload["time_anchor"])

    def test_the_instructions_say_where_a_period_attaches(self):
        message = system_message(Request(utterance="x", catalogue={}))
        self.assertIn("time_anchor", message)

    def test_the_instructions_forbid_dropping_a_period(self):
        """La regola che conta: oggi lasciar cadere un pezzo di frase non costa
        niente al modello, perche' la busta resta valida lo stesso."""
        message = system_message(Request(utterance="x", catalogue={}))
        self.assertIn("NEVER drop a time expression", message)
```

- [ ] **Step 2: Eseguirlo e vederlo fallire**

Run: `python3 tools/pure/run.py`
Expected: FAIL con `KeyError: 'time_anchor'`

- [ ] **Step 3: Implementare**

In `custom_addons/nli_engine/prompt.py`, dentro `INSTRUCTIONS`, subito dopo la riga `- never resolve a date. "this month" is {"kind":"temporal","expression":"current_month"};` inserire:

```
- a time expression that names no attribute is a condition on the catalogue's
  "time_anchor". If it declares "ref", the condition is on that attribute. If it
  declares "choices", the sentence does not say which date it means: answer with a
  clarification whose options are those dates. If it is null, this entity exposes no
  date at all: answer with a clarification;
- NEVER drop a time expression. If you cannot place it, ask. A sentence that names a
  period and an answer that does not is a wrong answer, not a shorter one;
```

E in `catalogue_payload`, aggiungere la chiave dopo `"entity": catalogue.entity,`:

```python
        # D110: dove si attacca un periodo che non nomina un campo. Viaggia sempre,
        # anche nulla: una chiave assente si scambia per un catalogo vecchio, una
        # chiave nulla dice che date non ce ne sono.
        "time_anchor": catalogue.time_anchor,
```

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `python3 tools/pure/run.py`
Expected: PASS. Test puri 404 → 408.

- [ ] **Step 5: Commit**

```bash
git add custom_addons/nli_engine/prompt.py \
        custom_addons/nli_engine/pure_tests/test_interpreter.py
git commit -m "D110 e D111 (3/3): il prompt dice dove si attacca un periodo

Due regole. La prima da' l'appiglio: un'espressione temporale che non nomina
un attributo e' una condizione sull'ancora del catalogo, e se l'ancora non e'
unica la risposta e' un chiarimento. La seconda toglie l'uscita di sicurezza:
oggi lasciar cadere un pezzo di frase non costa niente al modello, perche' la
busta senza quella condizione resta valida.

L'ancora viaggia sempre, anche nulla: una chiave assente si scambia per un
catalogo vecchio, una chiave nulla dice che date non ce ne sono.

4 test puri."
```

---

## Task 4: Le categorie ammesse sono quelle nominate (D112)

**Files:**
- Modify: `custom_addons/nli_engine/prompt.py` (`catalogue_references`)
- Modify: `custom_addons/nli_engine/interpreter.py` (`interpret`)
- Test: `custom_addons/nli_engine/pure_tests/test_interpreter.py`

**Interfaces:**
- Consumes: niente dai task precedenti.
- Produces: `catalogue_references(payload, *, utterance="", mentions=None) -> References` e `interpret(adapter, *, utterance, catalogue, state=None, mentions=None, max_repairs=1)`. `mentions` e' un callable `(ref: str, text: str) -> bool`; assente, il restringimento non si applica.

- [ ] **Step 1: Scrivere il test che fallisce**

In `custom_addons/nli_engine/pure_tests/test_interpreter.py`, aggiungere:

```python
class SpiaDelloSchema(RecordedAdapter):
    """Registra gli schemi ricevuti: il restringimento di D112 e' invisibile nella
    risposta e visibile solo nell'alfabeto che il modello ha ricevuto."""

    def __init__(self, replies, **kwargs):
        super().__init__(replies, **kwargs)
        self.schemas = []

    def complete(self, request, *, schema=None):
        self.schemas.append(schema)
        return super().complete(request, schema=schema)


class TestCategoryNarrowing(unittest.TestCase):
    """Una categoria che la frase non nomina non deve essere scrivibile (D112).

    D112 e' la decisione per cui le categorie ammesse dalla generazione vincolata
    sono quelle nominate dalla frase, non tutte quelle del catalogo.
    """

    def _refs_ammessi(self, schema) -> str:
        """Lo schema intero come testo: basta a dire se un riferimento e' citabile."""
        return json.dumps(schema)

    def test_a_category_the_sentence_does_not_name_is_not_admitted(self):
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: False)
        self.assertNotIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_a_category_the_sentence_names_stays_admitted(self):
        """L'altra meta': un restringimento che toglie tutto non e' un
        restringimento, e' un guasto."""
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti attivi",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: "attivi" in text)
        self.assertIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_without_a_matcher_nothing_is_narrowed(self):
        """Come `validate_grounding`, che senza `mentions` non controlla: i test
        puri del motore girano senza dizionario, e il motore non puo' importarlo."""
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="qualunque cosa", catalogue=Catalogue())
        self.assertIn("clienti.attivi", self._refs_ammessi(spia.schemas[0]))

    def test_the_attributes_are_never_narrowed(self):
        """Solo le categorie. Un attributo si nomina da se' nella frase — «con
        importo oltre 500» — e restringerlo toglierebbe le colonne e i
        raggruppamenti, che nella frase compaiono altrove."""
        spia = SpiaDelloSchema([VALID])
        interpret(spia, utterance="voglio vedere i clienti",
                  catalogue=Catalogue(),
                  mentions=lambda ref, text: False)
        self.assertIn("clienti.citta", self._refs_ammessi(spia.schemas[0]))
```

- [ ] **Step 2: Eseguirlo e vederlo fallire**

Run: `python3 tools/pure/run.py`
Expected: FAIL — `interpret()` non accetta `mentions`, `TypeError: interpret() got an unexpected keyword argument 'mentions'`

- [ ] **Step 3: Implementare in `prompt.py`**

Sostituire la firma e il corpo di `catalogue_references`:

```python
def catalogue_references(payload: dict, *, utterance: str = "",
                         mentions=None) -> schema_module.References:
    """The references this catalogue admits, kept apart by genus (D101, D102).

    Read from the payload rather than from the catalogue object because the payload is
    exactly what the model was shown: a reference admitted by the schema and absent
    from the message would be a reference the model is allowed to emit and has no way
    to know, which is worse than either.

    The entity of the turn travels with the other entities: `set_target` may change
    the subject, and a catalogue that admitted only the current one would make the
    change unexpressible.

    **D112 — the categories are narrowed to what the sentence names.** A named
    condition is the only condition whose reference the sentence does not have to
    spell: no field, no value, no type. Measured on 80 openings, that made it the
    place every fragment the model could not place ended up — *«prelievi»*, the name
    of the entity itself, became *«in bozza»*. Since the utterance is known before the
    schema is built, a category the sentence does not mention can be made
    **inexpressible** rather than refused afterwards.

    `mentions` is injected, never imported: deciding what counts as *mentioning* a
    term belongs to the dictionary, which knows about accents, typos and
    abbreviations, and `nli_engine` does not depend on `nli_semantics` (§6.3).
    Omitted, nothing is narrowed — the same shape `validate_grounding` already has,
    and what lets the engine's pure tests run without a dictionary.

    Only the categories. An attribute names itself in the sentence — *«con importo
    oltre 500»* — and narrowing those would take away the columns and the groupings,
    which the sentence names somewhere else entirely.
    """
    entities = {payload["entity"], *(entity["ref"] for entity in payload["entities"])}
    categories = tuple(sorted(category["ref"] for category in payload["categories"]))
    if mentions is not None:
        categories = tuple(ref for ref in categories if mentions(ref, utterance))
    return schema_module.References(
        entities=tuple(sorted(ref for ref in entities if ref)),
        attributes=tuple(sorted(attribute["ref"] for attribute in payload["attributes"])),
        categories=categories,
        # D103: the type each attribute carries in the catalogue is the one §8.1 pairs
        # with its predicates. An attribute whose type the catalogue does not declare
        # is simply absent here, and keeps the whole predicate set.
        types={attribute["ref"]: attribute["type"]
               for attribute in payload["attributes"] if attribute.get("type")},
    )
```

- [ ] **Step 4: Implementare in `interpreter.py`**

Cambiare la firma di `interpret`:

```python
def interpret(adapter, *, utterance: str, catalogue, state: dict | None = None,
              mentions=None, max_repairs: int = 1) -> Interpretation:
```

Aggiungere al docstring, dopo il paragrafo su `max_repairs`:

```
    `mentions(ref, text)` narrows the admitted categories to those the sentence names
    (**D112**). It is a callable and not a dictionary because `nli_engine` does not
    depend on `nli_semantics` (§6.3); omitted, nothing is narrowed.
```

E cambiare la costruzione dello schema:

```python
    envelope_schema = schema_module.build_envelope_schema(
        refs=catalogue_references(payload, utterance=utterance, mentions=mentions))
```

- [ ] **Step 5: Eseguire i test e vederli passare**

Run: `python3 tools/pure/run.py`
Expected: PASS. Test puri 408 → 412.

- [ ] **Step 6: Verifica dei confini**

Run: `python3 tools/arch/run.py`
Expected: `PASS Imports` — `nli_engine` non deve aver acquisito alcuna dipendenza da `nli_semantics`.

- [ ] **Step 7: Commit**

```bash
git add custom_addons/nli_engine/prompt.py \
        custom_addons/nli_engine/interpreter.py \
        custom_addons/nli_engine/pure_tests/test_interpreter.py
git commit -m "D112: una categoria che la frase non nomina e' inesprimibile

Una condizione nominata e' l'unica il cui riferimento la frase non deve
compitare: niente campo, niente valore, niente tipo. Misurato su 80 aperture,
questo l'ha resa il posto dove finiva ogni frammento che il modello non
sapeva collocare — «prelievi», il nome dell'entita' stessa, diventava «in
bozza».

La frase la conosciamo prima di costruire lo schema, quindi la categoria
infondata smette di essere rifiutata dopo e diventa non scrivibile. Stesso
riconoscitore di D105 (la decisione per cui una condizione nominata dev'essere
fondata nel frammento che la giustifica), passato come argomento perche'
nli_engine non dipende da nli_semantics (04 §6.3).

Solo le categorie: un attributo si nomina da se' nella frase, e restringerlo
toglierebbe colonne e raggruppamenti. D105 resta al livello 3 come rete per
cio' che arriva da altre strade — una query salvata, un'interpretazione
modificata a mano.

4 test puri, fra cui quello che mostra il restringimento non scattare."
```

---

## Task 5: La conduttura passa il riconoscitore

**Files:**
- Modify: `custom_addons/nli_dispatch/runtime/pipeline.py:129-132`
- Test: `custom_addons/nli_dispatch/tests/test_dispatch.py`

**Interfaces:**
- Consumes: `interpret(..., mentions=...)` dal Task 4; `grounding.mentions_of(dictionary)` che la conduttura costruisce già per il livello 3.
- Produces: niente per i task successivi.

- [ ] **Step 1: Scrivere il test che fallisce**

Il banco esiste già: `TestTheChain` (riga 300 di `custom_addons/nli_dispatch/tests/test_dispatch.py`) fa girare la conduttura intera su un dizionario vivo con un fornitore registrato, e `run_pipeline(item, replies)` è il suo helper. Aggiungere il test **dentro quella classe**, così eredita `setUp` e `self.scope`:

```python
    def test_the_pipeline_hands_the_matcher_to_the_interpreter(self):
        """D112 vive nella costruzione dello schema, quindi non si vede nella
        risposta: senza questo passaggio il restringimento sarebbe codice che non
        gira mai, e nessun altro test se ne accorgerebbe."""
        item = self.accept("le aziende di Cittaprova")
        visti = {}
        originale = pipeline_module.interpreter_module.interpret

        def spia(adapter, **kwargs):
            visti.update(kwargs)
            return originale(adapter, **kwargs)

        with patch.object(pipeline_module.interpreter_module, "interpret", spia):
            self.run_pipeline(item, [envelope(target("res_partner"))])

        self.assertIn("mentions", visti,
                      "senza il riconoscitore il restringimento di D112 non si "
                      "applica, e la categoria infondata torna scrivibile")
        self.assertTrue(callable(visti["mentions"]),
                        "dev'essere una funzione e non un dizionario: nli_engine "
                        "non puo' importare nli_semantics (04 §6.3, il confine fra "
                        "il motore e la semantica)")
```

`patch`, `pipeline_module`, `envelope` e `target` sono già importati in testa al file — verificarlo prima di aggiungerne.

- [ ] **Step 2: Eseguirlo e vederlo fallire**

Run: `./manage.sh test nli_test nli_dispatch`
Expected: FAIL con `AssertionError: 'mentions' not found in {...}`

- [ ] **Step 3: Implementare**

In `custom_addons/nli_dispatch/runtime/pipeline.py`, il riconoscitore va costruito **una volta** e usato due volte. Prima della chiamata a `interpret` (riga ~129), inserire:

```python
    # D112 e D105 leggono lo stesso riconoscitore: uno impedisce alla categoria
    # infondata di essere scrivibile, l'altro rifiuta quelle che arrivano da altre
    # strade. Costruirlo due volte significherebbe costruire due indici dei termini
    # nel percorso della richiesta, per la stessa risposta.
    mentions = grounding.mentions_of(semantics.dictionary)
```

Cambiare la chiamata:

```python
    interpretation = interpreter_module.interpret(
        adapter, utterance=utterance, catalogue=catalogue,
        state=state if state.get("target") else None,
        mentions=mentions,
    )
```

E più sotto, nella chiamata a `contextual.validate`, sostituire
`mentions=grounding.mentions_of(semantics.dictionary))` con `mentions=mentions)`,
lasciando il commento che c'è già.

Applicare lo stesso trattamento alla seconda chiamata a `interpret` (riga ~234), verificando prima quale dizionario è in scope in quel punto.

- [ ] **Step 4: Eseguire i test e vederli passare**

Run: `./manage.sh test nli_test`
Expected: PASS, 0 failed di 117 test (116 + 1 nuovo).

- [ ] **Step 5: Commit**

```bash
git add custom_addons/nli_dispatch/runtime/pipeline.py \
        custom_addons/nli_dispatch/tests/test_dispatch.py
git commit -m "D112: la conduttura consegna il riconoscitore all'interprete

Il restringimento vive nella costruzione dello schema, quindi non si vede
nella risposta: senza questo passaggio sarebbe codice che non gira mai, e
nessun test se ne accorgerebbe. Il riconoscitore si costruisce una volta e
serve due volte — D112 prima, D105 dopo — perche' costruirne due significa
due indici dei termini nel percorso della richiesta per la stessa risposta.

1 test Odoo."
```

---

## Task 6: Il generatore smette di fare domande senza risposta

**Files:**
- Modify: `ai/corpus/genera_corpus.py`
- Modify: `ai/corpus/corpus_fondativo.jsonl` (rigenerato, non modificato a mano)

**Interfaces:**
- Consumes: `anchor.time_anchor` dal Task 1, importato via il bootstrap della zona pura.
- Produces: casi di apertura con temporale ambiguo che dichiarano `"esito_atteso": "clarification"`.

- [ ] **Step 1: Capire lo stato di partenza**

Leggere `ai/corpus/genera_corpus.py` righe 540-580 (`_intento`) e 606-621 (`caso_apertura`). Il difetto è a riga 569: `campo = self.rng.choice(spec["temporali"])` sceglie una data a caso, e la frase che ne esce — riga 247, `return c["frase"]` — non nomina il campo. Per `account.move.out_invoice`, `"temporali": ["invoice_date", "invoice_date_due"]`: l'atteso è testa o croce.

Contare quanti casi ne sono affetti prima di toccare niente:

```bash
python3 - <<'PY'
import json
casi = [json.loads(r) for r in open("ai/corpus/corpus_fondativo.jsonl") if r.strip()]
aperture = [c for c in casi if c["tipo"] == "apertura"]
due_date = [c for c in aperture if c["etichette"]["entita"] == "account.move.out_invoice"]
con_tempo = [c for c in due_date
             if any("temporal" in json.dumps(cond)
                    for cond in [c["stato_atteso"].get("filter") or {}])]
print(f"aperture totali {len(aperture)}, su fatture {len(due_date)}, "
      f"con temporale {len(con_tempo)}")
PY
```

Annotare il numero: è il denominatore di quanto cambia.

- [ ] **Step 2: Dare una casa sola alla lista delle date**

Oggi `genera_corpus.CATALOGO` è l'unico posto che sa quali campi di un'entità sono date, e il verificatore non può leggerlo senza importare il generatore. Spostare quella conoscenza in `ai/corpus/riferimenti.py`, che è già il modulo delle mappe condivise fra gli strumenti del corpus:

```python
#: I campi che portano una data, per entita' (D110). Vive qui e non nel generatore
#: perche' lo leggono in tre: il generatore per costruire l'intento, il verificatore
#: per controllare l'attesa, e chiunque misuri. Tre copie di questa lista sono tre
#: occasioni di divergere, e una misura che diverge dal prodotto misura un altro
#: prodotto.
TEMPORALI_PER_ENTITA: dict[str, tuple[str, ...]] = {
    "sale.order": ("date_order",),
    "account.move.out_invoice": ("invoice_date", "invoice_date_due"),
    "res.partner.customer": (),
    "product.template": (),
    "crm.lead": (),
    "stock.picking": ("scheduled_date",),
}
```

> **Prima di scriverlo**, aprire `CATALOGO` in `genera_corpus.py` (riga ~317) e copiare i valori **veri** di ogni `"temporali"`, entità per entità. La tabella qui sopra riporta quelle lette alla stesura del piano; se il generatore ne ha altre, valgono le sue.

In `genera_corpus.py`, ogni voce di `CATALOGO` deve leggere da lì invece di ripetere la lista:

```python
    "account.move.out_invoice": {
        ...
        "temporali": TEMPORALI_PER_ENTITA["account.move.out_invoice"],
        ...
    },
```

- [ ] **Step 3: Scrivere il controllo che fallisce**

Il generatore non ha una suite propria. Il controllo va dove vivono già i controlli del corpus: `ai/corpus/verifica_contratto.py`, che `./manage.sh check` esegue.

Aggiungere la funzione accanto a `verifica_incoerenze`:

```python
def verifica_ancora_del_tempo(casi: list[dict]) -> tuple[int, list[str]]:
    """Un'apertura con un periodo su un'entita' che espone due date non puo'
    attendersi un'operazione (**D110**, l'ancora del tempo dichiarata dal catalogo).

    La frase non contiene l'informazione che l'attesa pretende — quale delle due date
    — e nessuno puo' indovinarla, ne' un modello ne' una persona. L'attesa corretta e'
    un chiarimento.

    Il controllo dichiara quante aperture ha ispezionato: un'ispezione vuota e' un
    fallimento, non un successo silenzioso.
    """
    ispezionate, problemi = 0, []
    for caso in casi:
        if caso["tipo"] != "apertura":
            continue
        entita = caso["etichette"].get("entita")
        ancora = time_anchor([riferimento_attributo(entita, campo)
                              for campo in TEMPORALI_PER_ENTITA.get(entita, ())])
        if not ancora or "choices" not in ancora:
            continue
        ispezionate += 1
        stato = caso.get("stato_atteso") or {}
        ha_periodo = '"kind": "temporal"' in json.dumps(stato, ensure_ascii=False)
        if ha_periodo and caso["esito_atteso"] != "clarification":
            problemi.append(
                f"{caso['id']}: '{caso['testo']}' porta un periodo su {entita}, "
                f"che espone {len(ancora['choices'])} date, e si attende "
                f"'{caso['esito_atteso']}' invece di 'clarification'")
    if not ispezionate:
        problemi.append(
            "nessuna apertura ispezionata su un'entita' con due date: il controllo "
            "sta passando a vuoto")
    return ispezionate, problemi
```

Aggiungere gli import in testa a `verifica_contratto.py`, accanto a quelli che ci sono già:

```python
from nli_semantics.catalogue.anchor import time_anchor  # noqa: E402
from riferimenti import TEMPORALI_PER_ENTITA, riferimento_attributo  # noqa: E402
```

E chiamarla in `main()`, **prima** del ciclo che salta i casi non-`operations` — perché ispeziona proprio quelli che diventeranno chiarimenti. Subito dopo la lettura di `casi`:

```python
    ispezionate, problemi_ancora = verifica_ancora_del_tempo(casi)
    for problema in problemi_ancora:
        esito.errori.append(problema)
```

E nel rapporto, accanto alle altre righe di conteggio:

```python
    print(f"  aperture su entita' con due date  {ispezionate}")
```

- [ ] **Step 4: Eseguirlo e vederlo fallire**

Run: `python3 ai/corpus/verifica_contratto.py`
Expected: FAIL, con un elenco di casi — fra cui `F00466`, `F00857`, `F01091`, che sono quelli visti nella diagnosi.

- [ ] **Step 5: Correggere il generatore**

In `ai/corpus/genera_corpus.py`, `caso_apertura` deve produrre un chiarimento quando l'intento contiene un temporale su un'entità con due o più date. Sostituire il corpo di `caso_apertura`:

```python
    def caso_apertura(self, idx: int) -> dict:
        target = self.rng.choice(list(CATALOGO))
        intento = self._intento(target, self.rng.choice([0, 1, 1, 2, 2, 3]))
        testo = self.verb.frase(intento)
        testo, fen = self.pert.applica(testo)

        # D110: se l'entita' espone piu' di una data e la frase non nomina il campo,
        # l'atteso corretto non e' un'operazione ma una domanda. Prima, il generatore
        # ne pescava una a caso e la teneva per se': l'atteso era testa o croce, e
        # nessuno poteva indovinarlo — ne' un modello ne' una persona.
        ancora = time_anchor([riferimento_attributo(target, campo)
                              for campo in CATALOGO[target]["temporali"]])
        if "choices" in (ancora or {}) and _ha_temporale(intento):
            return {
                "id": f"F{idx:05d}", "tipo": "apertura",
                "esito_atteso": "clarification",
                "testo": testo, "stato_partenza": None,
                "motivo_atteso": (
                    f"il periodo non nomina la data: {target} ne espone "
                    f"{len(ancora['choices'])}, e la frase non dice quale"),
                "riferimenti_necessari": [], "binding_tecnico": {},
                "etichette": {"entita": target, "fenomeni": fen,
                              "difficolta": "difficile"},
            }

        riferimenti = riferimenti_di(intento)
        return {
            "id": f"F{idx:05d}", "tipo": "apertura", "esito_atteso": "operations",
            "testo": testo, "stato_partenza": None,
            "stato_atteso": stato_normativo(intento),
            "riferimenti_necessari": riferimenti,
            "binding_tecnico": binding(target, riferimenti),
            "etichette": {"entita": target, "fenomeni": fen,
                          "difficolta": ["facile", "media", "difficile"][
                              min(2, len(intento["condizioni"]))]},
        }
```

Aggiungere l'helper accanto alle altre funzioni di modulo:

```python
def _ha_temporale(intento: dict) -> bool:
    return any(c["tipo"] == "temporale" for c in intento["condizioni"])
```

E in testa al file, il bootstrap della zona pura e l'import della regola condivisa — **la stessa regola che usa il prodotto**, perché una misura che usa una regola diversa misura un altro prodotto:

```python
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO_ROOT = QUI.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(QUI))

from tools.pure import bootstrap  # noqa: E402
bootstrap.install_all()

from nli_semantics.catalogue.anchor import time_anchor  # noqa: E402
from riferimenti import riferimento_attributo  # noqa: E402
```

> Verificare come `misura_accuratezza.py` fa lo stesso bootstrap (righe ~35-50) e copiarne la forma esatta invece di inventarne una seconda.

- [ ] **Step 6: Rigenerare il corpus**

```bash
python3 ai/corpus/genera_corpus.py
```

- [ ] **Step 7: Verificare**

Run: `./manage.sh check`
Expected: tutto verde. Il numero di casi verificati cambierà rispetto a 948 — **annotare il nuovo numero e riportarlo**, non aggiustarlo.

- [ ] **Step 8: Commit**

```bash
git add ai/corpus/genera_corpus.py ai/corpus/verifica_contratto.py \
        ai/corpus/corpus_fondativo.jsonl
git commit -m "D110: il corpus smette di chiedere cio' che la frase non dice

Il generatore pescava a caso fra data fattura e scadenza (riga 569) e poi
scriveva nella frase solo il periodo (riga 247), perche' una condizione
temporale si verbalizza senza il proprio campo mentre una numerica lo porta
con se'. Su quei casi l'atteso era testa o croce: nessuno poteva fare meglio
del 50%, ne' un modello ne' una persona.

Ora un'apertura con un periodo su un'entita' che espone due date si attende
un chiarimento. La regola che decide quante date espone un'entita' e' la
stessa del prodotto, importata dalla zona pura: una misura che usa una regola
diversa da quella del prodotto misura un altro prodotto.

Il controllo che lo verifica dichiara quante aperture ha ispezionato, e
un'ispezione vuota e' un fallimento."
```

---

## Task 7: Il livello 3 dentro lo strumento di misura

**Files:**
- Modify: `ai/corpus/misura_accuratezza.py`

**Interfaces:**
- Consumes: `contextual.validate`, `grounding.mentions_of`.
- Produces: una riga nel rapporto con i rifiuti per fondatezza.

- [ ] **Step 1: Capire cosa manca**

`interpret()` esegue i livelli 1-2 e la coerenza, mai il livello 3 — che è dove vive il controllo di fondatezza di **D105**. Lo strumento di misura chiama `interpret` e poi `applicator.apply`, quindi non ha mai visto quel controllo. È il motivo per cui «D105 rende i fallimenti visibili senza spostare il punteggio»: il punteggio non li ha mai visti.

Con D112 in vigore il livello 3 non dovrebbe quasi più scattare sulle condizioni nuove. Se scatta, è un'informazione: vuol dire che il riconoscitore usato per restringere e quello usato per verificare non stanno dando la stessa risposta.

- [ ] **Step 2: Implementare**

In `ai/corpus/misura_accuratezza.py`, aggiungere agli import:

```python
from nli_core.validation import contextual  # noqa: E402
from nli_semantics.dictionary import grounding  # noqa: E402
```

Aggiungere un contatore in `Accuratezza`:

```python
        #: Rifiuti del livello 3 per condizione nominata infondata (D105). Con D112
        #: in vigore dovrebbero essere zero: se non lo sono, il riconoscitore che
        #: restringe e quello che verifica non danno la stessa risposta.
        self.infondate: int = 0
```

In `misura()`, dopo `applicator.apply` e prima del confronto, aggiungere:

```python
        fallimenti = contextual.validate(
            prodotto, known_refs=catalogo.refs,
            types={a.ref: a.type for a in catalogo.attributes},
            mentions=grounding.mentions_of(dizionario))
        if any(f.code == "ungrounded_category" for f in fallimenti):
            esito.infondate += 1
```

E nel `rapporto()`, accanto alla riga delle riparazioni:

```python
    print(f"  condizioni infondate    {esito.infondate}  "
          f"{esito.infondate / esito.casi:.1%} dei casi  (D105, atteso 0 con D112)")
```

La firma è stata verificata alla stesura del piano, in `custom_addons/nli_core/validation/contextual.py:216`:

```python
def validate(state, *, known_refs, types, category_costs=None, mentions=None,
             limits=DEFAULT_LIMITS) -> list[Failure]
```

`catalogo.refs` è la proprietà di `Catalogue` che raccoglie ogni riferimento nominabile (entità, attributi, categorie, nomi di entità) e restituisce un `frozenset`, che è esattamente ciò che `known_refs` vuole. `Failure` porta `.code`, ed è il campo su cui si riconosce `ungrounded_category`.

- [ ] **Step 3: Verificare senza il modello**

Lo strumento richiede il modello per girare. Verificare solo che importi e che la firma regga, senza chiamare `ollama`:

```bash
python3 -c "import sys; sys.path.insert(0,'ai/corpus'); import misura_accuratezza; print('import OK')"
```
Expected: `import OK`

- [ ] **Step 4: Commit**

```bash
git add ai/corpus/misura_accuratezza.py
git commit -m "il metro esegue il livello 3, cosi' il numero riflette D105

interpret() esegue i livelli 1-2 e la coerenza, mai il livello 3: lo
strumento di misura non aveva quindi mai visto il controllo di fondatezza.
Era il motivo per cui D105 'rende i fallimenti visibili senza spostare il
punteggio' — il punteggio non li ha mai visti.

Con D112 il contatore dovrebbe restare a zero. Se non lo e', il riconoscitore
che restringe e quello che verifica non danno la stessa risposta, ed e'
un'informazione che vogliamo vedere."
```

---

## Task 8: Le tre decisioni nel registro

**Files:**
- Modify: `ai/00-registro-decisioni.md`
- Modify: `ai/restart.md`

**Interfaces:**
- Consumes: gli esiti dei task 1-7, con i loro numeri veri.
- Produces: §21 del registro, e il punto di ripresa aggiornato.

- [ ] **Step 1: Aggiungere le tre righe alla tabella delle decisioni**

Accanto alla riga di **D109**, nello stesso formato:

```markdown
| **D110** | Il catalogo dichiara **l'ancora del tempo**: una data se ne espone una sola, l'insieme delle scelte se sono due o piu', nulla se non ce ne sono | ☑ Adottata | §21.1. Un'espressione temporale non nomina mai il proprio campo, ne' nel corpus ne' in italiano. Nessuna euristica su quale data conti di piu': sceglierne una fra due plausibili e' indovinare |
| **D111** | Un'espressione temporale **non puo' essere lasciata cadere**: se non si colloca, si chiede | ☑ Adottata | §21.2. Oggi lasciar cadere un pezzo di frase non costa niente al modello, perche' la busta senza quella condizione resta valida |
| **D112** | Le categorie ammesse dalla generazione vincolata sono quelle **nominate dalla frase** | ☑ Adottata | §21.3. `is_category` e' l'unica condizione senza appiglio lessicale, e per questo era la discarica di ogni frammento non collocabile. La frase si conosce prima dello schema, quindi la categoria infondata diventa inesprimibile invece che rifiutata dopo |
```

- [ ] **Step 2: Aggiornare la nota sulla numerazione**

Sostituire `**Per aggiungere una decisione**: numerazione in continuità da **D110**.` con:

```markdown
**Per aggiungere una decisione**: numerazione in continuità da **D113**. **D110**, **D111** e **D112** sono deliberate in §21, dalla proposta `14`.
```

- [ ] **Step 3: Scrivere §21**

In fondo al registro, una sezione per decisione, ognuna con: il difetto misurato, l'opzione che non toccava il contratto e perché è stata scartata, cosa cambia e cosa **non** cambia, e i numeri veri dei test. Il modello di riferimento è §19 e §20: si scrive perché una decisione è stata presa, non cosa fa il codice.

**Regola per chi scrive:** ogni sigla citata porta fra parentesi cosa tratta, e la glossa si verifica aprendo la riga del registro. Non si ricorda.

**Numeri da riportare per come sono usciti**, non come previsti: test puri prima e dopo, test Odoo prima e dopo, casi del corpus prima e dopo, e il conteggio delle aperture diventate chiarimenti.

- [ ] **Step 4: Aggiornare `ai/restart.md`**

Nella sezione «Aperto, in ordine di quanto sblocca», il punto 3 (`filter` al 73,6%) va riscritto: le due famiglie diagnosticate sono state affrontate, e restano le altre — il predicato possibile ma sbagliato, il valore preso male, le due condizioni fuse in una. Aggiungere che la rimisura non è ancora stata fatta.

- [ ] **Step 5: Verifica finale**

```bash
./manage.sh check && ./manage.sh test nli_test
```
Expected: entrambi verdi. Riportare i due conteggi finali.

- [ ] **Step 6: Commit**

```bash
git add ai/00-registro-decisioni.md ai/restart.md
git commit -m "D110, D111, D112 deliberate — 00 §21

Le tre decisioni della proposta 14, con i numeri veri delle verifiche e il
punto di ripresa allineato."
```

---

## Cosa resta fuori da questo piano, e perché

**La rimisura.** È il passo 5 di `14` §8 e va fatta **dopo**, con la riga di comando di `restart.md`. Misurare a metà strada produce un numero che non descrive né il prima né il dopo.

**Le altre famiglie di `filter`.** Il predicato possibile ma sbagliato, il valore preso male, le due condizioni fuse in una. Questo piano non le tocca e non pretende di farlo: `14` §7 lo dice esplicitamente.

**`within` e `between`.** Deliberato di lasciarli come sono.

**L'aspettativa sul punteggio.** Va detta prima di misurare, così non la si aggiusta dopo: **l'accuratezza complessiva può scendere.** Le risposte sbagliate diventano domande, e il corpus conta una domanda come un fallimento di `operations`. Il numero che deve migliorare è un altro — quanti filtri sbagliati escono con l'aria di essere giusti — e i suoi indicatori sono le condizioni infondate del Task 7 e i chiarimenti prodotti.
