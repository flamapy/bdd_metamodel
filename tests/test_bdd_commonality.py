"""Commonality of partial configurations on the BDD: the core operation, routed by the planner."""
import os
import tempfile

import pytest

from flamapy.core.discover import DiscoverMetamodels
from flamapy.core.operations import Commonality
from flamapy.core.planner import _implements
from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel import MANIFEST
from flamapy.metamodels.bdd_metamodel.operations import BDDCommonalityFactor, BDDConfigurations
from flamapy.metamodels.bdd_metamodel.operations.interfaces import CommonalityFactor
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


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
            Camera
            GPS
            Unreachable
constraints
    Camera => HighRes
    Unreachable => !Root
    GPS => Connector
'''

VOID = '''features
    Root
        mandatory
            A
        optional
            B
constraints
    A => B
    B => !A
'''


def _bdd(uvl):
    handle, path = tempfile.mkstemp(suffix='.uvl')
    try:
        with os.fdopen(handle, 'w') as file:
            file.write(uvl)
        return FmToBDD(UVLReader(path).transform()).transform()
    finally:
        os.remove(path)


def _commonality(bdd, elements):
    operation = BDDCommonalityFactor()
    operation.set_configuration(Configuration(elements))
    return operation.execute(bdd).get_commonality()


def _expected(configs, decided):
    return sum(1 for c in configs
               if all((name in c) == selected for name, selected in decided.items())) / len(configs)


def test_partial_configurations_against_the_listed_configurations():
    bdd = _bdd(SMARTWATCH)
    configs = [set(c) for c in BDDConfigurations().execute(bdd).get_result()]
    for decided in ({'Core': True}, {'Unreachable': True}, {'Camera': True}, {'Camera': False},
                    {'Camera': True, 'HighRes': False}, {'GPS': True, 'USB': False},
                    {'Analog': False, 'EInk': False}):
        assert _commonality(bdd, decided) == pytest.approx(_expected(configs, decided))
    assert _commonality(bdd, {'Core': True}) == 1.0
    assert _commonality(bdd, {'Unreachable': True}) == 0.0


def test_void_model_has_commonality_zero():
    assert _commonality(_bdd(VOID), {'A': True}) == 0.0


def test_implements_the_core_operation():
    operation = BDDCommonalityFactor()
    assert isinstance(operation, Commonality) and isinstance(operation, CommonalityFactor)
    assert BDDCommonalityFactor.facade is Commonality.facade
    assert Commonality.facade.name == 'commonality'
    assert MANIFEST.operations['commonality'].exact
    plugin = DiscoverMetamodels().plugins.get_plugin_by_extension('bdd')
    assert _implements(plugin, 'commonality')
    assert plugin.get_operation('Commonality').__class__ is BDDCommonalityFactor
