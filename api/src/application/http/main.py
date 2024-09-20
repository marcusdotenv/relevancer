from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from src.application.http.dependencies import get_trie_cache
from src.utils.database.postgres_terms_db import build_trie_from_db
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache


app = FastAPI()
load_dotenv()


@app.get("/terms")
async def terms(search_term: str, amount: int, cache: RedisTrieCache=Depends(get_trie_cache)):

    if cache.exists(term=search_term):
        return cache.retrieve(term=search_term).find_words_by_prefix(prefix=search_term, limit=amount)
    
    db_trie = await build_trie_from_db() # TODO: In future, should not necessary request to database. Cache will be the unique SOT.
                                         # TODO: An background worker can, once a day, update the database with new frequency values and
                                         # TODO: load on cache. Ensuring cache is available ever
    cache.save(trie=db_trie)
    return db_trie.find_words_by_prefix(prefix=search_term, limit=amount)