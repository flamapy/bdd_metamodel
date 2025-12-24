import random
from dataclasses import dataclass
from typing import Optional, cast, Any

from flamapy.core.models import VariabilityModel
from flamapy.core.exceptions import FlamaException
from flamapy.core.operations import Sampling
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class BDDSampling(Sampling):
    """Uniform Random Sampling (URS) using a Binary Decision Diagram (BDD).

    This is an adaptation of
    [Heradio et al. 2021.
    Uniform and Scalable Sampling of Highly Configurable Systems.
    Empirical Software Engineering]
    which relies on counting-based sampling inspired in the original Knuth algorithm.

    This implementation supports samples with and without replacement,
    as well as samples from a given partial configuration.
    """

    def __init__(self) -> None:
        self._result: list[Configuration] = []
        self._sample_size: int = 0
        self._with_replacement: bool = False
        self._partial_configuration: Optional[Configuration] = None

    def set_sample_size(self, sample_size: int) -> None:
        if sample_size < 0:
            raise FlamaException(f"Sample size {sample_size} cannot be negative.")
        self._sample_size = sample_size

    def set_with_replacement(self, with_replacement: bool) -> None:
        self._with_replacement = with_replacement

    def set_partial_configuration(self, partial_configuration: Configuration) -> None:
        self._partial_configuration = partial_configuration

    def get_result(self) -> list[Configuration]:
        return self._result

    def get_sample(self) -> list[Configuration]:
        return self.get_result()

    def execute(self, model: VariabilityModel) -> "BDDSampling":
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
        self._result = get_random_solutions(
            bdd_model, self._sample_size, self._with_replacement, assignment
        )
        return self


@dataclass
class SamplingContext:
    target_root: Any
    remaining_vars: list[str]
    s_count: dict[Any, tuple[int, int]]
    assignment: dict[str, bool]
    vars_features: dict[str, Any]


def get_random_solutions(bdd_model: BDDModel,
                         n_samples: int,
                         with_replacement: bool = False,
                         assignment: Optional[dict[str, bool]] = None
                        ) -> list[dict[str, bool]]:
    """Generates a list of random valid configurations using BDD sampling."""
    assignment = assignment or {}

    # 1. Restriction and initial validation
    target_root = bdd_model.bdd.let(assignment, bdd_model.root) if assignment else bdd_model.root
    if target_root == bdd_model.bdd.false:
        return []

    remaining_vars = [v for v in bdd_model.vars_order if v not in assignment]
    total_sat = bdd_model.bdd.count(target_root, len(remaining_vars))

    if not with_replacement:
        n_samples = min(n_samples, total_sat)

    # 2. Precomputation of weights for sampling
    context = SamplingContext(
        target_root=target_root,
        remaining_vars=remaining_vars,
        s_count=_precompute_solution_counts(target_root, remaining_vars),
        assignment=assignment,
        vars_features=bdd_model.vars_features
    )

    # 3. Sampling loop
    return _perform_sampling(context, n_samples, with_replacement)


def _precompute_solution_counts(target_root: Any,
                                remaining_vars: list[str]) -> dict[Any, tuple[int, int]]:
    """Calculates the number of solutions for each branch of the BDD (Dynamic Programming)."""
    n_rem = len(remaining_vars)
    var_to_idx = {var: i for i, var in enumerate(remaining_vars)}
    actual_root = ~target_root if target_root.negated else target_root

    # Get internal nodes sorted by level (bottom-up)
    internal_nodes = _get_sorted_internal_nodes(actual_root, var_to_idx)
    s_count: dict[Any, tuple[int, int]] = {}

    for u in internal_nodes:
        u_idx = var_to_idx[u.var]

        def get_branch_sol(child: Any) -> int:
            c_idx = var_to_idx[child.var] if child.var else n_rem
            if child.var is None:
                val = 0 if child.negated else 1
            else:
                act_c = ~child if child.negated else child
                val = sum(s_count[act_c])
                if child.negated:
                    val = (2 ** (n_rem - c_idx)) - val
            return val * (2 ** (c_idx - u_idx - 1))

        s_count[u] = (get_branch_sol(u.low), get_branch_sol(u.high))

    return s_count


def _get_sorted_internal_nodes(root: Any, var_to_idx: dict[Any, int]) -> list[Any]:
    """Extracts and sorts internal nodes of the BDD using BFS."""
    if root.var is None:
        return []

    nodes = [root]
    visited = {root}
    idx = 0
    while idx < len(nodes):
        u = nodes[idx]
        idx += 1
        for child in [u.low, u.high]:
            act_c = ~child if child.negated else child
            if act_c.var is not None and act_c not in visited:
                visited.add(act_c)
                nodes.append(act_c)

    return sorted(nodes, key=lambda x: var_to_idx[x.var], reverse=True)


def _perform_sampling(ctx: SamplingContext,
                      n_samples: int,
                      with_replacement: bool) -> list[dict[Any, bool]]:
    """Executes the weighted random selection process."""
    results: list[dict[Any, bool]] = []
    seen_configs = set()
    actual_root = ~ctx.target_root if ctx.target_root.negated else ctx.target_root

    while len(results) < n_samples:
        config_vals = _sample_one_config(actual_root, ctx.target_root.negated, ctx)
        config_tuple = tuple(sorted(config_vals.items()))
        if with_replacement or config_tuple not in seen_configs:
            seen_configs.add(config_tuple)
            full_config = {**ctx.assignment, **config_vals}
            results.append({ctx.vars_features[k]: v for k, v in full_config.items()})

    return results


def _sample_one_config(actual_root: Any,
                       is_negated: bool,
                       ctx: SamplingContext) -> dict[Any, bool]:
    """Generates a single valid configuration by traversing the BDD."""
    config = {}
    u = actual_root
    n_rem = len(ctx.remaining_vars)
    for i, var in enumerate(ctx.remaining_vars):
        if u.var == var:
            s_low, s_high = ctx.s_count[u]
            # Adjust if the path has odd parity
            if is_negated:
                s_low_eff = (2 ** (n_rem - i - 1)) - s_low
                s_high_eff = (2 ** (n_rem - i - 1)) - s_high
            else:
                s_low_eff, s_high_eff = s_low, s_high

            if random.random() < (s_high_eff / (s_low_eff + s_high_eff)):
                config[var], edge = True, u.high
            else:
                config[var], edge = False, u.low

            if edge.negated:
                is_negated = not is_negated
            u = ~edge if edge.negated else edge
        else:
            config[var] = random.choice([True, False])
    return config
