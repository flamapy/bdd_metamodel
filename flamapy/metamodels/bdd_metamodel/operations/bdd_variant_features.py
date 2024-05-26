from typing import Any, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import VariantFeatures
from flamapy.metamodels.bdd_metamodel.operations import BDDFeatureInclusionProbability


class BDDVariantFeatures(VariantFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []

    def execute(self, model: VariabilityModel) -> 'BDDVariantFeatures':
        bdd_model = cast(BDDModel, model)
        self._result = variant_features(bdd_model)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def variant_features(self) -> list[Any]:
        return self.get_result()


def variant_features(bdd_model: BDDModel) -> list[Any]:
    feat_incl_prob = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    return [feat for feat, prob, in feat_incl_prob.items() if 0.0 < prob < 1.0]
