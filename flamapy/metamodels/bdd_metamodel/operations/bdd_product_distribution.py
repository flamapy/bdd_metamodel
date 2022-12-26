import math
from collections import defaultdict

from dd.autoref import Function

from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import ProductDistribution


class BDDProductDistribution(ProductDistribution):

    def __init__(self) -> None:
        self.result: list[int] = []
        self.bdd_model = None

    def execute(self, model: BDDModel) -> 'BDDProductDistribution':
        self.bdd_model = model
        self.result = product_distribution(self.bdd_model)
        return self

    def get_result(self) -> list[int]:
        return self.result

    def product_distribution(self) -> list[int]:
        return product_distribution(self.bdd_model)


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
    id_root = BDDModel.get_value(root, root.negated)
    dist: dict[int, list[int]] = {0: [], 1: [1]}
    mark: dict[int, bool] = defaultdict(bool)
    get_prod_dist(root, dist, mark, root.negated)
    return dist[id_root]


def get_prod_dist(node: Function, 
                  dist: dict[int, list[int]], 
                  mark: dict[int, bool], 
                  complemented: bool) -> None:
    id_node = BDDModel.get_value(node, complemented)
    mark[id_node] = not mark[id_node]

    if not BDDModel.is_terminal_node(node):

        # traverse
        low = BDDModel.get_low_node(node)
        id_low = BDDModel.get_value(low, complemented)

        if mark[id_node] != mark[id_low]:
            get_prod_dist(low, dist, mark, complemented ^ low.negated)

        # compute low_dist to account for the removed nodes through low
        removed_nodes = BDDModel.index(low) - BDDModel.index(node) - 1
        low_dist = [0] * (removed_nodes + len(dist[id_low]))
        for i in range(removed_nodes + 1):
            for j in range(len(dist[id_low])):
                low_dist[i + j] = low_dist[i + j] + dist[id_low][j] * math.comb(removed_nodes, i)

        # traverse
        high = BDDModel.get_high_node(node)
        id_high = BDDModel.get_value(high, complemented)

        high = BDDModel.get_high_node(node)
        id_high = BDDModel.get_value(high, complemented)
        if mark[id_node] != mark[id_high]:
            get_prod_dist(high, dist, mark, complemented ^ high.negated)

        # compute high_dist to account for the removed nodes through high
        removed_nodes = BDDModel.index(high) - BDDModel.index(node) - 1
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