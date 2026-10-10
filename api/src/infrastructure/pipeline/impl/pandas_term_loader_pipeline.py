from src.domain.models.term import is_valid_term, normalize_term
from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.trie_cache_contract import TrieCacheContract
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
import pandas as pd
import logging
logger = logging.getLogger(__name__)

class PandasTermLoaderPipeline(TermLoaderPipeline):
    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage, trie_cache: TrieCacheContract, term_file_name: str) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage
        self.__trie_cache = trie_cache
        self.__term_file_name = term_file_name
    
    def __discard_invalid_terms(self, terms: pd.DataFrame) -> pd.DataFrame:
        valid_terms = terms[terms['term'].map(is_valid_term)]

        discarded_amount = len(terms) - len(valid_terms)
        if discarded_amount > 0:
            logger.warning(f"{discarded_amount} invalid terms was discarded")

        return valid_terms

    def __sum_frequency_of_same_terms(self, terms: pd.DataFrame) -> pd.DataFrame:
        valid_terms = self.__discard_invalid_terms(terms=terms[['term', 'frequency']])
        normalized_terms = valid_terms['term'].map(normalize_term)

        # spellings of the same term become one term: the first spelling is kept and the frequencies are summed
        return valid_terms.groupby(normalized_terms, as_index=False, sort=False).agg(term=('term', 'first'), frequency=('frequency', 'sum'))

    def execute(self):
        logger.info("Starting pipeline")
        aggregated_logs = self.__log_source.retrieve()
        dict_logs = list(map(lambda it: it.model_dump(), aggregated_logs))

        logger.info(f"Log Source returned {len(dict_logs)} aggregated searched terms")

        log_terms = pd.DataFrame(dict_logs)
        new_trie = Trie(partition_name="root")

        known_terms = self.__term_file_storage.load_terms_by_filename(name=self.__term_file_name)

        if len(log_terms) == 0:
            known_terms = self.__sum_frequency_of_same_terms(terms=known_terms)
            known_terms.apply(lambda row: new_trie.insert(row['term'], row['frequency']), axis=1)
            logger.info(f"Usign {self.__term_file_name} to fill trie")
        else:
            # known terms come first, so their spelling is the one kept when a log has another spelling
            updated_terms = self.__sum_frequency_of_same_terms(terms=pd.concat([known_terms, log_terms]))
            logger.info(f"Locally, the terms was updated")

            self.__term_file_storage.replace_term_file_by_name(name=self.__term_file_name, updated_df=updated_terms)
            logger.info(f"Term File Storage updated the file {self.__term_file_name}")

            updated_terms.apply(lambda row: new_trie.insert(row['term'], row['frequency']), axis=1)

        self.__trie_cache.save(trie=new_trie)
        logger.info("The udpated trie was loaded on trie cache")
