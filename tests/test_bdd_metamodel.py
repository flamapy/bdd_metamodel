from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD, BDDWriter
from flamapy.metamodels.bdd_metamodel.transformations.bdd_writer import BDDDumpFormat
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


def main():
    # Load the feature model from UVLReader
    feature_model = UVLReader('tests/input_fms/uvl_models/Pizzas.uvl').transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()

    # Save the BDD as a .png
    bdd_writer = BDDWriter(bdd_model.root.var + '.png', bdd_model)
    bdd_writer.set_format(BDDDumpFormat.SVG)
    bdd_writer.set_roots([bdd_model.root])
    bdd_writer.transform()
    
    # Satisfiable (valid)
    satisfiable = BDDSatisfiable().execute(bdd_model).get_result()
    print(f'Satisfiable (valid)?: {satisfiable}')

    # Configurations numbers
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')

    # Configurations
    configs = BDDConfigurations().execute(bdd_model).get_result()
    for i, config in enumerate(configs, 1):
        print(f'Config {i}: {config.get_selected_elements()}')

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


if __name__ == '__main__':
    main()