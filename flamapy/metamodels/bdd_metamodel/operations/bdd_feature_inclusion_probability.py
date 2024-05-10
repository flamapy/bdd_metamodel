from typing import Any, Optional, cast
from collections import defaultdict

from dd.autoref import Function

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurations


class BDDFeatureInclusionProbability(FeatureInclusionProbability):
    """The Feature Inclusion Probability (FIP) operation determines the probability
    for a variable to be included in a valid solution.

    This is a brute-force implementation that enumerates all solutions
    for calculating the probabilities.

    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models. SPLC.
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    def __init__(self, partial_configuration: Optional[Configuration] = None) -> None:
        self.result: dict[Any, float] = {}
        self.partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDFeatureInclusionProbability':
        bdd_model = cast(BDDModel, model)
        self.result = feature_inclusion_probability(bdd_model, self.partial_configuration)
        return self

    def get_result(self) -> dict[Any, float]:
        return self.result

    def feature_inclusion_probability(self) -> dict[Any, float]:
        return self.get_result()


def feature_inclusion_probability(bdd_model: BDDModel,
                                  config: Optional[Configuration] = None) -> dict[Any, float]:
    products = BDDConfigurations(config).execute(bdd_model).get_result()
    n_products = len(products)
    if n_products == 0:
        return {feature: 0.0 for feature in bdd_model.variables}

    prob = {}
    for feature in bdd_model.variables:
        prob[feature] = sum(feature in p.elements for p in products) / n_products
    return prob


# def feature_inclusion_probability(bdd_model: BDDModel,
#                                   config: Optional[Configuration] = None) -> dict[Any, float]:
#     root = bdd_model.root
#     id_root = BDDModel.get_value(root, root.negated)
#     prob: dict[int, float] = defaultdict(float)
#     prob[id_root] = 1/2
#     mark: dict[int, bool] = defaultdict(bool)
#     get_node_pr(root, prob, mark, root.negated)

#     prob_n_phi: dict[int, float] = defaultdict(float)
#     mark: dict[int, bool] = defaultdict(bool)
#     get_join_pr(root, prob, prob_n_phi, mark, root.negated)
#     # prob_phi = BDDModel.
#     # return dist[id_root]


def get_node_pr(node: Function,
                prob: dict[int, float], 
                mark: dict[int, bool], 
                complemented: bool) -> float:
    id_node = BDDModel.get_value(node, complemented)
    mark[id_node] = mark[id_node]
    
    if not BDDModel.is_terminal_node(node):

        # explore low
        low = BDDModel.get_low_node(node)
        id_low = BDDModel.get_value(low, complemented)
        if BDDModel.is_terminal_node(low):
            prob[id_low] = prob[id_low] + prob[id_node]
        else:
            prob[id_low] = prob[id_low] + prob[id_node]/2

        if mark[id_node] != mark[id_low]:
            get_node_pr(low, prob, mark, complemented ^ low.negated)

        # explore high
        high = BDDModel.get_high_node(node)
        id_high = BDDModel.get_value(high, complemented)
        if BDDModel.is_terminal_node(high):
            prob[id_high] = prob[id_high] + prob[id_node]
        else:
            prob[id_high] = prob[id_high] + prob[id_node]/2

        if mark[id_node] != mark[id_high]:
            get_node_pr(high, prob, mark, complemented ^ high.negated)
    

def get_join_pr(node: Function,
                prob: dict[int, float], 
                prob_n_phi: dict[int, float], 
                mark: dict[int, bool], 
                complemented: bool) -> float:
    id_node = BDDModel.get_value(node, complemented)
    mark[id_node] = mark[id_node]

    if not BDDModel.is_terminal_node(node):

        # explore low
        low = BDDModel.get_low_node(node)
        id_low = BDDModel.get_value(low, complemented)
        if low == node:
            pass


        # if BDDModel.is_terminal_node(low):
        #     prob[id_low] = prob[id_low] + prob[id_node]
        # else:
        #     prob[id_low] = prob[id_low] + prob[id_node]/2

        # if mark[id_node] != mark[id_low]:
        #     get_node_pr(low, prob, mark, complemented ^ low.negated)

        # # explore high
        # high = BDDModel.get_high_node(node)
        # id_high = BDDModel.get_value(high, complemented)
        # if BDDModel.is_terminal_node(high):
        #     prob[id_high] = prob[id_high] + prob[id_node]
        # else:
        #     prob[id_high] = prob[id_high] + prob[id_node]/2

        # if mark[id_node] != mark[id_high]:
        #     get_node_pr(high, prob, mark, complemented ^ high.negated)
    