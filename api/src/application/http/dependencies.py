
from fastapi import Depends
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
from src.infrastructure.adapters.contracts.serializer_contract import SerializerContract
from src.infrastructure.adapters.impl.serializer.proto.protobuff_serializer import ProtobuffSerializer


def get_cache_serializer() -> SerializerContract:
    return ProtobuffSerializer()

def get_trie_cache(serializer: SerializerContract = Depends(get_cache_serializer)) -> RedisTrieCache:
    return RedisTrieCache(serializer=serializer)
