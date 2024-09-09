import os
import asyncpg
from dotenv import load_dotenv

from src.entities.trie import Trie

load_dotenv()

db_config = {
    'host': os.getenv("DATABASE_HOST"),
    'database': os.getenv("DATABASE_NAME"),
    'user': os.getenv("DATABASE_USER"),
    'password': os.getenv("DATABASE_PASSWD"),
    'port': os.getenv("DATABASE_PORT"),
}

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(**db_config, min_size=1, max_size=50)

async def get_connection() -> asyncpg.pool.PoolAcquireContext:
    global pool
    if pool is None:
        await create_pool()
    return await pool.acquire()

async def release_connection(conn):
    global pool
    await pool.release(conn)

async def build_trie_from_db() -> Trie:
    connection = await get_connection()
    try:
        last_id = 0 
        trie = Trie("root")
        limit = 10000
        
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
    finally:
        await release_connection(conn=connection)
