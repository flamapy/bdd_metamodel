from famapy.core.models import Configuration
from famapy.core.operations import ProductsNumber

from famapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProductsNumber(ProductsNumber):
    """It computes the number of solutions of the BDD model.

    It also supports counting the solutions from a given partial configuration.
    """

    def __init__(self, partial_configuration: Configuration = None) -> None:
        self.result = 0
        self.bdd_model = None
        self.feature_model = None
        self.partial_configuration = partial_configuration

    def execute(self, model: BDDModel) -> 'BDDProductsNumber':
        self.bdd_model = model
        self.result = self.get_number_of_configurations(self.partial_configuration)
        return self

    def get_result(self) -> int:
        return self.result

    def get_number_of_configurations(self, partial_configuration: Configuration = None) -> int:
        if partial_configuration is None:
            u_func = self.bdd_model.root
            n_vars = len(self.bdd_model.variables)
        else:
            values = dict(partial_configuration.elements.items())
            u_func = self.bdd_model.bdd.let(values, self.bdd_model.root)
            n_vars = len(self.bdd_model.variables) - len(values)

        return self.bdd_model.bdd.count(u_func, nvars=n_vars)

    def get_products_number(self) -> int:
        return self.get_number_of_configurations()
