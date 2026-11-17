from utils import require_success_value


def run_test():
    require_success_value(
        "setLatencyInfo",
        {
            "videoLatency": "2",
            "lowLatencyMode": "1",
            "audioOutputCompensated": "1",
            "audioOutputDelay": "20",
        },
    )
    return True
