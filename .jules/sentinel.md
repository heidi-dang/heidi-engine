# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leakage in Code Execution Gate
**Vulnerability:** The unit test gate script (`scripts/03_unit_test_gate.py`) was passing the full environment to subprocesses executing generated code, allowing potential leakage of sensitive keys (OpenAI, GitHub, etc.).
**Learning:** Even with regex-based "dangerous pattern" blocking, code execution is risky. Subprocesses should always use a scrubbed environment. Additionally, injecting user code into a wrapper (`try/except`) requires careful indentation (`textwrap.indent`) to avoid SyntaxErrors.
**Prevention:** Explicitly define a `safe_env` for all subprocess calls that execute untrusted code. Scrub known sensitive keys and only pass necessary context.
