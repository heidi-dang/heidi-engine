# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry and Dashboard
**Vulnerability:** The `get_run_dir` functions in both `telemetry.py` and `dashboard.py` were vulnerable to path traversal because `Path(base) / run_id` allows absolute paths in `run_id` to override the base directory.
**Learning:** Path joining with `pathlib.Path` or `os.path.join` is unsafe if the second argument is an absolute path. `Path("/base") / "/etc/passwd"` results in `PosixPath('/etc/passwd')`.
**Prevention:** Always sanitize user-provided path components using `.name` or `os.path.basename` to ensure they remain relative to the intended base directory. Additionally, handle special markers like `.` and `..` which can still be used for traversal or unexpected behavior.
