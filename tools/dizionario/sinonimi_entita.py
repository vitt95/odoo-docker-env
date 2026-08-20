"""I nomi che una persona da' a un'entita' e che l'installazione non scrive da nessuna
parte.

## Il difetto che questo file esiste per togliere

Misurato il 20 agosto 2026, banca dati vera, conversazione 964:

    «mostrami le vendite con totale superiore a 2000»  ->  not_understood

La fase A non riconosceva **niente**. I nomi di `sale_order` si raccolgono
dall'installazione (**D126**, la decisione per cui le parole di un'entita' si prendono
dall'etichetta, dalle azioni e dalle voci di menu invece di inventarle), e la raccolta
aveva trovato questi:

    Ordine di vendita, Ordini di vendita, Ordini, Preventivi,
    I miei preventivi, Ordini da fatturare, Ordini per incremento vendite

*Vendite* da sola non c'e'. Compare dentro *Ordini per incremento vendite*, ma il
confronto vuole finestre di parole contigue: `vendite` da solo non aggancia niente.

## Perche' la raccolta non poteva trovarla, ed e' giusto cosi'

`l0.py` lega un nome a un modello **attraverso l'azione che il menu apre**. Il menu
radice *Vendite* non ha azione: sotto ci stanno Ordini, Prodotti, Clienti e Analisi,
cioe' quattro modelli diversi. Guardando l'installazione, *«vendite»* non ha **una**
risposta — e una raccolta che ne scegliesse una a caso sarebbe il ripiego silenzioso che
`ai/restart` §4 chiama il terzo modo di mentire.

Una persona invece lo sa. **E' esattamente il confine fra cio' che si raccoglie e cio'
che si scrive a mano**, e questo file e' il posto del secondo.

## Perche' una parola sola

Perche' e' l'unica **misurata**. Le altre candidate — *acquisti*, *fatturato*,
*anagrafiche* — sono plausibili e non provate, e un sinonimo sbagliato e' peggio di uno
mancante: la parola che manca produce un rifiuto onesto e visibile, quella sbagliata
produce una risposta sicura e sbagliata (**D29**, la decisione che esiste per rendere
impossibile la modalita' di guasto che non da' errori ma numeri plausibili). Il resto
arriva con il rilevatore di collisioni, non prima.

## Come si esegue

    ./manage.sh dizionario db          scrive le voci
    ./manage.sh dizionario db prova    dice cosa scriverebbe, senza scrivere
"""

import os

#: Le parole che una persona usa per **nominare un'entita'**, e che nessuna etichetta,
#: azione o voce di menu di questa installazione contiene.
#:
#: Sono livello **L1**: italiano, non gergo di un cliente. Che le vendite si chiamino
#: cosi' non dipende da chi ha comprato il prodotto — dipende dalla lingua. Il gergo di
#: una singola azienda (*«commessa»* per un ordine) e' **L2** e resta nella sua tabella:
#: spedirlo dentro uno strumento comune vorrebbe dire imporre a tutti le parole di uno.
FORME = {
    "sale_order": ("vendite",),
}


def esegui(env, prova=False):
    semantica = env["nli.semantics"]
    scope = semantica.entity_scope()
    semantiche = semantica.semantics(scope)
    registro = env["nli.dictionary.entry"].sudo()

    scritte, gia_presenti, fuori_perimetro = 0, 0, 0
    for entita, forme in sorted(FORME.items()):
        # Fuori perimetro non e' un errore: chi non ha installato le vendite non deve
        # vedersi scrivere le loro parole, e chi le installa domani rilancia il comando.
        if entita not in semantiche.entity_refs:
            fuori_perimetro += 1
            print(f"    fuori perimetro  {entita}")
            continue
        esistente = registro.with_context(active_test=False).search(
            [("entry_type", "=", "T1"), ("ref", "=", entita), ("level", "=", "L1")],
            limit=1)
        if esistente:
            gia_presenti += 1
            print(f"    gia' presente    {entita}")
            continue
        print(f"    {'scriverebbe' if prova else 'scritta    '}  {entita:<20} "
              f"{', '.join(forme)}")
        if not prova:
            registro.create({
                "entry_type": "T1",
                "level": "L1",
                "ref": entita,
                "entity_ref": entita,
                "terms": "\n".join(forme),
            })
            scritte += 1

    if prova:
        env.cr.rollback()
        print(f"\n    prova: {scritte} da scrivere, {gia_presenti} gia' presenti, "
              f"{fuori_perimetro} fuori perimetro, niente scritto\n")
    else:
        env.cr.commit()
        print(f"\n    {scritte} voci scritte, {gia_presenti} gia' presenti, "
              f"{fuori_perimetro} fuori perimetro\n")
    return scritte


esegui(
    env,  # noqa: F821 — la shell di Odoo lo mette lei
    prova=os.environ.get("DIZIONARIO_PROVA") == "1",
)
