"""Le prove del generatore del dataset.

**Perche' esistono.** Fino all'8 agosto 2026 `genera_dataset.py` non aveva prove, e
il difetto piu' grave che ha avuto — il 13,56% delle provenienze che citavano parole
non presenti nella frase — e' rimasto invisibile per una sola ragione: **finche' ogni
attributo aveva un termine solo, due sorteggi indipendenti davano sempre lo stesso
risultato**. Il difetto era gia' scritto, aspettava solo i sinonimi per manifestarsi.

Ogni controllo ha una prova che lo mostra **scattare** e una che lo mostra **non
scattare**: un controllo visto solo passare non e' un controllo, e' una decorazione.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import genera_dataset as g  # noqa: E402


class ProvenienzaFondata(unittest.TestCase):
    """La rete di §6: ogni provenienza dev'essere un pezzo della frase.

    E' cio' su cui **D105** (una condizione nominata non fondata nel proprio frammento
    e' rifiutata), **D119** e **D144** verificano in servizio.
    """

    FRASE = "mostrami clienti con fatturato sopra 5000 ordinati per data creazione"

    def test_scatta_quando_la_provenienza_non_e_nella_frase(self):
        envelope = {"operations": [
            {"op": "add_order", "ref": "x.create_date",
             "provenance": {"text": "ordina per data di creazione"}},
        ]}
        fuori = g.provenienze_scollegate(envelope, self.FRASE)
        self.assertEqual([("add_order", "ordina per data di creazione")], fuori)

    def test_scatta_anche_sulla_portata_e_sul_chiarimento(self):
        """Le provenienze non stanno solo dentro `operations`."""
        envelope = {"scope_provenance": {"text": "e mandagli una mail"},
                    "clarification": {"provenance": {"text": "il mese prossimo"}}}
        fuori = g.provenienze_scollegate(envelope, self.FRASE)
        self.assertEqual({"scope_note", "clarification"}, {op for op, _ in fuori})

    def test_non_scatta_quando_ogni_provenienza_e_nella_frase(self):
        envelope = {"operations": [
            {"op": "set_target", "ref": "res.partner",
             "provenance": {"text": "clienti"}},
            {"op": "add_condition",
             "provenance": {"text": "fatturato sopra 5000"}},
            {"op": "add_order",
             "provenance": {"text": "ordinati per data creazione"}},
        ]}
        self.assertEqual([], g.provenienze_scollegate(envelope, self.FRASE))

    def test_non_scatta_per_accenti_maiuscole_o_punteggiatura(self):
        """*«E-mail»* e *«e mail»* sono la stessa cosa; `Citta'` e `citta` pure."""
        frase = "mostrami contatti con E-mail, e Città uguale a Roma"
        envelope = {"operations": [
            {"op": "add_condition", "provenance": {"text": "e mail"}},
            {"op": "add_condition", "provenance": {"text": "citta uguale a roma"}},
        ]}
        self.assertEqual([], g.provenienze_scollegate(envelope, frase))

    def test_una_parola_dentro_un_altra_non_conta_come_presente(self):
        """`mail` non e' contenuto in `email`: sono due parole diverse.

        Senza questo, il controllo passerebbe a vuoto proprio sui casi che deve
        prendere — ed e' il modo tipico in cui un confronto per sottostringa mente.
        """
        envelope = {"operations": [
            {"op": "add_condition", "provenance": {"text": "mail"}},
        ]}
        self.assertEqual(
            [("add_condition", "mail")],
            g.provenienze_scollegate(envelope, "mostrami contatti con email"))


class VariantiMeccaniche(unittest.TestCase):
    """I modi di dire un'etichetta senza dirla come l'ha scritta Odoo (§2)."""

    def test_la_punteggiatura_produce_le_due_forme(self):
        varianti = g.varianti_meccaniche("E-mail", "it")
        minuscole = {v.lower() for v in varianti}
        self.assertIn("email", minuscole)
        self.assertIn("e mail", minuscole)

    def test_la_parola_di_servizio_entra_fra_due_parole_vere(self):
        self.assertIn("data di creazione",
                      {v.lower() for v in g.varianti_meccaniche("Data creazione", "it")})

    def test_non_entra_se_l_etichetta_ha_gia_una_preposizione(self):
        """*«metodi del di spedizione»* non l'ha mai detto nessuno."""
        for etichetta in ("Metodi di spedizione", "I miei rendiconti",
                          "Righe ordine del punto vendita"):
            with self.subTest(etichetta=etichetta):
                self.assertEqual(
                    [], [v for v in g.varianti_meccaniche(etichetta, "it")
                         if " di " in f" {v} "])

    def test_l_inglese_non_prende_preposizioni(self):
        """`Work Order` non diventa `Work of Order`: il composto inglese non si lega."""
        self.assertEqual((), g.varianti_meccaniche("Work Order", "en"))

    def test_la_lingua_inventata_non_ha_morfologia(self):
        self.assertEqual((), g.varianti_meccaniche("Zanquilmor", "inventata"))

    def test_l_etichetta_stessa_non_e_una_variante(self):
        self.assertNotIn("Data creazione", g.varianti_meccaniche("Data creazione", "it"))


class CornicIDelleOperazioni(unittest.TestCase):
    """Il punto 1: piu' modi di dire la stessa cosa, non piu' cose dette."""

    def test_ogni_operazione_ha_piu_di_una_cornice(self):
        """Una cornice sola insegna la posizione invece del significato."""
        for chiave, forme in g.CORNICI.items():
            with self.subTest(chiave=chiave):
                self.assertGreaterEqual(len(set(forme)), 4, chiave)
        for chiave, forme in g.RAFFINAMENTI_DETTI.items():
            with self.subTest(chiave=chiave):
                self.assertGreaterEqual(len(set(forme)), 4, chiave)

    def test_le_cornici_con_segnaposto_lo_usano_tutte(self):
        """Una cornice che perde il `{x}` produrrebbe una frase senza l'attributo."""
        for chiave in ("ordine", "gruppo", "campi"):
            for forma in g.CORNICI[chiave]:
                self.assertIn("{x}", forma, f"{chiave}: {forma}")
        for forma in g.CORNICI["limite"]:
            self.assertIn("{n}", forma)


class IlForno(unittest.TestCase):
    """Il giro vero, in piccolo: quello che esce dev'essere buono per costruzione."""

    @classmethod
    def setUpClass(cls):
        cls.entita = g.carica_atlante(g.ATLANTE, g.ATLANTE_EN)
        cls.esempi = g.genera(cls.entita, 900, 20260808, g.Counter())

    def test_nessuna_provenienza_e_scollegata(self):
        """La garanzia end-to-end, non solo la rete che la controlla.

        Se questo fallisce, il generatore e' tornato a sorteggiare le parole due
        volte — che e' il difetto del 7 agosto 2026, non una regressione qualunque.
        """
        scollegate = [(e.frase, fuori) for e in self.esempi
                      if (fuori := g.provenienze_scollegate(e.envelope, e.frase))]
        self.assertEqual([], scollegate[:5])

    def test_i_cataloghi_non_sono_tutti_piccoli(self):
        """Il punto 3: il prodotto vero serve 27-60 attributi, non 9.

        La soglia e' un **pavimento misurato**, non un obiettivo: l'atlante ha piu'
        entita' piccole che grandi e piu' di cosi' non si ottiene senza sacrificare
        l'ampiezza, che **D143** protegge col tetto dell'1,5% per entita'.
        """
        taglie = sorted(len(e.catalogo["attributes"]) for e in self.esempi)
        mediana = taglie[len(taglie) // 2]
        grandi = sum(1 for t in taglie if t >= 27) / len(taglie)
        self.assertGreaterEqual(mediana, 11, f"mediana {mediana}, era 9")
        self.assertGreaterEqual(grandi, 0.15, f"{grandi:.0%} sopra i 27, era l'11%")

    def test_gli_attributi_non_hanno_piu_un_termine_solo(self):
        """Il punto 2. Nel dataset del 7 agosto erano 123 363 su 123 363."""
        con_sinonimi = sum(1 for e in self.esempi
                           for a in e.catalogo["attributes"] if len(a["terms"]) > 1)
        totale = sum(len(e.catalogo["attributes"]) for e in self.esempi)
        self.assertGreater(con_sinonimi / totale, 0.05)

    def test_le_frasi_non_cominciano_quasi_tutte_allo_stesso_modo(self):
        """Quattro aperture coprivano il 51% del dataset del 7 agosto."""
        attacchi = [" ".join(e.frase.lower().split()[:2]) for e in self.esempi]
        comuni = sorted(
            {a: attacchi.count(a) for a in set(attacchi)}.values(), reverse=True)[:4]
        self.assertLess(sum(comuni) / len(attacchi), 0.30)


if __name__ == "__main__":
    unittest.main()
