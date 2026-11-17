from utils import (
    JsonRpcError,
    get_cec_enabled,
    require_success_value,
)


def run_test():
    original_state = get_cec_enabled()
    try:
        for expected_state in (False, True):
            require_success_value("setEnabled", {"enabled": expected_state})
            actual_state = get_cec_enabled()
            if actual_state is not expected_state:
                raise JsonRpcError(
                    f"setEnabled({expected_state}) read back {actual_state}"
                )
    finally:
        require_success_value("setEnabled", {"enabled": original_state})
        restored_state = get_cec_enabled()
        if restored_state is not original_state:
            raise JsonRpcError(
                f"CEC enabled state did not restore to {original_state}"
            )
    return True
