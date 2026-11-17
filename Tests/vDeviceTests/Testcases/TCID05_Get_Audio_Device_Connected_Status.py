from utils import require_boolean_field
from vcomponent_helpers import prepare_test_audio_system, wait_for_audio_device_connected


def run_test():
    method = "org.rdk.HdmiCecSink.getAudioDeviceConnectedStatus"
    prepare_test_audio_system()
    result = wait_for_audio_device_connected()
    require_boolean_field(result, "connected", method)
    return True
