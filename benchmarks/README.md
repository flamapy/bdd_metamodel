# BDD compilation benchmark

`bench_compile.py` compiles each model of `models.txt` with `FmToBDD`, in its own process. A
model is stopped after 120 s (`timeout`) or above 6 GB of resident memory (`memout`). The
times include building the BDD and, for the native builder, loading it into the dd engine.
Every configuration that finished agrees on the number of configurations of every model.

Run on 2026-11-02, Apple M-series (macOS, arm64), Python 3.12, dd 0.6.0:

| Label | Code | dd engine | Builder |
|---|---|---|---|
| `baseline-autoref` / `baseline-cudd` | `develop` before this work (one big expression, variable order from a Python `set`, no reordering) | autoref / CUDD | dd |
| `python-autoref-v2` / `python-cudd-v2` | this branch, `builder="python"` (tree order, minspan clause schedule, threshold reordering with CUDD) | autoref / CUDD | dd |
| `native-autoref` / `native-cudd` | this branch, `builder="native"` (Logic2BDD on CUDD, `flamapy-cudd`) | autoref / CUDD | Logic2BDD |

`XSEngine.uvl` (1273 features, 886 constraints) is not compiled by any configuration, not even
the native one with Logic2BDD's default options.

## Compile time

| Model | Features/CTCs | baseline-autoref | baseline-cudd | python-autoref-v2 | python-cudd-v2 | native-autoref | native-cudd |
|---|---|---|---|---|---|---|---|
| Truck.uvl | 33/10 | 6 ms | 7 ms | 4 ms | 5 ms | 9 ms | 10 ms |
| Trimesh_NFM.uvl | 31/21 | 25 ms | 22 ms | 24 ms | 23 ms | 29 ms | 32 ms |
| miband8.uvl | 37/22 | 8 ms | 5 ms | 6 ms | 6 ms | 11 ms | 13 ms |
| CDI.uvl | 43/7 | 28 ms | 5 ms | 4 ms | 5 ms | 7 ms | 9 ms |
| JHipster.uvl | 45/13 | 22 ms | 6 ms | 6 ms | 6 ms | 14 ms | 17 ms |
| strategies.uvl | 57/12 | 316 ms | 43 ms | 6 ms | 6 ms | 12 ms | 15 ms |
| 30-1.uvl | 100/30 | 6.2 s | 7.4 s | 21 ms | 10 ms | 38 ms | 41 ms |
| dm_DissModel.csv.uvl | 116/0 | 214 ms | 50 ms | 232 ms | 53 ms | 29 ms | 30 ms |
| model_20200316_153170359.uvl | 124/7 | 10.2 s | 3.1 s | 18 ms | 11 ms | 19 ms | 21 ms |
| 30-1.uvl (2) | 200/60 | memout | memout | 154 ms | 40 ms | 297 ms | 308 ms |
| 2007-11-02_23-31-10.uvl | 475/511 | memout | memout | memout | 42.7 s | 230 ms | 233 ms |
| 1-1.uvl | 500/5 | memout | timeout | 160 ms | 131 ms | 224 ms | 220 ms |
| 1-1.uvl (2) | 1000/10 | memout | memout | 623 ms | 821 ms | 2.7 s | 2.7 s |
| busybox_simple.uvl | 1108/930 | memout | memout | memout | timeout | 2.8 s | 2.6 s |
| embtoolkit.uvl | 1179/323 | memout | memout | memout | 14.3 s | 1.4 s | 1.4 s |
| XSEngine.uvl |  | memout | timeout | memout | timeout | timeout | timeout |

## BDD size (nodes)

