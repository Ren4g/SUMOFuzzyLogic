"""Aggregate per-vehicle SUMO trip data into run-level traffic metrics."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, Mapping


FIELD_ALIASES = {
    "duration": ("duration", "travel_time", "traveltime"),
    "waiting_time": ("waiting_time", "waitingtime", "wait_time"),
    "time_loss": ("time_loss", "timeloss"),
    "route_length": ("route_length", "routelength", "distance"),
}
METRIC_FIELDS = (
    "vehicle_count",
    "avg_travel_time",
    "avg_waiting_time",
    "avg_time_loss",
    "avg_route_length",
    "throughput_vehicles_per_hour",
)


def _normalized_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _find_field(row: Mapping[str, str], aliases: tuple[str, ...]) -> str | None:
    normalized = {_normalized_key(key): key for key in row}
    for alias in aliases:
        key = normalized.get(_normalized_key(alias))
        if key is not None:
            return key
    return None


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def calculate_metrics(
    rows: Iterable[Mapping[str, str]],
    controller: str,
    run_id: str,
    simulation_duration: float | None = None,
) -> dict[str, str | int | float]:
    """Return averages for completed trips in a per-vehicle CSV dataset."""
    records = list(rows)
    if records and _find_field(records[0], FIELD_ALIASES["duration"]) is None:
        raise ValueError(
            "Input CSV must contain a trip duration column (duration or travel_time)."
        )

    values: dict[str, list[float]] = {name: [] for name in FIELD_ALIASES}
    for row in records:
        duration_key = _find_field(row, FIELD_ALIASES["duration"])
        duration = _number(row.get(duration_key)) if duration_key else None
        if duration is None or duration < 0:
            continue
        values["duration"].append(duration)
        for metric in ("waiting_time", "time_loss", "route_length"):
            key = _find_field(row, FIELD_ALIASES[metric])
            number = _number(row.get(key)) if key else None
            if number is not None:
                values[metric].append(number)

    vehicle_count = len(values["duration"])
    if simulation_duration is not None and simulation_duration <= 0:
        raise ValueError("Simulation duration must be greater than zero seconds.")

    result: dict[str, str | int | float] = {
        "controller": controller,
        "run_id": run_id,
        "vehicle_count": vehicle_count,
        "avg_travel_time": _average(values["duration"]),
        "avg_waiting_time": _average(values["waiting_time"]),
        "avg_time_loss": _average(values["time_loss"]),
        "avg_route_length": _average(values["route_length"]),
        "throughput_vehicles_per_hour": (
            vehicle_count * 3600 / simulation_duration
            if simulation_duration is not None
            else ""
        ),
    }
    return result


def _average(values: list[float]) -> float | str:
    return sum(values) / len(values) if values else ""


def read_trip_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError(f"CSV file is empty or has no header: {path}")
        return list(reader)


def write_metrics(path: Path, metrics: Mapping[str, str | int | float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ("controller", "run_id", *METRIC_FIELDS)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerow(metrics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Per-vehicle trip CSV file")
    parser.add_argument("--output", type=Path, help="Output summary CSV path")
    parser.add_argument("--controller", help="Controller label; defaults to input filename")
    parser.add_argument("--run-id", help="Run label; defaults to input filename")
    parser.add_argument(
        "--simulation-duration",
        type=float,
        help="Simulation duration in seconds, used to calculate throughput",
    )
    args = parser.parse_args()

    controller = args.controller or args.input.stem
    run_id = args.run_id or args.input.stem
    output = args.output or args.input.with_name(f"{args.input.stem}_summary.csv")
    try:
        metrics = calculate_metrics(
            read_trip_csv(args.input), controller, run_id, args.simulation_duration
        )
        write_metrics(output, metrics)
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(f"Metrics written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
