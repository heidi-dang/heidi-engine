# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Hardening Untrusted Code Execution and Secret Detection
**Vulnerability:** Untrusted generated code in the unit test gate was executed with full host environment access (leaking sensitive keys like `OPENAI_API_KEY`) and dynamic import bypasses (`importlib`). Secret detection logic also missed newer `sk-proj-` OpenAI key formats.
**Learning:** Sandbox environments must follow the principle of least privilege, explicitly restricting environment variables. Static analysis of dangerous patterns must include reflection and dynamic loading modules.
**Prevention:** Always use a restricted `env` dictionary in `subprocess.run` for untrusted code execution. Maintain a robust and updated list of forbidden modules and built-ins. Regularly audit secret detection regexes against provider format updates.
