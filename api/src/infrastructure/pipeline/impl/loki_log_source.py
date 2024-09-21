from src.infrastructure.pipeline.contracts.log_source import LogSource
import requests
from pydantic import BaseModel
from datetime import datetime

class LogTearmSearch(BaseModel):
    searched_at: str
    term: str

class LokiLogSource(LogSource):

    def __init__(self) -> None:
        self.__loki_base_url = "http://localhost:3100"

    def __retrieve_term_search(self, log_line: list[str]) -> LogTearmSearch:
        splitted = log_line[1].split(" - search - ")
        return LogTearmSearch(searched_at=splitted[0], term=splitted[1])
    
    def retrieve(self) -> list[LogTearmSearch]:
        today = datetime.now()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'

        query = '{job="api"} |= "- search -"'
        
        try:
            response = requests.get(
                f'{self.__loki_base_url}/loki/api/v1/query_range',
                params={
                    'query': query,
                    'start': start_date,
                    'end': end_date
                }
            )
            response.raise_for_status()

            result = response.json().get('data', {}).get('result', [])
            if not result:
                return []

            values = result[0].get("values", [])
            return list(map(self.__retrieve_term_search, values))

        except requests.exceptions.RequestException as e:
            print(f"Erro ao recuperar logs: {e}")
            return []