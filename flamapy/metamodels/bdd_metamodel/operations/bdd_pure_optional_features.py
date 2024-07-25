from typing import Any, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import PureOptionalFeatures
from flamapy.metamodels.bdd_metamodel.operations import BDDFeatureInclusionProbability


class BDDPureOptionalFeatures(PureOptionalFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []

    def execute(self, model: VariabilityModel) -> 'BDDPureOptionalFeatures':
        bdd_model = cast(BDDModel, model)
        self._result = pure_optional_features(bdd_model)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def pure_optional_features(self) -> list[Any]:
        return self.get_result()


def pure_optional_features(bdd_model: BDDModel) -> list[Any]:
    probs = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    return [feat for feat, prob, in probs.items() if prob == 0.5]
