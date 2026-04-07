# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-04-07 - Environment Variable Leakage in Test Runners
**Vulnerability:** The unit test gate leaked the host's full environment (including `OPENAI_API_KEY`) to generated code being verified.
**Learning:** Passing `os.environ` to subprocesses executing potentially untrusted or synthetic code creates a massive credential leak risk.
**Prevention:** Always filter the environment passed to subprocesses. Use an allowlist or a blocklist for sensitive keys (e.g., 'KEY', 'SECRET', 'TOKEN').
