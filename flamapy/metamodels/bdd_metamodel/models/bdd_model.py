import logging
from enum import Enum
from typing import Any, Optional

try:
    from dd.cudd import BDD
except ImportError:
    from dd.autoref import BDD

from flamapy.core.models import VariabilityModel

logger = logging.getLogger(__name__)


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
        self.bdd.configure(reordering=False)  # Disable dynamic reordering for consistency
        for var in variables:
            self.bdd.declare(var)  # Declare variables in the BDD manager
        self.vars_order = variables  # The order is crucial to detect skipped variables
        self.root = self.bdd.add_expr(expression)  # Build the logical formula (root node)

    def get_expression(self) -> str:
        """ Converts the BDD to a readable Boolean expression string."""
        return self.bdd.to_expr(self.root)

    def get_all_paths(self) -> list[dict[str, bool]]:
        """Transverses the BDD to find all models (paths to True)."""
        return list(self.bdd.pick_iter(self.root))

    def count_solutions(self) -> int:
        """Count the number of valid configurations (SAT)."""
        return self.bdd.count(self.root, len(self.vars))  # count(node, n_vars)

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
