# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal via Run ID
**Vulnerability:** `get_run_dir` in `telemetry.py` and `dashboard.py` allowed path traversal because `Path(base) / run_id` enables an absolute `run_id` to override the base directory.
**Learning:** Using `pathlib`'s `/` operator with user-provided absolute paths is a common security pitfall. `Path('base') / '/etc/passwd'` results in `Path('/etc/passwd')`.
**Prevention:** Always sanitize user-provided path components using `.name` to ensure they remain relative, and explicitly handle special markers like `.` and `..` which `.name` may return.
