from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations.descriptor import OperationDescriptor
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import Homogeneity
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    feature_inclusion_fractions,
)


class BDDHomogeneity(Homogeneity):

    facade = OperationDescriptor(
        doc=(
            'Measures how similar the products of the feature model are to each other. It\n'
            'is computed as the average commonality factor across all features. A value of\n'
            '1.0 means all products are identical; lower values indicate more diversity.'
        ),
        returns='Union[None, float]',
        name='homogeneity', operation='BDDHomogeneity', default_backend='bdd'
    )
    def __init__(self) -> None:
        self._result: float = 0.0

    def execute(self, model: VariabilityModel) -> "BDDHomogeneity":
        bdd_model = cast(BDDModel, model)
        self._result = homogeneity(bdd_model)
        return self

    def get_result(self) -> float:
        return self._result

    def homogeneity(self) -> float:
        return self.get_result()


def homogeneity(bdd_model: BDDModel) -> float:
    """The mean commonality factor of the features.

    The commonality factor of a feature is its inclusion probability, so the mean of the exact
    probabilities (one traversal of the BDD for every feature) is the homogeneity.
    """
    fractions = feature_inclusion_fractions(bdd_model)
    if not fractions:
        return 0.0
    return float(sum(fractions.values()) / len(fractions))
