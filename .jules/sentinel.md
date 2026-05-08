# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leak in Unit Test Gate
**Vulnerability:** The unit test gate passed the entire host environment (`os.environ`) to subprocesses executing generated code, potentially leaking sensitive API keys or credentials.
**Learning:** Defaulting to `os.environ` in `subprocess.run` is a common but dangerous pattern when running code from different trust levels.
**Prevention:** Always use an allowlist-based approach for environment variables (`safe_env`) when executing external or generated code.
