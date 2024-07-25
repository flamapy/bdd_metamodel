from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import UniqueFeatures
from flamapy.metamodels.bdd_metamodel.operations.bdd_configurations_number import count


class BDDUniqueFeatures(UniqueFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDUniqueFeatures':
        bdd_model = cast(BDDModel, model)
        self._result = unique_features(bdd_model, self._partial_configuration)
        return self

    def get_result(self) -> list[Any]:
        return self._result

    def unique_features(self) -> list[Any]:
        return self.get_result()


def unique_features(bdd_model: BDDModel,
                    config: Optional[Configuration] = None) -> list[Any]:
    unique_features_list = []
    if config is None:
        assignments = []
    else:
        assignments = [str(f) if selected else f'not {f}' for f, selected 
                       in config.elements.items()]
    for feature in bdd_model.variables:
        feature_safename = bdd_model.original_features_names[str(feature)]
        n_configs = count(bdd_model, assignments + [feature_safename])
        if n_configs == 1:
            unique_features_list.append(feature)
    return unique_features_list
