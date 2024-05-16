import math
from collections import defaultdict
from typing import cast

from dd.autoref import Function

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import ProductDistribution


class BDDProductDistribution(ProductDistribution):

    def __init__(self) -> None:
        self._result: list[int] = []

    def execute(self, model: VariabilityModel) -> 'BDDProductDistribution':
        bdd_model = cast(BDDModel, model)
        self._result = product_distribution(bdd_model)
        return self

    def get_result(self) -> list[int]:
        return self._result

    def product_distribution(self) -> list[int]:
        return self.get_result()


def product_distribution(bdd_model: BDDModel) -> list[int]:
    """Computes the distribution of the number of activated features per product.

    That is,
        + How many products have 0 features activated?
        + How many products have 1 feature activated?
        + ...
        + How many products have all features activated?

    For detailed information, see the paper: 
        Heradio, R., Fernandez-Amoros, D., Mayr-Dorn, C., Egyed, A.:
        Supporting the statistical analysis of variability models. 
        In: 41st International Conference on Software Engineering (ICSE), pp. 843-853. 2019.
        DOI: https://doi.org/10.1109/ICSE.2019.00091

    The operation returns a list that stores:
        + In index 0, the number of products with 0 features activated.
        + In index 1, the number of products with 1 feature activated.
        ...
        + In index n, the number of products with n features activated.
    """
    root = bdd_model.root
    id_root = bdd_model.get_value(root, bdd_model.negated(root))
    dist: dict[int, list[int]] = {0: [], 1: [1]}
    mark: dict[int, bool] = defaultdict(bool)
    get_prod_dist(bdd_model, root, dist, mark, bdd_model.negated(root))
    # Complete distribution
    distribution = dist[id_root] + [0] * (len(bdd_model.variables) + 1 - len(dist[id_root]))
    return distribution


def get_prod_dist(bdd_model: BDDModel,
                  node: Function, 
                  dist: dict[int, list[int]], 
                  mark: dict[int, bool], 
                  complemented: bool) -> None:
    id_node = bdd_model.get_value(node, complemented)
    mark[id_node] = not mark[id_node]

    if not bdd_model.is_terminal_node(node):

        # traverse
        low = bdd_model.get_low_node(node)
        id_low = bdd_model.get_value(low, complemented)
        if mark[id_node] != mark[id_low]:
            get_prod_dist(bdd_model, low, dist, mark, complemented ^ bdd_model.negated(low))

        # compute low_dist to account for the removed nodes through low
        removed_nodes = bdd_model.index(low) - bdd_model.index(node) - 1
        low_dist = [0] * (removed_nodes + len(dist[id_low]))
        for i in range(removed_nodes + 1):
            for j in range(len(dist[id_low])):
                low_dist[i + j] = low_dist[i + j] + dist[id_low][j] * math.comb(removed_nodes, i)

        # traverse
        high = bdd_model.get_high_node(node)
        id_high = bdd_model.get_value(high, complemented)

        high = bdd_model.get_high_node(node)
        id_high = bdd_model.get_value(high, complemented)
        if mark[id_node] != mark[id_high]:
            get_prod_dist(bdd_model, high, dist, mark, complemented ^ bdd_model.negated(high))

        # compute high_dist to account for the removed nodes through high
        removed_nodes = bdd_model.index(high) - bdd_model.index(node) - 1
        high_dist = [0] * (removed_nodes + len(dist[id_high]))
        for i in range(removed_nodes + 1):
            for j in range(len(dist[id_high])):
                high_dist[i + j] = high_dist[i + j] + dist[id_high][j] * (
                    math.comb(removed_nodes, i))
        combine_distributions(id_node, dist, low_dist, high_dist)


def combine_distributions(id_node: int, 
                          dist: dict[int, list[int]], 
                          low_dist: list[int], 
                          high_dist: list[int]) -> None:
    # combine low and high distributions
    if len(low_dist) > len(high_dist):
        #dist_length = len(dist[id_low])
        dist_length = len(low_dist)
    else:
        #dist_length = len(dist[id_high]) + 1
        dist_length = len(high_dist) + 1

    node_dist = [0] * dist_length
    for i, value in enumerate(low_dist):
        node_dist[i] = value
    for i, value in enumerate(high_dist):
        node_dist[i + 1] = node_dist[i + 1] + value
    dist[id_node] = node_dist
