import asyncpg
from src.entities.trie import Trie


class PostgresTermDb:
    def __init__(self, connection: asyncpg.pool.PoolAcquireContext) -> None:
        self.__connection = connection

    async def build_try_using_db(self) -> Trie:
        try:
            last_id = 0 
            trie = Trie("root")
            limit = 10000
        
            while True:
                page_terms = await self.__connection.fetch(
                    "SELECT id, term FROM terms WHERE id > $1 ORDER BY id ASC LIMIT $2;",
                    last_id, limit
                )
            
                terms = map(lambda it: it["term"], page_terms)
                trie.insert_many(terms)
                if len(page_terms) < limit:
                    break

                last_id = page_terms[-1]["id"]

            return trie
        except Exception as e:
            print(f"Error: {e}")
            return None