# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage to Untrusted Code
**Vulnerability:** The unit test gate was passing the entire host environment (including `OPENAI_API_KEY`) to generated code being executed via `subprocess.run`.
**Learning:** Even when running code in a temporary directory with a timeout, the execution environment can still leak sensitive secrets if not explicitly filtered.
**Prevention:** Use a whitelist-based approach for environment variables when executing untrusted or generated code. Exclude common secret patterns like `KEY`, `TOKEN`, `SECRET`, and `PASS`.
