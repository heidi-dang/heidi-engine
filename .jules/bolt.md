## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimized Validation Pipeline]
**Learning:** Pre-compiling regex patterns and using "".join(text.split()) for whitespace removal provide measurable performance gains (~2x) in data validation scripts. Fast-path indicators are powerful but must be used carefully to avoid false negatives if keywords are not exhaustive.
**Action:** Use pre-compiled regex objects for repeated pattern matching and prefer built-in string methods over regex for simple operations like whitespace stripping.
