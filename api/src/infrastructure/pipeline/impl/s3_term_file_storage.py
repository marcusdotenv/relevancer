from io import StringIO
from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage
import boto3
import pandas as pd

class S3TermFileStorage(TermFileStorage):

    def __init__(self) -> None:
        self.__client = boto3.client('s3', endpoint_url='http://localhost:4566', 
                                           aws_access_key_id='test', 
                                           aws_secret_access_key='test'
        )
        self.__bucket_name = "trie-bucket"


    def load_terms_by_filename(self, name: str) -> pd.DataFrame:
        response = self.__client.get_object(Bucket=self.__bucket_name, Key=name)
        file_content = response['Body'].read().decode('utf-8')

        return pd.read_json(StringIO(file_content), lines=True)

    def replace_term_file_by_name(self, name: str, updated_df: pd.DataFrame):
        buffer = StringIO()
        updated_df.to_json(buffer, orient='records', lines=True)
        buffer.seek(0)
        
        self.__client.put_object(Bucket=self.__bucket_name, Key=name, Body=buffer.getvalue())