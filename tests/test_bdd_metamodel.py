from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD, DDDMPWriter
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling,
    BDDProductsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDValid
)


def main():
    # Load the feature model from UVLReader
    feature_model = UVLReader('tests/input_fms/uvl_models/Pizzas.uvl').transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()

    # Save the BDD as .dddmp file
    DDDMPWriter(f'{feature_model.root.name}_bdd.{DDDMPWriter.get_destination_extension()}', 
                bdd_model).transform()
    
    # Valid
    valid = BDDValid().execute(bdd_model).get_result()
    print(f'Valid?: {valid}')

    # Products numbers
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')

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
    sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, product in enumerate(sample, 1):
        print(f'Product {i}: {product.get_selected_elements()}')



if __name__ == '__main__':
    main()
