# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run ID Handling
**Vulnerability:** The pipeline used `run_id` directly in file paths without sanitization, allowing path traversal (e.g., `run_id='../'`) to escape the designated runs directory.
**Learning:** Logic relying on `Path(run_id).name` for sanitization must explicitly handle `".."` and empty string results, as `pathlib.Path("..").name` returns `".."` and `pathlib.Path(".").name` returns an empty string.
**Prevention:** Implement a dedicated `sanitize_run_id` helper that isolates the filename component and validates it against dangerous or empty values before path construction.
