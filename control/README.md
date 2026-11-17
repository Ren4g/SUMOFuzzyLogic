# Control

`launcher.py` provides the GUI. The runner can also be called directly from the repository root:

```powershell
python control/run_sumo.py --scenario 4huong3lan --mode observe --nogui --seed 1
python control/run_sumo.py --scenario 4huong3lan --mode fixed --green 30 --yellow 3 --nogui --seed 1
python control/run_sumo.py --scenario 4huong3lan --mode fuzzy --nogui --seed 1
```

Modes:

- `observe`: keep the signal program supplied by SUMO.
- `fixed`: set the two dominant green phases to the requested green time and set yellow phases to the requested yellow time. Protected turn greens retain their scenario timing.
- `fuzzy`: use `fuzzy/fuzzy_controller.py` to set the two dominant green durations from the queue on each phase's incoming lanes. SUMO's signal state and controlled-link indices provide the phase-to-lane mapping. Other phases, including protected turns, keep their configured durations.

Fuzzy timing is recalculated once when a main green phase begins. It does not replace the signal program or modify transition phases. After a run, tripinfo and per-run evaluation files are saved under `results/`. The `--seed` argument is passed to SUMO to make baseline/controller runs reproducible.

Install Python packages with `python -m pip install -r requirements.txt`; SUMO must also be installed and `SUMO_HOME` configured.
