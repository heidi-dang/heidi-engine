# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-31 - Environment Leakage in Test Runners
**Vulnerability:** Executing generated code samples by inheriting the full parent environment (`os.environ`) allowed potentially malicious code to leak sensitive keys (e.g., `OPENAI_API_KEY`).
**Learning:** Even when running code in temporary directories with timeouts, sensitive information from the host environment remains accessible unless explicitly filtered.
**Prevention:** Always use a strict allowlist (e.g., `PATH`, `PYTHONPATH`) for environment variables when executing untrusted or auto-generated code in a subprocess.
