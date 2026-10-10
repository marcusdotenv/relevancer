import json

import redis
import redis.asyncio

from src.domain.models.suggestions import find_suggestions, prefixes_of
from src.infrastructure.adapters.contracts.suggestion_cache_contract import SuggestionCacheContract, SuggestionCacheNotLoaded, SuggestionCacheUnavailable

# a redis hash where each field is a prefix and each value is the json list of the top terms of the prefix.
# Not every prefix is a field: see build_suggestions_by_prefix
SUGGESTIONS_KEY = "suggestions"
NEW_SUGGESTIONS_KEY = "suggestions:new"
SAVE_BATCH_SIZE = 5000

class RedisSuggestionCache(SuggestionCacheContract):
    def __init__(self, client: redis.Redis, async_client: redis.asyncio.Redis) -> None:
        self.__client = client
        self.__async_client = async_client

    def save(self, suggestions_by_prefix: dict[str, list[str]]):
        suggestions = [
            (prefix, json.dumps(terms, ensure_ascii=False))
            for prefix, terms in suggestions_by_prefix.items()
        ]

        self.__client.delete(NEW_SUGGESTIONS_KEY)
        for start in range(0, len(suggestions), SAVE_BATCH_SIZE):
            self.__client.hset(NEW_SUGGESTIONS_KEY, mapping=dict(suggestions[start:start + SAVE_BATCH_SIZE]))

        if not suggestions:
            self.__client.delete(SUGGESTIONS_KEY)
            return

        # searches see all the old suggestions or all the new ones, and old prefixes do not survive
        self.__client.rename(NEW_SUGGESTIONS_KEY, SUGGESTIONS_KEY)

    async def find_terms_by_prefix(self, prefix: str, limit: int) -> list[str]:
        # the prefix may not be saved, so all the shorter ones are read together to find the longest saved
        prefixes = prefixes_of(prefix)
        if not prefixes:
            return []

        try:
            saved_suggestions = await self.__async_client.hmget(SUGGESTIONS_KEY, prefixes)

            suggestions_by_prefix = {}
            for saved_prefix, suggestions in reversed(list(zip(prefixes, saved_suggestions))):
                if suggestions is not None:
                    suggestions_by_prefix[saved_prefix] = json.loads(suggestions)
                    break

            # no saved prefix is the answer of a loaded cache for an unknown prefix, but it is also what an empty cache answers
            if not suggestions_by_prefix and not await self.__async_client.exists(SUGGESTIONS_KEY):
                raise SuggestionCacheNotLoaded()
        except redis.exceptions.RedisError as error:
            raise SuggestionCacheUnavailable() from error

        return find_suggestions(prefix, suggestions_by_prefix)[:limit]
