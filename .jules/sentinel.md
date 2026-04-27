# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-02-21 - Unrestricted Subprocess Environment Leakage
**Vulnerability:** The unit test gate executed untrusted generated code with the full parent environment (`os.environ`), leaking sensitive secrets like `OPENAI_API_KEY`.
**Learning:** Subprocesses inherit the full environment by default in Python, which is dangerous when running code from untrusted sources (like LLM outputs).
**Prevention:** Always filter `os.environ` to a minimal allowlist of safe variables (`PATH`, `LANG`, etc.) before passing it to `subprocess.run(env=...)`.
