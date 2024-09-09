import os
import asyncpg
from dotenv import load_dotenv

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
    if pool is None:
        await create_pool()
    return await pool.acquire()

async def release_connection(conn):
    await pool.release(conn)

