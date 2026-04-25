# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Unit Test Gate Sandbox Escape and Secret Leakage
**Vulnerability:** The `03_unit_test_gate.py` script executed generated code while exposing all environment variables (including `OPENAI_API_KEY`) and had a flawed code injection mechanism that allowed escaping the intended `try-except` wrapper due to improper indentation.
**Learning:** Even internal "sanity check" tools that execute code must be treated as security-sensitive. Passing the entire environment to a subprocess is a common but dangerous pattern when that environment contains secrets.
**Prevention:** Always use an allowlist for environment variables when executing untrusted or semi-trusted code. Use `textwrap.indent` or similar utilities when embedding code into templates to ensure it remains within the intended scope.
