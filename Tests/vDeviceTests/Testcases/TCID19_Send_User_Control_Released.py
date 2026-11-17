from utils import require_success_value


def run_test():
    require_success_value(
        "sendUserControlReleased",
        {"logicalAddress": 4},
    )
    return True
