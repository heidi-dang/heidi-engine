# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage in Unit Test Gate
**Vulnerability:** The unit test gate script (`scripts/03_unit_test_gate.py`) executed untrusted generated code samples while inheriting the full environment of the parent process, potentially leaking sensitive API keys (e.g., `OPENAI_API_KEY`) to the tested code.
**Learning:** Even when code is executed in an "isolated" temporary directory or with timeout protection, it can still access sensitive information through environment variables if not explicitly scrubbed.
**Prevention:** Always use a "clean" or "scrubbed" environment when executing untrusted code in a subprocess. Explicitly remove sensitive variables from the environment dictionary passed to the execution command.
