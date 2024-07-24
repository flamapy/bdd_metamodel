import pytest
from collections import defaultdict

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.transformations import (
    FmToBDD,
    JSONReader,
    PickleReader,
    DDDMPReader
)
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductDistribution,
    BDDFeatureInclusionProbability,
    BDDSampling,
    BDDConfigurationsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDVariantFeatures,
    BDDSatisfiable,
    BDDPureOptionalFeatures,
    BDDUniqueFeatures,
    BDDVariability,
    BDDHomogeneity
)


def _read_model(path: str) -> BDDModel:
    bdd_model = None  # Initialize bdd_model to None
    if path.endswith('.uvl'):
        feature_model = UVLReader(path).transform()
        bdd_model = FmToBDD(feature_model).transform()
    elif path.endswith('.json'):
        bdd_model = JSONReader(path).transform()
    elif path.endswith('.dddmp'):
        bdd_model = DDDMPReader(path).transform()
    elif path.endswith('.p'):
        bdd_model = PickleReader(path).transform()
    if bdd_model is None:
        raise ValueError(f"Unsupported file extension for path: {path}")
    return bdd_model

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', True), 
    ('resources/models/uvl_models/JHipster.uvl', True), 
#    ('resources/models/uvl_models/busybox_simple.uvl', True),
    ('resources/models/uvl_models/Pizzas.uvl', True), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', True), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', True), 
])
def test_bdd_satisfiable(path: str, expected: bool):
    bdd_model = _read_model(path)
    result = BDDSatisfiable().execute(bdd_model).get_result()
    assert result == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', 14),  
    ('resources/models/uvl_models/JHipster.uvl', 26256), 
