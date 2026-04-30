# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Unit Test Gate Sandbox Bypass and Indentation Bug
**Vulnerability:** The unit test gate had a weak blocklist for dangerous Python patterns and a bug that caused it to fail on any multi-line code block due to incorrect indentation in the wrapping template.
**Learning:** Heuristic-based sandboxes are fragile. The indentation bug actually *reduced* security by making the gate unusable for complex (multi-line) code that might contain more sophisticated bypasses.
**Prevention:** Always properly indent injected code in f-string templates. Harden blocklists with Python internal attributes like `__globals__` and `__subclasses__`, and block sensitive modules like `gc`, `inspect`, and `importlib`.
