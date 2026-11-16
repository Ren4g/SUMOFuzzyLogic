"""Run a complete SUMO evaluation workflow for a controller strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

from control.run_sumo import run_sumo
from evaluation.calculate_metrics import calculate_metrics, write_metrics, read_trip_csv
from evaluation.collect_metrics import tripinfo_to_csv


def execute_experiment(
    config_path: Path,
    controller: str,
    run_id: str,
    output_dir: Path,
    simulation_duration: float,
    sumo_bin: str | None = None,
) -> Path:
    """Run SUMO, convert tripinfo XML to CSV, and aggregate metrics."""
    tripinfo_path = output_dir / "tripinfo.xml"
    run_sumo(config_path, tripinfo_path, sumo_bin=sumo_bin)

    csv_path = output_dir / "tripinfo.csv"
    tripinfo_to_csv(tripinfo_path, csv_path)

    rows = read_trip_csv(csv_path)
    metrics = calculate_metrics(rows, controller, run_id, simulation_duration)
    output_summary = output_dir / f"{controller}_{run_id}_summary.csv"
    write_metrics(output_summary, metrics)
    return output_summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a SUMO configuration *.sumocfg file")
    parser.add_argument("--controller", default="fixed_time", help="Controller name for the run")
    parser.add_argument("--run-id", default="run_1", help="Run label stored in the summary CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/results"), help="Directory for intermediate outputs")
    parser.add_argument("--simulation-duration", type=float, default=3600.0, help="Simulation duration in seconds")
    parser.add_argument("--sumo-bin", help="Optional path to the SUMO executable")
    args = parser.parse_args()

    output = execute_experiment(
        config_path=args.config,
        controller=args.controller,
        run_id=args.run_id,
        output_dir=args.output_dir,
        simulation_duration=args.simulation_duration,
        sumo_bin=args.sumo_bin,
    )
    print(f"Experiment summary written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
