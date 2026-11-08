"""The build options of FmToBDD (variable order, clause schedule, reordering) change how the
BDD is built, never what it represents."""
import json
import os
import subprocess
import sys

import pytest

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel
from flamapy.metamodels.bdd_metamodel.models.utils.ordering import (
    clause_order,
    force_order,
    total_span,
    variable_order,
)
from flamapy.metamodels.bdd_metamodel.models.utils.pl_model import PLClause
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDConfigurationsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


MODELS = [
    "resources/models/uvl_models/MobilePhone.uvl",
    "resources/models/uvl_models/JHipster.uvl",
    "resources/models/uvl_models/Pizzas.uvl",
    "resources/models/uvl_models/Pizzas_complex.uvl",
    "resources/models/uvl_models/Truck.uvl",
    "resources/models/uvl_models/group_cardinalities.uvl",
    "resources/models/uvl_models/mutex.uvl",
    "resources/models/uvl_models/Trimesh_NFM.uvl",
]

STRATEGIES = [
    {"build": "monolithic", "var_order": "tree"},
    {"build": "monolithic", "var_order": "force"},
    {"build": "incremental", "var_order": "model", "clause_order": "model", "reorder": False},
    {"build": "incremental", "var_order": "tree", "clause_order": "minspan", "reorder": False},
    {"build": "incremental", "var_order": "tree", "clause_order": "minmax", "reorder": False},
    {"build": "incremental", "var_order": "force", "clause_order": "minspan", "reorder": False},
    {"build": "incremental", "var_order": "tree", "clause_order": "minspan", "reorder": True},
    {"build": "incremental", "var_order": "force", "clause_order": "minmax", "reorder": True},
]


try:
    import flamapy_cudd  # noqa: F401  pylint: disable=unused-import
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


def _summary(path: str, **options):
    options.setdefault("builder", "python")
    feature_model = UVLReader(path).transform()
    bdd_model = FmToBDD(feature_model, **options).transform()
    levels = [bdd_model.bdd.level_of_var(var) for var in bdd_model.vars_order]
    assert levels == list(range(len(levels))), "vars_order must follow the BDD levels"
    count = BDDConfigurationsNumber().execute(bdd_model).get_result()
    core = sorted(BDDCoreFeatures().execute(bdd_model).get_result())
    dead = sorted(BDDDeadFeatures().execute(bdd_model).get_result())
    return count, core, dead


@pytest.mark.parametrize("path", MODELS)
def test_strategies_build_equivalent_bdds(path):
    reference = _summary(path, build="monolithic", var_order="model")
    for options in STRATEGIES:
        assert _summary(path, **options) == reference, options


@pytest.mark.skipif(not HAS_NATIVE, reason="needs the experimental flamapy-cudd package")
@pytest.mark.parametrize("path", MODELS)
def test_native_builder_is_equivalent(path):
    reference = _summary(path, build="monolithic", var_order="model")
    assert _summary(path, builder="native") == reference
    assert _summary(path, builder="native", var_order="force") == reference


def test_builder_option(monkeypatch):
    feature_model = UVLReader("resources/models/uvl_models/Pizzas.uvl").transform()
    assert FmToBDD(feature_model, builder="python").cache_options()["builder"] == "python"
    assert FmToBDD(feature_model).cache_options()["builder"] == "python"
    monkeypatch.setenv("FLAMAPY_BDD_BUILDER", "python")
    assert FmToBDD(feature_model).cache_options()["builder"] == "python"
    with pytest.raises(ValueError):
        FmToBDD(feature_model, builder="unknown")
    if not HAS_NATIVE:
        with pytest.raises(ValueError):
            FmToBDD(feature_model, builder="native")


def test_tree_order_is_preorder():
    feature_model = UVLReader("resources/models/uvl_models/Pizzas.uvl").transform()
    pl_model = PLModel()
    pl_model.build_from_feature_model(feature_model)
    order = pl_model.variables
    assert order[0] == feature_model.root.name
    assert sorted(order) == sorted(f.name for f in feature_model.get_features())
    # Every feature comes right after its parent or after a subtree of an earlier sibling.
    position = {name: i for i, name in enumerate(order)}
    for feature in feature_model.get_features():
        if feature.get_parent() is not None:
            assert position[feature.get_parent().name] < position[feature.name]


def test_clauses_cover_the_formula():
    feature_model = UVLReader("resources/models/uvl_models/Truck.uvl").transform()
    pl_model = PLModel()
    formula = pl_model.build_from_feature_model(feature_model)
    assert formula == " & ".join(f"({clause.formula})" for clause in pl_model.clauses)
    kinds = {clause.kind for clause in pl_model.clauses}
    assert "root" in kinds and "constraint" in kinds
    variables = set(pl_model.variables)
    for clause in pl_model.clauses:
        assert set(clause.support) <= variables


