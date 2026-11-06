from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Operation
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    partial_assignment,
)
from flamapy.metamodels.bdd_metamodel.operations.bdd_traversals import possible_literals


class BDDBackbone(Operation):
    """The backbone of the model: the core features (selected in every configuration) and the
    dead features (selected in none), grouped under the 'core' and 'dead' keys.

    Both sets come from one traversal of the BDD (see `possible_literals`), without counting.
    With a partial configuration, the backbone of the configurations that extend it: the features
    the configuration fixes are core or dead accordingly, and a configuration no product extends
    makes every feature dead and none core, as the SAT backbone does on a void model.
    """

    def __init__(self) -> None:
        self._result: dict[str, list[Any]] = {'core': [], 'dead': []}
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDBackbone':
        bdd_model = cast(BDDModel, model)
        self._result = backbone(bdd_model, self._partial_configuration)
        return self

    def get_result(self) -> dict[str, list[Any]]:
        return self._result

    def get_backbone(self) -> dict[str, list[Any]]:
        return self.get_result()


def backbone(bdd_model: BDDModel,
             configuration: Optional[Configuration] = None) -> dict[str, list[Any]]:
    """Core and dead features of the model, optionally under a partial configuration."""
    assignment = partial_assignment(bdd_model, configuration) or {}
    root = bdd_model.bdd.let(assignment, bdd_model.root) if assignment else bdd_model.root
    features = [bdd_model.vars_features[var] for var in bdd_model.vars_order]
    if root == bdd_model.bdd.false:
        return {'core': [], 'dead': features}
    can_true, can_false = possible_literals(bdd_model, root)
    core: list[Any] = []
    dead: list[Any] = []
    for var, feature, true_possible, false_possible in zip(bdd_model.vars_order, features,
                                                           can_true, can_false):
        if var in assignment:
            (core if assignment[var] else dead).append(feature)
        elif not false_possible:
            core.append(feature)
        elif not true_possible:
            dead.append(feature)
    return {'core': core, 'dead': dead}
