import re
import locale 
from typing import Any, cast

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations.interfaces import FeatureInclusionProbability


class BDDFeatureInclusionProbability(FeatureInclusionProbability):
    """Computes the probability each model feature has to be included in a valid product.

    That is, for every feature it returns the number of valid products with the feature activated
    divided by the total number of valid products 
    (a product is valid if it satisfies all model constraints).

    For detailed information, see the paper: 
    Heradio, R., Fernandez-Amoros, D., Mayr-Dorn, C., Egyed, A.:
    Supporting the statistical analysis of variability models. 
    In: 41st International Conference on Software Engineering (ICSE), pp. 843-853. 
    Montreal, Canada (2019).

    Return a dictionary with the format 
    {feature_1: feature_1_probability, feature_2: feature_2_probability, ...}
    """

    def __init__(self) -> None:
        self.result: dict[Any, float] = {}

    def get_result(self) -> dict[Any, float]:
        return self.result

    def feature_inclusion_probability(self) -> dict[Any, float]:
        return self.get_result()

    def execute(self, model: VariabilityModel) -> 'BDDFeatureInclusionProbability':
        bdd_model = cast(BDDModel, model)
        self.result = feature_inclusion_probability(bdd_model)
        return self


def feature_inclusion_probability(bdd_model: BDDModel) -> dict[Any, float]:
    # Check bdd_file
    bdd_file = bdd_model.check_file_existence(bdd_model.bdd_file, 'dddmp')
    feature_probabilities_process = bdd_model.run(BDDModel.FEATURE_PROBABILITIES, 
                                                  bdd_file)
    result = feature_probabilities_process.stdout.decode(locale.getdefaultlocale()[1])
    line_iterator = iter(result.splitlines())
    probabilities = {}
    for line in line_iterator:
        parsed_line = re.compile(r'\s+').split(line.strip())
        probabilities[parsed_line[0]] = float(parsed_line[1])
    return probabilities
