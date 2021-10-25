from famapy.core.models import Configuration
from famapy.core.operations import Products

from famapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProducts(Products):
    """It computes all the solutions of a BDD model.

    It also supports the computation of all solutions from a partial configuration.
    """

    def __init__(self, partial_configuration: Configuration = None) -> None:
        self.result = []
        self.bdd_model = None
        self.partial_configuration = partial_configuration

    def execute(self, model: BDDModel) -> 'BDDProducts':
        self.bdd_model = model
        self.result = self.get_products_from_partial_configuration(self.partial_configuration)
        return self

    def get_result(self) -> list[Configuration]:
        return self.result

    def get_products(self) -> list[Configuration]:
        return self.get_products_from_partial_configuration()

    def get_products_from_partial_configuration(self, 
                                                conf: Configuration = None) -> list[Configuration]:
        if conf is None:
            u_func = self.bdd_model.root
            care_vars = self.bdd_model.variables
            elements = {}
        else:
            values = dict(conf.elements.items())
            u_func = self.bdd_model.bdd.let(values, self.bdd_model.root)
            care_vars = set(self.bdd_model.variables) - values.keys()
            elements = conf.elements

        configs = []
        for assignment in self.bdd_model.bdd.pick_iter(u_func, care_vars=care_vars):
            features = {f: True for f in assignment.keys() if assignment[f]}
            features = features | elements
            configs.append(Configuration(features))
        return configs
