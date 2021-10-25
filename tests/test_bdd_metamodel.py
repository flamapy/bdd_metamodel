from famapy.metamodels.fm_metamodel.transformations.featureide_reader import FeatureIDEReader

from famapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import FmToBDD
from famapy.metamodels.bdd_metamodel.transformations.bdd_writer import BDDDumpFormat, BDDWriter
from famapy.metamodels.bdd_metamodel.operations import (
    BDDProducts, 
    BDDProductsNumber, 
    BDDProductDistributionBF, 
    BDDFeatureInclusionProbabilityBF, 
    BDDSampling)


# Models in FeatureIDE format for testing
INPUT_FMS = 'input_fms/featureide_models/'
PIZZA_FM = INPUT_FMS + 'pizzas.xml'
JHIPSTER_FM = INPUT_FMS + 'jHipster.xml'

# Models in CNF for testing (the same model in different CNF syntax notation)
INPUT_CNFS = 'input_fms/cnf_models/'
PIZZA_FM_CNF_SHORT = INPUT_CNFS + 'pizza_cnf_short.txt'
PIZZA_FM_CNF_JAVA = INPUT_CNFS + 'pizza_cnf_java.txt'
PIZZA_FM_CNF_LOGIC = INPUT_CNFS + 'pizza_cnf_logic.txt'
PIZZA_FM_CNF_TEXTUAL = INPUT_CNFS + 'pizza_cnf_textual.txt'


def main():
    # Load the feature model from FeatureIDE
    fm = FeatureIDEReader('input_fms/featureide_models/pizzas.xml').transform() 

    # Create the BDD from the FM
    bdd_model = FmToBDD(fm).transform()

    # Save the BDD as a .png
    bdd_writer = BDDWriter(bdd_model.root.var+'.png', bdd_model)
    bdd_writer.set_format(BDDDumpFormat.PNG)
    bdd_writer.set_roots([bdd_model.root])
    bdd_writer.transform()

    # BDD number of products
    nof_products = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Products: {nof_products}')

    # BDD products operation
    products = BDDProducts().execute(bdd_model).get_result()
    for i, prod in enumerate(products):
        print(f'Product {i}: {[f for f in prod.elements if prod.elements[f]]}')

    assert len(products) == nof_products 
    
    # BDD product distribution
    dist = BDDProductDistributionBF().execute(bdd_model).get_result()
    print(f'Product Distribution: {dist}')

    assert sum(dist) == nof_products

    # BDD feature inclusion probabilities
    prob = BDDFeatureInclusionProbabilityBF().execute(bdd_model).get_result()
    print('Feature Inclusion Probabilities:')
    for f in prob.keys():
        print(f'{f}: {prob[f]}')

    # BDD Sampling
    sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, prod in enumerate(sample):
        print(f'Product {i}: {[f for f in prod.elements if prod.elements[f]]}')


if __name__ == "__main__":
    main()
