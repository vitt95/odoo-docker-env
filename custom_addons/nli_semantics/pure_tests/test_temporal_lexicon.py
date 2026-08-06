"""Il lessico dei periodi nominati (**D144**).

**Zona pura.**

La classe di guasto che queste prove esercitano non e' *«manca il semestre»*: e' che
quando la parola manca il modello **ripiega su quella vicina invece di rifiutare**, in
silenzio. *«Nel secondo semestre»* e' tornato con il secondo trimestre, tre giri su tre,
contro una riga di prompt che lo vietava per nome (`00` §46.7).

Meta' delle prove qui sotto sono **falsi positivi che non devono scattare**, ed e' la
meta' che conta di piu': una rete che rifiuta risposte giuste e' peggio del difetto che
chiude. E' la lezione della misura di **D105** (la decisione che pretende che una
condizione nominata sia fondata nel proprio frammento) — undici risposte sbagliate
diventate rifiuti, **zero** risposte giuste rifiutate.
"""

from __future__ import annotations

import unittest

from odoo.addons.nli_core.contract.envelope import envelope
from odoo.addons.nli_core.validation import structural

from .. import temporal_lexicon as lessico


def _con_periodo(expression, frammento, **parametri):
    """Un envelope con una sola condizione temporale e il frammento che la cita."""
    valore = {"kind": "temporal", "expression": expression}
    valore.update(parametri)
    return envelope(
        "operations",
        confidence=0.9,
        operations=[{
            "op": "add_condition", "combine": "all",
            "condition": {"ref": "ordini.data", "predicate": "within",
                          "value": valore},
            "provenance": {"text": frammento},
        }],
    )


class TestIlPeriodoCheLaFraseNomina(unittest.TestCase):
    """Il frammento nomina un periodo, e il lessico dice quale."""

    def test_a_month_by_name(self):
        self.assertEqual(lessico.names_period("a gennaio"), ("month_of_year", 1))
        self.assertEqual(lessico.names_period("di dicembre"), ("month_of_year", 12))

    def test_an_ordinal_quarter(self):
        self.assertEqual(
            lessico.names_period("nel primo trimestre"), ("quarter_of_year", 1))
        self.assertEqual(
            lessico.names_period("nel 4 trimestre"), ("quarter_of_year", 4))

    def test_the_unit_can_come_first(self):
        """*«Trimestre 1»* e' la stessa cosa detta al contrario."""
        self.assertEqual(
            lessico.names_period("trimestre 2"), ("quarter_of_year", 2))

    def test_the_short_form_of_a_quarter(self):
        """*«Q1»* e *«T3»*: nel gergo aziendale si scrive cosi' piu' spesso che a
        parole, e un lessico che non lo sapesse coprirebbe meta' dei casi veri."""
        self.assertEqual(lessico.names_period("in Q1"), ("quarter_of_year", 1))
        self.assertEqual(lessico.names_period("nel T3"), ("quarter_of_year", 3))

    def test_a_four_digit_year(self):
        self.assertEqual(lessico.names_period("nel 2025"), ("year_of", 2025))

    def test_accents_and_case_do_not_fool_it(self):
        """La stessa indulgenza di D83 e del lessico di D119."""
        self.assertEqual(lessico.names_period("A GENNAIO"), ("month_of_year", 1))


class TestIPeriodiCheNessunSimboloSaDire(unittest.TestCase):
    """Il cuore della rete: un periodo che il contratto non esprime.

    Il simbolo e' `None`, e chi legge sa che qualunque espressione sarebbe un ripiego.
    """

    def test_a_two_month_period(self):
        self.assertEqual(lessico.names_period("nel primo bimestre"), (None, 1))

    def test_a_four_month_period(self):
        self.assertEqual(
            lessico.names_period("nel secondo quadrimestre"), (None, 2))

    def test_a_decade(self):
        self.assertEqual(lessico.names_period("nel primo decennio"), (None, 1))

    def test_a_half_year_is_expressible_now(self):
        """*«Semestre»* era inesprimibile fino a **D141**, che ha aggiunto
        `half_of_year`. La prova sta qui a dire che il lessico e il contratto sono
        d'accordo: se qualcuno togliesse il simbolo senza toccare il lessico, la rete
        continuerebbe a pretendere un simbolo che non c'e' piu'."""
        self.assertEqual(
            lessico.names_period("nel secondo semestre"), ("half_of_year", 2))


class TestQuandoIlControlloSiAstiene(unittest.TestCase):
    """I falsi positivi che non devono scattare.

    Ogni prova qui sotto e' una risposta **giusta** che una rete scritta male
    rifiuterebbe.
    """

    def test_a_relative_window_names_no_period(self):
        """*«Negli ultimi 30 giorni»* e' `last_n_days(30)`, non un periodo nominato."""
        self.assertIsNone(lessico.names_period("negli ultimi 30 giorni"))

    def test_a_current_period_names_no_period(self):
        self.assertIsNone(lessico.names_period("quest'anno"))
        self.assertIsNone(lessico.names_period("questo trimestre"))

    def test_the_last_quarter_is_relative_not_named(self):
        """*«L'ultimo trimestre»* indica un trimestre rispetto a oggi — che e' cio' che
        `previous_quarter` dice — e non ne nomina uno. E' la classe di falso positivo
        piu' probabile di tutte."""
        self.assertIsNone(lessico.names_period("nell'ultimo trimestre"))
        self.assertIsNone(lessico.names_period("lo scorso semestre"))

    def test_counting_units_is_not_naming_one(self):
        """*«Gli ultimi 3 trimestri»* conta unita', non ne nomina una: il plurale e'
        cio' che distingue le due cose, ed e' la ragione per cui il lessico e' al
        singolare."""
        self.assertIsNone(lessico.names_period("negli ultimi 3 trimestri"))
        self.assertIsNone(lessico.names_period("negli ultimi 6 mesi"))

    def test_two_periods_make_the_check_abstain(self):
        """Con due nomi non esiste un solo simbolo atteso, e sceglierne uno a caso
        rifiuterebbe una risposta giusta. E' il limite dichiarato della rete."""
        self.assertIsNone(lessico.names_period("da gennaio a marzo"))
        self.assertIsNone(lessico.names_period("dal 2024 al 2026"))
        self.assertIsNone(lessico.names_period("nel primo trimestre 2025"))

    def test_a_written_out_date_names_two_periods(self):
        """*«Il 1 gennaio 2025»* e' una data scritta per esteso: nomina un mese e un
        anno, quindi il lessico si astiene. Il controllo lascia comunque fuori
        `absolute`, ma questa e' la seconda rete."""
        self.assertIsNone(lessico.names_period("dal 1 gennaio 2025"))

    def test_an_amount_is_not_a_year(self):
        """Il limite basso di quattro cifre tiene fuori gli importi."""
        self.assertIsNone(lessico.names_period("sopra 1500"))

    def test_an_empty_fragment_names_nothing(self):
        self.assertIsNone(lessico.names_period(""))
        self.assertIsNone(lessico.names_period("   "))


