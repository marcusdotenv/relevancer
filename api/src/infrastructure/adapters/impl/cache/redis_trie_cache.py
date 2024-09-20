import redis
from dotenv import load_dotenv
import os
from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.trie_cache_contract import TrieCacheContract
from src.infrastructure.adapters.contracts.serializer_contract import SerializerContract 

load_dotenv()

class RedisTrieCache(TrieCacheContract):
    def __init__(self, serializer: SerializerContract) -> None:
        self.__client = redis.StrictRedis(
            host=os.getenv("CACHE_HOST"), 
            port=int((os.getenv("CACHE_PORT"))), 
            db=0
        )
        self.__serializer = serializer

    def __create_sub_trie(self, letter: str, trie: Trie)-> Trie:
        new_trie = Trie(partition_name=f"partition:{letter}")
        new_trie.get_root_node().assign_related_nodes(related_nodes={letter: trie.get_root_node().get_related_nodes()[letter]})

        return new_trie

    def __split_trie_in_chunks(self, trie: Trie) -> list[Trie]:
        node_letters = trie.get_root_node().get_related_nodes().keys()
        
        return list(map(lambda it: self.__create_sub_trie(letter=it, trie=trie) , node_letters))

    def save(self, trie: Trie):
        sub_tries = self.__split_trie_in_chunks(trie=trie)

        for st in sub_tries:
            bytes_serialized_trie = self.__serializer.serialize(trie=st)
            self.__client.set(st.get_root_node().letter, bytes_serialized_trie)

    def retrieve(self, term: str) -> Trie:
        partition_letter = term[0]
        saved_serialized_trie = self.__client.get(f"partition:{partition_letter}")
        return self.__serializer.deserialize(serialized_bytes=saved_serialized_trie)

    def exists(self, term: str) -> bool:
        partition_letter = term[0]
        return self.__client.exists(f"partition:{partition_letter}")