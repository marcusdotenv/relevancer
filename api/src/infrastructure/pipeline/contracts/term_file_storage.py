from abc import ABC, abstractmethod

class TermFileStorage(ABC):

    @abstractmethod
    def load(self):
        raise Exception("not implemented")