from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np

from membership_functions import queue_membership, green_membership
from fuzzy_controller import fuzzy_green_time, RULES

def evaluate_rules(ns_queue: float, ew_queue: float) -> dict:
    """Tính mức kích hoạt các tập đầu ra để minh họa."""

    ns = queue_membership(ns_queue)
    ew = queue_membership(ew_queue)

    strengths = {
        "Short": 0.0,
        "Medium": 0.0,
        "Long": 0.0,
    }

    for ns_label, ew_label, output_label in RULES:
        strength = min(
            ns[ns_label],
            ew[ew_label],
        )

        strengths[output_label] = max(
            strengths[output_label],
            strength,
        )

    return {"output_strengths": strengths}
def aggregated_membership(
    seconds: float,
    strengths: dict[str, float],
) -> float:
    """Tính độ cao đường đầu ra sau cắt–gộp tại một thời gian."""

    membership = green_membership(seconds)

    short_cut = min(
        strengths["Short"],
        membership["Short"],
    )

    medium_cut = min(
        strengths["Medium"],
        membership["Medium"],
    )

    long_cut = min(
        strengths["Long"],
        membership["Long"],
    )

    return max(short_cut, medium_cut, long_cut)
def plot_control_surface():
    # 21 giá trị: 0, 2, 4, ..., 40.
    queue_values = np.linspace(0, 40, 21)

    # Tạo tất cả tổ hợp số xe của hai hướng.
    ns_grid, ew_grid = np.meshgrid(queue_values, queue_values)

    # Mỗi ô sẽ chứa thời gian xanh tương ứng.
    green_grid = np.zeros_like(ns_grid)

    total = ns_grid.size

    print(f"Đang tính {total} cặp đầu vào...")

    for i in range(len(queue_values)):
        for j in range(len(queue_values)):
            ns = float(ns_grid[i, j])
            ew = float(ew_grid[i, j])

            green_grid[i, j] = fuzzy_green_time(ns, ew)

        print(f"Đã tính xong hàng {i + 1}/{len(queue_values)}")

    # Kiểm tra trước khi vẽ.
    if not np.all(np.isfinite(green_grid)):
        raise ValueError("Có kết quả không hữu hạn.")

    if np.any((green_grid < 10) | (green_grid > 60)):
        raise ValueError("Có kết quả vượt miền 10–60 giây.")

    output_dir = Path(__file__).resolve().parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 6), layout="constrained")

    # ----- Bên trái: bề mặt 3D -----
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")

    ax3d.plot_surface(
        ns_grid,
        ew_grid,
        green_grid,
        cmap="viridis",
        vmin=10,
        vmax=60,
        edgecolor="none",
        alpha=0.9,
    )

    # Đánh dấu ví dụ đã học.
    example_green = fuzzy_green_time(30, 5)

    ax3d.scatter(
        30,
        5,
        example_green,
        color="red",
        s=55,
        depthshade=False,
    )

    ax3d.set_title("Control Surface")
    ax3d.set_xlabel("Bắc–Nam (xe)")
    ax3d.set_ylabel("Đông–Tây (xe)")
    ax3d.set_zlabel("Xanh Bắc–Nam (giây)")
    ax3d.set_zlim(10, 60)
    ax3d.view_init(elev=25, azim=-135)

    # ----- Bên phải: bản đồ màu 2D -----
    ax2d = fig.add_subplot(1, 2, 2)

    heatmap = ax2d.pcolormesh(
        ns_grid,
        ew_grid,
        green_grid,
        shading="auto",
        cmap="viridis",
        vmin=10,
        vmax=60,
    )

    ax2d.set_xlim(0, 40)
    ax2d.set_ylim(0, 40)
    ax2d.set_aspect("equal")

    # Đường chéo: hai hướng có cùng số xe.
    ax2d.plot(
        [0, 40],
        [0, 40],
        color="white",
        linestyle="--",
        label="NS = EW",
    )

    ax2d.scatter(30, 5, color="red", s=45)

    ax2d.annotate(
        f"(30, 5): {example_green:.2f} giây",
        xy=(30, 5),
        xytext=(12, 10),
        textcoords="offset points",
        fontsize=9,
        color="black",
        bbox={"facecolor": "white", "alpha": 0.85},
    )

    ax2d.set_title("Bản đồ thời gian xanh")
    ax2d.set_xlabel("Bắc–Nam (xe)")
    ax2d.set_ylabel("Đông–Tây (xe)")
    ax2d.legend(loc="upper left")

    fig.colorbar(
        heatmap,
        ax=ax2d,
        label="Thời gian xanh Bắc–Nam (giây)",
        shrink=0.85,
    )

    # Lưu hình.
    image_path = output_dir / "control_surface.png"
    fig.savefig(image_path, dpi=200, bbox_inches="tight")

    # Lưu số liệu để kiểm tra hoặc dùng trong báo cáo.
    data = np.column_stack([
        ns_grid.ravel(),
        ew_grid.ravel(),
        green_grid.ravel(),
    ])

    csv_path = output_dir / "control_surface.csv"

    np.savetxt(
        csv_path,
        data,
        delimiter=",",
        header="ns_queue,ew_queue,green_time",
        comments="",
        fmt="%.6f",
    )

    print(f"\nNhỏ nhất trên lưới: {green_grid.min():.2f} giây")
    print(f"Lớn nhất trên lưới: {green_grid.max():.2f} giây")
    print(f"Đã lưu hình: {image_path}")
    print(f"Đã lưu dữ liệu: {csv_path}")

    plt.show()

