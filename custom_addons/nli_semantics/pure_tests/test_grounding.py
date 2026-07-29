"""What counts as *mentioning* a named condition (D105), against the real matcher.

The rule lives in `nli_core` and is tested there with a literal matcher, because the
rule is *«the fragment must mention the term»* and it is one thing. This file tests the
other thing: that **mentioning** survives what users actually type.

If a literal comparison were used, a protection would turn into a defect — a correct
answer refused because the user wrote *«provvisore»*. The corpus perturbs its own
sentences with exactly these phenomena on purpose (D83), which is why the check reuses
phase A's index instead of a second notion of *the same word*.
"""

from __future__ import annotations

import unittest

from ..dictionary import grounding
from ..dictionary.store import Dictionary

DIZIONARIO = Dictionary.build([
    {"type": "T5", "level": "L1", "version": "1", "ref": "ordini.in_bozza",
     "entity": "ordini", "terms": ["in bozza", "da confermare", "provvisori",
                                   "non confermati", "provvisorie"],
     "condition": {"kind": "in", "field": "state", "values": ["draft"]}},
    {"type": "T5", "level": "L1", "version": "1", "ref": "ordini.da_consegnare",
     "entity": "ordini", "terms": ["da consegnare", "da evadere"],
     "condition": {"kind": "in", "field": "delivery_status", "values": ["pending"]}},
    {"type": "T1", "level": "L0", "ref": "ordini", "terms": ["ordini", "commesse"]},
])

assert not DIZIONARIO.problems, DIZIONARIO.problems


class TestMentions(unittest.TestCase):
    def setUp(self):
        self.mentions = grounding.mentions_of(DIZIONARIO)

    def test_the_term_as_written(self):
        self.assertTrue(self.mentions("ordini.in_bozza", "da confermare"))

    def test_a_term_inside_a_longer_fragment(self):
        self.assertTrue(self.mentions("ordini.da_consegnare", "quelli da evadere"))

    def test_a_fragment_that_names_nothing(self):
        """The measured failure: *«lo scorso mese»* turned into *in bozza*."""
        self.assertFalse(self.mentions("ordini.in_bozza", "lo scorso mese"))

    def test_the_term_of_another_condition_does_not_count(self):
        self.assertFalse(self.mentions("ordini.in_bozza", "da evadere"))

    # --- what users actually type -----------------------------------------
    def test_a_typo(self):
        self.assertTrue(self.mentions("ordini.in_bozza", "provvisore"))

    def test_lowercase_and_no_accents(self):
        self.assertTrue(self.mentions("ordini.da_consegnare", "QUELLI DA CONSEGNARE"))

    def test_singular_for_plural(self):
        self.assertTrue(self.mentions("ordini.in_bozza", "provvisorio"))

    def test_punctuation_around_the_term(self):
        self.assertTrue(self.mentions("ordini.da_consegnare", "solo, da consegnare!"))

    # --- the boundaries ---------------------------------------------------
    def test_an_empty_fragment_mentions_nothing(self):
        self.assertFalse(self.mentions("ordini.in_bozza", ""))
        self.assertFalse(self.mentions("ordini.in_bozza", "   "))

    def test_an_unknown_reference_mentions_nothing(self):
        self.assertFalse(self.mentions("ordini.inventata", "in bozza"))

    def test_the_terms_of_an_entity_are_not_named_conditions(self):
        """The index is restricted to T5. Were it not, *«ordini»* would ground any
        condition of the entity, and the check would pass on almost everything —
        which is the empty inspection the project forbids."""
        self.assertFalse(self.mentions("ordini", "ordini"))


if __name__ == "__main__":
    unittest.main()
