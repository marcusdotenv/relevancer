import unittest

from src.domain.models.term import MAX_TERM_LENGTH, is_valid_term, normalize_term


class TermTest(unittest.TestCase):

    def test_accept_common_terms(self):
        self.assertTrue(is_valid_term("casa"))
        self.assertTrue(is_valid_term("Esse é o nome de um produto"))
        self.assertTrue(is_valid_term("Whirlpool 24' Built-In Dishwasher - DU1100SS"))

    def test_accept_term_with_max_length(self):
        self.assertTrue(is_valid_term("a" * MAX_TERM_LENGTH))

    def test_reject_term_longer_than_max_length(self):
        self.assertFalse(is_valid_term("a" * (MAX_TERM_LENGTH + 1)))

    def test_reject_term_that_gets_longer_than_max_length_when_lowered(self):
        # "İ".lower() has two characters, and the prefixes come from the lowered term
        self.assertFalse(is_valid_term("İ" * MAX_TERM_LENGTH))

    def test_reject_empty_or_blank_term(self):
        self.assertFalse(is_valid_term(""))
        self.assertFalse(is_valid_term("   "))

    def test_reject_term_with_control_characters(self):
        self.assertFalse(is_valid_term("casa\n2024-01-01 - search - injected"))
        self.assertFalse(is_valid_term("ca\tsa"))
        self.assertFalse(is_valid_term("ca\x00sa"))

    def test_reject_values_that_are_not_strings(self):
        self.assertFalse(is_valid_term(None))
        self.assertFalse(is_valid_term(123))

    def test_normalize_term_ignore_case_and_surrounding_spaces(self):
        self.assertEqual(normalize_term("Casa"), "casa")
        self.assertEqual(normalize_term("  CASA "), "casa")
        self.assertEqual(normalize_term("Esse É o nome"), "esse é o nome")
