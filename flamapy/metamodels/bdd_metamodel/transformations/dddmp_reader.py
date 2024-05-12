from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class DDDMPReader(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'dddmp'

    def __init__(self, path: str) -> None:
        self.path: str = path

    def transform(self) -> BDDModel:
        bdd_model = BDDModel()
        bdd_model.root = bdd_model.bdd.load(self.path)[0]

        bdd_model.variables = list(bdd_model.bdd.vars)
        return bdd_model
