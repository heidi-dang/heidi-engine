# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Sandbox Bypass and Information Leak in Unit Test Gate
**Vulnerability:** The unit test gate (`scripts/03_unit_test_gate.py`) was vulnerable to sandbox bypasses using Python internal attributes like `__builtins__` or `__subclasses__`. Additionally, sensitive host environment variables were leaked to the test subprocess.
**Learning:** Simple regex-based blacklists for dangerous modules are insufficient for sandboxing Python. Environment isolation is a critical layer of defense when executing untrusted code.
**Prevention:** Use an allowlist-based approach for environment variables in subprocesses. Enhance pattern matching to include Python internal attributes that can be used to reach restricted modules.
