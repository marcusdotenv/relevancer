from src.domain.models.suggestions import build_suggestions_by_prefix
from src.domain.models.term import MAX_SUGGESTED_TERMS, is_valid_term, normalize_term
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheContract
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
import pandas as pd
import logging
import threading
logger = logging.getLogger(__name__)

# only one load of suggestions from the term file by process, no matter how many requests ask for it
load_suggestions_lock = threading.Lock()

class PandasTermLoaderPipeline(TermLoaderPipeline):
    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage, suggestion_cache: SuggestionCacheContract, term_file_name: str) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage
        self.__suggestion_cache = suggestion_cache
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
        known_terms = self.__term_file_storage.load_terms_by_filename(name=self.__term_file_name)

        if len(log_terms) == 0:
            updated_terms = self.__sum_frequency_of_same_terms(terms=known_terms)
        else:
            # known terms come first, so their spelling is the one kept when a log has another spelling
            updated_terms = self.__sum_frequency_of_same_terms(terms=pd.concat([known_terms, log_terms]))
            logger.info(f"Locally, the terms was updated")

            self.__term_file_storage.replace_term_file_by_name(name=self.__term_file_name, updated_df=updated_terms)
            logger.info(f"Term File Storage updated the file {self.__term_file_name}")

        self.__save_suggestions(terms=updated_terms)

    def load_suggestions_from_term_file(self):
        """Fills the cache with the terms already counted, without reading logs or changing the term file."""
        if not load_suggestions_lock.acquire(blocking=False):
            logger.info("Suggestions are already being loaded from the term file")
            return

        try:
            logger.info(f"Loading suggestions from {self.__term_file_name}")
            known_terms = self.__term_file_storage.load_terms_by_filename(name=self.__term_file_name)
            self.__save_suggestions(terms=self.__sum_frequency_of_same_terms(terms=known_terms))
        finally:
            load_suggestions_lock.release()

    def __save_suggestions(self, terms: pd.DataFrame):
        logger.info(f"Usign {len(terms)} terms to build suggestions")
        suggestions_by_prefix = build_suggestions_by_prefix(
            terms=zip(terms['term'], terms['frequency']),
            limit=MAX_SUGGESTED_TERMS
        )
        logger.info(f"Suggestions was built for {len(suggestions_by_prefix)} prefixes")

        self.__suggestion_cache.save(suggestions_by_prefix=suggestions_by_prefix)
        logger.info("The updated suggestions was loaded on suggestion cache")
