# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage and Sandbox Bypasses in Unit Test Gate
**Vulnerability:** `scripts/03_unit_test_gate.py` executed generated code while passing the full parent environment, potentially leaking sensitive API keys (e.g., `OPENAI_API_KEY`). It also used bypassable regexes for sandbox enforcement.
**Learning:** Sandbox implementations often focus on blocking "dangerous" imports but forget that the execution environment itself is a sensitive asset. Regex-based blocking is also prone to bypasses if not carefully anchored with word boundaries and encompassing internal attributes like `__builtins__`.
**Prevention:** Always scrub the environment for subprocesses executing untrusted code to an allowlist of safe variables. Use word boundaries (`\b`) in security regexes and block access to reflection/internal attributes.
