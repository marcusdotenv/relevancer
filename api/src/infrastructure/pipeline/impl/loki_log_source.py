from src.infrastructure.pipeline.contracts.log_source import LogSource
import requests
from pydantic import BaseModel
from datetime import datetime

class LogTearmSearch(BaseModel):
    frequency: int
    term: str

class LokiLogSource(LogSource):

    def __init__(self) -> None:
        self.__loki_base_url = "http://localhost:3100"

    def __retrieve_term_search(self, log_line: list[str]) -> LogTearmSearch:
        frequency =int(log_line.get("value", None)[1])
        term = log_line.get("metric", None).get("term", "")
        return LogTearmSearch(frequency=frequency, term=term)
    
    def retrieve(self) -> list[LogTearmSearch]:
        now = datetime.now()

        query = 'sum by (term)(count_over_time({job="api"} |= "search" | pattern "<timestamp> - search - <term>" | term != ""  [1d]))'
        
        try:
            response = requests.get(
                f'{self.__loki_base_url}/loki/api/v1/query',
                params={
                    'query': query,
                    'time': now.timestamp(),
                }
            )
            response.raise_for_status()

            result = response.json().get('data', {}).get('result', [])
            if not result:
                return []

            return list(map(self.__retrieve_term_search, result))

        except requests.exceptions.RequestException as e:
            print(f"Erro ao recuperar logs: {e}")
            return []