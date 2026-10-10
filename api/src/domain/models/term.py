# The trie is cached as nested protobuf messages, and a term longer than this
# exceeds the protobuf nesting limit: the whole partition stops being readable.
MAX_TERM_LENGTH = 48


def is_valid_term(term: str) -> bool:
    if not isinstance(term, str):
        return False

    if term.strip() == "":
        return False

    # the trie stores the lowered term, which can be longer than the original one
    if len(term.lower()) > MAX_TERM_LENGTH:
        return False

    return term.isprintable()


def normalize_term(term: str) -> str:
    # terms that differ only by case or surrounding spaces are the same term.
    # This is the identity of the term, the spelling shown to the user is kept apart
    return term.strip().lower()