class TestLaFormaDellIniezione(unittest.TestCase):

    def test_the_lexicon_is_of_the_product_not_of_the_installation(self):
        """Prende il dizionario e non lo usa: *«gennaio»* e' italiano, non il gergo di
        un cliente. E' la ragione per cui questo lessico **non** sta in **D108** (il
        registro delle voci approvate) nonostante `00` §46.7 lo proponesse."""
        self.assertIs(lessico.names_period_of(), lessico.names_period)
        self.assertIs(lessico.names_period_of("un dizionario qualunque"),
                      lessico.names_period)


class TestLeDueMetaSonoDaccordo(unittest.TestCase):
    """Il lessico e il controllo, provati **insieme**.

    Provare il controllo con un lessico finto e il lessico senza controllo lascia
    scoperto l'unico difetto che conta: che le due meta' parlino di simboli diversi.
    E' §38 — codice dichiarato, provato e non collegato — applicato prima invece che
    dopo. La prova sta qui e non in `nli_core` perche' il nucleo non dipende da nulla
    (**D24**), e un import in una prova violerebbe il confine come lo violerebbe nel
    codice.
    """

    def test_the_half_year_of_D141_is_accepted_end_to_end(self):
        """*«Nel secondo semestre»* con `half_of_year(2)`: il caso che §46.7 ha
        chiuso, provato con le parole vere."""
        self.assertEqual(structural.validate_temporal_grounding(
            _con_periodo("half_of_year", "nel secondo semestre", n=2),
            names_period=lessico.names_period), [])

    def test_the_fallback_of_section_46_7_is_caught_end_to_end(self):
        """Lo stesso frammento con `quarter_of_year(2)`: il ripiego misurato tre giri
        su tre, contro una riga di prompt che lo vietava per nome. Questa e' la prova
        che la rete lo prende dove il prompt non ce l'ha fatta."""
        fallimenti = structural.validate_temporal_grounding(
            _con_periodo("quarter_of_year", "nel secondo semestre", n=2),
            names_period=lessico.names_period)
        self.assertEqual([f.code for f in fallimenti], ["temporal_period_mismatch"])

    def test_a_two_month_period_is_caught_end_to_end(self):
        """*«Nel primo bimestre»*: nessun simbolo lo dice, e senza questa rete
        tornerebbe come un trimestre — tre mesi di dati sbagliati, in silenzio."""
        fallimenti = structural.validate_temporal_grounding(
            _con_periodo("quarter_of_year", "nel primo bimestre", n=1),
            names_period=lessico.names_period)
        self.assertEqual([f.code for f in fallimenti], ["temporal_not_expressible"])

    def test_the_original_defect_of_D141_is_caught_end_to_end(self):
        """*«Nel primo trimestre»* risposto con il terzo: ventisei record sbagliati e
        nessun segnale, il difetto che ha aperto §46."""
        fallimenti = structural.validate_temporal_grounding(
            _con_periodo("quarter_of_year", "nel primo trimestre", n=3),
            names_period=lessico.names_period)
        self.assertEqual([f.code for f in fallimenti], ["temporal_period_mismatch"])

    def test_a_relative_window_still_passes_end_to_end(self):
        """La meta' che conta di piu': una risposta **giusta** non deve essere
        rifiutata."""
        self.assertEqual(structural.validate_temporal_grounding(
            _con_periodo("last_n_days", "negli ultimi 30 giorni", n=30),
            names_period=lessico.names_period), [])
        self.assertEqual(structural.validate_temporal_grounding(
            _con_periodo("current_quarter", "in questo trimestre"),
            names_period=lessico.names_period), [])
        self.assertEqual(structural.validate_temporal_grounding(
            _con_periodo("previous_quarter", "nell'ultimo trimestre"),
            names_period=lessico.names_period), [])

    def test_every_named_symbol_of_D141_is_reachable_from_words(self):
        """Ogni simbolo di periodo nominato dev'essere raggiungibile da qualche parola
        italiana. Un simbolo che il lessico non sa produrre e' un simbolo che la rete
        non protegge, e nessuno se ne accorgerebbe."""
        raggiunti = {lessico.names_period(testo)[0] for testo in (
            "a gennaio", "nel primo trimestre", "nel secondo semestre", "nel 2025")}
        self.assertEqual(
            raggiunti,
            {"month_of_year", "quarter_of_year", "half_of_year", "year_of"})


if __name__ == "__main__":
    unittest.main()
