import os

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD, DDDMPWriter, DDDMPReader
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling,
    BDDConfigurationsNumber,
    BDDConfigurations,
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


FM_PATH = 'tests/models/uvl_models/MobilePhone.uvl'
BDD_MODELS_PATH = 'tests/models/bdd_models/'


def analyze_bdd(bdd_model: BDDModel) -> None:
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
    path, filename = os.path.split(FM_PATH)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model from UVLReader
    feature_model = UVLReader(FM_PATH).transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()

    analyze_bdd(bdd_model)

    # Save the BDD as .dddmp file
    DDDMPWriter(f'{filename}.{DDDMPWriter.get_destination_extension()}', bdd_model).transform()
    
    # Load a BDD from a .dddmp file
    bdd_model = DDDMPReader(f'{os.path.join(BDD_MODELS_PATH, filename)}.dddmp').transform()
    analyze_bdd(bdd_model)

   
if __name__ == '__main__':
    main()
