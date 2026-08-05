"""Che cosa sta facendo il turno, detto mentre lo fa.

## Perche' serve un cursore tutto suo

Il turno gira dentro **una sola transazione**: `worker.execute` apre un cursore, chiama
il pipeline dall'inizio alla fine e committa una volta sola, in fondo. E' la scelta
giusta — il fallimento di un turno non deve annullare gli altri del lotto — ma ha una
conseguenza che qui e' decisiva.

`bus.bus._sendone` **non manda niente subito**. Accoda il messaggio su
`cr.precommit` e la sveglia del processo che serve il bus su `cr.postcommit`
(`core/addons/bus/models/bus.py`). Parte tutto al `commit`, e non un istante prima.

Quindi un avanzamento mandato sul cursore del lavoratore arriverebbe **insieme alla
risposta**, cioe' quando non serve piu' a nessuno: sarebbe un'animazione che racconta
un'attesa gia' finita. L'unico modo perche' arrivi mentre l'attesa e' in corso e'
aprire un cursore proprio, scrivere, committare e chiuderlo. E' quello che fa questo
modulo, ed e' l'unica ragione per cui esiste.

## Le tre proprieta' che non si negoziano

**Non solleva mai.** Un avviso di cortesia che uccide il turno che sta descrivendo
sarebbe il peggior scambio possibile. Ogni errore finisce nel registro e la corsa
continua: chi ha fatto la domanda perde l'animazione, non la risposta.

**E' strozzato.** Fra un evento e il successivo passano almeno
`INTERVALLO_MINIMO_MS`. Senza, un turno che risponde dalla cache sparerebbe sei
transazioni in cinquanta millisecondi — costo pieno, beneficio nessuno, perche'
nessun occhio distingue sei passi in un ventesimo di secondo.

**Ha un tetto.** Oltre `EVENTI_MASSIMI` non manda piu' niente. Il pipeline oggi ne
emette sei, ma un ciclo scritto male domani non deve poter allagare il bus di ogni
client connesso: il tetto e' li' per il difetto che non c'e' ancora.

## Cosa viaggia, e cosa no

Viaggia **la chiave del passo**, il suo numero d'ordine e un dettaglio neutro — un
conteggio, il nome dell'entita' come l'utente la chiama. Nient'altro.

Non viaggia la frase, non viaggia il catalogo, non viaggia la busta del modello. Il
canale e' il partner di chi ha scritto la frase, quindi non ci sarebbe un problema di
destinatario; e' D60 (nessuna frase e nessun catalogo nei registri diagnostici) letto
come principio invece che come regola sul solo `_logger`: il payload minimo che
funziona e' quello che non puo' diventare un archivio.

**Le parole non stanno qui.** Il server manda una chiave stabile, il client la
traduce. Il vantaggio non e' il peso del messaggio: e' che la lingua dell'interfaccia
e' una scelta dell'interfaccia, e un giorno la stessa chiave dovra' poter diventare
una riga diversa senza toccare il dispatcher.
"""

from __future__ import annotations

import logging
import time

_logger = logging.getLogger(__name__)

#: Il tipo di notifica sul bus. Il client vi si iscrive accanto a `nli.turn`, che
#: resta l'avviso di fine turno: sono due messaggi diversi con due destini diversi —
#: questo si puo' perdere senza danno, quello no.
CANALE = "nli.turn.progress"

#: Quanto deve passare fra due eventi. Sotto i due decimi di secondo l'occhio legge
#: una sfocatura, non una sequenza: mandarli piu' fitti costa e non si vede.
INTERVALLO_MINIMO_MS = 250

#: Il tetto per turno. Il pipeline ne emette sei; questo numero non e' una misura, e'
#: una cintura contro il ciclo che qualcuno scrivera' fra due anni.
EVENTI_MASSIMI = 12

#: Le chiavi che il pipeline puo' emettere. Sta qui e non nel pipeline perche' e'
#: **il contratto con il client**: chi aggiunge un passo deve passare da questa riga,
#: e chi legge il client sa dove trovarne l'elenco completo.
PASSI = (
    "dictionary",   # fase A — il dizionario cerca di che cosa parla la frase
    "entity",       # fase B — al modello: quale entita'? (solo se A non ha risolto)
    "catalogue",    # fase C — si prepara il catalogo dell'entita'
    "reading",      # D121 — la frase sceglie una lettura gia' pronta, niente modello
    "interpret",    # il modello legge la frase e restituisce la busta
    "validate",     # livelli 3-5 — cosa si accetta e cosa si rifiuta
    "execute",      # la query su Odoo
)


