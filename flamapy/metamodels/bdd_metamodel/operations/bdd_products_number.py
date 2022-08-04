from typing import Optional

from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.core.operations import ProductsNumber
from flamapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProductsNumber(ProductsNumber):
    """It computes the number of solutions of the BDD model.

    It also supports counting the solutions from a given partial configuration.
    """

    def __init__(self, partial_configuration: Optional[Configuration] = None) -> None:
        self.result = 0
        self.bdd_model = None
        self.feature_model = None
        self.partial_configuration = partial_configuration

    def execute(self, model: BDDModel) -> 'BDDProductsNumber':
        self.bdd_model = model
        self.result = products_number(self.bdd_model, self.partial_configuration)
        return self

    def get_result(self) -> int:
        return self.result

    def get_products_number(self) -> int:
        return products_number(self.bdd_model, self.partial_configuration)


def products_number(bdd_model: BDDModel,
                    partial_configuration: Optional[Configuration] = None) -> int:
    if partial_configuration is None:
        u_func = bdd_model.root
        n_vars = len(bdd_model.variables)
    else:
        values = dict(partial_configuration.elements.items())
        u_func = bdd_model.bdd.let(values, bdd_model.root)
        n_vars = len(bdd_model.variables) - len(values)

    return bdd_model.bdd.count(u_func, nvars=n_vars)
