"""Static variable orders and clause schedules for building a BDD clause by clause.

The size of a BDD depends heavily on the variable order, and the cost of building it
clause by clause depends on the order in which clauses are conjoined. These heuristics follow
the ideas of Logic2BDD (D. Fernández-Amorós, R. Heradio et al.) adapted to feature models:

Variable orders
    ``model``  the order of `FeatureModel.get_features()`.
    ``tree``   depth-first pre-order of the feature tree (a feature followed by its subtree).
    ``force``  the FORCE hypergraph heuristic (Aloul, Markov and Sakallah, 2003), seeded with
               the tree order: variables that share clauses are pulled together, which shortens
               the span of cross-tree constraints.

Clause schedules
    ``model``    the order in which the clauses were generated.
    ``minspan``  clauses with a smaller span (distance between their first and last variable
                 in the order) first; ties broken by the position of their first variable.
    ``minmax``   clauses whose deepest variable is higher in the order first.

All functions are pure and deterministic: the same inputs always give the same result.
"""
from typing import Sequence

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.bdd_metamodel.models.utils.pl_model import PLClause


class BDDOptionError(FlamaException, ValueError):
    """An invalid BDD build option (argument or FLAMAPY_BDD_* variable). A FlamaException like
    every other invalid transformation option; also a ValueError, as it was before 2.9."""


VARIABLE_ORDERS = ("model", "tree", "force")
CLAUSE_ORDERS = ("model", "minspan", "minmax")

FORCE_MAX_ITERATIONS = 50


def variable_order(variables: Sequence[str],
                   clauses: Sequence[PLClause],
                   strategy: str = "tree",
                   model_order: Sequence[str] = ()) -> list[str]:
    """Return the variables in the order given by `strategy`.

    `variables` must be in feature-tree pre-order (as `PLModel.variables`); `model_order` is
    only used by the ``model`` strategy.
    """
    if strategy == "tree":
        return list(variables)
    if strategy == "model":
        ordered = [var for var in model_order if var in set(variables)]
        seen = set(ordered)
        return ordered + [var for var in variables if var not in seen]
    if strategy == "force":
        return force_order(variables, [clause.support for clause in clauses])
    raise BDDOptionError(f"Unknown variable order '{strategy}'. Use one of {VARIABLE_ORDERS}.")


def total_span(order: Sequence[str], supports: Sequence[Sequence[str]]) -> int:
    """Sum over the clauses of the distance between their first and last variable."""
    position = {var: index for index, var in enumerate(order)}
    span = 0
    for support in supports:
        levels = [position[var] for var in support if var in position]
        if len(levels) > 1:
            span += max(levels) - min(levels)
    return span


def force_order(initial: Sequence[str], supports: Sequence[Sequence[str]]) -> list[str]:
    """FORCE: move every variable to the mean centre of gravity of its clauses, repeat.

    Each iteration computes the centre of gravity of every clause (the mean position of its
    variables), places every variable at the mean of the centres of the clauses it belongs
    to, and re-sorts. The best order found (smallest total span) is returned; ties keep the
    previous position, so the result is deterministic.
    """
    order = list(initial)
    edges = [tuple(dict.fromkeys(var for var in support if var in set(order)))
             for support in supports]
    edges = [edge for edge in edges if len(edge) > 1]
    if not edges:
        return order
    var_edges: dict[str, list[int]] = {var: [] for var in order}
    for index, edge in enumerate(edges):
        for var in edge:
            var_edges[var].append(index)

    best_order = order
    best_span = total_span(order, edges)
    for _ in range(FORCE_MAX_ITERATIONS):
        position = {var: index for index, var in enumerate(order)}
        centres = [sum(position[var] for var in edge) / len(edge) for edge in edges]
        target = {
            var: (sum(centres[i] for i in var_edges[var]) / len(var_edges[var])
                  if var_edges[var] else float(position[var]))
            for var in order
        }
        order = sorted(order, key=lambda var: (target[var], position[var]))
        span = total_span(order, edges)
        if span >= best_span:
            break
        best_order, best_span = order, span
    return best_order


def clause_order(clauses: Sequence[PLClause],
                 order: Sequence[str],
                 strategy: str = "minspan") -> list[PLClause]:
    """Return the clauses in the order given by `strategy` for the variable order `order`."""
    if strategy == "model":
        return list(clauses)
    position = {var: index for index, var in enumerate(order)}

    def bounds(clause: PLClause) -> tuple[int, int]:
        levels = [position[var] for var in clause.support if var in position] or [0]
        return min(levels), max(levels)

    indexed = list(enumerate(clauses))
    if strategy == "minspan":
        def span_key(item: tuple[int, PLClause]) -> tuple[int, int, int]:
            low, high = bounds(item[1])
            return (high - low, low, item[0])
        return [clause for _, clause in sorted(indexed, key=span_key)]
    if strategy == "minmax":
        def max_key(item: tuple[int, PLClause]) -> tuple[int, int, int]:
            low, high = bounds(item[1])
            return (high, low, item[0])
        return [clause for _, clause in sorted(indexed, key=max_key)]
    raise BDDOptionError(f"Unknown clause order '{strategy}'. Use one of {CLAUSE_ORDERS}.")
