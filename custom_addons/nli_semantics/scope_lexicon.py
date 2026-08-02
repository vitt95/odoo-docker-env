"""Le parole con cui si chiede una cosa che AIDA non sa fare (**D119**).

**Zona pura.**

## Perche' esiste

**D118** ha reso il rifiuto per portata una cosa che si guadagna: chi rifiuta deve
citare il pezzo di frase che chiede l'impossibile. Il controllo pero' verificava solo
che il frammento **ci fosse**, non che **dicesse** quella cosa — e un modello puo'
citare un pezzo qualunque della frase. Questo modulo e' la meta' che mancava.

## Perche' sta qui e non nel contratto

Il lessico e' di lingua: *«cancella»*, *«elimina»*, *«manda una mail»*. `nli_core` non
ha lingua **per costruzione** — e' la ragione per cui il controllo di fondatezza di
**D105** riceve il riconoscitore come argomento invece di importarlo. Mettere qui delle
parole italiane dentro il nucleo avrebbe rotto quella proprieta' per comodita'.

## Cosa non e'

Non e' un riconoscitore di intenzioni. Non decide se l'utente vuole cancellare qualcosa:
decide se **il frammento che il modello ha citato** contiene le parole con cui quella
cosa si chiede. La differenza conta — la prima domanda e' aperta, la seconda si risponde
confrontando due elenchi, ed e' l'unica che un controllo puo' porre onestamente.
"""

from __future__ import annotations

import unicodedata
from typing import Callable

#: Per ogni categoria di §11.4, le parole con cui si chiede quella cosa.
#:
#: Radici e non parole intere: *«cancell»* copre cancella, cancellare, cancellazione,
#: cancellale. Una lista di forme flesse sarebbe sempre incompleta di una, e la forma
#: mancante sarebbe un rifiuto che passa.
RADICI: dict[str, tuple[str, ...]] = {
    "cancellazione_record": (
        "cancell", "elimin", "rimuov", "cestin", "butta", "svuota",
    ),
    "creazione_record": (
        "crea", "creare", "aggiung", "inseris", "registra", "nuovo", "nuova",
        "genera",
    ),
    "modifica_dati": (
        "modific", "aggiorn", "cambia", "cambiare", "corregg", "imposta",
        "assegna", "rinomin", "sposta", "scrivi",
    ),
    "invio_esterno": (
        "invia", "inviare", "manda", "mandare", "spedis", "email", "e-mail",
        "mail", "notific", "condivid", "esporta",
    ),
    "previsione": (
        "prevedi", "prevision", "prevedere", "stima", "stimare", "proietta",
        "proiezion", "quanto vender", "andra", "andranno", "futur",
    ),
}


def _normalizza(testo: str) -> str:
    """Minuscolo e senza accenti: *«cancellera'»* e *«cancellera»* sono la stessa parola.

    La stessa indulgenza che il riconoscitore del dizionario usa per i termini (D83):
    chi scrive di fretta non mette gli accenti, e un controllo che si fa ingannare da
    un accento non protegge niente.
    """
    piatto = unicodedata.normalize("NFKD", testo or "")
    return "".join(c for c in piatto if not unicodedata.combining(c)).lower()


def justifies(scope_note: str, fragment: str) -> bool:
    """Se il frammento citato contiene le parole di quella categoria.

    Una categoria che non conosciamo passa: questo controllo esiste per **restringere**
    le uscite note, e un vocabolario incompleto non deve trasformarsi in un rifiuto di
    rifiutare. Se un domani `SCOPE_NOTES` cresce senza che qui si aggiunga la voce, il
    peggio che succede e' che quella categoria torna com'era prima di D119.
    """
    radici = RADICI.get(scope_note)
    if radici is None:
        return True
    testo = _normalizza(fragment)
    if not testo.strip():
        return False
    return any(radice in testo for radice in radici)


def justifies_of(_dictionary=None) -> Callable[[str, str], bool]:
    """La funzione da iniettare, con la stessa forma di `grounding.mentions_of`.

    Prende il dizionario e non lo usa: il lessico e' del **prodotto**, uguale in ogni
    installazione, non dell'installazione. L'argomento c'e' perche' il punto di
    iniezione sia lo stesso degli altri e chi lo chiama non debba ricordare quale dei
    due riconoscitori vuole cosa.
    """
    return justifies
