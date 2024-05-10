from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Satisfiable
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber


class BDDSatisfiable(Satisfiable):

    def __init__(self) -> None:
        self.result: bool = False

    def get_result(self) -> bool:
        return self.result

    def is_satisfiable(self) -> bool:
        return self.get_result()

    def execute(self, model: VariabilityModel) -> 'BDDSatisfiable':
        bdd_model = cast(BDDModel, model)
        self.result = is_satisfiable(bdd_model)
        return self


def is_satisfiable(bdd_model: BDDModel) -> bool:
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    return n_configs > 0
