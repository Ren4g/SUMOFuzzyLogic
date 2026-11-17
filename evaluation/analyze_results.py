"""Compare and summarize controller results from generated CSV summaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_RESULTS = Path("evaluation/results")


def read_summary_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError(f"Summary CSV is empty or has no header: {path}")
        return list(reader)


def compare_summaries(paths: list[Path]) -> list[dict[str, str]]:
    comparison: list[dict[str, str]] = []
    for path in paths:
        rows = read_summary_csv(path)
        if not rows:
            raise ValueError(f"No rows found in summary: {path}")
        row = rows[0]
        comparison.append({
            "controller": row.get("controller", path.stem),
            "run_id": row.get("run_id", path.stem),
            "scenario": row.get("scenario", ""),
            "seed": row.get("seed", ""),
            "vehicle_count": row.get("vehicle_count", ""),
            "avg_travel_time": row.get("avg_travel_time", ""),
            "avg_waiting_time": row.get("avg_waiting_time", ""),
            "avg_time_loss": row.get("avg_time_loss", ""),
            "avg_route_length": row.get("avg_route_length", ""),
            "throughput_vehicles_per_hour": row.get("throughput_vehicles_per_hour", ""),
        })
    return comparison


def save_comparison(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "controller",
        "run_id",
        "scenario",
        "seed",
        "vehicle_count",
        "avg_travel_time",
        "avg_waiting_time",
        "avg_time_loss",
        "avg_route_length",
        "throughput_vehicles_per_hour",
    ]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Summary CSV files to compare")
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS / "comparison.csv", help="Comparison CSV path")
    args = parser.parse_args()

    try:
        rows = compare_summaries(args.paths)
        output = save_comparison(args.output, rows)
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))

    print(f"Comparison written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
