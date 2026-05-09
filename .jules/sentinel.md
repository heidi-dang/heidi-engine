# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Weak Sandbox Isolation in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code with access to all parent environment variables, including sensitive API keys (e.g., `OPENAI_API_KEY`), and lacked protection against Python sandbox escape techniques.
**Learning:** Even simple sanity checks on untrusted code must isolate the execution environment and block access to internal attributes like `__subclasses__` and `__globals__` to prevent malicious exploitation.
**Prevention:** Filter subprocess environment variables to a minimal allowlist (`PATH`, `PYTHONPATH`, etc.) and maintain a robust set of dangerous patterns that block both powerful modules and sandbox-escape attributes.
