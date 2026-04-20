# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.
## 2025-04-20 - Unsafe Code Execution Environment in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code in an environment inheriting all parent environment variables, potentially leaking sensitive API keys (e.g., OPENAI_API_KEY) to untrusted code. Additionally, the sandbox could be easily escaped using standard Python introspection and library imports.
**Learning:** Executing code in a subprocess requires strict control over the environment and imports. Blocklists for dangerous patterns are easily bypassed; a combination of allowlisting environment variables and robust pattern matching for sandbox escape sequences (like `__subclasses__`) is required.
**Prevention:** Use environment variable allowlists when spawning subprocesses for code execution. Extend dangerous pattern detection to include introspection attributes and common sandbox escape libraries like `importlib` and `inspect`.