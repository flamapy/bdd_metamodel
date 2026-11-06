from fractions import Fraction
from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations.descriptor import OperationDescriptor
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability


class BDDFeatureInclusionProbability(FeatureInclusionProbability):
    """The Feature Inclusion Probability (FIP) operation determines the probability
    for a variable to be included in a valid solution.

    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models.
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    facade = OperationDescriptor(
        doc=(
            'Returns a mapping from each feature name to its inclusion probability: the\n'
            'fraction of valid configurations in which that feature is selected. Core\n'
            'features have probability 1.0 and dead features have probability 0.0.'
        ),
        returns='Union[None, Dict[str, float]]',
        name='feature_inclusion_probability', operation='BDDFeatureInclusionProbability',
        default_backend='bdd',
    )

    def __init__(self) -> None:
        self._result: dict[Any, float] = {}
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> "BDDFeatureInclusionProbability":
        bdd_model = cast(BDDModel, model)
        assignment = partial_assignment(bdd_model, self._partial_configuration)
        self._result = feature_inclusion_probabilities(bdd_model, assignment)
        return self

    def get_result(self) -> dict[Any, float]:
        return self._result

    def feature_inclusion_probability(self) -> dict[Any, float]:
        return self.get_result()


class FeatureInclusionEngine:
    def __init__(self, bdd_model: BDDModel, target_root: Any, assignment: dict[Any, bool]) -> None:
        self.bdd_model = bdd_model
        self.target_root = target_root
        self.assignment = assignment

        # Variables not assigned
        self.rem_vars = [v for v in bdd_model.vars_order if v not in assignment]
        self.n_rem = len(self.rem_vars)
        self.var_to_idx = {var: i for i, var in enumerate(self.rem_vars)}

        # Total solutions in the restricted space, computed exactly in run(): every count is
        # a Python int, as the counts of large models do not fit in a float (and the CUDD
        # engine's count() returns a float).
        self.total_sat = 0

        # Counting stores
        self.s_count: dict[Any, int] = {}  # Solutions in sub-BDDs
        self.sol_node_total = dict.fromkeys(self.rem_vars, 0)
        self.sol_node_high = dict.fromkeys(self.rem_vars, 0)

    def run(self) -> dict[str, Fraction]:
        if not self.rem_vars:
            return {self.bdd_model.vars_features[v]: Fraction(1 if self.assignment.get(v) else 0)
                    for v in self.bdd_model.vars_order}

        internal_nodes = self._get_internal_nodes()

        # Bottom-Up Step: Counting local solutions
        self._compute_s_counts(internal_nodes)
        self.total_sat = self._get_branch_sol(self.target_root, -1)

        # Top-Down Step: Counting paths with parity
        self._compute_path_counts(internal_nodes)

        return self._build_final_fractions()

    def _get_internal_nodes(self) -> list[Any]:
        """Gets and sorts the internal nodes of the restricted BDD."""
        actual_root = ~self.target_root if self.target_root.negated else self.target_root
        if actual_root.var is None:
            return []

        nodes = [actual_root]
        visited = {actual_root}
        idx = 0
        while idx < len(nodes):
            u = nodes[idx]
            idx += 1
            for child in [u.low, u.high]:
                act_c = ~child if child.negated else child
                if act_c.var is not None and act_c not in visited:
                    visited.add(act_c)
                    nodes.append(act_c)
        return nodes

    def _get_branch_sol(self, child: Any, u_idx: int) -> int:
        """Calculates the solutions of a branch considering skipped variables."""
        c_idx = self.var_to_idx.get(child.var, self.n_rem)
        if child.var is None:
            val = 0 if child.negated else 1
        else:
            act_c = ~child if child.negated else child
            val = self.s_count[act_c]
            if child.negated:
                val = (2 ** (self.n_rem - c_idx)) - val
        return val * (2 ** (c_idx - u_idx - 1))

    def _compute_s_counts(self, nodes: list[Any]) -> None:
        """Bottom-Up step to fill s_count."""
        nodes.sort(key=lambda x: self.var_to_idx[x.var], reverse=True)
        for u in nodes:
            u_idx = self.var_to_idx[u.var]
            self.s_count[u] = self._get_branch_sol(u.low, u_idx) + \
                              self._get_branch_sol(u.high, u_idx)

    def _compute_path_counts(self, nodes: list[Any]) -> None:
        """Bottom-Up step to fill s_count."""
        self.w_plus: dict[Any, int] = dict.fromkeys(nodes, 0)
        self.w_minus: dict[Any, int] = dict.fromkeys(nodes, 0)

        actual_root = ~self.target_root if self.target_root.negated else self.target_root
        root_idx = self.var_to_idx.get(actual_root.var, self.n_rem)

        if self.target_root.negated:
            self.w_minus[actual_root] = 2 ** root_idx
        else:
            self.w_plus[actual_root] = 2 ** root_idx

        nodes.sort(key=lambda x: self.var_to_idx[x.var])
        for u in nodes:
            u_idx = self.var_to_idx[u.var]
            self._update_node_accumulators(u, u_idx)
            self._propagate_w(u, u_idx)

    def _update_node_accumulators(self, u: Any, u_idx: int) -> None:
        """Calculates the accumulated weight using the class attributes."""
        wp = self.w_plus[u]
        wm = self.w_minus[u]

        # Total solutions
        self.sol_node_total[u.var] += wp * self.s_count[u] + \
                                      wm * ((2 ** (self.n_rem - u_idx)) - self.s_count[u])

        # High branch solutions
        s_h_adj = self._get_branch_sol(u.high, u_idx)
        self.sol_node_high[u.var] += wp * s_h_adj + \
                                     wm * ((2 ** (self.n_rem - u_idx - 1)) - s_h_adj)

    def _propagate_w(self, u: Any, u_idx: int) -> None:
        """Propagates the weights."""
        wp = self.w_plus[u]
        wm = self.w_minus[u]

        for branch in ['low', 'high']:
            edge = getattr(u, branch)
            act_c = ~edge if edge.negated else edge
            if act_c.var is not None:
                c_idx = self.var_to_idx[act_c.var]
                skip_factor = 2 ** (c_idx - u_idx - 1)
                if not edge.negated:
                    self.w_plus[act_c] += wp * skip_factor
                    self.w_minus[act_c] += wm * skip_factor
                else:
                    self.w_plus[act_c] += wm * skip_factor
                    self.w_minus[act_c] += wp * skip_factor

    def _build_final_fractions(self) -> dict[str, Fraction]:
        """The exact inclusion probability of each variable, as a fraction of two integers."""
        final_fip: dict[str, Fraction] = {}
        for var in self.bdd_model.vars_order:
            feat = self.bdd_model.vars_features[var]
            if var in self.assignment:
                final_fip[feat] = Fraction(1 if self.assignment[var] else 0)
            else:
                # Solutions with var = 1: those through a node of var taking its high branch,
                # plus half of those that skip var. Exact integers, no division until the caller
                # asks for a float: decisions such as "core" (= 1) or "dead" (= 0) must not be
                # taken on a float, as on models with many configurations a probability within
                # 1e-16 of 1 rounds to 1.0 and one below ~1e-308 underflows to 0.0.
                s_high = self.sol_node_high.get(var, 0)
                s_total = self.sol_node_total.get(var, 0)
                count_v1_twice = 2 * s_high + (self.total_sat - s_total)
                final_fip[feat] = (Fraction(count_v1_twice, 2 * self.total_sat)
                                   if self.total_sat > 0 else Fraction(0))
        return final_fip


def partial_assignment(bdd_model: BDDModel,
                       configuration: Optional[Configuration]) -> Optional[dict[Any, bool]]:
    """The BDD variable assignment of a (partial or full) configuration, or None."""
    if configuration is None:
        return None
    assignment = {bdd_model.features_vars[feat]: selected
                  for feat, selected in configuration.elements.items()}
    if configuration.is_full:
        for feature in bdd_model.features_vars.keys():
            if feature not in configuration.elements:
                assignment[bdd_model.features_vars[feature]] = False
    return assignment


def feature_inclusion_probabilities(bdd_model: BDDModel,
                                    assignment: Optional[dict[str, bool]] = None
                                   ) -> dict[str, float]:
    """Inclusion probability of each feature, as a float (see feature_inclusion_fractions)."""
    return {feat: float(prob)
            for feat, prob in feature_inclusion_fractions(bdd_model, assignment).items()}


def exact_feature_inclusion(bdd_model: BDDModel,
                            configuration: Optional[Configuration] = None
                            ) -> dict[str, Fraction]:
    """Exact inclusion probability of each feature under a configuration.

    Use it, not the floats, to decide whether a feature is core (== 1), dead (== 0), variant
    (strictly between) or pure optional (== 1/2).
    """
    return feature_inclusion_fractions(bdd_model, partial_assignment(bdd_model, configuration))


def feature_inclusion_fractions(bdd_model: BDDModel,
                                assignment: Optional[dict[str, bool]] = None
                               ) -> dict[str, Fraction]:
    """Exact inclusion probability of each feature, as a Fraction."""
    if assignment is None:
        assignment = {}

    # 1. Restrict the BDD root based on the partial assignment
    target_root = bdd_model.bdd.let(assignment, bdd_model.root) if assignment else bdd_model.root

    # 2. If the combination is impossible (UNSAT), all probabilities are 0
    if target_root == bdd_model.bdd.false:
        return {bdd_model.vars_features[var]: Fraction(0) for var in bdd_model.vars_order}

    # 3. Run the Feature Inclusion Probability Engine
    engine = FeatureInclusionEngine(bdd_model, target_root, assignment)
    return engine.run()
