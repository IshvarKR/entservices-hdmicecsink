from utils import require_string_field, require_success_value


def run_test():
    method = "org.rdk.HdmiCecSink.getVendorId"
    result = require_success_value("getVendorId")
    vendor_id = require_string_field(result, "vendorid", method)
    try:
        int(vendor_id, 16)
    except ValueError as exc:
        raise ValueError(f"{method}: vendorid is not hexadecimal: {vendor_id!r}") from exc
    return True