#    ('resources/models/uvl_models/busybox_simple.uvl', 0),
    ('resources/models/uvl_models/Pizzas.uvl', 42), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', 25), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', 734720), 
])
def test_nconfigs(path: str, expected: int):
    bdd_model = _read_model(path)
    n_configs = BDDConfigurationsNumber().execute(bdd_model).get_result()
    assert n_configs == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', [0, 0, 0, 0, 3, 5, 7, 4, 1, 0, 0]),  
    ('resources/models/uvl_models/JHipster.uvl', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 16, 42, 106, 200, 238, 250, 488, 1276, 2688, 4314, 5460, 5322, 3696, 1668, 432, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', [0, 0, 0, 0, 0, 0, 0, 12, 18, 10, 2, 0, 0]), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', [0, 0, 0, 0, 0, 0, 0, 8, 11, 5, 1, 0, 0]), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', [0, 0, 0, 1, 15, 115, 625, 2669, 9084, 24500, 52364, 89251, 122277, 135507, 121826, 88721, 51980, 24176, 8734, 2366, 452, 54, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 
])
def test_bdd_product_distribution(path: str, expected: list):
    bdd_model = _read_model(path)
    dist_op = BDDProductDistribution().execute(bdd_model)
    dist = dist_op.get_result()
    assert dist == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', defaultdict(float, {'"Mobile Phone"': 1.0, 'Calls': 1.0, 'Screen': 1.0, 'Basic': 0.14285714285714285, 'Color': 0.2857142857142857, '"High Resolution"': 0.5714285714285714, 'GPS': 0.42857142857142855, 'Media': 0.6428571428571429, 'Camera': 0.2857142857142857, 'MP3': 0.5})),  
    ('resources/models/uvl_models/JHipster.uvl', defaultdict(float, {'JHipster': 1.0, 'Generator': 1.0, 'Server': 0.0517976843388178, 'Application': 0.9482023156611822, 'MicroserviceApplication': 0.03473491773308958, 'UaaServer': 0.017062766605728214, 'MicroserviceGateway': 0.2730042656916514, 'Monolithic': 0.6751980499695308, 'Authentication': 1.0, 'HTTPSession': 0.27056672760511885, 'OAuth2': 0.1340645947592931, 'Uaa': 0.17093235831809872, 'JWT': 0.4244363193174893, 'SocialLogin': 0.2681291895185862, 'Database': 0.9993906154783668, 'SQL': 0.9707495429616088, 'Cassandra': 0.010664229128580133, 'MongoDB': 0.01797684338817794, 'Hibernate2ndLvlCache': 0.6471663619744058, 'HazelCast': 0.3235831809872029, 'EhCache': 0.3235831809872029, 'Development': 0.9707495429616088, 'H2': 0.6471663619744058, 'PostgreSQLDev': 0.10786106032906764, 'MariaDBDev': 0.10786106032906764, 'MySql': 0.10786106032906764, 'DiskBased': 0.3235831809872029, 'InMemory': 0.3235831809872029, 'Production': 0.9707495429616088, 'MySQL': 0.3235831809872029, 'MariaDB': 0.3235831809872029, 'PostgreSQL': 0.3235831809872029, 'ElasticSearch': 0.4853747714808044, 'SpringWebSockets': 0.4741011578305911, 'Libsass': 0.4741011578305911, 'ClusteredSession': 0.4741011578305911, 'BackEnd': 1.0, 'Gradle': 0.5, 'Maven': 0.5, 'InternationalizationSupport': 0.5, 'Docker': 0.5, 'TestingFrameworks': 1.0, 'Protractor': 0.9482023156611822, 'Gatling': 1.0, 'Cucumber': 1.0})), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', defaultdict(float, {'Pizza': 1.0, 'Topping': 1.0, 'Salami': 0.5714285714285714, 'Ham': 0.5714285714285714, 'Mozzarella': 0.5714285714285714, 'Size': 1.0, 'Normal': 0.3333333333333333, 'Big': 0.6666666666666666, 'Dough': 1.0, 'Neapolitan': 0.5, 'Sicilian': 0.5, 'CheesyCrust': 0.3333333333333333})), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', defaultdict(float, {'Pizza': 1.0, 'Topping': 1.0, 'Salami': 0.48, 'Ham': 0.48, 'Mozzarella': 0.64, 'Size': 1.0, 'Normal': 0.36, 'Big': 0.64, 'Dough': 1.0, 'Neapolitan': 0.16, 'Sicilian': 0.84, 'CheesyCrust': 0.36})), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', defaultdict(float,{'v0': 1.0, 'Cycle': 1.0, 'Smoother': 1.0, 'v1': 0.55, 'v2': 0.45, 'v3': 0.45, 'v4': 0.1, 'v5': 0.0, 'v6': 0.45, 'v7': 0.45, 'v8': 0.475, 'v9': 0.125, 'v10': 0.0, 'v11': 0.49825783972125437, 'v12': 0.49825783972125437, 'v13': 0.49825783972125437, 'v14': 0.49825783972125437, 'v15': 0.0, 'v16': 0.0, 'v17': 0.49825783972125437, 'v18': 0.445993031358885, 'v19': 0.445993031358885, 'v20': 0.445993031358885, 'v21': 0.10801393728222997, 'v22': 0.0, 'V': 0.5, 'F': 0.5, 'Jacobi': 0.5, 'ColorGS': 0.5, 'Line': 0.5, 'ZebraLine': 0.5})), 
])
def test_probabilities(path: str, expected: dict):
    bdd_model = _read_model(path)
    probabilities = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    print(probabilities)
    assert str(probabilities) == str(expected)

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', ['"Mobile Phone"', 'Calls', 'Screen']),
    ('resources/models/uvl_models/JHipster.uvl', ['JHipster', 'Generator', 'Authentication', 'BackEnd', 'TestingFrameworks', 'Gatling', 'Cucumber']), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', ['Pizza', 'Topping', 'Size', 'Dough']), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', ['Pizza', 'Topping', 'Size', 'Dough']), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', ['v0', 'Cycle', 'Smoother']),   
])
def test_core_features(path: str, expected: list):
    bdd_model = _read_model(path)
    core_features = BDDCoreFeatures().execute(bdd_model).get_result()
    assert core_features == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', []),
    ('resources/models/uvl_models/JHipster.uvl', []), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', []), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', []), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', ['v5', 'v10', 'v15', 'v16', 'v22']),   
])
def test_dead_features(path: str, expected: list):
    bdd_model = _read_model(path)
    dead_features = BDDDeadFeatures().execute(bdd_model).get_result()
    assert dead_features == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', ['Basic', 'Color', '"High Resolution"', 'GPS', 'Media', 'Camera', 'MP3']),
    ('resources/models/uvl_models/JHipster.uvl', ['Server', 'Application', 'MicroserviceApplication', 'UaaServer', 'MicroserviceGateway', 'Monolithic', 'HTTPSession', 'OAuth2', 'Uaa', 'JWT', 'SocialLogin', 'Database', 'SQL', 'Cassandra', 'MongoDB', 'Hibernate2ndLvlCache', 'HazelCast', 'EhCache', 'Development', 'H2', 'PostgreSQLDev', 'MariaDBDev', 'MySql', 'DiskBased', 'InMemory', 'Production', 'MySQL', 'MariaDB', 'PostgreSQL', 'ElasticSearch', 'SpringWebSockets', 'Libsass', 'ClusteredSession', 'Gradle', 'Maven', 'InternationalizationSupport', 'Docker', 'Protractor']), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', ['Salami', 'Ham', 'Mozzarella', 'Normal', 'Big', 'Neapolitan', 'Sicilian', 'CheesyCrust']), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', ['Salami', 'Ham', 'Mozzarella', 'Normal', 'Big', 'Neapolitan', 'Sicilian', 'CheesyCrust']), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', ['v1', 'v2', 'v3', 'v4', 'v6', 'v7', 'v8', 'v9', 'v11', 'v12', 'v13', 'v14', 'v17', 'v18', 'v19', 'v20', 'v21', 'V', 'F', 'Jacobi', 'ColorGS', 'Line', 'ZebraLine']),   
])
def test_variant_features(path: str, expected: list):
    bdd_model = _read_model(path)
    variant_features = BDDVariantFeatures().execute(bdd_model).get_result()
    assert variant_features == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', ['MP3']),
    ('resources/models/uvl_models/JHipster.uvl', ['Gradle', 'Maven', 'InternationalizationSupport', 'Docker']), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', ['Neapolitan', 'Sicilian']), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', []), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', ['V', 'F', 'Jacobi', 'ColorGS', 'Line', 'ZebraLine']),   
])
def test_pure_optional_features(path: str, expected: list):
    bdd_model = _read_model(path)
    pure_optional_features = BDDPureOptionalFeatures().execute(bdd_model).get_result()
    assert pure_optional_features == expected

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', []),
    ('resources/models/uvl_models/JHipster.uvl', []), 
