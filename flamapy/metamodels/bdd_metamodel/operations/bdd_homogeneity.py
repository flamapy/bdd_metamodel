from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations.descriptor import OperationDescriptor
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import Homogeneity
from flamapy.metamodels.bdd_metamodel.operations import BDDCommonalityFactor


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
    commonality_sum = 0.0
    commonality_op = BDDCommonalityFactor()

    for feature in bdd_model.features_vars.keys():
        config = Configuration(elements={feature: True})
        commonality_op.set_configuration(config)
        commonality_sum += commonality_op.execute(bdd_model).get_result()
    return commonality_sum / len(bdd_model.features_vars)