def plot_fuzzy_process(ns_queue, ew_queue):
    # Tính kết quả bằng các hàm đã viết.
    result = evaluate_rules(ns_queue, ew_queue)
    strengths = result["output_strengths"]
    green_time = fuzzy_green_time(ns_queue, ew_queue)

    # Các điểm dùng để vẽ đường.
    queue_values = [i / 10 for i in range(401)]       # 0 → 40
    time_values = [10 + i / 100 for i in range(5001)] # 10 → 60

    input_colors = {
        "Low": "tab:blue",
        "Medium": "tab:orange",
        "High": "tab:green",
    }

    output_colors = {
        "Short": "tab:blue",
        "Medium": "tab:orange",
        "Long": "tab:green",
    }

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # Biểu đồ 1 và 2: hai đầu vào.
    input_plots = [
        (axes[0, 0], ns_queue, "Bắc–Nam"),
        (axes[0, 1], ew_queue, "Đông–Tây"),
    ]

    for ax, queue, direction in input_plots:
        memberships = queue_membership(queue)
        effective_queue = min(float(queue), 40.0)

        for label, color in input_colors.items():
            y = [
                queue_membership(x)[label]
                for x in queue_values
            ]

            ax.plot(queue_values, y, color=color, label=label)

            # Đánh dấu các mức thuộc khác 0 của đầu vào.
            degree = memberships[label]

            if degree > 0:
                ax.scatter(
                    effective_queue,
                    degree,
                    color=color,
                    s=65,
                    zorder=5,
                )

        ax.axvline(
            effective_queue,
            color="black",
            linestyle="--",
            label=f"Giá trị dùng tính: {effective_queue:g}",
        )

        values_text = ", ".join(
            f"{label}={degree:.2f}"
            for label, degree in memberships.items()
        )

        ax.set_title(f"{direction}: {queue:g} xe\n{values_text}")
        ax.set_xlabel("Số xe đang chờ")
        ax.set_ylabel("Mức độ thuộc")
        ax.set_xlim(0, 40)

    # Biểu đồ 3: hàm thuộc đầu ra gốc và sau khi cắt.
    ax = axes[1, 0]

    for label, color in output_colors.items():
        original = [
            green_membership(t)[label]
            for t in time_values
        ]

        clipped = [
            min(strengths[label], value)
            for value in original
        ]

        # Nét đứt: hình ban đầu.
        ax.plot(
            time_values,
            original,
            color=color,
            linestyle="--",
            alpha=0.45,
        )

        # Nét liền: hình sau khi cắt.
        ax.plot(
            time_values,
            clipped,
            color=color,
            linewidth=2,
            label=f"{label}: cắt tại {strengths[label]:.2f}",
        )

    ax.set_title("Đầu ra: nét đứt là gốc, nét liền là sau cắt")
    ax.set_xlabel("Thời gian xanh Bắc–Nam (giây)")
    ax.set_ylabel("Mức độ thuộc")
    ax.set_xlim(10, 60)

    # Biểu đồ 4: vùng tổng hợp và trọng tâm.
    ax = axes[1, 1]

    aggregated = [
        aggregated_membership(t, strengths)
        for t in time_values
    ]

    ax.plot(
        time_values,
        aggregated,
        color="tab:purple",
        label="Đường tổng hợp bằng max",
    )

    ax.fill_between(
        time_values,
        0,
        aggregated,
        color="tab:purple",
        alpha=0.25,
    )

    ax.axvline(
        green_time,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Trọng tâm: {green_time:.2f} giây",
    )

    ax.set_title("Vùng tổng hợp và kết quả giải mờ")
    ax.set_xlabel("Thời gian xanh Bắc–Nam (giây)")
    ax.set_ylabel("Mức độ thuộc")
    ax.set_xlim(10, 60)

    # Định dạng chung.
    for ax in axes.flat:
        ax.set_ylim(-0.05, 1.08)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle(
        f"Mamdani: NS={ns_queue:g}, EW={ew_queue:g}"
        f" → xanh Bắc–Nam {green_time:.2f} giây",
        fontsize=14,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.95))

    # Lưu ảnh vào thư mục fuzzy/figures.
    output_dir = Path(__file__).resolve().parent / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / (
        f"fuzzy_process_ns_{ns_queue:g}_ew_{ew_queue:g}.png"
    )

    fig.savefig(output_path, dpi=200, bbox_inches="tight")

    print(f"Thời gian xanh Bắc–Nam: {green_time:.2f} giây")
    print(f"Đã lưu ảnh: {output_path}")

    plt.show()


