# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Sandbox Hardening and Environment Protection in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code without filtering sensitive environment variables (like `OPENAI_API_KEY`) and lacked protections against advanced Python sandbox escape techniques using `importlib`, `builtins`, `inspect`, or `gc`.
**Learning:** Simple blacklisting of common modules like `os` or `subprocess` is insufficient in Python; advanced reflection and dynamic import modules must also be blocked. Furthermore, sub-processes inherit the parent's environment by default, which can leak production secrets if not explicitly filtered.
**Prevention:** Always filter environment variables when running untrusted code in a subprocess. Expand sandboxing blacklists to include reflection/introspection modules. Use `textwrap.indent` to ensure proper wrapping of user code in execution templates to prevent syntax-based escape attempts.
