import importlib
import logging
import sys
from enum import Enum
from typing import Any, Iterable, Optional

try:
    from dd.cudd import BDD
except ImportError:
    from dd.autoref import BDD

from flamapy.core.models import VariabilityModel

logger = logging.getLogger(__name__)

# The dd engine in use: 'cudd' (C extension, only when dd is built against CUDD) or the
# pure-Python 'autoref'. dd's Linux x86_64 wheels include CUDD; elsewhere `pip install dd` builds
# dd from source with the pure-Python engine only.
DD_BACKEND = BDD.__module__.rsplit('.', 1)[-1]
_reorder = importlib.import_module(BDD.__module__).reorder  # sifting, in both engines

# Dynamic reordering while building (see BDDModel.build_bdd_incremental): sift once the
# manager holds REORDER_MIN_NODES nodes, then again each time it grows by REORDER_GROWTH
# since the last reordering. Small BDDs are never reordered: sifting thousands of variables
# costs more than it saves on a BDD that stays small.
REORDER_MIN_NODES = 50_000
REORDER_GROWTH = 2.0

# The pure-Python engine recurses once per BDD level (and the node-walking operations too),
# so Python's recursion limit must grow with the number of variables.
_RECURSION_BASE = 1_000
_RECURSION_PER_VARIABLE = 4


def exact_count(bdd: Any, node: Any, nvars: int) -> int:
    """Exact model count of `node` over `nvars` variables, with Python integers.

    Works on any dd engine with complement edges: the nodes of the support are counted
    bottom-up (without recursion) over the levels of the support, and the variables outside
    the support double the count.
    """
    def regular(edge: Any) -> Any:
        return ~edge if edge.negated else edge

    nodes: list[Any] = []
    seen: set[Any] = set()
    top = regular(node)
    stack = [top] if top.var is not None else []
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        nodes.append(current)
        for edge in (current.low, current.high):
            child = regular(edge)
            if child.var is not None and child not in seen:
                stack.append(child)
    level = {var: bdd.level_of_var(var) for var in {n.var for n in nodes}}
    rank = {var: i for i, var in enumerate(sorted(level, key=level.__getitem__))}
    n_support = len(rank)
    counts: dict[Any, int] = {}

    def edge_count(edge: Any, parent_rank: int) -> int:
        """Models of `edge` over the support variables below `parent_rank`."""
        if edge.var is None:
            value, child_rank = (0 if edge.negated else 1), n_support
        else:
            child_rank = rank[edge.var]
            value = counts[regular(edge)]
            if edge.negated:
                value = 2 ** (n_support - child_rank) - value
        return value * 2 ** (child_rank - parent_rank - 1)

    for current in sorted(nodes, key=lambda n: rank[n.var], reverse=True):
        current_rank = rank[current.var]
        counts[current] = (edge_count(current.low, current_rank)
                           + edge_count(current.high, current_rank))
    return edge_count(node, -1) * 2 ** max(nvars - n_support, 0)


def ensure_recursion_limit(n_variables: int) -> None:
    """Raise Python's recursion limit, if needed, for BDDs over `n_variables` variables."""
    needed = _RECURSION_BASE + _RECURSION_PER_VARIABLE * n_variables
    if sys.getrecursionlimit() < needed:
        sys.setrecursionlimit(needed)


