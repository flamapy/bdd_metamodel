from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Valid
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_products_number import BDDProductsNumber


class BDDValid(Valid):

    def __init__(self) -> None:
        self.result: bool = False

    def get_result(self) -> bool:
        return self.result

    def is_valid(self) -> bool:
        return self.get_result()

    def execute(self, model: VariabilityModel) -> 'BDDValid':
        bdd_model = cast(BDDModel, model)
        self.result = is_valid(bdd_model)
        return self


def is_valid(bdd_model: BDDModel) -> bool:
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    return n_configs > 0
