"""I pacchetti di parole per modulo, e la regola che decide se una parola si scrive.

Questo file e' **puro**: non importa Odoo, non tocca un database, e sta qui perche' la
parte che decide dev'essere provabile senza accendere niente. Lo script che scrive —
`sinonimi_entita.py` — gli passa cio' che ha letto dall'installazione e fa quello che
questo modulo dice.

## Perche' per modulo

Le parole di un'entita' hanno senso solo dove quell'entita' esiste. Chi non ha
installato le vendite non deve vedersi scrivere le loro parole: sarebbero righe morte
nel registro, e ogni riga morta e' un termine in piu' che l'indice confronta a ogni
frase. Il taglio per modulo Odoo e' quello che l'installazione dichiara gia' da sola.

## Perche' i pacchetti sono quasi vuoti, ed e' una misura e non una pigrizia

Il 21 agosto 2026 sono state passate alla fase A le **45 frasi distinte** che il
prodotto aveva davvero ricevuto. Ne riconosceva 36. Le altre 9 — *«solo quelli vinti»*,
*«ordinameli per email»*, *«Data creazione»* — non nominano nessuna entita': sono
raffinamenti, e la fase A muta li' e' il comportamento voluto (D127).

Dopo aver aggiunto *vendite*, **nessuna frase vera resta senza entita' per colpa di una
parola mancante**. Riempire i pacchetti adesso vorrebbe dire inventare: e un sinonimo
sbagliato e' peggio di uno mancante, perche' la parola che manca produce un rifiuto
onesto e visibile mentre quella sbagliata produce una risposta sicura e sbagliata
(**D29**). Il meccanismo sta qui pronto; le parole entrano quando una misura le chiede.

**E non si prendono dal corpus fondativo.** Il corpus parla d'ufficio — *anagrafiche*,
*giacenza*, *prelievi*, *comune* — ed e' allettante copiarle di la'. Sarebbe il modo
piu' rapido di rovinare l'unico esame indipendente che abbiamo (`ai/18` §5bis): un
modello misurato su parole che gli abbiamo insegnato apposta non e' piu' misurato.
"""

from __future__ import annotations

#: Le parole scritte a mano, per **modulo Odoo** e poi per entita'.
#:
#: Livello **L1**: italiano, uguale ovunque. Il gergo di una singola azienda —
#: *«commessa»* per un ordine — e' **L2** e resta nella tabella di quel cliente:
#: spedirlo dentro uno strumento comune vorrebbe dire imporre a tutti le parole di uno.
PACCHETTI: dict[str, dict[str, tuple[str, ...]]] = {
    # *Vendite* e' il menu radice dell'applicazione, e non ha azione: sotto ci stanno
    # Ordini, Prodotti, Clienti e Analisi. La raccolta di D126 non poteva sceglierne
    # una, una persona si'. E' il caso che ha aperto tutto (`00` §49).
    "sale": {"sale_order": ("vendite",)},
    "crm": {},
    "account": {},
    "stock": {},
    "hr": {},
    "product": {},
    "contacts": {},
}


def collisione(termine: str, *, ref: str, gia_noti: dict[str, str]) -> str | None:
    """Chi altro rivendica gia' questa parola, o `None` se e' libera.

    `gia_noti` sono i termini che l'installazione conosce, gia' normalizzati, con il
    riferimento a cui portano.

    **Perche' non si scrive e basta.** A frase fatta il prodotto se la cava da solo: due
    entita' che pareggiano sullo stesso pezzo finiscono sotto il margine e diventano un
    **chiarimento** (D33), che e' la risposta giusta e costa 0,08 s se l'utente clicca
    un'opzione (D121). Il problema non e' il comportamento, e' che una parola scritta a
    mano che rende ambiguo cio' che prima era certo e' una **decisione**, e nessuno la
    sta prendendo: si scopre mesi dopo come un peggioramento senza autore.

    Quindi qui la si nomina e non la si scrive. Chi la vuole davvero la mette nei
    pacchetti sapendo che cosa rende ambiguo.
    """
    posseduta = gia_noti.get(termine.strip().casefold())
    if posseduta is None or posseduta == ref:
        return None
    return posseduta


def da_scrivere(pacchetto: dict[str, tuple[str, ...]], *, entita_nel_perimetro,
                gia_noti: dict[str, str]):
    """Le voci scrivibili di un pacchetto, e le due liste di scarti con il motivo.

    Torna `(scrivibili, fuori_perimetro, collisioni)`. Nessun controllo passa vuoto: chi
    chiama stampa tutte e tre le liste, e un pacchetto che non scrive niente lo dice.
    """
    scrivibili, fuori_perimetro, collisioni = [], [], []
    for ref, termini in sorted(pacchetto.items()):
        if ref not in entita_nel_perimetro:
            fuori_perimetro.append(ref)
            continue
        tenuti = []
        for termine in termini:
            proprietario = collisione(termine, ref=ref, gia_noti=gia_noti)
            if proprietario:
                collisioni.append((termine, ref, proprietario))
            else:
                tenuti.append(termine)
        if tenuti:
            scrivibili.append((ref, tuple(tenuti)))
    return scrivibili, fuori_perimetro, collisioni
