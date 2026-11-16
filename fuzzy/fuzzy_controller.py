
import math
import sys

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

RULES = [
    ("Low",    "Low",    "Medium"),
    ("Low",    "Medium", "Short"),
    ("Low",    "High",   "Short"),

    ("Medium", "Low",    "Long"),
    ("Medium", "Medium", "Medium"),
    ("Medium", "High",   "Short"),

    ("High",   "Low",    "Long"),
    ("High",   "Medium", "Long"),
    ("High",   "High",   "Medium"),
]

def build_controller():
    """Xây dựng bộ điều khiển Mamdani."""

    # Miền giá trị của biến.
    queue_universe = np.linspace(0, 40, 401)
    time_universe = np.linspace(10, 60, 501)

    # Hai biến đầu vào.
    ns_queue = ctrl.Antecedent(queue_universe, "ns_queue")
    ew_queue = ctrl.Antecedent(queue_universe, "ew_queue")

    # Một biến đầu ra.
    green_time = ctrl.Consequent(time_universe, "green_time")
    green_time.defuzzify_method = "centroid"

    # Hai đầu vào dùng cùng thiết kế hàm thuộc.
    for variable in (ns_queue, ew_queue):
        variable["Low"] = fuzz.trimf(
            variable.universe, [0, 0, 20]
        )
        variable["Medium"] = fuzz.trimf(
            variable.universe, [0, 20, 40]
        )
        variable["High"] = fuzz.trimf(
            variable.universe, [20, 40, 40]
        )

    # Hàm thuộc đầu ra.
    green_time["Short"] = fuzz.trimf(
        green_time.universe, [10, 10, 35]
    )
    green_time["Medium"] = fuzz.trimf(
        green_time.universe, [10, 35, 60]
    )
    green_time["Long"] = fuzz.trimf(
        green_time.universe, [35, 60, 60]
    )

    # Tái sử dụng đúng 9 luật từ file đã viết.
    rules = []

    for index, (ns_label, ew_label, output_label) in enumerate(
        RULES, start=1
    ):
        rule = ctrl.Rule(
            antecedent=(
                ns_queue[ns_label] & ew_queue[ew_label]
            ),
            consequent=green_time[output_label],
            label=f"rule_{index}",
            and_func=np.fmin,
        )

        rules.append(rule)

    return ctrl.ControlSystem(rules)


# Chỉ xây cấu trúc bộ điều khiển một lần khi import file.
CONTROLLER = build_controller()


def validate_queue(value: float, name: str) -> float:
    """Kiểm tra đầu vào và chặn trên tại 40 xe."""

    value = float(value)

    if not math.isfinite(value) or value < 0:
        raise ValueError(
            f"{name} phải là số hữu hạn, không âm."
        )

    return min(value, 40.0)


def fuzzy_green_time(
    ns_queue: float,
    ew_queue: float,
) -> float:
    """
    Input:
        ns_queue: tổng số xe chờ Bắc–Nam.
        ew_queue: tổng số xe chờ Đông–Tây.

    Output:
        Thời gian xanh Bắc–Nam, đơn vị giây.
    """

    ns = validate_queue(ns_queue, "ns_queue")
    ew = validate_queue(ew_queue, "ew_queue")

    simulation = ctrl.ControlSystemSimulation(
        CONTROLLER,
        cache=False,
    )

    simulation.input["ns_queue"] = ns
    simulation.input["ew_queue"] = ew

    simulation.compute()

    return float(simulation.output["green_time"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cases = [
        (30, 5),
        (5, 30),
        (20, 20),
        (40, 0),
        (0, 40),
        (0, 0),
    ]

    for ns, ew in cases:
        seconds = fuzzy_green_time(ns, ew)

        print(
            f"NS={ns:>2}, EW={ew:>2}"
            f" → xanh Bắc–Nam: {seconds:.2f} giây"
        )
