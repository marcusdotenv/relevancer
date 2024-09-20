from abc import ABC

from src.domain.models.trie import Trie


class SerializerContract(ABC):
    def deserialize(self, serialized_bytes: bytes) -> Trie:
        raise Exception("not implemented")
    
    def serialize(self, trie: Trie) -> bytes:
        raise Exception("not implemented")