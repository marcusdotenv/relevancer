
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline
import pandas as pd


class PandasTermLoaderPipeline(TermLoaderPipeline):
    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage
    
    def execute(self):
        aggregated_logs = self.__log_source.retrieve()
        dict_logs = list(map(lambda it: it.model_dump(), aggregated_logs))
        log_terms = pd.DataFrame(dict_logs)

        known_terms = self.__term_file_storage.load_terms_by_filename(name="default.json")

        updated_terms = known_terms.merge(log_terms, on='term', how='outer', suffixes=('', '_new'))

        updated_terms['frequency'] = updated_terms['frequency'].fillna(0).astype(int) + updated_terms['frequency_new'].fillna(0).astype(int)

        updated_terms = updated_terms[['term', 'frequency']]

        self.__term_file_storage.replace_term_file_by_name(name="default.json", updated_df=updated_terms)
