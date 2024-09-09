from fastapi import FastAPI
from src.utils.database.db import *
from src.utils.database.seed.retrieve_trie import build_try_using_db

app = FastAPI()
load_dotenv()

trie = None

@app.get("/terms")
async def terms(search_term: str, amount: int):
    global trie
    if trie == None:
        db = await get_connection()
        trie = await build_try_using_db(db, 10000)

        await release_connection(db)
    return trie.find_most_relevant(search_term=search_term, amount=amount)