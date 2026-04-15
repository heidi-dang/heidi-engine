## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Optimizing Validation Script and Fixing Telemetry Regression]
**Learning:** Pre-compiling regex and using fast-path indicators in standalone scripts (like `02_validate_clean.py`) provides the same significant wins as seen in core engine telemetry (~98% reduction for misses). Also, `"".join(text.split())` is consistently ~5-6x faster than `re.sub(r"\s+", "", text)` for whitespace removal in Python. Removing a cache check in a hot path (like I did in `telemetry.py`) is a regression that should be caught by unit tests.
**Action:** Always prefer `join(split())` for full whitespace removal and implement fast-path indicators for any multi-regex scanning tasks. Never remove caching logic without benchmarking the impact.
