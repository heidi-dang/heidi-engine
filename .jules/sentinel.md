# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Run ID Handling
**Vulnerability:** Run IDs provided via environment variables or CLI were used directly in path construction (`Path(AUTOTRAIN_DIR) / "runs" / run_id`), allowing attackers to read or write files outside the intended runs directory (e.g., via `../../`).
**Learning:** Path traversal is a common risk when user-provided strings are used to build file paths. Sanitization at the input level is critical even if the environment is considered "internal" or "trusted".
**Prevention:** Always sanitize user-provided identifiers using `pathlib.Path(id).name` to strip directory components. Default to a safe placeholder if sanitization results in an empty or dangerous string (e.g., ".", "..").
