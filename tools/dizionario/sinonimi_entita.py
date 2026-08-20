"""Scrive nel registro le parole di `pacchetti.py` che l'installazione merita.

Questo file e' la meta' **impura**: legge quali moduli Odoo sono installati, quali
entita' sono nel perimetro e quali termini l'indice conosce gia', poi fa quello che
`pacchetti.py` — che di Odoo non sa niente ed e' provato da solo — gli dice di fare.

Si esegue concatenato a `pacchetti.py`, come `campo` fa con `frasi.py`:

    ./manage.sh dizionario db          scrive le voci
    ./manage.sh dizionario db prova    dice cosa scriverebbe, senza scrivere

## Il difetto che questo file esiste per togliere

Misurato il 20 agosto 2026, banca dati vera, conversazione 964:

    «mostrami le vendite con totale superiore a 2000»  ->  not_understood

La fase A non riconosceva niente, perche' i nomi raccolti da **D126** per `sale_order`
sono *Ordini*, *Preventivi*, *Ordine di vendita* — e *vendite* da sola non c'e'. Non
poteva esserci: il menu radice *Vendite* non ha azione e sotto porta a quattro modelli
diversi, quindi guardando l'installazione quella parola non ha **una** risposta. Una
persona invece lo sa, ed e' il confine fra cio' che si raccoglie e cio' che si scrive.
Tutta la storia sta in `00` §49.
"""

import os


def esegui(env, prova=False):
    semantica = env["nli.semantics"]
    scope = semantica.entity_scope()
    semantiche = semantica.semantics(scope)
    registro = env["nli.dictionary.entry"].sudo()

    installati = set(env["ir.module.module"].sudo().search(
        [("state", "=", "installed")]).mapped("name"))

    # I termini che l'installazione **gia'** conosce, normalizzati come li normalizza
    # l'indice. Servono al rilevatore di collisioni: una parola che porta gia' da
    # un'altra parte non si scrive di nascosto.
    gia_noti = {" ".join(t.tokens): t.ref for t in semantiche.dictionary.term_index().terms}

    scritte = saltate = 0
    for modulo, pacchetto in sorted(PACCHETTI.items()):  # noqa: F821 — concatenato
        if modulo not in installati:
            print(f"    modulo non installato   {modulo}")
            continue
        scrivibili, fuori, collisioni = da_scrivere(  # noqa: F821 — concatenato
            pacchetto, entita_nel_perimetro=set(semantiche.entity_refs),
            gia_noti=gia_noti)

        # **Nessun controllo passa vuoto**: si dice sempre quanto si e' guardato, anche
        # quando non c'e' niente da fare. Un pacchetto vuoto che tace e un pacchetto
        # scritto per intero si assomigliano troppo.
        print(f"    {modulo:<10} {len(pacchetto):2} entita' dichiarate, "
              f"{len(scrivibili)} da valutare, {len(fuori)} fuori perimetro, "
              f"{len(collisioni)} in collisione")
        for termine, ref, proprietario in collisioni:
            saltate += 1
            print(f"      COLLISIONE  «{termine}» chiesta per {ref}, "
                  f"la porta gia' {proprietario} — non scritta")

        for ref, termini in scrivibili:
            esistente = registro.with_context(active_test=False).search(
                [("entry_type", "=", "T1"), ("ref", "=", ref), ("level", "=", "L1")],
                limit=1)
            if esistente:
                print(f"      gia' presente  {ref}")
                continue
            print(f"      {'scriverebbe' if prova else 'scritta    '}  {ref:<18} "
                  f"{', '.join(termini)}")
            if not prova:
                registro.create({
                    "entry_type": "T1", "level": "L1", "ref": ref,
                    "entity_ref": ref, "terms": "\n".join(termini),
                })
                scritte += 1

    if prova:
        env.cr.rollback()
        print(f"\n    prova: {scritte} da scrivere, {saltate} saltate per collisione, "
              f"niente scritto\n")
    else:
        env.cr.commit()
        print(f"\n    {scritte} voci scritte, {saltate} saltate per collisione\n")
    return scritte


esegui(
    env,  # noqa: F821 — la shell di Odoo lo mette lei
    prova=os.environ.get("DIZIONARIO_PROVA") == "1",
)
