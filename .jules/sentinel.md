# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Environment Variable Leakage in Unit Test Gate
**Vulnerability:** The unit test gate subprocess inherited the full parent environment, exposing sensitive API keys (like `OPENAI_API_KEY`) to potentially untrusted generated code.
**Learning:** Default `subprocess.run` behavior (inheriting `os.environ`) is dangerous when executing generated content, even in a "sandbox" directory.
**Prevention:** Always use an explicit allowlist for environment variables (`PATH`, `LANG`, etc.) when executing generated or untrusted code in subprocesses.
