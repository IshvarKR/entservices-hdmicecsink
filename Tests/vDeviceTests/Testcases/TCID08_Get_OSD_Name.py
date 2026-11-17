from utils import require_string_field, require_success_value


def run_test():
    method = "org.rdk.HdmiCecSink.getOSDName"
    result = require_success_value("getOSDName")
    require_string_field(result, "name", method)
    return True
