import glob
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

CONTROL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CONTROL_DIR)
SUMO_DIR = os.path.join(PROJECT_DIR, "sumo")
RUN_SCRIPT = os.path.join(CONTROL_DIR, "run_sumo.py")
SETTINGS_FILE = os.path.join(CONTROL_DIR, "last_settings.json")

DEFAULTS = {
    "scenario": "",
    "mode": "observe",
    "green": 30,
    "yellow": 3,
    "seed": 1,
    "print_every": 0,
    "nogui": False,
}


def list_scenarios():
    """Thư mục con của sumo/ có chứa file .sumocfg."""
    if not os.path.isdir(SUMO_DIR):
        return []
    return [
        d for d in sorted(os.listdir(SUMO_DIR))
        if glob.glob(os.path.join(SUMO_DIR, d, "*.sumocfg"))
    ]


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return {**DEFAULTS, **json.load(f)}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SUMO Fuzzy Traffic - Chạy mô phỏng")
        self.resizable(False, False)
        self.proc = None
        self.log_queue = queue.Queue()

        s = load_settings()
        scenarios = list_scenarios()
        if s["scenario"] not in scenarios:
            s["scenario"] = scenarios[0] if scenarios else ""

        self.var_scenario = tk.StringVar(value=s["scenario"])
        self.var_mode = tk.StringVar(value=s["mode"])
        self.var_green = tk.IntVar(value=s["green"])
        self.var_yellow = tk.IntVar(value=s["yellow"])
        self.var_seed = tk.IntVar(value=s["seed"])
        self.var_print = tk.IntVar(value=s["print_every"])
        self.var_nogui = tk.BooleanVar(value=s["nogui"])

        self._build(scenarios)
        self._on_mode_change()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_log)

    def _build(self, scenarios):
        pad = {"padx": 8, "pady": 4}
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0)

        ttk.Label(frm, text="Kịch bản:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(frm, textvariable=self.var_scenario, values=scenarios,
                     state="readonly", width=22).grid(row=0, column=1, columnspan=2, sticky="w", **pad)

        ttk.Label(frm, text="Chế độ:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Radiobutton(frm, text="Quan sát (giữ đèn gốc)", value="observe",
                        variable=self.var_mode, command=self._on_mode_change
                        ).grid(row=1, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(frm, text="Đèn cố định (nhập giây)", value="fixed",
                        variable=self.var_mode, command=self._on_mode_change
                        ).grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(frm, text="Điều khiển fuzzy", value="fuzzy",
                        variable=self.var_mode, command=self._on_mode_change
                        ).grid(row=3, column=1, columnspan=2, sticky="w", **pad)

        ttk.Label(frm, text="Đèn xanh (s):").grid(row=4, column=0, sticky="w", **pad)
        self.sp_green = ttk.Spinbox(frm, from_=5, to=120, textvariable=self.var_green, width=6)
        self.sp_green.grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Đèn vàng (s):").grid(row=5, column=0, sticky="w", **pad)
        self.sp_yellow = ttk.Spinbox(frm, from_=1, to=10, textvariable=self.var_yellow, width=6)
        self.sp_yellow.grid(row=5, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Seed SUMO:").grid(row=6, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=0, to=99999999, textvariable=self.var_seed, width=10
                    ).grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(frm, text="In chi tiết mỗi (s), 0 = tắt:").grid(row=7, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=0, to=300, textvariable=self.var_print, width=6
                    ).grid(row=7, column=1, sticky="w", **pad)

        ttk.Checkbutton(frm, text="Chạy không GUI (nhanh hơn)", variable=self.var_nogui
                        ).grid(row=8, column=0, columnspan=3, sticky="w", **pad)

        btns = ttk.Frame(frm)
        btns.grid(row=9, column=0, columnspan=3, pady=8)
        self.btn_run = ttk.Button(btns, text="Chạy", command=self._run)
        self.btn_run.pack(side="left", padx=4)
        self.btn_stop = ttk.Button(btns, text="Dừng", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=4)

        self.log = tk.Text(frm, width=80, height=16, state="disabled", wrap="none")
        self.log.grid(row=10, column=0, columnspan=3, padx=8, pady=4)

    def _on_mode_change(self):
        state = "normal" if self.var_mode.get() == "fixed" else "disabled"
        self.sp_green.configure(state=state)
        self.sp_yellow.configure(state=state)

    def _settings(self):
        return {
            "scenario": self.var_scenario.get(),
            "mode": self.var_mode.get(),
            "green": self.var_green.get(),
            "yellow": self.var_yellow.get(),
            "seed": self.var_seed.get(),
            "print_every": self.var_print.get(),
            "nogui": self.var_nogui.get(),
        }

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _run(self):
        try:
            s = self._settings()
        except tk.TclError:
            messagebox.showerror("Lỗi", "Các ô số phải nhập số nguyên hợp lệ.")
            return
        if not s["scenario"]:
            messagebox.showerror("Lỗi", f"Không tìm thấy kịch bản nào trong:\n{SUMO_DIR}")
            return
        if s["mode"] == "fixed" and (s["green"] <= 0 or s["yellow"] <= 0):
            messagebox.showerror("Lỗi", "Thời gian đèn phải lớn hơn 0.")
            return

        save_settings(s)
        cmd = [sys.executable, "-u", RUN_SCRIPT,
               "--scenario", s["scenario"],
               "--mode", s["mode"],
               "--green", str(s["green"]),
               "--yellow", str(s["yellow"]),
               "--seed", str(s["seed"]),
               "--print-every", str(s["print_every"])]
        if s["nogui"]:
            cmd.append("--nogui")

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._append("> " + " ".join(cmd) + "\n\n")

        self.proc = subprocess.Popen(
            cmd, cwd=PROJECT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        threading.Thread(target=self._reader, args=(self.proc,), daemon=True).start()
        self.btn_run.configure(state="disabled")
        self.btn_stop.configure(state="normal")

    def _reader(self, proc):
        for line in proc.stdout:
            self.log_queue.put(line)
        proc.wait()
        self.log_queue.put(f"\n[Kết thúc, mã thoát {proc.returncode}]\n")
        self.log_queue.put(None)

    def _poll_log(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item is None:
                    self.btn_run.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.proc = None
                else:
                    self._append(item)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    def _stop(self):
        if self.proc and self.proc.poll() is None:
            if os.name == "nt":
                # kill cả cây tiến trình để sumo-gui không bị treo lại
                subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"],
                               capture_output=True)
            else:
                self.proc.terminate()

    def _on_close(self):
        self._stop()
        self.destroy()


if __name__ == "__main__":
    Launcher().mainloop()
