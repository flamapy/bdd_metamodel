import re
import locale
from typing import cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import ProductDistribution


class BDDProductDistribution(ProductDistribution):
    """Computes the distribution of the number of activated features per product.

    That is,
        + How many products have 0 features activated?
        + How many products have 1 feature activated?
        + ...
        + How many products have all features activated?

    For detailed information, see the paper: 
    Heradio, R., Fernandez-Amoros, D., Mayr-Dorn, C., Egyed, A.:
    Supporting the statistical analysis of variability models. 
    In: 41st International Conference on Software Engineering (ICSE), pp. 843-853. 
    Montreal, Canada (2019).

    Return a list that stores:
        + In index 0, the number of products with 0 features activated.
        + In index 1, the number of products with 1 feature activated.
        ...
        + In index n, the number of products with n features activated.
    """

    def __init__(self) -> None:
        self.result: list[int] = []

    def get_result(self) -> list[int]:
        return self.result

    def product_distribution(self) -> list[int]:
        return self.get_result()

    def execute(self, model: VariabilityModel) -> 'BDDProductDistribution':
        bdd_model = cast(BDDModel, model)
        self.result = product_distribution(bdd_model)
        return self


def product_distribution(bdd_model: BDDModel) -> list[int]: 
    # Check bdd_file
    bdd_file = bdd_model.check_file_existence(bdd_model.get_bdd_file(), 'dddmp')

    product_distribution_process = bdd_model.run(BDDModel.PRODUCT_DISTRIBUTION, 
                                                 bdd_file)
    result = product_distribution_process.stdout.decode(locale.getdefaultlocale()[1])
    line_iterator = iter(result.splitlines())
    distribution = []
    for line in line_iterator:
        parsed_line = re.compile(r'\s+').split(line.strip())
        distribution.append(int(parsed_line[1]))
    return distribution
