from dotenv import load_dotenv
from fastapi import FastAPI
from src.infrastructure.adapters.logging_config import configure_logging
from src.application.http.routers.auto_complete import auto_complete_router


app = FastAPI()
load_dotenv()
configure_logging()

app.include_router(auto_complete_router)
