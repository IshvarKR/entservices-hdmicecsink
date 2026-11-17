import itertools
import json
import os
import subprocess
import time
from pathlib import Path


TARGET_HOST = os.environ.get("TARGET_HOST", "127.0.0.1")
JSONRPC_PORT = os.environ.get("JSONRPC_PORT", "9998")
VCOMPONENT_PORT = os.environ.get("VCOMPONENT_PORT", "8080")
WPEFRAMEWORK_JSONRPC_URL = (
    os.environ.get("WPEFRAMEWORK_JSONRPC_URL")
    or os.environ.get("JSONRPC_URL")
    or f"http://{TARGET_HOST}:{JSONRPC_PORT}/jsonrpc"
)
VCOMPONENT_API_URL = (
    os.environ.get("VCOMPONENT_API_URL")
    or f"http://{TARGET_HOST}:{VCOMPONENT_PORT}/api/postKVP"
)

_BASE_DIR = Path(__file__).resolve().parent
_LOCAL_HDMICEC_CMD_BASE = _BASE_DIR / "vcomponent_configurations" / "commands"
HDMICEC_CMD_BASE = os.environ.get("HDMICEC_CMD_BASE") or str(_LOCAL_HDMICEC_CMD_BASE)

_REQUEST_IDS = itertools.count(1)


class JsonRpcError(RuntimeError):
    pass


class VComponentError(RuntimeError):
    pass


def log_info(message):
    print(f"\033[96m{message}\033[0m")


def log_warning(message):
    print(f"\033[93m{message}\033[0m")


def log_success(message):
    print(f"\033[92m\033[1m{message}\033[0m")


def log_error(message):
    print(f"\033[91m\033[1m{message}\033[0m")


def send_jsonrpc_command(method, params=None, timeout=10):
    request_id = next(_REQUEST_IDS)
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params

    command = [
        "curl",
        "-sS",
        "--max-time",
        str(timeout),
        "-w",
        "\n%{http_code}",
        "-H",
        "Content-Type: application/json",
        "-X",
        "POST",
        "--data-binary",
        json.dumps(payload),
    ]
    command.append(WPEFRAMEWORK_JSONRPC_URL)

    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise JsonRpcError(f"{method}: could not run curl: {exc}") from exc

    stdout = result.stdout or ""
    body, separator, http_status = stdout.rpartition("\n")
    if not separator:
        body, http_status = stdout, ""
    body = body.strip()
    http_status = http_status.strip()

    if result.returncode != 0:
        detail = (result.stderr or "").strip() or "no curl error details"
        raise JsonRpcError(f"{method}: curl exited with {result.returncode}: {detail}")
    if not http_status.isdigit() or not 200 <= int(http_status) < 300:
        raise JsonRpcError(f"{method}: HTTP {http_status or 'status unavailable'}")
    if not body:
        raise JsonRpcError(f"{method}: empty JSON-RPC response")

    try:
        response = json.loads(body)
    except json.JSONDecodeError as exc:
        raise JsonRpcError(f"{method}: invalid JSON response: {exc}") from exc

    if not isinstance(response, dict):
        raise JsonRpcError(f"{method}: expected a JSON object response")
    if response.get("id") != request_id:
        raise JsonRpcError(
            f"{method}: response id {response.get('id')!r} did not match "
            f"request id {request_id}"
        )
    if "error" in response:
        raise JsonRpcError(
            f"{method}: JSON-RPC error {json.dumps(response['error'], sort_keys=True)}"
        )
    if "result" not in response:
        raise JsonRpcError(f"{method}: response is missing 'result'")
    return response["result"]


def activate_plugin(callsign):
    return send_jsonrpc_command(
        "Controller.1.activate",
        params={"callsign": callsign},
    )


def deactivate_plugin(callsign):
    return send_jsonrpc_command(
        "Controller.1.deactivate",
        params={"callsign": callsign},
    )


def require_success(method, params=None):
    result = send_jsonrpc_command(method, params=params)
    if not isinstance(result, dict):
        raise JsonRpcError(f"{method}: expected an object result, got {result!r}")
    if result.get("success") is not True:
        raise JsonRpcError(
            f"{method}: expected success=true, got "
            f"{json.dumps(result, sort_keys=True)}"
        )
    return result


def require_boolean_field(result, field, method):
    value = result.get(field)
    if type(value) is not bool:
        raise JsonRpcError(
            f"{method}: expected boolean field {field!r}, got {value!r}"
        )
    return value


def require_integer_field(result, field, method):
    value = result.get(field)
    if type(value) is not int:
        raise JsonRpcError(
            f"{method}: expected integer field {field!r}, got {value!r}"
        )
    return value


def require_string_field(result, field, method):
    value = result.get(field)
    if not isinstance(value, str):
        raise JsonRpcError(
            f"{method}: expected string field {field!r}, got {value!r}"
        )
    return value


def get_cec_enabled():
    method = "org.rdk.HdmiCecSink.getEnabled"
    result = require_success(method)
    return require_boolean_field(result, "enabled", method)


def require_success_value(method, params=None):
    return require_success(f"org.rdk.HdmiCecSink.{method}", params=params)


def wait_for_result(method, predicate, expected, timeout=15, interval=0.25):
    if timeout <= 0 or interval <= 0:
        raise ValueError("timeout and interval must be positive")

    deadline = time.monotonic() + timeout
    last_result = None
    while True:
        last_result = require_success(method)
        if predicate(last_result):
            return last_result

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))

    raise JsonRpcError(
        f"{method}: did not report {expected} within {timeout}s; "
        f"last result: {json.dumps(last_result, sort_keys=True)}"
    )


def send_vcomponent_command(yaml_filename, timeout=10):
    relative_path = Path(yaml_filename)
    if (
        relative_path.is_absolute()
        or relative_path.name != yaml_filename
        or relative_path.suffix.lower() != ".yaml"
    ):
        raise VComponentError(f"Expected a YAML fixture name, got {yaml_filename!r}")

    yaml_path = Path(HDMICEC_CMD_BASE) / relative_path
    if not yaml_path.is_file():
        raise VComponentError(f"vComponent YAML fixture not found: {yaml_path}")

    command = [
        "curl",
        "-sS",
        "--max-time",
        str(timeout),
        "-w",
        "\n%{http_code}",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/x-yaml",
        "--data-binary",
        f"@{yaml_path}",
        VCOMPONENT_API_URL,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise VComponentError(f"{yaml_filename}: could not run curl: {exc}") from exc

    stdout = result.stdout or ""
    body, separator, status_text = stdout.rpartition("\n")
    if not separator:
        body, status_text = stdout, ""
    body = body.strip()
    status_text = status_text.strip()
    try:
        http_status = int(status_text)
    except ValueError:
        http_status = 0

    stderr = (result.stderr or "").strip()
    if (
        http_status == 0
        and result.returncode == 52
        and "Empty reply from server" in stderr
    ):
        log_warning(
            f"{yaml_filename}: vComponent closed the connection without an HTTP "
            "acknowledgment; the testcase will verify the resulting JSON-RPC state"
        )
        return 0, "Empty reply from server"

    if result.returncode != 0:
        detail = stderr or "no curl error details"
        raise VComponentError(
            f"{yaml_filename}: curl exited with {result.returncode}: {detail}"
        )
    if not 200 <= http_status < 300:
        raise VComponentError(
            f"{yaml_filename}: vComponent returned HTTP "
            f"{status_text or 'status unavailable'}: {body or stderr}"
        )
    return http_status, body
