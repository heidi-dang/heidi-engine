# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run IDs
**Vulnerability:** Run IDs were used directly in path construction without sanitization, allowing absolute paths or parent directory traversal (`../../`) to write/read files outside the intended `AUTOTRAIN_DIR`.
**Learning:** `pathlib.Path`'s `/` operator or `Path.joinpath` behavior will prioritize an absolute path if it is passed as a later segment (e.g., `Path('/base') / '/abs/path'` results in `Path('/abs/path')`).
**Prevention:** Always sanitize user-provided identifiers that will be used in file paths. Using `Path(identifier).name` is a simple way to extract only the filename component and prevent traversal or absolute path injection.
