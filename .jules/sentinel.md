# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in get_run_dir
**Vulnerability:** `get_run_dir` in both telemetry and dashboard modules was vulnerable to path traversal. An attacker-controlled `run_id` could use absolute paths or `..` sequences to escape the base directory.
**Learning:** `pathlib.Path`'s `/` operator treats absolute paths as anchors, effectively overriding previous path components.
**Prevention:** Sanitize user-provided path components with `Path(run_id).name` to ensure only the filename component is used, and validate that the resulting path is within the expected parent directory.
