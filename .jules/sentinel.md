# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run Directory Construction
**Vulnerability:** `get_run_dir` used `Path(base) / run_id`, which allows `run_id` to be an absolute path (e.g., `/etc/passwd`) or contain `..`, overriding the base directory.
**Learning:** `pathlib.Path` join logic handles absolute paths by making them the new root. `Path(run_id).name` successfully strips directories but returns `".."` if the input is `".."` and `""` if the input is `"."`.
**Prevention:** Sanitize user-provided path components using `.name` and explicitly check for `".."` or empty string results to provide a safe default.
