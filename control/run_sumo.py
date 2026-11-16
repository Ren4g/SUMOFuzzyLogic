"""Thin wrapper around SUMO CLI used by the project.

The file intentionally keeps the logic simple: it resolves the SUMO executable,
then runs the requested configuration file and exports the tripinfo XML result.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def resolve_sumo_binary(explicit: str | None = None) -> str:
    if explicit:
        candidate = Path(explicit)
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"SUMO binary was not found at {candidate}")

    env_path = os.environ.get("SUMO_HOME")
    if env_path:
        candidates = [
            Path(env_path) / "bin" / "sumo.exe",
            Path(env_path) / "bin" / "sumo",
            Path(env_path) / "sumo.exe",
            Path(env_path) / "sumo",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

    binary = shutil.which("sumo") or shutil.which("sumo.exe")
    if binary:
        return binary

    raise FileNotFoundError(
        "SUMO is not installed or not on PATH. Install SUMO or set SUMO_HOME."
    )


def run_sumo(config_path: Path, output_path: Path, sumo_bin: str | None = None) -> Path:
    if not config_path.exists():
        raise FileNotFoundError(f"SUMO config file does not exist: {config_path}")

    binary = resolve_sumo_binary(sumo_bin)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [binary, "-c", str(config_path), "--tripinfo-output", str(output_path)]
    subprocess.run(command, check=True)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a SUMO configuration .sumocfg file")
    parser.add_argument("--output", type=Path, default=Path("evaluation/results/tripinfo.xml"), help="Tripinfo XML output")
    parser.add_argument("--sumo-bin", help="Optional explicit path to the SUMO binary")
    args = parser.parse_args()

    try:
        output = run_sumo(args.config, args.output, args.sumo_bin)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        parser.error(str(error))

    print(f"SUMO output written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
