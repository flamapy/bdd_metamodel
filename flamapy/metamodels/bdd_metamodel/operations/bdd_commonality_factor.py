from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Commonality
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import CommonalityFactor
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber


class BDDCommonalityFactor(CommonalityFactor):
    """The commonality of a (partial) configuration: the products that include it over all
    the products, both counted on the BDD (the plugin's ``CommonalityFactor`` interface, found
    by that name as in 2.8; the core operation is ``BDDCommonality``)."""

    def __init__(self) -> None:
        self._result: float = 0.0
        self._configuration: Configuration = Configuration(elements={})

    def set_configuration(self, configuration: Configuration) -> None:
        self._configuration = configuration

    def execute(self, model: VariabilityModel) -> "BDDCommonalityFactor":
        bdd_model = cast(BDDModel, model)
        self._result = commonality_factor(bdd_model, self._configuration)
        return self

    def get_result(self) -> float:
        return self._result

    def commonality_factor(self) -> float:
        return self.get_result()

    def get_commonality(self) -> float:
        return self.get_result()



class BDDCommonality(Commonality):
    """The core ``Commonality`` operation on the BDD (the facade's ``commonality`` with
    ``backend='bdd'``): the products that include the (partial) configuration over all the
    products. Same computation as ``BDDCommonalityFactor``."""

    def __init__(self) -> None:
        self._result: float = 0.0
        self._configuration: Configuration = Configuration(elements={})

    def set_configuration(self, configuration: Configuration) -> None:
        self._configuration = configuration

    def execute(self, model: VariabilityModel) -> "BDDCommonality":
        self._result = commonality_factor(cast(BDDModel, model), self._configuration)
        return self

    def get_result(self) -> float:
        return self._result

    def get_commonality(self) -> float:
        return self.get_result()


def commonality_factor(bdd_model: BDDModel, config: Configuration) -> float:
    configs_number_op = BDDConfigurationsNumber()
    total_configs = configs_number_op.execute(bdd_model).get_result()
    if total_configs == 0:
        return 0.0
    configs_number_op.set_partial_configuration(config)
    n_configs = configs_number_op.execute(bdd_model).get_result()
    return n_configs / total_configs
