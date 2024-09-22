from abc import ABC, abstractmethod

from src.infrastructure.pipeline.models.log_source import LogTearmSearch

class LogSource(ABC):

    @abstractmethod
    def retrieve(self) -> list[LogTearmSearch]:
        raise Exception("not implemented")