# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-02-12 - Path Traversal in Run Directory Resolution
**Vulnerability:** Run IDs were used directly with `pathlib.Path` to construct file paths, allowing absolute paths or directory traversal (e.g., `../../`) to access arbitrary system files.
**Learning:** `pathlib.Path(base) / user_input` is inherently unsafe if `user_input` is an absolute path, as `pathlib` will prioritize the absolute path.
**Prevention:** Always sanitize user-provided identifiers using `os.path.basename()` or `Path(identifier).name` before joining them with base directories.
