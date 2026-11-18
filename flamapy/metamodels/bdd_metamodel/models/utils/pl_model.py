import itertools
from dataclasses import dataclass

from flamapy.core.models.ast import ASTOperation
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Relation, Constraint


@dataclass(frozen=True)
class PLClause:
    """One conjunct of the propositional formula of a feature model.

    `kind` says where the clause comes from ('root', 'mandatory', 'optional', 'or',
    'alternative', 'mutex', 'cardinality' or 'constraint'), `formula` is the clause in the
    model's logic connectives, and `support` lists the variables the clause mentions, in
    feature-tree order.
    """
    kind: str
    formula: str
    support: tuple[str, ...]


class PLModel():
    """A model representing a Prepositional Logical Formula (PL).

    Besides the whole formula (the conjunction of all clauses), the model keeps the clauses
    one by one (`clauses`) and the variables in feature-tree pre-order (`variables`), so a
    BDD can be built clause by clause with a deterministic variable order.
    """

    LOGIC_CONNECTIVES = {
        "NOT": "!",
        "OR": "|",
        "AND": "&",
        "IMPLIES": "=>",
        "EQUIVALENCE": "<=>",
        "XOR": "^"}

    def __init__(self, logic_connectives: dict[str, str] = LOGIC_CONNECTIVES) -> None:
        self.formula: str = ""
        self.variables: list[str] = []
        self.clauses: list[PLClause] = []
        self.logic_connectives: dict[str, str] = logic_connectives

    def build_from_feature_model(self, fm_model: FeatureModel) -> str:
        """Builds a PL formula from a feature model."""
        self.variables = self._tree_preorder(fm_model)
        self.clauses = self._get_clauses(fm_model)
        self.formula = f" {self.logic_connectives['AND']} ".join(
            f"({clause.formula})" for clause in self.clauses)
        return self.formula

    @staticmethod
    def _tree_preorder(feature_model: FeatureModel) -> list[str]:
        """Feature names in depth-first pre-order of the feature tree.

        A feature is followed by its whole subtree, so the variables of each group sit next
        to their parent, which is usually a good static order for a BDD.
        """
        if feature_model is None or feature_model.root is None:
            return []
        order: list[str] = []
        seen: set[str] = set()
        stack = [feature_model.root]
        while stack:
            feature = stack.pop()
            if feature.name in seen:
                continue
            seen.add(feature.name)
            order.append(feature.name)
            children = [child for relation in feature.get_relations()
                        for child in relation.children]
            stack.extend(reversed(children))
        return order

    def _get_clauses(self, feature_model: FeatureModel) -> list[PLClause]:
        """Traverse the feature tree from the root and return the clauses of the formula."""
        if feature_model is None or feature_model.root is None:
            return []
        position = {name: index for index, name in enumerate(self.variables)}

        def support(names: list[str]) -> tuple[str, ...]:
            return tuple(sorted(set(names), key=lambda name: position.get(name, len(position))))

        # The root is always present
        root_name = feature_model.root.name
        clauses = [PLClause("root", root_name, (root_name,))]
        for feature in feature_model.get_features():
            for relation in feature.get_relations():
                formula = self._get_relation_formula(relation)
                if formula:
                    names = [relation.parent.name] + [child.name for child in relation.children]
                    clauses.append(PLClause(self._get_relation_kind(relation), formula,
                                            support(names)))
        for constraint in feature_model.get_logical_constraints():
            clauses.append(PLClause("constraint", self._get_constraint_formula(constraint),
                                    support(constraint.get_features())))
        return clauses

    @staticmethod
    def _get_relation_kind(relation: Relation) -> str:
        kinds = (("mandatory", relation.is_mandatory), ("optional", relation.is_optional),
                 ("or", relation.is_or), ("alternative", relation.is_alternative),
                 ("mutex", relation.is_mutex), ("cardinality", relation.is_cardinal))
        return next((kind for kind, check in kinds if check()), "cardinality")

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
        else:
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
        children = list(dict.fromkeys(child.name for child in relation.children))
        equiv_str = self.logic_connectives['EQUIVALENCE']
        and_str = self.logic_connectives['AND']
        not_str = self.logic_connectives['NOT']
        for child in children:
            children_negatives = [ch for ch in children if ch != child]
            neg_children = f" {and_str} ".join(not_str + ch for ch in children_negatives)
            formula.append(f"{child} {equiv_str} ({neg_children} {and_str} {parent})")
        return f" {and_str} ".join(f"({f})" for f in formula)

    def _get_mutex_formula(self, relation: Relation) -> str:
        equiv_str = self.logic_connectives['EQUIVALENCE']
        and_str = self.logic_connectives['AND']
        not_str = self.logic_connectives['NOT']
        or_str = self.logic_connectives['OR']
        parent = relation.parent.name
        children = list(dict.fromkeys(child.name for child in relation.children))

        one_child_formula = []
        for child in children:
            other_children_or = f" {or_str} ".join(c for c in children if c != child)
            one_child_formula.append(f"({not_str} {child} {equiv_str} ({other_children_or}))")
        one_child_str = f" {and_str} ".join(f for f in one_child_formula)
        no_child_str = f" {and_str} ".join(f"{not_str} {c}" for c in children)
        return f"({no_child_str}) {or_str} (({one_child_str}) {and_str} {parent})"

    def _get_cardinality_formula(self, relation: Relation) -> str:
        parent = relation.parent.name
        children = [child.name for child in relation.children]
        not_str = self.logic_connectives['NOT']
        and_str = self.logic_connectives['AND']
        or_str = self.logic_connectives['OR']

        card_min = relation.card_min
        card_max = relation.card_max if relation.card_max != -1 else len(children)
        all_clauses = []

        # 1. If the parent is active, prohibit combinations outside the range [min..max]
        for val in range(len(children) + 1):
            if val < card_min or val > card_max:
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
        """Write a logical constraint with this model's connectives.

        `AST.pretty_str` replaces the operators node by node, so a feature called, e.g., `OR`
        is never taken for an operator.
        """
        conn = self.logic_connectives
        operators = {
            ASTOperation.NOT: conn['NOT'],
            ASTOperation.AND: conn['AND'],
            ASTOperation.OR: conn['OR'],
            ASTOperation.XOR: conn['XOR'],
            ASTOperation.IMPLIES: conn['IMPLIES'],
            ASTOperation.REQUIRES: conn['IMPLIES'],
            ASTOperation.EQUIVALENCE: conn['EQUIVALENCE'],
            ASTOperation.EXCLUDES: f"{conn['IMPLIES']} {conn['NOT']}",
        }
        return ctc.ast.pretty_str(operators)
