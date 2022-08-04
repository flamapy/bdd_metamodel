from typing import Optional

from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import ProductDistribution
from flamapy.metamodels.bdd_metamodel.operations import BDDProducts


class BDDProductDistribution(ProductDistribution):
    """The Product Distribution (PD) algorithm determines the number of solutions
    having a given number of variables.

    This is a brute-force implementation that enumerates all solutions for accounting them.

    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models. SPLC.
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    def __init__(self, partial_configuration: Optional[Configuration] = None) -> None:
        self.result: list[int] = []
        self.bdd_model = None
        self.partial_configuration = partial_configuration

    def execute(self, model: BDDModel) -> 'BDDProductDistribution':
        self.bdd_model = model
        self.result = product_distribution(self.bdd_model, self.partial_configuration)
        return self

    def get_result(self) -> list[int]:
        return self.result

    def product_distribution(self) -> list[int]:
        return product_distribution(self.bdd_model, self.partial_configuration)

    def serialize(self, filepath: str) -> None:
        result = self.get_result()
        serialize(result, filepath)


def product_distribution(bdd_model: BDDModel,
                         p_config: Optional[Configuration] = None) -> list[int]:
    """It accounts for how many solutions have no variables, one variable,
    two variables, ..., all variables.

    It enumerates all solutions and filters them.
    """
    products = BDDProducts(p_config).execute(bdd_model).get_result()
    dist: list[int] = []
    for i in range(len(bdd_model.variables) + 1):
        dist.append(sum(len(p.elements) == i for p in products))
    return dist


def serialize(prod_dist: list[int], filepath: str) -> None:
    with open(filepath, mode='w', encoding='utf8') as file:
        file.write('Features, Products\n')
        for features, products in enumerate(prod_dist):
            file.write(f'{features}, {products}\n')
