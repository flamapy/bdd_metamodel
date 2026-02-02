import re
import itertools

from flamapy.core.models.ast import ASTOperation
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Relation, Constraint


class PLModel():
    """A model representing a Prepositional Logical Formula (PL)."""

    LOGIC_CONNECTIVES = {
        "NOT": "!",
        "OR": "|",
        "AND": "&",
        "IMPLIES": "=>",
        "EQUIVALENCE": "<=>",
        "XOR": "^"}

    def __init__(self, logic_connectives: dict[str, str] = LOGIC_CONNECTIVES) -> None:
        self.formula: str = ""
        self.variables: set[str] = set()
        self.logic_connectives: dict[str, str] = logic_connectives

    def build_from_feature_model(self, fm_model: FeatureModel) -> str:
        """Builds a PL formula from a feature model."""
        self.variables = {feature.name for feature in fm_model.get_features()}
        self.formula = self._traverse_feature_tree(fm_model)
        return self.formula

    def _traverse_feature_tree(self, feature_model: FeatureModel) -> str:
        """Traverse the feature tree from the root and return the propositional formula."""
        if feature_model is None or feature_model.root is None:
            return ""
        # The root is always present
        root_feature = feature_model.root
        formula = [root_feature.name]
        for feature in feature_model.get_features():
            for relation in feature.get_relations():
                formula.append(self._get_relation_formula(relation))
        for constraint in feature_model.get_logical_constraints():
            formula.append(self._get_constraint_formula(constraint))
        propositional_formula = f" {self.logic_connectives['AND']} ".join(f"({f})" for f in formula)
        return propositional_formula

    def _get_relation_formula(self, relation: Relation) -> str:
        result = ""
        if relation.is_mandatory():
            result = self._get_mandatory_formula(relation)
        elif relation.is_optional():
            result = self._get_optional_formula(relation)
        elif relation.is_or():
            result = self._get_or_formula(relation)
        elif relation.is_alternative():
            result = self._get_alternative_formula(relation)
        elif relation.is_mutex():
            result = self._get_mutex_formula(relation)
        elif relation.is_cardinal():
            result = self._get_cardinality_formula(relation)
        return result

    def _get_mandatory_formula(self, relation: Relation) -> str:
        parent = relation.parent.name
        child = relation.children[0].name
        return f"{parent} {self.logic_connectives['EQUIVALENCE']} {child}"

    def _get_optional_formula(self, relation: Relation) -> str:
        parent = relation.parent.name
        child = relation.children[0].name
        return f"{child} {self.logic_connectives['IMPLIES']} {parent}"

    def _get_or_formula(self, relation: Relation) -> str:
        parent = relation.parent.name
        children = f" {self.logic_connectives['OR']} ".join(
            child.name for child in relation.children
        )
        return f"{parent} {self.logic_connectives['EQUIVALENCE']} ({children})"

    def _get_alternative_formula(self, relation: Relation) -> str:
        formula = []
        parent = relation.parent.name
        children = {child.name for child in relation.children}
        equiv_str = self.logic_connectives['EQUIVALENCE']
        and_str = self.logic_connectives['AND']
        not_str = self.logic_connectives['NOT']
        for child in children:
            children_negatives = children - {child}
            neg_children = f" {and_str} ".join(not_str + ch for ch in children_negatives)
            formula.append(f"{child} {equiv_str} ({neg_children} {and_str} {parent})")
        return f" {and_str} ".join(f"({f})" for f in formula)

    def _get_mutex_formula(self, relation: Relation) -> str:
        formula = []
        parent = relation.parent.name
        children = {child.name for child in relation.children}
        equiv_str = self.logic_connectives['EQUIVALENCE']
        and_str = self.logic_connectives['AND']
        not_str = self.logic_connectives['NOT']
        or_str = self.logic_connectives['OR']
        for child in children:
            children_negatives = children - {child}
            neg_children = f" {and_str} ".join(not_str + cn for cn in children_negatives)
            formula.append(f"{child} {equiv_str} ({neg_children} {and_str} {parent})")
        formula_str = f" {and_str} ".join(f"({f})" for f in formula)
        children_or = f" {or_str} ".join(child for child in children)
        left = f"({parent} {equiv_str} {not_str} ({children_or}))"
        return f"{left} {or_str} ({formula_str})"

    def _get_cardinality_formula(self, relation: Relation) -> str:
        parent = relation.parent.name
        children = [child.name for child in relation.children]
        not_str = self.logic_connectives['NOT']
        and_str = self.logic_connectives['AND']
        or_str = self.logic_connectives['OR']

        all_clauses = []

        # 1. If the parent is active, prohibit combinations outside the range [min..max]
        for val in range(len(children) + 1):
            if val < relation.card_min or val > relation.card_max:
                for combination in itertools.combinations(children, val):
                    # To prohibit an exact combination: (NOT parent OR NOT child1 OR child2...)
                    clause_parts = [f"{not_str}{parent}"]
                    for child in children:
                        if child in combination:
                            clause_parts.append(f"{not_str}{child}")
                        else:
                            clause_parts.append(child)
                    all_clauses.append(f"({f' {or_str} '.join(clause_parts)})")

        # 2. If the parent is inactive, NO child can be active (or combinations not allowed)
        # Following the logic of the first script to maintain consistency:
        for val in range(1, len(children) + 1):
            for combination in itertools.combinations(children, val):
                clause_parts = [parent]
                for child in children:
                    if child in combination:
                        clause_parts.append(f"{not_str}{child}")
                    else:
                        clause_parts.append(child)
                all_clauses.append(f"({f' {or_str} '.join(clause_parts)})")

        return f" {and_str} ".join(all_clauses)

    def _get_constraint_formula(self, ctc: Constraint) -> str:
        constraint_str = ctc.ast.pretty_str()
        constraint_str = re.sub(
            rf"\b{ASTOperation.XOR.value}\b", self.logic_connectives['XOR'], constraint_str
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.NOT.value}\b", self.logic_connectives['NOT'], constraint_str
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.AND.value}\b", self.logic_connectives['AND'], constraint_str
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.OR.value}\b", self.logic_connectives['OR'], constraint_str
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.IMPLIES.value}\b",
            self.logic_connectives['IMPLIES'],
            constraint_str,
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.EQUIVALENCE.value}\b",
            self.logic_connectives['EQUIVALENCE'],
            constraint_str,
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.REQUIRES.value}\b",
            self.logic_connectives['IMPLIES'],
            constraint_str,
        )
        constraint_str = re.sub(
            rf"\b{ASTOperation.EXCLUDES.value}\b",
            f"{self.logic_connectives['IMPLIES']} {self.logic_connectives['NOT']}",
            constraint_str,
        )
        return constraint_str
