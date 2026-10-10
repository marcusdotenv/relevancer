# every prefix of a term is saved on the cache, so the length of a term must be limited
MAX_TERM_LENGTH = 48

# how many terms can be suggested for a prefix
MAX_SUGGESTED_TERMS = 50


def is_valid_term(term: str) -> bool:
    if not isinstance(term, str):
        return False

    if term.strip() == "":
        return False

    # prefixes come from the lowered term, which can be longer than the original one
    if len(term.lower()) > MAX_TERM_LENGTH:
        return False

    return term.isprintable()


def normalize_term(term: str) -> str:
    # terms that differ only by case or surrounding spaces are the same term.
    # This is the identity of the term, the spelling shown to the user is kept apart
    return term.strip().lower()
