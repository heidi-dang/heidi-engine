# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Leakage and Regex Bypass in Unit Test Gate
**Vulnerability:** The unit test gate executed generated code with the full parent environment, potentially leaking API keys and secrets. It also used regex for dangerous pattern detection that could be bypassed using backslash-newline obfuscation.
**Learning:** Even when running code in a "sandbox" (like a temporary directory), sensitive environment variables must be explicitly filtered. Regex-based security checks must account for language-specific obfuscation like line continuations.
**Prevention:** Always filter `os.environ` before passing it to subprocesses executing untrusted code. Normalize code strings (e.g., removing backslash-newline) before applying security regexes.
