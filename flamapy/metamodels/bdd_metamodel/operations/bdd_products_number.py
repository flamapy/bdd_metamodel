import re
import locale

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.core.operations import ProductsNumber

from flamapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDProductsNumber(ProductsNumber):
    """It computes the number of solutions of the BDD model.

    It also supports counting the solutions from a given partial configuration.
    """

    def __init__(self, partial_configuration: Configuration = None) -> None:
        self.result = 0
        self.bdd_model = None
        self.feature_model = None
        self.partial_configuration = partial_configuration

    def execute(self, model: BDDModel) -> 'BDDProductsNumber':
        self.bdd_model = model
        self.result = products_number(self.bdd_model, self.partial_configuration)
        return self

    def get_result(self) -> int:
        return self.result

    def get_products_number(self) -> int:
        return products_number(self.bdd_model, self.partial_configuration)


def products_number(bdd_model: BDDModel, partial_configuration: Configuration = None) -> int:
    """
    Computes the number of valid configurations.
        :param feature_assignment: a list with a partial or a complete features' assignment
               (e.g., ["f1", "not f3", "f5"])
        :return: The number of valid configurations
    """
    if partial_configuration is not None:
        result = count(bdd_model, [f.name for f in partial_configuration.get_selected_elements()])
    else:
        result = count(bdd_model)
    return result
    

def count(bdd_model: BDDModel, feature_assignment: list[str]=[]) -> int:
    """
    Computes the number of valid configurations.
        :param feature_assignment: a list with a partial or a complete features' assignment
                (e.g., ["f1", "not f3", "f5"])
        :return: The number of valid configurations
    """
    # Check bdd_file
    bdd_file = bdd_model.check_file_existence(bdd_model.get_bdd_file(), 'dddmp')

    # Get all feature names
    f = open(bdd_file, "r")
    bdd_code = f.read()
    varnames = re.search('varnames\\s+(.*)', bdd_code).group(1).split()
    f.close()

    expanded_assignment = []
    for feature in feature_assignment:
        ft = None
        if re.match('not\\s+', feature):
            ft = re.search('not\\s+(.*)', feature).group(1)
            if varnames.count(ft) == 0:
                raise Exception(ft + " is not a valid feature of " + bdd_file)
            else:
                ft += "=false"
        else:
            if varnames.count(feature) == 0:
                raise Exception(feature + " is not a valid feature of " + bdd_file)
            else:
                ft = feature + "=true"
        expanded_assignment.append(ft)

    # Run counter
    print("Counting the number of valid configurations (this may take a while)...")
    count_process = bdd_model.run(BDDModel.COUNTER, *expanded_assignment, bdd_file)
    result = count_process.stdout.decode(locale.getdefaultlocale()[1])
    return int(result)
