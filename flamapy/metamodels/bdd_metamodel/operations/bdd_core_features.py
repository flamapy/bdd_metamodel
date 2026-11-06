from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.core.operations import CoreFeatures
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    exact_feature_inclusion,
)


class BDDCoreFeatures(CoreFeatures):
    def __init__(self) -> None:
        self._result: list[Any] = []
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> "BDDCoreFeatures":
        bdd_model = cast(BDDModel, model)
        self._result = core_features(bdd_model, self._partial_configuration)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def get_core_features(self) -> list[Any]:
        return self.get_result()


def core_features(bdd_model: BDDModel, config: Optional[Configuration] = None) -> list[Any]:
    probs = exact_feature_inclusion(bdd_model, config)
    return [feat for feat, prob in probs.items() if prob == 1]
