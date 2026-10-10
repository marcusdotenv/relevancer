import unittest

import pandas as pd

from src.domain.models.suggestions import find_suggestions
from src.domain.models.term import MAX_SUGGESTED_TERMS, MAX_TERM_LENGTH
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheContract
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.impl.pandas_term_loader_pipeline import PandasTermLoaderPipeline
from src.infrastructure.pipeline.models.log_source import LogTearmSearch


class FakeLogSource(LogSource):
    def __init__(self, logs: list[LogTearmSearch]) -> None:
        self.__logs = logs
        self.retrieved_times = 0

    def retrieve(self) -> list[LogTearmSearch]:
        self.retrieved_times += 1
        return self.__logs


class FakeTermFileStorage(TermFileStorage):
    def __init__(self, files: dict[str, pd.DataFrame]) -> None:
        self.files = files
        self.loaded_times = 0
        self.replaced_times = 0
        self.on_load = lambda: None

    def load_terms_by_filename(self, name: str) -> pd.DataFrame:
        self.loaded_times += 1
        self.on_load()
        if name not in self.files:
            raise KeyError(f"The specified key does not exist: {name}")
        return self.files[name]

    def replace_term_file_by_name(self, name: str, updated_df: pd.DataFrame):
        self.replaced_times += 1
        self.files[name] = updated_df


class FakeSuggestionCache(SuggestionCacheContract):
    def __init__(self) -> None:
        self.saved_suggestions = None

    def save(self, suggestions_by_prefix: dict[str, list[str]]):
        self.saved_suggestions = suggestions_by_prefix

    async def find_terms_by_prefix(self, prefix: str, limit: int) -> list[str]:
        return find_suggestions(prefix, self.saved_suggestions)[:limit]


class PandasTermLoaderPipelineTest(unittest.TestCase):

    def setUp(self):
        self.__term_file_name = "terms.jsonl"
        self.__storage = FakeTermFileStorage(files={
            self.__term_file_name: pd.DataFrame([
                {"term": "casa", "frequency": 3},
                {"term": "carro", "frequency": 1},
            ])
        })
        self.__cache = FakeSuggestionCache()

    def __build_pipeline(self, logs: list[LogTearmSearch]) -> PandasTermLoaderPipeline:
        self.__log_source = FakeLogSource(logs=logs)
        return PandasTermLoaderPipeline(
            log_source=self.__log_source,
            term_file_sotrage=self.__storage,
            suggestion_cache=self.__cache,
            term_file_name=self.__term_file_name
        )

    def test_load_suggestions_from_configured_term_file_when_there_is_no_logs(self):
        self.__build_pipeline(logs=[]).execute()

        terms = find_suggestions("ca", self.__cache.saved_suggestions)

        self.assertEqual(terms, ["casa", "carro"])

    def test_sum_log_frequencies_and_replace_configured_term_file(self):
        logs = [LogTearmSearch(term="carro", frequency=5), LogTearmSearch(term="cama", frequency=2)]

        self.__build_pipeline(logs=logs).execute()

        terms = find_suggestions("ca", self.__cache.saved_suggestions)
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

        terms = find_suggestions("c", self.__cache.saved_suggestions)
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

        terms = find_suggestions("c", self.__cache.saved_suggestions)
        self.assertEqual(terms, ["casa"])

    def test_sum_frequencies_of_terms_that_differ_only_by_case(self):
        logs = [LogTearmSearch(term="Casa", frequency=2), LogTearmSearch(term="CASA", frequency=1)]

        self.__build_pipeline(logs=logs).execute()

        terms = find_suggestions("ca", self.__cache.saved_suggestions)
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

        terms = find_suggestions("ca", self.__cache.saved_suggestions)
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
        self.assertEqual(find_suggestions("so", self.__cache.saved_suggestions), ["Sony Turntable - PSLX350H"])

    def test_new_term_from_logs_keep_its_first_spelling(self):
        logs = [LogTearmSearch(term="Cama Box", frequency=2), LogTearmSearch(term="cama box", frequency=1)]

        self.__build_pipeline(logs=logs).execute()

        updated_file = self.__storage.files[self.__term_file_name]
        frequencies = dict(zip(updated_file["term"], updated_file["frequency"]))
        self.assertEqual(frequencies, {"casa": 3, "carro": 1, "Cama Box": 3})
        self.assertEqual(find_suggestions("cam", self.__cache.saved_suggestions), ["Cama Box"])

    def test_save_at_most_max_suggested_terms_for_a_prefix(self):
        self.__storage.files[self.__term_file_name] = pd.DataFrame([
            {"term": f"casa {number:03}", "frequency": number} for number in range(MAX_SUGGESTED_TERMS + 10)
        ])

        self.__build_pipeline(logs=[]).execute()

        terms = find_suggestions("casa", self.__cache.saved_suggestions)
        self.assertEqual(len(terms), MAX_SUGGESTED_TERMS)
        self.assertEqual(terms[0], f"casa {MAX_SUGGESTED_TERMS + 9:03}")

    def test_load_suggestions_from_term_file_does_not_count_logs_again(self):
        logs = [LogTearmSearch(term="carro", frequency=5)]

        self.__build_pipeline(logs=logs).load_suggestions_from_term_file()

        self.assertEqual(find_suggestions("ca", self.__cache.saved_suggestions), ["casa", "carro"])
        self.assertEqual(self.__log_source.retrieved_times, 0)
        self.assertEqual(self.__storage.replaced_times, 0)

    def test_load_suggestions_from_term_file_is_skipped_while_another_load_is_running(self):
        pipeline = self.__build_pipeline(logs=[])
        # another load is asked in the middle of the first one
        self.__storage.on_load = pipeline.load_suggestions_from_term_file

        pipeline.load_suggestions_from_term_file()

        self.assertEqual(self.__storage.loaded_times, 1)
        self.assertEqual(find_suggestions("ca", self.__cache.saved_suggestions), ["casa", "carro"])

    def test_load_suggestions_from_term_file_can_run_again_after_a_failure(self):
        pipeline = self.__build_pipeline(logs=[])
        terms = self.__storage.files.pop(self.__term_file_name)

        with self.assertRaises(KeyError):
            pipeline.load_suggestions_from_term_file()

        self.__storage.files[self.__term_file_name] = terms
        pipeline.load_suggestions_from_term_file()

        self.assertEqual(find_suggestions("ca", self.__cache.saved_suggestions), ["casa", "carro"])
