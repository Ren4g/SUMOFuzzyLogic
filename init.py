"""Project bootstrap and quick entry point for SUMO traffic experiments.

Usage examples:
    python init.py --help
    python run_experiment.py sumo/4huong2lan/simulation.sumocfg --controller fixed_time --run-id fixed_time
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print workspace status and usage hints",
    )
    args = parser.parse_args()

    if args.status:
        print("SUMOFuzzyLogic project")
        print("- control/: traffic-light logic and SUMO runner")
        print("- evaluation/: metrics and report generation")
        print("- sumo/: network and route definitions")
        print("- run_experiment.py: end-to-end experiment launcher")
        return 0

    print("Project initialized. Use: python run_experiment.py --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
