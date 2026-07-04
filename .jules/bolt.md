## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Fast-Path Secret Detection and Pythonic String Joins]
**Learning:** Replacing `re.sub(r"\s+", "", text)` with `"".join(text.split())` provides a verified ~4.5x speedup for bulk whitespace removal. Additionally, using a keyword-based fast-path (`_SECRET_INDICATORS`) before iterating over detailed secret regexes avoids O(M*N) complexity for clean data.
**Action:** Use `"".join(text.split())` for stripping all whitespace. Implement keyword guards before executing expensive regex loops on clean payloads.
