# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Path Traversal in Run Directory Construction
**Vulnerability:** Run directory paths were constructed using raw `run_id` strings (`Path(base) / run_id`), allowing absolute paths or directory traversal sequences (e.g., `../../`) to escape the intended storage location.
**Learning:** Python's `pathlib.Path` join operator (`/`) overrides the base path if the second argument is an absolute path. Simple string concatenation or naive joins are insufficient for sanitizing user-provided path components.
**Prevention:** Always sanitize user-provided path components using `Path(input).name` or `os.path.basename()` to ensure they remain relative and restricted to a single directory level.
