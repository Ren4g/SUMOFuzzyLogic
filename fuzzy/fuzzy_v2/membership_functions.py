def queue_membership(queue: float) -> dict[str, float]:
    """Tính mức thuộc Low, Medium, High của số xe đang chờ."""

    # Chuyển đầu vào thành số thực.
    queue = float(queue)

    # Số xe phải hữu hạn và không âm.
    if not 0 <= queue < float("inf"):
        raise ValueError("Số xe phải là số hữu hạn, không âm.")

    # Bản đầu coi từ 40 xe trở lên là mức đông tối đa.
    x = min(queue, 40.0)

    if x <= 20:
        low = (20 - x) / 20
        medium = x / 20
        high = 0.0
    else:
        low = 0.0
        medium = (40 - x) / 20
        high = (x - 20) / 20

    return {
        "Low": low,
        "Medium": medium,
        "High": high,
    }

def green_membership(seconds: float) -> dict[str, float]:
    """Mức thuộc Short, Medium, Long của một thời gian xanh."""

    t = float(seconds)

    if not 10 <= t <= 60:
        raise ValueError("Thời gian phải nằm trong khoảng 10–60 giây.")

    if t <= 35:
        short = (35 - t) / 25
        medium = (t - 10) / 25
        long = 0.0
    else:
        short = 0.0
        medium = (60 - t) / 25
        long = (t - 35) / 25

    return {
        "Short": short,
        "Medium": medium,
        "Long": long,
    }
    
if __name__ == "__main__":
    test_values = [0, 5, 10, 15, 20, 25, 30, 35, 40, 65]

    print(f"{'Số xe':>6} {'Low':>8} {'Medium':>8} {'High':>8}")

    for queue in test_values:
        result = queue_membership(queue)

        print(
            f"{queue:>6}"
            f" {result['Low']:>8.2f}"
            f" {result['Medium']:>8.2f}"
            f" {result['High']:>8.2f}"
        )