from typing import cast, Any, Generator

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Operation
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_product_distribution import DistributionEngine


class BDDConfigurationsWithNFeatures(Operation):

    def __init__(self) -> None:
        self._result: Generator[Configuration, None, None]
        self.n_features: int = 0

    def set_n_features(self, n_features: int) -> None:
        self.n_features = n_features

    def execute(self, model: VariabilityModel) -> "BDDConfigurationsWithNFeatures":
        bdd_model = cast(BDDModel, model)
        self._result = get_configs_with_n_features(bdd_model, self.n_features)
        return self

    def get_result(self) -> Generator[Configuration, None, None]:
        return self._result

    def configurations_with_n_features(self) -> Generator[Configuration, None, None]:
        return self.get_result()


class _NFeatureConfigHelper:
    """Private class to manage the state of generation and reduce complexity."""

    def __init__(self, bdd_model: BDDModel) -> None:
        self.bdd = bdd_model.bdd
        self.vars_order = bdd_model.vars_order
        self.n_vars = len(self.vars_order)
        self.var_to_idx = {var: i for i, var in enumerate(self.vars_order)}

        # Initialize the distribution engine
        self.engine = DistributionEngine(bdd_model)
        self.engine.run()

    def get_count_at(self, node: Any, var_idx: int, k: int) -> int:
        """Determines how many solutions exist from this point."""
        if k < 0 or k > (self.n_vars - var_idx):
            return 0

        dist = self.engine._solve(node)
        node_v = str(getattr(node, 'var', None))
        node_v_idx = self.var_to_idx.get(node_v, self.n_vars)
        skipped = node_v_idx - var_idx

        final_dist = self.engine._apply_skipped(dist, skipped)
        return final_dist[k] if k < len(final_dist) else 0

    def backtrack(self, node: Any, var_idx: int, k: int,
                  current_path: list[bool]) -> Generator[Configuration, None, None]:
        """Recursive backtracking algorithm with pruning."""
        if var_idx == self.n_vars:
            if k == 0 and self.get_count_at(node, var_idx, 0) > 0:
                yield Configuration({self.vars_order[i]: current_path[i]
                                     for i in range(self.n_vars)})
            return

        if self.get_count_at(node, var_idx, k) == 0:
            return

        node_v = str(getattr(node, 'var', None))
        node_v_idx = self.var_to_idx.get(node_v, self.n_vars)

        if node_v_idx == var_idx:
            yield from self._handle_node_match(node, var_idx, k, current_path)
        else:
            yield from self._handle_skipped_var(node, var_idx, k, current_path)

    def _handle_node_match(self, node: Any, var_idx: int, k: int,
                           current_path: list[bool]) -> Generator[Configuration, None, None]:
        """Processes when the BDD variable matches the current index."""
        is_comp = node.negated
        actual = ~node if is_comp else node
        l_child = ~actual.low if is_comp else actual.low
        h_child = ~actual.high if is_comp else actual.high

        # False branch
        current_path.append(False)
        yield from self.backtrack(l_child, var_idx + 1, k, current_path)
        current_path.pop()

        # True branch
        if k > 0:
            current_path.append(True)
            yield from self.backtrack(h_child, var_idx + 1, k - 1, current_path)
            current_path.pop()

    def _handle_skipped_var(self, node: Any, var_idx: int, k: int,
                            current_path: list[bool]) -> Generator[Configuration, None, None]:
        """Processes skipped variables (Don't Care)."""
        # Try False
        current_path.append(False)
        yield from self.backtrack(node, var_idx + 1, k, current_path)
        current_path.pop()

        # Try True
        if k > 0:
            current_path.append(True)
            yield from self.backtrack(node, var_idx + 1, k - 1, current_path)
            current_path.pop()

def get_configs_with_n_features(bdd_model: BDDModel,
                                target_n: int) -> Generator[Configuration, None, None]:
    """Generate configurations with exactly target_n features."""
    helper = _NFeatureConfigHelper(bdd_model)
    yield from helper.backtrack(bdd_model.root, 0, target_n, [])
