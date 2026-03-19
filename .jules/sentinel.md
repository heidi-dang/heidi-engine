# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Environment Secret Leakage in Unit Test Gate
**Vulnerability:** The unit test gate passed the entire parent environment (including `OPENAI_API_KEY`) to a subprocess executing untrusted, LLM-generated code.
**Learning:** Automation scripts often inherit sensitive environment variables by default. When bridging to code execution, this creates a direct path for exfiltration.
**Prevention:** Always sanitize the environment passed to subprocesses. Use an explicit allowlist or a restrictive denylist to strip sensitive keywords (KEY, TOKEN, SECRET, PASS) before execution.
