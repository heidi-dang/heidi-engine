# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Unit Test Gate Sandbox Escape and Information Leak
**Vulnerability:** The unit test gate executed generated code with the full parent environment (leaking `OPENAI_API_KEY`) and had an incomplete blacklist that allowed modules like `importlib` and `ctypes` to bypass static analysis.
**Learning:** Static analysis with simple blacklists is easily bypassed in Python (e.g., via `__import__` or string concatenation). Environment sanitization is a critical secondary defense.
**Prevention:** Always sanitize `os.environ` before spawning untrusted subprocesses. Use an allowlist for environment variables. Ensure static analysis regexes use word boundaries and cover all dynamic import mechanisms.
