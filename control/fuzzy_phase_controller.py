"""xài cho luật mờ 2 đầu vào, 2 pha xanh"""
from __future__ import annotations

import math

import traci


GREEN_STATES = {"g", "G"}
MIN_GREEN_SECONDS = 10.0
MAX_GREEN_SECONDS = 60.0


class FuzzyPhaseController:
    """Ánh xạ hai pha tín hiệu chính sang các nhóm hàng đợi + thiết lập thời gian đèn xanh.
    """

    def __init__(self, tls_id: str):
        try:
            from fuzzy.fuzzy_controller import fuzzy_green_time
        except ImportError as error:
            raise RuntimeError(
                "Fuzzy mode requires scikit-fuzzy. Install dependencies with "
                "`python -m pip install -r requirements.txt`."
            ) from error

        self.tls_id = tls_id
        self.fuzzy_green_time = fuzzy_green_time
        logics = traci.trafficlight.getAllProgramLogics(tls_id)
        if not logics:
            raise RuntimeError(f"Traffic light {tls_id!r} has no signal program.")
        self.logic = logics[0]
        self.controlled_links = traci.trafficlight.getControlledLinks(tls_id)
        self.groups = self._discover_main_groups()
        self.last_phase = None

        print(
            "Fuzzy điều khiển hai nhóm pha chính: "
            f"pha {self.groups[0][0]} ({len(self.groups[0][1])} làn) và "
            f"pha {self.groups[1][0]} ({len(self.groups[1][1])} làn); "
            "các pha rẽ riêng giữ nguyên thời lượng SUMO."
        )

    def _discover_main_groups(self) -> list[tuple[int, set[str]]]:
        candidates: list[tuple[int, int, set[str]]] = []
        for phase_index, phase in enumerate(self.logic.phases):
            active_links = [
                index
                for index, state in enumerate(phase.state)
                if state in GREEN_STATES
            ]
            if not active_links:
                continue

            lanes: set[str] = set()
            for link_index in active_links:
                if link_index >= len(self.controlled_links):
                    continue
                for link in self.controlled_links[link_index]:
                    if link:
                        lanes.add(link[0])
            if lanes:
                candidates.append((len(active_links), phase_index, lanes))

        if len(candidates) < 2:
            raise RuntimeError(
                f"Traffic light {self.tls_id!r} needs at least two green phases."
            )

        candidates.sort(key=lambda item: (-item[0], item[1]))
        top_score = candidates[0][0]
        main = [candidate for candidate in candidates if candidate[0] == top_score]
        if len(main) != 2:
            raise RuntimeError(
                f"Cannot identify exactly two dominant green phases for "
                f"{self.tls_id!r}; found {len(main)} candidates."
            )
        return [(phase_index, lanes) for _, phase_index, lanes in main]

    def _queue_for_lanes(self, lanes: set[str]) -> int:
        return sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)

    def apply_current_phase(self) -> None:
        phase_index = traci.trafficlight.getPhase(self.tls_id)
        if phase_index == self.last_phase:
            return
        self.last_phase = phase_index

        group_index = next(
            (index for index, (main_phase, _) in enumerate(self.groups)
             if main_phase == phase_index),
            None,
        )
        if group_index is None:
            return

        queues = [self._queue_for_lanes(lanes) for _, lanes in self.groups]
        own_queue = queues[group_index]
        other_queue = queues[1 - group_index]
        green_seconds = self.fuzzy_green_time(own_queue, other_queue)
        green_seconds = min(MAX_GREEN_SECONDS, max(MIN_GREEN_SECONDS, green_seconds))
        if not math.isfinite(green_seconds):
            raise RuntimeError("Fuzzy controller returned a non-finite green time.")

        traci.trafficlight.setPhaseDuration(self.tls_id, green_seconds)
        print(
            f"Fuzzy pha {phase_index}: hàng chờ nhóm này={own_queue}, "
            f"nhóm kia={other_queue}, xanh={green_seconds:.2f}s"
        )
