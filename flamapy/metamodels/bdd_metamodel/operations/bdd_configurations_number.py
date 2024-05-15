import re
import locale
from typing import Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import ConfigurationsNumber
from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDConfigurationsNumber(ConfigurationsNumber):
    """It computes the number of solutions of the BDD model.

    It also supports counting the solutions from a given partial configuration.
    """

    def __init__(self) -> None:
        self.result: int = 0
        self.partial_configuration: Optional[Configuration] = None

    def set_partial_configuration(self, partial_configuration: Configuration) -> None:
        self.partial_configuration = partial_configuration

    def execute(self, model: VariabilityModel) -> 'BDDConfigurationsNumber':
        bdd_model = cast(BDDModel, model)
        self.result = configurations_number(bdd_model, self.partial_configuration)
        return self

    def get_result(self) -> int:
        return self.result

    def get_configurations_number(self) -> int:
        return self.get_result()


def configurations_number(bdd_model: BDDModel, 
                          partial_configuration: Optional[Configuration] = None) -> int:
    """
    Computes the number of valid configurations.
        :param feature_assignment: a list with a partial or a complete features' assignment
               (e.g., ["f1", "not f3", "f5"])
        :return: The number of valid configurations
    """
    if partial_configuration is not None:
        result = count(bdd_model, [f.name for f in partial_configuration.get_selected_elements()])
    else:
        result = count(bdd_model, [])
    return result


def count(bdd_model: BDDModel, feature_assignment: list[str]) -> int:
    """
    Computes the number of valid configurations.
        :param feature_assignment: a list with a partial or a complete features' assignment
                (e.g., ["f1", "not f3", "f5"])
        :return: The number of valid configurations
    """
    # Check bdd_file
    bdd_file = bdd_model.check_file_existence(bdd_model.bdd_file, 'dddmp')

    # Get all feature names
    with open(bdd_file, "r", encoding='utf8') as file:
        bdd_code = file.read()
        varnames = re.search('varnames\\s+(.*)', bdd_code).group(1).split()

    expanded_assignment = []
    for feature in feature_assignment:
        feat = None
        if re.match('not\\s+', feature):
            feat = re.search('not\\s+(.*)', feature).group(1)
            if varnames.count(feat) == 0:
                raise FlamaException(feat + " is not a valid feature of " + bdd_file)
            else:
                feat += "=false"
        else:
            if varnames.count(feature) == 0:
                raise FlamaException(feature + " is not a valid feature of " + bdd_file)
            else:
                feat = feature + "=true"
        expanded_assignment.append(feat)

    # Run counter
    #print("Counting the number of valid configurations (this may take a while)...")
    count_process = bdd_model.run(BDDModel.COUNTER, *expanded_assignment, bdd_file)
    result = count_process.stdout.decode(locale.getdefaultlocale()[1])
    return int(result)
