## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path Secret Detection Guard]
**Learning:** Fast-path keyword guards for secret detection must include a heuristic for high-entropy strings (e.g., `[\w+/]{40,}`) to avoid skipping generic secrets that don't match specific keywords like "key" or "token".
**Action:** When implementing fast-paths for security scanners, ensure the "shallow" check is a true superset of all "deep" patterns to avoid functional regressions.
