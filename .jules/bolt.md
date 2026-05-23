## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Validation Pipeline Optimization]
**Learning:** In `scripts/02_validate_clean.py`, replacing `re.sub(r"\s+", "", text)` with `"".join(text.split())` for whitespace removal in `fuzzy_hash` provided a ~6.8x performance gain. Additionally, implementing a pre-compiled regex fast-path for secret detection reduced processing time for clean samples by ~33%.
**Action:** Use string split/join for global whitespace removal instead of regex when performance is critical. Always pre-compile regex patterns at the module level for batch processing tasks.
