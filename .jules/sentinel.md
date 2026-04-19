# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leak in Unit Test Gate
**Vulnerability:** The `scripts/03_unit_test_gate.py` script executed generated code using `subprocess.run` with the full parent environment (`os.environ`). This allowed untrusted generated code to potentially access sensitive credentials like `OPENAI_API_KEY`.
**Learning:** Subprocesses inherit the parent environment by default in Python. When executing untrusted code, the environment must be explicitly sanitized.
**Prevention:** Always use a filtered environment when running untrusted code. Exclude variables containing sensitive keywords like "KEY", "TOKEN", "SECRET", or "PASS".
