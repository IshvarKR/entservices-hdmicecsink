from utils import require_success_value


def run_test():
    require_success_value("setMenuLanguage", {"language": "chi"})
    return True
