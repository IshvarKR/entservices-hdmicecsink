import argparse
import importlib
import os
import sys
import time
from pathlib import Path

from utils import (
    JsonRpcError,
    activate_plugin,
    deactivate_plugin,
    get_cec_enabled,
    log_error,
    log_info,
    log_success,
    require_success_value,
)


BASE_DIR = Path(__file__).resolve().parent
CALLSIGN = "org.rdk.HdmiCecSink"
TEST_MODULES = [
    "TCID01_Get_Enabled_Status",
    "TCID02_Set_Enabled_Roundtrip",
    "TCID03_Get_Active_Route",
    "TCID04_Get_Active_Source",
    "TCID05_Get_Audio_Device_Connected_Status",
    "TCID06_Get_Device_List",
    "TCID07_Print_Device_List",
    "TCID08_Get_OSD_Name",
    "TCID09_Set_OSD_Name_Readback",
    "TCID10_Get_Vendor_ID",
    "TCID11_Set_Vendor_ID_Readback",
    "TCID12_Send_Standby_Message",
    "TCID13_Send_Keypress_Event",
    "TCID14_Request_Active_Source",
    "TCID15_Request_Short_Audio_Descriptor",
    "TCID16_Send_Audio_Device_Power_On_Message",
    "TCID17_Send_Get_Audio_Status_Message",
    "TCID18_Send_User_Control_Pressed",
    "TCID19_Send_User_Control_Released",
    "TCID20_Set_Active_Path",
    "TCID21_Set_Active_Source",
    "TCID22_Set_Menu_Language",
    "TCID23_Set_Routing_Change",
    "TCID24_Set_Latency_Info",
]

PLUGIN_ACTIVATION_DELAY_SECONDS = 6
PLUGIN_DEACTIVATION_DELAY_SECONDS = 1


def load_test_cases(selected_tests=None):
    module_dir = str(BASE_DIR / "Testcases")
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    test_cases = []
    for module_name in TEST_MODULES:
        tcid = module_name.split("_", 1)[0]
        if selected_tests is not None and tcid not in selected_tests:
            continue
        module = importlib.import_module(module_name)
        run_test = getattr(module, "run_test", None)
        if not callable(run_test):
            raise RuntimeError(f"{module_name} does not define run_test()")
        test_cases.append((module_name, run_test))
    return test_cases


def _restore_cec_state(original_state):
    try:
        require_success_value("setEnabled", {"enabled": original_state})
        restored_state = get_cec_enabled()
        if restored_state is not original_state:
            raise JsonRpcError(
                f"CEC enabled state did not restore to {original_state}"
            )
        log_info(f"Restored CEC enabled state to {original_state}")
        return True
    except Exception as exc:
        log_error(f"Could not restore the original CEC enabled state: {exc}")
        return False


