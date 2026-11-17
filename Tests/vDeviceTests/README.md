# HDMI CEC Sink vDevice tests

This is a runtime JSON-RPC suite, separate from the CMake-driven L1/L2 tests in
`Tests`. It converts the supported calls from `run_hdmicecsink_curls.sh` into
assertions and can run selected cases by TCID.

## Preconditions

- WPEFramework and `org.rdk.HdmiCecSink` are installed and reachable.
- The HDMI CEC vComponent HTTP API is running and reachable.
- The device must use the **TV** RDK profile. The sink plugin rejects the STB
  profile. This suite does not modify `/etc/device.properties` or run
  `RDKProfile.sh`; set the profile and restart WPEFramework manually if needed.
- `curl` and Python 3 are available wherever the suite runs.
- Plugin activation uses `Controller.1.activate` without a bearer token, like
  the HDMI CEC Source suite. If the plugin is already active, use `--no-activate`.

## Run

From this directory on the target (or a host configured to reach it):

```sh
python3 SuiteManager.py hdmicecsink
python3 SuiteManager.py hdmicecsink --tests TCID01 TCID06 TCID09
python3 SuiteManager.py hdmicecsink --no-activate
```

By default, the runner activates the plugin before each testcase, temporarily
enables CEC, restores the original CEC enabled state, then deactivates the
plugin. It waits 6 seconds after activation and 1 second after deactivation.
`--no-activate` skips the per-test activation/deactivation cycle; the plugin
must already be active. Set `AUTO_ACTIVATE_PLUGINS=0` for the same behavior.

The endpoint defaults to `http://127.0.0.1:9998/jsonrpc`. Override it with
`WPEFRAMEWORK_JSONRPC_URL` (or `JSONRPC_URL`), or set `TARGET_HOST` and
`JSONRPC_PORT`.

The vComponent endpoint defaults to
`http://127.0.0.1:8080/api/postKVP`. Override it with `VCOMPONENT_API_URL`, or
set `TARGET_HOST` and `VCOMPONENT_PORT`. Commands are loaded from this suite's
`vcomponent_configurations/commands` directory; set `HDMICEC_CMD_BASE` to use
another command directory.

## Scope and side effects

The OSD-name and vendor-ID readback cases restore their original settings. The
suite also restores the original CEC enabled state. Other commands in the
provided smoke sequence can send CEC frames or change the active route. The
vComponent-backed active-route, active-source, audio-status, and device-list
cases configure the emulated bus with `Device_Config_Sink_Test.yaml` and inject
CEC frames; the bus is left in that test topology. Run the suite against a test
device or emulator rather than a live user setup.

The curl smoke script's `{{response}}` values are literal in Bash unless an
external step substitutes them; this suite instead verifies the set/get
round-trip with real values. The `register` calls are not included because
separate short-lived curl requests cannot verify delivery of asynchronous
notifications. Event delivery requires a persistent JSON-RPC subscription
client. This suite follows the supplied smoke sequence; it does not currently
exercise API calls outside that sequence, including ARC routing control and
audio-device power-status requests. The vComponent frame fixtures do not use
`Device_Add.yaml`; they announce a single known logical address explicitly and
avoid relying on the reported Source-side add-all behavior.
