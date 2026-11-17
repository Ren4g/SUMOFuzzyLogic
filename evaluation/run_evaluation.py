"""Create per-vehicle and per-run evaluation files from one SUMO run."""

from __future__ import annotations

import re
from pathlib import Path

from evaluation.calculate_metrics import calculate_metrics, read_trip_csv, write_metrics
from evaluation.collect_metrics import tripinfo_to_csv


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "run"


def evaluate_tripinfo(
    tripinfo_path: str | Path,
    scenario: str,
    controller: str,
    run_id: str,
    seed: int,
    simulation_duration: float,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Evaluate one run and return its vehicle CSV and summary paths."""
    tripinfo_path = Path(tripinfo_path)
    output_dir = Path(output_dir)
    stem = f"{_safe_name(scenario)}_{_safe_name(controller)}_{_safe_name(run_id)}"
    vehicle_csv = output_dir / f"{stem}_vehicles.csv"
    summary_csv = output_dir / f"{stem}_summary.csv"

    tripinfo_to_csv(tripinfo_path, vehicle_csv)
    metrics = calculate_metrics(
        read_trip_csv(vehicle_csv), controller, run_id, simulation_duration
    )
    metrics["scenario"] = scenario
    metrics["seed"] = seed
    write_metrics(summary_csv, metrics)
    return {"vehicles": vehicle_csv, "summary": summary_csv}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tripinfo", type=Path)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--controller", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--simulation-duration", type=float, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/evaluation"))
    args = parser.parse_args()
    paths = evaluate_tripinfo(
        args.tripinfo, args.scenario, args.controller, args.run_id, args.seed,
        args.simulation_duration, args.output_dir,
    )
    print(f"Vehicle metrics: {paths['vehicles']}")
    print(f"Run summary: {paths['summary']}")
