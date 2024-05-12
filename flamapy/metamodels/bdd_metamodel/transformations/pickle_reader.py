from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class PickleReader(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'p'

    def __init__(self, path: str) -> None:
        self.path: str = path
        self.preserve_original_ordering: bool = False

    def transform(self) -> BDDModel:
        bdd_model = BDDModel()
        bdd_model.root = bdd_model.bdd.load(self.path)[0]
        bdd_model.variables = list(bdd_model.bdd.vars)
        return bdd_model
