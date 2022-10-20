from pathlib import Path

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import SPLOTWriter
from famapy.metamodels.bdd_metamodel.models import BDDModel
from famapy.metamodels.bdd_metamodel.transformations import SPLOTReader


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
        splot_filepath = self.source_model.root.name
        SPLOTWriter(path=splot_filepath, source_model=self.source_model).transform()
        bdd_model = SPLOTReader(splot_filepath).transform()
        Path(splot_filepath + '.' + SPLOTWriter.get_destination_extension()).unlink()
        return bdd_model