def test_force_never_increases_the_span():
    clauses = [PLClause("c", "", support) for support in
               [("a", "z"), ("b", "y"), ("a", "b"), ("y", "z"), ("m", "n")]]
    initial = ["a", "b", "m", "n", "y", "z"]
    supports = [clause.support for clause in clauses]
    order = force_order(initial, supports)
    assert sorted(order) == sorted(initial)
    assert total_span(order, supports) <= total_span(initial, supports)
    assert variable_order(initial, clauses, "force") == order


def test_clause_orders():
    order = ["a", "b", "c", "d"]
    wide = PLClause("c", "a | d", ("a", "d"))
    low = PLClause("c", "c | d", ("c", "d"))
    high = PLClause("c", "a | b", ("a", "b"))
    clauses = [wide, low, high]
    assert clause_order(clauses, order, "model") == clauses
    assert clause_order(clauses, order, "minspan") == [high, low, wide]
    assert clause_order(clauses, order, "minmax") == [high, wide, low]
    with pytest.raises(ValueError):
        clause_order(clauses, order, "unknown")


def test_invalid_options_are_rejected(monkeypatch):
    feature_model = UVLReader("resources/models/uvl_models/Pizzas.uvl").transform()
    with pytest.raises(ValueError):
        FmToBDD(feature_model, build="unknown")
    monkeypatch.setenv("FLAMAPY_BDD_VAR_ORDER", "unknown")
    with pytest.raises(ValueError):
        FmToBDD(feature_model)


def test_options_from_environment(monkeypatch):
    feature_model = UVLReader("resources/models/uvl_models/Pizzas.uvl").transform()
    monkeypatch.setenv("FLAMAPY_BDD_BUILDER", "python")
    monkeypatch.setenv("FLAMAPY_BDD_VAR_ORDER", "force")
    monkeypatch.setenv("FLAMAPY_BDD_CLAUSE_ORDER", "minmax")
    monkeypatch.setenv("FLAMAPY_BDD_REORDER", "0")
    transformation = FmToBDD(feature_model)
    assert transformation.cache_options()["var_order"] == "force"
    assert transformation.cache_options()["clause_order"] == "minmax"
    assert transformation.cache_options()["reorder"] is False
    # Explicit arguments win over the environment.
    assert FmToBDD(feature_model, var_order="tree").cache_options()["var_order"] == "tree"
    assert FmToBDD(feature_model, builder="native" if HAS_NATIVE else "python") \
        .cache_options()["builder"] == ("native" if HAS_NATIVE else "python")


_ORDER_SCRIPT = """
import json
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel
from flamapy.metamodels.bdd_metamodel.models.utils.ordering import variable_order, clause_order
fm = UVLReader("resources/models/uvl_models/JHipster.uvl").transform()
pl = PLModel()
formula = pl.build_from_feature_model(fm)
order = variable_order(pl.variables, pl.clauses, "force")
schedule = [c.formula for c in clause_order(pl.clauses, order, "minspan")]
print(json.dumps([formula, order, schedule]))
"""


def test_orders_do_not_depend_on_hash_seed():
    outputs = []
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        proc = subprocess.run([sys.executable, "-c", _ORDER_SCRIPT], env=env, check=True,
                              capture_output=True, text=True)
        outputs.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("path", MODELS)
def test_exact_count_matches_enumeration(path):
    # pylint: disable=import-outside-toplevel
    from flamapy.metamodels.bdd_metamodel.models.bdd_model import exact_count

    feature_model = UVLReader(path).transform()
    model = FmToBDD(feature_model, builder="python").transform()
    bdd, n_vars = model.bdd, len(model.vars_order)
    expected = sum(1 for _ in bdd.pick_iter(model.root, care_vars=set(model.vars_order)))
    assert exact_count(bdd, model.root, n_vars) == expected
    assert exact_count(bdd, ~model.root, n_vars) == 2 ** n_vars - expected
    assert exact_count(bdd, model.root, n_vars + 3) == expected * 8
    first = model.vars_order[len(model.vars_order) // 2]
    restricted = bdd.let({first: True}, model.root)
    expected_restricted = sum(1 for _ in bdd.pick_iter(
        restricted, care_vars=set(model.vars_order) - {first}))
    assert exact_count(bdd, restricted, n_vars - 1) == expected_restricted
