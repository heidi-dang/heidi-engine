# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage in Code Sandbox
**Vulnerability:** The unit test gate executed generated code with `**os.environ`, exposing sensitive keys like `OPENAI_API_KEY` to potentially malicious generated code.
**Learning:** Defaulting to the full environment for convenience creates a major security hole when running untrusted code. Static analysis alone (blocking `import os`) is insufficient as it can be bypassed via `importlib`.
**Prevention:** Always use a minimal `safe_env` when executing subprocesses for untrusted code. Include `importlib` in dangerous pattern lists to prevent dynamic import bypasses. Use `textwrap.indent` to ensure correctly formatted code injection.
