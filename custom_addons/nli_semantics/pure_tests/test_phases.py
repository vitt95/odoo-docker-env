"""Fase A — cosa conta come prova che una frase nomina un'entita'.

Il guardiano di **V-D93-1** butta via l'evidenza di un'entita' quando un termine che
entita' non e' — un attributo, una categoria — copre lo stesso pezzo di frase almeno
altrettanto bene. E' cio' che rende usabile il livello morfologico, ed e' il corpus ad
averlo mostrato.

Queste prove fissano il **confine** di quel guardiano: fin dove deve arrivare, e dove
deve fermarsi.
"""

from __future__ import annotations

import unittest

from ..catalogue import phases
from ..dictionary.index import TermIndex


class TestExactEvidenceSurvivesTheGuard(unittest.TestCase):
    """V-D93-1 vale contro le prove morfologiche, non contro quelle esatte (D126).

    Misurato sul database vero il 3 agosto 2026: *«le fatture non pagate»* non
    risolveva niente. L'entita' `account_move` porta il termine *Fatture* — esatto —
    e sullo stesso pezzo di frase lo portano anche `res_partner.invoice_ids` e
    `sale_order.invoice_ids`, che si chiamano *Fatture* pure loro. Tre prove esatte
    identiche, e il guardiano le buttava tutte.
    """

    ENTITIES = frozenset({"fatture"})

    @staticmethod
    def _index(*entries):
        index = TermIndex()
        for ref, term in entries:
            index.add_entry(
                {"type": "T1", "level": "L0", "ref": ref, "terms": [term]}, ref=ref)
        return index

    def test_an_exact_entity_name_survives_an_identical_field_name(self):
        """Se l'utente ha detto «fatture» e le fatture sono un'entita', le fatture sono
        un candidato. Il pareggio fra due prove esatte non e' una ragione per buttare
        quella dell'entita'."""
        index = self._index(("fatture", "fatture"),
                            ("ordini.fatture", "fatture"))
        esito = phases.determine_entity(
            "le fatture non pagate", index, entity_refs=self.ENTITIES)
        self.assertTrue(esito.resolved, esito.explain())
        self.assertEqual(esito.entity, "fatture")

    def test_a_morphological_entity_match_is_still_discarded(self):
        """Il caso che il guardiano esiste per prendere, e che deve continuare a
        prendere: l'entita' arriva dalla forma base — evidenza **piu' debole** di
        quella che le si oppone — e li' il pareggio la elimina."""
        index = self._index(("clienti", "clienti"), ("fatture.cliente", "cliente"))
        esito = phases.determine_entity(
            "raggruppati per cliente", index,
            entity_refs=frozenset({"clienti"}))
        self.assertFalse(esito.resolved, esito.explain())

    def test_two_exact_entities_on_one_span_are_a_question_not_a_guess(self):
        """Piu' candidati esatti non diventano una scelta a caso: decide il margine,
        che e' li' apposta (D33)."""
        index = self._index(("ordini_vendita", "ordini"),
                            ("ordini_acquisto", "ordini"))
        esito = phases.determine_entity(
            "mostrami gli ordini", index,
            entity_refs=frozenset({"ordini_vendita", "ordini_acquisto"}))
        self.assertFalse(esito.resolved)
        self.assertTrue(esito.needs_clarification, esito.explain())


class TestTheHandWrittenEntityName(unittest.TestCase):
    """Il sinonimo di entita' scritto a mano: dove deve scattare e dove non deve.

    Misurato il 20 agosto 2026 sul database vero: *«mostrami le vendite con totale
    superiore a 2000»* non risolveva niente, perche' fra i nomi raccolti da D126 —
    *Ordini*, *Preventivi*, *Ordine di vendita* — *vendite* da sola non c'e'.
    `tools/dizionario/sinonimi_entita.py` la aggiunge come voce T1 di livello L1.

    La seconda prova e' quella che conta davvero. *Vendite* e' una parola che vive
    anche **dentro il nome di un attributo** — *Addetto vendite*, *Team di vendita* —
    e un sinonimo che rubasse quel pezzo di frase sarebbe peggio del difetto che
    ripara: trasformerebbe un raggruppamento in un cambio di entita', in silenzio.
    """

    ENTITIES = frozenset({"sale_order", "crm_lead"})

    @staticmethod
    def _index(*entries):
        index = TermIndex()
        for ref, term in entries:
            index.add_entry(
                {"type": "T1", "level": "L1", "ref": ref, "terms": [term]}, ref=ref)
        return index

    def test_the_word_alone_names_the_entity(self):
        """Cio' per cui la voce esiste: la frase dice «vendite» e nient'altro la
        contende, quindi la fase A risolve senza pagare il modello."""
        index = self._index(("sale_order", "vendite"),
                            ("sale_order", "ordini"))
        esito = phases.determine_entity(
            "mostrami le vendite con totale superiore a 2000", index,
            entity_refs=self.ENTITIES)
        self.assertTrue(esito.resolved, esito.explain())
        self.assertEqual(esito.entity, "sale_order")

    def test_the_word_inside_an_attribute_name_does_not_steal_the_span(self):
        """Il caso in cui la voce **non** deve scattare: *addetto vendite* e' il nome
        di un attributo dei lead, copre lo stesso pezzo di frase con due parole invece
        di una, e la frase nomina gia' la propria entita'. Se qui uscisse `sale_order`
        avremmo comprato una parola al prezzo di una classe di risposte sbagliate."""
        index = self._index(("sale_order", "vendite"),
                            ("crm_lead", "lead"),
                            ("crm_lead.user_id", "addetto vendite"))
        esito = phases.determine_entity(
            "i lead raggruppati per addetto vendite", index,
            entity_refs=self.ENTITIES)
        self.assertTrue(esito.resolved, esito.explain())
        self.assertEqual(esito.entity, "crm_lead")
