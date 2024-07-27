from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import UniqueFeatures


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
        for variable, feature in bdd_model.variables_features.items():
            values = {variable: True}
            u_func = bdd_model.bdd.let(values, bdd_model.root)
            n_vars = len(bdd_model.variables_features) - len(values)
            n_configs = bdd_model.bdd.count(u_func, nvars=n_vars)
            if n_configs == 1:
                unique_features_list.append(feature)
    else:
        values = {bdd_model.features_variables[f]: selected 
                  for f, selected in config.elements.items()}
        for variable, feature in bdd_model.variables_features.items():
            feature_selected = values.get(variable, None)    
            values = {variable: True}
            u_func = bdd_model.bdd.let(values, bdd_model.root)
            n_vars = len(bdd_model.variables_features) - len(values)
            n_configs = bdd_model.bdd.count(u_func, nvars=n_vars)
            if n_configs == 1:
                unique_features_list.append(feature)

            if feature_selected is None:
                values.pop(variable)
            else:
                values[variable] = feature_selected
    return unique_features_list
