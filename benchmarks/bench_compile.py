"""Benchmark FM -> BDD compilation.

Each model is compiled in its own subprocess so that a timeout or a memory blow-up only
affects that model: the child is killed after `--timeout` seconds (status `timeout`) or when
its resident memory exceeds `--max-rss-mb` (status `memout`). For every model the benchmark
records the compile time, the size of the compiled BDD (reachable nodes), the number of
configurations (to check that different builders agree) and the peak resident memory of the
child process.

Usage (from the bdd_metamodel directory):

    python benchmarks/bench_compile.py --label baseline --timeout 300 \\
        --out benchmarks/results/baseline.csv MODEL.uvl [MODEL.uvl ...]

Builder options are forwarded to `FmToBDD` as keyword arguments with `--option key=value`
(only for builders that accept them). The dd engine in use (`cudd` or `autoref`) is recorded
in every row.
"""
import argparse
import csv
import json
import os
import pathlib
import resource
import subprocess
import sys
import tempfile
import time
from typing import Any

FIELDS = [
    "label", "model", "features", "constraints", "dd_backend", "status",
    "compile_s", "nodes", "configurations", "peak_rss_mb", "options",
]


def _peak_rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is in bytes on macOS and in kilobytes on Linux.
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


def _model_name(path: str) -> str:
    """The model's file name with its directory (several corpora reuse file names)."""
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return f"{parent}/{os.path.basename(path)}"


def _parse_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def run_single(path: str, options: dict[str, Any]) -> dict[str, Any]:
    """Compile one model in the current process and return its measurements."""
    # Imported here so that only the child processes load flamapy.
    # pylint: disable=import-outside-toplevel
    from flamapy.metamodels.fm_metamodel.transformations import UVLReader  # noqa: PLC0415
    from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD  # noqa: PLC0415
    from flamapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import (  # noqa: PLC0415
        DD_BACKEND,
    )

    feature_model = UVLReader(path).transform()
    start = time.perf_counter()
    bdd_model = FmToBDD(feature_model, **options).transform()
    compile_s = time.perf_counter() - start
    return {
        "features": len(feature_model.get_features()),
        "constraints": len(feature_model.get_constraints()),
        "dd_backend": DD_BACKEND,
        "status": "ok",
        "compile_s": round(compile_s, 4),
        "nodes": bdd_model.root.dag_size,
        "configurations": bdd_model.count_solutions(),
        "peak_rss_mb": round(_peak_rss_mb(), 1),
    }


def _rss_mb(pid: int) -> float:
    """Current resident memory of a process in MB (0 if it cannot be read)."""
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True,
                             text=True, check=False).stdout.strip()
        return int(out) / 1024 if out else 0.0
    except (OSError, ValueError):
        return 0.0


def run_isolated(path: str, options: dict[str, Any], timeout: float,
                 max_rss_mb: float) -> dict[str, Any]:
    """Compile one model in a child process, killing it on timeout or above `max_rss_mb`."""
    cmd = [sys.executable, __file__, "--single", path, "--options-json", json.dumps(options)]
    with tempfile.TemporaryFile("w+") as out, tempfile.TemporaryFile("w+") as err:
        proc = subprocess.Popen(cmd, stdout=out, stderr=err, text=True)  # pylint: disable=consider-using-with
        start = time.monotonic()
        status = None
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                status = {"status": "timeout", "compile_s": timeout}
            elif _rss_mb(proc.pid) > max_rss_mb:
                status = {"status": "memout", "compile_s": round(elapsed, 1),
                          "peak_rss_mb": max_rss_mb}
            if status is not None:
                proc.kill()
                proc.wait()
                return status
            time.sleep(0.2)
        out.seek(0)
        err.seek(0)
        if proc.returncode != 0:
            last_line = (err.read().strip().splitlines() or ["unknown error"])[-1]
            return {"status": f"error: {last_line[:200]}"}
        return json.loads(out.read().strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="*", help="UVL model paths")
    parser.add_argument("--label", default="run", help="name of this configuration")
    parser.add_argument("--timeout", type=float, default=300.0, help="seconds per model")
    parser.add_argument("--max-rss-mb", type=float, default=6000.0,
                        help="kill a model's process above this resident memory (MB)")
    parser.add_argument("--out", help="CSV file to append the results to")
    parser.add_argument("--option", action="append", default=[],
                        help="key=value keyword argument for FmToBDD (repeatable)")
    parser.add_argument("--single", help=argparse.SUPPRESS)
    parser.add_argument("--options-json", default="{}", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.single:
        print(json.dumps(run_single(args.single, json.loads(args.options_json))))
        return

    options = {}
    for item in args.option:
        key, _, value = item.partition("=")
        options[key] = _parse_value(value)

    writer = None
    out_file = None
    if args.out:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not out_path.exists()
        out_file = open(out_path, "a", newline="", encoding="utf8")  # pylint: disable=consider-using-with
        writer = csv.DictWriter(out_file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

    try:
        for path in args.models:
            row = {"label": args.label, "model": _model_name(path),
                   "options": json.dumps(options, sort_keys=True)}
            row.update(run_isolated(path, options, args.timeout, args.max_rss_mb))
            print(f"{row['model']:45} {row.get('status', ''):10} "
                  f"{row.get('compile_s', ''):>10}s nodes={row.get('nodes', '')} "
                  f"configs={row.get('configurations', '')} rss={row.get('peak_rss_mb', '')}MB",
                  flush=True)
            if writer is not None:
                writer.writerow({k: row.get(k, "") for k in FIELDS})
                out_file.flush()  # type: ignore[union-attr]
    finally:
        if out_file is not None:
            out_file.close()


if __name__ == "__main__":
    main()
