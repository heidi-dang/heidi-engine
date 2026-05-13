# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage in Unit Test Gate
**Vulnerability:** `scripts/03_unit_test_gate.py` executed generated code using `subprocess.run` without filtering environment variables, allowing potentially malicious generated code to exfiltrate sensitive data (e.g., `OPENAI_API_KEY`) from the environment.
**Learning:** `subprocess.run` in Python inherits the full parent environment by default. Isolation of the working directory is insufficient if the environment remains exposed.
**Prevention:** Explicitly filter the `env` argument in `subprocess.run` using an allowlist of safe variables (e.g., `PATH`, `PYTHONPATH`, `LANG`) when executing untrusted or generated code.
