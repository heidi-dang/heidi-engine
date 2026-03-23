# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage in Unit Test Gate
**Vulnerability:** The unit test gate script was executing untrusted (AI-generated) code while inheriting the full environment of the pipeline, potentially exposing sensitive keys like `OPENAI_API_KEY`.
**Learning:** Even when running in a "sandbox" or isolated directory, `subprocess.run` by default inherits `os.environ`. Defense-in-depth requires explicit environment whitelisting for untrusted code execution.
**Prevention:** Always use a minimal, hardcoded environment (whitelist approach) when executing untrusted code with `subprocess`.
