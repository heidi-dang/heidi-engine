# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal via Run ID
**Vulnerability:** Run ID parameters were used directly to construct file paths in telemetry and dashboard modules, allowing path traversal (e.g., ../../etc/passwd).
**Learning:** Functions that construct paths from user-provided or environment-provided identifiers must always sanitize those identifiers. Relying on these IDs being "well-behaved" is a security risk.
**Prevention:** Use a dedicated sanitization function (like `sanitize_run_id`) that enforces safe path components (using `Path(id).name`) and rejects dangerous segments like '..' or empty strings.
