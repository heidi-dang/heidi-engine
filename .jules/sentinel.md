# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage in Test Sandbox
**Vulnerability:** `scripts/03_unit_test_gate.py` executed untrusted code blocks in a subprocess with the full host environment inherited, exposing sensitive keys like `OPENAI_API_KEY`.
**Learning:** Developers often use `os.environ` or `**os.environ` out of convenience for subprocesses without considering the security implications of inheriting the entire environment in a sandbox context.
**Prevention:** Always use an explicit allowlist for environment variables when executing untrusted code. Ensure the subprocess environment is restricted to the bare minimum required for execution.
