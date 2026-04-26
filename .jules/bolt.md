## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-path regression in secret detection]
**Learning:** Adding a single combined regex "fast-path" for secret detection in `scripts/02_validate_clean.py` actually slowed down execution (0.74x - 0.96x speedup). This is likely because the individual regexes were already relatively simple, and the overhead of the extra combined regex check outweighed any skipping benefit.
**Action:** Always benchmark "obvious" optimizations like combined regex fast-paths; pre-compiling individual regexes is often sufficient and more reliable.