class Reporter:
    """Manda gli avanzamenti di **un** turno. Uno per turno, costruito dal lavoratore.

    Si chiama come una funzione: `reporter("catalogue", detail="Fatture")`.

    Tiene lo stato che serve a strozzare e a numerare, e nient'altro. In particolare
    **non tiene un cursore aperto**: aprirne uno per l'intera durata del turno
    significherebbe occupare una connessione del pool per tutto il tempo in cui il
    modello pensa, che e' il tempo lungo — e sarebbe esattamente il costo che questo
    modulo esiste per non pagare.
    """

    __slots__ = ("_dbname", "_uid", "_partner_id", "_turn_id", "_interrogation_id",
                 "_indice", "_ultimo")

    def __init__(self, dbname: str, *, uid: int, partner_id: int, turn_id: int,
                 interrogation_id: int):
        self._dbname = dbname
        self._uid = uid
        self._partner_id = partner_id
        self._turn_id = turn_id
        self._interrogation_id = interrogation_id
        self._indice = 0
        self._ultimo = 0.0

    def __call__(self, step: str, *, detail: str | None = None,
                 force: bool = False) -> None:
        """Annuncia un passo. Torna sempre, qualunque cosa succeda sotto.

        `force` salta lo strozzamento — non il tetto. Serve al primo passo, che deve
        partire subito: e' quello che toglie dallo schermo l'attesa muta, e farlo
        aspettare un quarto di secondo vorrebbe dire aggiungere attrito proprio dove
        lo si sta togliendo.
        """
        if self._indice >= EVENTI_MASSIMI:
            return
        adesso = time.monotonic()
        if not force and (adesso - self._ultimo) * 1000 < INTERVALLO_MINIMO_MS:
            return
        self._ultimo = adesso
        self._indice += 1
        try:
            self._invia({
                "turn_id": self._turn_id,
                "interrogation_id": self._interrogation_id,
                "step": step,
                "index": self._indice,
                "detail": detail or "",
            })
        except Exception:  # noqa: BLE001 — vedi il docstring del modulo
            # Il turno vale piu' della sua animazione. Si registra il tipo e basta:
            # il messaggio di un'eccezione puo' citare cio' che l'ha causata, e qui
            # sopra ci passano i nomi del catalogo.
            _logger.warning("AIDA: avanzamento non inviato per il turno %s (%s)",
                            self._turn_id, "errore")

    def _invia(self, payload: dict) -> None:
        """Cursore proprio, scrittura, commit, chiusura. In quest'ordine e basta.

        Il `with` di `registry.cursor()` committa all'uscita, ed e' proprio il commit
        che fa partire il messaggio: senza, questo modulo sarebbe un giro lungo per
        ottenere lo stesso ritardo di prima.

        **Odoo si importa qui dentro e non in cima al file**, ed e' una scelta di
        collaudo. Lo strozzamento, il tetto e il silenzio sugli errori sono le tre
        proprieta' che tengono in piedi questo modulo, e sono decisioni pure: con
        l'import in cima servirebbe una base dati per provarle, e le prove che
        chiedono una base dati sono quelle che poi nessuno esegue. Cosi' il file si
        importa da solo e le tre proprieta' stanno in `pure_tests`, dove appartengono.
        """
        import odoo
        from odoo import api

        registry = odoo.registry(self._dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, self._uid, {})
            env["res.partner"].browse(self._partner_id)._bus_send(CANALE, payload)


def report(reporter, step: str, *, detail: str | None = None,
           force: bool = False) -> None:
    """Annuncia un passo, se qualcuno sta aspettando.

    Il `None` e' l'interruttore, ed e' la stessa forma di `pipeline.trace`: a
    reporter spento non si costruisce niente e non si paga niente, e il pipeline non
    si riempie di condizioni che devono ricordarsi di essere tutte uguali.

    Un turno che gira dentro un test non ha un reporter, e va bene cosi': l'assenza
    dell'avanzamento non cambia una virgola di cio' che il turno produce, ed e'
    esattamente per questo che si puo' spegnere senza cautele.
    """
    if reporter is not None:
        reporter(step, detail=detail, force=force)
