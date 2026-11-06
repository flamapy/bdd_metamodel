"""Unique features, homogeneity, the metrics and satisfiable configurations derived from one
run of the inclusion-probability engine, checked against the per-feature formulas they replace."""
import os
import tempfile

import pytest

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDHomogeneity,
    BDDMetrics,
    BDDSatisfiableConfiguration,
    BDDUniqueFeatures,
)
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    feature_inclusion_counts,
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


MODELS = [
    'resources/models/uvl_models/MobilePhone.uvl',
    'resources/models/uvl_models/JHipster.uvl',
    'resources/models/uvl_models/Pizzas.uvl',
    'resources/models/uvl_models/Pizzas_complex.uvl',
    'resources/models/uvl_models/Truck.uvl',
    'resources/models/uvl_models/group_cardinalities.uvl',
    'resources/models/uvl_models/mutex.uvl',
]

SMARTWATCH = '''features
    Root
        mandatory
            Core
            Screen
                alternative
                    Analog
                    HighRes
                    EInk
        optional
            Camera
            Always
constraints
    Camera => HighRes
    Core => Always
'''

VOID = '''features
    Root
        mandatory
            A
        optional
            B
constraints
    !A
'''


def _read(path):
    return FmToBDD(UVLReader(path).transform()).transform()


def _read_text(uvl):
    handle, path = tempfile.mkstemp(suffix='.uvl')
    try:
        with os.fdopen(handle, 'w') as file:
            file.write(uvl)
        return _read(path)
    finally:
        os.remove(path)


@pytest.mark.parametrize('path', MODELS)
def test_unique_and_homogeneity_match_the_per_feature_counts(path):
    bdd = _read(path)
    n_vars = len(bdd.vars_order)
    total = bdd.count_models(bdd.root, n_vars)
    expected_counts = {}
    for var, feature in bdd.vars_features.items():
        restricted = bdd.bdd.let({var: True}, bdd.root)
        expected_counts[feature] = bdd.count_models(restricted, n_vars - 1)
    assert feature_inclusion_counts(bdd) == (total, expected_counts)
    assert BDDUniqueFeatures().execute(bdd).get_result() == \
        [feature for feature, count in expected_counts.items() if count == 1]
    commonality = [count / total for count in expected_counts.values()]
    assert BDDHomogeneity().execute(bdd).get_result() == \
        pytest.approx(sum(commonality) / len(commonality))


def test_unique_features_under_a_partial_configuration_count_per_feature():
    bdd = _read_text(SMARTWATCH)
    operation = BDDUniqueFeatures()
    operation.set_partial_configuration(Configuration({'Camera': True}))
    # Camera forces HighRes: exactly one configuration, so every feature in it is unique
    assert sorted(operation.execute(bdd).get_result()) == \
        sorted(['Root', 'Core', 'Screen', 'HighRes', 'Camera', 'Always'])


def test_void_model():
    bdd = _read_text(VOID)
    assert feature_inclusion_counts(bdd) == (0, {'Root': 0, 'A': 0, 'B': 0})
    assert BDDUniqueFeatures().execute(bdd).get_result() == []
    assert BDDHomogeneity().execute(bdd).get_result() == 0.0
    operation = BDDSatisfiableConfiguration()
    operation.set_configuration(Configuration({'B': True}))
    assert operation.execute(bdd).get_result() is False


def test_satisfiable_configuration_without_counting():
    bdd = _read_text(SMARTWATCH)
    operation = BDDSatisfiableConfiguration()
    operation.set_configuration(Configuration({'Camera': True, 'Analog': True}))
    assert operation.execute(bdd).get_result() is False
    operation.set_configuration(Configuration({'Camera': True}))
    assert operation.execute(bdd).get_result() is True
    full = Configuration({'Root': True, 'Core': True, 'Screen': True, 'EInk': True, 'Always': True})
    full.is_full = True
    operation.set_configuration(full)
    assert operation.execute(bdd).get_result() is True


def test_metrics_agree_with_the_operations():
    bdd = _read('resources/models/uvl_models/Pizzas_complex.uvl')
    operation = BDDMetrics()
    operation.only_these_metrics(['unique_features', 'homogeneity', 'configurations_number',
                                  'core_features', 'dead_features'])
    metrics = {m['name']: m['result'] for m in operation.calculate_metamodel_metrics(bdd)}
    assert metrics['Unique features'] == BDDUniqueFeatures().execute(bdd).get_result()
    assert metrics['Homogeneity'] == pytest.approx(BDDHomogeneity().execute(bdd).get_result())
    assert metrics['Configurations number'] == 25
    assert metrics['Core features'] == BDDCoreFeatures().execute(bdd).get_result()
    assert metrics['Dead features'] == BDDDeadFeatures().execute(bdd).get_result()
    assert operation._prod_dist_op is None  # the product distribution was not needed
    operation.only_these_metrics(['product_distribution', 'descriptive_statistics'])
    metrics = {m['name']: m['result'] for m in operation.calculate_metamodel_metrics(bdd)}
    assert sum(metrics['Product distribution']) == 25
    assert metrics['Descriptive statistics']['Min'] >= 0
