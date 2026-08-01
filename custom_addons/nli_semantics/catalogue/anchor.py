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
