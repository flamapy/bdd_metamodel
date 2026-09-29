from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.transformations import CacheableModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import FMSecureFeaturesNames
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.models.bdd_model import BDD
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel


# The dd package ships two engines: 'cudd' (C extension, only when dd is built against
# CUDD) and the pure-Python 'autoref' that a plain `pip install dd` provides. Only CUDD can
# write DDDMP, so cached artifacts use DDDMP with CUDD and dd's JSON format otherwise.
DD_BACKEND = BDD.__module__.rsplit('.', 1)[-1]


class FmToBDD(CacheableModelToModel):
    """Transforms a Feature Model into a BDD Model.

    BDD compilation is the expensive step, so the transformation is cacheable: the compiled
    BDD round-trips through DDDMP (dd built with CUDD) or dd's JSON format (the pure-Python
    engine), opt-in via FLAMAPY_CACHE=1, and only the cheap feature-name mapping is
    recomputed on a cache load.
    """

    artifact_suffix = "dddmp" if DD_BACKEND == "cudd" else "json"
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

    def cache_options(self) -> dict[str, Any]:
        # Artifacts written by one dd engine are never loaded by the other.
        return {"dd_backend": DD_BACKEND}

    def dump_artifact(self, model: VariabilityModel, path: str) -> None:
        bdd_model = cast(BDDModel, model)
        if DD_BACKEND != "cudd":
            bdd_model.save_bdd(path, [bdd_model.root], "json")
            return
        # Local import: the writer imports models, keep module import light.
        from flamapy.metamodels.bdd_metamodel.transformations.dddmp_writer import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
            DDDMPWriter,
        )
        DDDMPWriter(path, bdd_model).transform()

    def load_artifact(self, path: str, source_model: VariabilityModel) -> VariabilityModel:
        if DD_BACKEND != "cudd":
            model = BDDModel.load_bdd(path)
        else:
            from flamapy.metamodels.bdd_metamodel.transformations.dddmp_reader import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
                DDDMPReader,
            )
            model = DDDMPReader(path).transform()
        fm_secure_names_op = FMSecureFeaturesNames(cast(FeatureModel, source_model))
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
