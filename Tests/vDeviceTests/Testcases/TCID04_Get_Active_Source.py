from utils import require_boolean_field, require_integer_field, require_string_field
from vcomponent_helpers import prepare_test_playback_source, wait_for_active_source


def run_test():
    method = "org.rdk.HdmiCecSink.getActiveSource"
    prepare_test_playback_source(active=True)
    result = wait_for_active_source()
    if require_boolean_field(result, "available", method) is not True:
        raise ValueError(f"{method}: expected the test source to be available")
    logical_address = require_integer_field(result, "logicalAddress", method)
    if logical_address != 4:
        raise ValueError(f"{method}: expected logical address 4, got {logical_address}")
    physical_address = require_string_field(result, "physicalAddress", method)
    if physical_address != "1.0.0.0":
        raise ValueError(
            f"{method}: expected physical address '1.0.0.0', got {physical_address!r}"
        )
    return True
