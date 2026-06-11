# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in get_run_dir
**Vulnerability:** The `get_run_dir` function in both telemetry and dashboard was vulnerable to path traversal because it used `Path(base) / run_id`. In Python's `pathlib`, if the second argument is an absolute path, it completely overrides the base.
**Learning:** Never trust user-provided identifiers in path construction, even when using `pathlib.Path`. Absolute paths in join operations can escape the intended root directory.
**Prevention:** Always sanitize user-provided path components using `.name` or `os.path.basename()` to ensure they remain relative and do not contain traversal markers like `..`.
