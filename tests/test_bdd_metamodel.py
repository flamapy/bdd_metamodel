import os

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
    BDDSatisfiable
)


FM_PATH = 'tests/models/uvl_models/Pizzas.uvl'
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
    dist = BDDProductDistribution().execute(bdd_model).get_result()
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

    # BDD Sampling
    sample_op = BDDSampling()
    sample_op.set_sample_size(5)
    sample = sample_op.execute(bdd_model).get_result()
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
