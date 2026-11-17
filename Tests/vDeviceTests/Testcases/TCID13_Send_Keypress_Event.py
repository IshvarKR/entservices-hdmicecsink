from utils import require_success_value


def run_test():
    require_success_value(
        "sendKeyPressEvent",
        {"logicalAddress": 0, "keyCode": 9},
    )
    return True
