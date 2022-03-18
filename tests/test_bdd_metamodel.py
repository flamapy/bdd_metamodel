from famapy.metamodels.fm_metamodel.transformations import FeatureIDEReader

from famapy.metamodels.bdd_metamodel.transformations import FmToBDD, DDDMPWriter
from famapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling
)


def main():
    # Load the feature model from FeatureIDE
    feature_model = FeatureIDEReader('input_fms/featureide_models/jHipster.xml').transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()

    # Save the BDD as .dddmp file
    DDDMPWriter(feature_model.root.name + '_bdd', bdd_model).transform()

    # BDD product distribution
    dist = BDDProductDistribution().execute(bdd_model).get_result()
    print(f'Product Distribution: {dist}')
    print(f'#Products: {sum(dist)}')

    # BDD feature inclusion probabilities
    probabilities = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    print('Feature Inclusion Probabilities:')
    for feat, prob in probabilities.items():
        print(f'{feat}: {prob}')

    # BDD Sampling
    sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, product in enumerate(sample, 1):
        print(f'Product {i}: {product.get_selected_elements()}')


if __name__ == "__main__":
    main()
