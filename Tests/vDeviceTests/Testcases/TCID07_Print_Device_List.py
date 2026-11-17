from utils import require_boolean_field, require_success_value


def run_test():
    method = "org.rdk.HdmiCecSink.printDeviceList"
    result = require_success_value("printDeviceList")
    if require_boolean_field(result, "printed", method) is not True:
        raise ValueError(f"{method}: printed was not true")
    return True
