# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Secret Leakage via Subprocess Environment in Unit Test Gate
**Vulnerability:** `scripts/03_unit_test_gate.py` executed generated code samples using `subprocess.run` without filtering `os.environ`, allowing samples to access sensitive environment variables like `OPENAI_API_KEY`.
**Learning:** Default `subprocess` behavior inherits the entire parent environment. In security-sensitive contexts like executing untrusted or synthetic code, the environment must be explicitly sanitized.
**Prevention:** Always use a restricted environment allowlist when executing code via `subprocess`. In Python, filter `os.environ` to a minimal set of safe keys (e.g., `PATH`, `PYTHONPATH`) before passing it to the `env` parameter.
