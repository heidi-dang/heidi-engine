# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.
## 2025-05-15 - Path Traversal in Run Directory Construction
**Vulnerability:** `get_run_dir` in both `telemetry.py` and `dashboard.py` was vulnerable to path traversal and absolute path injection because it used `Path(base) / run_id` without sanitizing `run_id`.
**Learning:** In Python's `pathlib.Path`, joining an absolute path as the second argument (e.g., `Path("/base") / "/etc/passwd"`) results in the absolute path overriding the base.
**Prevention:** Always sanitize user-provided path components using `Path(component).name` to ensure only the basename is used, and handle edge cases where `.name` might return empty strings or navigation tokens (`.`, `..`).
