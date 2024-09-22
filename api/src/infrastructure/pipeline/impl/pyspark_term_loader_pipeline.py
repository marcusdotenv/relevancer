
from src.infrastructure.pipeline.contracts.log_source import LogSource
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
from src.infrastructure.pipeline.contracts.term_loader_pipeline import TermLoaderPipeline


class PysparkTermLoaderPipeline(TermLoaderPipeline):
    def __init__(self, log_source: LogSource, term_file_sotrage: TermFileStorage) -> None:
        self.__log_source = log_source
        self.__term_file_storage = term_file_sotrage
    
    def execute(self):
        print("here i am")
        print(self.__log_source.retrieve())

        # process

        #self.__term_file_storage.load()