class BDDModel(VariabilityModel):
    """A Binary Decision Diagram (BDD) representation of the feature model.

    It relies on the dd library: https://pypi.org/project/dd/
    """

    class LogicConnective(Enum):
        NOT = "!"
        OR = "|"
        AND = "&"
        IMPLIES = "=>"
        EQUIVALENCE = "<=>"
        XOR = "^"

    @staticmethod
    def get_extension() -> str:
        return "bdd"

    def __init__(self) -> None:
        self.bdd: BDD = BDD()  # BDD manager
        self.root: Any = None
        self.features_vars: dict[str, str] = {}  # Mapping feature name -> variable name
        self.vars_features: dict[str, str] = {}  # Mapping variable name -> feature name
        self.vars_order: list[str] = []  # Ordered list of variables according to the BDD

    def build_bdd(self, expression: str, variables: list[str]) -> None:
        """Built a BDD from an expression representing a logical formula."""
        ensure_recursion_limit(len(variables))
        self.bdd.configure(reordering=False)  # Disable dynamic reordering for consistency
        for var in variables:
            self.bdd.declare(var)  # Declare variables in the BDD manager
        self.vars_order = variables  # The order is crucial to detect skipped variables
        self.root = self.bdd.add_expr(expression)  # Build the logical formula (root node)

    def build_bdd_incremental(self,
                              clauses: Iterable[str],
                              variables: list[str],
                              reorder: bool = False) -> None:
        """Build a BDD as the conjunction of `clauses`, one clause at a time.

        The variables are declared in the given order (the first one is the top level).
        Conjoining clause by clause keeps the intermediate BDDs small when the clauses are
        scheduled well, instead of parsing one huge expression. With `reorder`, the variables
        are sifted between clauses when the BDD grows (REORDER_MIN_NODES, REORDER_GROWTH);
        the engine's own automatic reordering stays disabled so that levels never change in
        the middle of an operation, and `vars_order` is set to the final level order.
        """
        ensure_recursion_limit(len(variables))
        self.bdd.configure(reordering=False)
        for var in variables:
            self.bdd.declare(var)
        threshold = REORDER_MIN_NODES
        root = self.bdd.true
        for clause in clauses:
            root = root & self.bdd.add_expr(clause)
            if root == self.bdd.false:
                break  # The model is void: further clauses cannot change the result
            if reorder and len(self.bdd) >= threshold:
                _reorder(self.bdd)
                threshold = max(REORDER_MIN_NODES, int(REORDER_GROWTH * len(self.bdd)))
        self.root = root
        # Operations rely on vars_order[i] being the variable at level i.
        self.vars_order = sorted(variables, key=self.bdd.level_of_var)

    def get_expression(self) -> str:
        """ Converts the BDD to a readable Boolean expression string."""
        return self.bdd.to_expr(self.root)

    def get_all_paths(self) -> list[dict[str, bool]]:
        """Transverses the BDD to find all models (paths to True)."""
        return list(self.bdd.pick_iter(self.root))

    def count_solutions(self) -> int:
        """Count the number of valid configurations (SAT)."""
        return self.count_models(self.root, len(self.vars_order))

    def count_models(self, node: Any, nvars: int) -> int:
        """Exact number of assignments of `nvars` variables (a superset of the support of
        `node`) that satisfy `node`.

        dd's pure-Python engine counts with Python integers; the CUDD engine counts with
        floating point, which is approximate beyond 2**53 and overflows beyond ~1e308, so for
        CUDD the count is computed here with integers.
        """
        if DD_BACKEND != "cudd":
            return int(self.bdd.count(node, nvars))
        return exact_count(self.bdd, node, nvars)

    def dump_structure(self) -> None:
        """Prints the structure of the BDD for debugging purposes."""
        if self.root is None:
            logger.debug("Empty BDD.")
            return

        visited = set()
        # In dd.autoref, bdd.true is the unique terminal.
        # bdd.false is just ~bdd.true

        def _dump(node: Any, indent: str = "") -> None:
            if node == self.bdd.true:
                logger.debug("%s leaf: TRUE", indent)
                return
            if node == self.bdd.false:
                logger.debug("%s leaf: FALSE", indent)
                return

            # We use the node object for the visited set
            if node in visited:
                logger.debug("%s (Ref: %s)", indent, node.var)
                return
            visited.add(node)

            logger.debug("%s Node [Var: %s]", indent, node.var)
            # Safe access: only internal nodes have children
            _dump(node.low, indent + "  Low: ")
            _dump(node.high, indent + " High: ")

        logger.debug("Exploring BDD (Root: %s)", self.root)
        _dump(self.root)

    def save_bdd(self,
                 path: str,
                 roots: Optional[Any] = None,
                 filetype: Optional[str] = None) -> None:
        if filetype is None:
            filetype = self.bdd.dump(filename=path, roots=roots)
        else:
            self.bdd.dump(filename=path, roots=roots, filetype=filetype)

    @staticmethod
    def load_bdd(path: str, vars: Optional[list[str]] = None) -> 'BDDModel':
        bdd_model = BDDModel()
        if vars is not None:
            ensure_recursion_limit(len(vars))
            for var in vars:
                bdd_model.bdd.declare(var)
        roots = bdd_model.bdd.load(path)
        if isinstance(roots, dict):
            bdd_model.root = next(iter(roots.values()))
        elif isinstance(roots, list):
            bdd_model.root = roots[0]
        else:
            bdd_model.root = roots
        all_vars = list(bdd_model.bdd.vars)
        ensure_recursion_limit(len(all_vars))
        sorted_vars = sorted(all_vars, key=bdd_model.bdd.level_of_var)
        bdd_model.vars_order = sorted_vars
        bdd_model.vars_features = {var: var for var in bdd_model.vars_order}
        bdd_model.features_vars = {var: var for var in bdd_model.vars_order}
        return bdd_model

    def __str__(self) -> str:
        bdd = self.bdd
        root = self.root
        # Recolect reachable nodes from the root
        # This avoids counting orphan nodes that are in the manager's memory
        reachable_nodes = set()
        to_visit = [root]
        while to_visit:
            u = to_visit.pop()
            if u not in reachable_nodes:
                reachable_nodes.add(u)
                if u.var is not None:
                    to_visit.extend([u.low, u.high])

        result = ""
        result += f"Total nodes in manager: {len(self.bdd)}\n"
        result += f"Nodes in this formula: {len(reachable_nodes)}\n"

        root_var = root.var if root.var is not None else "Terminal"
        result += f"Root node: {root} (Variable: {root_var}, Negated: {root.negated})\n"

        # Group nodes by level
        # In dd, level 0 is the top (root) and goes down
        nodes_by_level: dict[int, list[Any]] = {}
        terminals: list[Any] = []
        for node in reachable_nodes:
            if node.var is not None:
                # Get the level of the variable
                level = bdd.level_of_var(node.var)
                if level not in nodes_by_level:
                    nodes_by_level[level] = []
                nodes_by_level[level].append(node)
            else:
                terminals.append(node)

        # Print levels in order
        for level in sorted(nodes_by_level.keys()):
            var_name = self.vars_order[level]
            num_nodes = len(nodes_by_level[level])
            result += f"Level {level:2} | Variable: {var_name:15} | Nodes: {num_nodes}"
            # Optional: print IDs of nodes at this level
            node_ids = [str(n) for n in nodes_by_level[level]]
            result += f"   IDs: {', '.join(node_ids)}\n"

        # Terminal nodes
        # IIn dd (CUDD), there is only one real terminal node (True)
        # The value False is represented as a negated edge to True
        for t in terminals:
            val = "TRUE" if not t.negated else "FALSE"
            result += f"Terminal Node ID: {t} (Semantic Value: {val})\n"
        #result += f"Expression: {self.get_expression()}\n"
        return result
