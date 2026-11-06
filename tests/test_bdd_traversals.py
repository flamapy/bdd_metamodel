"""Backbone (core and dead features) and false-optional features computed with BDD traversals,
checked against the counting engine and the SAT plugin."""
import os
import tempfile

import pytest

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.pysat_metamodel.operations import (
    PySATBackbone,
    PySATFalseOptionalFeatures,
)
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDBackbone,
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDFalseOptionalFeatures,
)
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    exact_feature_inclusion,
)
from flamapy.metamodels.bdd_metamodel.operations.bdd_traversals import (
    possible_literals,
    refuted_implications,
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
            Connector
                or
                    USB
                    Wireless
                    Bluetooth
            Camera
            GPS
            Unreachable
            Always
            NeedsParent
                optional
                    Child
constraints
    Camera => HighRes
    Unreachable => !Root
    Core => Always
    NeedsParent => Child
    GPS => Connector
'''

VOID = '''features
    Root
        mandatory
            A
        optional
            B
            C
constraints
    !A
'''

IMPLICATION = '''features
    Root
        optional
            A
            B
constraints
    A => B
'''


def _read(path):
    feature_model = UVLReader(path).transform()
    return feature_model, FmToBDD(feature_model).transform()


def _read_text(uvl):
    handle, path = tempfile.mkstemp(suffix='.uvl')
    try:
        with os.fdopen(handle, 'w') as file:
            file.write(uvl)
        return _read(path)
    finally:
        os.remove(path)


@pytest.mark.parametrize('path', MODELS)
def test_backbone_matches_the_inclusion_probabilities(path):
    _, bdd = _read(path)
    probs = exact_feature_inclusion(bdd)
    result = BDDBackbone().execute(bdd).get_result()
    assert result['core'] == [feat for feat, prob in probs.items() if prob == 1]
    assert result['dead'] == [feat for feat, prob in probs.items() if prob == 0]
    assert BDDCoreFeatures().execute(bdd).get_result() == result['core']
    assert BDDDeadFeatures().execute(bdd).get_result() == result['dead']


@pytest.mark.parametrize('path', MODELS)
def test_false_optional_matches_the_sat_plugin(path):
    feature_model, bdd = _read(path)
    sat = FmToPysat(feature_model).transform()
    assert sorted(BDDFalseOptionalFeatures().execute(bdd).get_result()) == \
        sorted(PySATFalseOptionalFeatures().execute(sat).get_result())


def test_smartwatch_backbone_and_false_optional_match_the_sat_plugin():
    feature_model, bdd = _read_text(SMARTWATCH)
    sat = FmToPysat(feature_model).transform()
    bdd_backbone = BDDBackbone().execute(bdd).get_result()
    sat_backbone = PySATBackbone().execute(sat).get_result()
    assert sorted(bdd_backbone['core']) == sorted(sat_backbone['core'])
    assert sorted(bdd_backbone['dead']) == sorted(sat_backbone['dead']) == ['Unreachable']
    assert 'Always' in bdd_backbone['core']
    false_optional = BDDFalseOptionalFeatures().execute(bdd).get_result()
    assert sorted(false_optional) == \
        sorted(PySATFalseOptionalFeatures().execute(sat).get_result())
    assert 'Child' in false_optional and 'HighRes' not in false_optional


def test_backbone_under_a_partial_configuration():
    _, bdd = _read_text(SMARTWATCH)
    configuration = Configuration({'Camera': True})
    probs = exact_feature_inclusion(bdd, configuration)
    operation = BDDBackbone()
    operation.set_partial_configuration(configuration)
    result = operation.execute(bdd).get_result()
    assert result['core'] == [feat for feat, prob in probs.items() if prob == 1]
    assert result['dead'] == [feat for feat, prob in probs.items() if prob == 0]
    assert {'Camera', 'HighRes'} <= set(result['core'])
    assert {'Analog', 'EInk', 'Unreachable'} <= set(result['dead'])
    # a configuration no product extends: every feature is dead, none is core
    operation.set_partial_configuration(Configuration({'Unreachable': True}))
    result = operation.execute(bdd).get_result()
    assert result['core'] == [] and len(result['dead']) == len(bdd.vars_order)


def test_void_model():
    feature_model, bdd = _read_text(VOID)
    assert BDDBackbone().execute(bdd).get_result() == {'core': [], 'dead': ['Root', 'A', 'B', 'C']}
    # the implications hold vacuously, as in the SAT plugin
    assert sorted(BDDFalseOptionalFeatures().execute(bdd).get_result()) == ['B', 'C']
    sat = FmToPysat(feature_model).transform()
    assert sorted(PySATFalseOptionalFeatures().execute(sat).get_result()) == ['B', 'C']


def test_refuted_implications_in_both_level_orders():
    _, bdd = _read_text(IMPLICATION)
    var = bdd.features_vars
    pairs = [(var['A'], var['B']), (var['B'], var['A']), (var['Root'], var['A']),
             (var['A'], var['Root']), (var['B'], var['Root']), (var['Root'], var['B'])]
    assert refuted_implications(bdd, pairs) == [False, True, True, False, False, True]
    can_true, can_false = possible_literals(bdd)
    assert can_true == [True, True, True]
    assert can_false == [False, True, True]  # the root is core


def test_possible_literals_on_a_restricted_root():
    _, bdd = _read_text(SMARTWATCH)
    restricted = bdd.bdd.let({bdd.features_vars['Camera']: True}, bdd.root)
    can_true, can_false = possible_literals(bdd, restricted)
    level = {v: i for i, v in enumerate(bdd.vars_order)}
    assert not can_false[level[bdd.features_vars['HighRes']]]
    assert not can_true[level[bdd.features_vars['Analog']]]
    # the restricted variable is skipped on every path: reported free
    assert can_true[level[bdd.features_vars['Camera']]]
    assert can_false[level[bdd.features_vars['Camera']]]
