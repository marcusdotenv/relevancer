from abc import ABC, abstractmethod

from src.domain.models.trie import Trie


class SerializerContract(ABC):
    
    @abstractmethod
    def deserialize(self, serialized_bytes: bytes) -> Trie:
        raise Exception("not implemented")
    @abstractmethod
    def serialize(self, trie: Trie) -> bytes:
        raise Exception("not implemented")