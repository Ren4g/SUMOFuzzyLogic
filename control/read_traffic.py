import traci


def get_lanes(tls_id):
    """Các làn đi vào nút giao do đèn này điều khiển (đã bỏ trùng)."""
    return list(dict.fromkeys(traci.trafficlight.getControlledLanes(tls_id)))


def get_queue(lane_id):
    """Số xe đang chờ (tốc độ < 0.1 m/s) trên một làn, ở bước vừa rồi."""
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_queues(tls_id):
    return {lane: get_queue(lane) for lane in get_lanes(tls_id)}


def get_light_state(tls_id):
    now = traci.simulation.getTime()
    return {
        "phase": traci.trafficlight.getPhase(tls_id),
        "state": traci.trafficlight.getRedYellowGreenState(tls_id),
        "remaining": round(traci.trafficlight.getNextSwitch(tls_id) - now, 1),
    }