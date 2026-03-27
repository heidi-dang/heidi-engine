# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Run ID Management
**Vulnerability:** The `run_id` was used directly to construct file paths in `heidi_engine/telemetry.py`, allowing an attacker to read/write files outside the intended `runs/` directory using `../` sequences.
**Learning:** External inputs (including environment variables) used for path construction must be sanitized regardless of their source or perceived trustworthiness.
**Prevention:** Use `os.path.basename()` to strip directory components from identifiers used in path construction, and implement fallback logic for invalid/empty identifiers.

## 2025-01-24 - Environment Leakage in Untrusted Code Execution
**Vulnerability:** `scripts/03_unit_test_gate.py` executed generated (untrusted) code using the full parent environment, potentially exposing sensitive variables like `OPENAI_API_KEY`.
**Learning:** Subprocesses executing untrusted or generated code should always use a minimal, explicit environment ("safe_env") rather than inheriting the full host environment.
**Prevention:** Use a whitelist-based `env` dictionary in `subprocess.run()` calls when executing potentially untrusted code.
