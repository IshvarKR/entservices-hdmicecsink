from utils import (
    JsonRpcError,
    require_string_field,
    require_success_value,
)


def run_test():
    get_method = "org.rdk.HdmiCecSink.getOSDName"
    original_name = require_string_field(
        require_success_value("getOSDName"), "name", get_method
    )
    test_name = "Fire TV Stick"

    try:
        require_success_value("setOSDName", {"name": test_name})
        actual_name = require_string_field(
            require_success_value("getOSDName"), "name", get_method
        )
        if actual_name != test_name:
            raise JsonRpcError(
                f"setOSDName read back {actual_name!r}, expected {test_name!r}"
            )
    finally:
        require_success_value("setOSDName", {"name": original_name})
        restored_name = require_string_field(
            require_success_value("getOSDName"), "name", get_method
        )
        if restored_name != original_name:
            raise JsonRpcError("OSD name did not restore to its original value")
    return True
