# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run IDs
**Vulnerability:** The `run_id` used to construct telemetry directory paths was not sanitized, allowing absolute paths or traversal sequences (e.g., `..`) to write files outside the intended `runs/` directory.
**Learning:** Prepending a base directory is not sufficient to prevent path traversal if the input can be an absolute path or contain parent directory markers.
**Prevention:** Sanitize all path components from untrusted sources (including environment variables) using `os.path.basename` or `pathlib.Path.name`. For extra safety, verify the resolved path is within the expected base directory using `pathlib.Path.relative_to`.
