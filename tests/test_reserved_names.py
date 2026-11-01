"""Feature names that collide with operator words or with dd's reserved identifiers."""
import pytest

from flamapy.core.models.ast import AST, ASTOperation, Node
from flamapy.metamodels.fm_metamodel.models import Constraint, Feature, FeatureModel, Relation

from flamapy.metamodels.bdd_metamodel.operations import (
    BDDConfigurationsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
)
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


def _model(names: list[str], ctcs: list[AST]) -> FeatureModel:
    """Root with an optional-children group [0..n] over `names`, plus the given constraints."""
    root = Feature('Root')
    children = [Feature(n, parent=root) for n in names]
    root.add_relation(Relation(root, children, 0, len(children)))
    return FeatureModel(root, [Constraint(f'c{i}', ast) for i, ast in enumerate(ctcs)])


def _count(fm: FeatureModel) -> int:
    return BDDConfigurationsNumber().execute(FmToBDD(fm).transform()).get_result()


@pytest.mark.parametrize('name', ['True', 'False', 'TRUE', 'FALSE', 'ite'])
def test_dd_reserved_name_is_a_variable(name: str) -> None:
    # Two optional features, one of them forbidden: 2 configurations.
    fm = _model([name, 'x'], [AST.create_simple_unary_operation(ASTOperation.NOT, name)])
    assert _count(fm) == 2
    bdd = FmToBDD(fm).transform()
    assert BDDDeadFeatures().execute(bdd).get_result() == [name]


@pytest.mark.parametrize('name', ['AND', 'OR', 'NOT', 'XOR', 'IMPLIES', 'EQUIVALENCE', 'REQUIRES', 'EXCLUDES'])
def test_operator_word_as_feature_name(name: str) -> None:
    # name and y cannot both be selected: 3 configurations.
    fm = _model([name, 'y'], [AST.create_unary_operation(
        ASTOperation.NOT, Node(ASTOperation.AND, Node(name), Node('y')))])
    assert _count(fm) == 3


def test_reserved_name_suffix_does_not_clash() -> None:
    # 'True_1' already exists, so the renamed 'True' must not reuse it.
    fm = _model(['True', 'True_1'], [AST.create_simple_binary_operation(ASTOperation.REQUIRES, 'True', 'True_1')])
    assert _count(fm) == 3
    bdd = FmToBDD(fm).transform()
    assert sorted(BDDCoreFeatures().execute(bdd).get_result()) == ['Root']


def test_excludes_and_xor_are_serialized_correctly() -> None:
    excludes = _model(['a', 'b'], [AST.create_simple_binary_operation(ASTOperation.EXCLUDES, 'a', 'b')])
    assert _count(excludes) == 3
    xor = _model(['a', 'b'], [AST.create_simple_binary_operation(ASTOperation.XOR, 'a', 'b')])
    assert _count(xor) == 2
