from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Response
from src.infrastructure.adapters.logging_config import configure_logging
from src.application.http.dependencies import get_loader_pipeline, get_trie_cache
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
import logging


app = FastAPI()
load_dotenv()
configure_logging()

logger = logging.getLogger(__name__)

@app.get("/terms", status_code=200)
async def handler(search_term: str, amount: int, cache: RedisTrieCache=Depends(get_trie_cache)):
    logger.info(f"search - {search_term}")

    if cache.exists(term=search_term):
        return cache.retrieve(term=search_term).find_terms_by_prefix(prefix=search_term, limit=amount)
    
    else:
        # In this case, cache is already loaded by pipeline
        # What can be a good fallback if we cant access cache or something?
        # Here, I have to generate a trie from file?
        return [] 


@app.post("/pipeline", status_code=204)
def handler(background_task: BackgroundTasks, term_pipeline: TermLoaderPipeline = Depends(get_loader_pipeline)):
    background_task.add_task(term_pipeline.execute)