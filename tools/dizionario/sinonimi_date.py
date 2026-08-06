"""I sinonimi delle date: le forme verbali che una persona dice e il catalogo non ha.

## Il difetto che questo file esiste per togliere

Batteria intera del 5 agosto 2026, banca dati vera: **18 frasi su 18** della famiglia
`date` finivano in chiarimento, e in tutte e 18 il modello aveva gia' scelto la data
giusta. Il controllo di **D135** (un periodo appoggiato su una data che la frase non
nomina si chiede) chiedeva al riconoscitore se la frase nominasse `crm_lead.create_date`,
e il riconoscitore rispondeva di no:

    names(crm_lead.create_date, "i lead creati questo mese")   ->  False
    names(crm_lead.create_date, "i lead con data creazione")   ->  True

Il catalogo porta l'etichetta Odoo — `Data creazione` — e una persona non dice
*«i lead con data creazione di questo mese»*: dice *«i lead **creati** questo mese»*.
Fra le due c'e' una desinenza, e il riconoscitore non fa morfologia: confronta termini.

## Perche' dei dati e non del codice

Sono **parole**, e le parole di un dizionario stanno in un dizionario: `nli.dictionary.entry`
e' il registro delle voci approvate di D108. Le voci T1 (i nomi di entita' e attributi)
**si fondono** fra i livelli — `06` §2.2 — quindi aggiungere «creati» non toglie
`Data creazione`: la data si potra' chiamare in tutti e due i modi.

Sono al livello **L1**, il dominio: che «creati» sia il participio di «creazione» e'
un fatto della lingua italiana, non di questa installazione. L2 resta per le parole di
un cliente — *«pratiche»* per i lead, per dire.

## Perche' non sono dedotti dall'etichetta

Si potrebbe tagliare `creazione` e attaccare le desinenze. Sarebbe indovinare: da
`Chiusura attesa` uscirebbe «chiuso», che e' un'altra data (`date_closed`). Le forme
qui sotto sono **scritte e lette da una persona**, che e' la stessa ragione per cui
D108 vieta di tradurre da soli il dominio di un filtro salvato.

## Le ambiguita' non sono un problema, e la ragione va detta

«chiusura» finisce per nominare sia `date_closed` (di qui) sia `date_deadline` (che si
chiama `Chiusura attesa`). Bene cosi': la regola di D135 accetta l'ancora presa dalla
frase **solo quando la frase nomina una data sola**. Con due, decide il frammento come
prima, cioe' si chiede. Un sinonimo ambiguo non produce una risposta sbagliata: produce
una domanda.

## Come si esegue

    ./manage.sh dizionario db          # scrive le voci
    ./manage.sh dizionario db prova    # dice cosa scriverebbe, senza scrivere
"""

import os

#: Le forme che una persona usa, per **nome di campo** e non per entita': `create_date`
#: e' lo stesso campo su ogni modello di Odoo, e la lingua non cambia da un'entita'
#: all'altra. Prima riga = quella che si mostra indietro (`06` §2).
FORME = {
    "create_date": ("creazione", "creato", "creata", "creati", "create"),
    "write_date": ("modifica", "modificato", "modificata", "modificati",
                   "modificate", "aggiornato", "aggiornati", "aggiornamento"),
    "date_closed": ("chiusura", "chiuso", "chiusa", "chiusi", "chiuse"),
    "date_open": ("assegnazione", "assegnato", "assegnata", "assegnati", "assegnate"),
    "date_conversion": ("conversione", "convertito", "convertita", "convertiti",
                        "convertite"),
    "date_deadline": ("scadenza", "scade", "scaduto", "scaduti"),
}

#: **Le date degli ordini e delle fatture non sono qui, ed e' una scelta.** Per
#: `sale_order.date_order` verrebbe naturale scrivere «ordinati», che in italiano vuol
#: dire anche *messi in ordine*: una frase come *«gli ordini di questo mese ordinati per
#: totale»* nominerebbe la data senza che nessuno l'abbia nominata, e il periodo ci
#: verrebbe ancorato. E' esattamente il modo di sbagliare che D135 esiste per impedire.
#: Meglio nessun sinonimo che uno che indovina: quelle date restano da chiamare per
#: nome, e la domanda di chiarimento resta l'esito giusto.


def esegui(env, prova=False):
    semantica = env["nli.semantics"]
    scope = semantica.entity_scope()
    semantiche = semantica.semantics(scope)
    registro = env["nli.dictionary.entry"].sudo()

    scritte, gia_presenti = 0, 0
    for chiave in sorted(semantiche.bindings):
        if "." not in chiave:
            continue
        entita, campo = chiave.split(".", 1)
        forme = FORME.get(campo)
        if not forme:
            continue
        esistente = registro.with_context(active_test=False).search(
            [("entry_type", "=", "T1"), ("ref", "=", chiave), ("level", "=", "L1")],
            limit=1)
        if esistente:
            gia_presenti += 1
            print(f"  gia' presente  {chiave}")
            continue
        print(f"  {'scriverebbe' if prova else 'scritta     '}   {chiave:<38} "
              f"{', '.join(forme)}")
        if not prova:
            registro.create({
                "entry_type": "T1",
                "level": "L1",
                "ref": chiave,
                "entity_ref": entita,
                "terms": "\n".join(forme),
            })
        scritte += 1

    if prova:
        env.cr.rollback()
        print(f"\n  prova: {scritte} da scrivere, {gia_presenti} gia' presenti, "
              f"niente scritto\n")
    else:
        env.cr.commit()
        print(f"\n  {scritte} voci scritte, {gia_presenti} gia' presenti\n")
    return scritte


esegui(
    env,  # noqa: F821 — la shell di Odoo lo mette lei
    prova=os.environ.get("DIZIONARIO_PROVA") == "1",
)
