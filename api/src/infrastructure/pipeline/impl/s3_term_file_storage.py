from src.infrastructure.pipeline.contracts.term_file_storage import TermFileStorage


class S3TermFileStorage(TermFileStorage):

    def load(self):
        return super().load()