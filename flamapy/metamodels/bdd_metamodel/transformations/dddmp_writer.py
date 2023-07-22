import shutil

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.fm_metamodel.models import FeatureModel


class DDDMPWriter(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return 'dddmp'

    def __init__(self, path: str, source_model: FeatureModel) -> None:
        self.path = path + '.' + DDDMPWriter.get_destination_extension()
        self.source_model = source_model

    def transform(self) -> str:
        filename = self.source_model.get_bdd_file() + '.' + DDDMPWriter.get_destination_extension()
        shutil.copy(filename, self.path) 
        with open(self.path, 'r', encoding='utf8') as file:
            content = file.read()
        return content
