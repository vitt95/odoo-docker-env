"""Le prove della regola che decide quali parole si scrivono.

Ogni controllo ne ha una che lo mostra **scattare** e una che lo mostra **non
scattare**: un controllo visto solo passare non e' un controllo, e' una decorazione.
"""

from __future__ import annotations

import unittest

from tools.dizionario import pacchetti


class TestLaCollisione(unittest.TestCase):
    """Una parola gia' rivendicata da un'altra entita' non si scrive di nascosto."""

    def test_una_parola_di_un_altro_e_una_collisione(self):
        """Il caso per cui il controllo esiste: `ordini` porta gia' agli ordini di
        vendita, e scriverlo per gli acquisti renderebbe ambiguo cio' che era certo."""
        proprietario = pacchetti.collisione(
            "ordini", ref="purchase_order", gia_noti={"ordini": "sale_order"})
        self.assertEqual(proprietario, "sale_order")

    def test_una_parola_libera_non_e_una_collisione(self):
        """Il lato che non deve scattare: nessuno rivendica `vendite`, quindi si
        scrive. Se scattasse anche qui il controllo bloccherebbe tutto e sembrerebbe
        prudente."""
        self.assertIsNone(pacchetti.collisione(
            "vendite", ref="sale_order", gia_noti={"ordini": "sale_order"}))

    def test_la_stessa_entita_non_collide_con_se_stessa(self):
        """Rilanciare il comando due volte non deve trasformare la seconda volta in un
        conflitto: la parola c'e' gia', ed e' sua."""
        self.assertIsNone(pacchetti.collisione(
            "vendite", ref="sale_order", gia_noti={"vendite": "sale_order"}))

    def test_il_confronto_ignora_maiuscole_e_spazi(self):
        """*Vendite* e *vendite* sono la stessa parola: un controllo che non lo sapesse
        passerebbe vuoto proprio nei casi che deve prendere."""
        self.assertEqual(
            pacchetti.collisione(" Vendite ", ref="purchase_order",
                                 gia_noti={"vendite": "sale_order"}),
            "sale_order")


class TestCosaSiScrive(unittest.TestCase):
    """Le tre liste, e il fatto che nessuna passa vuota senza dirlo."""

    PACCHETTO = {"sale_order": ("vendite", "ordini"),
                 "purchase_order": ("acquisti",)}

    def test_scrive_solo_cio_che_e_libero_e_nel_perimetro(self):
        scrivibili, fuori, collisioni = pacchetti.da_scrivere(
            self.PACCHETTO,
            entita_nel_perimetro={"sale_order"},
            gia_noti={"ordini": "crm_lead"})
        self.assertEqual(scrivibili, [("sale_order", ("vendite",))])
        self.assertEqual(fuori, ["purchase_order"])
        self.assertEqual(collisioni, [("ordini", "sale_order", "crm_lead")])

    def test_un_entita_le_cui_parole_collidono_tutte_non_si_scrive(self):
        """Non deve restare una riga vuota: se non si scrive niente per un'entita',
        quell'entita' non compare fra le scrivibili."""
        scrivibili, _fuori, collisioni = pacchetti.da_scrivere(
            {"sale_order": ("ordini",)},
            entita_nel_perimetro={"sale_order"},
            gia_noti={"ordini": "crm_lead"})
        self.assertEqual(scrivibili, [])
        self.assertEqual(len(collisioni), 1)

    def test_il_pacchetto_vuoto_non_e_un_errore(self):
        """La maggior parte dei pacchetti oggi e' vuota apposta, e passarci dentro non
        deve rompere niente."""
        self.assertEqual(
            pacchetti.da_scrivere({}, entita_nel_perimetro={"sale_order"},
                                  gia_noti={}),
            ([], [], []))


class TestIPacchettiSpediti(unittest.TestCase):
    """Cio' che il repository dichiara davvero, non un esempio."""

    def test_le_parole_scritte_a_mano_sono_quelle_misurate(self):
        """Il 21 agosto 2026, su 45 frasi vere, l'unica entita' che una parola mancante
        rendeva irraggiungibile era `sale_order`. Se qualcuno aggiunge parole, questa
        prova lo obbliga a passare di qui e a portare la propria misura."""
        parole = {ref: termini
                  for pacchetto in pacchetti.PACCHETTI.values()
                  for ref, termini in pacchetto.items()}
        self.assertEqual(parole, {"sale_order": ("vendite",)})

    def test_ogni_modulo_dichiarato_ha_un_pacchetto_anche_se_vuoto(self):
        """Un modulo del perimetro senza voce nella tabella non e' «nessuna parola»:
        e' «nessuno ci ha guardato». Le due cose non devono somigliarsi."""
        for modulo in ("sale", "crm", "account", "stock", "hr", "product", "contacts"):
            self.assertIn(modulo, pacchetti.PACCHETTI)


if __name__ == "__main__":
    unittest.main()
