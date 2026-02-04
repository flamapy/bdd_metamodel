from flamapy.core.discover import DiscoverMetamodels
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDConfigurationsWithNFeatures,
    BDDCoreFeatures,
    BDDFalseOptionalFeatures
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


FM_MODEL = 'resources/models/uvl_models/Pizzas.uvl'


def main() -> None:
    dm = DiscoverMetamodels()
    fm_model = dm.use_transformation_t2m(FM_MODEL, 'fm')
    bdd_model = FmToBDD(fm_model).transform()
    print(f'BDD model: {bdd_model}')

    pdist = BDDProductDistribution().execute(bdd_model).get_result()
    print(f'Product Distribution ({sum(pdist)}): {pdist}')

    n_features = 7
    bdd_configs_n_op = BDDConfigurationsWithNFeatures()
    bdd_configs_n_op.set_n_features(n_features)
    bdd_configs_n_op.execute(bdd_model)
    configs_n = bdd_configs_n_op.get_result()
    configs = list(configs_n)
    print(f'Configurations with {n_features} features: {len(configs)}')
    for i, config in enumerate(configs, 1):
        print(f'Config {i} with {n_features} features: {config.get_selected_elements()}')

    core_features = BDDCoreFeatures().execute(bdd_model).get_result()
    print(f'Core features: {core_features}')

    print(f'Features: {fm_model.get_features()}')
    print(f'Variables: {bdd_model.features_vars}')
    print(f'Feature-vars: {bdd_model.features_vars}')
    print(f'Var-features: {bdd_model.vars_features}')

    false_optional_features = BDDFalseOptionalFeatures().execute(bdd_model).get_result()
    print(f'False-optional features: {false_optional_features}')



if __name__ == "__main__":
    main()
