
import asyncpg
from src.entities.trie import Trie

async def retrieve_terms_and_get_trie(connection: asyncpg.pool.PoolAcquireContext, limit: int) -> Trie:
    try:
        last_id = 0 
        trie = Trie("root")
        
        while True:
            page_terms = await connection.fetch(
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
