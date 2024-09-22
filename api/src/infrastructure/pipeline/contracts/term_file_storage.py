from abc import ABC, abstractmethod
import pandas as pd

class TermFileStorage(ABC):

    @abstractmethod
    def load_terms_by_filename(self, name: str) -> pd.DataFrame:
        raise Exception("not implemented")
    
    @abstractmethod
    def replace_term_file_by_name(self, name: str, updated_df: pd.DataFrame):
        raise Exception("not implemented")