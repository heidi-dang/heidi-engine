import base64
import json
import os
import time
import urllib.request
import urllib.error
from heidi_engine import telemetry


def test_http_security_headers_and_path_parsing():
    port = 8879
    session_pass = "testsecretpass123"
    os.environ["TELEMETRY_PASS"] = session_pass

    telemetry.start_http_server(port)
    time.sleep(0.3)

    # 1. Test /health with query parameter (no auth required)
    url_health = f"http://127.0.0.1:{port}/health?check=1"
    req = urllib.request.Request(url_health)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        headers = dict(resp.headers)
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Content-Security-Policy") == "default-src 'none'"
        assert "no-store" in headers.get("Cache-Control", "")
        data = json.loads(resp.read().decode())
        assert data == {"health": "ok"}

    # 2. Test 401 Unauthorized headers on protected endpoint
    url_status = f"http://127.0.0.1:{port}/status?refresh=1"
    req_unauth = urllib.request.Request(url_status)
    try:
        urllib.request.urlopen(req_unauth)
        assert False, "Should have raised HTTPError 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        headers = dict(e.headers)
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Content-Security-Policy") == "default-src 'none'"
        assert "no-store" in headers.get("Cache-Control", "")

    # 3. Test Authorized status request with query parameter
    auth_str = base64.b64encode(f"admin:{session_pass}".encode()).decode()
    req_auth = urllib.request.Request(url_status, headers={"Authorization": f"Basic {auth_str}"})
    with urllib.request.urlopen(req_auth) as resp:
        assert resp.status == 200
        headers = dict(resp.headers)
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Content-Security-Policy") == "default-src 'none'"
        assert "no-store" in headers.get("Cache-Control", "")
        data = json.loads(resp.read().decode())
        assert "health" in data
