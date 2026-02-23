import pytest
import subprocess
import time
import urllib.request
import json
import socket
import os

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

@pytest.fixture(scope="module")
def daemon_process():
    # Use a non-standard port for test to avoid conflicts
    port = 8181
    if check_port(port):
        pytest.skip(f"Port {port} is already in use. Cannot run daemon test.")

    # Start the daemon in foreground mode so it can be managed by subprocess
    # We must mock subprocesses so the test doesn't actually try to run the slow Python train scripts
    test_env = os.environ.copy()
    test_env["HEIDI_MOCK_SUBPROCESSES"] = "1"

    bin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build', 'bin', 'heidid'))
    if not os.path.exists(bin_path):
        pytest.skip("C++ daemon binary not built (build/bin/heidid missing)")
    process = subprocess.Popen([bin_path, "-p", str(port)], env=test_env)
    
    # Give the server a moment to bind and start listening
    time.sleep(0.5)
    
    yield port
    
    # Teardown: terminate the process gently
    process.terminate()
    process.wait(timeout=2)


def test_daemon_status_json(daemon_process):
    port = daemon_process
    url = f"http://127.0.0.1:{port}/api/v1/status"
    
    # Fetch status
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        
        # Verify valid JSON content generated from C++ struct
        assert "state" in data
        assert data["state"] == "IDLE"
        assert "round" in data
        assert data["round"] == 1

def test_daemon_train_now_action(daemon_process):
    port = daemon_process
    action_url = f"http://127.0.0.1:{port}/api/v1/action/train_now"
    status_url = f"http://127.0.0.1:{port}/api/v1/status"
    
    # Hit the POST endpoint
    req = urllib.request.Request(action_url, method='POST')
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        
    # Poll state until it updates or timeout
    updated = False
    for _ in range(10):
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Because mocked commands are instantaneous, it immediately executes
            # training, eval, and then ticks to the next round of collection (or settles back to IDLE).
            # The most reliable check is that the round incremented as a result of the workflow.
            if data["round"] >= 2:
                updated = True
                break
        time.sleep(0.1)
        
    assert updated, "Core state failed to complete the training trigger (round did not increment)"
