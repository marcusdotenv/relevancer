from abc import ABC, abstractmethod

from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage

class TermLoaderPipeline(ABC):

    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage

    def execute():
        raise Exception("not implemented")