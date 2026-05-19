# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-05-19 - Hardening Unit Test Gate Isolation
**Vulnerability:** Environment secret exfiltration and code injection/bypass in unit test gate.
**Learning:** Subprocesses used for unit testing inherited the full parent environment, allowing generated code to access sensitive API keys via `os.environ`. Additionally, improperly indented user code could break out of the test wrapper's try-except block.
**Prevention:** Filter environment variables to a minimal allowlist before spawning test subprocesses and use `textwrap.indent` to safely embed user code within isolation templates.
