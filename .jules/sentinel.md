# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Exposure in Untrusted Code Execution
**Vulnerability:** The unit test gate in `scripts/03_unit_test_gate.py` was executing generated code with `os.environ` passed through to `subprocess.run`, potentially exposing sensitive keys (e.g., `OPENAI_API_KEY`) to the untrusted code.
**Learning:** Defaulting to `os.environ` when running external processes is common but dangerous when the code being run is untrusted (even if it's AI-generated).
**Prevention:** Always use a whitelist (`safe_env`) of essential variables (e.g., `PATH`, `PYTHONPATH`) and explicitly exclude secrets and user-sensitive environment data when spawning subprocesses for untrusted code.
