import re 

from famapy.core.transformations import TextToModel
from famapy.metamodels.bdd_metamodel.models import BDDModel


class DDDMPReader(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'dddmp'

    def __init__(self, path: str) -> None:
        self._path = path

    def transform(self) -> BDDModel:
        bdd_model = BDDModel()
        re_expression = '(.*)[.]' + DDDMPReader.get_source_extension()
        match = re.search(re_expression, self._path)
        if match is not None:
            file_name = match.group(1)
        bdd_model.set_bdd_file(file_name)
        return bdd_model
