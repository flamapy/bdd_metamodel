"""Turn a bench_compile.py CSV into a markdown table: one row per model, one column per label.

Usage: python benchmarks/summarize.py benchmarks/results/compile.csv [--metric compile_s]
"""
import argparse
import csv
from collections import defaultdict


def _cell(row: dict[str, str], metric: str) -> str:
    status = row["status"]
    if status != "ok":
        return status.split(":")[0]
    value = row[metric]
    if metric == "compile_s":
        seconds = float(value)
        return f"{seconds * 1000:.0f} ms" if seconds < 1 else f"{seconds:.1f} s"
    if metric == "peak_rss_mb":
        return f"{float(value):.0f} MB"
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--metric", default="compile_s",
                        choices=["compile_s", "nodes", "peak_rss_mb", "configurations"])
    parser.add_argument("--labels", help="comma-separated labels to show (default: all)")
    args = parser.parse_args()

    with open(args.csv, encoding="utf8") as file:
        rows = list(csv.DictReader(file))
    labels = list(dict.fromkeys(row["label"] for row in rows))
    if args.labels:
        labels = [label for label in args.labels.split(",") if label in labels]
    # Older results name models by file name only: tell apart models with the same name by
    # their order of appearance in each run (all runs use the same model list).
    seen: dict[tuple[str, str], int] = defaultdict(int)
    keys = []
    for row in rows:
        occurrence = seen[(row["label"], row["model"])]
        seen[(row["label"], row["model"])] += 1
        keys.append(row["model"] if occurrence == 0 else f"{row['model']} ({occurrence + 1})")
    models = list(dict.fromkeys(keys))
    sizes: dict[str, str] = {}
    table: dict[str, dict[str, str]] = defaultdict(dict)
    for key, row in zip(keys, rows):
        table[key][row["label"]] = _cell(row, args.metric)
        if row["features"]:
            sizes[key] = f"{row['features']}/{row['constraints']}"

    print("| Model | Features/CTCs | " + " | ".join(labels) + " |")
    print("|---|---|" + "---|" * len(labels))
    for model in models:
        cells = [table[model].get(label, "") for label in labels]
        print(f"| {model} | {sizes.get(model, '')} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
