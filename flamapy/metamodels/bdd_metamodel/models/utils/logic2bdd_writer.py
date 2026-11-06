"""Write a feature model as Logic2BDD input (a variable file and an expression file).

Logic2BDD (D. Fernández-Amorós, UNED) reads the variables, one order, from the variable file
and one constraint per line from the expression file. Its grammar has some traps that this
writer avoids:

* `<->` binds tighter than `and`/`or`, so every binary operation is written in parentheses.
* Operators must be separated by spaces (`a->b` would be read as one symbol).
* `and`, `or`, `not`, `xor`, `mux`, `if`... are keywords, so variables are written with
  neutral names (`v0`, `v1`, ...) and the mapping to the real names is returned.
* Every line, the last one included, ends with a newline and there are no blank lines.

Groups use Logic2BDD's n-ary operators: `mux(...)` (at most one) for alternative and mutex
groups, which CUDD builds directly instead of from pairwise clauses.
"""
import itertools
from dataclasses import dataclass, field

from flamapy.core.models.ast import ASTOperation, Node
from flamapy.metamodels.fm_metamodel.models import Constraint, FeatureModel, Relation


@dataclass
class Logic2BDDInput:
    """Logic2BDD input files and the mapping between their names and the variables."""
    variables: list[str]                     # variable names (the model's), in order
    names: dict[str, str]                    # Logic2BDD name -> variable name
    expressions: list[str] = field(default_factory=list)

    @property
    def var_text(self) -> str:
        to_l2b = {var: name for name, var in self.names.items()}
        return " ".join(to_l2b[var] for var in self.variables) + "\n"

    @property
    def exp_text(self) -> str:
        return "".join(f"{line}\n" for line in self.expressions)


def feature_model_to_logic2bdd(feature_model: FeatureModel,
                               order: list[str]) -> Logic2BDDInput:
    """Translate `feature_model` (with sanitized names) using the variable order `order`."""
    names = {f"v{index}": var for index, var in enumerate(order)}
    to_l2b = {var: name for name, var in names.items()}
    result = Logic2BDDInput(variables=list(order), names=names)
    if feature_model.root is None:
        return result
    result.expressions.append(to_l2b[feature_model.root.name])
    for feature in feature_model.get_features():
        for relation in feature.get_relations():
            result.expressions.extend(_relation_lines(relation, to_l2b))
    for constraint in feature_model.get_logical_constraints():
        result.expressions.append(_constraint_line(constraint, to_l2b))
    return result


def _or(items: list[str]) -> str:
    return items[0] if len(items) == 1 else "(" + " or ".join(items) + ")"


def _relation_lines(relation: Relation, to_l2b: dict[str, str]) -> list[str]:
    parent = to_l2b[relation.parent.name]
    children = list(dict.fromkeys(to_l2b[child.name] for child in relation.children))
    at_most_one = [f"mux({', '.join(children)})"] if len(children) > 1 else []
    lines: list[str] = []
    if relation.is_mandatory():
        lines = [f"({parent} <-> {children[0]})"]
    elif relation.is_optional():
        lines = [f"({children[0]} -> {parent})"]
    elif relation.is_or():
        lines = [f"({parent} <-> {_or(children)})"]
    elif relation.is_alternative():
        lines = [f"({parent} <-> {_or(children)})", *at_most_one]
    elif relation.is_mutex():
        lines = [*(f"({child} -> {parent})" for child in children), *at_most_one]
    elif relation.is_cardinal():
        lines = _cardinality_lines(parent, children, relation.card_min, relation.card_max)
    return lines


def _cardinality_lines(parent: str, children: list[str], card_min: int,
                       card_max: int) -> list[str]:
    """Same clauses as PLModel: forbid every selection outside [min, max] under the parent,
    and any selection without the parent."""
    card_max = len(children) if card_max == -1 else card_max
    lines = [f"({child} -> {parent})" for child in children]
    for size in range(len(children) + 1):
        if card_min <= size <= card_max:
            continue
        for selected in itertools.combinations(children, size):
            literals = [f"(not {parent})"]
            literals += [f"(not {child})" if child in selected else child for child in children]
            lines.append(_or(literals))
    return lines


_BINARY = {
    ASTOperation.AND: "and",
    ASTOperation.OR: "or",
    ASTOperation.IMPLIES: "->",
    ASTOperation.REQUIRES: "->",
    ASTOperation.EQUIVALENCE: "<->",
}


def _constraint_line(constraint: Constraint, to_l2b: dict[str, str]) -> str:
    return _node_text(constraint.ast.root, to_l2b)


def _node_text(node: Node, to_l2b: dict[str, str]) -> str:
    if not node.is_op():
        return to_l2b[str(node.data)]
    operation = node.data
    if operation == ASTOperation.NOT:
        return f"(not {_node_text(node.left, to_l2b)})"
    left = _node_text(node.left, to_l2b)
    right = _node_text(node.right, to_l2b)
    if operation == ASTOperation.EXCLUDES:
        return f"({left} -> (not {right}))"
    if operation == ASTOperation.XOR:
        return f"(({left} or {right}) and (not ({left} and {right})))"
    if operation in _BINARY:
        return f"({left} {_BINARY[operation]} {right})"
    raise ValueError(f"Operation {operation} is not supported by Logic2BDD.")
