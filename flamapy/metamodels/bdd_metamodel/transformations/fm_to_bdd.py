import itertools

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import (
    FeatureModel,
    Constraint,
    Feature,
    Relation,
)
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class FmToBDD(ModelToModel):
    @staticmethod
    def get_source_extension() -> str:
        return 'fm'

    @staticmethod
    def get_destination_extension() -> str:
        return 'bdd'

    def __init__(self, source_model: FeatureModel) -> None:
        self.source_model = source_model
        self.counter = 1
        self.destination_model = BDDModel()
        self.variables: dict[str, int] = {}
        self.features: dict[int, str] = {}
        self.clauses: list[list[int]] = []

    def _get_variable(self, name: str) -> int:
        variable = self.variables.get(name)
        if variable is None:
            raise ValueError("the parent variable wasn't found")
        return variable

    def add_feature(self, feature: Feature) -> None:
        if feature.name not in self.variables:
            self.variables[feature.name] = self.counter
            self.features[self.counter] = feature.name
            self.counter += 1

    def add_root(self, feature: Feature) -> None:
        self.clauses.append([self._get_variable(feature.name)])

    def add_relation(self, relation: Relation) -> None:  # noqa: MC0001
        # pylint: disable=too-many-nested-blocks
        var_parent = self._get_variable(relation.parent.name)
        # TODO: fix too many nested blocks
        if relation.is_mandatory():
            var_child = self._get_variable(relation.children[0].name)
            self.clauses.append([-1 * var_parent, var_child])
            self.clauses.append([-1 * var_child, var_parent])

        elif relation.is_optional():
            self.clauses.append([
                -1 * self._get_variable(relation.children[0].name), var_parent
            ])

        elif relation.is_or():  # this is a 1 to n relatinship with multiple childs
            # add the first cnf child1 or child2 or ... or childN or no parent)

            # first elem of the constraint
            alt_cnf = [-1 * var_parent]
            for child in relation.children:
                alt_cnf.append(self._get_variable(child.name))
            self.clauses.append(alt_cnf)

            for child in relation.children:
                self.clauses.append([-1 * self._get_variable(child.name), var_parent])

        elif relation.is_alternative():
            # this is a 1 to 1 relatinship with multiple childs
            # add the first cnf child1 or child2 or ... or childN or no parent)

            # first elem of the constraint
            alt_cnf = [-1 * var_parent]
            for child in relation.children:
                alt_cnf.append(self._get_variable(child.name))
            self.clauses.append(alt_cnf)

            for i, _ in enumerate(relation.children):
                var_child_i = self._get_variable(relation.children[i].name)
                for j in range(i + 1, len(relation.children)):
                    if i != j:
                        self.clauses.append([
                            -1 * var_child_i, -1 * self._get_variable(relation.children[j].name)
                        ])
                self.clauses.append([-1 * var_child_i, var_parent])

        else:
            # This is a _min to _max relationship
            _min = relation.card_min
            _max = relation.card_max
            for val in range(len(relation.children) + 1):
                if val < _min or val > _max:
                    #combinations of val elements
                    for combination in itertools.combinations(relation.children, val):
                        cnf = [-1 * self._get_variable(relation.parent.name)]
                        for feat in relation.children:
                            if feat in combination:
                                cnf.append(-1 * self._get_variable(feat.name))
                            else:
                                cnf.append(self._get_variable(feat.name))
                        self.clauses.append(cnf)

            #there is a special case when coping with the upper part of the thru table
            #In the case of allowing 0 childs, you cannot exclude the option  in that
            # no feature in this relation is activated
            for val in range(1, len(relation.children) + 1):
                for combination in itertools.combinations(relation.children, val):
                    cnf = [self._get_variable(relation.parent.name)]
                    for feat in relation.children:
                        if feat in combination:
                            cnf.append(-1 * self._get_variable(feat.name))
                        else:
                            cnf.append(self._get_variable(feat.name))
                    self.clauses.append(cnf)

    def add_constraint(self, ctc: Constraint) -> None:
        clauses = ctc.ast.get_clauses()
        for clause in clauses:
            cls = []
            for term in clause:
                if term.startswith('-'):
                    var_term = -1 * self._get_variable(term[1:])
                else:
                    var_term = self._get_variable(term)
                cls.append(var_term)
            self.clauses.append(cls)

    def transform(self) -> BDDModel:
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
