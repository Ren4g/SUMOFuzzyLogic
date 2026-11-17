# Fuzzy controller

The controller keeps the existing Mamdani rule base in `fuzzy_controller.py`:

```python
fuzzy_green_time(own_queue, opposing_queue) -> green_seconds
```

The first argument is the queue for the direction currently being served. Swap the arguments when asking for the opposing direction's green duration. Inputs are finite, non-negative queue counts clipped at 40; the output universe is 10–60 seconds. The SUMO adapter is in `control/fuzzy_phase_controller.py`; it finds the two dominant green phases from SUMO's program and maps active links back to incoming lanes. Protected turn phases retain their network-defined timing.

Run a fuzzy simulation from the repository root:

```powershell
python -m pip install -r requirements.txt
python control/run_sumo.py --scenario 4huong3lan --mode fuzzy --nogui
```

The fuzzy module only computes a green duration. `control/` owns phase transitions and SUMO integration. The current adapter expects exactly two equally dominant main green phases; it reports an error for a signal program that does not fit that structure.
