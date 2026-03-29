# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Environment Variable Leak in Test Gate
**Vulnerability:** The unit test gate executed untrusted generated code while passing the full host environment (`**os.environ`), leaking sensitive API keys (e.g., `OPENAI_API_KEY`) to the subprocess.
**Learning:** Using `**os.environ` in `subprocess.run` is dangerous when executing untrusted code as it provides full access to host secrets.
**Prevention:** Use a whitelist-based `restricted_env` (containing only `PATH`, `TMPDIR`, etc.) when executing code from untrusted sources.