#    ('resources/models/uvl_models/busybox_simple.uvl', []),
    ('resources/models/uvl_models/Pizzas.uvl', []), 
    ('resources/models/uvl_models/Pizzas_complex.uvl', []), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl', []),   
])
def test_unique_features(path: str, expected: list):
    bdd_model = _read_model(path)
    unique_features = BDDUniqueFeatures().execute(bdd_model).get_result()
    assert unique_features == expected

@pytest.mark.parametrize("path, expected_total, expected_partial", [
    ('resources/models/uvl_models/MobilePhone.uvl', 0.013685239491691105, 0.11023622047244094),
    ('resources/models/uvl_models/JHipster.uvl',  7.462404028047088e-10, 9.551877155934751e-08), 
#    ('resources/models/uvl_models/busybox_simple.uvl',  0.0, 0.0),
    ('resources/models/uvl_models/Pizzas.uvl',  0.010256410256410256, 0.16470588235294117), 
    ('resources/models/uvl_models/Pizzas_complex.uvl',  0.006105006105006105, 0.09803921568627451), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl',  0.0003421306611700592, 0.08758545965975043),   
])
def test_variability(path: str, expected_total: float, expected_partial: float):
    bdd_model = _read_model(path)
    variability_op = BDDVariability().execute(bdd_model)
    total_variability = variability_op.total_variability()
    partial_variability = variability_op.partial_variability()
    assert total_variability == expected_total
    assert partial_variability == expected_partial

@pytest.mark.parametrize("path, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', 0.5857142857142857),
    ('resources/models/uvl_models/JHipster.uvl',  0.5099397386417497), 
#    ('resources/models/uvl_models/busybox_simple.uvl',  0.0),
    ('resources/models/uvl_models/Pizzas.uvl',  0.6706349206349206), 
    ('resources/models/uvl_models/Pizzas_complex.uvl',  0.6633333333333333), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl',  0.41894458806339213),     
])
def test_homogeneity(path: str, expected: float):    
    bdd_model = _read_model(path)
    homogeneity = BDDHomogeneity().execute(bdd_model).get_result()
    assert homogeneity == expected

@pytest.mark.parametrize("path, sample_size, expected", [
    ('resources/models/uvl_models/MobilePhone.uvl', 5, 5),
    ('resources/models/uvl_models/JHipster.uvl',  5, 5), 
#    ('resources/models/uvl_models/busybox_simple.uvl',  5, []),
    ('resources/models/uvl_models/Pizzas.uvl',  5, 5), 
    ('resources/models/uvl_models/Pizzas_complex.uvl',  5, 5), 
    ('resources/models/uvl_models/Trimesh_NFM.uvl',  5, 5),     
])
def test_sampling(path: str, sample_size: int, expected: list):
    bdd_model = _read_model(path)
    sampling_op = BDDSampling()
    sampling_op.set_sample_size(sample_size)
    sample = sampling_op.execute(bdd_model).get_result()
    assert len(sample) == expected