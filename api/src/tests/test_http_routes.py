import unittest

from fastapi.testclient import TestClient

from src.application.http.dependencies import get_loader_pipeline, get_trie_cache
from src.application.http.main import app
from src.domain.models.trie import Trie


class FakeTrieCache:
    def __init__(self) -> None:
        self.__trie = Trie("root")
        self.__trie.insert("casa", 3)
        self.__trie.insert("carro", 1)

    def exists(self, term: str) -> bool:
        return term[0] == "c"

    def retrieve(self, term: str) -> Trie:
        return self.__trie


class FakeTermLoaderPipeline:
    def __init__(self) -> None:
        self.executed = False

    def execute(self):
        self.executed = True


class HttpRoutesTest(unittest.TestCase):

    def setUp(self):
        self.__pipeline = FakeTermLoaderPipeline()
        app.dependency_overrides[get_trie_cache] = lambda: FakeTrieCache()
        app.dependency_overrides[get_loader_pipeline] = lambda: self.__pipeline
        self.__client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_auto_complete_return_terms_sorted_by_frequency(self):
        response = self.__client.get("/auto-complete", params={"term": "ca", "amount": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["casa", "carro"])

    def test_auto_complete_return_empty_when_partition_is_not_cached(self):
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
