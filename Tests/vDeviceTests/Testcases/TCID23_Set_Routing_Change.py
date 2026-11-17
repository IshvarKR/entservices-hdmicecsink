from utils import require_success_value


def run_test():
    require_success_value(
        "setRoutingChange",
        {"oldPort": "HDMI0", "newPort": "TV"},
    )
    return True
