from utils import require_boolean_field
from vcomponent_helpers import prepare_test_playback_source, wait_for_active_route


def run_test():
    method = "org.rdk.HdmiCecSink.getActiveRoute"
    prepare_test_playback_source(active=True)
    result = wait_for_active_route()
    require_boolean_field(result, "available", method)
    return True
