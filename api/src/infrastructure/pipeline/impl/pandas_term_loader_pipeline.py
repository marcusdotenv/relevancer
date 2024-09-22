from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.trie_cache_contract import TrieCacheContract
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
import pandas as pd
import logging
logger = logging.getLogger(__name__)

class PandasTermLoaderPipeline(TermLoaderPipeline):
    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage, trie_cache: TrieCacheContract) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage
        self.__trie_cache = trie_cache
    
    def execute(self):
        logger.info("Starting pipeline")
        aggregated_logs = self.__log_source.retrieve()
        dict_logs = list(map(lambda it: it.model_dump(), aggregated_logs))

        logger.info(f"Log Source returned {len(dict_logs)} aggregated searched terms")

        log_terms = pd.DataFrame(dict_logs)

        known_terms = self.__term_file_storage.load_terms_by_filename(name="default.json")
        updated_terms = known_terms.merge(log_terms, on='term', how='outer', suffixes=('', '_new'))
        updated_terms['frequency'] = updated_terms['frequency'].fillna(0).astype(int) + updated_terms['frequency_new'].fillna(0).astype(int)
        updated_terms = updated_terms[['term', 'frequency']]

        logger.info(f"Locally, the terms was updated")

        self.__term_file_storage.replace_term_file_by_name(name="default.json", updated_df=updated_terms)

        logger.info("Term File Storage updated the file default.json")

        new_trie = Trie(partition_name="root")

        updated_terms.apply(lambda row: new_trie.insert(row['term'], row['frequency']), axis=1)

        logger.info("A new local trie was generated")
        self.__trie_cache.save(trie=new_trie)

        logger.info("The udpated trie was loaded on trie cache")
