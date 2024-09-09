from dotenv import load_dotenv
from fastapi import FastAPI
from src.utils.database.db import build_try_using_db
from src.utils.cache.redis_trie_cache import RedisTrieCache
from src.utils.cache.serializers.proto.protobuff_serializer import ProtobuffSerializer


app = FastAPI()
load_dotenv()

trie = None
protobuff = ProtobuffSerializer()
cache = RedisTrieCache(serializer=protobuff)

@app.get("/terms")
async def terms(search_term: str, amount: int):
    if cache.is_trie_saved():
        return cache.retrieve().find_most_relevant(search_term=search_term, amount=amount)
    
    db_trie = await build_try_using_db()
    cache.save(trie=trie)
    return db_trie.find_most_relevant(search_term=search_term, amount=amount)