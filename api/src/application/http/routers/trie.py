import logging
from fastapi import APIRouter, BackgroundTasks, Depends

from src.application.http.dependencies import get_loader_pipeline, get_trie_cache
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
from src.infrastructure.adapters.logging_config import configure_logging
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline

trie_router = APIRouter()
configure_logging()

logger = logging.getLogger(__name__)

@trie_router.get("/auto-complete", status_code=200)
async def handler(term: str, amount: int, cache: RedisTrieCache=Depends(get_trie_cache)):
    logger.info(f"search - {term}")

    if cache.exists(term=term):
        return cache.retrieve(term=term).find_terms_by_prefix(prefix=term, limit=amount)
    
    else:
        # In this case, cache is already loaded by pipeline
        # What can be a good fallback if we cant access cache or something?
        # Here, I have to generate a trie from file?
        return [] 

@trie_router.post("/pipeline", status_code=204)
def handler(background_task: BackgroundTasks, term_pipeline: TermLoaderPipeline = Depends(get_loader_pipeline)):
    background_task.add_task(term_pipeline.execute)