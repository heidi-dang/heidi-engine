# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Information Exposure in Unit Test Gate
**Vulnerability:** The unit test gate passed the full host environment to subprocesses executing untrusted generated code, potentially leaking `OPENAI_API_KEY`.
**Learning:** Even internal tool scripts that execute code must follow the principle of least privilege for environment variables to prevent accidental secret exposure.
**Prevention:** Always use a restricted `safe_env` whitelist when running `subprocess.run` with untrusted input.

## 2025-01-24 - Broken Cache Logic with NameError
**Vulnerability:** A redundant cache check in `telemetry.py:get_state` used an undefined variable `target_run_id`, which would crash the telemetry server on a cache miss in certain paths.
**Learning:** "Optimization" code that isn't covered by tests can introduce critical failures. Dead code or redundant blocks should be aggressively pruned.
**Prevention:** Ensure every logic branch, especially performance optimizations, is covered by unit tests. Remove redundant code blocks that mirror already-implemented thread-safe patterns.
