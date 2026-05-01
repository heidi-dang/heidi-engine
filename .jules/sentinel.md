# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-05-01 - Environment Leakage in Unit Test Gate
**Vulnerability:** Generated code samples were executed in a subprocess that inherited the entire host environment, leaking sensitive API keys (e.g., OPENAI_API_KEY) to potentially untrusted synthetic code.
**Learning:** Defaulting to `os.environ` in subprocesses is dangerous when executing generated or external code. In synthetic data pipelines, "safe" execution must include environment isolation.
**Prevention:** Always use a strict allowlist for environment variables when running subprocesses that execute generated code. Use a clean `safe_env` dictionary instead of spreading `os.environ`.
