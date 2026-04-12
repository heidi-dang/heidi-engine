# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Secret Leakage in Unit Test Sandbox
**Vulnerability:** The unit test gate executed generated code in a subprocess that inherited all parent environment variables, potentially leaking sensitive API keys or tokens to untrusted code.
**Learning:** Even a "basic sanity check" subprocess can be an attack vector if it lacks environment isolation. Dangerous pattern checks are easily bypassed by obfuscation like backslash-newline continuations.
**Prevention:** Always filter environment variables for subprocesses executing untrusted code. Normalize code strings (e.g., remove line continuations) before applying security regex patterns to prevent bypasses.
