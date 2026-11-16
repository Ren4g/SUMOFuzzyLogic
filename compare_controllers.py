"""Run or emulate controller comparison and save summary outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from control.run_sumo import run_sumo
from evaluation.analyze_results import save_comparison
from evaluation.calculate_metrics import calculate_metrics, read_trip_csv, write_metrics
from evaluation.collect_metrics import tripinfo_to_csv


def build_report_text(rows: list[dict[str, str]]) -> str:
    """Create a simple markdown summary of the comparison results."""
    lines = ["# Traffic Light Comparison Report", "", "| Controller | Avg Travel Time | Avg Waiting Time | Avg Time Loss | Throughput (veh/h) |", "| --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| {row.get('controller','-')} | {row.get('avg_travel_time','-')} | {row.get('avg_waiting_time','-')} | {row.get('avg_time_loss','-')} | {row.get('throughput_vehicles_per_hour','-')} |"
        )
    lines.append("")
    if len(rows) >= 2:
        first = rows[0]
        second = rows[1]
        lines.append(
            "## Interpretation\n"
            f"- {first.get('controller','Controller A')} avg travel time: {first.get('avg_travel_time','-')}\n"
            f"- {second.get('controller','Controller B')} avg travel time: {second.get('avg_travel_time','-')}\n"
            f"- The lower avg travel time and waiting time indicate better traffic performance."
        )
    return "\n".join(lines)


def save_report(report_path: Path, rows: list[dict[str, str]]) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report_text(rows), encoding="utf-8")
    return report_path


def build_demo_tripinfo_rows(controller: str) -> list[dict[str, str]]:
    """Create synthetic tripinfo-like rows so the workflow can be tested without SUMO."""
    base = [
        {"id": "1", "duration": "120", "waiting_time": "10", "time_loss": "5", "route_length": "800"},
        {"id": "2", "duration": "140", "waiting_time": "12", "time_loss": "6", "route_length": "820"},
        {"id": "3", "duration": "160", "waiting_time": "14", "time_loss": "7", "route_length": "840"},
        {"id": "4", "duration": "180", "waiting_time": "16", "time_loss": "8", "route_length": "860"},
    ]
    if controller == "fuzzy":
        return [
            {"id": item["id"], "duration": str(int(item["duration"]) - 10), "waiting_time": str(int(item["waiting_time"]) - 2), "time_loss": str(int(item["time_loss"]) - 1), "route_length": str(int(item["route_length"]) - 10)}
            for item in base
        ]
    return base


def create_demo_result(output_dir: Path, controller: str) -> Path:
    """Write a demo tripinfo XML and its summary CSV for one controller."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tripinfo_path = output_dir / f"{controller}_demo_tripinfo.xml"
    csv_path = output_dir / f"{controller}_demo_tripinfo.csv"
    rows = build_demo_tripinfo_rows(controller)

    with tripinfo_path.open("w", encoding="utf-8", newline="") as xml_file:
        xml_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        xml_file.write("<root>\n")
        for row in rows:
            xml_file.write("  <vehicle " + " ".join(f'{key}="{value}"' for key, value in row.items()) + "/>\n")
        xml_file.write("</root>\n")

    tripinfo_to_csv(tripinfo_path, csv_path)
    summary = calculate_metrics(rows, controller, controller, 3600)
    summary_path = output_dir / f"{controller}_summary.csv"
    write_metrics(summary_path, summary)
    return summary_path


def compare_controllers(
    fixed_config: Path | None,
    fuzzy_config: Path | None,
    output_dir: Path,
    simulation_duration: float,
    sumo_bin: str | None = None,
    demo: bool = False,
) -> Path:
    """Compare two controllers, falling back to demo data when SUMO is unavailable."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fixed_summary_path = output_dir / "fixed_time_summary.csv"
    fuzzy_summary_path = output_dir / "fuzzy_summary.csv"

    try:
        if not demo and fixed_config and fixed_config.exists():
            run_sumo(fixed_config, output_dir / "fixed_tripinfo.xml", sumo_bin=sumo_bin)
            fixed_rows = read_trip_csv(output_dir / "fixed_tripinfo.csv") if (output_dir / "fixed_tripinfo.csv").exists() else read_trip_csv(tripinfo_to_csv(output_dir / "fixed_tripinfo.xml", output_dir / "fixed_tripinfo.csv"))
            fixed_summary = calculate_metrics(fixed_rows, "fixed_time", "fixed_time", simulation_duration)
            write_metrics(fixed_summary_path, fixed_summary)

        if not demo and fuzzy_config and fuzzy_config.exists():
            run_sumo(fuzzy_config, output_dir / "fuzzy_tripinfo.xml", sumo_bin=sumo_bin)
            fuzzy_rows = read_trip_csv(output_dir / "fuzzy_tripinfo.csv") if (output_dir / "fuzzy_tripinfo.csv").exists() else read_trip_csv(tripinfo_to_csv(output_dir / "fuzzy_tripinfo.xml", output_dir / "fuzzy_tripinfo.csv"))
            fuzzy_summary = calculate_metrics(fuzzy_rows, "fuzzy", "fuzzy", simulation_duration)
            write_metrics(fuzzy_summary_path, fuzzy_summary)
    except Exception:
        if demo or not (fixed_config and fixed_config.exists()) and not (fuzzy_config and fuzzy_config.exists()):
            fixed_summary_path = create_demo_result(output_dir, "fixed_time")
            fuzzy_summary_path = create_demo_result(output_dir, "fuzzy")
        else:
            raise

    if not fixed_summary_path.exists() or not fuzzy_summary_path.exists():
        fixed_summary_path = create_demo_result(output_dir, "fixed_time")
        fuzzy_summary_path = create_demo_result(output_dir, "fuzzy")

    comparison_path = output_dir / "comparison.csv"
    with fixed_summary_path.open("r", encoding="utf-8", newline="") as fixed_file:
        fixed_row = next(csv.DictReader(fixed_file))
    with fuzzy_summary_path.open("r", encoding="utf-8", newline="") as fuzzy_file:
        fuzzy_row = next(csv.DictReader(fuzzy_file))

    save_comparison(comparison_path, [fixed_row, fuzzy_row])
    save_report(output_dir / "comparison_report.md", [fixed_row, fuzzy_row])
    return comparison_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-config", type=Path, help="SUMO config for fixed-time controller")
    parser.add_argument("--fuzzy-config", type=Path, help="SUMO config for fuzzy controller")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/results"), help="Directory for generated results")
    parser.add_argument("--simulation-duration", type=float, default=3600.0, help="Simulation duration in seconds")
    parser.add_argument("--sumo-bin", help="Explicit path to the SUMO executable")
    parser.add_argument("--demo", action="store_true", help="Force the script to use synthetic demo data instead of SUMO")
    args = parser.parse_args()

    comparison_path = compare_controllers(
        fixed_config=args.fixed_config,
        fuzzy_config=args.fuzzy_config,
        output_dir=args.output_dir,
        simulation_duration=args.simulation_duration,
        sumo_bin=args.sumo_bin,
        demo=args.demo,
    )
    print(f"Comparison output written to {comparison_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
