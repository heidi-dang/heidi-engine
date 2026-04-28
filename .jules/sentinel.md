# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-04-28 - Environment Leakage and Sandbox Escape in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code blocks by inheriting the parent process's environment, which included sensitive keys like `OPENAI_API_KEY`. Additionally, the sandbox could be easily escaped using unblocked modules like `posixpath` or internal attributes like `__subclasses__`.
**Learning:** Even if code is executed in a "temporary directory", it is NOT secure if it shares the same environment or has access to powerful introspection/system modules.
**Prevention:** Always use a restricted environment allowlist for subprocesses executing untrusted code. Maintain a robust blocklist of modules and attributes that can be used for introspection and sandbox escapes. Ensure code is correctly isolated and validated before execution.
