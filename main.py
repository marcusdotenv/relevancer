from dotenv import load_dotenv
from fastapi import FastAPI
from src.utils.database.db import build_try_using_db
from src.utils.cache.serializers.protobuff_serializer import ProtobuffSerializer
import redis

app = FastAPI()
load_dotenv()

trie = None
serializer = ProtobuffSerializer()
r = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.get("/terms")
async def terms(search_term: str, amount: int):
    global trie
    if trie == None:
        trie = await build_try_using_db()
        serialized = serializer.serialize(trie=trie)
        r.set("root", serialized)
    
    stored = r.get("root")
    deserialized_trie = serializer.deserialize(serialized_bytes=stored)

    return deserialized_trie.find_most_relevant(search_term=search_term, amount=amount)