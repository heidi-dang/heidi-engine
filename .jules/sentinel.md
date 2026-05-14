# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-05-14 - Environment Leakage in Unit Test Gate
**Vulnerability:** The unit test gate script inherited all environment variables when executing generated code samples, potentially exposing sensitive API keys and tokens to untrusted code.
**Learning:** Python's `subprocess.run` inherits `os.environ` by default. In a pipeline that generates and tests code, this allows the generated code to exfiltrate secrets from the environment.
**Prevention:** Explicitly filter the `env` argument in `subprocess` calls to an allowlist of essential, non-sensitive variables when executing untrusted code.
