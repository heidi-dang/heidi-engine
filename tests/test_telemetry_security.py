import base64
import json
import os
import time
import urllib.request
import urllib.parse
from heidi_engine import telemetry


def test_telemetry_security_headers_and_query_params():
    # Set TELEMETRY_PASS in os.environ before starting server
    os.environ["TELEMETRY_PASS"] = "testsecret123"
    port = 7789
    telemetry.start_http_server(port)

    time.sleep(0.1)

    url = f"http://127.0.0.1:{port}/status?query=1"
    req = urllib.request.Request(url)
    auth_str = base64.b64encode(b"admin:testsecret123").decode()
    req.add_header("Authorization", f"Basic {auth_str}")

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        headers = dict(resp.headers)
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Content-Security-Policy") == "default-src 'none'"
        assert headers.get("Cache-Control") == "no-store, max-age=0"

        body = json.loads(resp.read().decode())
        assert "health" in body


def test_health_endpoint_security_headers_and_query_params():
    port = 7789
    url = f"http://127.0.0.1:{port}/health?check=true"
    req = urllib.request.Request(url)

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        headers = dict(resp.headers)
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Content-Security-Policy") == "default-src 'none'"
        assert headers.get("Cache-Control") == "no-store, max-age=0"

        body = json.loads(resp.read().decode())
        assert body.get("health") == "ok"
