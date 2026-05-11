# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage in Unit Test Gate
**Vulnerability:** The `scripts/03_unit_test_gate.py` script was executing generated code in a subprocess while passing the entire host environment, including sensitive API keys like `OPENAI_API_KEY`.
**Learning:** Executing untrusted code, even for validation purposes, must be done in a highly restricted environment. Relying on simple regex filters for "dangerous code" is insufficient if the execution environment itself is over-privileged.
**Prevention:** Always use a minimal allowlist for environment variables passed to subprocesses executing untrusted code. Use standard libraries like `textwrap` to ensure code is properly formatted (e.g., indented) when wrapped in security/logging templates to avoid functional failures that might bypass checks.
