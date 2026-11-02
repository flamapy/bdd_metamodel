from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations.descriptor import OperationDescriptor
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import Variability
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber, BDDVariantFeatures


class BDDVariability(Variability):

    facade = OperationDescriptor(
        doc=(
            'Returns a tuple of (total_variability, partial_variability). Total variability\n'
            'is the ratio of valid configurations to the theoretical maximum; partial\n'
            'variability is the ratio relative to only the variant features.'
        ),
        returns='Union[None, Tuple[float, float]]',
        name='variability', operation='BDDVariability', default_backend='bdd'
    )
    def __init__(self) -> None:
        self._result: tuple[float, float] = (0.0, 0.0)

    def execute(self, model: VariabilityModel) -> "BDDVariability":
        bdd_model = cast(BDDModel, model)
        self._result = variability(bdd_model)
        return self

    def get_result(self) -> tuple[float, float]:
        return self._result

    def total_variability(self) -> float:
        return self.get_result()[0]

    def partial_variability(self) -> float:
        return self.get_result()[1]


def variability(bdd_model: BDDModel) -> tuple[float, float]:
    """(total, partial) variability as defined in FLAME (see the Variability interface):
    configurations / (2^n - 1), with n all the features or only the variant ones. Partial
    variability is 0 when there are no variant features (void model or a single configuration).
    """
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    total_variability = n_configs / (2 ** len(bdd_model.vars_order) - 1)
    variant_features = BDDVariantFeatures().execute(bdd_model).get_result()
    if not variant_features:
        return (total_variability, 0.0)
    partial_variability = n_configs / (2 ** len(variant_features) - 1)
    return (total_variability, partial_variability)
