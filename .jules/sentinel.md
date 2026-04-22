# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage and Sandbox Escape in Unit Test Gate
**Vulnerability:** The unit test gate executed untrusted code snippets with full access to the host's environment variables (including `OPENAI_API_KEY`) and allowed importing sensitive modules like `ctypes` or `importlib`.
**Learning:** Even "basic sanity checks" that execute code must be treated as security boundaries. Relying solely on a partial blacklist of modules is insufficient as Python offers many ways to access sensitive data (e.g., `os.environ` via `importlib` or `/proc/self/environ`).
**Prevention:** Always filter subprocess environments to a strict allowlist. Use a defense-in-depth approach by combining environment isolation with a robust blocklist of modules and built-ins. Ensure code injection templates are properly sanitized and indented to prevent execution logic bypasses.
