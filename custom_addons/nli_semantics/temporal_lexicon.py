"""Le parole con cui una frase **nomina un periodo** (**D144**).

**Zona pura.**

## Perche' esiste

**D141** ha messo nel contratto i periodi che una frase nomina — *«a gennaio»*, *«nel
primo trimestre»*, *«nel 2025»*. Nella stessa sessione e' arrivato il difetto che quella
decisione portava con se': appena il modello ha avuto `quarter_of_year`, ha risposto
*«nel secondo semestre»* con il **secondo trimestre**, tre giri su tre. Una riga di
prompt che lo vietava per nome non ha retto (§46.7).

La classe di guasto non e' *«manca il semestre»*: e' che **quando la parola manca il
modello ripiega su quella vicina invece di rifiutare**, in silenzio. Aggiungere simboli
finche' non ne mancano piu' non chiude una classe — la chiude una rete.

Questo modulo e' meta' della rete: sa dire, guardando **solo il frammento citato**,
quale periodo quella frase nomina. L'altra meta' e' `validate_temporal_grounding` in
`nli_core`, che confronta cio' che il frammento nomina con cio' che il modello ha
scritto.

## Perche' sta qui e non nel dizionario

`00` §46.7 proponeva il dizionario e i suoi livelli (**D108**, il registro delle voci
approvate). **Non e' il posto giusto, e la ragione e' gia' scritta in `scope_lexicon`**:
il dizionario porta la lingua **dell'installazione** — i sinonimi di un cliente, le
categorie nate dai suoi filtri salvati. *«Gennaio»* e *«trimestre»* non sono di un
cliente: sono italiano, uguale ovunque, e non cambiano mai. Metterli nel dizionario
vorrebbe dire un percorso di approvazione, una coda L3 e una schermata di
amministrazione per delle parole che nessuno approvera' mai diversamente.

Sta qui per la stessa ragione per cui ci sta il lessico di **D119** (la decisione che
pretende che il frammento di un rifiuto contenga le parole di cio' che si rifiuta):
e' lingua del **prodotto**, e `nli_core` non ha lingua per costruzione.

## Cosa non e'

Non capisce il tempo. Non decide quale periodo l'utente intendesse: decide se **il
frammento che il modello ha citato** contiene le parole con cui un periodo si nomina, e
quale. La prima domanda e' aperta, la seconda si risponde confrontando due elenchi — ed
e' l'unica che un controllo puo' porre onestamente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Callable

#: I mesi, per nome intero e in ordine.
#:
#: **Niente abbreviazioni**, ed e' una scelta: *«gen»*, *«mar»*, *«ago»*, *«set»* sono
#: corte abbastanza da comparire dentro parole che non parlano di mesi, e un falso
#: positivo qui rifiuta una risposta giusta. Chi scrive *«a gen»* perde la rete e
#: ottiene il comportamento di prima, che e' il verso giusto in cui sbagliare.
MESI: tuple[str, ...] = (
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
)

#: Le unita' di periodo che una frase puo' nominare con un ordinale, e il simbolo del
#: contratto che le dice. `None` vuol dire **nessun simbolo lo dice**: e' il caso che
#: questa rete esiste per intercettare.
#:
#: Al **singolare** e nient'altro. *«Gli ultimi 3 trimestri»* e' un conteggio di unita'
#: (`last_n_quarters`), non un trimestre nominato, e accettare il plurale trasformerebbe
#: la rete nel difetto che deve impedire.
UNITA: dict[str, str | None] = {
    "trimestre": "quarter_of_year",
    "semestre": "half_of_year",
    "bimestre": None,
    "quadrimestre": None,
    "biennio": None,
    "triennio": None,
    "quinquennio": None,
    "decennio": None,
}

#: Gli ordinali che nominano **quale** unita'. Solo da uno a quattro: oltre non esiste
#: un'unita' che li ammetta.
#:
#: *«Ultimo»*, *«scorso»*, *«questo»* non sono qui di proposito: *«l'ultimo trimestre»*
#: non nomina un trimestre, ne indica uno rispetto a oggi, ed e' cio' che
#: `previous_quarter` e `current_quarter` gia' dicono. Sono la classe di falso positivo
#: piu' probabile, e restano fuori.
ORDINALI: dict[str, int] = {
    "primo": 1, "prima": 1, "1": 1,
    "secondo": 2, "seconda": 2, "2": 2,
    "terzo": 3, "terza": 3, "3": 3,
    "quarto": 4, "quarta": 4, "4": 4,
}

_ORDINALE = "|".join(sorted(ORDINALI, key=len, reverse=True))
_UNITA = "|".join(sorted(UNITA, key=len, reverse=True))

#: *«primo trimestre»*, *«2° semestre»*, *«1 bimestre»*.
_ORDINALE_UNITA = re.compile(
    rf"\b({_ORDINALE})[°ºo]?\s+({_UNITA})\b")
#: *«trimestre 1»*: la stessa cosa detta al contrario.
_UNITA_ORDINALE = re.compile(
    rf"\b({_UNITA})\s+({_ORDINALE})[°ºo]?\b")
#: *«Q1»*, *«T3»*: la scrittura breve dei trimestri, che nel gergo aziendale e' comune.
_TRIMESTRE_BREVE = re.compile(r"\b[qt]([1-4])\b")
#: Un anno a quattro cifre. Il limite basso tiene fuori gli importi: *«sopra 1500»* non
#: e' un anno, e un frammento di condizione temporale non parla del 1500.
_ANNO = re.compile(r"\b(199\d|20\d\d)\b")

_MESE = re.compile(rf"\b({'|'.join(MESI)})\b")


def _normalizza(testo: str) -> str:
    """Minuscolo e senza accenti, come fa il lessico di D119.

    Chi scrive di fretta non mette gli accenti, e un controllo che si fa ingannare da un
    accento non protegge niente (**D83**, la decisione per cui il riconoscimento dei
    termini e' indulgente su refusi e accenti).
    """
    piatto = unicodedata.normalize("NFKD", testo or "")
    return "".join(c for c in piatto if not unicodedata.combining(c)).lower()


def _periodi(testo: str) -> list[tuple[str | None, int]]:
    """Tutti i periodi che il frammento nomina, nell'ordine in cui compaiono.

    Un periodo e' una coppia: il simbolo che lo direbbe e il suo parametro. Il simbolo
    e' `None` quando **nessun simbolo del contratto lo dice** — *«bimestre»*,
    *«quadrimestre»*, *«decennio»*.
    """
    trovati: list[tuple[str | None, int]] = []

    for mese in _MESE.findall(testo):
        trovati.append(("month_of_year", MESI.index(mese) + 1))

    for ordinale, unita in _ORDINALE_UNITA.findall(testo):
        trovati.append((UNITA[unita], ORDINALI[ordinale]))
    for unita, ordinale in _UNITA_ORDINALE.findall(testo):
        trovati.append((UNITA[unita], ORDINALI[ordinale]))

    for cifra in _TRIMESTRE_BREVE.findall(testo):
        trovati.append(("quarter_of_year", int(cifra)))

    for anno in _ANNO.findall(testo):
        trovati.append(("year_of", int(anno)))

    return trovati


def names_period(fragment: str) -> tuple[str | None, int] | None:
    """Il periodo che il frammento nomina, o `None` se non c'e' niente da dire.

    `None` in due casi, e in entrambi il controllo si astiene:

    * **nessun periodo nominato** — *«negli ultimi 30 giorni»*, *«quest'anno»*. Sono
      espressioni relative: dicono un periodo rispetto a oggi, non lo nominano, e il
      contratto le copre gia';
    * **piu' di un periodo** — *«da gennaio a marzo»*, *«dal 2024 al 2026»*. Con due
      nomi non esiste un solo simbolo atteso, e un controllo che ne sceglie uno a caso
      rifiuterebbe risposte giuste. E' il limite dichiarato di questa rete.

    Quando invece il periodo e' uno solo, la coppia dice quale — e un simbolo `None`
    dice che il contratto quel periodo non lo sa esprimere.
    """
    trovati = _periodi(_normalizza(fragment))
    if len(trovati) != 1:
        return None
    return trovati[0]


def names_period_of(_dictionary=None) -> Callable[[str], tuple[str | None, int] | None]:
    """La funzione da iniettare, con la stessa forma di `scope_lexicon.justifies_of`.

    Prende il dizionario e non lo usa: il lessico e' del **prodotto**, uguale in ogni
    installazione. L'argomento c'e' perche' il punto di iniezione sia lo stesso degli
    altri e chi lo chiama non debba ricordare quale riconoscitore vuole cosa.
    """
    return names_period
