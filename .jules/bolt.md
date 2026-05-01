## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Negligible Regex Pre-compilation Impact for Small Pattern Sets]
**Learning:** Pre-compiling a small set of regex patterns (e.g., code block extraction) yields negligible performance improvement (approx. 1%) in high-level Python code where execution overhead is dominated by other factors like string manipulation or I/O.
**Action:** Prioritize algorithmic optimizations (like keyword fast-paths) over micro-optimizations like pre-compiling very small pattern sets unless they are used in extremely tight loops.
