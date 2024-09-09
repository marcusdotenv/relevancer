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

    def save(self, trie: Trie):
        bytes_serialized_trie = self.__serializer.serialize(trie=trie)
        self.__client.set("root", bytes_serialized_trie)

    def retrieve(self) -> Trie:
        saved_serialized_trie = self.__client.get("root")
        return self.__serializer.deserialize(serialized_bytes=saved_serialized_trie)

    def is_trie_saved(self) -> bool:
        return self.__client.exists("root") # TODO: hardcoded key