from famapy.core.models import Configuration
from famapy.core.operations import Products

from famapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProducts(Products):
    """It computes all the solutions of a BDD model.
    
    It also supports the computation of all solutions from a partial configuration.
    """
    
    def __init__(self, partial_configuration: Configuration=None) -> None:
        self.result = []
        self.partial_configuration = partial_configuration
    
    def execute(self, bdd_model: BDDModel) -> 'BDDProducts':
        self.bdd_model = bdd_model
        self.result = self.get_products(self.partial_configuration)
        return self

    def get_result(self) -> list[Configuration]:
        return self.result

    def get_products(self, partial_configuration: Configuration=None) -> list[Configuration]:
        if partial_configuration is None:
            u = self.bdd_model.root
            care_vars = self.bdd_model.variables
            elements = {}
        else:
            values = {f: selected for f, selected in partial_configuration.elements.items()}
            u = self.bdd_model.bdd.let(values, self.bdd_model.root)
            care_vars = set(self.bdd_model.variables) - values.keys()
            elements = partial_configuration.elements
        
        configs = []
        for c in self.bdd_model.bdd.pick_iter(u, care_vars=care_vars):
            features = {f: True for f in c.keys() if c[f]}
            features = features | elements
            configs.append(Configuration(features))
        return configs
