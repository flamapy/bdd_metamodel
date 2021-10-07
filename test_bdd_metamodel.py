from famapy.metamodels.fm_metamodel.transformations.featureide_parser import FeatureIDEParser

from famapy.metamodels.bdd_metamodel.models.utils import TextCNFModel
from famapy.metamodels.bdd_metamodel.models import BDDModel
from famapy.metamodels.bdd_metamodel.transformations.bdd_writer import BDDDumpFormat, BDDWriter
from famapy.metamodels.bdd_metamodel.operations import BDDProducts, BDDProductsNumber, BDDProductDistributionBF, BDDFeatureInclusionProbabilityBF, BDDSampling
from famapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import FmToBDD

# Models in FeatureIDE format for testing
INPUT_FMS = 'input_fms/FeatureIDE_models/'
PIZZA_FM = INPUT_FMS + 'pizzas.xml'

# Models in CNF for testing (the same model in different CNF syntax notation)
INPUT_CNFS = 'input_fms/cnf_models/'
PIZZA_FM_CNF_SHORT = INPUT_CNFS + 'pizza_cnf_short.txt'
PIZZA_FM_CNF_JAVA = INPUT_CNFS + 'pizza_cnf_java.txt'
PIZZA_FM_CNF_LOGIC = INPUT_CNFS + 'pizza_cnf_logic.txt'
PIZZA_FM_CNF_TEXTUAL = INPUT_CNFS + 'pizza_cnf_textual.txt'


def main():
    # Load the feature model from FeatureIDE
    fm = FeatureIDEParser(PIZZA_FM).transform() 

    # Create the BDD from the FM
    bdd_model = FmToBDD(fm).transform()

    # Alternative:
    # Load the feature model from a CNF formula
    # cnf_model = TextCNFModel()
    # cnf_model.from_textual_cnf_file(PIZZA_FM_CNF_JAVA)

    # Create the BDD model from the CNF model
    #bdd_model = BDDModel()
    #bdd_model.from_textual_cnf(cnf_model.get_textual_cnf_formula(BDDModel.CNF_NOTATION), cnf_model.get_variables())

    # Save the BDD as a .png
    bdd_writer = BDDWriter(bdd_model.root.var+'.png', bdd_model)
    bdd_writer.set_format(BDDDumpFormat.PNG)
    bdd_writer.set_roots([bdd_model.root])
    bdd_writer.transform()

    # BDD Solutions operation
    solutions = BDDProducts().execute(bdd_model).get_result()
    for i, sol in enumerate(solutions):
        print(f'Sol. {i}: {[f for f in sol.elements if sol.elements[f]]}')

    # BDD number of solutions
    nof_solutions = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Solutions: {nof_solutions}')

    assert len(solutions) == nof_solutions 

    # BDD product distribution
    dist = BDDProductDistributionBF().execute(bdd_model).get_result()
    print(f'Product Distribution: {dist}')

    assert sum(dist) == nof_solutions

    # BDD feature inclusion probabilities
    prob = BDDFeatureInclusionProbabilityBF().execute(bdd_model).get_result()
    print('Feature Inclusion Probabilities:')
    for f in prob.keys():
        print(f'{f}: {prob[f]}')

    # BDD Sampling
    sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    print('Uniform Random Sampling:')
    for i, sol in enumerate(sample):
        print(f'Sol. {i}: {[f for f in sol.elements if sol.elements[f]]}')


if __name__ == "__main__":
    main()
