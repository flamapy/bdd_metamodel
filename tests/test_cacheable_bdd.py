import pytest

from flamapy.core.discover import DiscoverMetamodels
from flamapy.metamodels.bdd_metamodel.operations import BDDConfigurationsNumber

MODEL = 'resources/models/uvl_models/Pizzas.uvl'


def _count(model) -> int:
    operation = BDDConfigurationsNumber()
    operation.execute(model)
    return operation.get_result()


@pytest.fixture(name='cache_dir')
def _cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv('FLAMAPY_CACHE', '1')
    monkeypatch.setenv('FLAMAPY_CACHE_DIR', str(tmp_path / 'cache'))
    return tmp_path / 'cache'


def test_bdd_cache_round_trip(cache_dir):
    dm = DiscoverMetamodels()
    fm_model = dm.use_transformation_t2m(MODEL, 'fm')

    first = dm.use_transformation_m2m(fm_model, 'bdd')
    assert not getattr(first, '_flamapy_cache_hit', False)
    assert any(cache_dir.glob('*-bdd-*.dddmp'))

    second = dm.use_transformation_m2m(fm_model, 'bdd')
    assert getattr(second, '_flamapy_cache_hit', False)
    assert _count(second) == _count(first)


def test_bdd_cache_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv('FLAMAPY_CACHE', raising=False)
    monkeypatch.setenv('FLAMAPY_CACHE_DIR', str(tmp_path / 'cache'))
    dm = DiscoverMetamodels()
    fm_model = dm.use_transformation_t2m(MODEL, 'fm')
    model = dm.use_transformation_m2m(fm_model, 'bdd')
    assert not getattr(model, '_flamapy_cache_hit', False)
    assert not (tmp_path / 'cache').exists()
