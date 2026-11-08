# flamapy-bdd

BDD-based analysis for [flamapy](https://flamapy.org) feature models, built on
the [dd](https://github.com/tulip-control/dd) library.

**Documentation:** https://docs.flamapy.org/framework/plugins/bdd_plugin

## Installation

```bash
pip install flamapy-bdd
```

Which BDD engine you get depends on the platform. On Linux x86_64, dd installs from wheels
that already include [CUDD](https://github.com/ivmai/cudd), which is much faster and enables
dynamic variable reordering. On macOS, Windows and Pyodide, dd installs from source with its
pure-Python engine; to use CUDD there, build dd against it:

```bash
pip install cython
DD_FETCH=1 DD_CUDD=1 pip install --force-reinstall --no-deps --no-build-isolation --no-binary dd "dd==0.6.0"
```

## How the BDD is built

`FmToBDD` conjoins the clauses of the feature model one at a time over a static
variable order inspired by Logic2BDD. With the CUDD engine it also reorders variables
dynamically while building. Every option can be passed to `FmToBDD(...)` or set with an
environment variable; explicit arguments take precedence.

| Option | Environment variable | Values (default first) |
|--------|----------------------|------------------------|
| `builder` | `FLAMAPY_BDD_BUILDER` | `python`; `native` and `auto` are experimental and need a native package that is not released yet |
| `build` | `FLAMAPY_BDD_BUILD` | `incremental`, `monolithic` (the whole formula at once) |
| `var_order` | `FLAMAPY_BDD_VAR_ORDER` | `tree` (feature-tree pre-order), `force` (FORCE heuristic), `model` |
| `clause_order` | `FLAMAPY_BDD_CLAUSE_ORDER` | `minspan`, `minmax`, `model` |
| `reorder` | `FLAMAPY_BDD_REORDER` | `auto` (on with CUDD, off otherwise), `1`, `0` |

The options only change how the BDD is built, never the configurations it represents.

With dd's pure-Python engine, building and walking a BDD recurses once per variable, so the
plugin raises Python's recursion limit (to about 1,000 + 4 per variable) when it builds or loads
a BDD. The limit applies to the whole process and is not lowered afterwards, because the
operations on the BDD need it too; keep it in mind when flamapy-bdd runs inside a server or in
Pyodide. See
`flamapy/metamodels/bdd_metamodel/models/utils/ordering.py` and `benchmarks/`.
