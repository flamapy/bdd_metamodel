from typing import Optional

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.transformations.fm_to_bdd_pl import FmToBDD as FmToBddPL
from flamapy.metamodels.fm_metamodel.transformations import FMSecureFeaturesNames


class FmToBDD(ModelToModel):
    @staticmethod
    def get_source_extension() -> str:
        return "fm"

    @staticmethod
    def get_destination_extension() -> str:
        return "bdd"

    def __init__(self, source_model: FeatureModel) -> None:
        self.source_model = source_model
        self.destination_model: Optional[BDDModel] = None

    def transform(self) -> BDDModel:
        fm_secure = FMSecureFeaturesNames(self.source_model).transform()
        bdd_model = FmToBddPL(fm_secure).transform()
        bdd_model.mapping_secure_names = fm_secure.mapping_names
        msn_inverted = {val: key for key, val in fm_secure.mapping_names.items()}
        bdd_model.mapping_secure_names_inverted = msn_inverted
        return bdd_model
