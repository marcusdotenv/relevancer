from abc import ABC, abstractmethod

class SuggestionCacheNotLoaded(Exception):
    """The cache has no suggestions at all, so it can not tell if a prefix has suggestions."""

class SuggestionCacheUnavailable(Exception):
    """The cache can not be reached."""

class SuggestionCacheContract(ABC):

    @abstractmethod
    def save(self, suggestions_by_prefix: dict[str, list[str]]):
        raise Exception("not implemented")

    @abstractmethod
    async def find_terms_by_prefix(self, prefix: str, limit: int) -> list[str]:
        raise Exception("not implemented")
