# flamapy-bdd

BDD-based analysis for [flamapy](https://flamapy.org) feature models, built on
the [dd](https://github.com/tulip-control/dd) library.

**Documentation:** https://docs.flamapy.org/framework/plugins/bdd_plugin

## Installation

```bash
pip install flamapy-bdd
pip install flamapy-bdd[fast]   # optional: native builder for large models (see below)
```

`pip install dd` provides dd's pure-Python engine. For larger models, build dd against
[CUDD](https://github.com/ivmai/cudd), which is much faster and enables dynamic variable
reordering:

```bash
pip install cython
DD_FETCH=1 DD_CUDD=1 pip install --force-reinstall --no-deps --no-build-isolation --no-binary dd "dd==0.6.0"
```

## How the BDD is built

With the `fast` extra, `FmToBDD` builds the BDD natively with **Logic2BDD** on CUDD
(David Fernández-Amorós, UNED; package [flamapy-cudd](https://github.com/flamapy/cudd_native))
and loads it into the `dd` engine in use. That handles models with over a thousand features
(see `benchmarks/`).

Without it, `FmToBDD` conjoins the clauses of the feature model one at a time over a static
variable order inspired by Logic2BDD. With the CUDD engine it also reorders variables
dynamically while building. Every option can be passed to `FmToBDD(...)` or set with an
environment variable; explicit arguments take precedence.

| Option | Environment variable | Values (default first) |
|--------|----------------------|------------------------|
| `builder` | `FLAMAPY_BDD_BUILDER` | `auto` (native when installed), `native`, `python` |
| `build` | `FLAMAPY_BDD_BUILD` | `incremental`, `monolithic` (the whole formula at once) |
| `var_order` | `FLAMAPY_BDD_VAR_ORDER` | `tree` (feature-tree pre-order), `force` (FORCE heuristic), `model` |
| `clause_order` | `FLAMAPY_BDD_CLAUSE_ORDER` | `minspan`, `minmax`, `model` |
| `reorder` | `FLAMAPY_BDD_REORDER` | `auto` (on with CUDD, off otherwise), `1`, `0` |

The options only change how the BDD is built, never the configurations it represents. See
`flamapy/metamodels/bdd_metamodel/models/utils/ordering.py` and `benchmarks/`.
