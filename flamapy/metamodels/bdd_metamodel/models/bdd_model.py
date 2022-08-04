from typing import Optional

from dd.autoref import BDD, Function

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
        self.bdd = BDD()  # BDD manager
        self.cnf_formula: Optional[str] = None
        self.root = None
        self.variables: list[str] = []

    def from_textual_cnf(self, textual_cnf_formula: str, variables: list[str]) -> None:
        """Build the BDD from a textual representation of the CNF formula,
        and the list of variables."""
        self.cnf_formula = textual_cnf_formula
        self.variables = variables

        # Declare variables
        for var in self.variables:
            self.bdd.declare(var)

        # Build the BDD
        self.root = self.bdd.add_expr(self.cnf_formula)

    def nof_nodes(self) -> int:
        """Return number of nodes in the BDD."""
        return len(self.bdd)

    @staticmethod
    def level(node: Function) -> int:
        """Return the level of the node.

        Non-terminal nodes start at 0.
        Terminal nodes have level `s' being the `s' the number of variables.
        """
        return node.level

    @staticmethod
    def index(node: Function) -> int:
        """Position (index) of the variable that labels the node `n` in the ordering.

        Indexes start at 1.
        Terminal nodes (n0 and n1) have indexes `s + 1`, being `s' the number of variables.
        Note that index(n) = level(n) + 1.

        Example: node `n4` is labeled `B`, and `B` is in the 2nd position in ordering `[A,B,C]`,
        thus level(n4) = 2.
        """
        return node.level + 1

    @staticmethod
    def is_terminal_node(node: Function) -> bool:
        """Check if the node is a terminal node."""
        return node.var is None

    @staticmethod
    def is_terminal_n1(node: Function) -> bool:
        """Check if the node is the terminal node 1 (n1)."""
        return node.var is None and node.node == 1

    @staticmethod
    def is_terminal_n0(node: Function) -> bool:
        """Check if the node is the terminal node 0 (n0)."""
        return node.var is None and node.node == -1

    @staticmethod
    def get_high_node(node: Function) -> Function:
        """Return the high (right, solid) node."""
        return node.high

    @staticmethod
    def get_low_node(node: Function) -> Function:
        """Return the low (left, dashed) node.

        If the arc is complemented it returns the negation of the left node.
        """
        return ~node.low if node.negated and node.low.var is not None else node.low
