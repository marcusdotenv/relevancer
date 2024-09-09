import redis
from dotenv import load_dotenv
import os

from src.entities.trie import Trie
from src.utils.cache.serializers.serializer_contract import SerializerContract 

load_dotenv()

class RedisTrieCache:
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

    def retrieve(self, partition_letter: str) -> Trie:
        saved_serialized_trie = self.__client.get(f"partition:{partition_letter}")
        return self.__serializer.deserialize(serialized_bytes=saved_serialized_trie)

    def is_trie_saved(self, partition_letter: str) -> bool:
        return self.__client.exists(f"partition:{partition_letter}")