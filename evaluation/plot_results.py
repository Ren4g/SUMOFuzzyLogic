"""Plot summary metrics for comparison between controllers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_INPUT = Path("evaluation/results/comparison.csv")
DEFAULT_OUTPUT = Path("evaluation/results/plot.png")


def load_comparison(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"No comparison data found in {path}")
    return df


def plot_comparison(data: pd.DataFrame, output_path: Path) -> Path:
    metrics = [
        "avg_travel_time",
        "avg_waiting_time",
        "avg_time_loss",
        "throughput_vehicles_per_hour",
    ]
    missing = [metric for metric in metrics if metric not in data.columns]
    if missing:
        raise ValueError(f"Comparison CSV is missing metric columns: {', '.join(missing)}")
    numeric_data = data[metrics].apply(pd.to_numeric, errors="coerce")
    if numeric_data.empty:
        raise ValueError("No numeric metrics available for plotting")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 9))
    axes = axes.flatten()

    for ax, metric in zip(axes, metrics):
        values = numeric_data[metric].tolist()
        labels = [
            f"{row.get('controller', 'run')}\n{str(row.get('run_id', ''))[-6:]}"
            for row in data.to_dict(orient="records")
        ]
        palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        ax.bar(labels, values, color=[palette[index % len(palette)] for index in range(len(labels))])
        ax.set_title(metric.replace("_", " ").title())
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=DEFAULT_INPUT, help="CSV comparison input")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PNG output path")
    args = parser.parse_args()

    try:
        data = load_comparison(args.input)
        output = plot_comparison(data, args.output)
    except (FileNotFoundError, ValueError, pd.errors.EmptyDataError) as error:
        parser.error(str(error))

    print(f"Plot saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
