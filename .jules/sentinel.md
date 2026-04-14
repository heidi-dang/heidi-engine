# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Environment Variable Leakage in Unit Test Gate
**Vulnerability:** The unit test gate script was passing the entire parent environment to the subprocesses running generated code, potentially leaking API keys and other secrets.
**Learning:** Even when running code in an isolated temporary directory, the environment can still contain sensitive information if inherited from the parent process.
**Prevention:** Always filter the environment passed to untrusted code. Use an allow-list or a strict deny-list for environment variables, and avoid inheriting the parent's environment by default in sensitive contexts.
