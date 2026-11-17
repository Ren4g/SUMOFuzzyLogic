"""Build a comparison CSV and chart from summaries emitted by SUMO runs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from evaluation.analyze_results import compare_summaries, save_comparison
from evaluation.plot_results import plot_comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results/evaluation"))
    parser.add_argument("--scenario", help="Only include runs from this scenario")
    parser.add_argument("--seed", type=int, help="Only include runs using this SUMO seed")
    args = parser.parse_args()

    summaries = sorted(args.results_dir.glob("*_summary.csv"))
    if not summaries:
        parser.error(f"No run summaries found in {args.results_dir}")

    grouped: dict[str, list[Path]] = {}
    for path in summaries:
        rows = _read_rows(path)
        scenario = rows[0].get("scenario", "") if rows else ""
        if args.scenario and scenario != args.scenario:
            continue
        if args.seed is not None and (not rows or rows[0].get("seed") != str(args.seed)):
            continue
        grouped.setdefault(scenario or "unspecified", []).append(path)
    if not grouped:
        selection = []
        if args.scenario:
            selection.append(f"scenario {args.scenario!r}")
        if args.seed is not None:
            selection.append(f"seed {args.seed}")
        parser.error(f"No summaries found for {' and '.join(selection) or 'the selected filters'}")

    for scenario, scenario_summaries in sorted(grouped.items()):
        rows = compare_summaries(scenario_summaries)
        suffix = "" if (args.scenario or len(grouped) == 1) and args.seed is None else f"_{scenario}"
        if args.seed is not None:
            suffix += f"_seed{args.seed}"
        comparison_path = args.results_dir / f"comparison{suffix}.csv"
        chart_path = args.results_dir / f"comparison{suffix}.png"
        save_comparison(comparison_path, rows)
        plot_comparison(pd.DataFrame(rows), chart_path)
        print(f"[{scenario}] Comparison CSV: {comparison_path}")
        print(f"[{scenario}] Comparison chart: {chart_path}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


if __name__ == "__main__":
    raise SystemExit(main())
