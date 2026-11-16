"""Read SUMO tripinfo output into Python-friendly dictionaries."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def read_tripinfo(path: Path) -> list[dict[str, str]]:
    """Read a SUMO tripinfo XML file and return one dict per vehicle."""
    tree = ET.parse(path)
    root = tree.getroot()
    rows: list[dict[str, str]] = []

    for vehicle in root.findall("vehicle"):
        rows.append({**vehicle.attrib})

    if not rows:
        raise ValueError(f"No vehicle data found in {path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tripinfo", type=Path, help="Path to a SUMO tripinfo.xml file")
    args = parser.parse_args()

    rows = read_tripinfo(args.tripinfo)
    print(f"Loaded {len(rows)} vehicles")
    print(rows[0] if rows else {})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
