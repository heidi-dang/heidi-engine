# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Environment Leakage in Unit Test Gate
**Vulnerability:** The unit test gate script was passing the entire parent environment to the subprocess running generated code, potentially leaking sensitive API keys (e.g., `OPENAI_API_KEY`).
**Learning:** Using `env={**os.environ, ...}` is dangerous when executing untrusted or generated code, as it inherits all secrets from the host process.
**Prevention:** Always use a restricted allowlist for environment variables when running subprocesses that execute code. Only include essential variables like `PATH` and `PYTHONPATH`.
