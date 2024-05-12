from typing import Any, Optional, cast
from collections import defaultdict

#from dd.autoref import Function

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber


class BDDFeatureInclusionProbability(FeatureInclusionProbability):
    """The Feature Inclusion Probability (FIP) operation determines the probability
    for a variable to be included in a valid solution.

    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models. SPLC.
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    def __init__(self, partial_configuration: Optional[Configuration] = None) -> None:
        self.result: dict[Any, float] = {}
        self.partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDFeatureInclusionProbability':
        bdd_model = cast(BDDModel, model)
        self.result = feature_inclusion_probability(bdd_model, self.partial_configuration)
        #self.result = variable_probabilities_single_traverse(bdd_model)
        return self

    def get_result(self) -> dict[Any, float]:
        return self.result

    def feature_inclusion_probability(self) -> dict[Any, float]:
        return self.get_result()


def feature_inclusion_probability(bdd_model: BDDModel,
                                  config: Optional[Configuration] = None) -> dict[Any, float]:
    n_configs_op = BDDConfigurationsNumber()
    n_configs_op.set_partial_configuration(config)
    total_configs = n_configs_op.execute(bdd_model).get_result()

    prob: dict[Any, float] = defaultdict(float)
    if config is None:
        for feature in bdd_model.variables:
            values = {feature: True}
            u_func = bdd_model.bdd.let(values, bdd_model.root)
            n_vars = len(bdd_model.variables) - len(values)
            prob[feature] = bdd_model.bdd.count(u_func, nvars=n_vars) / total_configs
    else:
        values = dict(config.elements.items())
        for feature in bdd_model.variables:
            feature_selected = values.get(feature, None)    
            values = {feature: True}
            u_func = bdd_model.bdd.let(values, bdd_model.root)
            n_vars = len(bdd_model.variables) - len(values)
            prob[feature] = bdd_model.bdd.count(u_func, nvars=n_vars) / total_configs
            if feature_selected is None:
                values.pop(feature)
            else:
                values[feature] = feature_selected
    return prob


## TODO: The following is the optimized implementation from UNED 
## Algoritm available in the paper: https://doi.org/10.1109/ICSE.2019.00091
## Currently, the implementation is not correct at all.

# def feature_inclusion_probability(bdd_model: BDDModel,
#                                   config: Optional[Configuration] = None) -> dict[Any, float]:
#     root = bdd_model.root
#     id_root = bdd_model.get_value(root, root.negated)
#     prob: dict[int, float] = defaultdict(float)
#     prob[id_root] = 1/2
#     mark: dict[int, bool] = defaultdict(bool)
#     get_node_pr(bdd_model, root, prob, mark, root.negated)

#     prob_n_phi: dict[tuple[int, Any], float] = defaultdict(float)
#     prob_phi_n: dict[tuple[int, Any], float] = defaultdict(float)
#     mark: dict[int, bool] = defaultdict(bool)
#     get_joint_pr(bdd_model, root, prob, prob_n_phi, prob_phi_n, mark, root.negated)

#     fip = {}
#     for xj in bdd_model.variables:
#         xj_node = bdd_model.get_node(xj)
#         xj_id = bdd_model.get_value(xj_node)
#         fip[xj] = prob_n_phi[xj_id] / prob[1]
#     return fip


# def get_node_pr(bdd_model: BDDModel,
#                 node: Function,
#                 prob: dict[int, float], 
#                 mark: dict[int, bool], 
#                 complemented: bool) -> None:
#     id_node = bdd_model.get_value(node, complemented)
#     mark[id_node] = not mark[id_node]

#     if not bdd_model.is_terminal_node(node):

#         # explore low
#         low = bdd_model.get_low_node(node)
#         id_low = bdd_model.get_value(low, complemented)
#         if bdd_model.is_terminal_node(low):
#             prob[id_low] = prob[id_low] + prob[id_node]
#         else:
#             prob[id_low] = prob[id_low] + (prob[id_node] / 2)
#         if mark[id_node] != mark[id_low]:
#             get_node_pr(bdd_model, low, prob, mark, complemented ^ low.negated)

#         # explore high
#         high = bdd_model.get_high_node(node)
#         id_high = bdd_model.get_value(high, complemented)
#         if bdd_model.is_terminal_node(high):
#             prob[id_high] = prob[id_high] + prob[id_node]
#         else:
#             prob[id_high] = prob[id_high] + (prob[id_node] / 2)
#         if mark[id_node] != mark[id_high]:
#             get_node_pr(bdd_model, high, prob, mark, complemented ^ high.negated)


# def get_joint_pr(bdd_model: BDDModel,
#                  node: Function,
#                  prob: dict[int, float], 
#                  prob_n_phi: dict[tuple[int, Any], float], 
#                  prob_phi_n: dict[tuple[int, Any], float],
#                  mark: dict[int, bool], 
#                  complemented: bool) -> None:
#     id_node = bdd_model.get_value(node, complemented)
#     mark[id_node] = not mark[id_node]

#     if not bdd_model.is_terminal_node(node):

#         # explore low
#         low = bdd_model.get_low_node(node)
#         id_low = bdd_model.get_value(low, complemented)
#         if bdd_model.is_terminal_n0(low):
#             prob_phi_n[(id_node, False)] = 0.0
#         elif bdd_model.is_terminal_n1(low):
#             prob_phi_n[(id_node, False)] = 1.0
#         else:
#             if mark[id_node] != mark[id_low]:
#                 get_joint_pr(bdd_model, low, prob, prob_n_phi, prob_phi_n, mark, complemented ^ low.negated)
#             prob_phi_n[(id_node, False)] = prob_phi_n[(id_low, None)] / (2 * prob[id_low])
#         prob_n_phi[(id_node, False)] = prob_phi_n[(id_node, False)] * prob[id_node]

#         # explore high
#         high = bdd_model.get_high_node(node)
#         id_high = bdd_model.get_value(high, complemented)
#         if bdd_model.is_terminal_n0(high):
#             prob_phi_n[(id_node, True)] = 0.0
#         elif bdd_model.is_terminal_n1(high):
#             prob_phi_n[(id_node, True)] = 1.0
#         else:
#             if mark[id_node] != mark[id_high]:
#                 get_joint_pr(bdd_model, high, prob, prob_n_phi, prob_phi_n, mark, complemented ^ high.negated)
#             prob_phi_n[(id_node, True)] = prob_phi_n[(id_high, None)] / (2 * prob[id_high])
#         prob_n_phi[(id_node, True)] = prob_phi_n[(id_node, True)] * prob[id_node]

#         # Combine both low and high
#         prob_phi_n[(id_node, None)] = prob_phi_n[(id_node, True)] + prob_phi_n[(id_node, False)]
#         prob_n_phi[bdd_model.index(node)] = prob[bdd_model.index(node)] + prob_n_phi[id_node]

#         # Add joint probabilities of the removed nodes
#         for xj in range(bdd_model.index(node) + 1, bdd_model.index(high)):
#             prob_n_phi[xj] = prob_n_phi[xj] + (prob_n_phi[(id_node, True)] / 2)
#         for xj in range(bdd_model.index(node) + 1, bdd_model.index(low)):
#             prob_n_phi[xj] = prob_n_phi[xj] + (prob_n_phi[(id_node, False)] / 2)
