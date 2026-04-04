# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run Directory
**Vulnerability:** The `get_run_dir` function in `heidi_engine/telemetry.py` used the `run_id` directly to construct file paths, allowing absolute path traversal (e.g., `/tmp/evil`) and relative path traversal (e.g., `../../evil`) outside the intended `runs/` directory.
**Learning:** Even internal-only identifiers should be sanitized before being used in path construction, especially when they might be influenced by environment variables or CLI arguments.
**Prevention:** Use `Path(id).name` to strip directory components from identifiers before using them to construct file paths. Implement fallback logic for empty or reserved names like `.` and `..`.
