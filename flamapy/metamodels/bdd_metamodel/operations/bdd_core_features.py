from flamapy.core.operations import CoreFeatures

from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import BDDFeatureInclusionProbability


class BDDCoreFeatures(CoreFeatures):

    def __init__(self) -> None:
        self.result = []
        self.bdd_model = None

    def execute(self, model: BDDModel) -> 'BDDCoreFeatures':
        self.bdd_model = model
        self.result = core_features(self.bdd_model)
        return self

    def get_result(self) -> list[str]:
        return self.result

    def get_core_features(self) -> list[str]:
        return core_features(self.bdd_model)


def core_features(bdd_model: BDDModel) -> list[str]:
    feat_incl_prob = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    return [f for f, p in feat_incl_prob.items() if p >= 1.0]