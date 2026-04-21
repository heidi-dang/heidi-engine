# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Environment Variable Leakage in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code in a subprocess that inherited all environment variables from the parent process, potentially leaking sensitive data like `OPENAI_API_KEY`.
**Learning:** Defaulting to inheriting the parent environment in `subprocess.run` is dangerous when executing untrusted or semi-trusted code. Sandbox wrappers must explicitly define an allowlist of safe environment variables.
**Prevention:** Use a strict allowlist for environment variables passed to child processes executing user-provided code.
