from dd.autoref import BDD, Function

from famapy.core.models import VariabilityModel

from famapy.metamodels.bdd_metamodel.models.utils.txtcnf import TextCNFNotation, CNFLogicConnective


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

    def __init__(self):
        self.bdd = BDD()  # BDD manager
        self.textual_cnf_formula = None
        self.root = None
        self.variables = []

    def from_textual_cnf(self, textual_cnf_formula: str, variables: list[str]):
        """Build the BDD from a textual representation of the CNF formula,
        and the list of variables."""
        self.cnf_formula = textual_cnf_formula
        self.variables = variables

        # Declare variables
        for v in self.variables:
            self.bdd.declare(v)

        # Build the BDD
        self.root = self.bdd.add_expr(self.cnf_formula)
        
        # Reorder variables
        # variable_order = self.bdd.vars 
        # var = self.bdd.var_at_level(0)
        # level = self.root.level
        # variable_order[self.root.var] = 0
        # variable_order[var] = level
        # self.bdd.reorder(variable_order)
        # self.root = self.bdd.var(self.bdd.var_at_level(0))
    
    def nof_nodes(self) -> int:
        """Return number of nodes in the BDD."""
        return len(self.bdd)

    def level(self, n: Function) -> int:
        """Return the level of the node. 
        
        Non-terminal nodes start at 0. 
        Terminal nodes have level `s' being the `s' the number of variables.
        """
        return n.level

    def index(self, n: Function) -> int:
        """Position (index) of the variable that labels the node `n` in the ordering.

        Indexes start at 1. 
        Terminal nodes (n0 and n1) have indexes `s + 1`, being `s' the number of variables.
        Note that index(n) = level(n) + 1.

        Example: node `n4` is labeled `B`, and `B` is in the 2nd position in ordering `[A,B,C]`,
        thus level(n4) = 2.
        """
        if n.node == -1 or n.node == 1:  # index(n0) = index(n1) = s + 1, s = number of variables
            return len(self.bdd.vars) + 1
        else:
            return n.level + 1
    
    def is_terminal_node(self, node: Function) -> bool:
        """Check if the node is a terminal node."""
        return node.var is None    

    def is_terminal_n1(self, node: Function) -> bool:
        """Check if the node is the terminal node 1 (n1)."""
        return self.is_terminal_node(node) and node.node == 1

    def is_terminal_n0(self, node: Function) -> bool:
        """Check if the node is the terminal node 0 (n0)."""
        return self.is_terminal_node(node) and node.node == -1

    def get_high_node(self, node: Function) -> Function:
        """Return the high (right, solid) node."""
        return node.high

    def get_low_node(self, node: Function) -> Function:
        """Return the low (left, dashed) node.
        
        If the arc is complemented it returns the negation of the left node.
        """
        return ~node.low if node.negated and not self.is_terminal_node(node.low) else node.low
        