# Sentinel Security Journal

## 2025-01-24 - Path Traversal in Run ID Handling
**Vulnerability:** `get_run_dir` and `get_run_id` accepted arbitrary `run_id` strings containing path traversal sequences (e.g. `../../`), allowing file operations outside `AUTOTRAIN_DIR/runs`.
**Learning:** Accepting user-controlled or environment identifiers directly as path components without character restrictions poses path traversal risks when constructing `Path` objects.
**Prevention:** Always sanitize input identifiers using strict character whitelists (e.g. `re.sub(r"[^\w\-]", "", run_id)`) before constructing file system paths.

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.
