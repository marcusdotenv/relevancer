
from fastapi import Depends
from src.infrastructure.adapters.impl.cache.redis_trie_cache import RedisTrieCache
from src.infrastructure.adapters.contracts.serializer_contract import SerializerContract
from src.infrastructure.adapters.impl.serializer.proto.protobuff_serializer import ProtobuffSerializer
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
from src.infrastructure.pipeline.impl.loki_log_source import LokiLogSource
from src.infrastructure.pipeline.impl.pyspark_term_loader_pipeline import PandasTermLoaderPipeline
from src.infrastructure.pipeline.impl.s3_term_file_storage import S3TermFileStorage


def get_cache_serializer() -> SerializerContract:
    return ProtobuffSerializer()

def get_trie_cache(serializer: SerializerContract = Depends(get_cache_serializer)) -> RedisTrieCache:
    return RedisTrieCache(serializer=serializer)

def get_log_source() -> LogSource:
    return LokiLogSource()

def get_term_storage() -> TermFileStorage:
    return S3TermFileStorage()

def get_loader_pipeline(log_source: LogSource = Depends(get_log_source), term_storage: TermFileStorage= Depends(get_term_storage)) -> TermLoaderPipeline:
    return PandasTermLoaderPipeline(log_source=log_source, term_file_sotrage=term_storage)

def get_log_source() -> LogSource:
    return LokiLogSource()