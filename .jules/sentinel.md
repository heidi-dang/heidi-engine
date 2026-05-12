# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage and Sandbox Escape in Unit Test Gate
**Vulnerability:** The unit test gatekeeper was passing the entire host environment to the subprocess executing generated code, and lacked checks for Python internal attributes like `__subclasses__`.
**Learning:** Even "optional" or "local" test scripts can become vectors for secret leakage (e.g., OPENAI_API_KEY) if they don't explicitly isolate the execution environment. Regex-based filtering is a baseline, but environment isolation is more robust.
**Prevention:** Always use a strict allowlist for environment variables when spawning subprocesses to execute untrusted or generated code. Include Python introspection attributes in blocklists for a basic defense-in-depth against sandbox escapes.
