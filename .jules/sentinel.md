# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-05-20 - Unit Test Gate Escape via Environment and Attribute Access
**Vulnerability:** The unit test gate in `scripts/03_unit_test_gate.py` passed the full host environment to executed code and lacked regex patterns for common Python sandbox bypasses (`posix`, `__subclasses__`, etc.).
**Learning:** Relying solely on regex for blacklisting dangerous modules is insufficient. Defense-in-depth requires environment isolation and blocking introspection attributes.
**Prevention:** Always filter environment variables for executed code to the absolute minimum required. Use broad regex patterns that cover platform-specific module aliases and dunder methods.
