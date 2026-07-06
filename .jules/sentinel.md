# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Sandbox Bypass and Isolation Gaps in Unit Test Gate
**Vulnerability:** The unit test gate lacked proper environment isolation (HOME variable) and had incomplete dangerous pattern filtering (importlib, builtins), potentially allowing generated code to access sensitive local files or bypass sandbox restrictions.
**Learning:** Basic regex filtering is insufficient for code sandboxing; defense-in-depth requires both strict pattern matching and OS-level isolation (like overriding HOME and PYTHONPATH).
**Prevention:** Always isolate execution environments by overriding sensitive environment variables and use comprehensive forbidden-pattern lists that include dynamic import mechanisms.
