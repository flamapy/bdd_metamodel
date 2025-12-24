from typing import Optional

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import FMSecureFeaturesNames
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel


class FmToBDD(ModelToModel):
    """Transforms a Feature Model into a BDD Model."""

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
        fm_secure_names_op = FMSecureFeaturesNames(self.source_model)
        self.source_model = fm_secure_names_op.transform()

        pl_model = PLModel()
        formula = pl_model.build_from_feature_model(self.source_model)
        self.destination_model = BDDModel()
        self.destination_model.build_bdd(formula, list(pl_model.variables))

        self.destination_model.features_vars = fm_secure_names_op.mapping_names
        self.destination_model.vars_features = {
            v: f for f, v in self.destination_model.features_vars.items()
        }
        # Attached the original model for operations that may need it
        self.destination_model.original_model = self.source_model
        return self.destination_model
