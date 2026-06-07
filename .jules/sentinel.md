# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-23 - Path Traversal in Run Directory Resolution
**Vulnerability:** `get_run_dir` was vulnerable to path traversal because `Path(base) / "runs" / run_id` allowed absolute paths or `../` in `run_id` to escape the intended directory.
**Learning:** `Path` concatenation with an absolute path string in Python overrides the base path. This is a common pitfall when using `pathlib`.
**Prevention:** Always sanitize user-provided path components using `Path(input).name` to extract only the filename/leaf component before joining it to a base directory.
