"""DDDMP files load with any dd engine and represent the same set of configurations."""
import os
import tempfile

import pytest

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models.bdd_model import DD_BACKEND
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDConfigurationsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
)
from flamapy.metamodels.bdd_metamodel.transformations import DDDMPReader, FmToBDD
from flamapy.metamodels.bdd_metamodel.transformations.dddmp_reader import (
    dddmp_v3_to_v2,
    load_dddmp,
)


def _count(path: str) -> int:
    if path.endswith(".uvl"):
        model = FmToBDD(UVLReader(path).transform()).transform()
    else:
        model = DDDMPReader(path).transform()
    return BDDConfigurationsNumber().execute(model).get_result()


@pytest.mark.parametrize(
    "dddmp_path, uvl_path",
    [
        ("resources/models/bdd_models/Pizzas.dddmp", "resources/models/uvl_models/Pizzas.uvl"),
        ("resources/models/bdd_models/Pizzas_uned.dddmp",
         "resources/models/uvl_models/Pizzas.uvl"),
        ("resources/models/bdd_models/MobilePhone.dddmp",
         "resources/models/uvl_models/MobilePhone.uvl"),
    ],
)
def test_dddmp_fixture_matches_uvl(dddmp_path, uvl_path):
    assert _count(dddmp_path) == _count(uvl_path)


@pytest.mark.parametrize("path", ["resources/models/bdd_models/Pizzas.dddmp",
                                  "resources/models/bdd_models/Pizzas_uned.dddmp"])
def test_python_loader_keeps_file_levels(path):
    model = load_dddmp(path)
    with open(path, encoding="utf8") as file:
        ordered = next(line for line in file if line.startswith(".orderedvarnames")).split()[1:]
    assert model.vars_order == ordered


def test_v3_without_varnames_converts(tmp_path):
    source = tmp_path / "no_varnames.dddmp"
    with open("resources/models/bdd_models/Pizzas.dddmp", encoding="utf8") as file:
        lines = [line for line in file if not line.startswith(".varnames")]
    source.write_text("".join(lines), encoding="utf8")
    converted = dddmp_v3_to_v2(str(source))
    try:
        with open(converted, encoding="utf8") as file:
            assert ".ver DDDMP-2.0" in file.read()
    finally:
        os.unlink(converted)


@pytest.mark.skipif(DD_BACKEND != "cudd", reason="writing DDDMP needs dd built with CUDD")
@pytest.mark.parametrize("uvl_path", ["resources/models/uvl_models/JHipster.uvl",
                                      "resources/models/uvl_models/Truck.uvl",
                                      "resources/models/uvl_models/Trimesh_NFM.uvl"])
def test_python_loader_reads_cudd_dumps(uvl_path):
    # pylint: disable=import-outside-toplevel
    from flamapy.metamodels.bdd_metamodel.transformations import DDDMPWriter

    feature_model = UVLReader(uvl_path).transform()
    # Dynamic reordering leaves levels that differ from the declaration order.
    model = FmToBDD(feature_model, builder="python", reorder=True).transform()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "model.dddmp")
        DDDMPWriter(path, model).transform()
        loaded = load_dddmp(path)
    assert loaded.vars_order == model.vars_order
    for operation in (BDDConfigurationsNumber, BDDCoreFeatures, BDDDeadFeatures):
        expected = operation().execute(model).get_result()
        result = operation().execute(loaded).get_result()
        if isinstance(expected, list):
            expected, result = sorted(expected), sorted(result)
        assert result == expected
