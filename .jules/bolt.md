## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-04-11 - Optimization for whitespace removal
**Learning:** For simple whitespace removal (replacing all whitespace with nothing), "".join(text.split()) is significantly faster (~6x) than re.sub(r"\s+", "", text) in Python because split() is implemented in C and avoids the overhead of the regex engine.
**Action:** Use "".join(text.split()) for aggressive whitespace removal in performance-critical paths like fuzzy hashing or data cleaning.
