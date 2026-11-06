from typing import Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.core.operations import SatisfiableConfiguration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    partial_assignment,
)


class BDDSatisfiableConfiguration(SatisfiableConfiguration):
    def __init__(self) -> None:
        self._result: bool = False
        self._configuration: Optional[Configuration] = None

    def set_configuration(self, configuration: Configuration) -> None:
        self._configuration = configuration

    def execute(self, model: VariabilityModel) -> "BDDSatisfiableConfiguration":
        bdd_model = cast(BDDModel, model)
        self._result = is_satisfiable(bdd_model, self._configuration)
        return self

    def get_result(self) -> bool:
        return self._result

    def is_satisfiable(self) -> bool:
        return self.get_result()


def is_satisfiable(bdd_model: BDDModel, configuration: Optional[Configuration]) -> bool:
    """Whether some product extends the configuration (every product, for a full one): the
    BDD restricted to the configuration is not the false node. No counting is needed."""
    assignment = partial_assignment(bdd_model, configuration) or {}
    root = bdd_model.bdd.let(assignment, bdd_model.root) if assignment else bdd_model.root
    return root != bdd_model.bdd.false
