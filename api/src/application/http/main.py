from dotenv import load_dotenv
from fastapi import FastAPI
from src.infrastructure.adapters.logging_config import configure_logging
from src.application.http.routers.trie import trie_router


app = FastAPI()
load_dotenv()
configure_logging()

app.include_router(trie_router)