def run_suite(selected_tests=None, auto_activate=True):
    try:
        test_cases = load_test_cases(selected_tests)
    except Exception as exc:
        log_error(f"Could not load test cases: {exc}")
        return False

    if not test_cases:
        log_error("No test cases selected")
        return False

    print("******************** RDK - HDMI CEC SINK vDevice TEST SUITE ********************")
    original_enabled = None
    passed = 0
    failed_cases = []
    suite_setup_ok = True
    restore_ok = True

    try:
        if not auto_activate:
            original_enabled = get_cec_enabled()
            if not original_enabled:
                log_info("Temporarily enabling CEC for runtime cases")
                require_success_value("setEnabled", {"enabled": True})
                if not get_cec_enabled():
                    raise JsonRpcError("CEC did not become enabled")

        for index, (module_name, run_test) in enumerate(test_cases):
            log_info(f"\n{'=' * 60}\nRunning: {module_name}\n{'=' * 60}")
            activated = False
            test_started = False
            test_result = False
            test_elapsed = 0
            case_cleanup_ok = True
            abort_suite = False

            try:
                if auto_activate:
                    log_info(f"Activating {CALLSIGN} at the configured WPEFramework endpoint")
                    activate_plugin(CALLSIGN)
                    activated = True
                    log_success(f"Plugin activated: {CALLSIGN}")
                    time.sleep(PLUGIN_ACTIVATION_DELAY_SECONDS)

                    enabled_state = get_cec_enabled()
                    if original_enabled is None:
                        original_enabled = enabled_state
                    if not enabled_state:
                        log_info("Temporarily enabling CEC for runtime cases")
                        require_success_value("setEnabled", {"enabled": True})
                        if not get_cec_enabled():
                            raise JsonRpcError("CEC did not become enabled")

                started = time.perf_counter()
                test_started = True
                try:
                    test_result = run_test() is True
                except Exception as exc:
                    log_error(f"{module_name} raised an exception: {exc}")
                test_elapsed = time.perf_counter() - started
            except Exception as exc:
                suite_setup_ok = False
                abort_suite = True
                log_error(f"Testcase setup failed for {module_name}: {exc}")
                if auto_activate and not activated:
                    log_error(
                        "Check WPEFramework and Controller/plugin activation logs. "
                        "If the plugin is already active, rerun with --no-activate."
                    )
            finally:
                if auto_activate and activated:
                    if original_enabled is not None:
                        case_cleanup_ok = _restore_cec_state(original_enabled)
                        restore_ok = case_cleanup_ok and restore_ok
                        if not case_cleanup_ok:
                            suite_setup_ok = False
                            abort_suite = True

                    try:
                        log_info(f"Deactivating {CALLSIGN}")
                        deactivate_plugin(CALLSIGN)
                        log_success(f"Plugin deactivated: {CALLSIGN}")
                        time.sleep(PLUGIN_DEACTIVATION_DELAY_SECONDS)
                    except Exception as exc:
                        case_cleanup_ok = False
                        suite_setup_ok = False
                        abort_suite = True
                        log_error(
                            f"Plugin deactivation failed after {module_name}: {exc}"
                        )

            if test_started and test_result and case_cleanup_ok:
                passed += 1
                suffix = (
                    f" ({test_elapsed:.3f}s)"
                    if os.environ.get("HDMICEC_TIMING_ENABLED")
                    else ""
                )
                log_success(f"[PASS] {module_name}{suffix}")
            else:
                failed_cases.append(module_name)
                log_error(f"[FAIL] {module_name}")

            if abort_suite:
                break
            if not auto_activate and index + 1 < len(test_cases):
                time.sleep(1)
    except Exception as exc:
        suite_setup_ok = False
        log_error(f"Suite setup failed: {exc}")
    finally:
        if not auto_activate and original_enabled is not None:
            restore_ok = _restore_cec_state(original_enabled)

    failed = len(failed_cases)
    log_info(f"\nSuite summary: {passed} passed, {failed} failed")
    if failed_cases:
        log_error(f"Failed cases: {', '.join(failed_cases)}")
    return suite_setup_ok and restore_ok and failed == 0


def main():
    parser = argparse.ArgumentParser(description="Run HDMI CEC Sink runtime tests")
    parser.add_argument("suite", nargs="?", default="hdmicecsink")
    parser.add_argument(
        "--tests",
        nargs="+",
        type=str.upper,
        choices=[name.split("_", 1)[0] for name in TEST_MODULES],
        help="Run selected TCIDs in suite order",
    )
    parser.add_argument(
        "--no-activate",
        action="store_true",
        help="Skip per-test plugin activation and deactivation",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Show elapsed time for passed test cases",
    )
    args = parser.parse_args()

    if args.suite.replace("_", "").replace("-", "").lower() != "hdmicecsink":
        log_error("The available suite is 'hdmicecsink'")
        return 2
    if args.timing:
        os.environ["HDMICEC_TIMING_ENABLED"] = "1"

    auto_activate = (
        not args.no_activate
        and os.environ.get("AUTO_ACTIVATE_PLUGINS", "1").lower()
        not in ("0", "false", "no")
    )
    return 0 if run_suite(args.tests, auto_activate=auto_activate) else 1


if __name__ == "__main__":
    sys.exit(main())
