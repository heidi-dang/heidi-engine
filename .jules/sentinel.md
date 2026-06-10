# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Run Directory Construction
**Vulnerability:** Using `Path(base) / run_id` allowed an attacker to override the `base` directory if `run_id` was an absolute path, leading to path traversal.
**Learning:** Python's `pathlib.Path` join behavior (`/` operator) treats absolute path arguments as a new root, ignoring preceding components.
**Prevention:** Always sanitize user-provided path components using `.name` or `os.path.basename` to ensure they remain relative to the intended parent directory.
