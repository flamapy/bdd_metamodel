import re 

from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


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
        bdd_model.bdd_file = file_name
        # Read the features
        with open(self._path, 'r', encoding='utf8') as file:
            lines = file.readlines()
            varnames_line = next(line.strip() for line in lines if '.varnames' in line)
            variables = varnames_line.split(' ')[1:]
        bdd_model.variables = variables
        return bdd_model
