# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run Directory Resolution
**Vulnerability:** `heidi_engine/telemetry.py:get_run_dir` used `Path(base) / "runs" / run_id`, which allows an absolute `run_id` to override the base path, leading to arbitrary file writes/reads.
**Learning:** Python's `pathlib.Path / string` behavior treats absolute strings as path overrides rather than relative components. `Path('..').name` returns `'..'` and `Path('.').name` returns `''`, requiring explicit checks for these cases.
**Prevention:** Always sanitize user-controlled path components using `.name` (or `os.path.basename`) and explicitly validate against empty strings or directory markers (`.`, `..`) before concatenation.
