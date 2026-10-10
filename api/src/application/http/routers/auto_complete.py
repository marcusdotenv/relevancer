import logging
from typing import Callable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel

from src.application.http.dependencies import get_loader_pipeline, get_suggestion_cache, get_suggestion_loader
from src.domain.models.term import MAX_SUGGESTED_TERMS, MAX_TERM_LENGTH, is_valid_term, normalize_term
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheContract, SuggestionCacheNotLoaded, SuggestionCacheUnavailable
from src.infrastructure.adapters.logging_config import configure_logging
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline

auto_complete_router = APIRouter()
configure_logging()

logger = logging.getLogger(__name__)

# how long a client should wait before searching again, while the suggestions are loaded
SECONDS_TO_LOAD_SUGGESTIONS = 15

class TermSelection(BaseModel):
    term: str

def validate_term(term: str) -> str:
    if not is_valid_term(term):
        raise HTTPException(
            status_code=422,
            detail=f"term can not be blank, have control characters or more than {MAX_TERM_LENGTH} characters"
        )
    return term.strip()

@auto_complete_router.get("/auto-complete", status_code=200)
async def handler(
        term: str = Query(min_length=1, max_length=MAX_TERM_LENGTH),
        amount: int = Query(ge=1, le=MAX_SUGGESTED_TERMS),
        cache: SuggestionCacheContract=Depends(get_suggestion_cache),
        load_suggestions: Callable[[], None]=Depends(get_suggestion_loader)
    ):
    term = normalize_term(validate_term(term))
    logger.info(f"auto-complete - {term}")

    try:
        return await cache.find_terms_by_prefix(prefix=term, limit=amount)

    except SuggestionCacheNotLoaded:
        # an empty list would say that no term has this prefix, and that is not known.
        # The suggestions are loaded from the term file while the client is asked to try again
        logger.warning("suggestion cache is not loaded, loading it from the term file")
        return JSONResponse(
            status_code=503,
            content={"detail": "suggestions are being loaded, try again"},
            headers={"Retry-After": str(SECONDS_TO_LOAD_SUGGESTIONS)},
            background=BackgroundTask(load_suggestions)
        )

    except SuggestionCacheUnavailable:
        logger.exception("suggestion cache can not be reached")
        raise HTTPException(status_code=503, detail="suggestions are unavailable")

@auto_complete_router.post("/auto-complete/select", status_code=204)
def handler(selection: TermSelection):
    # the pipeline counts every "search - <term>" log as one search for the term.
    # Only a term chosen by the user is logged like this: a prefix typed on auto-complete is not a search
    term = validate_term(selection.term)
    logger.info(f"search - {term}")

@auto_complete_router.post("/pipeline", status_code=204)
def handler(background_task: BackgroundTasks, term_pipeline: TermLoaderPipeline = Depends(get_loader_pipeline)):
    background_task.add_task(term_pipeline.execute)