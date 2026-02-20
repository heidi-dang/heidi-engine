import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
import pytest
import json

REPO_ROOT = Path(__file__).resolve().parents[1]

# List of possible heidid paths
CANDIDATES = [
    REPO_ROOT / "build" / "bin" / "heidid",
    REPO_ROOT / "cmake-build-release" / "bin" / "heidid",
    REPO_ROOT / "cmake-build" / "bin" / "heidid",
]


def _find_heidid() -> str | None:
    for p in CANDIDATES:
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return shutil.which("heidid")


HEIDID = _find_heidid()
if not HEIDID:
    pytest.skip(
        "Skipping daemon tests: heidid binary not built/installed in CI", allow_module_level=True
    )


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture(scope="module")
def daemon_process():
    port = 8181
    if _port_open(port):
        pytest.skip(f"Port {port} already in use")

    env = os.environ.copy()
    env["HEIDI_MOCK_SUBPROCESSES"] = "1"

    process = subprocess.Popen([HEIDID, "-p", str(port)], env=env)

    # Bounded polling instead of hard sleep
    for _ in range(50):
        if _port_open(port):
            break
        time.sleep(0.05)
    else:
        process.terminate()
        raise RuntimeError("heidid did not start listening")

    yield port

    process.terminate()
    process.wait(timeout=3)


def test_daemon_status_json(daemon_process):
    port = daemon_process
    url = f"http://127.0.0.1:{port}/api/v1/status"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert "state" in data
        assert data["state"] == "IDLE"
        assert "round" in data
        assert data["round"] == 1


def test_daemon_train_now_action(daemon_process):
    port = daemon_process
    action_url = f"http://127.0.0.1:{port}/api/v1/action/train_now"
    status_url = f"http://127.0.0.1:{port}/api/v1/status"

    req = urllib.request.Request(action_url, method="POST")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200

    updated = False
    for _ in range(10):
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data["round"] >= 2:
                updated = True
                break
        time.sleep(0.1)

    assert updated, "Core state failed to complete the training trigger (round did not increment)"
