from famapy.metamodels.fm_metamodel.transformations.featureide_reader import FeatureIDEReader

from famapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import FmToBDD
from famapy.metamodels.bdd_metamodel.transformations.bdd_writer import BDDDumpFormat, BDDWriter
from famapy.metamodels.bdd_metamodel.operations import (
    BDDProducts,
    BDDProductsNumber,
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling)


FM_PATH = 'tests/input_fms/featureide_models/pizzas.xml'


def test_main():
    # Load the feature model from FeatureIDE
    feature_model = FeatureIDEReader(FM_PATH).transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(feature_model).transform()

    # # Save the BDD as a .png
    bdd_writer = BDDWriter(bdd_model.root.var + '.png', bdd_model)
    bdd_writer.set_format(BDDDumpFormat.SVG)
    bdd_writer.set_roots([bdd_model.root])
    bdd_writer.transform()

    # BDD number of products
    nof_products = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Products: {nof_products}')

    # BDD products operation
    products = BDDProducts().execute(bdd_model).get_result()
    for i, prod in enumerate(products):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')

    assert len(products) == nof_products

    # BDD product distribution
    dist = BDDProductDistribution().execute(bdd_model).get_result()
    print(f'Product Distribution: {dist}')

    assert sum(dist) == nof_products

    # BDD feature inclusion probabilities
    prob = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    print('Feature Inclusion Probabilities:')
    for feat in prob.keys():
        print(f'{feat}: {prob[feat]}')

    # BDD Sampling
    sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, prod in enumerate(sample):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')


if __name__ == '__main__':
    test_main()