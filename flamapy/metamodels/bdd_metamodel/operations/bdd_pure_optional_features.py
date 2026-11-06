from fractions import Fraction
from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations.descriptor import OperationDescriptor
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import PureOptionalFeatures
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    exact_feature_inclusion,
)


class BDDPureOptionalFeatures(PureOptionalFeatures):

    facade = OperationDescriptor(
        doc=(
            'Returns features with a feature inclusion probability of exactly 0.5, meaning\n'
            'they are selected in exactly half of the valid configurations. These are the\n'
            'most unconstrained optional features.'
        ),
        returns='Union[None, List[str]]',
        name='pure_optional_features', operation='BDDPureOptionalFeatures', default_backend='bdd'
    )
    def __init__(self) -> None:
        self._result: list[Any] = []
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> "BDDPureOptionalFeatures":
        bdd_model = cast(BDDModel, model)
        self._result = pure_optional_features(bdd_model, self._partial_configuration)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def pure_optional_features(self) -> list[Any]:
        return self.get_result()


def pure_optional_features(
    bdd_model: BDDModel, config: Optional[Configuration] = None
) -> list[Any]:
    probs = exact_feature_inclusion(bdd_model, config)
    return [feat for feat, prob in probs.items() if prob == Fraction(1, 2)]
