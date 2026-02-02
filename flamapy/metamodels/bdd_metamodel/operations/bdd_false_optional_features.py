import logging
from typing import Any, cast


from flamapy.core.models import VariabilityModel
from flamapy.core.operations import FalseOptionalFeatures
from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


LOGGER = logging.getLogger('PySATFalseOptionalFeatures')


class BDDFalseOptionalFeatures(FalseOptionalFeatures):

    def __init__(self) -> None:
        self._result: list[Any] = []

    def get_false_optional_features(self) -> list[Any]:
        return self.get_result()

    def get_result(self) -> list[Any]:
        return self._result

    def execute(self, model: VariabilityModel) -> 'BDDFalseOptionalFeatures':
        bdd_model = cast(BDDModel, model)
        try:
            feature_model = cast(FeatureModel, model.original_model)
        except FlamaException:
            LOGGER.exception("The transformation didn't attach the source model, "
                             "which is required for this operation.")
        self._result = get_false_optional_features(bdd_model, feature_model)
        return self


def get_false_optional_features(bdd_model: BDDModel, feature_model: FeatureModel) -> list[Any]:
    false_optional_features = []
    real_optional_features = [f for f in feature_model.get_features()
                              if not f.is_root() and not f.is_mandatory()]
    for feature in real_optional_features:
        parent_feature = feature.get_parent()
        u_parent = bdd_model.bdd.var(parent_feature.name)
        u_feature = bdd_model.bdd.var(feature.name)

        implication_check = bdd_model.root & u_parent & ~u_feature
        if implication_check == bdd_model.bdd.false:
            false_optional_features.append(bdd_model.vars_features[feature.name])
    return false_optional_features
