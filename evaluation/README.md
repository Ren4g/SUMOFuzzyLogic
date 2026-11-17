# Evaluation

Each completed `control/run_sumo.py` run automatically writes:

- SUMO `tripinfo_*.xml` in `results/`.
- Per-vehicle CSV and one-row run summary in `results/evaluation/`.
- The existing aggregate row in `results/results.csv`.

Build charts and comparison CSVs from saved run summaries:

```powershell
python -m evaluation.report_results
python -m evaluation.report_results --scenario 4huong3lan
python -m evaluation.report_results --scenario 4huong3lan --seed 1
```

When summaries from multiple scenarios exist, the default command writes a separate comparison for each scenario. Each bar represents an individual run and records its SUMO seed. The tool does not aggregate seeds or calculate confidence intervals, so run fuzzy and baseline with the same scenario, demand, and multiple identical seed values before drawing performance conclusions.

Metrics include completed-vehicle count, mean travel time, waiting time, time loss, route length, and completed vehicles per simulated hour. Waiting-time and travel metrics are computed for vehicles present in SUMO tripinfo (completed trips).
