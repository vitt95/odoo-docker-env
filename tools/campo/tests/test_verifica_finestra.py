"""Le tre strade del controllo sulla finestra, una prova ciascuna.

Un controllo visto solo passare non e' un controllo: quello sulla finestra e' nato
perche' per settimane la diagnostica portava i due numeri vicini e **nessuno falliva**
quando divergevano.
"""

from __future__ import annotations

import unittest

from tools.campo import verifica_finestra


class TestLEsitoDelControllo(unittest.TestCase):

    def test_i_due_numeri_uguali_si_misura(self):
        """Il caso normale: il fornitore serve quello che il profilo dichiara."""
        self.assertEqual(verifica_finestra.esito_della_finestra(8192, 8192), verifica_finestra.VAI)

    def test_i_due_numeri_diversi_ci_si_ferma(self):
        """Il caso vero del 20 agosto 2026: profilo 8192, server 4096. La misura non
        andava presa, e invece e' stata presa."""
        self.assertEqual(verifica_finestra.esito_della_finestra(8192, 4096), verifica_finestra.FERMATI)

    def test_servita_piu_grande_ferma_lo_stesso(self):
        """Anche al contrario. Non e' pignoleria: se il server serve piu' di quanto il
        profilo dichiara, D79 sta dimensionando il catalogo su un numero sbagliato e
        stiamo buttando via attributi per niente — un difetto piu' silenzioso, non meno."""
        self.assertEqual(verifica_finestra.esito_della_finestra(4096, 8192), verifica_finestra.FERMATI)

    def test_un_fornitore_che_non_lo_dice_non_ferma_la_misura(self):
        """Il lato che non deve scattare. `/api/ps` e' di `ollama`, non del protocollo:
        fermarsi qui vorrebbe dire che la batteria funziona con un fornitore solo. Si
        misura, e lo si dice a chi legge."""
        self.assertEqual(verifica_finestra.esito_della_finestra(8192, None),
                         verifica_finestra.NON_VERIFICABILE)


if __name__ == "__main__":
    unittest.main()
