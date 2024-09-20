from abc import ABC, abstractmethod

from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.serializer_contract import SerializerContract

class TrieCacheContract(ABC):
    def __init__(self, serializer: SerializerContract) -> None:
        pass

    @abstractmethod
    def save(self, trie: Trie):
        raise Exception("not implemented")
    
    @abstractmethod
    def retrieve(self, term: str) -> Trie:
        raise Exception("not implemented")

    @abstractmethod
    def exists(self, term: str) -> bool:
        raise Exception("not implemented")