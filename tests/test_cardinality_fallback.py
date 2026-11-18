"""Relations outside the standard shapes still need cardinality constraints."""

import pytest

from flamapy.metamodels.fm_metamodel.models import Feature, FeatureModel, Relation
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel
from flamapy.metamodels.bdd_metamodel.models.utils.logic2bdd_writer import (
    feature_model_to_logic2bdd,
)
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDConfigurationsNumber,
    BDDDeadFeatures,
    BDDSatisfiable,
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


def _model(card_min: int, card_max: int, children: int = 1,
           optional_parent: bool = False) -> FeatureModel:
    root = Feature("Root")
    parent = root
    if optional_parent:
        parent = Feature("Parent", parent=root)
        root.add_relation(Relation(root, [parent], 0, 1))
    members = [Feature(f"F{i}", parent=parent) for i in range(children)]
    parent.add_relation(Relation(parent, members, card_min, card_max))
    return FeatureModel(root)


@pytest.mark.parametrize("card_min,card_max,children,expected", [
    (0, 0, 1, 1),  # Reported [0..0] case.
    (0, 1, 1, 2),  # Standard optional relation.
    (1, 1, 1, 1),  # Standard mandatory relation.
    (1, 2, 1, 1),  # Upper bound above child count.
    (2, 2, 1, 0),  # Impossible lower bound: the model is void.
    (0, 3, 1, 2),  # Extra upper range must not cause an error.
    (0, -1, 1, 2),  # Internal unbounded upper-bound sentinel.
    (0, 0, 2, 1),  # Ordinary two-child cardinality group.
    (0, 0, 0, 1),  # Empty, vacuous relation.
    (1, 1, 0, 0),  # Empty, impossible relation.
])
@pytest.mark.parametrize("build", ["incremental", "monolithic"])
def test_cardinality_counts(card_min, card_max, children, expected, build):
    fm = _model(card_min, card_max, children)
    bdd = FmToBDD(fm, builder="python", build=build).transform()
    assert BDDConfigurationsNumber().execute(bdd).get_result() == expected
    assert BDDSatisfiable().execute(bdd).get_result() == (expected > 0)


def test_unary_zero_group_under_optional_parent() -> None:
    fm = _model(0, 0, optional_parent=True)
    pl_model = PLModel()
    pl_model.build_from_feature_model(fm)
    assert [clause.kind for clause in pl_model.clauses] == [
        "root", "optional", "cardinality",
    ]
    bdd = FmToBDD(fm, builder="python").transform()
    assert BDDConfigurationsNumber().execute(bdd).get_result() == 2
    assert BDDDeadFeatures().execute(bdd).get_result() == ["F0"]


@pytest.mark.parametrize("card_min,card_max", [(0, 0), (0, 3), (2, 2)])
def test_native_writer_keeps_nonstandard_unary_relation(card_min, card_max) -> None:
    fm = _model(card_min, card_max)
    encoded = feature_model_to_logic2bdd(fm, ["Root", "F0"])
    assert encoded.expressions[0] == "v0"
    assert any("v1" in line for line in encoded.expressions[1:])
    assert all(encoded.expressions)


def test_native_writer_handles_empty_relation() -> None:
    assert feature_model_to_logic2bdd(_model(0, 0, children=0), ["Root"]).expressions == [
        "v0",
    ]
    assert feature_model_to_logic2bdd(_model(1, 1, children=0), ["Root"]).expressions == [
        "v0", "(not v0)",
    ]
