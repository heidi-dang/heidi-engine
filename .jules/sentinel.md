# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in get_run_dir
**Vulnerability:** `get_run_dir` was vulnerable to path traversal because `Path(AUTOTRAIN_DIR) / "runs" / run_id` allows absolute paths in `run_id` to override the base directory.
**Learning:** `pathlib.Path`'s `/` operator prioritizes the second operand if it is an absolute path.
**Prevention:** Always sanitize user-provided IDs using `Path(id).name` when constructing file system paths to ensure they remain within the intended directory.
