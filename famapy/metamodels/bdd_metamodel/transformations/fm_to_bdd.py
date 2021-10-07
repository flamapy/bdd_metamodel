import itertools
from typing import Any

from famapy.core.exceptions import ElementNotFound
from famapy.core.models import VariabilityModel
from famapy.core.transformations import ModelToModel
from famapy.metamodels.fm_metamodel.models.feature_model import (  # pylint: disable=import-error
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
        self.variables: dict[str, Any] = {}
        self.features: dict[str, Any] = {}
        self.clauses = []

    def add_feature(self, feature: Feature) -> None:
        if feature.name not in self.variables.keys():
            self.variables[feature.name] = self.counter
            self.features[self.counter] = feature.name
            self.counter += 1

    def add_root(self, feature: Feature) -> None:
        self.clauses.append([self.variables.get(feature.name)])

    def add_relation(self, relation: Relation) -> None:  # noqa: MC0001
        if relation.is_mandatory():
            self.clauses.append([
                -1 * self.variables.get(relation.parent.name),
                self.variables.get(relation.children[0].name)
            ])
            self.clauses.append([
                -1 * self.variables.get(relation.children[0].name),
                self.variables.get(relation.parent.name)
            ])

        elif relation.is_optional():
            self.clauses.append([
                -1 * self.variables.get(relation.children[0].name),
                self.variables.get(relation.parent.name)
            ])

        elif relation.is_or():  # this is a 1 to n relatinship with multiple childs
            # add the first cnf child1 or child2 or ... or childN or no parent)

            # first elem of the constraint
            alt_cnf = [-1 * self.variables.get(relation.parent.name)]
            for child in relation.children:
                alt_cnf.append(self.variables.get(child.name))
            self.clauses.append(alt_cnf)

            for child in relation.children:
                self.clauses.append([
                    -1 * self.variables.get(child.name),
                    self.variables.get(relation.parent.name)
                ])

        # TODO: fix too many nested blocks
        elif relation.is_alternative():  # pylint: disable=too-many-nested-blocks
            # this is a 1 to 1 relatinship with multiple childs
            # add the first cnf child1 or child2 or ... or childN or no parent)

            # first elem of the constraint
            alt_cnf = [-1 * self.variables.get(relation.parent.name)]
            for child in relation.children:
                alt_cnf.append(self.variables.get(child.name))
            self.clauses.append(alt_cnf)

            for i in range(len(relation.children)):
                for j in range(i + 1, len(relation.children)):
                    if i != j:
                        self.clauses.append([
                            -1 * self.variables.get(relation.children[i].name),
                            -1 * self.variables.get(relation.children[j].name)
                        ])
                self.clauses.append([
                    -1 * self.variables.get(relation.children[i].name),
                    self.variables.get(relation.parent.name)
                ])

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
                        cnf = [-1 * self.variables.get(relation.parent.name)]
                        for feat in relation.children:
                            if feat in res:
                                cnf.append(-1 * self.variables.get(feat.name))
                            else:
                                cnf.append(self.variables.get(feat.name))
                        self.clauses.append(cnf)
                else:
                    # This first for loop is to combine when the parent is not
                    # and the childs led to a 1-pathself which is actually
                    # 0-path considering the parent.
                    for res in itertools.combinations(relation.children, val):
                        cnf = [self.variables.get(relation.parent.name)]
                        for feat in relation.children:
                            if feat in res:
                                cnf.append(-1 * self.variables.get(feat.name))
                            else:
                                cnf.append(self.variables.get(feat.name))
                        self.clauses.append(cnf)

    def add_constraint(self, ctc: Constraint) -> None:
        #We are only supporting requires or excludes
        if ctc.ast.root.data.upper() == 'REQUIRES' or ctc.ast.root.data.upper() == 'IMPLIES':
            dest = self.variables.get(
                ctc.ast.root.right.data
            )
            orig = self.variables.get(
                ctc.ast.root.left.data
            )
            if dest is None or orig is None:
                print(self.source_model)
                raise ElementNotFound
            self.clauses.append([-1 * orig, dest])
        elif ctc.ast.root.data.upper() == 'EQUIVALENCE':
            dest = self.variables.get(
                ctc.ast.root.right.data
            )
            orig = self.variables.get(
                ctc.ast.root.left.data
            )
            if dest is None or orig is None:
                print(self.source_model)
                raise ElementNotFound
            self.clauses.append([-1 * orig, dest])
            self.clauses.append([-1 * dest, orig])
        elif ctc.ast.root.data.upper() == 'EXCLUDES':
            dest = self.variables.get(
                ctc.ast.root.right.data
            )
            orig = self.variables.get(
                ctc.ast.root.left.data
            )
            if dest is None or orig is None:
                print(self.source_model)
                raise ElementNotFound
            self.clauses.append([-1 * orig, -1 * dest])

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
