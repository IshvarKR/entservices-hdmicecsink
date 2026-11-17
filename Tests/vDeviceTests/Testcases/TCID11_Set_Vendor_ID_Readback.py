from utils import (
    JsonRpcError,
    require_string_field,
    require_success_value,
)


def _read_vendor_id():
    method = "org.rdk.HdmiCecSink.getVendorId"
    result = require_success_value("getVendorId")
    value = require_string_field(result, "vendorid", method)
    try:
        return int(value, 16)
    except ValueError as exc:
        raise JsonRpcError(f"{method}: vendorid is not hexadecimal: {value!r}") from exc


def run_test():
    original_vendor_id = _read_vendor_id()
    test_vendor_id = "0x0018FB"
    expected_value = int(test_vendor_id, 16)

    try:
        require_success_value("setVendorId", {"vendorid": test_vendor_id})
        actual_value = _read_vendor_id()
        if actual_value != expected_value:
            raise JsonRpcError(
                f"setVendorId read back 0x{actual_value:06x}, "
                f"expected 0x{expected_value:06x}"
            )
    finally:
        require_success_value(
            "setVendorId", {"vendorid": f"0x{original_vendor_id:06x}"}
        )
        restored_value = _read_vendor_id()
        if restored_value != original_vendor_id:
            raise JsonRpcError("vendor ID did not restore to its original value")
    return True
