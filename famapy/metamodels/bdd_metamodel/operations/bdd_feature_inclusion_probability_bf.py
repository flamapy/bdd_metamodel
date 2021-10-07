from famapy.core.models import Configuration 

from famapy.metamodels.bdd_metamodel.models import BDDModel
from famapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability
from famapy.metamodels.bdd_metamodel.operations import BDDProducts


class BDDFeatureInclusionProbabilityBF(FeatureInclusionProbability):
    """The Feature Inclusion Probability (FIP) operation determines the probability 
    for a variable to be included in a valid solution. 
    
    This is a brute-force implementation that enumerates all solutions for calculating the probabilities.
    
    Ref.: [Heradio et al. 2019. Supporting the Statistical Analysis of Variability Models. SPLC. 
    (https://doi.org/10.1109/ICSE.2019.00091)]
    """

    def __init__(self, partial_configuration: Configuration=None) -> None:
        self.result = []
        self.partial_configuration = partial_configuration
        
    
    def execute(self, bdd_model: BDDModel) -> 'BDDFeatureInclusionProbabilityBF':
        self.bdd_model = bdd_model
        self.result = self.feature_inclusion_probability(self.partial_configuration)
        return self

    def get_result(self) -> list[int]:
        return self.result

    def feature_inclusion_probability(self, partial_configuration: Configuration=None) -> dict[str, float]:
        products = BDDProducts(partial_configuration).execute(self.bdd_model).get_result()
        n_products = len(products)
        if n_products == 0:
            return {feature: 0.0 for feature in self.bdd_model.variables}
            
        prob = {}
        for feature in self.bdd_model.variables:
            prob[feature] = sum(feature in p.elements for p in products) / n_products
        return prob
