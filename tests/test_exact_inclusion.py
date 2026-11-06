"""Core, dead, variant and pure-optional features are decided on exact inclusion probabilities.

On models with many configurations the float probability of a feature that is missing from a
tiny fraction of them rounds to 1.0, and that of a feature present in a tiny fraction underflows
to 0.0; deciding on the floats then reports false core or false dead features (seen on
uClinux-distribution, automotive02 and KubernetesFM_Boolean). The models below reproduce both.
"""
import os
import tempfile
from fractions import Fraction

import pytest

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.pysat_metamodel.operations import (
    PySATCoreFeatures,
    PySATDeadFeatures,
)
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDFeatureInclusionProbability,
    BDDMetrics,
    BDDPureOptionalFeatures,
    BDDVariantFeatures,
)
from flamapy.metamodels.bdd_metamodel.operations.bdd_feature_inclusion_probability import (
    exact_feature_inclusion,
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


def _fm(n_free, constraints):
    """Root with an optional F and n_free optional X0..Xn-1, plus the given constraints."""
    xs = '\n'.join(f'            X{i}' for i in range(n_free))
    ctcs = '\n'.join(f'    {c}' for c in ([constraints] if isinstance(constraints, str) else constraints))
    uvl = f'features\n    Root\n        optional\n            F\n{xs}\nconstraints\n{ctcs}\n'
    handle, path = tempfile.mkstemp(suffix='.uvl')
    try:
        with os.fdopen(handle, 'w') as file:
            file.write(uvl)
        return UVLReader(path).transform()
    finally:
        os.remove(path)


def _each(n, template):
    """One small constraint per Xi (a single n-ary conjunction is slow to parse)."""
    return [template.format(f'X{i}') for i in range(n)]


def test_almost_core_feature_is_not_core():
    # F is absent only when every Xi is selected: 1 configuration in 2^61 + 1.
    n = 60
    fm = _fm(n, _each(n, '!F => {}'))
    bdd = FmToBDD(fm).transform()
    prob = exact_feature_inclusion(bdd)['F']
    assert prob != 1 and float(prob) == 1.0  # the float rounds: the case being tested
    assert 'F' not in BDDCoreFeatures().execute(bdd).get_result()
    assert 'F' in BDDVariantFeatures().execute(bdd).get_result()
    sat = FmToPysat(fm).transform()
    assert sorted(BDDCoreFeatures().execute(bdd).get_result()) == \
        sorted(PySATCoreFeatures().execute(sat).get_result())


def test_almost_dead_feature_is_not_dead():
    # F is selected only when every Xi is: 1 configuration in 2^1100 + 1, below the
    # smallest float, so the float probability underflows to 0.0.
    n = 1100
    fm = _fm(n, _each(n, 'F => {}'))
    bdd = FmToBDD(fm).transform()
    prob = exact_feature_inclusion(bdd)['F']
    assert prob != 0 and float(prob) == 0.0  # the float underflows: the case being tested
    assert 'F' not in BDDDeadFeatures().execute(bdd).get_result()
    assert 'F' in BDDVariantFeatures().execute(bdd).get_result()
    sat = FmToPysat(fm).transform()
    assert sorted(BDDDeadFeatures().execute(bdd).get_result()) == \
        sorted(PySATDeadFeatures().execute(sat).get_result())


def test_metrics_use_the_exact_probabilities():
    n = 60
    fm = _fm(n, _each(n, '!F => {}'))
    bdd = FmToBDD(fm).transform()
    operation = BDDMetrics()
    operation.only_these_metrics(['core_features', 'dead_features'])
    metrics = {m['name']: m['result'] for m in operation.calculate_metamodel_metrics(bdd)}
    assert 'F' not in metrics['Core features']
    assert 'F' not in metrics['Dead features']


def test_pure_optional_is_exactly_one_half():
    fm = _fm(3, 'X0 => X1')
    bdd = FmToBDD(fm).transform()
    probs = exact_feature_inclusion(bdd)
    assert probs['F'] == Fraction(1, 2) and probs['X2'] == Fraction(1, 2)
    assert probs['X0'] != Fraction(1, 2)
    assert set(BDDPureOptionalFeatures().execute(bdd).get_result()) == {'F', 'X2'}


def test_inclusion_probability_still_returns_floats():
    fm = _fm(3, 'X0 => X1')
    bdd = FmToBDD(fm).transform()
    result = BDDFeatureInclusionProbability().execute(bdd).get_result()
    assert all(isinstance(p, float) for p in result.values())
    assert result['Root'] == 1.0 and result['F'] == 0.5
    assert result == {f: float(p) for f, p in exact_feature_inclusion(bdd).items()}


@pytest.mark.parametrize('builder', ['python', 'native'])
def test_builders_agree_on_the_exact_probabilities(builder):
    if builder == 'native':
        pytest.importorskip('flamapy_cudd')
    n = 60
    fm = _fm(n, _each(n, '!F => {}'))
    bdd = FmToBDD(fm, builder=builder).transform()
    assert 'F' not in BDDCoreFeatures().execute(bdd).get_result()
