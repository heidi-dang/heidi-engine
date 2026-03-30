# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run ID
**Vulnerability:** The `run_id` was used directly in path construction (e.g., `runs/<run_id>/state.json`), allowing an attacker to read/write files outside the intended directory via `../` sequences or absolute paths.
**Learning:** Even internally-generated or environment-sourced IDs must be sanitized if they are used as path components. `os.path.basename` is an effective first line of defense.
**Prevention:** Always sanitize input used in file paths using `os.path.basename` and ensure the resulting path is contained within the intended base directory. Provide safe fallbacks for empty or dangerous strings like `.` or `..`.
