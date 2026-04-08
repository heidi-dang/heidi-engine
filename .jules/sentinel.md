# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Credential Leakage via Subprocess Environment
**Vulnerability:** The unit test gate leaked all host environment variables (including `OPENAI_API_KEY`) to subprocesses executing generated code.
**Learning:** `subprocess.run` by default or when passing `{**os.environ}` includes sensitive host credentials.
**Prevention:** Always filter the environment passed to child processes to include only necessary, non-sensitive variables. Use a allowlist or a broad keyword-based denylist (e.g., 'KEY', 'TOKEN', 'SECRET').
