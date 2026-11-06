"""Linear traversals of a BDD that answer literal questions without building new BDDs.

Every internal node of a reduced BDD represents a non-constant function, so every path from the
root to an internal node extends to a satisfying assignment, whatever the number of complemented
edges on the path. Only the edges into the terminal need that parity to know whether they reach
TRUE. The traversals below visit every reachable (node, parity) state once, in level order; a
variable skipped along an edge can take both values, and the skipped variables of an edge are a
contiguous range of levels, so their contribution is a difference-array or prefix-mask update.
Both traversals are O(|BDD|) node visits plus O(1) Python operations per edge.
"""
from typing import Any, Iterator, Optional

from flamapy.metamodels.bdd_metamodel.models import BDDModel

State = tuple[Any, int]  # (regular node, parity: number of complemented edges mod 2)
Edge = tuple[bool, Any, int, int]  # (sign, regular child or None for TRUE, parity, level)


def _regular(edge: Any) -> Any:
    return ~edge if edge.negated else edge


def _levels(bdd_model: BDDModel) -> dict[str, int]:
    return {var: level for level, var in enumerate(bdd_model.vars_order)}


def reachable_states(root: Any, level: dict[str, int]) -> list[State]:
    """The (node, parity) states reachable from `root`, parents before children.

    `root` must be a non-terminal node. States are ordered by level, which is a topological order
    because every edge goes to a strictly deeper level.
    """
    top = _regular(root)
    first: State = (top, 1 if root.negated else 0)
    states = {first}
    stack = [first]
    while stack:
        node, parity = stack.pop()
        for edge in (node.low, node.high):
            child = _regular(edge)
            if child.var is None:
                continue
            state = (child, parity ^ (1 if edge.negated else 0))
            if state not in states:
                states.add(state)
                stack.append(state)
    return sorted(states, key=lambda state: level[state[0].var])


def _satisfying_edges(state: State, level: dict[str, int], n_vars: int) -> Iterator[Edge]:
    """The edges out of a state that lie on a satisfying path: every edge into an internal node,
    and the edges into the terminal that reach TRUE (parity 0). The terminal has level n_vars."""
    node, parity = state
    for sign, edge in ((False, node.low), (True, node.high)):
        child = _regular(edge)
        child_parity = parity ^ (1 if edge.negated else 0)
        if child.var is None:
            if child_parity == 0:
                yield sign, None, 0, n_vars
        else:
            yield sign, child, child_parity, level[child.var]


def possible_literals(bdd_model: BDDModel,
                      root: Optional[Any] = None) -> tuple[list[bool], list[bool]]:
    """For each variable of `vars_order`, whether some model of `root` has it true / false.

    Dead variables are those that cannot be true, core variables those that cannot be false.
    `root` defaults to the model's root; a restricted root (`bdd.let`) works as well, in which
    case the restricted variables are reported free (both values), as any other skipped variable.
    """
    bdd = bdd_model.bdd
    if root is None:
        root = bdd_model.root
    level = _levels(bdd_model)
    n_vars = len(bdd_model.vars_order)
    if root == bdd.false:
        return [False] * n_vars, [False] * n_vars
    top = _regular(root)
    if top.var is None:  # a tautology: every variable is free
        return [True] * n_vars, [True] * n_vars
    can_true = [False] * n_vars
    can_false = [False] * n_vars
    skipped = [0] * (n_vars + 1)  # difference array over levels

    def skip(low: int, high: int) -> None:  # the levels strictly between are skipped
        if high - low > 1:
            skipped[low + 1] += 1
            skipped[high] -= 1

    skip(-1, level[top.var])  # the variables above the root, on every path
    for state in reachable_states(root, level):
        node_level = level[state[0].var]
        for sign, _child, _parity, child_level in _satisfying_edges(state, level, n_vars):
            (can_true if sign else can_false)[node_level] = True
            skip(node_level, child_level)
    count = 0
    for index in range(n_vars):
        count += skipped[index]
        if count > 0:
            can_true[index] = True
            can_false[index] = True
    return can_true, can_false


