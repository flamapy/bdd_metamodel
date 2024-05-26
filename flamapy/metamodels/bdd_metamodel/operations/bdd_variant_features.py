from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import VariantFeatures
from flamapy.metamodels.bdd_metamodel.operations import BDDFeatureInclusionProbability


class BDDVariantFeatures(VariantFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDVariantFeatures':
        bdd_model = cast(BDDModel, model)
        self._result = variant_features(bdd_model, self._partial_configuration)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def variant_features(self) -> list[Any]:
        return self.get_result()


def variant_features(bdd_model: BDDModel,
                     config: Optional[Configuration] = None) -> list[Any]:
    fip_op = BDDFeatureInclusionProbability()
    fip_op.set_partial_configuration(config)
    probs = fip_op.execute(bdd_model).get_result()
    return [feat for feat, prob, in probs.items() if 0.0 < prob < 1.0]
