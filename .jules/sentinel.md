# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in run_id Handling
**Vulnerability:** Run identifiers were used directly to construct filesystem paths (e.g., `runs/<run_id>/state.json`), allowing a malicious `run_id` like `../../etc` to access files outside the intended scope.
**Learning:** Re-using `pathlib.Path(run_id).name` is a simple and effective way to strip all directory components from a user-provided string, but it requires explicit handling for `".."` and empty strings which `.name` may still return.
**Prevention:** Centralize path construction in a utility that enforces sanitization. Never trust a string used as a directory name if it originates from an environment variable or user input.
