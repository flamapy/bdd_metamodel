import logging
from typing import Any, cast


from flamapy.core.models import VariabilityModel
from flamapy.core.operations import FalseOptionalFeatures
from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.bdd_traversals import refuted_implications


LOGGER = logging.getLogger('BDDFalseOptionalFeatures')


class BDDFalseOptionalFeatures(FalseOptionalFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []

    def get_false_optional_features(self) -> list[Any]:
        return self.get_result()

    def get_result(self) -> list[Any]:
        return self._result

    def execute(self, model: VariabilityModel) -> 'BDDFalseOptionalFeatures':
        bdd_model = cast(BDDModel, model)
        original_model = getattr(model, 'original_model', None)
        if original_model is None:
            raise FlamaException("The transformation didn't attach the source model, "
                                 "which is required for this operation.")
        feature_model = cast(FeatureModel, original_model)
        self._result = get_false_optional_features(bdd_model, feature_model)
        return self


def get_false_optional_features(bdd_model: BDDModel, feature_model: FeatureModel) -> list[Any]:
    """The optional features their parent implies: every (parent, feature) implication is
    checked in one traversal of the BDD (`refuted_implications`), without building any BDD.
    A feature whose parent is dead is implied vacuously, as in the SAT and Z3 plugins.
    """
    real_optional_features = [f for f in feature_model.get_features()
                              if not f.is_root() and not f.is_mandatory()]
    pairs = [(feature.get_parent().name, feature.name) for feature in real_optional_features]
    refuted = refuted_implications(bdd_model, pairs)
    return [bdd_model.vars_features[feature.name]
            for feature, is_refuted in zip(real_optional_features, refuted) if not is_refuted]
