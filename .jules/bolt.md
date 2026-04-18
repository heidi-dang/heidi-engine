## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-20 - [Redundant Cache Check with NameError]
**Learning:** Redundant cache checks can not only waste CPU cycles but also hide bugs like NameErrors if the second check uses an undefined variable and is partially shadowed by a correct check earlier in the function.
**Action:** Always ensure that caching logic is clean and non-redundant. Use automated tests to verify that all code paths in performance-critical functions like `get_state` are actually reachable and correct.
