## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).
## 2026-02-21 - [Validation Pipeline Optimizations]
**Learning:** In `scripts/02_validate_clean.py`, implementing a keyword-based fast-path for `detect_secrets` provides a massive speedup (approx. 70x) for 'very clean' text samples by skipping all expensive regex searches. Additionally, `"".join(text.split())` is significantly faster (~5.3x) than `re.sub(r"\s+", "", text)` for whitespace removal in fingerprinting.
**Action:** Use string-based fast-paths before regex for common-case filtering, and prefer native string methods over regex for simple character/whitespace manipulations.
