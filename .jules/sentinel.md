# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run ID Handling
**Vulnerability:** Run identifiers (`run_id`) were used directly in path construction (e.g., `Path(ROOT) / "runs" / run_id`), allowing attackers to access or overwrite arbitrary files by providing absolute paths or relative traversal strings like `../../etc/passwd`.
**Learning:** `pathlib.Path` join operations (`/` operator) will prioritize an absolute path if it is the right-hand operand, completely overriding the base path.
**Prevention:** Always sanitize user-provided identifiers that will be used in file paths. Use `Path(user_input).name` to extract only the filename component and ensure the resulting path remains within the intended subdirectory.
