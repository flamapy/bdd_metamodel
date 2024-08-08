from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.core.operations import SatisfiableConfiguration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber


class BDDSatisfiableConfiguration(SatisfiableConfiguration):

    def __init__(self) -> None:
        self._result: bool = False
        self._configuration: Optional[Configuration] = None
        self._is_full: bool = False

    def set_configuration(self, configuration: Configuration, is_full: bool) -> None:
        self._configuration = configuration
        self._is_full = is_full

    def execute(self, model: VariabilityModel) -> 'BDDSatisfiableConfiguration':
        bdd_model = cast(BDDModel, model)
        self._result = is_satisfiable(bdd_model, self._configuration, self._is_full)
        return self

    def get_result(self) -> bool:
        return self._result

    def is_satisfiable(self) -> bool:
        return self.get_result()


def is_satisfiable(bdd_model: BDDModel,
                   configuration: Optional[Configuration],
                   is_full: bool) -> bool:
    config_number_op = BDDConfigurationsNumber()
    if not is_full:
        config_number_op.set_partial_configuration(configuration)
    else:
        config = Configuration(dict(configuration.elements))
        for feature in bdd_model.features_variables.keys():
            if feature not in config.elements:
                config.elements[feature] = False
        config_number_op.set_partial_configuration(config)
    n_configs = config_number_op.execute(bdd_model).get_result()
    return n_configs > 0
