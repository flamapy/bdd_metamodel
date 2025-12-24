from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.configuration_metamodel.models.configuration import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability


class BDDFeatureInclusionProbability(FeatureInclusionProbability):
    """The Feature Inclusion Probability (FIP) operation determines the probability
    for a variable to be included in a valid solution.

    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models.
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    def __init__(self) -> None:
        self._result: dict[Any, float] = {}
        self._partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Optional[Configuration]) -> None:
        self._partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> "BDDFeatureInclusionProbability":
        bdd_model = cast(BDDModel, model)
        # Handle partial configuration
        assignment = None
        if self._partial_configuration is not None:
            assignment = {bdd_model.features_vars[feat]: selected
                          for feat, selected in self._partial_configuration.elements.items()}
            if self._partial_configuration.is_full:
                for feature in bdd_model.features_vars.keys():
                    if feature not in self._partial_configuration.elements:
                        assignment[bdd_model.features_vars[feature]] = False
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

        # Total solutions in the restricted space
        self.total_sat = bdd_model.bdd.count(target_root, self.n_rem)

        # Counting stores
        self.s_count: dict[Any, int] = {}  # Solutions in sub-BDDs
        self.sol_node_total = dict.fromkeys(self.rem_vars, 0)
        self.sol_node_high = dict.fromkeys(self.rem_vars, 0)

    def run(self) -> dict[str, float]:
        if not self.rem_vars:
            return {self.bdd_model.vars_features[v]: (1.0 if self.assignment.get(v) else 0.0)
                    for v in self.bdd_model.vars_order}

        internal_nodes = self._get_internal_nodes()

        # Bottom-Up Step: Counting local solutions
        self._compute_s_counts(internal_nodes)

        # Top-Down Step: Counting paths with parity
        self._compute_path_counts(internal_nodes)

        return self._build_final_probabilities()

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
        self.w_plus = dict.fromkeys(nodes, 0.0)
        self.w_minus = dict.fromkeys(nodes, 0.0)

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

    def _build_final_probabilities(self) -> dict[str, float]:
        """Applies the final probabilistic formula for each variable."""
        final_fip = {}
        for var in self.bdd_model.vars_order:
            feat = self.bdd_model.vars_features[var]
            if var in self.assignment:
                final_fip[feat] = 1.0 if self.assignment[var] else 0.0
            else:
                # La "Fórmula Mágica"
                s_high = self.sol_node_high.get(var, 0)
                s_total = self.sol_node_total.get(var, 0)
                count_v1 = s_high + 0.5 * (self.total_sat - s_total)
                final_fip[feat] = float(count_v1) / self.total_sat if self.total_sat > 0 else 0.0
        return final_fip


def feature_inclusion_probabilities(bdd_model: BDDModel,
                                    assignment: Optional[dict[str, bool]] = None
                                   ) -> dict[str, float]:
    if assignment is None:
        assignment = {}

    # 1. Restrict the BDD root based on the partial assignment
    target_root = bdd_model.bdd.let(assignment, bdd_model.root) if assignment else bdd_model.root

    # 2. If the combination is impossible (UNSAT), all probabilities are 0
    if target_root == bdd_model.bdd.false:
        return {bdd_model.vars_features[var]: 0.0 for var in bdd_model.vars_order}

    # 3. Run the Feature Inclusion Probability Engine
    engine = FeatureInclusionEngine(bdd_model, target_root, assignment)
    return engine.run()
