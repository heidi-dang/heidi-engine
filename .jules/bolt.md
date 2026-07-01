## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path Guard for Secret Detection]
**Learning:** A keyword-based fast-path for secret detection must include patterns for high-entropy strings (e.g., `[\w+/]{40,}`) to avoid functional regressions when skipping expensive regex scans on clean data.
**Action:** When implementing fast-paths for security scanners, ensure the indicator regex covers all potential match categories, including length-based heuristics.
