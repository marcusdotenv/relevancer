import unittest

import fakeredis

from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheNotLoaded, SuggestionCacheUnavailable
from src.infrastructure.adapters.impl.cache.redis_suggestion_cache import RedisSuggestionCache


class RedisSuggestionCacheTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.__server = fakeredis.FakeServer()
        self.__client = fakeredis.FakeRedis(server=self.__server)
        self.__cache = RedisSuggestionCache(
            client=self.__client,
            async_client=fakeredis.FakeAsyncRedis(server=self.__server)
        )

    async def test_find_terms_saved_for_the_prefix(self):
        self.__cache.save(suggestions_by_prefix={
            "ca": ["Casa de Praia", "cama", "carro"],
            "casa de": ["Casa de Praia"],
            "é": ["época"],
        })

        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="ca", limit=10), ["Casa de Praia", "cama", "carro"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="casa de", limit=10), ["Casa de Praia"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="é", limit=10), ["época"])

    async def test_find_terms_of_prefix_that_is_not_saved_from_the_longest_saved_prefix(self):
        self.__cache.save(suggestions_by_prefix={
            "c": ["Casa de Praia", "cubo"],
            "ca": ["Casa de Praia", "cama", "carro", "casaco"],
        })

        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="cas", limit=10), ["Casa de Praia", "casaco"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="casa de praia", limit=10), ["Casa de Praia"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="cas", limit=1), ["Casa de Praia"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="cu", limit=10), ["cubo"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="cab", limit=10), [])

    async def test_find_terms_respect_limit(self):
        self.__cache.save(suggestions_by_prefix={"ca": ["casa", "cama", "carro"]})

        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="ca", limit=2), ["casa", "cama"])

    async def test_find_terms_return_empty_for_unknown_prefix(self):
        self.__cache.save(suggestions_by_prefix={"ca": ["casa"]})

        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="za", limit=10), [])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="", limit=10), [])

    async def test_save_replace_everything_saved_before(self):
        self.__cache.save(suggestions_by_prefix={"ca": ["casa"], "b": ["bola"]})
        self.__cache.save(suggestions_by_prefix={"ca": ["carro"]})

        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="ca", limit=10), ["carro"])
        self.assertEqual(await self.__cache.find_terms_by_prefix(prefix="b", limit=10), [])
        # nothing is left behind by a save, like a temporary key
        self.assertEqual(len(self.__client.keys("*")), 1)

    async def test_save_without_suggestions_clean_the_cache(self):
        self.__cache.save(suggestions_by_prefix={"ca": ["casa"]})
        self.__cache.save(suggestions_by_prefix={})

        self.assertEqual(self.__client.keys("*"), [])

    async def test_find_terms_fail_when_nothing_was_saved(self):
        # no suggestions for a prefix is an answer, but an empty cache does not know the answer
        with self.assertRaises(SuggestionCacheNotLoaded):
            await self.__cache.find_terms_by_prefix(prefix="ca", limit=10)

        self.__cache.save(suggestions_by_prefix={"ca": ["casa"]})
        self.__cache.save(suggestions_by_prefix={})

        with self.assertRaises(SuggestionCacheNotLoaded):
            await self.__cache.find_terms_by_prefix(prefix="ca", limit=10)

    async def test_find_terms_fail_when_redis_can_not_be_reached(self):
        self.__cache.save(suggestions_by_prefix={"ca": ["casa"]})
        self.__server.connected = False

        with self.assertRaises(SuggestionCacheUnavailable):
            await self.__cache.find_terms_by_prefix(prefix="ca", limit=10)

        with self.assertRaises(SuggestionCacheUnavailable):
            await self.__cache.find_terms_by_prefix(prefix="za", limit=10)
