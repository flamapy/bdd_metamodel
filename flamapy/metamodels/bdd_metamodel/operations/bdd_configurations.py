from typing import Any, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Configurations
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber, BDDSampling


class BDDConfigurations(Configurations):

    def __init__(self) -> None:
        self.result: list[Any] = []

    def execute(self, model: VariabilityModel) -> 'BDDConfigurations':
        bdd_model = cast(BDDModel, model)
        self.result = configurations(bdd_model)
        return self

    def get_result(self) -> list[Any]:
        return self.result

    def get_configurations(self) -> list[Any]:
        return self.get_result()


def configurations(bdd_model: BDDModel) -> list[Any]:
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    sampling_op = BDDSampling()
    sampling_op.set_sample_size(n_configs)
    return sampling_op.execute(bdd_model).get_result()
