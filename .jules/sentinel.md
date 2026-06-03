# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Telemetry Run Directories
**Vulnerability:** `heidi_engine/telemetry.py:get_run_dir` allowed absolute paths in `run_id` to override the base directory, potentially leaking or corrupting files outside the intended path.
**Learning:** Python's `Path(base) / user_input` is unsafe if `user_input` is an absolute path. The `Path` object will discard the base and use the absolute path instead.
**Prevention:** Always sanitize user-provided path components using `.name` or `os.path.basename` to ensure they remain relative to the intended parent directory.
