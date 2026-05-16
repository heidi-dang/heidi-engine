# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-05-16 - Environment Variable Leakage in Test Sandbox
**Vulnerability:** The unit test gate executed generated code in a subprocess that inherited the full host environment, allowing untrusted code to exfiltrate sensitive secrets (e.g., `OPENAI_API_KEY`) via `os.environ`.
**Learning:** Subprocess isolation must include environment scrubbing. Regex-based keyword detection for Python code can be bypassed with unconventional whitespace (e.g., `import\tos`).
**Prevention:** Filter subprocess environment variables to a minimal allowlist (`PATH`, `PYTHONPATH`, etc.). Use robust word-boundary regex (`\b`) for keyword detection.