| Model | Features/CTCs | baseline-autoref | baseline-cudd | python-autoref-v2 | python-cudd-v2 | native-autoref | native-cudd |
|---|---|---|---|---|---|---|---|
| Truck.uvl | 33/10 | 353 | 479 | 99 | 99 | 73 | 73 |
| Trimesh_NFM.uvl | 31/21 | 227 | 212 | 65 | 65 | 45 | 45 |
| miband8.uvl | 37/22 | 253 | 218 | 188 | 188 | 84 | 84 |
| CDI.uvl | 43/7 | 2967 | 2128 | 74 | 74 | 65 | 65 |
| JHipster.uvl | 45/13 | 2150 | 783 | 215 | 215 | 154 | 154 |
| strategies.uvl | 57/12 | 29586 | 52265 | 822 | 822 | 169 | 169 |
| 30-1.uvl | 100/30 | 6727 | 11944 | 390 | 390 | 321 | 321 |
| dm_DissModel.csv.uvl | 116/0 | 654 | 853 | 331 | 331 | 240 | 240 |
| model_20200316_153170359.uvl | 124/7 | 75474 | 191614 | 263 | 263 | 184 | 184 |
| 30-1.uvl (2) | 200/60 | memout | memout | 6636 | 6636 | 1197 | 1197 |
| 2007-11-02_23-31-10.uvl | 475/511 | memout | memout | memout | 80199 | 2084 | 2084 |
| 1-1.uvl | 500/5 | memout | timeout | 5038 | 5038 | 3048 | 3048 |
| 1-1.uvl (2) | 1000/10 | memout | memout | 23204 | 23204 | 18648 | 18648 |
| busybox_simple.uvl | 1108/930 | memout | memout | memout | timeout | 70122 | 70122 |
| embtoolkit.uvl | 1179/323 | memout | memout | memout | 16193 | 3647 | 3647 |
| XSEngine.uvl |  | memout | timeout | memout | timeout | timeout | timeout |

## Peak resident memory

| Model | Features/CTCs | baseline-autoref | baseline-cudd | python-autoref-v2 | python-cudd-v2 | native-autoref | native-cudd |
|---|---|---|---|---|---|---|---|
| Truck.uvl | 33/10 | 45 MB | 63 MB | 45 MB | 61 MB | 86 MB | 94 MB |
| Trimesh_NFM.uvl | 31/21 | 52 MB | 67 MB | 51 MB | 68 MB | 94 MB | 103 MB |
| miband8.uvl | 37/22 | 46 MB | 61 MB | 46 MB | 61 MB | 86 MB | 95 MB |
| CDI.uvl | 43/7 | 53 MB | 61 MB | 44 MB | 61 MB | 86 MB | 94 MB |
| JHipster.uvl | 45/13 | 51 MB | 61 MB | 45 MB | 61 MB | 86 MB | 95 MB |
| strategies.uvl | 57/12 | 181 MB | 73 MB | 45 MB | 61 MB | 86 MB | 94 MB |
| 30-1.uvl | 100/30 | 1937 MB | 916 MB | 50 MB | 62 MB | 87 MB | 96 MB |
| dm_DissModel.csv.uvl | 116/0 | 135 MB | 65 MB | 168 MB | 66 MB | 87 MB | 96 MB |
| model_20200316_153170359.uvl | 124/7 | 2993 MB | 709 MB | 48 MB | 62 MB | 87 MB | 96 MB |
| 30-1.uvl (2) | 200/60 | memout | memout | 110 MB | 66 MB | 89 MB | 98 MB |
| 2007-11-02_23-31-10.uvl | 475/511 | memout | memout | memout | 94 MB | 96 MB | 106 MB |
| 1-1.uvl | 500/5 | memout | timeout | 115 MB | 69 MB | 101 MB | 109 MB |
| 1-1.uvl (2) | 1000/10 | memout | memout | 335 MB | 84 MB | 137 MB | 139 MB |
| busybox_simple.uvl | 1108/930 | memout | memout | memout | timeout | 221 MB | 193 MB |
| embtoolkit.uvl | 1179/323 | memout | memout | memout | 275 MB | 200 MB | 200 MB |
| XSEngine.uvl |  | memout | timeout | memout | timeout | timeout | timeout |

## Reproducing

The models in `resources/` are listed in `models.txt` as paths; the others come from the
UVLHub corpus and the BeTTy synthetic set and are named there in comments. Add their paths to
reproduce the whole table.

```bash
# from the bdd_metamodel directory
grep -v '^#' benchmarks/models.txt | awk '{print $1}' | \
  xargs python benchmarks/bench_compile.py --label my-run --timeout 120 \
        --out benchmarks/results/compile.csv --option builder=python
python benchmarks/summarize.py benchmarks/results/compile.csv --metric compile_s
```

`compile.csv` also holds the runs made while developing the build options, under their own labels.
