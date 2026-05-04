## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-05-04 - [Optimized Validation Pipeline and Fixed Telemetry Cache]
**Learning:** Keyword-based fast-paths for regex-heavy validation (like secret scanning) provide massive speedups (up to 9x) but must explicitly include markers for all patterns (e.g., quotes for high-entropy strings) to avoid skipping detections. Additionally, Python's `"".join(text.split())` is consistently ~6-7x faster than `re.sub` for global whitespace removal.
**Action:** Use idiomatic string methods over regex for simple manipulations and always guard regex loops with comprehensive fast-path checks that cover all target patterns.
