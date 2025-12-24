from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class SVGWriter(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return "svg"

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self._path: str = path
        self._source_model: BDDModel = source_model

    def transform(self) -> str:
        self._source_model.save_bdd(self._path,
                                    [self._source_model.root],
                                    SVGWriter.get_destination_extension())
        return ""
