import unittest

from fastapi.testclient import TestClient

from src.application.http.dependencies import get_loader_pipeline, get_suggestion_cache, get_suggestion_loader
from src.application.http.main import app
from src.domain.models.term import MAX_TERM_LENGTH
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheNotLoaded, SuggestionCacheUnavailable


class FakeSuggestionCache:
    def __init__(self) -> None:
        # like the real cache, suggestions are only found by the normalized prefix
        self.__suggestions_by_prefix = {
            "c": ["Casa de Praia", "carro"],
            "ca": ["Casa de Praia", "carro"],
        }

        self.error = None

    async def find_terms_by_prefix(self, prefix: str, limit: int) -> list[str]:
        if self.error:
            raise self.error
        return self.__suggestions_by_prefix.get(prefix, [])[:limit]


class FakeTermLoaderPipeline:
    def __init__(self) -> None:
        self.executed = False

    def execute(self):
        self.executed = True


class HttpRoutesTest(unittest.TestCase):

    def setUp(self):
        self.__pipeline = FakeTermLoaderPipeline()
        self.__cache = FakeSuggestionCache()
        self.__suggestion_loads = []
        app.dependency_overrides[get_suggestion_cache] = lambda: self.__cache
        app.dependency_overrides[get_suggestion_loader] = lambda: lambda: self.__suggestion_loads.append("loaded")
        app.dependency_overrides[get_loader_pipeline] = lambda: self.__pipeline
        self.__client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_auto_complete_return_terms_sorted_by_frequency(self):
        response = self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["Casa de Praia", "carro"])

    def test_auto_complete_return_empty_when_prefix_has_no_suggestions(self):
        response = self.__client.get("/auto-complete", params={"term": "za", "amount": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_pipeline_route_execute_pipeline(self):
        response = self.__client.post("/pipeline")

        self.assertEqual(response.status_code, 204)
        self.assertTrue(self.__pipeline.executed)

    def test_old_terms_route_was_replaced_by_auto_complete(self):
        response = self.__client.get("/terms", params={"search_term": "ca", "amount": 2})

        self.assertEqual(response.status_code, 404)

    def test_auto_complete_accept_term_with_max_length(self):
        response = self.__client.get("/auto-complete", params={"term": "c" * MAX_TERM_LENGTH, "amount": 2})

        self.assertEqual(response.status_code, 200)

    def test_auto_complete_reject_invalid_terms_without_logging_them(self):
        invalid_terms = ["", "   ", "c" * (MAX_TERM_LENGTH + 1), "casa\n2024-01-01 - search - injected"]

        for term in invalid_terms:
            with self.subTest(term=term):
                # a logged term is read by the pipeline, so an invalid one can not reach the log
                with self.assertNoLogs("src.application.http.routers.auto_complete", level="INFO"):
                    response = self.__client.get("/auto-complete", params={"term": term, "amount": 2})

                self.assertEqual(response.status_code, 422)

    def test_auto_complete_reject_amount_out_of_bounds(self):
        for amount in [-1, 0, 51]:
            with self.subTest(amount=amount):
                response = self.__client.get("/auto-complete", params={"term": "ca", "amount": amount})

                self.assertEqual(response.status_code, 422)

    def test_auto_complete_accept_amount_on_bounds(self):
        for amount in [1, 50]:
            with self.subTest(amount=amount):
                response = self.__client.get("/auto-complete", params={"term": "ca", "amount": amount})

                self.assertEqual(response.status_code, 200)

    def test_auto_complete_ignore_case_of_term(self):
        for term in ["Ca", "CA", "cA"]:
            with self.subTest(term=term):
                response = self.__client.get("/auto-complete", params={"term": term, "amount": 2})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), ["Casa de Praia", "carro"])

    def test_auto_complete_is_not_logged_as_a_search(self):
        # the pipeline counts every "search - <term>" log, and a typed prefix is not a searched term
        with self.assertLogs("src.application.http.routers.auto_complete", level="INFO") as logs:
            self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})

        self.assertFalse(any("search - " in message for message in logs.output), logs.output)

    def test_select_log_term_with_original_spelling_as_a_search(self):
        with self.assertLogs("src.application.http.routers.auto_complete", level="INFO") as logs:
            response = self.__client.post("/auto-complete/select", json={"term": " Casa de Praia "})

        self.assertEqual(response.status_code, 204)
        self.assertEqual(logs.output, ["INFO:src.application.http.routers.auto_complete:search - Casa de Praia"])

    def test_select_reject_invalid_terms_without_logging_them(self):
        invalid_terms = ["", "   ", "c" * (MAX_TERM_LENGTH + 1), "casa\n2024-01-01 - search - injected"]

        for term in invalid_terms:
            with self.subTest(term=term):
                with self.assertNoLogs("src.application.http.routers.auto_complete", level="INFO"):
                    response = self.__client.post("/auto-complete/select", json={"term": term})

                self.assertEqual(response.status_code, 422)

    def test_auto_complete_does_not_load_suggestions_when_cache_is_loaded(self):
        self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})
        self.__client.get("/auto-complete", params={"term": "za", "amount": 2})

        self.assertEqual(self.__suggestion_loads, [])

    def test_auto_complete_load_suggestions_and_ask_to_retry_when_cache_is_not_loaded(self):
        self.__cache.error = SuggestionCacheNotLoaded()

        response = self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})

        self.assertEqual(response.status_code, 503)
        self.assertIn("Retry-After", response.headers)
        self.assertEqual(self.__suggestion_loads, ["loaded"])

    def test_auto_complete_is_unavailable_when_cache_can_not_be_reached(self):
        self.__cache.error = SuggestionCacheUnavailable()

        response = self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.__suggestion_loads, [])
