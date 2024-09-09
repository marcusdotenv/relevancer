from dotenv import load_dotenv
from fastapi import FastAPI
from src.utils.database.postgres_terms_db import build_trie_from_db
from src.utils.cache.redis_trie_cache import RedisTrieCache
from src.utils.cache.serializers.proto.protobuff_serializer import ProtobuffSerializer


app = FastAPI()
load_dotenv()

protobuff = ProtobuffSerializer()
cache = RedisTrieCache(serializer=protobuff)

@app.get("/terms")
async def terms(search_term: str, amount: int):
    first_letter = search_term[0]
    if cache.is_trie_saved(partition_letter=first_letter):
        return cache.retrieve(partition_letter=first_letter).find_words_by_prefix(prefix=search_term, limit=amount)
    
    db_trie = await build_trie_from_db() # TODO: In future, should not necessary request to database. Cache will be the unique SOT.
                                         # TODO: An background worker can, once a day, update the database with new frequency values and
                                         # TODO: load on cache. Ensuring cache is available ever
    cache.save(trie=db_trie)
    return db_trie.find_words_by_prefix(prefix=search_term, limit=amount)