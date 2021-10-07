from dd.autoref import BDD, Function

from famapy.core.models import VariabilityModel

from famapy.metamodels.bdd_metamodel.models.utils.txtcnf import TextCNFNotation, CNFLogicConnective


class BDDModel(VariabilityModel):
    """A Binary Decision Diagram (BDD) representation of the feature model given as a CNF formula.

    It relies on the dd module: https://pypi.org/project/dd/
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
        
    def index(self, n: Function) -> int:
        """Position of the variable that labels the node `n` in the ordering (i.e., the level).
            
        Example: node `n4` is labeled `B`, and `B` is in the second position of the ordering `[A,B,C]`.
        thus var(n4) = 2.
        """
        if n.node == -1 or n.node == 1:  # index(n0) = index(n1) = s + 1, being s the number of variables.
            return len(self.bdd.vars) + 1
        else:
            return n.level + 1
    
    def is_terminal_node(self, node: Function) -> bool:
        return node.var is None    

    def get_high_node(self, node: Function) -> Function:
        # TODO: check!!!
        return node.high

    def get_low_node(self, node: Function) -> Function:
        # TODO: check!!!
        return ~node.low if node.negated and not self.is_terminal_node(node.low) else node.low
        