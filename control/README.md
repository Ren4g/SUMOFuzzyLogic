# Control package

This package contains the simulation runner and controller definitions used to
experiment with fixed-time vs fuzzy traffic-light policies.

## Typical flow

1. Run the simulator with the chosen SUMO configuration file.
2. Export `tripinfo.xml` with the runner.
3. Convert the XML to CSV in the evaluation package.
4. Derive aggregate metrics and compare controller performance.

## Example

```bash
"C:/Program Files/Python311/python.exe" control/run_sumo.py sumo/4huong2lan/simulation.sumocfg --output evaluation/results/tripinfo.xml
"C:/Program Files/Python311/python.exe" evaluation/collect_metrics.py evaluation/results/tripinfo.xml --output evaluation/results/tripinfo.csv
"C:/Program Files/Python311/python.exe" evaluation/calculate_metrics.py evaluation/results/tripinfo.csv --output evaluation/results/fixed_time_summary.csv --controller fixed_time --run-id fixed_time --simulation-duration 3600
```

> The actual SUMO executable must be installed and accessible on PATH or via `SUMO_HOME`.
