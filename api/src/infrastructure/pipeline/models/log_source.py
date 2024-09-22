from pydantic import BaseModel


class LogTearmSearch(BaseModel):
    frequency: int
    term: str