# Sentinel Security Journal

## 2025-05-18 - Path Traversal in Run Directory Resolution
**Vulnerability:** `get_run_dir()` used raw `run_id` strings to construct file paths, allowing path traversal vectors (e.g., `../../`) to resolve paths outside `AUTOTRAIN_DIR/runs`.
**Learning:** Functions handling dynamic identifier inputs for file system paths must strictly sanitize input characters rather than trusting environment variables or caller parameters.
**Prevention:** Always use a `sanitize_run_id()` function that strips non-alphanumeric characters (except `-` and `_`) before joining path components.

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.
