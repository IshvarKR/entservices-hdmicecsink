from utils import require_success_value


def run_test():
    require_success_value("setActivePath", {"activePath": "1.0.0.0"})
    return True
