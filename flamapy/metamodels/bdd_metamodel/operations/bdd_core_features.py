from typing import Any, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import CoreFeatures
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations import BDDFeatureInclusionProbability


class BDDCoreFeatures(CoreFeatures):

    def __init__(self) -> None:
        self.result: list[Any] = []

    def execute(self, model: VariabilityModel) -> 'BDDCoreFeatures':
        bdd_model = cast(BDDModel, model)
        self.result = core_features(bdd_model)
        return self

    def get_result(self) -> list[Any]:
        return self.result

    def get_core_features(self) -> list[Any]:
        return self.get_result()


def core_features(bdd_model: BDDModel) -> list[Any]:
    feat_incl_prob = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    return [f for f, p in feat_incl_prob.items() if p >= 1.0]
