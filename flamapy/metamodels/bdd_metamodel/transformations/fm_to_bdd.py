from pathlib import Path
import tempfile

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import SPLOTWriter
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.transformations import SPLOTReader


class FmToBDD(ModelToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'fm'

    @staticmethod
    def get_destination_extension() -> str:
        return 'bdd'

    def __init__(self, source_model: FeatureModel) -> None:
        self.source_model = source_model

    def transform(self) -> BDDModel:
        with tempfile.NamedTemporaryFile(mode='w', 
                                         encoding='utf8', 
                                         suffix='.'+SPLOTWriter.get_destination_extension()
                                        ) as file:
            SPLOTWriter(path=file.name, source_model=self.source_model).transform()
            bdd_model = SPLOTReader(file.name).transform()
            bdd_model.variables = [f.name for f in self.source_model.get_features()]
        return bdd_model
