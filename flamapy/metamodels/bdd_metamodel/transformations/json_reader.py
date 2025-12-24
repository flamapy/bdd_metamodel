from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class JSONReader(TextToModel):
    @staticmethod
    def get_source_extension() -> str:
        return "json"

    def __init__(self, path: str) -> None:
        self.path: str = path

    def transform(self) -> BDDModel:
        return BDDModel.load_bdd(self.path)
