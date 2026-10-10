import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from src.application.http.dependencies import get_loader_pipeline, get_trie_cache
from src.domain.models.term import MAX_TERM_LENGTH, is_valid_term, normalize_term
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
from src.infrastructure.adapters.logging_config import configure_logging
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline

trie_router = APIRouter()
configure_logging()

logger = logging.getLogger(__name__)

MAX_AMOUNT = 50

class TermSelection(BaseModel):
    term: str

def validate_term(term: str) -> str:
    if not is_valid_term(term):
        raise HTTPException(
            status_code=422,
            detail=f"term can not be blank, have control characters or more than {MAX_TERM_LENGTH} characters"
        )
    return term.strip()

@trie_router.get("/auto-complete", status_code=200)
async def handler(
        term: str = Query(min_length=1, max_length=MAX_TERM_LENGTH),
        amount: int = Query(ge=1, le=MAX_AMOUNT),
        cache: RedisTrieCache=Depends(get_trie_cache)
    ):
    term = normalize_term(validate_term(term))
    logger.info(f"auto-complete - {term}")

    if cache.exists(term=term):
        return cache.retrieve(term=term).find_terms_by_prefix(prefix=term, limit=amount)
    
    else:
        # In this case, cache is already loaded by pipeline
        # What can be a good fallback if we cant access cache or something?
        # Here, I have to generate a trie from file?
        return [] 

@trie_router.post("/auto-complete/select", status_code=204)
def handler(selection: TermSelection):
    # the pipeline counts every "search - <term>" log as one search for the term.
    # Only a term chosen by the user is logged like this: a prefix typed on auto-complete is not a search
    term = validate_term(selection.term)
    logger.info(f"search - {term}")

@trie_router.post("/pipeline", status_code=204)
def handler(background_task: BackgroundTasks, term_pipeline: TermLoaderPipeline = Depends(get_loader_pipeline)):
    background_task.add_task(term_pipeline.execute)