# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Path Traversal via Absolute Path in Pathlib
**Vulnerability:** `get_run_dir` used `Path(AUTOTRAIN_DIR) / "runs" / run_id`, which allowed a `run_id` starting with `/` to override the entire base directory, enabling arbitrary directory access.
**Learning:** In Python's `pathlib`, the `/` operator treats absolute paths as a new root, silently discarding the preceding path components. This is a subtle but dangerous behavior when handling user-provided path segments.
**Prevention:** Always sanitize user-provided path segments using `Path(input).name` to ensure they are treated as single, relative filename components before joining them to a base directory.
