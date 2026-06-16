# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run Directory Resolution
**Vulnerability:** `get_run_dir` was vulnerable to path traversal because `Path(base) / run_id` allows absolute paths in `run_id` to override the base.
**Learning:** Python's `pathlib.Path` join logic (`/` operator) returns the last absolute path if multiple are provided. `Path('/a') / '/b'` results in `Path('/b')`.
**Prevention:** Always sanitize user-provided path components using `Path(component).name` to extract only the final segment. Additionally, handle cases where `.name` returns `.` or `..` or an empty string to ensure the path stays within the intended directory.
