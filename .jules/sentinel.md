# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leak in Unit Test Subprocess
**Vulnerability:** The unit test gate executed user-provided code in a subprocess that inherited the full environment of the parent process, potentially leaking sensitive API keys (e.g., `OPENAI_API_KEY`).
**Learning:** Subprocess execution by default inherits the parent's environment. When running untrusted or generated code, the environment must be explicitly sanitized.
**Prevention:** Always use a filtered environment for subprocesses executing potentially untrusted code. Blacklist keys containing sensitive keywords like 'KEY', 'TOKEN', 'SECRET', or 'PASS'.
