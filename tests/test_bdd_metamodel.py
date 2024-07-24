"""
The BDD plugin relies on the dd library.
The representation depends on what you want and have installed. 
For solving small to medium size problems, say for teaching, or prototyping new algorithms, 
pure Python can be more convenient. 
To work with larger problems, it works better if you install the C library CUDD. 
Let's call these “backends”.

The Flamapy BDD plugin imports the best available interface:
try:
    import dd.cudd as _bdd
except ImportError:
    import dd.autoref as _bdd

The same user code can run with both the Python and C backends.
The interfaces are almost identical, some differences may have.
For more information, check: https://github.com/tulip-control/dd
"""

import os

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.transformations import (
    FmToBDD,
    JSONWriter,
    PNGWriter,
    PickleWriter,
    DDDMPWriter,
    PDFWriter,
    SVGWriter,
    JSONReader,
    PickleReader,
    DDDMPReader
)
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling,
    BDDConfigurationsNumber,
    #BDDConfigurations,
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDVariantFeatures,
    BDDSatisfiable,
    BDDPureOptionalFeatures,
    BDDUniqueFeatures,
    BDDVariability,
    BDDCommonalityFactor,
    BDDHomogeneity
)


FM_PATH = 'resources/models/uvl_models/MobilePhone.uvl'
BDD_MODELS_PATH = 'resources/models/bdd_models/'


def analyze_bdd(bdd_model: BDDModel) -> None:
    # pylint: disable=too-many-locals
    # Satisfiable (valid)
    satisfiable = BDDSatisfiable().execute(bdd_model).get_result()
    print(f'Satisfiable (valid)?: {satisfiable}')

    # Configurations numbers
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')

    assert n_configs > 0 if satisfiable else n_configs == 0

    # Configurations
    # configs = BDDConfigurations().execute(bdd_model).get_result()
    # for i, config in enumerate(configs, 1):
    #     print(f'Config {i}: {config.get_selected_elements()}')

    # BDD product distribution
    dist_op = BDDProductDistribution().execute(bdd_model)
    dist = dist_op.get_result()
    print(f'Product Distribution: {dist}')
    print(f'#Products: {sum(dist)}')

    # BDD feature inclusion probabilities
    probabilities = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    print('Feature Inclusion Probabilities:')
    for feat, prob in probabilities.items():
        print(f'{feat}: {prob}')

    # Core features
    core_features = BDDCoreFeatures().execute(bdd_model).get_result()
    print(f'Core features: {core_features}')

    # Dead features
    dead_features = BDDDeadFeatures().execute(bdd_model).get_result()
    print(f'Dead features: {dead_features}')

    # Variant features
    variant_features = BDDVariantFeatures().execute(bdd_model).get_result()
    print(f'Variant features: {variant_features}')

    # Pure optional features
    pure_optional_features = BDDPureOptionalFeatures().execute(bdd_model).get_result()
    print(f'Pure optional features: {pure_optional_features}')

    # Unique features
    unique_features = BDDUniqueFeatures().execute(bdd_model).get_result()
    print(f'Unique features: {unique_features}')

    # Variability
    variability_op = BDDVariability().execute(bdd_model)
    total_variability = variability_op.total_variability()
    partial_variability = variability_op.partial_variability()
    print(f'Total variability: {total_variability}')
    print(f'Partial variability: {partial_variability}')

    # Commonality factor
    config = Configuration(elements={'MP3': True, 'GPS': False})
    cf_op = BDDCommonalityFactor()
    cf_op.set_configuration(config)
    commonality_factor = cf_op.execute(bdd_model).get_result()
    print(f'Commonality factor: {commonality_factor}')

    # Homogeneity
    homogeneity = BDDHomogeneity().execute(bdd_model).get_result()
    print(f'Homogeneity: {homogeneity}')

    # BDD Sampling
    sampling_op = BDDSampling()
    sampling_op.set_sample_size(5)
    sample = sampling_op.execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, config in enumerate(sample, 1):
        print(f'Config {i}: {config.get_selected_elements()}')


def main():
    _path, filename = os.path.split(FM_PATH)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model from UVLReader
    feature_model = UVLReader(FM_PATH).transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()
    print(bdd_model)

    # Apply different analysis operations
    analyze_bdd(bdd_model)

    # Save the BDD to different image formats
    PNGWriter(f'{filename}.{PNGWriter.get_destination_extension()}', bdd_model).transform()
    SVGWriter(f'{filename}.{SVGWriter.get_destination_extension()}', bdd_model).transform()
    PDFWriter(f'{filename}.{PDFWriter.get_destination_extension()}', bdd_model).transform()
    # Serialize the BDD to different formats
    JSONWriter(f'{filename}.{JSONWriter.get_destination_extension()}', bdd_model).transform()
    try:
        DDDMPWriter(f'{filename}.{DDDMPWriter.get_destination_extension()}', bdd_model).transform()
    except FlamaException as exception:
        print(exception)
    try:
        PickleWriter(f'{filename}.p', bdd_model).transform()
    except FlamaException as exception:
        print(exception)

    # Load the BDD model from a .json file
    reader = JSONReader(f'{os.path.join(BDD_MODELS_PATH, filename)}.json')
    #reader.set_preserve_original_ordering(True)
    bdd_model = reader.transform()
    print(f'BDD from JSON:\n{bdd_model}')
    analyze_bdd(bdd_model)

    # Load the BDD model from a .dddmp file
    bdd_model = DDDMPReader(f'{os.path.join(BDD_MODELS_PATH, filename)}.dddmp').transform()
    print(f'BDD from DDDMP:\n{bdd_model}')
    analyze_bdd(bdd_model)

    # Load the BDD model from a .p file
    try:
        bdd_model = PickleReader(f'{os.path.join(BDD_MODELS_PATH, filename)}.p').transform()
        print(f'BDD from Pickle:\n{bdd_model}')
        analyze_bdd(bdd_model)
    except FlamaException as exception:
        print(exception)


if __name__ == '__main__':
    import sys
    sys.setrecursionlimit(100000)
    main()
