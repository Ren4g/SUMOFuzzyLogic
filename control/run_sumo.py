import argparse
import glob
import os
import sys

if "SUMO_HOME" not in os.environ:
    sys.exit("Chưa đặt biến môi trường SUMO_HOME")
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import sumolib
import traci

from read_traffic import get_light_state, get_queues
from control_traffic_light import print_program, set_fixed_timing
from fuzzy_phase_controller import FuzzyPhaseController

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import csv
import xml.etree.ElementTree as ET
from datetime import datetime

RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
STEP_LENGTH = 0.1


def find_config(scenario):
    folder = os.path.join(PROJECT_DIR, "sumo", scenario)
    files = glob.glob(os.path.join(folder, "*.sumocfg"))
    if len(files) != 1:
        sys.exit(f"Cần đúng 1 file .sumocfg trong {folder}, tìm thấy: {files}")
    return files[0]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="4huong3lan", help="tên thư mục trong sumo/")
    ap.add_argument("--mode", choices=["observe", "fixed", "fuzzy"], default="observe")
    ap.add_argument("--green", type=int, default=30)
    ap.add_argument("--yellow", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1, help="SUMO random seed for reproducible comparisons")
    ap.add_argument("--print-every", type=float, default=10, help="giây mô phỏng")
    ap.add_argument("--nogui", action="store_true")
    args = ap.parse_args()

    config = find_config(args.scenario)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    tripinfo_path = os.path.join(
        RESULTS_DIR, f"tripinfo_{args.scenario}_{args.mode}_{run_id}.xml")

    binary = sumolib.checkBinary("sumo" if args.nogui else "sumo-gui")
    cmd = [binary, "-c", config, "--step-length", str(STEP_LENGTH),
           "--tripinfo-output", tripinfo_path, "--seed", str(args.seed),
           "--no-step-log", "true"]
    if not args.nogui:
        cmd += ["--delay", "100", "--start", "--quit-on-end"]

    SAMPLE_INTERVAL = 2.0  # giây mô phỏng giữa hai lần lấy mẫu, giữ như bản cũ để so sánh được
    traci.start(cmd)
    total_waiting = 0.0
    samples = 0
    arrived = 0
    sim_time = 0.0
    try:
        tls_id = traci.trafficlight.getIDList()[0]
        print("Đèn giao thông:", tls_id)
        print_program(tls_id)

        if args.mode == "fixed":
            set_fixed_timing(tls_id, green=args.green, yellow=args.yellow)
            print(f"\nĐã đặt: xanh {args.green} s, vàng {args.yellow} s\n")
            print_program(tls_id)

        fuzzy_control = FuzzyPhaseController(tls_id) if args.mode == "fuzzy" else None
        if fuzzy_control:
            fuzzy_control.apply_current_phase()

        sample_steps = max(1, round(SAMPLE_INTERVAL / traci.simulation.getDeltaT()))
        step = 0
        next_print = 0.0

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1
            arrived += traci.simulation.getArrivedNumber()
            t = traci.simulation.getTime()

            if fuzzy_control:
                fuzzy_control.apply_current_phase()

            # thu số liệu cho phần tổng kết
            if step % sample_steps == 0:
                vehicles = traci.vehicle.getIDList()
                total_waiting += sum(traci.vehicle.getWaitingTime(v) for v in vehicles)
                samples += len(vehicles)

            # in chi tiết (tùy chọn)
            if args.print_every > 0 and t >= next_print:
                light = get_light_state(tls_id)
                queues = {k: v for k, v in get_queues(tls_id).items() if v > 0}
                print(f"t={t:6.1f}  pha={light['phase']}  {light['state']}  "
                    f"còn {light['remaining']}s  hàng chờ={queues}")
                next_print += args.print_every

        sim_time = traci.simulation.getTime()
    finally:
        traci.close()

    print("\n=== Tổng kết ===")
    print(f"Thời gian mô phỏng: {sim_time:.0f} s")
    print(f"Số xe đã đi qua hết mạng: {arrived}")
    
    trip = read_tripinfo(tripinfo_path)
    if trip:
        print(f"Thời gian chờ trung bình mỗi xe: {trip['avg_wait']:.2f} s")
        print(f"Thời gian mất mát trung bình mỗi xe: {trip['avg_time_loss']:.2f} s")

    row = {
        "run_id": run_id,
        "scenario": args.scenario,
        "mode": args.mode,
        "green": args.green if args.mode == "fixed" else "",
        "yellow": args.yellow if args.mode == "fixed" else "",
        "seed": args.seed,
        "step_length": STEP_LENGTH,
        "sim_time": round(sim_time),
        "vehicles": trip["vehicles"] if trip else "",
        "avg_wait_per_vehicle": round(trip["avg_wait"], 2) if trip else "",
        "avg_time_loss": round(trip["avg_time_loss"], 2) if trip else "",
        "avg_trip_duration": round(trip["avg_duration"], 2) if trip else "",
        "avg_wait_sampled": round(total_waiting / samples, 2) if samples else "",
    }
    print("Đã lưu kết quả vào:", save_row(row))
    if trip:
        from evaluation.run_evaluation import evaluate_tripinfo

        evaluation_paths = evaluate_tripinfo(
            tripinfo_path=tripinfo_path,
            scenario=args.scenario,
            controller={"observe": "sumo_default", "fixed": "fixed_time", "fuzzy": "fuzzy"}[args.mode],
            run_id=run_id,
            seed=args.seed,
            simulation_duration=sim_time,
            output_dir=os.path.join(PROJECT_DIR, "results", "evaluation"),
        )
        print("Đã lưu dữ liệu đánh giá:", evaluation_paths["summary"])
    if samples:
        print(f"Thời gian chờ trung bình mỗi mẫu xe: {total_waiting / samples:.2f} s")

def read_tripinfo(path):
    """Đọc file tripinfo của SUMO, trả về số liệu trung bình theo từng xe."""
    if not os.path.exists(path):
        return None
    waits, losses, durations = [], [], []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "tripinfo":
            waits.append(float(el.get("waitingTime")))
            losses.append(float(el.get("timeLoss")))
            durations.append(float(el.get("duration")))
            el.clear()
    n = len(waits)
    if n == 0:
        return None
    return {
        "vehicles": n,
        "avg_wait": sum(waits) / n,
        "avg_time_loss": sum(losses) / n,
        "avg_duration": sum(durations) / n,
    }


def save_row(row):
    path = os.path.join(RESULTS_DIR, "results.csv")
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new_file:
            w.writeheader()
        w.writerow(row)
    return path

if __name__ == "__main__":
    main()
