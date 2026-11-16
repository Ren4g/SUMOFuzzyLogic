"""Traffic-light controller scaffolding for SUMO experiments.

This module defines the controller interfaces used by the evaluation pipeline.
The project can switch between a fixed-time controller and a fuzzy controller
without changing the surrounding logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass
class TrafficState:
    """Minimal traffic-state placeholder used by controller logic."""

    north_south: float = 0.0
    east_west: float = 0.0
    queue_length: float = 0.0
    vehicle_density: float = 0.0


class TrafficLightController:
    """Base controller interface."""

    name: str = "controller"

    def choose_phase(self, state: Mapping[str, float] | TrafficState) -> str:
        raise NotImplementedError


class FixedTimeController(TrafficLightController):
    """Simple round-robin signal phase selector."""

    def __init__(self, phase_order: Iterable[str] = ("NS", "EW"), phase_duration: float = 30.0):
        self.name = "fixed_time"
        self.phase_order = list(phase_order)
        self.phase_duration = float(phase_duration)
        self._index = 0

    def choose_phase(self, state: Mapping[str, float] | TrafficState) -> str:
        phase = self.phase_order[self._index % len(self.phase_order)]
        self._index += 1
        return phase


class FuzzyController(TrafficLightController):
    """Fuzzy controller placeholder.

The implementation intentionally remains small because the actual fuzzy
membership logic belongs in a dedicated inference module if the project grows.
"""

    def __init__(self, phase_order: Iterable[str] = ("NS", "EW"), thresholds: tuple[float, float] = (0.5, 0.7)):
        self.name = "fuzzy"
        self.phase_order = list(phase_order)
        self.low_threshold, self.high_threshold = thresholds

    def choose_phase(self, state: Mapping[str, float] | TrafficState) -> str:
        if isinstance(state, TrafficState):
            traffic = {
                "north_south": state.north_south,
                "east_west": state.east_west,
                "queue_length": state.queue_length,
                "vehicle_density": state.vehicle_density,
            }
        else:
            traffic = dict(state)

        north_south = float(traffic.get("north_south", 0.0))
        east_west = float(traffic.get("east_west", 0.0))
        queue = float(traffic.get("queue_length", 0.0))
        density = float(traffic.get("vehicle_density", 0.0))

        score = max(north_south, east_west, queue, density)
        if score >= self.high_threshold:
            return self.phase_order[0]
        return self.phase_order[1]


def build_controller(controller_name: str) -> TrafficLightController:
    controller_name = (controller_name or "fixed_time").lower()
    if controller_name == "fuzzy":
        return FuzzyController()
    return FixedTimeController()
