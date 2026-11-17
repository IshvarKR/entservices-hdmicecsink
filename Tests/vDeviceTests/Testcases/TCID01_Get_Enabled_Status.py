from utils import require_boolean_field, require_success_value


def run_test():
    method = "org.rdk.HdmiCecSink.getEnabled"
    result = require_success_value("getEnabled")
    require_boolean_field(result, "enabled", method)
    return True
