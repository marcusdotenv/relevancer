import os
from functools import lru_cache
from typing import Callable

import redis
import redis.asyncio
from fastapi import Depends
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheContract
from src.infrastructure.adapters.impl.cache.redis_suggestion_cache import RedisSuggestionCache
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
from src.infrastructure.pipeline.impl.loki_log_source import LokiLogSource
from src.infrastructure.pipeline.impl.pandas_term_loader_pipeline import PandasTermLoaderPipeline
from src.infrastructure.pipeline.impl.s3_term_file_storage import S3TermFileStorage


# one cache for the whole process, so every request shares the same connection pool
@lru_cache
def get_suggestion_cache() -> SuggestionCacheContract:
    host = os.getenv("CACHE_HOST")
    port = int(os.getenv("CACHE_PORT"))

    return RedisSuggestionCache(
        # the pipeline does not run on the event loop, so it has its own client
        client=redis.Redis(host=host, port=port, db=0),
        async_client=redis.asyncio.Redis(host=host, port=port, db=0)
    )

def get_log_source() -> LogSource:
    return LokiLogSource()

def get_suggestion_loader(cache: SuggestionCacheContract=Depends(get_suggestion_cache)) -> Callable[[], None]:
    # the pipeline is only created if the loader is called: a search must not pay for it
    def load_suggestions():
        pipeline = get_loader_pipeline(log_source=get_log_source(), term_storage=get_term_storage(), cache=cache)
        pipeline.load_suggestions_from_term_file()

    return load_suggestions

def get_term_storage() -> TermFileStorage:
    return S3TermFileStorage()

def get_loader_pipeline(
        log_source: LogSource = Depends(get_log_source), 
        term_storage: TermFileStorage= Depends(get_term_storage),
        cache: SuggestionCacheContract=Depends(get_suggestion_cache)
    ) -> TermLoaderPipeline:
    return PandasTermLoaderPipeline(
        log_source=log_source,
        term_file_sotrage=term_storage,
        suggestion_cache=cache,
        term_file_name=os.getenv("TERM_FILE_NAME")
    )

def get_log_source() -> LogSource:
    return LokiLogSource()