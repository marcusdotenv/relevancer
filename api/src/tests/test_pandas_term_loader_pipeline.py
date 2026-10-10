import unittest

import pandas as pd

from src.domain.models.term import MAX_TERM_LENGTH
from src.domain.models.trie import Trie
from src.infrastructure.adapters.contracts.trie_cache_contract import TrieCacheContract
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.impl.pandas_term_loader_pipeline import PandasTermLoaderPipeline
from src.infrastructure.pipeline.models.log_source import LogTearmSearch


class FakeLogSource(LogSource):
    def __init__(self, logs: list[LogTearmSearch]) -> None:
        self.__logs = logs

    def retrieve(self) -> list[LogTearmSearch]:
        return self.__logs


class FakeTermFileStorage(TermFileStorage):
    def __init__(self, files: dict[str, pd.DataFrame]) -> None:
        self.files = files

    def load_terms_by_filename(self, name: str) -> pd.DataFrame:
        if name not in self.files:
            raise KeyError(f"The specified key does not exist: {name}")
        return self.files[name]

    def replace_term_file_by_name(self, name: str, updated_df: pd.DataFrame):
        self.files[name] = updated_df


class FakeTrieCache(TrieCacheContract):
    def __init__(self) -> None:
        self.saved_trie = None

    def save(self, trie: Trie):
        self.saved_trie = trie

    def retrieve(self, term: str) -> Trie:
        return self.saved_trie

    def exists(self, term: str) -> bool:
        return self.saved_trie is not None


class PandasTermLoaderPipelineTest(unittest.TestCase):

    def setUp(self):
        self.__term_file_name = "terms.jsonl"
        self.__storage = FakeTermFileStorage(files={
            self.__term_file_name: pd.DataFrame([
                {"term": "casa", "frequency": 3},
                {"term": "carro", "frequency": 1},
            ])
        })
        self.__cache = FakeTrieCache()

    def __build_pipeline(self, logs: list[LogTearmSearch]) -> PandasTermLoaderPipeline:
        return PandasTermLoaderPipeline(
            log_source=FakeLogSource(logs=logs),
            term_file_sotrage=self.__storage,
            trie_cache=self.__cache,
            term_file_name=self.__term_file_name
        )

    def test_load_trie_from_configured_term_file_when_there_is_no_logs(self):
        self.__build_pipeline(logs=[]).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("ca", 10)

        self.assertEqual(terms, ["casa", "carro"])

    def test_sum_log_frequencies_and_replace_configured_term_file(self):
        logs = [LogTearmSearch(term="carro", frequency=5), LogTearmSearch(term="cama", frequency=2)]

        self.__build_pipeline(logs=logs).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("ca", 10)
        self.assertEqual(terms, ["carro", "casa", "cama"])

        self.assertEqual(list(self.__storage.files.keys()), [self.__term_file_name])
        updated_file = self.__storage.files[self.__term_file_name]
        frequencies = dict(zip(updated_file["term"], updated_file["frequency"]))
        self.assertEqual(frequencies, {"casa": 3, "carro": 6, "cama": 2})

    def test_discard_invalid_terms_from_logs(self):
        too_long_term = "c" * (MAX_TERM_LENGTH + 1)
        logs = [
            LogTearmSearch(term=too_long_term, frequency=9),
            LogTearmSearch(term="ca\tma", frequency=9),
            LogTearmSearch(term="cama", frequency=2),
        ]

        self.__build_pipeline(logs=logs).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("c", 10)
        self.assertEqual(terms, ["casa", "cama", "carro"])

        updated_file = self.__storage.files[self.__term_file_name]
        self.assertEqual(sorted(updated_file["term"]), ["cama", "carro", "casa"])

    def test_discard_invalid_terms_from_term_file_when_there_is_no_logs(self):
        too_long_term = "c" * (MAX_TERM_LENGTH + 1)
        self.__storage.files[self.__term_file_name] = pd.DataFrame([
            {"term": "casa", "frequency": 3},
            {"term": too_long_term, "frequency": 9},
        ])

        self.__build_pipeline(logs=[]).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("c", 10)
        self.assertEqual(terms, ["casa"])

    def test_sum_frequencies_of_terms_that_differ_only_by_case(self):
        logs = [LogTearmSearch(term="Casa", frequency=2), LogTearmSearch(term="CASA", frequency=1)]

        self.__build_pipeline(logs=logs).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("ca", 10)
        self.assertEqual(terms, ["casa", "carro"])

        updated_file = self.__storage.files[self.__term_file_name]
        frequencies = dict(zip(updated_file["term"], updated_file["frequency"]))
        self.assertEqual(frequencies, {"casa": 6, "carro": 1})
        self.assertEqual(len(updated_file), 2)

    def test_sum_frequencies_of_term_file_duplicates_when_there_is_no_logs(self):
        self.__storage.files[self.__term_file_name] = pd.DataFrame([
            {"term": "Carro", "frequency": 2},
            {"term": "casa", "frequency": 3},
            {"term": "carro", "frequency": 2},
        ])

        self.__build_pipeline(logs=[]).execute()

        terms = self.__cache.saved_trie.find_terms_by_prefix("ca", 10)
        self.assertEqual(terms, ["Carro", "casa"])

    def test_keep_spelling_of_term_file_when_logs_have_other_spelling(self):
        self.__storage.files[self.__term_file_name] = pd.DataFrame([
            {"term": "Sony Turntable - PSLX350H", "frequency": 1},
        ])
        logs = [LogTearmSearch(term="sony turntable - pslx350h", frequency=7)]

        self.__build_pipeline(logs=logs).execute()

        updated_file = self.__storage.files[self.__term_file_name]
        frequencies = dict(zip(updated_file["term"], updated_file["frequency"]))
        self.assertEqual(frequencies, {"Sony Turntable - PSLX350H": 8})
        self.assertEqual(self.__cache.saved_trie.find_terms_by_prefix("so", 10), ["Sony Turntable - PSLX350H"])

    def test_new_term_from_logs_keep_its_first_spelling(self):
        logs = [LogTearmSearch(term="Cama Box", frequency=2), LogTearmSearch(term="cama box", frequency=1)]

        self.__build_pipeline(logs=logs).execute()

        updated_file = self.__storage.files[self.__term_file_name]
        frequencies = dict(zip(updated_file["term"], updated_file["frequency"]))
        self.assertEqual(frequencies, {"casa": 3, "carro": 1, "Cama Box": 3})
        self.assertEqual(self.__cache.saved_trie.find_terms_by_prefix("cam", 10), ["Cama Box"])
