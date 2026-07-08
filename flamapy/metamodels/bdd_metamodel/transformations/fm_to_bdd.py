from typing import Optional

from flamapy.core.models import VariabilityModel
from flamapy.core.transformations import CacheableModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import FMSecureFeaturesNames
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel


class FmToBDD(CacheableModelToModel):
    """Transforms a Feature Model into a BDD Model.

    BDD compilation is the expensive step, so the transformation is cacheable: the compiled
    BDD round-trips through the DDDMP serialization (opt-in via FLAMAPY_CACHE=1), and only
    the cheap feature-name mapping is recomputed on a cache load.
    """

    artifact_suffix = "dddmp"
    artifact_format_version = 1

    @staticmethod
    def get_source_extension() -> str:
        return "fm"

    @staticmethod
    def get_destination_extension() -> str:
        return "bdd"

    def __init__(self, source_model: FeatureModel) -> None:
        self.source_model = source_model
        self.destination_model: Optional[BDDModel] = None

    def dump_artifact(self, model: VariabilityModel, path: str) -> None:
        # Local import: the writer imports models, keep module import light.
        from flamapy.metamodels.bdd_metamodel.transformations.dddmp_writer import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
            DDDMPWriter,
        )
        DDDMPWriter(path, model).transform()  # type: ignore[arg-type]

    def load_artifact(self, path: str, source_model: VariabilityModel) -> VariabilityModel:
        from flamapy.metamodels.bdd_metamodel.transformations.dddmp_reader import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
            DDDMPReader,
        )
        model = DDDMPReader(path).transform()
        fm_secure_names_op = FMSecureFeaturesNames(source_model)  # type: ignore[arg-type]
        secured_model = fm_secure_names_op.transform()
        model.features_vars = fm_secure_names_op.mapping_names
        model.vars_features = {v: f for f, v in model.features_vars.items()}
        model.original_model = secured_model
        return model

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
