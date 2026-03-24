# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage to Untrusted Code
**Vulnerability:** The unit test gate script was passing the entire parent process environment (`os.environ`) to subprocesses executing generated (and potentially untrusted) code, exposing sensitive secrets like `OPENAI_API_KEY`.
**Learning:** Defaulting to inherited environments for convenience in testing scripts can inadvertently bridge secure and insecure execution contexts.
**Prevention:** Explicitly whitelist only essential environment variables (e.g., `PATH`, `LANG`) when spawning subprocesses for untrusted code execution. Use a dedicated `safe_env` dictionary.
