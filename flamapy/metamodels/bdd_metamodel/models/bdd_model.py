from typing import Optional, Any

try:
    import dd.cudd as _bdd
except ImportError:
    import dd.autoref as _bdd

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models.utils.txtcnf import (
    CNFLogicConnective,
    TextCNFNotation,
)


class BDDModel(VariabilityModel):
    """A Binary Decision Diagram (BDD) representation of the feature model.

    It relies on the dd library: https://pypi.org/project/dd/
    """

    CNF_NOTATION = TextCNFNotation.JAVA_SHORT
    NOT = CNF_NOTATION.value[CNFLogicConnective.NOT]
    AND = CNF_NOTATION.value[CNFLogicConnective.AND]
    OR = CNF_NOTATION.value[CNFLogicConnective.OR]

    @staticmethod
    def get_extension() -> str:
        return 'bdd'

    def __init__(self) -> None:
        self.bdd = _bdd.BDD()  # BDD manager
        self.root: Optional[_bdd.Function] = None
        self.variables: dict[str, int] = {}

    @classmethod
    def from_cnf_formula(cls, cnf_formula: str, variables: list[str]) -> 'BDDModel':
        """Build the BDD from a textual representation of the CNF formula,
        and the list of variables."""
        bdd_model = cls()
        # Declare variables
        for var in variables:
            bdd_model.bdd.declare(var)
        # Build the BDD
        bdd_model.root = bdd_model.bdd.add_expr(cnf_formula)
        # Store variables
        bdd_model.variables = bdd_model.bdd.vars
        return bdd_model

    @classmethod
    def from_propositional_formula(cls, formula: str, variables: list[str]) -> 'BDDModel':
        """Build the BDD from a textual representation of the CNF formula,
        and the list of variables."""
        bdd_model = cls()
        # Declare variables
        for var in variables:
            bdd_model.bdd.declare(var)
        # Build the BDD
        bdd_model.root = bdd_model.bdd.add_expr(formula)
        # Store variables
        bdd_model.variables = bdd_model.bdd.vars
        return bdd_model

    def nof_nodes(self) -> int:
        """Return number of nodes in the BDD."""
        return len(self.bdd)

    def get_node(self, var: Any) -> _bdd.Function:
        """Return the node of the named var 'var'."""
        return self.bdd.var(var) 

    def level(self, node: _bdd.Function) -> int:
        """Return the level of the node.

        Non-terminal nodes start at 0.
        Terminal nodes have level `s' being the `s' the number of variables.
        """
        return node.level if not self.is_terminal_node(node) else len(self.bdd.vars)

    def index(self, node: _bdd.Function) -> int:
        """Position (index) of the variable that labels the node `n` in the ordering.

        Indexes start at 1.
        Terminal nodes (n0 and n1) have indexes `s + 1`, being `s' the number of variables.
        Note that index(n) = level(n) + 1.

        Example: node `n4` is labeled `B`, and `B` is in the 2nd position in ordering `[A,B,C]`,
        thus level(n4) = 2.
        """
        return self.level(node) + 1

    def is_terminal_node(self, node: Any) -> bool:
        """Check if the node is a terminal node."""
        #return node.var is None
        return self.is_terminal_n0(node) or self.is_terminal_n1(node)

    def is_terminal_n1(self, node: Any) -> bool:
        """Check if the node is the terminal node 1 (n1)."""
        return node == self.bdd.true

    def is_terminal_n0(self, node: Any) -> bool:
        """Check if the node is the terminal node 0 (n0)."""
        return node == self.bdd.false

    def get_high_node(self, node: _bdd.Function) -> Optional[_bdd.Function]:
        """Return the high (right, solid) node."""
        return node.high

    def get_low_node(self, node: _bdd.Function) -> Optional[_bdd.Function]:
        """Return the low (left, dashed) node.

        If the arc is complemented it returns the negation of the left node.
        """
        return node.low

    def get_value(self, node: _bdd.Function, complemented: bool = False) -> int:
        """Return the value (id) of the node considering complemented arcs."""
        value = int(node)
        if self.is_terminal_n0(node):
            value = 1 if complemented else 0
        elif self.is_terminal_n1(node):
            value = 0 if complemented else 1
        return value

    def __str__(self) -> str:
        result = f'Root: {self.root.var} ' \
                 f'(id: {int(self.root)}) ' \
                 f'(level: {self.level(self.root)}) ' \
                 f'(index: {self.index(self.root)})\n'
        result += f'Vars: ({len(self.bdd.vars)})\n'
        var_levels = dict(sorted(self.bdd.var_levels.items(), key=lambda item: item[1]))
        for var in var_levels:
            node = self.get_node(var)
            result += f' |-{node.var} ' \
                      f'(id: {int(node)}) ' \
                      f'(level: {self.level(node)}) ' \
                      f'(index: {self.index(node)})\n'
        node = self.bdd.false
        result += f'Terminal node (n0): {node.var} ' \
                  f'(id: {int(node)}) ' \
                  f'(level: {self.level(node)}) ' \
                  f'(index: {self.index(node)})\n'
        node = self.bdd.true
        result += f'Terminal node (n1): {node.var} ' \
                  f'(id: {int(node)}) ' \
                  f'(level: {self.level(node)}) ' \
                  f'(index: {self.index(node)})\n'
        return result
