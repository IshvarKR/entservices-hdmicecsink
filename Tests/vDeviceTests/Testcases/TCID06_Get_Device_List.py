from utils import (
    JsonRpcError,
    require_integer_field,
)
from vcomponent_helpers import (
    find_device,
    post_fixture,
    prepare_test_playback_source,
    wait_for_device,
)


def _has_test_device_metadata(device):
    if (
        device.get("physicalAddress") != "1.0.0.0"
        or device.get("osdName") != "BOX"
    ):
        return False
    vendor_id = device.get("vendorID")
    try:
        return int(vendor_id, 16) == 0x0019FB
    except (TypeError, ValueError):
        return False


def run_test():
    method = "org.rdk.HdmiCecSink.getDeviceList"
    prepare_test_playback_source()
    post_fixture("Process_Set_OSD_Name.yaml")
    post_fixture("Process_Device_Vendor_ID.yaml")
    result = wait_for_device(
        4,
        _has_test_device_metadata,
        "logical address 4 with the expected physical address, OSD name, and vendor ID",
    )
    count = require_integer_field(result, "numberofdevices", method)
    if count < 0:
        raise JsonRpcError(f"{method}: numberofdevices cannot be negative")

    devices = result.get("deviceList")
    if not isinstance(devices, list):
        raise JsonRpcError(f"{method}: deviceList must be an array")
    if len(devices) < count:
        raise JsonRpcError(
            f"{method}: deviceList has {len(devices)} entries for count {count}"
        )
    if find_device(result, 4) is None:
        raise JsonRpcError(f"{method}: the vComponent playback device was not listed")

    for index, device in enumerate(devices):
        if not isinstance(device, dict):
            raise JsonRpcError(f"{method}: deviceList[{index}] is not an object")
        if type(device.get("logicalAddress")) is not int:
            raise JsonRpcError(
                f"{method}: deviceList[{index}] has no integer logicalAddress"
            )
    return True
