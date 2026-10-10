from collections import Counter
from typing import Iterable, Mapping

from src.domain.models.term import normalize_term


def prefixes_of(normalized_term: str) -> list[str]:
    return [normalized_term[:size] for size in range(1, len(normalized_term) + 1)]


def build_suggestions_by_prefix(terms: Iterable[tuple[str, int]], limit: int) -> dict[str, list[str]]:
    """The most frequent terms of each prefix, only for the prefixes needed by find_suggestions.

    A prefix with at most `limit` terms has all its terms as suggestions, so the suggestions of
    any longer prefix can be found among them. Because of that, a prefix is only saved when it
    is the first letter of a term or when the prefix before it has more terms than the limit.

    Each term is expected only once: terms with the same normalized spelling must be merged before.
    """
    ranked_terms = sorted(
        ((normalize_term(term), term, frequency) for term, frequency in terms),
        # most frequent first. With the same frequency, the shorter term first and then alphabetically
        key=lambda it: (-it[2], len(it[0]), it[0])
    )

    amount_of_terms_by_prefix = Counter(
        prefix for normalized_term, _, _ in ranked_terms for prefix in prefixes_of(normalized_term)
    )

    suggestions_by_prefix = {}
    for normalized_term, term, _ in ranked_terms:
        for prefix in prefixes_of(normalized_term):
            # terms come from the most to the least frequent, so the first ones to reach a prefix are its top terms
            suggestions = suggestions_by_prefix.setdefault(prefix, [])
            if len(suggestions) < limit:
                suggestions.append(term)

            # from here, every longer prefix of this term is found among the suggestions of this one
            if amount_of_terms_by_prefix[prefix] <= limit:
                break

    return suggestions_by_prefix


def find_suggestions(prefix: str, suggestions_by_prefix: Mapping[str, list[str]]) -> list[str]:
    """The suggestions of a normalized prefix, even when the prefix itself was not saved.

    Only the suggestions of prefixes_of(prefix) are read from `suggestions_by_prefix`.
    """
    for saved_prefix in reversed(prefixes_of(prefix)):
        suggestions = suggestions_by_prefix.get(saved_prefix)
        if suggestions is None:
            continue

        if saved_prefix == prefix:
            return suggestions

        # the longest saved prefix has every term that starts with a longer prefix, if there is one
        return [term for term in suggestions if normalize_term(term).startswith(prefix)]

    return []
