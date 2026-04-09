# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leak to Untrusted Code
**Vulnerability:** The unit test gate executed generated code with the full parent environment, potentially exposing sensitive keys like `OPENAI_API_KEY`.
**Learning:** Subprocesses inherit the environment by default; when executing untrusted or generated code, a strict whitelist or blacklist of environment variables must be applied.
**Prevention:** Filter `os.environ` before passing it to `subprocess.run` when executing code from external sources. Exclude common secret-bearing keywords like `KEY`, `TOKEN`, `SECRET`, and `PASS`.
