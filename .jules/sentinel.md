# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Telemetry Run Directory
**Vulnerability:** `get_run_dir` in `heidi_engine/telemetry.py` was vulnerable to path traversal because it directly concatenated `run_id` to the base path. Absolute paths in `run_id` would override the base directory entirely.
**Learning:** Python's `Path / user_input` is dangerous if `user_input` is an absolute path. The `Path` object interprets the second part as a new root.
**Prevention:** Always sanitize user-provided path components using `.name` (in `pathlib`) or `os.path.basename` to ensure they remain relative and cannot escape the intended parent directory.
