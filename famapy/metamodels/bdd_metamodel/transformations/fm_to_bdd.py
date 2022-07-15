import itertools

from famapy.core.transformations import ModelToModel
from famapy.metamodels.fm_metamodel.models import (
    FeatureModel,
    Constraint,
    Feature,
    Relation,
)
from famapy.metamodels.bdd_metamodel.models import BDDModel


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
                # This is a _min to _max relationship
                _min = relation.card_min
                _max = relation.card_max
                for val in range(len(relation.children) + 1):
                    if val < _min or val > _max:
                        #combinations of val elements
                        for combination in itertools.combinations(relation.children, val):
                            cnf = [-1 *
                                self.variables.get(relation.parent.name)]
                            for feat in relation.children:
                                if feat in combination:
                                    cnf.append( -1 *
                                            self.variables.get(feat.name))
                                else:
                                    cnf.append(
                                        self.variables.get(feat.name))  
                            self.clauses.append(cnf)   
                            
                #there is a special case when coping with the upper part of the thru table
                #In the case of allowing 0 childs, you cannot exclude the option  in that 
                # no feature in this relation is activated
                for val in range(1,len(relation.children)+1):
                    
                    for combination in itertools.combinations(relation.children, val):
                        cnf = [self.variables.get(
                                relation.parent.name)]
                        for feat in relation.children:
                            if feat in combination:
                                cnf.append(-1*
                                        self.variables.get(feat.name))
                            else:
                                cnf.append(
                                    self.variables.get(feat.name))
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
