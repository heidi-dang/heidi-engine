# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Run Directory Resolution
**Vulnerability:** `Path(BASE) / run_id` allowed absolute paths or `..` to escape the base directory because `pathlib`'s `/` operator overrides the base when joined with an absolute path.
**Learning:** Standard path joining in Python is not safe for untrusted components. `Path(run_id).name` is an effective way to strip all directory components.
**Prevention:** Always sanitize user-provided path components using `.name` to ensure they remain relative to the intended parent directory.
