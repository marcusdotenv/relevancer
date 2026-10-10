import random
import unittest

from src.domain.models.suggestions import build_suggestions_by_prefix, find_suggestions, prefixes_of
from src.domain.models.term import normalize_term


def find_without_suggestions(prefix: str, terms: list[tuple[str, int]], limit: int) -> list[str]:
    """The expected suggestions of a prefix, found by looking at every term."""
    matching_terms = [(term, frequency) for term, frequency in terms if normalize_term(term).startswith(prefix)]
    ranked_terms = sorted(matching_terms, key=lambda it: (-it[1], len(normalize_term(it[0])), normalize_term(it[0])))

    return [term for term, _ in ranked_terms[:limit]]


class SuggestionsTest(unittest.TestCase):

    def test_prefixes_of(self):
        self.assertEqual(prefixes_of("casa"), ["c", "ca", "cas", "casa"])
        self.assertEqual(prefixes_of(""), [])

    def test_only_first_letter_is_saved_when_all_its_terms_fit_in_the_limit(self):
        suggestions = build_suggestions_by_prefix(terms=[("casa", 5), ("carro", 3), ("bola", 1)], limit=10)

        self.assertEqual(suggestions, {"c": ["casa", "carro"], "b": ["bola"]})

    def test_longer_prefixes_are_saved_only_below_a_prefix_with_more_terms_than_the_limit(self):
        terms = [("casa", 5), ("casaco", 4), ("carro", 3), ("cama", 1)]

        suggestions = build_suggestions_by_prefix(terms=terms, limit=2)

        # "c" and "ca" have 4 terms and keep only 2, so the next letter is needed to find the others.
        # "cas" has all its 2 terms, so "casa", "casac"... can be found from it
        self.assertEqual(suggestions, {
            "c": ["casa", "casaco"],
            "ca": ["casa", "casaco"],
            "cas": ["casa", "casaco"],
            "car": ["carro"],
            "cam": ["cama"],
        })

    def test_prefix_with_exactly_the_limit_of_terms_does_not_need_longer_prefixes(self):
        suggestions = build_suggestions_by_prefix(terms=[("casa", 5), ("carro", 3)], limit=2)

        self.assertEqual(suggestions, {"c": ["casa", "carro"]})

    def test_find_suggestions_of_saved_prefix(self):
        suggestions = build_suggestions_by_prefix(terms=[("carro", 1), ("casa", 3), ("cama", 2), ("bola", 9)], limit=10)

        self.assertEqual(find_suggestions("c", suggestions), ["casa", "cama", "carro"])
        self.assertEqual(find_suggestions("b", suggestions), ["bola"])

    def test_find_suggestions_of_prefix_that_is_not_saved(self):
        suggestions = build_suggestions_by_prefix(terms=[("carro", 1), ("casa", 3), ("casaco", 2), ("bola", 9)], limit=10)

        self.assertNotIn("cas", suggestions)
        self.assertEqual(find_suggestions("ca", suggestions), ["casa", "casaco", "carro"])
        self.assertEqual(find_suggestions("cas", suggestions), ["casa", "casaco"])
        self.assertEqual(find_suggestions("casac", suggestions), ["casaco"])
        self.assertEqual(find_suggestions("casaco", suggestions), ["casaco"])

    def test_find_suggestions_return_empty_when_no_term_has_the_prefix(self):
        terms = [("casa", 5), ("casaco", 4), ("carro", 3), ("cama", 1)]

        for limit in [2, 10]:
            with self.subTest(limit=limit):
                suggestions = build_suggestions_by_prefix(terms=terms, limit=limit)

                self.assertEqual(find_suggestions("z", suggestions), [])
                self.assertEqual(find_suggestions("cab", suggestions), [])
                self.assertEqual(find_suggestions("casaz", suggestions), [])
                self.assertEqual(find_suggestions("casacos", suggestions), [])

        self.assertEqual(find_suggestions("c", {}), [])

    def test_find_suggestions_is_the_same_of_looking_at_every_term(self):
        generator = random.Random(7)
        letters = "abc"
        terms_by_normalized_term = {}
        for _ in range(400):
            term = "".join(generator.choice(letters) for _ in range(generator.randint(1, 7)))
            # some terms with capital letters, to have a spelling different of the prefix
            term = term.capitalize() if generator.random() < 0.3 else term
            terms_by_normalized_term[normalize_term(term)] = (term, generator.randint(0, 3))
        terms = list(terms_by_normalized_term.values())

        searched_prefixes = {prefix for term, _ in terms for prefix in prefixes_of(normalize_term(term))}
        searched_prefixes.update(["abcabcabc", "cccccccc", "ab" * 10])

        for limit in [1, 3, 10, 1000]:
            suggestions = build_suggestions_by_prefix(terms=terms, limit=limit)

            for prefix in searched_prefixes:
                with self.subTest(limit=limit, prefix=prefix):
                    self.assertEqual(find_suggestions(prefix, suggestions), find_without_suggestions(prefix, terms, limit))

    def test_less_prefixes_are_saved_than_one_for_each_prefix_of_each_term(self):
        terms = [(f"casa {number:03}", number) for number in range(60)]

        suggestions = build_suggestions_by_prefix(terms=terms, limit=50)

        # "c", "ca"... "casa 0" have more than 50 terms. From "casa 00" on, every prefix has at most 10 terms
        self.assertEqual(len(suggestions["casa"]), 50)
        self.assertEqual(suggestions["casa"][0], "casa 059")
        self.assertIn("casa 05", suggestions)
        self.assertNotIn("casa 059", suggestions)
        self.assertEqual(find_suggestions("casa 059", suggestions), ["casa 059"])

    def test_prefix_is_normalized_and_term_keep_original_spelling(self):
        suggestions = build_suggestions_by_prefix(terms=[("Casa de Praia", 3), ("  CARRO ", 1)], limit=10)

        self.assertEqual(suggestions, {"c": ["Casa de Praia", "  CARRO "]})
        self.assertEqual(find_suggestions("casa de p", suggestions), ["Casa de Praia"])
        self.assertEqual(find_suggestions("car", suggestions), ["  CARRO "])

    def test_terms_with_same_frequency_are_sorted_by_length_and_then_alphabetically(self):
        terms = [("casaco", 1), ("cama", 1), ("Casa", 1), ("casamento", 7), ("cabo", 1)]

        for _ in range(5):
            random.shuffle(terms)
            with self.subTest(terms=terms):
                suggestions = build_suggestions_by_prefix(terms=terms, limit=10)

                self.assertEqual(find_suggestions("ca", suggestions), ["casamento", "cabo", "cama", "Casa", "casaco"])

    def test_long_term_does_not_need_a_prefix_for_each_letter(self):
        longest_term = "a" * 200

        suggestions = build_suggestions_by_prefix(terms=[(longest_term, 1)], limit=10)

        self.assertEqual(suggestions, {"a": [longest_term]})
        self.assertEqual(find_suggestions("a" * 150, suggestions), [longest_term])

    def test_no_terms_has_no_suggestions(self):
        self.assertEqual(build_suggestions_by_prefix(terms=[], limit=10), {})
