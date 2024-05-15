import shutil

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class DDDMPWriter(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return 'dddmp'

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self.path = path
        self.source_model = source_model

    def transform(self) -> str:
        filename = f'{self.source_model.bdd_file}.{DDDMPWriter.get_destination_extension()}'
        shutil.copy(filename, self.path) 
        with open(self.path, 'r', encoding='utf8') as file:
            content = file.read()
        return content
