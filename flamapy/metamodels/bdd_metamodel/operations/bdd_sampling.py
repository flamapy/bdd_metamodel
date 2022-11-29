import re
import locale
from typing import Optional

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.core.operations import Sampling
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class BDDSampling(Sampling):
    """Generates a uniform random sample of a given size with or without replacement.

    For detailed information, see the paper: 
    R. Heradio, D. Fernandez-Amoros, J. Galindo, D. Benavides, and D. Batory, 
    "Uniform and Scalable Sampling of Highly Configurable Systems,” 
    Empirical Software Engineering, 2022.

    The sample size is the number of configurations to be generated.
    If the 'with_replacement' parameter is True, every configuration is generated from scratch, 
    independently of the prior generated configurations. 
    Accordingly, a configuration may be repeated in the sample. 
    If the 'with_replacement' parameter is False then the sample is generated without replacement 
    and there won't be any repeated configurations.

    Return a list with the generated configurations. Each element in that list is a configuration, 
    and each configuration is in turn a list of strings encoding the feature values.
    """
    def __init__(self, size: int, with_replacement: bool = False) -> None:
        self.result: list[Configuration] = []
        self.bdd_model = None
        self.size = size 
        self.with_replacement = with_replacement 

    def execute(self, model: BDDModel) -> 'BDDSampling':
        self.bdd_model = model
        self.result = sample(self.bdd_model, self.size, self.with_replacement)
        return self

    def get_result(self) -> list[Configuration]:
        return self.result

    def sample(self, size: int, with_replacement: bool = False,
               partial_configuration: Optional[Configuration] = None) -> list[Configuration]:
        return sample(self.bdd_model, size, with_replacement)


def sample(bdd_model: BDDModel, size: int, with_replacement: bool = False) -> list[Configuration]:
    # Check config_number
    if size <= 0:
        message = 'Size must be an integer greater than zero.'
        raise Exception(message) from Exception

    # BDDSampler requires the bdd_file with the '.dddmp' extension.
    bdd_file = bdd_model.check_file_existence(bdd_model.get_bdd_file(), 'dddmp')

    # Run binary BDDSampler
    parameters = ["-names"]
    if not with_replacement:
        parameters.append("-norep")
    sample_process = bdd_model.run(BDDModel.BDD_SAMPLER, "-names", str(size), bdd_file)
    result = sample_process.stdout.decode(locale.getdefaultlocale()[1])
    line_iterator = iter(result.splitlines())
    configurations = []
    for line in line_iterator:
        parsed_line = re.compile(r'\s+').split(line)
        configuration = {}
        negation = False
        for element in parsed_line:
            if element != "":
                if element == "not":
                    negation = True
                else:
                    configuration[element] = not negation
                    negation = False
        configurations.append(Configuration(configuration))
    return configurations