def test_controller():
    # Kết quả tham chiếu của thiết kế hiện tại.
    # Đây không phải kết quả thực nghiệm giao thông.
    cases = [
        (30, 5, 40.4166667),
        (5, 30, 29.5833333),
        (20, 20, 35.0),
        (40, 0, 51.6666667),
        (0, 40, 18.3333333),
        (0, 0, 35.0),
    ]

    print(
        f"{'NS':>6} {'EW':>6}"
        f" {'Kết quả':>12} {'Tham chiếu':>12}"
    )

    for ns, ew, expected in cases:
        actual = fuzzy_green_time(ns, ew)

        print(
            f"{ns:>6} {ew:>6}"
            f" {actual:>12.4f} {expected:>12.4f}"
        )

        assert math.isfinite(actual), (
            f"Kết quả không hữu hạn tại ({ns}, {ew})."
        )

        assert 10 <= actual <= 60, (
            f"Kết quả vượt miền tại ({ns}, {ew})."
        )

        assert abs(actual - expected) < 0.02, (
            f"Kết quả khác tham chiếu tại ({ns}, {ew})."
        )

    # Kiểm tra quy ước chặn trên tại 40 xe ở cả hai đầu vào.
    assert abs(
        fuzzy_green_time(65, 5)
        - fuzzy_green_time(40, 5)
    ) < 1e-9

    assert abs(
        fuzzy_green_time(5, 65)
        - fuzzy_green_time(5, 40)
    ) < 1e-9

    # Kiểm tra đầu vào không hợp lệ.
    for invalid in [-1, float("nan"), float("inf")]:
        for ns, ew in [(invalid, 5), (5, invalid)]:
            try:
                fuzzy_green_time(ns, ew)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    f"Chưa từ chối đầu vào ({ns}, {ew})."
                )

    print("\nĐã vượt qua các kiểm tra.")

if __name__ == "__main__":
    test_controller()
    plot_fuzzy_process(5, 40)
    plot_control_surface()