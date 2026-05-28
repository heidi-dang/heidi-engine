# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run Directory
**Vulnerability:** A path traversal vulnerability existed in `heidi_engine/telemetry.py` where a maliciously crafted `run_id` (e.g., an absolute path like `/etc/passwd`) could cause the pipeline to write files to arbitrary locations on the filesystem.
**Learning:** `pathlib.Path`'s `/` operator (and `joinpath`) treats the second operand as an absolute path if it starts with a slash, effectively discarding the first operand. This is a common pitfall when joining user-controlled strings to base directories.
**Prevention:** Always sanitize user-controlled path components using `Path(component).name` or similar methods to ensure they remain within the intended parent directory.
