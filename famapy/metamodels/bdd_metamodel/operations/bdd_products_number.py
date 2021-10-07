from famapy.core.models import Configuration
from famapy.core.operations import ProductsNumber

from famapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProductsNumber(ProductsNumber):
    """It computes the number of solutions of the BDD model.
    
    It also supports counting the solutions from a given partial configuration.
    """
    
    def __init__(self, partial_configuration: Configuration=None) -> None:
        self.result = 0
        self.feature_model = None
        self.partial_configuration = partial_configuration
    
    def execute(self, bdd_model: BDDModel) -> 'BDDProductsNumber':
        self.bdd_model = bdd_model
        self.result = self.get_number_of_configurations(self.partial_configuration)
        return self

    def get_result(self) -> int:
        return self.result

    def get_number_of_configurations(self, partial_configuration: Configuration=None) -> int:
        if partial_configuration is None:
            u = self.bdd_model.root
            n_vars = len(self.bdd_model.variables)
        else:
            values = {f: selected for f, selected in partial_configuration.elements.items()}
            u = self.bdd_model.bdd.let(values, self.bdd_model.root)
            n_vars = len(self.bdd_model.variables) - len(values)
        
        return self.bdd_model.bdd.count(u, nvars=n_vars)

    def get_products_number(self) -> int:
        return self.get_number_of_configurations()
