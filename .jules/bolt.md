## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path Guard for Secret Detection]
**Learning:** A fast-path keyword indicator check (using a single pre-compiled regex) before performing multiple individual regex scans yields a ~1.7x speedup for clean dataset samples. However, this fast-path must explicitly include all classes of patterns, such as high-entropy strings, to avoid functional regressions.
**Action:** When implementing fast-path guards for composite security logic, ensure the guard regex is a true superset of all underlying patterns.
