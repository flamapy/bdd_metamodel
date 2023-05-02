from flamapy.core.operations import Valid

from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_products_number import BDDProductsNumber


class BDDValid(Valid):

    def __init__(self) -> None:
        self.result = None
        self.bdd_model = None

    def execute(self, model: BDDModel) -> 'BDDValid':
        self.bdd_model = model
        self.result = is_valid(self.bdd_model)
        return self

    def get_result(self) -> bool:
        return self.result

    def is_valid(self) -> bool:
        return is_valid(self.bdd_model)


def is_valid(bdd_model: BDDModel) -> bool:
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    return n_configs > 0