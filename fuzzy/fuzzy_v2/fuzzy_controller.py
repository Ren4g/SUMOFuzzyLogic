
import math
import sys
from functools import lru_cache

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


# Chọn trên seed 1 của 3 kịch bản; kiểm tra riêng trên seed 11 và 23.
# Đây là tham số tốt nhất trong các ứng viên thích nghi đã thử, không phải tối ưu toàn cục.
MIN_GREEN = 10.0
MAX_GREEN = 60.0
ACTIVITY_QUEUE = 20.0
WAIT_REFERENCE = 60.0
MAX_WAIT_ADJUSTMENT = 10.0


def validate_queue(value: float, name: str) -> float:
    """Kiểm tra đầu vào, KHÔNG cắt riêng từng hướng tại 40 xe."""
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} phải là số hữu hạn, không âm.")
    return value


def normalize_queues(ns_queue, ew_queue):
    """Đưa cả hai hướng vào [0, 40] và giữ tỷ lệ giữa chúng."""
    ns = validate_queue(ns_queue, "ns_queue")
    ew = validate_queue(ew_queue, "ew_queue")
    scale = 40.0 / max(40.0, ns, ew)
    return ns * scale, ew * scale


@lru_cache(maxsize=4096)
def _mamdani(normalized_ns: float, normalized_ew: float) -> float:
    """Lõi 9 luật cũ; nhớ tối đa 4096 cặp để giảm tính lặp."""
    simulation = ctrl.ControlSystemSimulation(CONTROLLER, cache=False)
    simulation.input["ns_queue"] = normalized_ns
    simulation.input["ew_queue"] = normalized_ew
    simulation.compute()
    return float(simulation.output["green_time"])


def fuzzy_green_time(
    ns_queue: float,
    ew_queue: float,
    own_wait: float = 0.0,
    other_wait: float = 0.0,
) -> float:
    """Trả về số giây xanh cho hướng của tham số THỨ NHẤT.

    Giữ nguyên cách gọi cũ: fuzzy_green_time(ns_queue, ew_queue).
    Hai đầu vào là tổng xe ĐANG CHỜ, không phải mọi xe trên đường.
    own_wait/other_wait tùy chọn: số giây chờ lâu nhất mỗi nhóm.
    Không tự đọc SUMO, không đổi pha, không lưu trạng thái giao thông.
    Chỉ gọi để chọn thời lượng khi BẮT ĐẦU pha xanh chính.
    """
    ns = validate_queue(ns_queue, "ns_queue")
    ew = validate_queue(ew_queue, "ew_queue")
    own_wait = validate_queue(own_wait, "own_wait")
    other_wait = validate_queue(other_wait, "other_wait")

    if ns == 0:
        return MIN_GREEN

    normalized_ns, normalized_ew = normalize_queues(ns, ew)
    raw_green = _mamdani(normalized_ns, normalized_ew)

    # Giảm xanh khi ít xe; vẫn giữ tác động của lõi fuzzy.
    activity = min(ns / ACTIVITY_QUEUE, 1.0)
    green = MIN_GREEN + activity * (raw_green - MIN_GREEN)

    # Chỉ có tác dụng nếu chương trình tích hợp truyền thời gian chờ.
    own_urgency = min(own_wait / WAIT_REFERENCE, 1.0)
    other_urgency = min(other_wait / WAIT_REFERENCE, 1.0) if ew > 0 else 0.0
    green += MAX_WAIT_ADJUSTMENT * (own_urgency - other_urgency)

    return float(max(MIN_GREEN, min(MAX_GREEN, green)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'Own':>6} {'Other':>6} {'Xanh V2 (s)':>14}")
    for own, other in [(0,0), (0,20), (1,1), (5,5), (20,20),
                       (30,5), (5,30), (80,40), (40,80)]:
        print(f"{own:>6} {other:>6} {fuzzy_green_time(own, other):>14.2f}")
