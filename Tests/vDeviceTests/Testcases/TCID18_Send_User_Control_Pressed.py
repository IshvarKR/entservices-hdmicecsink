from utils import require_success_value


def run_test():
    require_success_value(
        "sendUserControlPressed",
        {"logicalAddress": 4, "keyCode": 65},
    )
    return True
