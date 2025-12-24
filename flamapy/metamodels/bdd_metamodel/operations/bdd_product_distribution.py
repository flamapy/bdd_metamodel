from typing import cast, Any

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import ProductDistribution


class BDDProductDistribution(ProductDistribution):
    def __init__(self) -> None:
        self._result: list[int] = []

    def execute(self, model: VariabilityModel) -> "BDDProductDistribution":
        bdd_model = cast(BDDModel, model)
        self._result = product_distribution(bdd_model)
        return self

    def get_result(self) -> list[int]:
        return self._result

    def product_distribution(self) -> list[int]:
        return self.get_result()

    def descriptive_statistics(self) -> dict[str, Any]:
        return descriptive_statistics(self._result)


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
    if bdd_model.root is None:
        return [0] * (len(bdd_model.vars_order) + 1)

    # Delegate the entire complexity to a dedicated object
    engine = DistributionEngine(bdd_model)
    return engine.run()


class DistributionEngine:
    def __init__(self, bdd_model: BDDModel):
        self.bdd = bdd_model.bdd
        self.root = bdd_model.root
        self.n = len(bdd_model.vars_order)
        self.var_to_idx = {var: i for i, var in enumerate(bdd_model.vars_order)}
        self.memo: dict[Any, list[int]] = {}

    def run(self) -> list[int]:
        # 1. Calculate recursion from the root
        raw_dist = self._solve(self.root)

        # 2. Adjust for variables skipped before the root
        root_idx = self.var_to_idx.get(self.root.var, self.n) if self.root.var else self.n
        final_dist = self._apply_skipped(raw_dist, root_idx)

        # 3. Format final output
        output = final_dist + [0] * (self.n + 1 - len(final_dist))
        return output[:self.n + 1]

    def _solve(self, node: Any) -> list[int]:
        is_complemented = node.negated
        actual_node = ~node if is_complemented else node

        if actual_node == self.bdd.true:
            res = [1]
        elif actual_node in self.memo:
            res = self.memo[actual_node]
        else:
            res = self._compute_internal_node(actual_node)
            self.memo[actual_node] = res

        if is_complemented:
            if actual_node.var:
                curr_var_idx = self.var_to_idx.get(actual_node.var, self.n)
            else:
                curr_var_idx = self.n
            return self._complement_dist(res, self.n - curr_var_idx)
        return res

    def _compute_internal_node(self, node: Any) -> list[int]:
        curr_idx = self.var_to_idx[node.var]

        # Distances to children (Don't cares)
        idx_low = self.var_to_idx.get(node.low.var, self.n) if node.low.var else self.n
        idx_high = self.var_to_idx.get(node.high.var, self.n) if node.high.var else self.n

        d_low = self._apply_skipped(self._solve(node.low), idx_low - curr_idx - 1)
        d_high = self._apply_skipped(self._solve(node.high), idx_high - curr_idx - 1)

        # Combine LOW (z^0) and HIGH (z^1)
        res = [0] * max(len(d_low), len(d_high) + 1)
        for i, v in enumerate(d_low):
            res[i] += v
        for i, v in enumerate(d_high):
            res[i+1] += v
        return res

    @staticmethod
    def _get_binom(k: int) -> list[int]:
        res = [1]
        for _ in range(k):
            res = [a + b for a, b in zip([0, *res], [*res, 0])]
        return res

    def _apply_skipped(self, dist: list[int], k: int) -> list[int]:
        if k <= 0:
            return dist
        binom = self._get_binom(k)
        new_dist = [0] * (len(dist) + k)
        for i, val in enumerate(dist):
            for j, b_val in enumerate(binom):
                new_dist[i + j] += val * b_val
        return new_dist

    def _complement_dist(self, dist: list[int], k: int) -> list[int]:
        total = self._get_binom(k)
        extended = dist + [0] * (len(total) - len(dist))
        return [t - d for t, d in zip(total, extended)]


def descriptive_statistics(prod_dist: list[int]) -> dict[str, Any]:
    """Computes statistics from a frequency distribution in O(N) time."""
    total_elements = sum(prod_dist)
    if total_elements == 0:
        return _get_empty_stats()

    # Fase 1: Limits and LLimits and Central Tendency (First pass)
    central_stats = _compute_central_tendency(prod_dist, total_elements)

    # Phase 2: Dispersion and Deviation (Second pass)
    dispersion_stats = _compute_dispersion(
        prod_dist,
        total_elements,
        central_stats["Mean"],
        central_stats["Median"]
    )

    return {**central_stats, **dispersion_stats}

def _compute_central_tendency(prod_dist: list[int], total: int) -> dict[str, Any]:
    """Calculates min, max, mode, mean and median in one pass."""
    total_sum = 0
    running_total = 0
    min_val, max_val, mode_val = None, None, 0
    max_freq = -1

    # Positions for the median
    m_pos1, m_pos2 = (total + 1) // 2, (total + 2) // 2
    med1, med2 = None, None

    for i, count in enumerate(prod_dist):
        if count <= 0:
            continue

        # Min, Max y Mode
        if min_val is None:
            min_val = i
        max_val = i
        if count > max_freq:
            max_freq, mode_val = count, i

        # Sums for the Mean
        total_sum += i * count

        # Location of Median
        running_total += count
        if med1 is None and running_total >= m_pos1:
            med1 = i
        if med2 is None and running_total >= m_pos2:
            med2 = i

    mean = total_sum / total
    median = (med1 + med2) / 2 if med1 is not None and med2 is not None else 0

    return {
        "Mean": mean,
        "Median": median,
        "Mode": mode_val,
        "Min": min_val,
        "Max": max_val,
        "Range": (max_val - min_val) if min_val is not None and max_val is not None else 0
    }

def _compute_dispersion(prod_dist: list[int],
                        total: int,
                        mean: float,
                        median: float) -> dict[str, Any]:
    """Calculates Variance and MAD in a second pass."""
    sum_squared_diff = 0.0

    # For MAD (Median Absolute Deviation) we need the median of |x_i - median|
    # We build a frequency distribution of the deviations
    abs_deviations_dist: dict[float, int] = {}

    for i, count in enumerate(prod_dist):
        if count > 0:
            # For Standard Deviation
            sum_squared_diff += count * (i - mean) ** 2

            # For MAD: we group by magnitude of deviation
            dev = abs(i - median)
            abs_deviations_dist[dev] = abs_deviations_dist.get(dev, 0) + count

    std_dev = (sum_squared_diff / total) ** 0.5
    mad = _calculate_median_from_dist(abs_deviations_dist, total)

    return {
        "Standard deviation": std_dev,
        "Median absolute deviation": mad
    }

def _calculate_median_from_dist(freq_dist: dict[float, int], total: int) -> float:
    """Helper to find the median from a frequency dictionary."""
    if not freq_dist:
        return 0.0

    sorted_devs = sorted(freq_dist.keys())
    m_pos1, m_pos2 = (total + 1) // 2, (total + 2) // 2
    running_total = 0
    res1, res2 = None, None

    for dev in sorted_devs:
        running_total += freq_dist[dev]
        if res1 is None and running_total >= m_pos1:
            res1 = dev
        if res2 is None and running_total >= m_pos2:
            res2 = dev
        if res1 is not None and res2 is not None:
            break

    return (res1 + res2) / 2 if res1 is not None and res2 is not None else 0.0

def _get_empty_stats() -> dict[str, Any]:
    return {k: (0 if "deviation" in k.lower() or "Mean" in k or "Range" in k else None)
            for k in ["Mean", "Standard deviation", "Median", "Median absolute deviation",
                      "Mode", "Min", "Max", "Range"]}
