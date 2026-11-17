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
    green_counts = [sum(char in "gG" for char in ph.state) for ph in logic.phases]
    largest = max(green_counts, default=0)
    main_phases = {
        index for index, count in enumerate(green_counts)
        if count == largest and count > 0
    }
    if len(main_phases) != 2:
        raise RuntimeError(
            f"Expected two dominant green phases for {tls_id!r}, "
            f"found {len(main_phases)}."
        )

    for index, ph in enumerate(logic.phases):
        kind = phase_kind(ph.state)
        if kind == "yellow":
            ph.duration = yellow
        elif kind == "red":
            ph.duration = all_red
        elif index in main_phases:
            ph.duration = green
    traci.trafficlight.setProgramLogic(tls_id, logic)
