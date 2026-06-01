# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-06-01 - Path Traversal in Run Directory Resolution
**Vulnerability:** `heidi_engine/telemetry.py:get_run_dir` allowed absolute paths or `../` in `run_id` to escape the intended `runs/` directory.
**Learning:** Using `Path(base) / component` in Python's `pathlib` will override the base if `component` is an absolute path.
**Prevention:** Always sanitize user-provided or externally-influenced path components using `Path(component).name` and handle edge cases like `.` or `..` to restrict access to a single directory level.
