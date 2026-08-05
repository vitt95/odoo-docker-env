"""Le tre proprieta' dell'avanzamento, ai loro confini.

L'avanzamento e' cortesia: dice a chi aspetta che cosa sta succedendo. La cortesia
non deve costare niente a chi non la guarda, e soprattutto **non deve poter far
male** al turno che descrive. Sono tre proprieta', e sono tutte e tre facili da
perdere in una modifica distratta:

* si strozza, altrimenti un turno veloce apre sei transazioni in mezzo secondo;
* ha un tetto, altrimenti un ciclo scritto male allaga il bus di ogni client;
* non solleva mai, altrimenti l'animazione uccide la risposta che sta annunciando.

Ognuna di queste si perde in silenzio: nessuna rompe un test funzionale, nessuna si
vede in una revisione veloce, e tutte e tre si notano solo in produzione sotto
carico. E' esattamente il tipo di regola che va scritta adesso, mentre il motivo e'
ancora sotto gli occhi.
"""

import unittest

from nli_dispatch.runtime import progress as progress_module


class ReporterFinto(progress_module.Reporter):
    """Un `Reporter` che raccoglie invece di scrivere.

    Sostituisce **solo** `_invia`, cioe' l'unico metodo che tocca una base dati.
    Tutto cio' che questo file prova — ordine, strozzamento, tetto, silenzio — e'
    logica pura, e provarla senza un cursore non e' una scorciatoia: e' provarla
    dove sta davvero.
    """

    __slots__ = ("inviati", "esplode")

    def __init__(self, *args, esplode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.inviati = []
        self.esplode = esplode

    def _invia(self, payload):
        if self.esplode:
            raise RuntimeError("la base dati non risponde")
        self.inviati.append(payload)


def reporter(**kwargs):
    return ReporterFinto("db", uid=2, partner_id=7, turn_id=42,
                         interrogation_id=9, **kwargs)


class TestIlPayload(unittest.TestCase):
    def test_porta_il_turno_la_conversazione_il_passo_e_il_numero(self):
        r = reporter()
        r("dictionary", force=True)
        self.assertEqual(r.inviati, [{
            "turn_id": 42,
            "interrogation_id": 9,
            "step": "dictionary",
            "index": 1,
            "detail": "",
        }])

    def test_il_numero_d_ordine_cresce_di_uno_per_evento(self):
        r = reporter()
        for passo in ("dictionary", "catalogue", "interpret"):
            r(passo, force=True)
        self.assertEqual([e["index"] for e in r.inviati], [1, 2, 3])

    def test_il_dettaglio_arriva_quando_c_e_e_resta_vuoto_quando_manca(self):
        r = reporter()
        r("interpret", detail="fatture", force=True)
        r("execute", force=True)
        self.assertEqual([e["detail"] for e in r.inviati], ["fatture", ""])

    def test_ogni_passo_emesso_e_dichiarato_nel_contratto(self):
        # Il client traduce le chiavi in parole. Una chiave che il client non conosce
        # e' un passo che l'utente vede come una riga vuota, e nessun test funzionale
        # se ne accorge: la risposta arriva lo stesso.
        for passo in progress_module.PASSI:
            self.assertIsInstance(passo, str)
            self.assertTrue(passo)


class TestLoStrozzamento(unittest.TestCase):
    """Sotto l'intervallo minimo l'evento si butta via, e non si accumula."""

    def test_due_eventi_ravvicinati_ne_lasciano_passare_uno(self):
        r = reporter()
        r("dictionary", force=True)
        r("catalogue")  # subito dopo: strozzato
        self.assertEqual(len(r.inviati), 1)

    def test_un_evento_strozzato_non_consuma_il_numero_d_ordine(self):
        # Se lo consumasse, il client vedrebbe «passo 1, passo 3» e disegnerebbe un
        # buco che non corrisponde a niente.
        r = reporter()
        r("dictionary", force=True)
        r("catalogue")
        r("interpret", force=True)
        self.assertEqual([e["index"] for e in r.inviati], [1, 2])

    def test_force_passa_lo_strozzamento(self):
        r = reporter()
        for _ in range(4):
            r("dictionary", force=True)
        self.assertEqual(len(r.inviati), 4)

    def test_passato_l_intervallo_l_evento_passa(self):
        r = reporter()
        r("dictionary", force=True)
        # Si sposta l'orologio interno indietro invece di dormire: un test che
        # aspetta un quarto di secondo per provare un quarto di secondo e' un test
        # che qualcuno prima o poi salta.
        r._ultimo -= progress_module.INTERVALLO_MINIMO_MS / 1000
        r("catalogue")
        self.assertEqual(len(r.inviati), 2)


class TestIlTetto(unittest.TestCase):
    def test_oltre_il_massimo_non_manda_piu_niente(self):
        r = reporter()
        for _ in range(progress_module.EVENTI_MASSIMI + 5):
            r("dictionary", force=True)
        self.assertEqual(len(r.inviati), progress_module.EVENTI_MASSIMI)

    def test_il_tetto_vale_anche_con_force(self):
        # `force` salta lo strozzamento, che e' una scelta di ritmo. Il tetto e' una
        # cintura di sicurezza, e una cintura che si puo' slacciare non e' una
        # cintura.
        r = reporter()
        for _ in range(50):
            r("execute", force=True)
        self.assertEqual(len(r.inviati), progress_module.EVENTI_MASSIMI)


class TestIlSilenzio(unittest.TestCase):
    """Silenzio verso il turno, non verso il registro.

    «Non solleva mai» non vuol dire «non lo sa nessuno». Un avanzamento che sparisce
    senza lasciare traccia e' un guasto che si diagnostica per congettura, e la
    congettura su una cosa che succede solo sotto carico non arriva mai in fondo.
    """

    def test_un_errore_di_invio_non_esce_dal_reporter(self):
        r = reporter(esplode=True)
        with self.assertLogs(progress_module._logger, level="WARNING"):
            r("dictionary", force=True)  # non deve sollevare

    def test_l_errore_finisce_nel_registro_senza_citare_la_causa(self):
        # Il messaggio di un'eccezione puo' contenere cio' che l'ha provocata, e qui
        # sopra ci passano i nomi del catalogo dell'utente: nel registro va il fatto,
        # non il testo (D60).
        r = reporter(esplode=True)
        with self.assertLogs(progress_module._logger, level="WARNING") as registro:
            r("dictionary", force=True)
        riga = registro.output[0]
        self.assertIn("42", riga)
        self.assertNotIn("la base dati non risponde", riga)

    def test_dopo_un_errore_il_reporter_continua_a_funzionare(self):
        # Un errore transitorio — il pool momentaneamente esaurito — non deve
        # spegnere l'avanzamento per il resto del turno.
        r = reporter(esplode=True)
        with self.assertLogs(progress_module._logger, level="WARNING"):
            r("dictionary", force=True)
        r.esplode = False
        r("catalogue", force=True)
        self.assertEqual(len(r.inviati), 1)


class TestL_interruttore(unittest.TestCase):
    """`report(None, ...)` e' il turno che gira senza che nessuno guardi."""

    def test_senza_reporter_non_succede_niente(self):
        progress_module.report(None, "dictionary")  # non deve sollevare

    def test_con_reporter_inoltra_passo_dettaglio_e_force(self):
        r = reporter()
        progress_module.report(r, "interpret", detail="lead", force=True)
        self.assertEqual(r.inviati[0]["step"], "interpret")
        self.assertEqual(r.inviati[0]["detail"], "lead")


if __name__ == "__main__":
    unittest.main()
