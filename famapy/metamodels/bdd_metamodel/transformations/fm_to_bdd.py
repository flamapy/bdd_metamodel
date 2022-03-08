import itertools

from famapy.core.models import VariabilityModel
from famapy.core.transformations import ModelToModel
from famapy.metamodels.fm_metamodel.models.feature_model import (
    Constraint,
    Feature,
    Relation,
)
from famapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class FmToBDD(ModelToModel):
    @staticmethod
    def get_source_extension() -> str:
        return 'fm'

    @staticmethod
    def get_destination_extension() -> str:
        return 'bdd'

    def __init__(self, source_model: VariabilityModel) -> None:
        self.source_model = source_model
        self.counter = 1
        self.destination_model = BDDModel()
        self.variables: dict[str, int] = {}
        self.features: dict[int, str] = {}
        self.clauses: list[list[int]] = []

    def add_feature(self, feature: Feature) -> None:
        if feature.name not in self.variables:
            self.variables[feature.name] = self.counter
            self.features[self.counter] = feature.name
            self.counter += 1

    def add_root(self, feature: Feature) -> None:
        var = self.variables.get(feature.name)
        if var is not None:
            self.clauses.append([var])

    def add_relation(self, relation: Relation) -> None:  # noqa: MC0001
        var_parent = self.variables.get(relation.parent.name)
        # TODO: fix too many nested blocks
        if var_parent is not None:  # pylint: disable=too-many-nested-blocks

            if relation.is_mandatory():
                var_child = self.variables.get(relation.children[0].name)
                if var_child is not None:
                    self.clauses.append([-1 * var_parent, var_child])
                    self.clauses.append([-1 * var_child, var_parent])

            elif relation.is_optional():
                var_child = self.variables.get(relation.children[0].name)
                if var_child is not None:
                    self.clauses.append([-1 * var_child, var_parent])

            elif relation.is_or():  # this is a 1 to n relatinship with multiple childs
                # add the first cnf child1 or child2 or ... or childN or no parent)

                # first elem of the constraint
                alt_cnf = [-1 * var_parent]
                for child in relation.children:
                    var_child = self.variables.get(child.name)
                    if var_child is not None:
                        alt_cnf.append(var_child)
                self.clauses.append(alt_cnf)

                for child in relation.children:
                    var_child = self.variables.get(child.name)
                    if var_child is not None:
                        self.clauses.append([-1 * var_child, var_parent])

            elif relation.is_alternative():
                # this is a 1 to 1 relatinship with multiple childs
                # add the first cnf child1 or child2 or ... or childN or no parent)

                # first elem of the constraint
                alt_cnf = [-1 * var_parent]
                for child in relation.children:
                    var_child = self.variables.get(child.name)
                    if var_child is not None:
                        alt_cnf.append(var_child)
                self.clauses.append(alt_cnf)

                for i, _ in enumerate(relation.children):
                    var_child_i = self.variables.get(relation.children[i].name)
                    if var_child_i is not None:
                        for j in range(i + 1, len(relation.children)):
                            if i != j:
                                var_child_j = self.variables.get(relation.children[j].name)
                                if var_child_j is not None:
                                    self.clauses.append([-1 * var_child_i, -1 * var_child_j])
                        self.clauses.append([-1 * var_child_i, var_parent])

            else:
                # This is a _min to _max relationship
                _min = relation.card_min
                _max = relation.card_max

                for val in range(len(relation.children) + 1):
                    if val < _min or val > _max:
                        # These sets are the combinations that shouldn't be in the res
                        # Let ¬A, B, C be one of your 0-paths.
                        # The relative clause will be (A ∨ ¬B ∨ ¬C).
                        # This first for loop is to combine when the parent is and
                        # the childs led to a 0-pathself.
                        for res in itertools.combinations(relation.children, val):
                            cnf = [-1 * var_parent]
                            for feat in relation.children:
                                var_feat = self.variables.get(feat.name)
                                if var_feat is not None:
                                    if feat in res:
                                        cnf.append(-1 * var_feat)
                                    else:
                                        cnf.append(var_feat)
                            self.clauses.append(cnf)
                    else:
                        # This first for loop is to combine when the parent is not
                        # and the childs led to a 1-pathself which is actually
                        # 0-path considering the parent.
                        for res in itertools.combinations(relation.children, val):
                            cnf = [var_parent]
                            for feat in relation.children:
                                var_feat = self.variables.get(feat.name)
                                if var_feat is not None:
                                    if feat in res:
                                        cnf.append(-1 * var_feat)
                                    else:
                                        cnf.append(var_feat)
                            self.clauses.append(cnf)

    def add_constraint(self, ctc: Constraint) -> None:
        clauses = ctc.ast.get_clauses()
        for clause in clauses:
            cls = []
            for term in clause:
                var_term = None
                if term.startswith('-'):
                    var_term = self.variables.get(term[1:])
                    if var_term is not None:
                        var_term = -1 * var_term
                else:
                    var_term = self.variables.get(term)
                if var_term is not None:
                    cls.append(var_term)
            self.clauses.append(cls)

    def transform(self) -> VariabilityModel:
        for feature in self.source_model.get_features():
            self.add_feature(feature)

        self.add_root(self.source_model.root)

        for relation in self.source_model.get_relations():
            self.add_relation(relation)

        for constraint in self.source_model.get_constraints():
            self.add_constraint(constraint)

        # Transform clauses to textual CNF notation required by the BDD
        not_connective = BDDModel.NOT
        or_connective = ' ' + BDDModel.OR + ' '
        and_connective = ' ' + BDDModel.AND + ' '
        cnf_list = []
        for clause in self.clauses:
            cnf_list.append('(' + or_connective.join(list(map(lambda l: 
                            not_connective + self.features[abs(l)] if l < 0 else 
                            self.features[abs(l)], clause))) + ')')

        cnf_formula = and_connective.join(cnf_list)
        self.destination_model.from_textual_cnf(cnf_formula, list(self.variables.keys()))

        return self.destination_model
