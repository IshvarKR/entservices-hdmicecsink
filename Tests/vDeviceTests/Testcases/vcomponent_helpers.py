from utils import (
    JsonRpcError,
    log_info,
    log_warning,
    send_vcomponent_command,
    wait_for_result,
)


TEST_PLAYBACK_LOGICAL_ADDRESS = 4
TEST_PLAYBACK_PHYSICAL_ADDRESS = "1.0.0.0"


def post_fixture(yaml_filename):
    http_status, body = send_vcomponent_command(yaml_filename)
    if http_status == 0:
        log_warning(f"Posted {yaml_filename}; validating its effect through JSON-RPC")
    else:
        log_info(f"Posted {yaml_filename}: HTTP {http_status} {body}")


def prepare_test_playback_source(active=False):
    post_fixture("Device_Config_Sink_Test.yaml")
    post_fixture("Process_Report_Physical_Address.yaml")
    if active:
        post_fixture("Process_Active_Source.yaml")


def prepare_test_audio_system():
    post_fixture("Device_Config_Sink_Test.yaml")
    post_fixture("Process_Report_Physical_Address_Audio_System.yaml")


def find_device(result, logical_address):
    devices = result.get("deviceList")
    if devices is None:
        return None
    if not isinstance(devices, list):
        raise JsonRpcError("getDeviceList: deviceList must be an array or null")

    for index, device in enumerate(devices):
        if not isinstance(device, dict):
            raise JsonRpcError(f"getDeviceList: deviceList[{index}] is not an object")
        if device.get("logicalAddress") == logical_address:
            return device
    return None


def wait_for_device(logical_address, predicate, expected):
    method = "org.rdk.HdmiCecSink.getDeviceList"

    def matches(result):
        device = find_device(result, logical_address)
        return device is not None and predicate(device)

    return wait_for_result(
        method,
        matches,
        expected,
    )


def wait_for_active_source():
    method = "org.rdk.HdmiCecSink.getActiveSource"
    return wait_for_result(
        method,
        lambda result: (
            result.get("available") is True
            and result.get("logicalAddress") == TEST_PLAYBACK_LOGICAL_ADDRESS
            and result.get("physicalAddress") == TEST_PLAYBACK_PHYSICAL_ADDRESS
        ),
        "the test playback device as active source",
    )


def wait_for_active_route():
    method = "org.rdk.HdmiCecSink.getActiveRoute"
    return wait_for_result(
        method,
        lambda result: result.get("available") is True,
        "an available active route",
    )


def wait_for_audio_device_connected():
    method = "org.rdk.HdmiCecSink.getAudioDeviceConnectedStatus"
    return wait_for_result(
        method,
        lambda result: result.get("connected") is True,
        "an audio device connection",
    )
