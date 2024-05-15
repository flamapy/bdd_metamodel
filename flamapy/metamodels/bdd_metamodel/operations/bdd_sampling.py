import re
import locale
from typing import Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.operations import Sampling
from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.configuration_metamodel.models import Configuration
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
    def __init__(self) -> None:
        self.result: list[Configuration] = []
        self.sample_size: int = 0
        self.with_replacement: bool = False
        self.partial_configuration: Optional[Configuration] = None

    def set_sample_size(self, sample_size: int) -> None:
        if sample_size <= 0:
            raise FlamaException(f'Sample size {sample_size} must be a positive integer.')
        self.sample_size = sample_size

    def set_with_replacement(self, with_replacement: bool) -> None:
        self.with_replacement = with_replacement

    def set_partial_configuration(self, partial_configuration: Configuration) -> None:
        self.partial_configuration = partial_configuration

    def get_sample(self) -> list[Configuration]:
        return self.get_result()

    def get_result(self) -> list[Configuration]:
        return self.result

    def execute(self, model: VariabilityModel) -> 'BDDSampling':
        bdd_model = cast(BDDModel, model)
        self.result = sample(bdd_model, 
                             self.sample_size, 
                             self.with_replacement, 
                             self.partial_configuration)
        return self


def sample(bdd_model: BDDModel, 
           sample_size: int, 
           with_replacement: bool,
           partial_configuration: Optional[Configuration]  # pylint: disable=unused-argument
           ) -> list[Configuration]:
    # BDDSampler requires the bdd_file with the '.dddmp' extension.
    bdd_file = bdd_model.check_file_existence(bdd_model.bdd_file, 'dddmp')

    # Run binary BDDSampler
    parameters = ["-names"]
    if not with_replacement:
        parameters.append("-norep")
    sample_process = bdd_model.run(BDDModel.BDD_SAMPLER, str(sample_size), bdd_file)
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
