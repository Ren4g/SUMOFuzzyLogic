import traci


def phase_kind(state):
    s = state.lower()
    if "y" in s:
        return "yellow"
    if "g" in s:
        return "green"
    return "red"  # pha đỏ toàn bộ


def print_program(tls_id):
    logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
    print(f"Chương trình đèn '{logic.programID}', kiểu type={logic.type}")
    for i, ph in enumerate(logic.phases):
        print(f"  pha {i}: {ph.duration:>4} s  {ph.state}  ({phase_kind(ph.state)})")


def set_fixed_timing(tls_id, green=30, yellow=3, all_red=2):
    """Đặt thời gian cố định (giây) cho từng loại pha của đèn."""
    logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
    durations = {"green": green, "yellow": yellow, "red": all_red}
    for ph in logic.phases:
        ph.duration = durations[phase_kind(ph.state)]
    traci.trafficlight.setProgramLogic(tls_id, logic)