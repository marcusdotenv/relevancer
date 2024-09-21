from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI
from src.infrastructure.adapters.logging_config import configure_logging
from src.application.http.dependencies import get_loader_pipeline, get_trie_cache
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
from src.utils.database.postgres_terms_db import build_trie_from_db
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
import logging


app = FastAPI()
load_dotenv()
configure_logging()

logger = logging.getLogger(__name__)

@app.get("/terms")
async def handler(search_term: str, amount: int, cache: RedisTrieCache=Depends(get_trie_cache)):
    logger.info(f"search - {search_term}")
    if cache.exists(term=search_term):
        return cache.retrieve(term=search_term).find_words_by_prefix(prefix=search_term, limit=amount)
    
    db_trie = await build_trie_from_db() # TODO: In future, should not necessary request to database. Cache will be the unique SOT.
                                         # TODO: An background worker can, once a day, update the database with new frequency values and
                                         # TODO: load on cache. Ensuring cache is available ever
    cache.save(trie=db_trie)
    return db_trie.find_words_by_prefix(prefix=search_term, limit=amount)


@app.post("/pipeline")
async def handler(background_task: BackgroundTasks, term_pipeline: TermLoaderPipeline = Depends(get_loader_pipeline)):
    background_task.add_task(term_pipeline.execute)