class _PairMasks:
    """Bitsets over the implication pairs (a, b), indexed by the level of a or of b."""

    def __init__(self, pairs: list[tuple[str, str]], level: dict[str, int], n_vars: int) -> None:
        self.ante_at = [0] * n_vars  # pairs whose antecedent is the variable at the level
        self.cons_at = [0] * n_vars  # pairs whose consequent is the variable at the level
        for index, (antecedent, consequent) in enumerate(pairs):
            self.ante_at[level[antecedent]] |= 1 << index
            self.cons_at[level[consequent]] |= 1 << index
        self._ante_prefix = [0] * (n_vars + 1)  # pairs whose antecedent is above the level
        self._cons_prefix = [0] * (n_vars + 1)
        for index in range(n_vars):
            self._ante_prefix[index + 1] = self._ante_prefix[index] | self.ante_at[index]
            self._cons_prefix[index + 1] = self._cons_prefix[index] | self.cons_at[index]

    def ante_between(self, low: int, high: int) -> int:
        return self._ante_prefix[high] & ~self._ante_prefix[low + 1]

    def cons_between(self, low: int, high: int) -> int:
        return self._cons_prefix[high] & ~self._cons_prefix[low + 1]

    def ante_at_node(self, node_level: int, sign: bool) -> int:
        """The antecedents decided true at the node (its high edge)."""
        return self.ante_at[node_level] if sign else 0

    def cons_at_node(self, node_level: int, sign: bool) -> int:
        """The consequents decided false at the node (its low edge)."""
        return 0 if sign else self.cons_at[node_level]


def _sets_above(states: list[State], masks: _PairMasks, level: dict[str, int],
                n_vars: int) -> tuple[dict[State, int], dict[State, int]]:
    """Per state: the antecedents 1-or-skipped and the consequents 0-or-skipped on some path
    from the root to the state (the state's own variable excluded)."""
    ante_above: dict[State, int] = dict.fromkeys(states, 0)
    cons_above: dict[State, int] = dict.fromkeys(states, 0)
    top_level = level[states[0][0].var]
    ante_above[states[0]] = masks.ante_between(-1, top_level)
    cons_above[states[0]] = masks.cons_between(-1, top_level)
    for state in states:
        node_level = level[state[0].var]
        for sign, child, child_parity, child_level in _satisfying_edges(state, level, n_vars):
            if child is None:
                continue
            child_state = (child, child_parity)
            ante_above[child_state] |= (ante_above[state] | masks.ante_at_node(node_level, sign)
                                        | masks.ante_between(node_level, child_level))
            cons_above[child_state] |= (cons_above[state] | masks.cons_at_node(node_level, sign)
                                        | masks.cons_between(node_level, child_level))
    return ante_above, cons_above


def _refuted_pairs(states: list[State], masks: _PairMasks, level: dict[str, int],
                   n_vars: int) -> int:
    """Bottom-up: per state, the antecedents 1-or-skipped and the consequents 0-or-skipped on
    some path from the state to TRUE (the state's own variable included); at every satisfying
    edge, the pairs refuted by combining a prefix above with a suffix below."""
    ante_above, cons_above = _sets_above(states, masks, level, n_vars)
    ante_below: dict[State, int] = {}
    cons_below: dict[State, int] = {}
    refuted = 0
    for state in reversed(states):
        node_level = level[state[0].var]
        ante_here = 0
        cons_here = 0
        for sign, child, child_parity, child_level in _satisfying_edges(state, level, n_vars):
            child_ante = ante_below[(child, child_parity)] if child is not None else 0
            child_cons = cons_below[(child, child_parity)] if child is not None else 0
            edge_ante = (child_ante | masks.ante_at_node(node_level, sign)
                         | masks.ante_between(node_level, child_level))
            edge_cons = (child_cons | masks.cons_at_node(node_level, sign)
                         | masks.cons_between(node_level, child_level))
            ante_here |= edge_ante
            cons_here |= edge_cons
            # antecedent decided above or at the node, consequent at or below along the edge
            refuted |= (ante_above[state] | masks.ante_at_node(node_level, sign)) & edge_cons
            # consequent decided above or at the node, antecedent at or below along the edge
            refuted |= (cons_above[state] | masks.cons_at_node(node_level, sign)) & edge_ante
        ante_below[state] = ante_here
        cons_below[state] = cons_here
    return refuted


def refuted_implications(bdd_model: BDDModel,
                         pairs: list[tuple[str, str]],
                         root: Optional[Any] = None) -> list[bool]:
    """For each pair (a, b) of variables, whether some model of `root` has a true and b false,
    i.e. whether the implication a -> b does NOT hold in the model.

    All pairs are answered in two traversals (one top-down, one bottom-up) with big-integer
    bitsets over the pairs: a pair is refuted iff some satisfying path has a = 1 (or skips a) and
    b = 0 (or skips b), and every prefix of a satisfying path up to a state combines with every
    suffix from that state (see the module docstring).
    """
    bdd = bdd_model.bdd
    if root is None:
        root = bdd_model.root
    if root == bdd.false:
        return [False] * len(pairs)  # every implication holds vacuously
    if _regular(root).var is None:
        return [True] * len(pairs)  # every assignment is a model
    level = _levels(bdd_model)
    n_vars = len(bdd_model.vars_order)
    masks = _PairMasks(pairs, level, n_vars)
    refuted = _refuted_pairs(reachable_states(root, level), masks, level, n_vars)
    return [bool((refuted >> index) & 1) for index in range(len(pairs))]
