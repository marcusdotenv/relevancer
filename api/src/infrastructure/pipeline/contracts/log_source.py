from abc import ABC, abstractmethod

class LogSource(ABC):

    @abstractmethod
    def retrieve(self):
        raise Exception("not implemented")